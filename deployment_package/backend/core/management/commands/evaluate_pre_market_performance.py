"""
Django management command to evaluate pre-market pick performance
Records outcomes for ML learning
Usage: python manage.py evaluate_pre_market_performance
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.pre_market_ml_learner import get_ml_learner
from core.signal_performance_models import DayTradingSignal, SignalPerformance
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Evaluate pre-market pick performance and record outcomes for ML learning'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days back to evaluate (default: 1)'
        )
        parser.add_argument(
            '--symbol',
            type=str,
            help='Evaluate specific symbol only'
        )

    def handle(self, *args, **options):
        days_back = options['days']
        symbol_filter = options.get('symbol')
        
        self.stdout.write(self.style.SUCCESS("📊 Evaluating Pre-Market Performance"))
        self.stdout.write(f"Looking back {days_back} day(s)")
        self.stdout.write("")
        
        # Get signals from the last N days
        cutoff_date = timezone.now() - timedelta(days=days_back)
        
        query = Q(created_at__gte=cutoff_date)
        if symbol_filter:
            query &= Q(symbol=symbol_filter)
        
        signals = DayTradingSignal.objects.filter(query).order_by('-created_at')
        
        if not signals.exists():
            self.stdout.write(self.style.WARNING("⚠️  No signals found in the specified period"))
            return
        
        self.stdout.write(f"Found {signals.count()} signal(s) to evaluate")
        self.stdout.write("")
        
        ml_learner = get_ml_learner()
        evaluated_count = 0
        
        for signal in signals:
            # Get performance data
            performances = SignalPerformance.objects.filter(signal=signal)
            
            if not performances.exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠️  No performance data for {signal.symbol} (signal ID: {signal.id})")
                )
                continue
            
            # Use EOD performance if available, otherwise use latest
            eod_perf = performances.filter(horizon='EOD').first()
            if not eod_perf:
                eod_perf = performances.order_by('-evaluated_at').first()
            
            # Reconstruct original pick data (simplified - in production, store this)
            pick_data = {
                'symbol': signal.symbol,
                'side': signal.side,
                'pre_market_price': float(signal.entry_price) if hasattr(signal, 'entry_price') else 0,
                'pre_market_change_pct': 0,  # Would need to store this
                'volume': 0,  # Would need to store this
                'market_cap': 0,  # Would need to store this
                'prev_close': 0,  # Would need to store this
            }
            
            # Create outcome dict
            outcome = {
                'success': eod_perf.outcome in ['WIN', 'TARGET_HIT'],
                'return_pct': float(eod_perf.pnl_percent),
                'hit_target': eod_perf.hit_target_1 or eod_perf.hit_target_2,
                'hit_stop': eod_perf.hit_stop,
                'max_favorable': float(eod_perf.max_favorable_excursion) if eod_perf.max_favorable_excursion else 0,
                'max_adverse': float(eod_perf.max_adverse_excursion) if eod_perf.max_adverse_excursion else 0,
            }
            
            # Record outcome for ML learning
            ml_learner.record_pick_outcome(pick_data, outcome)
            evaluated_count += 1
            
            self.stdout.write(
                f"✅ {signal.symbol}: "
                f"{'✅ WIN' if outcome['success'] else '❌ LOSS'} "
                f"({outcome['return_pct']:+.2f}%)"
            )
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"✅ Evaluated {evaluated_count} signal(s)"))
        self.stdout.write("")
        self.stdout.write("💡 Run 'python manage.py pre_market_scan_with_alerts --train-ml' to train the model")

