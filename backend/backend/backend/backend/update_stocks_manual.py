#!/usr/bin/env python3
"""
Manual script to update stocks with real-time data
"""
import os
import sys
import django
import requests
import time
from decimal import Decimal

# Setup Django
sys.path.append('/Users/marioncollins/RichesReach/backend/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import Stock

# API Keys
ALPHA_VANTAGE_API_KEY = "OHYSFF1AE446O7CR"
FINNHUB_API_KEY = "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"

def get_alpha_vantage_quote(symbol):
    """Get stock quote from Alpha Vantage"""
    try:
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'Global Quote' in data:
            quote = data['Global Quote']
            return {
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                'volume': int(quote.get('06. volume', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'open': float(quote.get('02. open', 0)),
                'source': 'alpha_vantage'
            }
    except Exception as e:
        print(f"Alpha Vantage error for {symbol}: {e}")
    
    return None

def get_finnhub_quote(symbol):
    """Get stock quote from Finnhub"""
    try:
        url = f"https://finnhub.io/api/v1/quote"
        params = {
            'symbol': symbol,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'c' in data and data['c'] > 0:  # c = current price
            return {
                'price': float(data.get('c', 0)),
                'change': float(data.get('d', 0)),  # d = change
                'change_percent': float(data.get('dp', 0)),  # dp = change percent
                'volume': int(data.get('v', 0)),  # v = volume
                'high': float(data.get('h', 0)),  # h = high
                'low': float(data.get('l', 0)),   # l = low
                'open': float(data.get('o', 0)),  # o = open
                'source': 'finnhub'
            }
    except Exception as e:
        print(f"Finnhub error for {symbol}: {e}")
    
    return None

def update_stock_price(symbol):
    """Update a single stock with real-time price"""
    print(f"📊 Updating {symbol}...")
    
    # Try Finnhub first (more reliable)
    price_data = get_finnhub_quote(symbol)
    
    # Fallback to Alpha Vantage
    if not price_data:
        price_data = get_alpha_vantage_quote(symbol)
    
    if price_data and price_data.get('price', 0) > 0:
        try:
            stock = Stock.objects.get(symbol=symbol)
            stock.current_price = Decimal(str(price_data['price']))
            stock.save()
            print(f"   ✅ {symbol}: ${price_data['price']} ({price_data['source']})")
            return True
        except Stock.DoesNotExist:
            print(f"   ❌ Stock {symbol} not found in database")
            return False
    else:
        print(f"   ❌ No price data available for {symbol}")
        return False

def update_all_stocks():
    """Update all stocks with real-time prices"""
    print("🚀 Starting real-time stock price update...")
    
    stocks = Stock.objects.all()
    updated = 0
    failed = 0
    
    for stock in stocks:
        try:
            success = update_stock_price(stock.symbol)
            if success:
                updated += 1
            else:
                failed += 1
            
            # Rate limiting delay
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error updating {stock.symbol}: {e}")
            failed += 1
    
    print(f"\n🎉 Update complete: {updated}/{stocks.count()} stocks updated")
    return {'updated': updated, 'failed': failed, 'total': stocks.count()}

def update_priority_stocks():
    """Update priority stocks only"""
    print("🚀 Updating priority stocks...")
    
    priority_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'JPM', 'JNJ', 'PG']
    updated = 0
    failed = 0
    
    for symbol in priority_symbols:
        try:
            success = update_stock_price(symbol)
            if success:
                updated += 1
            else:
                failed += 1
            
            # Rate limiting delay
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error updating {symbol}: {e}")
            failed += 1
    
    print(f"\n🎉 Priority update complete: {updated}/{len(priority_symbols)} stocks updated")
    return {'updated': updated, 'failed': failed, 'total': len(priority_symbols)}

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--priority':
            update_priority_stocks()
        elif sys.argv[1] == '--all':
            update_all_stocks()
        else:
            # Update specific symbol
            update_stock_price(sys.argv[1])
    else:
        # Default: update priority stocks
        update_priority_stocks()
