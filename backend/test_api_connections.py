#!/usr/bin/env python3
"""
Test API Connections Script
Verify all configured API keys are working
"""

import os
import asyncio
import sys
from pathlib import Path

# Add core directory to path
sys.path.append(str(Path(__file__).parent / 'core'))

from advanced_market_data_service import AdvancedMarketDataService

async def test_api_connections():
    """Test all configured API connections"""
    print("🔍 Testing API Connections...")
    print("=" * 50)
    
    # Initialize service
    service = AdvancedMarketDataService()
    
    # Test each data source
    tests = [
        ("VIX Data", service.get_real_time_vix),
        ("Bond Yields", service.get_real_time_bond_yields),
        ("Currency Data", service.get_real_time_currency_strength),
        ("Economic Indicators", service.get_economic_indicators),
        ("Sector Performance", service.get_sector_performance),
        ("Alternative Data", service.get_alternative_data)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                print(f"   ✅ {test_name}: SUCCESS")
                print(f"      Source: {getattr(result, 'source', 'N/A')}")
                print(f"      Confidence: {getattr(result, 'confidence', 'N/A')}")
                results[test_name] = "SUCCESS"
            else:
                print(f"   ⚠️  {test_name}: NO DATA")
                results[test_name] = "NO DATA"
                
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED")
            print(f"      Error: {str(e)}")
            results[test_name] = "FAILED"
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 API Connection Test Summary")
    print("=" * 50)
    
    success_count = sum(1 for r in results.values() if r == "SUCCESS")
    total_count = len(results)
    
    for test_name, result in results.items():
        status_emoji = "✅" if result == "SUCCESS" else "⚠️" if result == "NO DATA" else "❌"
        print(f"{status_emoji} {test_name}: {result}")
    
    print(f"\n🎯 Overall: {success_count}/{total_count} APIs working")
    
    if success_count == total_count:
        print("🚀 All APIs working! Ready for live market data!")
    elif success_count > 0:
        print("⚠️  Some APIs working. Check failed connections.")
    else:
        print("❌ No APIs working. Check API keys and configuration.")
    
    # Close service
    await service.close()
    
    return results

if __name__ == "__main__":
    asyncio.run(test_api_connections())
