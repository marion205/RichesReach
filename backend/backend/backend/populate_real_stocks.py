#!/usr/bin/env python3
"""
Script to populate the database with real stock data using the existing API services
"""
import os
import sys
import django
import asyncio
from decimal import Decimal

# Setup Django
sys.path.append('/Users/marioncollins/RichesReach/backend/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import Stock
from core.market_data_api_service import MarketDataAPIService, DataProvider
from core.enhanced_stock_service import EnhancedStockService

# API Keys
ALPHA_VANTAGE_API_KEY = "OHYSFF1AE446O7CR"
FINNHUB_API_KEY = "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"

# Popular stocks to populate
POPULAR_STOCKS = [
    {'symbol': 'AAPL', 'company_name': 'Apple Inc.', 'sector': 'Technology'},
    {'symbol': 'MSFT', 'company_name': 'Microsoft Corporation', 'sector': 'Technology'},
    {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc.', 'sector': 'Communication Services'},
    {'symbol': 'TSLA', 'company_name': 'Tesla, Inc.', 'sector': 'Automotive'},
    {'symbol': 'AMZN', 'company_name': 'Amazon.com, Inc.', 'sector': 'Consumer Discretionary'},
    {'symbol': 'META', 'company_name': 'Meta Platforms, Inc.', 'sector': 'Communication Services'},
    {'symbol': 'NVDA', 'company_name': 'NVIDIA Corporation', 'sector': 'Technology'},
    {'symbol': 'JPM', 'company_name': 'JPMorgan Chase & Co.', 'sector': 'Financial Services'},
    {'symbol': 'JNJ', 'company_name': 'Johnson & Johnson', 'sector': 'Healthcare'},
    {'symbol': 'PG', 'company_name': 'Procter & Gamble Co.', 'sector': 'Consumer Staples'},
    {'symbol': 'V', 'company_name': 'Visa Inc.', 'sector': 'Financial Services'},
    {'symbol': 'MA', 'company_name': 'Mastercard Inc.', 'sector': 'Financial Services'},
    {'symbol': 'HD', 'company_name': 'Home Depot, Inc.', 'sector': 'Consumer Discretionary'},
    {'symbol': 'UNH', 'company_name': 'UnitedHealth Group Inc.', 'sector': 'Healthcare'},
    {'symbol': 'BAC', 'company_name': 'Bank of America Corp.', 'sector': 'Financial Services'},
]

# Beginner-friendly scores (based on stability, dividend history, volatility)
BEGINNER_SCORES = {
    'AAPL': 85, 'MSFT': 82, 'GOOGL': 78, 'TSLA': 65, 'AMZN': 72,
    'META': 68, 'NVDA': 58, 'JPM': 88, 'JNJ': 92, 'PG': 90,
    'V': 80, 'MA': 82, 'HD': 75, 'UNH': 85, 'BAC': 70
}

# Dividend scores (based on dividend history and yield)
DIVIDEND_SCORES = {
    'AAPL': 65, 'MSFT': 78, 'GOOGL': 0, 'TSLA': 0, 'AMZN': 0,
    'META': 0, 'NVDA': 25, 'JPM': 85, 'JNJ': 95, 'PG': 92,
    'V': 0, 'MA': 0, 'HD': 70, 'UNH': 75, 'BAC': 80
}

async def populate_stocks():
    """Populate database with real stock data"""
    print("🚀 Starting stock data population...")
    
    # Initialize the enhanced stock service
    enhanced_service = EnhancedStockService()
    
    for stock_data in POPULAR_STOCKS:
        symbol = stock_data['symbol']
        print(f"\n📊 Processing {symbol}...")
        
        try:
            # Get real-time price data
            price_data = await enhanced_service.get_real_time_price(symbol)
            
            if price_data and price_data.get('price'):
                current_price = Decimal(str(price_data['price']))
                print(f"   💰 Current price: ${current_price}")
                
                # Create or update stock record
                stock, created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'company_name': stock_data['company_name'],
                        'sector': stock_data['sector'],
                        'current_price': current_price,
                        'beginner_friendly_score': BEGINNER_SCORES.get(symbol, 70),
                        'dividend_score': DIVIDEND_SCORES.get(symbol, 0),
                        'market_cap': None,  # Will be populated by API if available
                        'pe_ratio': None,    # Will be populated by API if available
                        'dividend_yield': None,  # Will be populated by API if available
                    }
                )
                
                if not created:
                    # Update existing stock
                    stock.current_price = current_price
                    stock.beginner_friendly_score = BEGINNER_SCORES.get(symbol, 70)
                    stock.dividend_score = DIVIDEND_SCORES.get(symbol, 0)
                    stock.save()
                    print(f"   ✅ Updated {symbol}")
                else:
                    print(f"   ✅ Created {symbol}")
                    
            else:
                print(f"   ⚠️  No price data available for {symbol}, creating with basic info")
                # Create stock with basic info even if no price data
                stock, created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'company_name': stock_data['company_name'],
                        'sector': stock_data['sector'],
                        'beginner_friendly_score': BEGINNER_SCORES.get(symbol, 70),
                        'dividend_score': DIVIDEND_SCORES.get(symbol, 0),
                    }
                )
                if created:
                    print(f"   ✅ Created {symbol} with basic info")
                    
        except Exception as e:
            print(f"   ❌ Error processing {symbol}: {e}")
            # Still create the stock with basic info
            try:
                stock, created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'company_name': stock_data['company_name'],
                        'sector': stock_data['sector'],
                        'beginner_friendly_score': BEGINNER_SCORES.get(symbol, 70),
                        'dividend_score': DIVIDEND_SCORES.get(symbol, 0),
                    }
                )
                if created:
                    print(f"   ✅ Created {symbol} with basic info (fallback)")
            except Exception as e2:
                print(f"   ❌ Failed to create {symbol}: {e2}")
    
    print(f"\n🎉 Stock population complete!")
    print(f"📈 Total stocks in database: {Stock.objects.count()}")
    
    # Show beginner-friendly stocks
    beginner_stocks = Stock.objects.filter(beginner_friendly_score__gte=80).order_by('-beginner_friendly_score')
    print(f"\n🌟 Beginner-friendly stocks (score >= 80):")
    for stock in beginner_stocks:
        print(f"   {stock.symbol}: {stock.beginner_friendly_score}% (${stock.current_price or 'N/A'})")

if __name__ == "__main__":
    asyncio.run(populate_stocks())
