"""
Management command to seed mock training data for ML model training.

This creates:
1. DayTradingSignal records
2. RAHASignal records linked to them
3. SignalPerformance records with realistic P&L data

Usage:
    python manage.py seed_ml_training_data --count 100
    python manage.py seed_ml_training_data --symbol AAPL --count 50
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
import uuid

from core.raha_models import StrategyVersion, RAHASignal, UserStrategySettings
from core.signal_performance_models import DayTradingSignal, SignalPerformance

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed mock training data for ML model training'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of training samples to create (default: 100)'
        )
        parser.add_argument(
            '--symbol',
            type=str,
            default=None,
            help='Symbol to create data for (default: random symbols)'
        )
        parser.add_argument(
            '--strategy-version-id',
            type=str,
            default=None,
            help='Strategy version ID to use (default: first enabled strategy)'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to create data for (defaults to first user or creates test user)'
        )

    def handle(self, *args, **options):
        count = options.get('count', 100)
        symbol = options.get('symbol')
        strategy_version_id = options.get('strategy_version_id')
        user_email = options.get('user_email')
        
        # Get or create user
        if user_email:
            user, _ = User.objects.get_or_create(
                email=user_email,
                defaults={'name': user_email.split('@')[0]}
            )
        else:
            user = User.objects.first()
            if not user:
                user = User.objects.create(
                    email='test@example.com',
                    name='Test User'
                )
        
        # Get strategy version
        if strategy_version_id:
            try:
                strategy_version = StrategyVersion.objects.get(id=strategy_version_id)
            except StrategyVersion.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Strategy version {strategy_version_id} not found'))
                return
        else:
            # Get first enabled strategy
            settings = UserStrategySettings.objects.filter(user=user, enabled=True).first()
            if settings:
                strategy_version = settings.strategy_version
            else:
                # Get any enabled strategy
                strategy_version = StrategyVersion.objects.filter(strategy__enabled=True).first()
                if not strategy_version:
                    self.stdout.write(self.style.ERROR('No enabled strategies found'))
                    return
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'SPY', 'QQQ'] if not symbol else [symbol]
        
        self.stdout.write(f'Creating {count} training samples for user {user.email}...')
        
        created = 0
        start_date = timezone.now() - timedelta(days=90)
        
        with transaction.atomic():
            for i in range(count):
                try:
                    # Random symbol if not specified
                    signal_symbol = random.choice(symbols)
                    
                    # Random date within lookback period
                    days_ago = random.randint(0, 90)
                    signal_time = start_date + timedelta(days=days_ago, hours=random.randint(9, 15), minutes=random.randint(0, 59))
                    
                    # Random entry price
                    base_price = random.uniform(50, 500)
                    entry_price = Decimal(str(round(base_price, 2)))
                    stop_loss = Decimal(str(round(base_price * random.uniform(0.95, 0.99), 2)))
                    take_profit = Decimal(str(round(base_price * random.uniform(1.01, 1.05), 2)))
                    
                    # Create DayTradingSignal
                    day_signal = DayTradingSignal.objects.create(
                        signal_id=uuid.uuid4(),
                        generated_at=signal_time,
                        mode=random.choice(['SAFE', 'AGGRESSIVE']),
                        universe_source='CORE',
                        symbol=signal_symbol,
                        side=random.choice(['LONG', 'SHORT']),
                        features={
                            'momentum15m': random.uniform(-2, 2),
                            'rvol10m': random.uniform(0.5, 2.0),
                            'vwapDist': random.uniform(-0.05, 0.05),
                        },
                        score=Decimal(str(random.uniform(5, 10))),
                        entry_price=entry_price,
                        stop_price=stop_loss,
                        target_prices=[str(take_profit)],
                        time_stop_minutes=240,
                        atr_5m=Decimal(str(random.uniform(0.5, 2.0))),
                        suggested_size_shares=100,
                        risk_per_trade_pct=Decimal('0.005'),
                        notes='Mock signal for ML training'
                    )
                    
                    # Create RAHASignal linked to DayTradingSignal
                    raha_signal = RAHASignal.objects.create(
                        user=user,
                        strategy_version=strategy_version,
                        symbol=signal_symbol,
                        timestamp=signal_time,
                        timeframe='5m',
                        signal_type='ENTRY_LONG' if day_signal.side == 'LONG' else 'ENTRY_SHORT',
                        price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        confidence_score=Decimal(str(random.uniform(0.5, 0.9))),
                        day_trading_signal=day_signal,
                        meta={}
                    )
                    
                    # Create SignalPerformance with realistic outcomes
                    # 60% win rate for training
                    is_win = random.random() < 0.6
                    
                    if is_win:
                        # Winning trade
                        pnl_percent = Decimal(str(random.uniform(0.5, 3.0)))
                        outcome = random.choice(['WIN', 'TARGET_HIT'])
                        hit_target_1 = True
                        hit_stop = False
                    else:
                        # Losing trade
                        pnl_percent = Decimal(str(random.uniform(-3.0, -0.5)))
                        outcome = random.choice(['LOSS', 'STOP_HIT'])
                        hit_target_1 = False
                        hit_stop = random.random() < 0.7  # 70% hit stop
                    
                    pnl_dollars = pnl_percent * entry_price * day_signal.suggested_size_shares / 100
                    price_at_horizon = entry_price + (entry_price * pnl_percent / 100)
                    
                    SignalPerformance.objects.create(
                        signal=day_signal,
                        horizon='2h',  # Use 2h horizon for training
                        evaluated_at=signal_time + timedelta(hours=2),
                        price_at_horizon=price_at_horizon,
                        pnl_dollars=pnl_dollars,
                        pnl_percent=pnl_percent,
                        hit_stop=hit_stop,
                        hit_target_1=hit_target_1,
                        hit_target_2=False,
                        hit_time_stop=False,
                        outcome=outcome,
                        max_favorable_excursion=Decimal(str(abs(float(pnl_percent)) * 1.2)) if is_win else Decimal('0'),
                        max_adverse_excursion=Decimal(str(abs(float(pnl_percent)) * 0.8)) if not is_win else Decimal('0'),
                    )
                    
                    created += 1
                    
                    if (i + 1) % 10 == 0:
                        self.stdout.write(f'  Created {i + 1}/{count} samples...')
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating sample {i+1}: {e}'))
                    continue
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Created {created} training samples'
        ))
        self.stdout.write(f'   Strategy: {strategy_version.strategy.name}')
        self.stdout.write(f'   User: {user.email}')
        self.stdout.write(f'\n💡 You can now train an ML model from the ML Training screen!')

