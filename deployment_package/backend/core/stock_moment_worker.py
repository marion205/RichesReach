"""
Worker that processes raw moment jobs and generates AI-powered stock moments.

Uses structured outputs for reliable JSON parsing and Pydantic for validation.
"""

from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
from functools import wraps

from django.db import transaction
from django.conf import settings

from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
IMPORTANCE_THRESHOLD = float(os.getenv("IMPORTANCE_THRESHOLD", "0.2"))
MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
RETRY_DELAY = 2  # seconds, exponential backoff base

_openai_client = None

# Data structures for jobs (using Pydantic for better validation)
class PriceContext(BaseModel):
    start_price: float = Field(..., gt=0)
    end_price: float = Field(..., gt=0)
    pct_change: float
    volume_vs_average: str


# Event is now imported from unified_data_service
# Keeping this for backward compatibility, but will use UnifiedDataService.Event
class Event(BaseModel):
    type: str  # "EARNINGS", "NEWS", "INSIDER", "MACRO", "SENTIMENT", "OPTIONS"
    time: datetime
    headline: str
    summary: str
    url: Optional[str] = None


class RawMomentJob(BaseModel):
    """
    This represents the input you feed into the worker.
    In your real system this might be a DB row, Kafka message, etc.
    """
    symbol: str
    timestamp: datetime  # primary date for the moment
    price_context: PriceContext
    events: List[Event]


# LLM Output Schema (Pydantic model for structured output)
class StockMomentOutput(BaseModel):
    title: str = Field(..., max_length=140)
    quick_summary: str = Field(...)
    deep_summary: str = Field(...)
    category: str
    importance_score: float = Field(..., ge=0.0, le=1.0)
    source_links: List[str] = Field(default_factory=list)

    @validator("category")
    def validate_category(cls, v):
        from core.models import MomentCategory
        v = (v or "").upper().strip()
        valid_categories = {c[0] for c in MomentCategory.choices}  # Get the value (first element of tuple)
        if v not in valid_categories:
            return MomentCategory.OTHER  # Return the value directly
        return v


def normalize_category(value: Optional[str]) -> str:
    """Normalize a category string to a valid MomentCategory value."""
    from core.models import MomentCategory

    v = (value or "").upper().strip()
    valid_categories = {c[0] for c in MomentCategory.choices}
    return v if v in valid_categories else MomentCategory.OTHER


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI()
    return _openai_client


# Prompt pieces (refined for clarity and structured output)
SYSTEM_MESSAGE = """You are an expert financial journalist and educator.

Your job is to explain important stock price movements in clear, 
simple language that a beginner can understand in under 30 seconds.

Constraints:
- Do NOT give investment advice or tell the user what to buy/sell/hold.
- Be neutral and factual in tone.
- Focus on *why* the price moved and what the key drivers were.
- Avoid jargon; if you must use a term, briefly define it.
- Prefer 6th–8th grade reading level.
- Never hallucinate facts. Only use the data provided to you.
- If the cause is unclear, say that clearly and give possible factors.

Respond with a single JSON object matching the provided schema."""


USER_TEMPLATE = """Create a single STOCK MOMENT for this symbol and time window.

Symbol: {symbol}
Primary date / timestamp for the moment: {timestamp}

Price + volume context:
- Starting price: {start_price}
- Ending price: {end_price}
- % change over window: {pct_change}%
- Volume vs normal: {volume_vs_average}

Relevant events around this time:
{events_block}

Decide whether this period is important enough to show the user.
If not important (too noisy / random), set "importance_score" very low (≤0.05).

Synthesize all inputs into ONE coherent story for this moment.

Guidelines:
- "title" should capture the main driver, not clickbait.
- "quick_summary" must stand alone on a small card under a stock chart.
- "deep_summary" should add context: what happened, why it mattered, 
  and how it fits into the company's or market's broader story.
- If the price move is likely driven by multiple events, briefly connect them.
- If there is genuine uncertainty, say "The move may be related to..." 
  instead of inventing certainty."""


def build_events_block(events: List[Event]) -> str:
    if not events:
        return "- No specific events found in this window."

    lines = []
    for ev in events:
        lines.append(
            f"- Type: {ev.type}\n"
            f"  Time: {ev.time.isoformat()}\n"
            f"  Headline: {ev.headline}\n"
            f"  Summary: {ev.summary}\n"
            f"  Source URL: {ev.url or ''}"
        )
    return "\n".join(lines)


def retry_on_failure(max_retries: int = MAX_RETRIES, delay: int = RETRY_DELAY):
    """Simple retry decorator for transient errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                        import time
                        time.sleep(wait)
                    else:
                        raise
            raise last_exception
        return wrapper
    return decorator


@retry_on_failure()
def call_llm_for_moment(job: RawMomentJob) -> StockMomentOutput:
    events_block = build_events_block(job.events)
    price_ctx = job.price_context

    user_message = USER_TEMPLATE.format(
        symbol=job.symbol,
        timestamp=job.timestamp.isoformat(),
        start_price=price_ctx.start_price,
        end_price=price_ctx.end_price,
        pct_change=price_ctx.pct_change,
        volume_vs_average=price_ctx.volume_vs_average,
        events_block=events_block,
    )

    # Use structured outputs with Pydantic schema
    client = _get_openai_client()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_message},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "stock_moment_output",
                "schema": StockMomentOutput.model_json_schema(),
                "strict": True,  # Enforce strict adherence
            },
        },
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Model returned empty content")

    try:
        # Parse and validate with Pydantic
        data = StockMomentOutput.model_validate_json(content)
    except ValueError as e:
        raise RuntimeError(f"Failed to validate structured output: {e}\nRaw: {content}")

    return data


@transaction.atomic
def create_stock_moment_from_job(job: RawMomentJob) -> Optional[StockMoment]:
    from core.models import StockMoment
    try:
        data = call_llm_for_moment(job)
    except Exception as e:
        logger.error("Failed to generate stock moment for %s: %s", job.symbol, e, exc_info=True)
        return None

    if isinstance(data, dict):
        try:
            data = StockMomentOutput.model_validate(data)
        except Exception as e:
            logger.error("Invalid LLM response for %s: %s", job.symbol, e, exc_info=True)
            return None

    if not hasattr(data, "importance_score"):
        logger.error("LLM response missing importance_score for %s", job.symbol)
        return None

    # Ignore unimportant moments
    if data.importance_score <= IMPORTANCE_THRESHOLD:
        logger.info(f"Skipped low-importance moment for {job.symbol} @ {job.timestamp} (score: {data.importance_score})")
        return None

    # Ensure UTC timestamp
    timestamp = job.timestamp.replace(tzinfo=timezone.utc) if job.timestamp.tzinfo is None else job.timestamp

    moment = StockMoment.objects.create(
        symbol=job.symbol.upper(),
        timestamp=timestamp,
        importance_score=float(data.importance_score),
        category=normalize_category(getattr(data, "category", None)),
        title=(data.title or "").strip(),
        quick_summary=(data.quick_summary or "").strip(),
        deep_summary=(data.deep_summary or "").strip(),
        source_links=getattr(data, "source_links", []) or [],
        # impact_1d / impact_7d can be backfilled later by a separate worker
    )
    logger.info(f"Created StockMoment {moment.id} for {moment.symbol} @ {moment.timestamp} (score: {data.importance_score})")
    return moment


async def fetch_events_for_moment(
    symbol: str,
    timestamp: datetime,
    window_hours: int = 24,
) -> List[Event]:
    """
    Fetch all events for a symbol around a given timestamp using the unified data service.
    This replaces manual event fetching with automated aggregation from all sources.
    """
    import asyncio
    
    from core.data_sources.unified_data_service import UnifiedDataService

    start_date = timestamp - timedelta(hours=window_hours)
    end_date = timestamp + timedelta(hours=window_hours)
    
    try:
        unified_data_service = UnifiedDataService()
        events = await unified_data_service.get_all_events_for_symbol(
            symbol, start_date, end_date
        )
        
        # Convert unified events to worker Event format
        worker_events = []
        for event in events:
            worker_events.append(
                Event(
                    type=event.type,
                    time=event.time,
                    headline=event.headline,
                    summary=event.summary,
                    url=event.url,
                )
            )
        
        logger.info(f"Fetched {len(worker_events)} events for {symbol} around {timestamp}")
        return worker_events
    except Exception as e:
        logger.error(f"Error fetching events for {symbol}: {e}")
        return []


# Example "main loop"
def fetch_pending_jobs() -> List[RawMomentJob]:
    """
    Replace this with your real queue/DB fetch.

    This example just returns an empty list so it's safe to run.
    """
    return []


def main():
    jobs = fetch_pending_jobs()
    if not jobs:
        logger.info("No pending jobs found.")
        return

    for job in jobs:
        try:
            moment = create_stock_moment_from_job(job)
        except Exception as e:
            logger.error(f"Error processing job for {job.symbol} @ {job.timestamp}: {e}", exc_info=True)
            # Optionally, mark job as failed in your queue/DB


if __name__ == "__main__":
    main()
