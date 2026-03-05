"""
management/commands/generate_daily_brief.py
============================================
Django management command to generate and cache the daily AI market brief.

Usage
-----
    python manage.py generate_daily_brief
    python manage.py generate_daily_brief --regime Expansion
    python manage.py generate_daily_brief --no-llm          # template fallback only
    python manage.py generate_daily_brief --tickers AAPL MSFT NVDA

Schedule via cron or Celery beat at market open (e.g. 09:30 ET Mon–Fri):
    0 14 * * 1-5  /path/to/venv/bin/python manage.py generate_daily_brief

The brief is stored in Django's cache under the key 'daily_market_brief'
so the REST endpoint (api/market/brief/) can serve it instantly.
"""

from __future__ import annotations

import json
import logging

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate and cache the daily AI market brief (regime + top signals + LLM narrative)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--regime",
            type=str,
            default=None,
            help="Override the detected market regime (e.g. Expansion, Crisis).",
        )
        parser.add_argument(
            "--tickers",
            nargs="*",
            default=None,
            help="Optional list of tickers to score for top signals. "
                 "Defaults to a small representative universe.",
        )
        parser.add_argument(
            "--no-llm",
            action="store_true",
            dest="no_llm",
            help="Skip LLM synthesis; use template fallback only.",
        )
        parser.add_argument(
            "--max-bullish",
            type=int,
            default=5,
            dest="max_bullish",
            help="Max bullish tickers to include in brief (default 5).",
        )
        parser.add_argument(
            "--max-bearish",
            type=int,
            default=5,
            dest="max_bearish",
            help="Max bearish tickers to include in brief (default 5).",
        )
        parser.add_argument(
            "--cache-timeout",
            type=int,
            default=86400,
            dest="cache_timeout",
            help="Cache TTL in seconds (default 86400 = 24 hours).",
        )

    def handle(self, *args, **options):
        regime = options["regime"]
        tickers = options["tickers"]
        use_llm = not options["no_llm"]
        max_bullish = options["max_bullish"]
        max_bearish = options["max_bearish"]
        cache_timeout = options["cache_timeout"]

        self.stdout.write("Generating daily market brief …")

        # -----------------------------------------------------------------
        # 1. Detect regime if not supplied
        # -----------------------------------------------------------------
        if not regime:
            try:
                from core.ai_service import AIService
                indicators = AIService()._cached_regime_indicators()
                regime = (
                    indicators.get("regime", "Unknown")
                    if isinstance(indicators, dict)
                    else "Unknown"
                )
                self.stdout.write(f"  Detected regime: {regime}")
            except Exception as exc:
                logger.warning("Could not detect regime: %s", exc)
                regime = "Unknown"
                self.stdout.write(f"  Regime detection failed — using: {regime}")

        # -----------------------------------------------------------------
        # 2. Score a representative set of stocks for top signals
        # -----------------------------------------------------------------
        _DEFAULT_BRIEF_TICKERS = [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META",
            "TSLA", "JPM", "V", "XOM", "JNJ", "UNH", "SPY",
        ]
        brief_tickers = tickers or _DEFAULT_BRIEF_TICKERS
        top_signals = []
        try:
            from django.db.models import Q
            from core.models import Stock
            from core.ai_service import AIService

            stocks_qs = list(
                Stock.objects.filter(symbol__in=brief_tickers)
                .values("id", "symbol", "name", "beginner_friendly_score", "current_price")
            )
            if stocks_qs:
                ai_service = AIService()
                scored = ai_service.score_stocks_ml(stocks_qs, {}, {})
                for s in scored:
                    sig = s.get("signal_output") or {}
                    top_signals.append({
                        "symbol":     s.get("symbol"),
                        "signal":     sig.get("signal", "Neutral"),
                        "confidence": sig.get("confidence", "Low"),
                        "fss_score":  s.get("fss_score"),
                        "ml_score":   s.get("ml_score"),
                    })
                self.stdout.write(f"  Scored {len(top_signals)} tickers for brief")
        except Exception as exc:
            logger.warning("Could not score stocks for brief: %s", exc)
            self.stdout.write(f"  Warning: stock scoring failed ({exc}) — proceeding without signals")

        # -----------------------------------------------------------------
        # 3. Build brief
        # -----------------------------------------------------------------
        try:
            from core.daily_market_brief import build_daily_brief

            brief = build_daily_brief(
                regime=regime,
                top_signals=top_signals or None,
                max_bullish=max_bullish,
                max_bearish=max_bearish,
                use_llm=use_llm,
            )
        except Exception as exc:
            raise CommandError(f"Failed to build daily brief: {exc}") from exc

        # -----------------------------------------------------------------
        # 4. Cache the brief
        # -----------------------------------------------------------------
        brief_dict = {
            "regime":       brief.regime,
            "top_bullish":  brief.top_bullish,
            "top_bearish":  brief.top_bearish,
            "narrative":    brief.narrative,
            "generated_at": brief.generated_at,
        }
        try:
            from django.core.cache import cache
            cache.set("daily_market_brief", brief_dict, timeout=cache_timeout)
            self.stdout.write(f"  Cached under 'daily_market_brief' (TTL {cache_timeout}s)")
        except Exception as exc:
            logger.warning("Cache write failed: %s — brief generated but not cached", exc)

        self.stdout.write(self.style.SUCCESS(
            f"\nDaily brief generated ✓\n"
            f"  Regime:      {brief.regime}\n"
            f"  Bullish:     {', '.join(brief.top_bullish) or 'none'}\n"
            f"  Bearish:     {', '.join(brief.top_bearish) or 'none'}\n"
            f"  Narrative:   {brief.narrative[:120]}{'…' if len(brief.narrative) > 120 else ''}\n"
            f"  Generated:   {brief.generated_at}"
        ))
