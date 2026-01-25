#!/usr/bin/env python3
"""
Test FSS with Real Data
Tests FSS calculation using real market data from APIs.
"""
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
from core.fss_engine import get_fss_engine
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_real_data():
    """Test FSS with real market data"""
    
    print("\n" + "="*80)
    print("FSS v3.0 - Real Data Test")
    print("="*80)
    print("Testing with real market data from Polygon/Alpaca/yfinance...\n")
    
    # Test with a single stock first (to avoid rate limits)
    test_stock = "AAPL"
    
    print(f"📊 Fetching real data for {test_stock}...")
    print("   (This may take 30-60 seconds due to API rate limits)\n")
    
    pipeline = get_fss_data_pipeline()
    
    try:
        async with pipeline:
            request = FSSDataRequest(
                tickers=[test_stock],
                lookback_days=252,
                include_fundamentals=False  # Skip fundamentals to speed up
            )
            
            data_result = await pipeline.fetch_fss_data(request)
        
        print("✅ Data fetched successfully!")
        print(f"\nData Quality:")
        print(f"  Prices coverage: {data_result.data_quality.get('prices_coverage', {}).get('overall', 0)*100:.1f}%")
        print(f"  Volumes coverage: {data_result.data_quality.get('volumes_coverage', {}).get('overall', 0)*100:.1f}%")
        print(f"  Tickers with data: {len(data_result.data_quality.get('tickers_with_data', []))}")
        print(f"  Missing tickers: {data_result.data_quality.get('missing_tickers', [])}")
        
        if test_stock not in data_result.prices.columns:
            print(f"\n❌ {test_stock} not found in price data")
            return
        
        # Calculate FSS
        print(f"\n📈 Calculating FSS v3.0...")
        
        fss_engine = get_fss_engine()
        fss_data = fss_engine.compute_fss_v3(
            prices=data_result.prices,
            volumes=data_result.volumes,
            spy=data_result.spy,
            vix=data_result.vix,
            fundamentals_daily=None
        )
        
        # Get latest score
        latest_date = fss_data.index[-1]
        fss_score = fss_data["FSS"].loc[latest_date, test_stock]
        T = fss_data["T"].loc[latest_date, test_stock]
        C = fss_data["C"].loc[latest_date, test_stock]
        R = fss_data["R"].loc[latest_date, test_stock]
        
        # Detect regime
        regime_result = fss_engine.detect_market_regime(data_result.spy, data_result.vix)
        
        print(f"\n{'='*80}")
        print(f"FSS v3.0 Result: {test_stock}")
        print(f"{'='*80}")
        print(f"Date: {latest_date.strftime('%Y-%m-%d')}")
        print(f"Market Regime: {regime_result.regime}")
        print(f"\nOverall FSS Score: {float(fss_score):.1f}/100")
        print(f"\nComponent Breakdown:")
        print(f"  Trend:        {float(T):.1f}/100")
        print(f"  Fundamentals: 50.0/100 (not fetched)")
        print(f"  Capital Flow: {float(C):.1f}/100")
        print(f"  Risk:         {float(R):.1f}/100")
        
        # Recommendation
        fss_val = float(fss_score)
        if fss_val >= 75:
            rec = "🟢 HIGH CONVICTION BUY"
        elif fss_val >= 60:
            rec = "🟡 WATCHLIST"
        else:
            rec = "🔴 AVOID"
        
        print(f"\nRecommendation: {rec}")
        print(f"\n{'='*80}")
        print("✅ Real Data Test Complete!")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: This might be due to:")
        print("  - API rate limits (429 errors)")
        print("  - API authentication issues (401 errors)")
        print("  - Network connectivity")
        print("\nThe system will fall back to yfinance if APIs fail.\n")


if __name__ == "__main__":
    asyncio.run(test_real_data())

