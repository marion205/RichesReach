"""
management/commands/run_earnings_sprint.py
==========================================
Idempotent earnings data fetch — runs the Alpha Vantage earnings sprint,
fetching up to 25 uncached tickers per run (free tier limit).

Run once per day until the full universe is cached (~4 days for 78 tickers,
~8 days for the 200-ticker expanded universe).

Usage
-----
    python manage.py run_earnings_sprint
    python manage.py run_earnings_sprint --max 25
    python manage.py run_earnings_sprint --max 500   # paid key (500 req/day)
    python manage.py run_earnings_sprint --status    # show cache coverage, don't fetch

Schedule (free tier — run once per day at off-peak hours):
    0 6 * * *  /path/to/venv/bin/python manage.py run_earnings_sprint

Or via Celery beat (see settings.CELERY_BEAT_SCHEDULE key 'earnings-sprint-daily').

Exit codes
----------
0  — completed successfully (even if some tickers failed)
1  — ALPHAVANTAGE_API_KEY not set
"""

from __future__ import annotations

import logging
import os

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Fetch up to N uncached earnings records from Alpha Vantage (25/day free). "
        "Idempotent — already-cached tickers are skipped automatically."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--max",
            type=int,
            default=25,
            dest="max_per_run",
            help="Max API requests this run (default 25 for free tier; 500 for paid).",
        )
        parser.add_argument(
            "--start",
            type=str,
            default="2010-01-01",
            help="Start date for earnings filter (default 2010-01-01).",
        )
        parser.add_argument(
            "--end",
            type=str,
            default="2026-12-31",
            help="End date for earnings filter (default 2026-12-31).",
        )
        parser.add_argument(
            "--status",
            action="store_true",
            help="Print cache coverage and exit without fetching.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.5,
            dest="sleep_between_requests",
            help="Seconds between API calls (default 0.5, courtesy delay).",
        )
        parser.add_argument(
            "--auto-retrain",
            action="store_true",
            dest="auto_retrain",
            help=(
                "If the full universe becomes cached after this run, automatically "
                "trigger a model retrain via the retrain_production_model command."
            ),
        )

    def handle(self, *args, **options):
        from core.ml.earnings_loader import get_cached_tickers, run_earnings_sprint
        from core.ml.train import DEFAULT_TICKERS

        tickers = DEFAULT_TICKERS
        cached = get_cached_tickers()
        total = len(tickers)
        already_cached = len([t for t in tickers if t.upper() in cached])

        # ------------------------------------------------------------------
        # --status: just report coverage and exit
        # ------------------------------------------------------------------
        if options["status"]:
            remaining = total - already_cached
            self.stdout.write(
                f"Earnings cache coverage: {already_cached}/{total} tickers "
                f"({already_cached/total*100:.0f}%). "
                f"Remaining: {remaining}."
            )
            if remaining == 0:
                self.stdout.write(self.style.SUCCESS("Full universe cached. Ready to retrain."))
            else:
                self.stdout.write(
                    f"Run 'python manage.py run_earnings_sprint' once per day "
                    f"for ~{-(-remaining // options['max_per_run'])} more day(s)."
                )
            return

        # ------------------------------------------------------------------
        # Check API key
        # ------------------------------------------------------------------
        key = os.getenv("ALPHAVANTAGE_API_KEY") or os.getenv("ALPHA_VANTAGE_KEY")
        if not key:
            raise CommandError(
                "ALPHAVANTAGE_API_KEY is not set. "
                "Add it to your .env file and re-run.\n"
                "Free tier: https://www.alphavantage.co/support/#api-key"
            )

        max_per_run = options["max_per_run"]
        self.stdout.write(
            f"Starting earnings sprint: {already_cached}/{total} already cached. "
            f"Fetching up to {max_per_run} more …"
        )

        # ------------------------------------------------------------------
        # Run sprint
        # ------------------------------------------------------------------
        result = run_earnings_sprint(
            tickers=tickers,
            max_per_run=max_per_run,
            start_date=options["start"],
            end_date=options["end"],
            use_cache=True,
            sleep_between_requests=options["sleep_between_requests"],
        )

        fetched = result["fetched"]
        ok      = result["ok"]
        failed  = result["failed"]
        remaining = result["remaining"]
        cached_total = result["cached_total"]

        self.stdout.write(
            self.style.SUCCESS(
                f"\nEarnings sprint complete:\n"
                f"  Fetched this run : {fetched} tickers\n"
                f"  OK               : {ok}\n"
                f"  Failed / no data : {failed}\n"
                f"  Total cached     : {cached_total}/{total} ({cached_total/total*100:.0f}%)\n"
                f"  Still remaining  : {remaining}"
            )
        )

        if remaining > 0:
            days_left = -(-remaining // max_per_run)
            self.stdout.write(
                f"\nRun again tomorrow ({days_left} more day(s) to full coverage)."
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nFull universe cached! Run 'python manage.py retrain_production_model' "
                    "to retrain with earnings coverage."
                )
            )
            # Optional auto-retrain
            if options["auto_retrain"]:
                self.stdout.write("\nAuto-retrain triggered …")
                from django.core.management import call_command
                call_command("retrain_production_model")
