"""
Management command to create sample performance data for testing ML training.
This is useful when you have signals but no performance data yet.

Usage:
    python manage.py create_sample_performance_data --count 50
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
import logging

from core.signal_performance_models import DayTradingSignal, SignalPerformance

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create sample performance data for day trading signals (for testing ML training)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of performance records to create (default: 50)'
        )
        parser.add_argument(
            '--horizon',
            type=str,
            default='EOD',
            choices=['30m', '2h', 'EOD', '1d', '2d'],
            help='Horizon to create performance for (default: EOD)'
        )
        parser.add_argument(
            '--win-rate',
            type=float,
            default=0.55,
            help='Target win rate for sample data (default: 0.55)'
        )

    def handle(self, *args, **options):
        count = options['count']
        horizon = options['horizon']
        win_rate = options['win_rate']
        
        self.stdout.write(f"📊 Creating {count} sample performance records ({horizon} horizon, {win_rate:.1%} win rate)...")
        
        # Get signals without performance data
        signals = DayTradingSignal.objects.filter(
            performance__isnull=True
        ).order_by('-generated_at')[:count]
        
        if signals.count() < count:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Only {signals.count()} signals without performance data found (requested {count})"
            ))
        
        created = 0
        wins = 0
        losses = 0
        
        for signal in signals:
            try:
                # Determine if this should be a win (based on win_rate)
                is_win = random.random() < win_rate
                
                # Calculate realistic PnL
                entry_price = float(signal.entry_price)
                stop_price = float(signal.stop_price)
                
                if is_win:
                    # Win: hit target or positive return
                    if signal.target_prices and len(signal.target_prices) > 0:
                        target_price = float(signal.target_prices[0])
                        pnl_pct = (target_price - entry_price) / entry_price if signal.side == 'LONG' else (entry_price - target_price) / entry_price
                        hit_target_1 = True
                        hit_stop = False
                    else:
                        # Positive return but no target hit
                        pnl_pct = random.uniform(0.005, 0.03)  # 0.5% to 3% gain
                        hit_target_1 = False
                        hit_stop = False
                    outcome = 'WIN'
                    wins += 1
                else:
                    # Loss: hit stop or negative return
                    pnl_pct = (stop_price - entry_price) / entry_price if signal.side == 'LONG' else (entry_price - stop_price) / entry_price
                    # Make it a loss (negative)
                    pnl_pct = -abs(pnl_pct) * random.uniform(0.8, 1.2)  # 80-120% of stop distance
                    hit_target_1 = False
                    hit_stop = True
                    outcome = 'LOSS'
                    losses += 1
                
                # Calculate price at horizon
                if signal.side == 'LONG':
                    price_at_horizon = entry_price * (1 + pnl_pct)
                else:
                    price_at_horizon = entry_price * (1 - pnl_pct)
                
                # Calculate PnL in dollars (assuming 100 shares)
                shares = signal.suggested_size_shares or 100
                pnl_dollars = abs(pnl_pct) * entry_price * shares
                if pnl_pct < 0:
                    pnl_dollars = -pnl_dollars
                
                # Create performance record
                perf, created_flag = SignalPerformance.objects.update_or_create(
                    signal=signal,
                    horizon=horizon,
                    defaults={
                        'evaluated_at': timezone.now(),
                        'price_at_horizon': Decimal(str(price_at_horizon)),
                        'pnl_dollars': Decimal(str(pnl_dollars)),
                        'pnl_percent': Decimal(str(pnl_pct)),
                        'hit_stop': hit_stop,
                        'hit_target_1': hit_target_1,
                        'hit_target_2': False,
                        'hit_time_stop': False,
                        'outcome': outcome,
                        'max_favorable_excursion': Decimal(str(abs(pnl_pct) * 1.2)) if is_win else Decimal('0'),
                        'max_adverse_excursion': Decimal(str(abs(pnl_pct) * 0.8)) if not is_win else Decimal('0'),
                    }
                )
                
                if created_flag:
                    created += 1
                    logger.debug(f"✅ Created {horizon} performance for {signal.symbol} ({outcome}, {pnl_pct:.2%})")
                
            except Exception as e:
                logger.error(f"Error creating performance for {signal.symbol}: {e}")
                continue
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Created {created} performance records"
        ))
        self.stdout.write(f"   Wins: {wins} ({wins/max(created,1):.1%})")
        self.stdout.write(f"   Losses: {losses} ({losses/max(created,1):.1%})")
        self.stdout.write(f"\n💡 Now you can retrain the ML model:")
        self.stdout.write(f"   python manage.py retrain_day_trading_ml --days 365 --force")

