"""
Management command to seed mock order and position data for testing the Order Monitoring Dashboard.

Usage:
    python manage.py seed_mock_orders
    python manage.py seed_mock_orders --reset  # Delete existing orders/positions first
    python manage.py seed_mock_orders --user-email user@example.com  # For specific user
    python manage.py seed_mock_orders --count 20  # Number of orders to create
"""
from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
import uuid

from core.broker_models import BrokerAccount, BrokerOrder, BrokerPosition
from core.raha_models import RAHASignal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed mock broker order and position data for UI testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing orders and positions before seeding'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to create orders for (defaults to first user or creates test user)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Number of orders to create (default: 15)'
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        user_email = options.get('user_email')
        count = options.get('count', 15)

        with transaction.atomic():
            # Get or create user
            if user_email:
                user, created = User.objects.get_or_create(
                    email=user_email,
                    defaults={'name': user_email.split('@')[0]}
                )
            else:
                user = User.objects.first()
                if not user:
                    user = User.objects.create_user(
                        email='test@example.com',
                        name='Test User'
                    )

            self.stdout.write(self.style.SUCCESS(f'Using user: {user.email}'))

            # Get or create broker account
            broker_account, created = BrokerAccount.objects.get_or_create(
                user=user,
                defaults={
                    'alpaca_account_id': f'ALPACA_{uuid.uuid4().hex[:8]}',
                    'kyc_status': 'APPROVED',
                    'status': 'OPEN',
                    'buying_power': Decimal('50000.00'),
                    'cash': Decimal('50000.00'),
                    'equity': Decimal('50000.00'),
                    'day_trading_buying_power': Decimal('100000.00'),
                    'pattern_day_trader': False,
                    'day_trade_count': 0,
                    'trading_blocked': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created broker account for {user.email}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Using existing broker account'))

            # Reset if requested
            if reset:
                deleted_orders = BrokerOrder.objects.filter(broker_account=broker_account).delete()[0]
                deleted_positions = BrokerPosition.objects.filter(broker_account=broker_account).delete()[0]
                self.stdout.write(self.style.WARNING(f'Deleted {deleted_orders} orders and {deleted_positions} positions'))

            # Get some RAHA signals to link to orders (if any exist)
            raha_signals = list(RAHASignal.objects.filter(user=user)[:10])
            signal_index = 0

            # Popular symbols for trading
            symbols = ['AAPL', 'TSLA', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'NFLX', 'AMD', 'SPY']

            # Order statuses with realistic distribution
            status_weights = {
                'FILLED': 0.6,  # 60% filled
                'PARTIALLY_FILLED': 0.1,  # 10% partially filled
                'PENDING_NEW': 0.1,  # 10% pending
                'CANCELED': 0.1,  # 10% canceled
                'REJECTED': 0.05,  # 5% rejected
                'ACCEPTED': 0.05,  # 5% accepted
            }
            statuses = []
            for status, weight in status_weights.items():
                statuses.extend([status] * int(weight * 100))

            # Create orders
            orders_created = 0
            now = timezone.now()

            for i in range(count):
                symbol = random.choice(symbols)
                side = random.choice(['BUY', 'SELL'])
                order_type = random.choice(['MARKET', 'LIMIT', 'STOP'])
                status = random.choice(statuses)
                
                # Base price for the symbol (mock prices)
                base_prices = {
                    'AAPL': 180.0, 'TSLA': 250.0, 'MSFT': 380.0, 'NVDA': 500.0,
                    'AMZN': 150.0, 'GOOGL': 140.0, 'META': 350.0, 'NFLX': 450.0,
                    'AMD': 120.0, 'SPY': 450.0
                }
                base_price = base_prices.get(symbol, 100.0)
                
                # Add some variation
                price_variation = random.uniform(-0.05, 0.05)  # ±5%
                current_price = Decimal(str(base_price * (1 + price_variation))).quantize(Decimal('0.01'))
                
                quantity = random.randint(1, 100)
                notional = current_price * quantity
                
                # Set limit/stop prices if needed
                limit_price = None
                stop_price = None
                if order_type in ['LIMIT', 'STOP_LIMIT']:
                    if side == 'BUY':
                        limit_price = current_price * Decimal('0.99')  # 1% below
                    else:
                        limit_price = current_price * Decimal('1.01')  # 1% above
                if order_type in ['STOP', 'STOP_LIMIT']:
                    if side == 'BUY':
                        stop_price = current_price * Decimal('1.01')  # 1% above
                    else:
                        stop_price = current_price * Decimal('0.99')  # 1% below

                # Fill details for filled/partially filled orders
                filled_qty = 0
                filled_avg_price = None
                filled_at = None
                if status in ['FILLED', 'PARTIALLY_FILLED']:
                    if status == 'FILLED':
                        filled_qty = quantity
                    else:
                        # For partially filled, ensure we have at least 1 and less than quantity
                        if quantity > 1:
                            filled_qty = random.randint(1, quantity - 1)
                        else:
                            filled_qty = 1  # If quantity is 1, treat as filled
                            status = 'FILLED'
                    filled_avg_price = current_price + Decimal(str(random.uniform(-0.02, 0.02))).quantize(Decimal('0.01'))
                    filled_at = now - timedelta(minutes=random.randint(1, 60))

                # Timestamps
                created_at = now - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
                submitted_at = created_at + timedelta(seconds=random.randint(1, 30))
                
                # Link to RAHA signal for some orders (auto-trades)
                raha_signal = None
                source = 'MANUAL'
                if random.random() < 0.4 and raha_signals:  # 40% are auto-trades
                    raha_signal = raha_signals[signal_index % len(raha_signals)]
                    signal_index += 1
                    source = 'RAHA_AUTO'

                # Guardrail checks
                guardrail_passed = status not in ['REJECTED']
                guardrail_reason = None
                if not guardrail_passed:
                    guardrail_reason = random.choice([
                        'Insufficient buying power',
                        'Position size exceeds limit',
                        'Day trading limit reached',
                    ])

                order = BrokerOrder.objects.create(
                    broker_account=broker_account,
                    client_order_id=f'ORDER_{uuid.uuid4().hex[:12]}',
                    alpaca_order_id=f'ALP_{uuid.uuid4().hex[:10]}' if status != 'REJECTED' else None,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    time_in_force=random.choice(['DAY', 'GTC', 'IOC']),
                    quantity=quantity,
                    notional=notional,
                    limit_price=limit_price,
                    stop_price=stop_price,
                    status=status,
                    filled_qty=filled_qty,
                    filled_avg_price=filled_avg_price,
                    guardrail_checks_passed=guardrail_passed,
                    guardrail_reject_reason=guardrail_reason,
                    rejection_reason=guardrail_reason if status == 'REJECTED' else None,
                    source=source,
                    raha_signal=raha_signal,
                    created_at=created_at,
                    submitted_at=submitted_at,
                    filled_at=filled_at,
                )

                orders_created += 1

            self.stdout.write(self.style.SUCCESS(f'Created {orders_created} orders'))

            # Create positions (for filled buy orders)
            filled_buy_orders = BrokerOrder.objects.filter(
                broker_account=broker_account,
                side='BUY',
                status__in=['FILLED', 'PARTIALLY_FILLED']
            )

            positions_created = 0
            position_symbols = set()

            for order in filled_buy_orders[:5]:  # Create up to 5 positions
                if order.symbol in position_symbols:
                    continue  # One position per symbol
                
                position_symbols.add(order.symbol)
                
                # Calculate position details
                qty = order.filled_qty or order.quantity
                avg_entry = order.filled_avg_price or order.limit_price or current_price
                
                # Current price (slightly different from entry)
                price_change = random.uniform(-0.10, 0.15)  # -10% to +15%
                current_price = (avg_entry * Decimal(str(1 + price_change))).quantize(Decimal('0.01'))
                
                cost_basis = avg_entry * qty
                market_value = current_price * qty
                unrealized_pl = market_value - cost_basis
                # unrealized_plpc is stored as decimal (0.15 = 15%), not percentage
                unrealized_plpc = (unrealized_pl / cost_basis) if cost_basis > 0 else Decimal('0')
                # Ensure it's within valid range for the field
                unrealized_plpc = max(Decimal('-0.9999'), min(Decimal('0.9999'), unrealized_plpc))

                BrokerPosition.objects.update_or_create(
                    broker_account=broker_account,
                    symbol=order.symbol,
                    defaults={
                        'qty': qty,
                        'avg_entry_price': avg_entry,
                        'current_price': current_price,
                        'market_value': market_value,
                        'cost_basis': cost_basis,
                        'unrealized_pl': unrealized_pl,
                        'unrealized_plpc': unrealized_plpc,
                        'last_synced_at': now,
                    }
                )
                positions_created += 1

            self.stdout.write(self.style.SUCCESS(f'Created/updated {positions_created} positions'))

            # Update broker account equity based on positions
            total_unrealized_pl = BrokerPosition.objects.filter(
                broker_account=broker_account
            ).aggregate(
                total=models.Sum('unrealized_pl')
            )['total'] or Decimal('0')

            broker_account.equity = broker_account.cash + total_unrealized_pl
            broker_account.save()

            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Successfully seeded mock order data:\n'
                f'   - {orders_created} orders\n'
                f'   - {positions_created} positions\n'
                f'   - Account equity: ${broker_account.equity:,.2f}\n'
                f'   - Unrealized P&L: ${total_unrealized_pl:+,.2f}'
            ))

