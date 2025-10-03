#!/usr/bin/env python3
"""
Add sample stocks to the database for testing the ML algorithms
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import Stock, User

def add_sample_stocks():
    """Add sample stocks to the database"""
    
    # Sample stocks data
    sample_stocks = [
        {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'current_price': 150.0,
            'market_cap': 2800000000000,  # $2.8T
            'pe_ratio': 28.5,
            'dividend_yield': 0.0044,  # 0.44%
            'beginner_friendly_score': 67
        },
        {
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'sector': 'Technology',
            'current_price': 300.0,
            'market_cap': 2200000000000,  # $2.2T
            'pe_ratio': 25.0,
            'dividend_yield': 0.007,  # 0.7%
            'beginner_friendly_score': 72
        },
        {
            'symbol': 'TSLA',
            'company_name': 'Tesla, Inc.',
            'sector': 'Automotive',
            'current_price': 200.0,
            'market_cap': 800000000000,  # $800B
            'pe_ratio': 65.2,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 45
        },
        {
            'symbol': 'JNJ',
            'company_name': 'Johnson & Johnson',
            'sector': 'Healthcare',
            'current_price': 160.0,
            'market_cap': 420000000000,  # $420B
            'pe_ratio': 15.0,
            'dividend_yield': 0.03,  # 3%
            'beginner_friendly_score': 85
        },
        {
            'symbol': 'PG',
            'company_name': 'Procter & Gamble Co.',
            'sector': 'Consumer Defensive',
            'current_price': 140.0,
            'market_cap': 350000000000,  # $350B
            'pe_ratio': 22.0,
            'dividend_yield': 0.025,  # 2.5%
            'beginner_friendly_score': 78
        },
        {
            'symbol': 'KO',
            'company_name': 'The Coca-Cola Company',
            'sector': 'Consumer Defensive',
            'current_price': 60.0,
            'market_cap': 260000000000,  # $260B
            'pe_ratio': 20.0,
            'dividend_yield': 0.03,  # 3%
            'beginner_friendly_score': 82
        },
        {
            'symbol': 'NVDA',
            'company_name': 'NVIDIA Corporation',
            'sector': 'Technology',
            'current_price': 400.0,
            'market_cap': 1000000000000,  # $1T
            'pe_ratio': 45.0,
            'dividend_yield': 0.001,  # 0.1%
            'beginner_friendly_score': 55
        },
        {
            'symbol': 'AMZN',
            'company_name': 'Amazon.com, Inc.',
            'sector': 'Consumer Cyclical',
            'current_price': 120.0,
            'market_cap': 1200000000000,  # $1.2T
            'pe_ratio': 35.0,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 60
        }
    ]
    
    print("🔄 Adding sample stocks to database...")
    
    # Clear existing stocks
    Stock.objects.all().delete()
    print("✅ Cleared existing stocks")
    
    # Add sample stocks
    for stock_data in sample_stocks:
        stock, created = Stock.objects.get_or_create(
            symbol=stock_data['symbol'],
            defaults=stock_data
        )
        if created:
            print(f"✅ Added {stock.symbol} - {stock.company_name}")
        else:
            print(f"⚠️  {stock.symbol} already exists")
    
    # Create a default user if none exists
    user, created = User.objects.get_or_create(
        username='ml_default',
        defaults={
            'email': 'ml@default.com',
            'first_name': 'ML',
            'last_name': 'Default'
        }
    )
    if created:
        print("✅ Created default ML user")
    else:
        print("✅ Default ML user already exists")
    
    print(f"\n🎉 Database setup complete!")
    print(f"📊 Total stocks: {Stock.objects.count()}")
    print(f"👤 Total users: {User.objects.count()}")

if __name__ == '__main__':
    add_sample_stocks()
