#!/usr/bin/env python3
"""
Simple script to populate the database with stock data
"""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_production')
django.setup()

from core.models import Stock

def populate_stocks():
    """Populate database with real stock data"""
    
    # Real stock data that matches the ML/AI backend expectations
    real_stocks = [
        {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'current_price': 175.50,
            'market_cap': 2800000000000,
            'pe_ratio': 28.5,
            'dividend_yield': 0.44,
            'beginner_friendly_score': 90
        },
        {
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'sector': 'Technology',
            'current_price': 380.25,
            'market_cap': 2800000000000,
            'pe_ratio': 32.1,
            'dividend_yield': 0.68,
            'beginner_friendly_score': 85
        },
        {
            'symbol': 'TSLA',
            'company_name': 'Tesla, Inc.',
            'sector': 'Automotive',
            'current_price': 250.75,
            'market_cap': 800000000000,
            'pe_ratio': 45.2,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 60
        },
        {
            'symbol': 'NVDA',
            'company_name': 'NVIDIA Corporation',
            'sector': 'Technology',
            'current_price': 450.30,
            'market_cap': 1100000000000,
            'pe_ratio': 65.8,
            'dividend_yield': 0.04,
            'beginner_friendly_score': 70
        },
        {
            'symbol': 'GOOGL',
            'company_name': 'Alphabet Inc.',
            'sector': 'Technology',
            'current_price': 140.85,
            'market_cap': 1800000000000,
            'pe_ratio': 24.3,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 80
        },
        {
            'symbol': 'AMZN',
            'company_name': 'Amazon.com Inc.',
            'sector': 'Consumer Discretionary',
            'current_price': 188.45,
            'market_cap': 1900000000000,
            'pe_ratio': 52.1,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 75
        },
        {
            'symbol': 'META',
            'company_name': 'Meta Platforms Inc.',
            'sector': 'Technology',
            'current_price': 485.20,
            'market_cap': 1200000000000,
            'pe_ratio': 22.8,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 65
        },
        {
            'symbol': 'NFLX',
            'company_name': 'Netflix Inc.',
            'sector': 'Communication Services',
            'current_price': 425.15,
            'market_cap': 190000000000,
            'pe_ratio': 35.2,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 70
        }
    ]
    
    try:
        # Clear existing stocks and add new ones
        print(f"Clearing existing stocks...")
        Stock.objects.all().delete()
        
        print(f"Adding {len(real_stocks)} stocks to database...")
        for stock_data in real_stocks:
            stock = Stock.objects.create(**stock_data)
            print(f"Added: {stock.symbol} - {stock.company_name} (${stock.current_price})")
        
        print(f"Successfully populated database with {len(real_stocks)} real stocks")
        print(f"Total stocks in database: {Stock.objects.count()}")
        
    except Exception as e:
        print(f"Error populating database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    populate_stocks()
