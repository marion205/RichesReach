"""
Django management command to create test portfolio data for user 2
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Portfolio, Stock
from decimal import Decimal

User = get_user_model()

# Test portfolio data matching the frontend mock data
TEST_HOLDINGS = [
    {'symbol': 'AAPL', 'shares': 10, 'average_price': 150.00, 'current_price': 180.00, 'portfolio_name': 'Main Portfolio'},
    {'symbol': 'MSFT', 'shares': 8, 'average_price': 230.00, 'current_price': 320.00, 'portfolio_name': 'Main Portfolio'},
    {'symbol': 'GOOGL', 'shares': 5, 'average_price': 120.00, 'current_price': 140.00, 'portfolio_name': 'Main Portfolio'},
    {'symbol': 'SPY', 'shares': 15, 'average_price': 380.00, 'current_price': 420.00, 'portfolio_name': 'Main Portfolio'},
    {'symbol': 'AMZN', 'shares': 4, 'average_price': 130.00, 'current_price': 150.00, 'portfolio_name': 'Main Portfolio'},
    {'symbol': 'TSLA', 'shares': 6, 'average_price': 200.00, 'current_price': 250.00, 'portfolio_name': 'Main Portfolio'},
    {'symbol': 'NVDA', 'shares': 3, 'average_price': 400.00, 'current_price': 500.00, 'portfolio_name': 'Main Portfolio'},
]


class Command(BaseCommand):
    help = 'Create test portfolio data for user 2 (test@example.com)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            default=2,
            help='User ID to create portfolio for (default: 2)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing holdings before creating new ones',
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        clear_existing = options['clear']
        
        try:
            # Get user
            user = User.objects.filter(id=user_id).first()
            if not user:
                self.stdout.write(
                    self.style.ERROR(f'❌ User with id={user_id} not found')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Found user: {user.email} (id={user.id})')
            )
            
            # Delete existing holdings if requested
            if clear_existing:
                existing_count = Portfolio.objects.filter(user=user).count()
                if existing_count > 0:
                    self.stdout.write(f'🗑️  Deleting {existing_count} existing holdings...')
                    Portfolio.objects.filter(user=user).delete()
            
            created_count = 0
            updated_count = 0
            
            for holding_data in TEST_HOLDINGS:
                symbol = holding_data['symbol']
                
                # Get or create the stock
                stock, stock_created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'name': f'{symbol} Inc.',  # Placeholder name
                        'exchange': 'NASDAQ' if symbol != 'SPY' else 'NYSE',
                    }
                )
                
                if stock_created:
                    self.stdout.write(f'  📈 Created stock: {symbol}')
                
                # Create portfolio holding
                portfolio_name = holding_data['portfolio_name']
                notes = f'portfolio:{portfolio_name}'
                
                portfolio_item, created = Portfolio.objects.get_or_create(
                    user=user,
                    stock=stock,
                    defaults={
                        'shares': holding_data['shares'],
                        'average_price': Decimal(str(holding_data['average_price'])),
                        'current_price': Decimal(str(holding_data['current_price'])),
                        'notes': notes,
                    }
                )
                
                if created:
                    created_count += 1
                    total_value = holding_data['shares'] * holding_data['current_price']
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Created: {symbol} - {holding_data["shares"]} shares @ '
                            f'${holding_data["current_price"]:.2f} = ${total_value:.2f}'
                        )
                    )
                else:
                    # Update existing
                    portfolio_item.shares = holding_data['shares']
                    portfolio_item.average_price = Decimal(str(holding_data['average_price']))
                    portfolio_item.current_price = Decimal(str(holding_data['current_price']))
                    portfolio_item.notes = notes
                    portfolio_item.save()
                    updated_count += 1
                    total_value = holding_data['shares'] * holding_data['current_price']
                    self.stdout.write(
                        self.style.WARNING(
                            f'  🔄 Updated: {symbol} - {holding_data["shares"]} shares @ '
                            f'${holding_data["current_price"]:.2f} = ${total_value:.2f}'
                        )
                    )
            
            # Calculate total portfolio value
            total_value = sum(h['shares'] * h['current_price'] for h in TEST_HOLDINGS)
            
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Successfully created {created_count} and updated {updated_count} portfolio holdings'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(f'💰 Total portfolio value: ${total_value:,.2f}')
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'📊 Holdings: {", ".join([h["symbol"] for h in TEST_HOLDINGS])}'
                )
            )
            self.stdout.write('')
            self.stdout.write('Next steps:')
            self.stdout.write('1. Refresh the Portfolio screen in the app')
            self.stdout.write('2. The Portfolio Risk Metrics card should now show data')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating test portfolio: {e}')
            )
            import traceback
            traceback.print_exc()

