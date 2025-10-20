#!/usr/bin/env python3
"""
Setup local database with production schema and test data
"""

import os
import sys
import django

# Add the backend directory to the path
sys.path.append('/Users/marioncollins/RichesReach/backend/backend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from core.models import IncomeProfile, Portfolio, Watchlist, Stock
from decimal import Decimal
import json

User = get_user_model()

def setup_test_user():
    """Create or update test user with complete profile"""
    print("🔧 Setting up test user...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='Test@example.com',
        defaults={
            'username': 'Test',
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True,
        }
    )
    
    if created:
        user.set_password('password123')
        user.save()
    
    if created:
        print(f"✅ Created new test user: {user.email}")
    else:
        print(f"✅ Found existing test user: {user.email}")
    
    # Create or update income profile
    profile, profile_created = IncomeProfile.objects.get_or_create(
        user=user,
        defaults={
            'age': 30,
            'income_bracket': '50000-75000',
            'investment_goals': ['retirement', 'wealth_building'],
            'investment_horizon': '10-20_years',
            'risk_tolerance': 'moderate',
        }
    )
    
    if profile_created:
        print(f"✅ Created user profile for {user.email}")
    else:
        print(f"✅ Updated user profile for {user.email}")
    
    return user, profile

def setup_sample_stocks():
    """Create sample stocks"""
    print("📊 Setting up sample stocks...")
    
    sample_stocks = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'sector': 'Technology'},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'sector': 'Automotive'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'sector': 'Technology'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'sector': 'Consumer Discretionary'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'sector': 'Technology'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'sector': 'Technology'},
    ]
    
    created_count = 0
    for stock_data in sample_stocks:
        stock, created = Stock.objects.get_or_create(
            symbol=stock_data['symbol'],
            defaults=stock_data
        )
        if created:
            created_count += 1
    
    print(f"✅ Created {created_count} new stocks")

def setup_sample_portfolio(user):
    """Create sample portfolio for test user"""
    print("💼 Setting up sample portfolio...")
    
    portfolio, created = Portfolio.objects.get_or_create(
        user=user,
        name='My Portfolio',
        defaults={
            'description': 'Test portfolio with sample holdings',
            'is_primary': True,
        }
    )
    
    if created:
        print(f"✅ Created portfolio: {portfolio.name}")
    else:
        print(f"✅ Found existing portfolio: {portfolio.name}")
    
    return portfolio

def setup_sample_watchlist(user):
    """Create sample watchlist for test user"""
    print("👀 Setting up sample watchlist...")
    
    watchlist, created = Watchlist.objects.get_or_create(
        user=user,
        name='My Watchlist',
        defaults={
            'description': 'Stocks I\'m watching',
        }
    )
    
    if created:
        print(f"✅ Created watchlist: {watchlist.name}")
    else:
        print(f"✅ Found existing watchlist: {watchlist.name}")
    
    return watchlist

def main():
    print("🚀 Setting up local database with production schema and test data...")
    print("=" * 60)
    
    try:
        # Setup test user and profile
        user, profile = setup_test_user()
        
        # Setup sample data
        setup_sample_stocks()
        setup_sample_portfolio(user)
        setup_sample_watchlist(user)
        
        print("\n" + "=" * 60)
        print("✅ Database setup complete!")
        print(f"📧 Test user: {user.email}")
        print(f"👤 Username: {user.username}")
        print(f"🔑 Password: password123")
        print(f"📊 Profile: Age {profile.age}, Risk: {profile.risk_tolerance}")
        print("\n🌐 You can now test the mobile app with this user account.")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
