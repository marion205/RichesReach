"""
management/commands/retrain_production_model.py
================================================
Runs the full walk-forward ML training pipeline and saves the new model to
ml_models/production_r2.pkl.

This command should be run:
  - After full earnings cache coverage (python manage.py run_earnings_sprint --status)
  - Monthly as a scheduled Celery beat task
  - On-demand after significant universe or feature changes

Usage
-----
    python manage.py retrain_production_model
    python manage.py retrain_production_model --n-splits 4
    python manage.py retrain_production_model --tickers AAPL MSFT NVDA
    python manage.py retrain_production_model --start-date 2018-01-01

Output
------
Prints fold-by-fold metrics (R², IC, decile spread, hit rate) and saves the
model + feature schema to ml_models/production_r2.pkl.

Duration
--------
~10–30 minutes depending on universe size and hardware.
With 78 tickers and 4 folds: ~12 minutes on an M1 Mac.
With 200 tickers and 6 folds: ~35 minutes.
"""

from __future__ import annotations

import logging
import time

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Run the full walk-forward ML training pipeline. "
        "Saves production_r2.pkl with updated fold_ics, regime_ic, and xs_normalization stats."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tickers",
            nargs="*",
            default=None,
            help="Override ticker universe (default: DEFAULT_TICKERS from train.py, 200+ names).",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            default="2019-01-01",
            dest="start_date",
            help="Start of training window (default 2019-01-01).",
        )
        parser.add_argument(
            "--n-splits",
            type=int,
            default=6,
            dest="n_splits",
            help="Number of walk-forward folds (default 6).",
        )
        parser.add_argument(
            "--horizon",
            type=int,
            default=20,
            help="Forward-return horizon in trading days (default 20 ≈ 1 month).",
        )
        parser.add_argument(
            "--no-save",
            action="store_true",
            dest="no_save",
            help="Dry-run: train but do not overwrite production_r2.pkl.",
        )
        parser.add_argument(
            "--notify-brief",
            action="store_true",
            dest="notify_brief",
            help=(
                "After successful retrain, regenerate the daily market brief cache "
                "so the brief reflects the new model's signals immediately."
            ),
        )

    def handle(self, *args, **options):
        tickers    = options["tickers"]
        start_date = options["start_date"]
        n_splits   = options["n_splits"]
        horizon    = options["horizon"]
        save_model = not options["no_save"]
        notify     = options["notify_brief"]

        self.stdout.write(
            f"Starting ML retrain: "
            f"tickers={'DEFAULT (' + str(_count_default()) + ')' if not tickers else len(tickers)}, "
            f"start={start_date}, n_splits={n_splits}, horizon={horizon}, "
            f"save={save_model}"
        )

        t0 = time.time()
        try:
            from core.ml.train import run_pipeline

            fold_metrics, model = run_pipeline(
                tickers=tickers,
                start_date=start_date,
                n_splits=n_splits,
                horizon=horizon,
                save_model=save_model,
                vol_adjust=True,
            )

        except ImportError as exc:
            raise CommandError(
                f"LightGBM or a required ML dependency is missing: {exc}\n"
                "Run: pip install lightgbm scikit-learn"
            ) from exc
        except Exception as exc:
            raise CommandError(f"Training pipeline failed: {exc}") from exc

        elapsed = time.time() - t0

        # Print results
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Walk-Forward Results")
        self.stdout.write("=" * 60)
        try:
            self.stdout.write(
                fold_metrics[["r2", "ic", "decile_spread", "hit_rate"]]
                .to_string(float_format="{:.4f}".format)
            )
        except Exception:
            self.stdout.write(str(fold_metrics))

        if "mean" in fold_metrics.index:
            mean_ic = fold_metrics.loc["mean", "ic"]
            mean_r2 = fold_metrics.loc["mean", "r2"]
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nRetrain complete in {elapsed/60:.1f} min.\n"
                    f"  Mean IC : {mean_ic:.4f}  "
                    f"({'above' if mean_ic >= 0.02 else 'below'} 0.02 bar)\n"
                    f"  Mean R² : {mean_r2:.4f}\n"
                    f"  Model saved : {'production_r2.pkl' if save_model else 'NOT SAVED (--no-save)'}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Retrain complete in {elapsed/60:.1f} min.")
            )

        # Optional: regenerate daily brief after retrain
        if notify and save_model:
            self.stdout.write("\nRegenerating daily brief cache with new model signals …")
            try:
                from django.core.management import call_command
                call_command("generate_daily_brief")
            except Exception as exc:
                self.stdout.write(
                    self.style.WARNING(f"Brief regeneration failed (non-fatal): {exc}")
                )


def _count_default() -> int:
    try:
        from core.ml.train import DEFAULT_TICKERS
        return len(DEFAULT_TICKERS)
    except Exception:
        return 0
