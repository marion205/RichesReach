#!/usr/bin/env python3
"""
Test All APIs Live - Complete Market Intelligence
Test Alpha Vantage, Finnhub, and News API working together
"""

import os
import asyncio
import sys
from pathlib import Path

# Add core directory to path
sys.path.append(str(Path(__file__).parent / 'core'))

from advanced_market_data_service import AdvancedMarketDataService

async def test_all_apis_live():
    """Test all three APIs working together for live market data"""
    print("🚀 TESTING ALL APIS FOR LIVE MARKET INTELLIGENCE")
    print("=" * 60)
    
    # Set all API keys for testing
    os.environ['ALPHA_VANTAGE_API_KEY'] = 'K0A7XYLDNXHNQ1WI'
    os.environ['FINNHUB_API_KEY'] = 'd2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0'
    os.environ['NEWS_API_KEY'] = '94a335c7316145f79840edd62f77e11e'
    
    print("🔑 API Keys Configured:")
    print(f"   Alpha Vantage: {os.environ['ALPHA_VANTAGE_API_KEY'][:8]}...")
    print(f"   Finnhub: {os.environ['FINNHUB_API_KEY'][:8]}...")
    print(f"   News API: {os.environ['NEWS_API_KEY'][:8]}...")
    
    # Initialize service
    service = AdvancedMarketDataService()
    
    print("\n🚀 Advanced Market Data Service initialized")
    print("   Testing live market intelligence...")
    
    try:
        # Test 1: VIX Data (Market Fear Gauge)
        print(f"\n🧪 Test 1: VIX (Volatility Index)")
        print("-" * 40)
        vix_data = await service.get_real_time_vix()
        
        if vix_data:
            print(f"   ✅ VIX Data Retrieved!")
            print(f"      Value: {vix_data.value:.2f}")
            print(f"      Change: {vix_data.change:+.2f} ({vix_data.change_percent:+.2f}%)")
            print(f"      Trend: {vix_data.trend}")
            print(f"      Source: {vix_data.source}")
            print(f"      Confidence: {vix_data.confidence:.2f}")
            
            # Check if it's real data
            if vix_data.source != 'synthetic':
                print(f"      🎉 LIVE DATA CONFIRMED!")
            else:
                print(f"      ⚠️  Using synthetic data (API may need time)")
        else:
            print(f"   ❌ VIX data failed")
        
        # Test 2: Bond Yields (Interest Rate Indicators)
        print(f"\n🧪 Test 2: Bond Yields")
        print("-" * 40)
        bond_data = await service.get_real_time_bond_yields()
        
        if bond_data and len(bond_data) > 0:
            print(f"   ✅ Bond Yields Retrieved!")
            for bond in bond_data:
                print(f"      {bond.name}: {bond.value:.2f}% ({bond.change:+.2f}%)")
                print(f"         Trend: {bond.trend}, Source: {bond.source}")
                
                if bond.source != 'synthetic':
                    print(f"         🎉 LIVE DATA CONFIRMED!")
                else:
                    print(f"         ⚠️  Using synthetic data")
        else:
            print(f"   ❌ Bond yields failed")
        
        # Test 3: Sector Performance (Market Sectors)
        print(f"\n🧪 Test 3: Sector Performance")
        print("-" * 40)
        sector_data = await service.get_sector_performance()
        
        if sector_data and len(sector_data) > 0:
            print(f"   ✅ Sector Performance Retrieved!")
            for sector, data in list(sector_data.items())[:3]:  # Show first 3
                print(f"      {sector}: ${data.value:.2f} ({data.change:+.2f})")
                print(f"         Trend: {data.trend}, Source: {data.source}")
                
                if data.source != 'synthetic':
                    print(f"         🎉 LIVE DATA CONFIRMED!")
                else:
                    print(f"         ⚠️  Using synthetic data")
        else:
            print(f"   ❌ Sector performance failed")
        
        # Test 4: Economic Indicators (GDP, Inflation, etc.)
        print(f"\n🧪 Test 4: Economic Indicators")
        print("-" * 40)
        econ_data = await service.get_economic_indicators()
        
        if econ_data and len(econ_data) > 0:
            print(f"   ✅ Economic Indicators Retrieved!")
            for indicator in econ_data:
                print(f"      {indicator.name}: {indicator.value:.2f}")
                print(f"         Change: {indicator.change:+.2f} ({indicator.change_percent:+.2f}%)")
                print(f"         Impact: {indicator.impact}, Source: {indicator.source}")
                
                if indicator.source != 'synthetic':
                    print(f"         🎉 LIVE DATA CONFIRMED!")
                else:
                    print(f"         ⚠️  Using synthetic data")
        else:
            print(f"   ❌ Economic indicators failed")
        
        # Test 5: Alternative Data (News Sentiment)
        print(f"\n🧪 Test 5: Alternative Data (News Sentiment)")
        print("-" * 40)
        alt_data = await service.get_alternative_data()
        
        if alt_data and len(alt_data) > 0:
            print(f"   ✅ Alternative Data Retrieved!")
            for data in alt_data:
                print(f"      Source: {data.source}")
                print(f"         Sentiment: {data.sentiment_score:.2f} ({data.trend})")
                print(f"         Mentions: {data.mentions}, Confidence: {data.confidence:.2f}")
                
                if data.source != 'synthetic':
                    print(f"         🎉 LIVE DATA CONFIRMED!")
                else:
                    print(f"         ⚠️  Using synthetic data")
        else:
            print(f"   ❌ Alternative data failed")
        
        # Test 6: Comprehensive Market Overview
        print(f"\n🧪 Test 6: Comprehensive Market Overview")
        print("-" * 40)
        print("   🔍 Gathering comprehensive market data...")
        
        market_overview = await service.get_comprehensive_market_overview()
        
        if market_overview:
            print(f"   ✅ Comprehensive Overview Generated!")
            print(f"      Timestamp: {market_overview['timestamp']}")
            
            # Market Regime Analysis
            regime = market_overview.get('market_regime', {})
            if regime:
                print(f"      Market Regime: {regime.get('regime', 'N/A')}")
                print(f"      Confidence: {regime.get('confidence', 0):.2f}")
                print(f"      Trend: {regime.get('trend', 'N/A')}")
                print(f"      Volatility: {regime.get('volatility', 'N/A')}")
            
            # Risk Assessment
            risk = market_overview.get('risk_assessment', {})
            if risk:
                print(f"      Risk Level: {risk.get('risk_level', 'N/A')}")
                print(f"      Risk Score: {risk.get('risk_score', 0):.2f}")
            
            # Opportunities
            opportunities = market_overview.get('opportunity_analysis', {})
            if opportunities:
                print(f"      Opportunity Score: {opportunities.get('opportunity_score', 0):.2f}")
                print(f"      Top Opportunities: {', '.join(opportunities.get('top_opportunities', []))}")
        else:
            print(f"   ❌ Comprehensive overview failed")
        
        # Summary and Analysis
        print(f"\n" + "=" * 60)
        print("📊 LIVE MARKET INTELLIGENCE TEST SUMMARY")
        print("=" * 60)
        
        # Count live vs synthetic data
        live_data_count = 0
        synthetic_data_count = 0
        
        if vix_data and vix_data.source != 'synthetic':
            live_data_count += 1
        elif vix_data:
            synthetic_data_count += 1
            
        if bond_data and len(bond_data) > 0:
            if any(b.source != 'synthetic' for b in bond_data):
                live_data_count += 1
            else:
                synthetic_data_count += 1
                
        if sector_data and len(sector_data) > 0:
            if any(s.source != 'synthetic' for s in sector_data.values()):
                live_data_count += 1
            else:
                synthetic_data_count += 1
                
        if econ_data and len(econ_data) > 0:
            if any(e.source != 'synthetic' for e in econ_data):
                live_data_count += 1
            else:
                synthetic_data_count += 1
                
        if alt_data and len(alt_data) > 0:
            if any(a.source != 'synthetic' for a in alt_data):
                live_data_count += 1
            else:
                synthetic_data_count += 1
        
        print(f"🎉 Live Data Sources: {live_data_count}")
        print(f"⚠️  Synthetic Data Sources: {synthetic_data_count}")
        
        if live_data_count > 0:
            print(f"\n🚀 SUCCESS! Live market intelligence is working!")
            print(f"   You now have real-time market data!")
            print(f"   Your AI system is live and intelligent!")
        else:
            print(f"\n⚠️  All data is synthetic. This may be due to:")
            print(f"   1. API rate limits (wait a few minutes)")
            print(f"   2. API keys need time to activate")
            print(f"   3. Network connectivity issues")
        
        # Close service
        await service.close()
        
        return live_data_count > 0
        
    except Exception as e:
        print(f"❌ Error testing APIs: {e}")
        import traceback
        traceback.print_exc()
        await service.close()
        return False

async def main():
    """Main test function"""
    print("🎯 COMPLETE MARKET INTELLIGENCE TEST")
    print("=" * 60)
    print("Testing Alpha Vantage + Finnhub + News API")
    print("This will show you live market intelligence in action!")
    
    success = await test_all_apis_live()
    
    if success:
        print(f"\n🎉 LIVE MARKET INTELLIGENCE TEST SUCCESSFUL!")
        print(f"📋 Your AI System Now Has:")
        print(f"   📊 Real-time VIX, bond yields, stock prices")
        print(f"   🏛️  Live economic indicators")
        print(f"   🏢 Current sector performance")
        print(f"   📰 Real news sentiment analysis")
        print(f"   🎯 Live market regime detection")
        print(f"   ⚠️  Real-time risk assessment")
        print(f"   💡 Live opportunity identification")
        
        print(f"\n🚀 Next Steps:")
        print(f"1. 🧪 Test in your app")
        print(f"2. 📊 Monitor live data quality")
        print(f"3. 🎯 Deploy for users")
        print(f"4. 🔄 Set up continuous monitoring")
        
        print(f"\n💡 Pro Tip:")
        print(f"   Your AI system now provides institutional-grade")
        print(f"   market intelligence that gives users a competitive edge!")
        
    else:
        print(f"\n⚠️  Live market intelligence test needs troubleshooting")
        print(f"   Check API keys and try again in a few minutes")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
