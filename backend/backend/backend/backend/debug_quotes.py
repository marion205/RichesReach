#!/usr/bin/env python3
"""
Debug script to test quote fetching logic
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/marioncollins/RichesReach/backend/backend/backend/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_dev')
django.setup()

# Now import Django modules
from core.views_market import _fetch_quote_finnhub, _normalize_finnhub_quote, _fetch_quote_polygon, _normalize_polygon_quote
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_quote_fetching():
    """Test the quote fetching process"""
    symbol = "AAPL"
    
    print(f"=== Testing Quote Fetching for {symbol} ===")
    
    # Test Finnhub
    try:
        print("\n1. Testing Finnhub...")
        finnhub_data = _fetch_quote_finnhub(symbol)
        print(f"Raw Finnhub data: {finnhub_data}")
        
        normalized = _normalize_finnhub_quote(symbol, finnhub_data)
        print(f"Normalized Finnhub: {normalized}")
        
        if normalized['price'] > 0:
            print("✅ Finnhub working correctly")
        else:
            print("❌ Finnhub returned zero price")
            
    except Exception as e:
        print(f"❌ Finnhub failed: {e}")
    
    # Test Polygon
    try:
        print("\n2. Testing Polygon...")
        polygon_data = _fetch_quote_polygon(symbol)
        print(f"Raw Polygon data: {polygon_data}")
        
        normalized = _normalize_polygon_quote(symbol, polygon_data)
        print(f"Normalized Polygon: {normalized}")
        
        if normalized['price'] > 0:
            print("✅ Polygon working correctly")
        else:
            print("❌ Polygon returned zero price")
            
    except Exception as e:
        print(f"❌ Polygon failed: {e}")

if __name__ == "__main__":
    test_quote_fetching()
