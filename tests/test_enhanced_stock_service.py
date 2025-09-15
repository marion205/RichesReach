#!/usr/bin/env python3
"""
Test Enhanced Stock Service
Verifies real-time stock price functionality
"""
import os
import sys
import asyncio
import django
from pathlib import Path
# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()
async def test_enhanced_stock_service():
"""Test the enhanced stock service"""
print(" Testing Enhanced Stock Service")
print("=" * 50)
try:
from core.enhanced_stock_service import enhanced_stock_service
# Test symbols
test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
print(f" Testing real-time prices for: {', '.join(test_symbols)}")
# Get real-time prices
prices = await enhanced_stock_service.get_multiple_prices(test_symbols)
print("\n Price Results:")
print("-" * 30)
for symbol in test_symbols:
price_data = prices.get(symbol)
if price_data:
print(f" {symbol}: ${price_data['price']:.2f} ({price_data.get('change_percent', '0%')})")
print(f" Source: {price_data.get('source', 'unknown')}")
print(f" Verified: {price_data.get('verified', False)}")
print(f" Last Updated: {price_data.get('last_updated', 'unknown')}")
print()
else:
print(f" {symbol}: No price data available")
print()
# Test individual price
print(" Testing individual price for AAPL:")
aapl_price = await enhanced_stock_service.get_real_time_price('AAPL')
if aapl_price:
print(f" Price: ${aapl_price['price']:.2f}")
print(f" Source: {aapl_price.get('source', 'unknown')}")
print(f" Verified: {aapl_price.get('verified', False)}")
else:
print(" No price data for AAPL")
# Test price summary
print("\n Testing price summary for AAPL:")
summary = await enhanced_stock_service.get_price_summary('AAPL')
print(f" Summary: {summary}")
print("\n Enhanced Stock Service Test Complete!")
except Exception as e:
print(f" Error testing enhanced stock service: {e}")
import traceback
traceback.print_exc()
def test_sync_functions():
"""Test synchronous functions"""
print("\n Testing Synchronous Functions")
print("=" * 50)
try:
from core.enhanced_stock_service import enhanced_stock_service
# Test database price
print(" Testing database price retrieval:")
db_price = enhanced_stock_service._get_database_price('AAPL')
if db_price:
print(f" Database price: ${db_price['price']:.2f}")
else:
print(" No database price available")
# Test cache functions
print("\n Testing cache functions:")
test_data = {
'symbol': 'TEST',
'price': 100.0,
'source': 'test',
'verified': True,
'last_updated': '2024-01-01T00:00:00'
}
# Set cache
success = enhanced_stock_service._cache_price('TEST', test_data)
print(f" Cache set: {'' if success else ''}")
# Get cache
cached = enhanced_stock_service._get_cached_price('TEST')
print(f" Cache get: {'' if cached else ''}")
# Check expiration
expired = enhanced_stock_service._is_cache_expired(test_data)
print(f" Cache expired: {'' if expired else ''}")
print("\n Synchronous Functions Test Complete!")
except Exception as e:
print(f" Error testing synchronous functions: {e}")
import traceback
traceback.print_exc()
def main():
"""Main test function"""
print(" Enhanced Stock Service Test Suite")
print("=" * 60)
# Test synchronous functions
test_sync_functions()
# Test async functions
asyncio.run(test_enhanced_stock_service())
print("\n" + "=" * 60)
print(" All tests completed!")
if __name__ == "__main__":
main()
