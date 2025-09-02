#!/usr/bin/env python3
"""
Test Alpha Vantage API Connection
Test live market data with your API key
"""

import os
import asyncio
import sys
from pathlib import Path

# Add core directory to path
sys.path.append(str(Path(__file__).parent / 'core'))

from advanced_market_data_service import AdvancedMarketDataService

async def test_alpha_vantage():
    """Test Alpha Vantage API connection specifically"""
    print("🔍 Testing Alpha Vantage API Connection...")
    print("=" * 50)
    
    # Set the API key directly for testing
    os.environ['ALPHA_VANTAGE_API_KEY'] = 'K0A7XYLDNXHNQ1WI'
    
    # Initialize service
    service = AdvancedMarketDataService()
    
    print("🚀 Advanced Market Data Service initialized")
    print(f"🔑 API Key: {os.environ.get('ALPHA_VANTAGE_API_KEY', 'Not set')[:8]}...")
    
    try:
        # Test VIX data (most important)
        print("\n🧪 Testing VIX (Volatility Index)...")
        vix_data = await service.get_real_time_vix()
        
        if vix_data and vix_data.source != 'synthetic':
            print(f"   ✅ VIX Data: SUCCESS!")
            print(f"      Value: {vix_data.value:.2f}")
            print(f"      Change: {vix_data.change:+.2f} ({vix_data.change_percent:+.2f}%)")
            print(f"      Trend: {vix_data.trend}")
            print(f"      Source: {vix_data.source}")
            print(f"      Confidence: {vix_data.confidence:.2f}")
        else:
            print(f"   ⚠️  VIX Data: Using synthetic data")
            print(f"      Value: {vix_data.value:.2f}")
            print(f"      Source: {vix_data.source}")
        
        # Test bond yields
        print(f"\n🧪 Testing Bond Yields...")
        bond_data = await service.get_real_time_bond_yields()
        
        if bond_data and len(bond_data) > 0:
            print(f"   ✅ Bond Yields: SUCCESS!")
            for bond in bond_data:
                print(f"      {bond.name}: {bond.value:.2f}% ({bond.change:+.2f}%)")
                print(f"         Source: {bond.source}, Trend: {bond.trend}")
        else:
            print(f"   ⚠️  Bond Yields: No data available")
        
        # Test sector performance
        print(f"\n🧪 Testing Sector Performance...")
        sector_data = await service.get_sector_performance()
        
        if sector_data and len(sector_data) > 0:
            print(f"   ✅ Sector Performance: SUCCESS!")
            for sector, data in list(sector_data.items())[:3]:  # Show first 3
                print(f"      {sector}: ${data.value:.2f} ({data.change:+.2f})")
                print(f"         Source: {data.source}, Trend: {data.trend}")
        else:
            print(f"   ⚠️  Sector Performance: No data available")
        
        # Test economic indicators
        print(f"\n🧪 Testing Economic Indicators...")
        econ_data = await service.get_economic_indicators()
        
        if econ_data and len(econ_data) > 0:
            print(f"   ✅ Economic Indicators: SUCCESS!")
            for indicator in econ_data:
                print(f"      {indicator.name}: {indicator.value:.2f}")
                print(f"         Change: {indicator.change:+.2f} ({indicator.change_percent:+.2f}%)")
                print(f"         Source: {indicator.source}, Impact: {indicator.impact}")
        else:
            print(f"   ⚠️  Economic Indicators: No data available")
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 Alpha Vantage Test Summary")
        print("=" * 50)
        
        # Count successful vs synthetic data
        successful_tests = 0
        synthetic_tests = 0
        
        if vix_data and vix_data.source != 'synthetic':
            successful_tests += 1
        else:
            synthetic_tests += 1
            
        if bond_data and len(bond_data) > 0:
            successful_tests += 1
        else:
            synthetic_tests += 1
            
        if sector_data and len(sector_data) > 0:
            successful_tests += 1
        else:
            synthetic_tests += 1
            
        if econ_data and len(econ_data) > 0:
            successful_tests += 1
        else:
            synthetic_tests += 1
        
        print(f"✅ Live Data Tests: {successful_tests}")
        print(f"⚠️  Synthetic Data Tests: {synthetic_tests}")
        
        if successful_tests > 0:
            print(f"\n🚀 SUCCESS! Alpha Vantage is working!")
            print(f"   You now have live market data!")
            print(f"   Next: Get Finnhub and News API keys for complete coverage")
        else:
            print(f"\n⚠️  Alpha Vantage connection may need troubleshooting")
            print(f"   Check API key and rate limits")
        
        # Close service
        await service.close()
        
        return successful_tests > 0
        
    except Exception as e:
        print(f"❌ Error testing Alpha Vantage: {e}")
        await service.close()
        return False

if __name__ == "__main__":
    print("🚀 Testing Alpha Vantage API with Your Key!")
    print("=" * 50)
    
    success = asyncio.run(test_alpha_vantage())
    
    if success:
        print(f"\n🎉 Alpha Vantage test completed successfully!")
        print(f"📋 Next Steps:")
        print(f"1. 🔑 Get Finnhub API key: https://finnhub.io/register")
        print(f"2. 📰 Get News API key: https://newsapi.org/register")
        print(f"3. 🧪 Test all connections: python3 test_api_connections.py")
        print(f"4. 🚀 Enable production mode in .env")
    else:
        print(f"\n❌ Alpha Vantage test failed. Check API key and try again.")
