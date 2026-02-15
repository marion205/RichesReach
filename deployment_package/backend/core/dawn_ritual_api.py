"""
Dawn Ritual API (Ritual Dawn)
Tactical morning check-in: portfolio snapshot, market context, action suggestion.
Syncs Yodlee transactions as an optional background step.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import sys
import os
import secrets
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup logger
logger = logging.getLogger(__name__)

# Django imports
import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
    django.setup()

from django.contrib.auth import get_user_model
from django.db import connections
from asgiref.sync import sync_to_async

User = get_user_model()

# Try to import Yodlee client
try:
    from .yodlee_client import YodleeClient
    from .banking_models import BankAccount, BankTransaction
    YODLEE_AVAILABLE = True
except ImportError:
    YODLEE_AVAILABLE = False
    logger.warning("Yodlee not available for Dawn Ritual")

# Try to import portfolio / market / streak services
try:
    from .portfolio_service import PortfolioService
    PORTFOLIO_AVAILABLE = True
except ImportError:
    PORTFOLIO_AVAILABLE = False
    logger.warning("PortfolioService not available for Ritual Dawn")

try:
    from .daily_brief_models import UserStreak, RitualDawnCompletion
    STREAK_AVAILABLE = True
    RITUAL_COMPLETION_AVAILABLE = True
except ImportError:
    STREAK_AVAILABLE = False
    RITUAL_COMPLETION_AVAILABLE = False
    RitualDawnCompletion = None  # type: ignore[misc, assignment]
    logger.warning("UserStreak / RitualDawnCompletion not available for Ritual Dawn")

try:
    from .ritual_action_engine import generate_ritual_action
    ACTION_ENGINE_AVAILABLE = True
except ImportError:
    ACTION_ENGINE_AVAILABLE = False
    logger.warning("Ritual action engine not available")

_market_data_service = None


def _get_market_data_service():
    """Return shared market data service via facade."""
    global _market_data_service
    if _market_data_service is None:
        try:
            from .market_data_manager import get_market_data_service
            _market_data_service = get_market_data_service()
        except Exception as e:
            logger.warning(f"Market data service not available: {e}")
    return _market_data_service


router = APIRouter(prefix="/api/rituals/dawn", tags=["rituals"])

# ============================================================================
# Greeting / Tagline Pool (all original)
# ============================================================================

def _gk(bucket: str, i: int) -> str:
    """Greeting key for A/B: bucket + index."""
    return f"{bucket}_{i}"

GREETINGS = [
    {"greeting": "Markets opened. Your portfolio moved.", "tagline": "Clarity precedes capital.", "key": _gk("default", 0)},
    {"greeting": "A new day. New data. One decision.", "tagline": "What's your highest-conviction move today?", "key": _gk("default", 1)},
    {"greeting": "Good morning. Your money didn't sleep.", "tagline": "Let's see what changed overnight.", "key": _gk("default", 2)},
    {"greeting": "The market moved. Did your conviction?", "tagline": "Precision over impulse.", "key": _gk("default", 3)},
    {"greeting": "Dawn check-in. Quick. Focused. Done.", "tagline": "One clear action beats ten vague intentions.", "key": _gk("default", 4)},
    {"greeting": "Your capital is awake. Are you?", "tagline": "Awareness is the first edge.", "key": _gk("default", 5)},
    {"greeting": "Another day, another data point.", "tagline": "Compound decisions, not just returns.", "key": _gk("default", 6)},
    {"greeting": "The overnight session closed. Time to assess.", "tagline": "Informed beats reactive.", "key": _gk("default", 7)},
]

STREAK_GREETINGS = [
    {"greeting": "{streak}-day streak. Consistency compounds.", "tagline": "Discipline is your edge.", "key": _gk("streak", 0)},
    {"greeting": "Day {streak}. You keep showing up.", "tagline": "Habits build portfolios.", "key": _gk("streak", 1)},
]

# Time-of-day greeting pools (client_hour 0-23)
GREETINGS_MORNING = [
    {"greeting": "Good morning. Your money didn't sleep.", "tagline": "Let's see what changed overnight.", "key": _gk("morning", 0)},
    {"greeting": "Dawn check-in. Quick. Focused. Done.", "tagline": "One clear action beats ten vague intentions.", "key": _gk("morning", 1)},
    {"greeting": "Your capital is awake. Are you?", "tagline": "Awareness is the first edge.", "key": _gk("morning", 2)},
    {"greeting": "A new day. New data. One decision.", "tagline": "What's your highest-conviction move today?", "key": _gk("morning", 3)},
]
GREETINGS_AFTERNOON = [
    {"greeting": "Good afternoon. Time for a quick check-in.", "tagline": "Clarity precedes capital.", "key": _gk("afternoon", 0)},
    {"greeting": "Markets are moving. Here's where you stand.", "tagline": "Informed beats reactive.", "key": _gk("afternoon", 1)},
    {"greeting": "Midday pulse. One clear action.", "tagline": "Precision over impulse.", "key": _gk("afternoon", 2)},
]
GREETINGS_EVENING = [
    {"greeting": "Good evening. How did today treat your portfolio?", "tagline": "Compound decisions, not just returns.", "key": _gk("evening", 0)},
    {"greeting": "Evening check-in. Close the day with clarity.", "tagline": "Awareness is the first edge.", "key": _gk("evening", 1)},
]
GREETINGS_NIGHT = [
    {"greeting": "Ready when you are.", "tagline": "Your tactical check-in, any time.", "key": _gk("night", 0)},
    {"greeting": "Night owl? Your portfolio summary is here.", "tagline": "Let's see what changed.", "key": _gk("night", 1)},
]


def _hour_bucket(hour: int) -> str:
    """Return 'morning' (5-11), 'afternoon' (12-16), 'evening' (17-21), 'night' (22-4)."""
    if 5 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 16:
        return "afternoon"
    if 17 <= hour <= 21:
        return "evening"
    return "night"


def _pick_greeting(streak: int, client_hour: Optional[int] = None) -> dict:
    """Pick an original tactical greeting; optionally streak-aware and time-of-day aware. Returns greeting, tagline, key (for A/B)."""
    if streak >= 7 and random.random() < 0.4:
        g = random.choice(STREAK_GREETINGS)
        return {
            "greeting": g["greeting"].format(streak=streak),
            "tagline": g["tagline"],
            "key": g.get("key", "streak"),
        }
    if client_hour is not None and 0 <= client_hour <= 23:
        bucket = _hour_bucket(client_hour)
        if bucket == "morning":
            g = random.choice(GREETINGS_MORNING)
        elif bucket == "afternoon":
            g = random.choice(GREETINGS_AFTERNOON)
        elif bucket == "evening":
            g = random.choice(GREETINGS_EVENING)
        else:
            g = random.choice(GREETINGS_NIGHT)
        return {"greeting": g["greeting"], "tagline": g["tagline"], "key": g.get("key", bucket)}
    g = random.choice(GREETINGS)
    return {"greeting": g["greeting"], "tagline": g["tagline"], "key": g.get("key", "default")}


# ============================================================================
# Legacy Haiku Generator (kept for backward compat)
# ============================================================================

HAIKUS = [
    "From grocery shadows to investment light\nYour wealth awakens, bold and bright.",
    "Each transaction, a seed in the ground\nWatch your fortune grow, without a sound.",
    "Morning sun rises, accounts align\nFinancial freedom, truly divine.",
    "Small steps today, mountains tomorrow\nYour wealth path, no need to borrow.",
    "Dawn breaks through, clearing the way\nYour financial future, bright as day.",
    "Pennies saved today, dollars earned tomorrow\nYour wealth journey, no need to borrow.",
    "Transactions flow, like morning streams\nBuilding wealth, fulfilling dreams.",
    "From daily spending to smart investing\nYour financial future, truly uplifting.",
    "Each dollar tracked, each goal in sight\nYour wealth awakens, bold and bright.",
    "Morning ritual, wealth aligned\nFinancial peace, truly refined.",
]


def generate_haiku(transactions_synced: int = 0) -> str:
    """Generate a motivational haiku based on transaction sync"""
    if transactions_synced > 0:
        success_haikus = [
            "From grocery shadows to investment light\nYour wealth awakens, bold and bright.",
            "Each transaction, a seed in the ground\nWatch your fortune grow, without a sound.",
            "Transactions flow, like morning streams\nBuilding wealth, fulfilling dreams.",
        ]
        return random.choice(success_haikus)
    return random.choice(HAIKUS)


# ============================================================================
# Authentication Helper
# ============================================================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Get current user from token"""
    if not authorization or not authorization.startswith('Bearer '):
        import asyncio
        def get_user_sync():
            connections.close_all()
            user = User.objects.first()
            if user:
                return user
            return User.objects.create_user(
                email='test@example.com',
                name='Test User',
                password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
            )
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_user_sync)

    token = authorization[7:]

    if token.startswith('dev-token-'):
        import asyncio
        def get_user_sync():
            connections.close_all()
            user = User.objects.first()
            if user:
                return user
            return User.objects.create_user(
                email='test@example.com',
                name='Test User',
                password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
            )
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_user_sync)

    import asyncio
    def get_user_sync():
        connections.close_all()
        return User.objects.first() or User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password=os.getenv('DEV_TEST_USER_PASSWORD', secrets.token_urlsafe(16))
        )
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_user_sync)


# ============================================================================
# Request/Response Models
# ============================================================================

class DawnRitualRequest(BaseModel):
    """Optional client local hour (0-23) for time-aware greetings."""
    client_hour: Optional[int] = None


class PortfolioHoldingSnapshot(BaseModel):
    symbol: str
    name: str
    shares: float
    current_price: float
    previous_close: float
    change_dollars: float
    change_percent: float


class PortfolioSnapshot(BaseModel):
    total_value: float
    previous_total_value: float
    change_dollars: float
    change_percent: float
    top_holdings: List[PortfolioHoldingSnapshot]
    holdings_count: int
    has_portfolio: bool


class MarketContext(BaseModel):
    sp500_change_percent: float
    sp500_direction: str
    market_sentiment: str
    notable_indices: List[Dict[str, Any]]
    headline: str
    volatility_level: str
    is_weekend: bool = False  # True when markets closed (Sat/Sun) for weekly-recap mode


class ActionSuggestion(BaseModel):
    action_type: str
    headline: str
    detail: str
    action_label: str
    target_screen: Optional[str] = None
    urgency: str


class RitualDawnResponse(BaseModel):
    greeting: str
    tagline: str
    greeting_key: Optional[str] = None  # A/B: which greeting variant was shown
    portfolio: PortfolioSnapshot
    market: MarketContext
    action: ActionSuggestion
    streak: int
    timestamp: str
    # Legacy fields for backward compatibility
    transactionsSynced: int
    haiku: str


class RitualDawnCompleteRequest(BaseModel):
    action_taken: str = ""
    greeting_key: Optional[str] = None  # A/B: which greeting was shown when user completed


class RitualDawnFollowThroughRequest(BaseModel):
    """Report that the user opened the target screen (e.g. StockDetail for symbol)."""
    target_screen: str
    target_params: Optional[Dict[str, Any]] = None  # e.g. {"symbol": "AAPL"}


# ============================================================================
# Data Aggregation Helpers
# ============================================================================

async def _build_portfolio_snapshot(user) -> PortfolioSnapshot:
    """Build portfolio snapshot from PortfolioService."""
    if not PORTFOLIO_AVAILABLE:
        return PortfolioSnapshot(
            total_value=0, previous_total_value=0,
            change_dollars=0, change_percent=0,
            top_holdings=[], holdings_count=0, has_portfolio=False,
        )

    try:
        service = PortfolioService()
        portfolios_data = await sync_to_async(service.get_user_portfolios)(user)

        if not portfolios_data or not portfolios_data.get("portfolios"):
            return PortfolioSnapshot(
                total_value=0, previous_total_value=0,
                change_dollars=0, change_percent=0,
                top_holdings=[], holdings_count=0, has_portfolio=False,
            )

        total_value = float(portfolios_data.get("total_value", 0))
        all_holdings = []
        symbols = set()

        for portfolio in portfolios_data.get("portfolios", []):
            for holding in portfolio.get("holdings", []):
                stock = holding.get("stock")
                if not stock:
                    continue
                symbol = stock.symbol if hasattr(stock, "symbol") else str(stock)
                symbols.add(symbol)

        # Fetch real previous-close from market data when available (per-symbol quotes)
        prev_close_by_symbol = {}
        market_svc = _get_market_data_service()
        if market_svc and symbols:
            import asyncio
            async def _quote(s):
                q = await market_svc.get_stock_quote(s)
                if q and (q.get("previous_close") or q.get("pc")):
                    return (s, float(q.get("previous_close") or q.get("pc", 0)))
                if q and q.get("price") is not None and q.get("change") is not None:
                    return (s, float(q["price"]) - float(q.get("change", 0)))
                return (s, None)
            results = await asyncio.gather(*[_quote(s) for s in symbols], return_exceptions=True)
            for r in results:
                if isinstance(r, tuple) and r[1] is not None:
                    prev_close_by_symbol[r[0]] = r[1]

        for portfolio in portfolios_data.get("portfolios", []):
            for holding in portfolio.get("holdings", []):
                stock = holding.get("stock")
                if not stock:
                    continue
                symbol = stock.symbol if hasattr(stock, "symbol") else str(stock)
                name = stock.name if hasattr(stock, "name") else symbol
                shares = float(holding.get("shares", 0))
                current_price = float(holding.get("current_price", 0) or holding.get("average_price", 0))
                average_price = float(holding.get("average_price", 0) or current_price)
                value = shares * current_price

                # Real previous-close from market data when available; else average_price (cost-basis proxy)
                previous_close = prev_close_by_symbol.get(symbol)
                if previous_close is None or previous_close <= 0:
                    previous_close = average_price if average_price > 0 else current_price
                change_dollars = (current_price - previous_close) * shares
                change_pct = ((current_price - previous_close) / previous_close * 100) if previous_close else 0

                all_holdings.append({
                    "symbol": symbol,
                    "name": name,
                    "shares": shares,
                    "current_price": current_price,
                    "previous_close": previous_close,
                    "change_dollars": round(change_dollars, 2),
                    "change_percent": round(change_pct, 2),
                    "value": value,
                })

        all_holdings.sort(key=lambda h: h["value"], reverse=True)
        top_5 = all_holdings[:5]

        total_change = sum(h["change_dollars"] for h in all_holdings)
        previous_total = total_value - total_change
        change_pct = (total_change / previous_total * 100) if previous_total else 0

        return PortfolioSnapshot(
            total_value=round(total_value, 2),
            previous_total_value=round(previous_total, 2),
            change_dollars=round(total_change, 2),
            change_percent=round(change_pct, 2),
            top_holdings=[
                PortfolioHoldingSnapshot(
                    symbol=h["symbol"],
                    name=h["name"],
                    shares=h["shares"],
                    current_price=h["current_price"],
                    previous_close=h["previous_close"],
                    change_dollars=h["change_dollars"],
                    change_percent=h["change_percent"],
                )
                for h in top_5
            ],
            holdings_count=len(all_holdings),
            has_portfolio=len(all_holdings) > 0,
        )

    except Exception as e:
        logger.error(f"Error building portfolio snapshot: {e}", exc_info=True)
        return PortfolioSnapshot(
            total_value=0, previous_total_value=0,
            change_dollars=0, change_percent=0,
            top_holdings=[], holdings_count=0, has_portfolio=False,
        )


def _is_weekend() -> bool:
    """True if today is Saturday or Sunday (markets closed)."""
    from datetime import datetime
    return datetime.utcnow().weekday() >= 5  # 5=Sat, 6=Sun


async def _build_market_context() -> MarketContext:
    """Build market context from the market data facade. Weekend mode: weekly recap headline."""
    is_weekend = _is_weekend()
    default_ctx = MarketContext(
        sp500_change_percent=0,
        sp500_direction="flat",
        market_sentiment="neutral",
        notable_indices=[],
        headline="Market data is currently unavailable.",
        volatility_level="moderate",
        is_weekend=is_weekend,
    )

    market_service = _get_market_data_service()
    if not market_service:
        return default_ctx

    try:
        overview = await market_service.get_market_overview()
        if not overview:
            return default_ctx

        # Extract indices
        indices = overview.get("indices") or {}
        notable = []
        for sym, data in indices.items():
            if isinstance(data, dict):
                notable.append({
                    "name": data.get("name", sym),
                    "symbol": sym,
                    "change_percent": round(float(data.get("change_percent", data.get("change", 0))), 2),
                })

        # S&P 500 specifically
        gspc = indices.get("^GSPC") or {}
        sp500_pct = float(gspc.get("change_percent", gspc.get("change", overview.get("average_change", 0))))
        sp500_dir = "up" if sp500_pct > 0.05 else ("down" if sp500_pct < -0.05 else "flat")

        # Sentiment
        sentiment = overview.get("sentiment", "neutral")
        if isinstance(sentiment, str):
            pass
        elif sp500_pct > 0.5:
            sentiment = "bullish"
        elif sp500_pct < -0.5:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        # Volatility
        vol = overview.get("volatility", 0.015)
        if isinstance(vol, (int, float)):
            if vol > 0.02:
                vol_level = "elevated"
            elif vol < 0.01:
                vol_level = "low"
            else:
                vol_level = "moderate"
        else:
            vol_level = "moderate"

        # Headline (weekend = weekly recap; weekdays = overnight)
        if is_weekend:
            headline = "Markets are closed. Here's your weekly recap and what to watch when they reopen."
        else:
            abs_pct = abs(sp500_pct)
            if abs_pct > 2:
                headline = "Markets made a significant move overnight."
            elif abs_pct > 0.5:
                direction_word = "higher" if sp500_pct > 0 else "lower"
                headline = f"Markets shifted {direction_word} overnight. Here's what changed."
            else:
                headline = "Markets are relatively quiet. A good day to review, not react."

        return MarketContext(
            sp500_change_percent=round(sp500_pct, 2),
            sp500_direction=sp500_dir,
            market_sentiment=sentiment,
            notable_indices=notable,
            headline=headline,
            volatility_level=vol_level,
            is_weekend=is_weekend,
        )

    except Exception as e:
        logger.error(f"Error building market context: {e}", exc_info=True)
        return default_ctx


async def _get_streak(user) -> int:
    """Get user's current streak."""
    if not STREAK_AVAILABLE:
        return 0
    try:
        streak_obj, _ = await sync_to_async(UserStreak.objects.get_or_create)(user=user)
        return streak_obj.current_streak
    except Exception as e:
        logger.warning(f"Error getting streak: {e}")
        return 0


def _build_action_suggestion(portfolio: PortfolioSnapshot, market: MarketContext) -> ActionSuggestion:
    """Build action suggestion using the ritual action engine."""
    # Convert Pydantic models to dicts for the engine
    portfolio_data = {
        "has_portfolio": portfolio.has_portfolio,
        "total_value": portfolio.total_value,
        "holdings_count": portfolio.holdings_count,
        "holdings": [h.model_dump() for h in portfolio.top_holdings],
        "top_holding": portfolio.top_holdings[0].symbol if portfolio.top_holdings else "",
        "top_holding_pct": (
            (portfolio.top_holdings[0].current_price * portfolio.top_holdings[0].shares)
            / portfolio.total_value * 100
            if portfolio.top_holdings and portfolio.total_value > 0
            else 0
        ),
        "is_concentrated": False,
    }
    # Recompute concentration
    if portfolio_data["top_holding_pct"] > 40:
        portfolio_data["is_concentrated"] = True

    market_data = {
        "change_percent": market.sp500_change_percent,
        "volatility": 0.025 if market.volatility_level == "elevated" else 0.015,
        "sentiment": market.market_sentiment,
        "is_weekend": getattr(market, "is_weekend", False),
    }

    if ACTION_ENGINE_AVAILABLE:
        result = generate_ritual_action(portfolio_data, market_data)
    else:
        result = {
            "action_type": "no_action",
            "headline": "Portfolio aligned. No action needed today.",
            "detail": "Markets are calm and your positions are balanced.",
            "action_label": "Stay the course",
            "target_screen": None,
            "urgency": "low",
        }

    return ActionSuggestion(**result)


# ============================================================================
# Yodlee Sync (kept from original, runs as optional background step)
# ============================================================================

def _sync_yodlee_transactions(user) -> int:
    """Sync Yodlee transactions synchronously. Returns count of new transactions."""
    connections.close_all()

    if not YODLEE_AVAILABLE:
        return 0
    if os.getenv('USE_YODLEE', 'false').lower() != 'true':
        return 0

    try:
        yodlee = YodleeClient()
        user_id_str = str(user.id)
        bank_accounts = BankAccount.objects.filter(user=user)
        if not bank_accounts.exists():
            return 0

        to_date = datetime.now().date()
        from_date = to_date - timedelta(days=1)
        total_synced = 0

        for account in bank_accounts:
            if not account.yodlee_account_id:
                continue
            try:
                transactions = yodlee.get_transactions(
                    user_id_str,
                    account_id=account.yodlee_account_id,
                    from_date=from_date.strftime('%Y-%m-%d'),
                    to_date=to_date.strftime('%Y-%m-%d'),
                )
                for txn in transactions:
                    normalized = YodleeClient.normalize_transaction(txn)
                    _, created = BankTransaction.objects.update_or_create(
                        bank_account=account,
                        yodlee_transaction_id=normalized['yodlee_transaction_id'],
                        defaults={
                            'user': user,
                            'amount': normalized['amount'],
                            'currency': normalized['currency'],
                            'description': normalized['description'],
                            'merchant_name': normalized['merchant_name'],
                            'category': normalized['category'],
                            'subcategory': normalized['subcategory'],
                            'transaction_type': normalized['transaction_type'],
                            'posted_date': (
                                datetime.strptime(normalized['posted_date'], '%Y-%m-%d').date()
                                if normalized['posted_date'] else to_date
                            ),
                            'transaction_date': (
                                datetime.strptime(normalized['transaction_date'], '%Y-%m-%d').date()
                                if normalized['transaction_date'] else None
                            ),
                            'status': normalized['status'],
                            'raw_json': normalized['raw_json'],
                        }
                    )
                    if created:
                        total_synced += 1
            except Exception as e:
                logger.warning(f"Error syncing account {account.id}: {e}")
                continue

        logger.info(f"Synced {total_synced} transactions for dawn ritual")
        return total_synced
    except Exception as e:
        logger.error(f"Error in Yodlee sync: {e}")
        return 0


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/perform", response_model=RitualDawnResponse)
async def perform_dawn_ritual(
    request: DawnRitualRequest,
    user: User = Depends(get_current_user)
):
    """
    Perform the Ritual Dawn: portfolio snapshot, market context, action suggestion.
    Yodlee sync runs as optional background step.
    """
    try:
        import asyncio

        # Run portfolio, market, streak, and yodlee sync concurrently
        portfolio_task = _build_portfolio_snapshot(user)
        market_task = _build_market_context()
        streak_task = _get_streak(user)

        loop = asyncio.get_event_loop()
        yodlee_task = loop.run_in_executor(None, _sync_yodlee_transactions, user)

        portfolio, market, streak, transactions_synced = await asyncio.gather(
            portfolio_task, market_task, streak_task, yodlee_task,
            return_exceptions=False,
        )

        # Handle cases where gather returned exceptions
        if isinstance(portfolio, Exception):
            logger.error(f"Portfolio fetch error: {portfolio}")
            portfolio = PortfolioSnapshot(
                total_value=0, previous_total_value=0,
                change_dollars=0, change_percent=0,
                top_holdings=[], holdings_count=0, has_portfolio=False,
            )
        if isinstance(market, Exception):
            logger.error(f"Market fetch error: {market}")
            market = MarketContext(
                sp500_change_percent=0, sp500_direction="flat",
                market_sentiment="neutral", notable_indices=[],
                headline="Market data is currently unavailable.",
                volatility_level="moderate",
            )
        if isinstance(streak, Exception):
            streak = 0
        if isinstance(transactions_synced, Exception):
            transactions_synced = 0

        # Build action suggestion
        action = _build_action_suggestion(portfolio, market)

        # Pick greeting (time-aware if client sent client_hour)
        client_hour = getattr(request, "client_hour", None)
        g = _pick_greeting(streak, client_hour=client_hour)

        return RitualDawnResponse(
            greeting=g["greeting"],
            tagline=g["tagline"],
            greeting_key=g.get("key"),
            portfolio=portfolio,
            market=market,
            action=action,
            streak=streak,
            timestamp=datetime.now().isoformat(),
            transactionsSynced=transactions_synced,
            haiku=generate_haiku(transactions_synced),
        )

    except Exception as e:
        logger.error(f"Error performing Ritual Dawn: {e}", exc_info=True)
        # Fallback response
        return RitualDawnResponse(
            greeting="Good morning. Your money didn't sleep.",
            tagline="Let's see what changed overnight.",
            greeting_key=None,
            portfolio=PortfolioSnapshot(
                total_value=0, previous_total_value=0,
                change_dollars=0, change_percent=0,
                top_holdings=[], holdings_count=0, has_portfolio=False,
            ),
            market=MarketContext(
                sp500_change_percent=0, sp500_direction="flat",
                market_sentiment="neutral", notable_indices=[],
                headline="Market data is currently unavailable.",
                volatility_level="moderate",
                is_weekend=_is_weekend(),
            ),
            action=ActionSuggestion(
                action_type="no_action",
                headline="Start your day with awareness.",
                detail="Review your portfolio when you're ready.",
                action_label="Open portfolio",
                target_screen="portfolio-management",
                urgency="low",
            ),
            streak=0,
            timestamp=datetime.now().isoformat(),
            transactionsSynced=0,
            haiku=generate_haiku(0),
        )


@router.post("/complete")
async def complete_ritual_dawn(
    request: RitualDawnCompleteRequest,
    user: User = Depends(get_current_user)
):
    """Record the user's commitment action from Ritual Dawn."""
    try:
        logger.info(
            f"Ritual Dawn completed by user {user.id}: action_taken={request.action_taken}"
        )

        # Update streak
        streak = 0
        if STREAK_AVAILABLE:
            from django.utils import timezone
            streak_obj, _ = await sync_to_async(UserStreak.objects.get_or_create)(user=user)
            today = timezone.now().date()
            await sync_to_async(streak_obj.update_streak)(today)
            streak = streak_obj.current_streak

        # Persist completion for analytics, follow-through, and A/B (greeting_key)
        if RITUAL_COMPLETION_AVAILABLE and RitualDawnCompletion is not None:
            from django.utils import timezone
            today = timezone.now().date()
            defaults = {
                "action_taken": request.action_taken or "no_action",
                "greeting_key": (request.greeting_key or "")[:64],
            }
            await sync_to_async(RitualDawnCompletion.objects.update_or_create)(
                user=user,
                date=today,
                defaults=defaults,
            )

        return {
            "success": True,
            "action_taken": request.action_taken,
            "streak": streak,
        }
    except Exception as e:
        logger.error(f"Error completing Ritual Dawn: {e}")
        return {"success": False, "error": str(e)}


@router.post("/follow-through")
async def record_follow_through(
    request: RitualDawnFollowThroughRequest,
    user: User = Depends(get_current_user)
):
    """Record that the user opened the target screen (follow-through on ritual commitment)."""
    if not RITUAL_COMPLETION_AVAILABLE or RitualDawnCompletion is None:
        return {"success": False, "error": "Ritual completion not available"}

    try:
        from django.utils import timezone
        today = timezone.now().date()
        def _get_today_completion():
            return RitualDawnCompletion.objects.filter(user=user, date=today).first()

        completion = await sync_to_async(_get_today_completion)()
        if not completion or completion.followed_through_at:
            return {"success": True, "recorded": False}

        action_taken = (completion.action_taken or "").strip().lower()
        if action_taken in ("", "no_action"):
            return {"success": True, "recorded": False}

        target_screen = (request.target_screen or "").strip()
        params = request.target_params or {}

        # Match: e.g. target_screen "StockDetail" + params {"symbol": "AAPL"} vs action_taken "review aapl"
        if target_screen == "StockDetail" and params.get("symbol"):
            symbol = str(params.get("symbol", "")).upper()
            if symbol and (f"review {symbol.lower()}" in action_taken or symbol.lower() in action_taken):
                completion.followed_through_at = timezone.now()
                await sync_to_async(completion.save)()
                logger.info(f"Ritual Dawn follow-through: user {user.id} opened StockDetail for {symbol}")
                return {"success": True, "recorded": True}
        elif target_screen and target_screen.lower() in ("portfolio-management", "stocks"):
            if "allocation" in action_taken or "position" in action_taken or "portfolio" in action_taken:
                completion.followed_through_at = timezone.now()
                await sync_to_async(completion.save)()
                logger.info(f"Ritual Dawn follow-through: user {user.id} opened {target_screen}")
                return {"success": True, "recorded": True}

        return {"success": True, "recorded": False}
    except Exception as e:
        logger.error(f"Error recording Ritual Dawn follow-through: {e}")
        return {"success": False, "error": str(e)}
