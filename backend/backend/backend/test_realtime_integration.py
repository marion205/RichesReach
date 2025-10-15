#!/usr/bin/env python3
"""
Test script for real-time data integration
"""
import os
import sys
import asyncio
import django

# Setup Django
sys.path.append('/Users/marioncollins/RichesReach/backend/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.realtime_data_service import realtime_data_service
from core.models import Stock

async def test_realtime_integration():
    """Test the real-time data integration"""
    print("🚀 Testing Real-Time Data Integration...")
    
    # Test 1: Update a single stock
    print("\n📊 Test 1: Updating AAPL with real-time data...")
    try:
        success = await realtime_data_service.update_stock_in_database('AAPL')
        if success:
            stock = Stock.objects.get(symbol='AAPL')
            print(f"   ✅ AAPL updated: ${stock.current_price}")
        else:
            print("   ❌ Failed to update AAPL")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Update priority stocks
    print("\n📊 Test 2: Updating priority stocks...")
    priority_symbols = ['AAPL', 'MSFT', 'GOOGL']
    try:
        results = await realtime_data_service.update_priority_stocks(priority_symbols)
        print(f"   ✅ Priority update: {results['updated']}/{results['total']} updated")
        if results['errors']:
            print(f"   ⚠️  Errors: {results['errors']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get comprehensive data for a stock
    print("\n📊 Test 3: Getting comprehensive data for TSLA...")
    try:
        data = await realtime_data_service.get_comprehensive_stock_data('TSLA')
        if data:
            print(f"   ✅ TSLA data: ${data.get('current_price', 'N/A')}")
            print(f"   📈 Change: {data.get('change_percent', 'N/A')}")
            print(f"   📊 Volume: {data.get('volume', 'N/A')}")
        else:
            print("   ❌ No data available for TSLA")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Show current database state
    print("\n📊 Test 4: Current database state...")
    try:
        stocks = Stock.objects.all()[:5]
        for stock in stocks:
            print(f"   {stock.symbol}: ${stock.current_price or 'N/A'} (Score: {stock.beginner_friendly_score}%)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 Real-time integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_realtime_integration())
