"""
Management command to seed mock RAHA signals for testing The Whisper screen.

Usage:
    python manage.py seed_mock_raha_signals
    python manage.py seed_mock_raha_signals --symbol SPY
    python manage.py seed_mock_raha_signals --reset  # Delete existing signals first
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from core.raha_models import StrategyVersion, RAHASignal, UserStrategySettings

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed mock RAHA signals for UI testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing signals before seeding'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to create signals for (defaults to first user or creates test user)'
        )
        parser.add_argument(
            '--symbol',
            type=str,
            default='SPY',
            help='Symbol to create signals for (default: SPY)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of signals to create (default: 3)'
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        user_email = options.get('user_email')
        symbol = options.get('symbol', 'SPY')
        count = options.get('count', 3)
        
        # Get or create user
        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ User with email {user_email} not found'))
                return
        else:
            # Get first user or create test user
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.WARNING('⚠️  No users found. Creating test user...'))
                user = User.objects.create_user(
                    email='test@richesreach.com',
                    username='testuser',
                    password='testpass123'
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created test user: {user.email}'))
        
        # Get strategy versions
        strategy_versions = list(StrategyVersion.objects.all())
        if not strategy_versions:
            self.stdout.write(self.style.ERROR('❌ No strategy versions found. Run seed_raha_strategies first.'))
            return
        
        # Enable at least one strategy for the user
        enabled_strategy = None
        for strategy_version in strategy_versions:
            settings, created = UserStrategySettings.objects.get_or_create(
                user=user,
                strategy_version=strategy_version,
                defaults={
                    'enabled': True,
                    'parameters': {'risk_per_trade': 0.01},
                }
            )
            if created or not settings.enabled:
                settings.enabled = True
                settings.save()
                enabled_strategy = strategy_version
                self.stdout.write(self.style.SUCCESS(f'✅ Enabled strategy: {strategy_version.strategy.name}'))
                break
        
        if not enabled_strategy:
            # Enable the first one
            enabled_strategy = strategy_versions[0]
            settings, _ = UserStrategySettings.objects.get_or_create(
                user=user,
                strategy_version=enabled_strategy,
                defaults={'enabled': True}
            )
            settings.enabled = True
            settings.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Enabled strategy: {enabled_strategy.strategy.name}'))
        
        if reset:
            self.stdout.write(self.style.WARNING('🗑️  Deleting existing signals...'))
            RAHASignal.objects.filter(user=user, symbol=symbol).delete()
            self.stdout.write(self.style.SUCCESS('✅ Deleted existing signals'))
        
        self.stdout.write(self.style.SUCCESS(f'\n🌱 Seeding {count} mock RAHA signals for {symbol}...\n'))
        
        # Get current price (mock - in real app this would come from market data)
        base_price = random.uniform(400, 500) if symbol == 'SPY' else random.uniform(100, 200)
        
        with transaction.atomic():
            for i in range(count):
                # Generate realistic signal data
                signal_type = random.choice(['ENTRY_LONG', 'ENTRY_SHORT'])
                is_long = signal_type == 'ENTRY_LONG'
                
                # Entry price (slightly above/below base for realism)
                entry_price = base_price + random.uniform(-2, 2)
                
                # Calculate stop loss and take profit based on ATR-like logic
                atr_multiplier = random.uniform(1.5, 3.0)
                price_range = base_price * 0.01 * atr_multiplier  # ~1-3% of price
                
                if is_long:
                    stop_loss = entry_price - price_range
                    take_profit = entry_price + (price_range * random.uniform(1.5, 3.0))  # 1.5-3R target
                else:
                    stop_loss = entry_price + price_range
                    take_profit = entry_price - (price_range * random.uniform(1.5, 3.0))
                
                # Confidence score (higher for better setups)
                confidence_score = random.uniform(0.55, 0.85)
                
                # Calculate R-multiple for expectancy
                if is_long:
                    risk = entry_price - stop_loss
                    reward = take_profit - entry_price
                else:
                    risk = stop_loss - entry_price
                    reward = entry_price - take_profit
                
                r_multiple = reward / risk if risk > 0 else 0
                
                # Meta data
                meta = {
                    'atr_multiplier': round(atr_multiplier, 2),
                    'r_multiple': round(r_multiple, 2),
                    'risk': round(risk, 2),
                    'reward': round(reward, 2),
                    'setup_type': random.choice(['breakout', 'reversal', 'momentum']),
                    'volume_confirmation': random.choice([True, False]),
                }
                
                # Create signal
                signal = RAHASignal.objects.create(
                    user=user,
                    strategy_version=enabled_strategy,
                    symbol=symbol,
                    timestamp=timezone.now() - timedelta(minutes=random.randint(0, 30)),
                    timeframe='5m',
                    signal_type=signal_type,
                    price=Decimal(str(round(entry_price, 2))),
                    stop_loss=Decimal(str(round(stop_loss, 2))),
                    take_profit=Decimal(str(round(take_profit, 2))),
                    confidence_score=Decimal(str(round(confidence_score, 4))),
                    meta=meta,
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ Created: {signal_type} on {symbol} @ ${entry_price:.2f} '
                        f'(SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}) '
                        f'Confidence: {confidence_score*100:.1f}%'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {count} mock signals!\n'))
        self.stdout.write(
            self.style.SUCCESS(
                f'📱 View them in The Whisper screen for {symbol}'
            )
        )

