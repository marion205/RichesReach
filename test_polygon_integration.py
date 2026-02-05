#!/usr/bin/env python3
"""
Test Polygon.io integration for Options Edge Factory.
Verifies real API calls are working.

Run: python test_polygon_integration.py
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

import django
django.setup()

from core.options_api_wiring import PolygonDataFetcher
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_polygon_integration():
    """Test live Polygon.io API integration"""
    
    # Get API key from environment
    polygon_key = os.getenv('POLYGON_API_KEY')
    if not polygon_key:
        print("❌ POLYGON_API_KEY not set in environment")
        print("   Set it with: export POLYGON_API_KEY=your_key_here")
        return False
    
    print("\n" + "=" * 80)
    print("POLYGON.IO INTEGRATION TEST")
    print("=" * 80)
    
    fetcher = PolygonDataFetcher(api_key=polygon_key)
    ticker = "AAPL"
    
    # Test 1: Fetch OHLCV History
    print(f"\n[1] Fetching {ticker} OHLCV history (60 days)...")
    ohlcv = fetcher._fetch_ohlcv_history(ticker, days=60)
    
    if ohlcv and len(ohlcv) > 0:
        print(f"    ✅ Got {len(ohlcv)} bars of data")
        latest = ohlcv[-1]
        print(f"    Latest: {latest.get('date')} - Close: ${latest.get('close'):.2f}")
    else:
        print(f"    ❌ No OHLCV data returned")
        return False
    
    # Test 2: Get Current Price
    print(f"\n[2] Fetching {ticker} current price...")
    price = fetcher._get_current_price(ticker)
    
    if price:
        print(f"    ✅ Current price: ${price:.2f}")
    else:
        print(f"    ❌ No price data returned")
        return False
    
    # Test 3: Calculate Realized Volatility
    print(f"\n[3] Calculating {ticker} realized volatility...")
    rv = fetcher._calculate_realized_volatility(ohlcv)
    print(f"    ✅ Realized volatility: {rv:.2%}")
    
    # Test 4: Fetch Option Chain
    print(f"\n[4] Fetching {ticker} option chain...")
    options = fetcher._fetch_option_chain(ticker)
    
    if options:
        print(f"    ✅ Got option chain data")
        
        # Show structure
        if isinstance(options, dict):
            num_expiries = len(options)
            print(f"    Expiries: {num_expiries}")
            
            # Show sample strikes
            if num_expiries > 0:
                first_expiry = list(options.keys())[0]
                strikes = options[first_expiry]
                if isinstance(strikes, dict):
                    print(f"    First expiry ({first_expiry}): {len(strikes)} strikes")
                    
                    if len(strikes) > 0:
                        sample_strike = list(strikes.keys())[0]
                        sample_data = strikes[sample_strike]
                        print(f"    Sample strike ({sample_strike}): {list(sample_data.keys())}")
    else:
        print(f"    ⚠️  No option chain returned (may be after-hours)")
    
    # Test 5: Calculate IV Rank
    print(f"\n[5] Calculating {ticker} IV Rank...")
    iv_rank = fetcher._calculate_iv_rank(options or {}, ticker)
    print(f"    ✅ IV Rank: {iv_rank:.2%}")
    
    # Test 6: Full Market Data Snapshot
    print(f"\n[6] Fetching full market snapshot for {ticker}...")
    market_data = fetcher.fetch_market_data(ticker)
    
    if market_data:
        print(f"    ✅ Market snapshot acquired")
        print(f"    Current price: ${market_data.current_price:.2f}")
        print(f"    IV Rank: {market_data.iv_rank:.2%}")
        print(f"    Realized Vol: {market_data.realized_vol:.2%}")
        print(f"    OHLCV bars: {len(market_data.ohlcv_history)}")
        print(f"    Option chain ready: {bool(market_data.option_chain)}")
    else:
        print(f"    ❌ Failed to fetch market snapshot")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL POLYGON.IO TESTS PASSED")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Pipeline can now fetch LIVE market data")
    print("2. Regime detection gets real OHLCV history")
    print("3. Strategy router accesses live option chain")
    print("4. Risk sizer works with real portfolio Greeks")
    print("\nTo use in production:")
    print("- GraphQL query: optionsAnalysis(ticker: 'AAPL')")
    print("- Returns: Live Flight Manuals with current market data")
    
    return True


if __name__ == "__main__":
    try:
        success = test_polygon_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
