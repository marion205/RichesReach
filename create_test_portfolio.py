#!/usr/bin/env python3
"""
Script to create test portfolio data for user 2 (test@example.com)
This matches the mock data shown in the frontend
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

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

def create_test_portfolio():
    """Create test portfolio holdings for user 2"""
    try:
        # Get user 2
        user = User.objects.filter(id=2).first()
        if not user:
            print(f"❌ User with id=2 not found")
            return False
        
        print(f"✅ Found user: {user.email} (id={user.id})")
        
        # Delete existing holdings for this user (clean slate)
        existing_count = Portfolio.objects.filter(user=user).count()
        if existing_count > 0:
            print(f"🗑️  Deleting {existing_count} existing holdings...")
            Portfolio.objects.filter(user=user).delete()
        
        created_count = 0
        skipped_count = 0
        
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
                print(f"  📈 Created stock: {symbol}")
            
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
                print(f"  ✅ Created: {symbol} - {holding_data['shares']} shares @ ${holding_data['current_price']:.2f} = ${total_value:.2f}")
            else:
                # Update existing
                portfolio_item.shares = holding_data['shares']
                portfolio_item.average_price = Decimal(str(holding_data['average_price']))
                portfolio_item.current_price = Decimal(str(holding_data['current_price']))
                portfolio_item.notes = notes
                portfolio_item.save()
                created_count += 1
                total_value = holding_data['shares'] * holding_data['current_price']
                print(f"  🔄 Updated: {symbol} - {holding_data['shares']} shares @ ${holding_data['current_price']:.2f} = ${total_value:.2f}")
        
        # Calculate total portfolio value
        total_value = sum(h['shares'] * h['current_price'] for h in TEST_HOLDINGS)
        
        print(f"\n✅ Successfully created/updated {created_count} portfolio holdings")
        print(f"💰 Total portfolio value: ${total_value:,.2f}")
        print(f"📊 Holdings: {', '.join([h['symbol'] for h in TEST_HOLDINGS])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test portfolio: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Creating Test Portfolio Data for User 2")
    print("=" * 60)
    print()
    
    success = create_test_portfolio()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Test portfolio created successfully!")
        print("\nNext steps:")
        print("1. Refresh the Portfolio screen in the app")
        print("2. The Portfolio Risk Metrics card should now show data")
    else:
        print("❌ Failed to create test portfolio")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

