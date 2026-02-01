#!/usr/bin/env python3
"""
Diagnostic script to identify why robustness/SSR calculations return defaults.

Tests a single ticker (AAPL) to see where the calculation fails.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package'))

from backend.core.fss_engine import get_fss_engine
from backend.core.chan_quant_signal_engine import ChanQuantSignalEngine

try:
    import yfinance as yf
except ImportError:
    print("❌ yfinance not available")
    sys.exit(1)

def fetch_stock_data(ticker: str, lookback_days: int = 504):
    """Fetch historical data"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + 30)
        
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, auto_adjust=True)
        
        if hist.empty:
            return None
        
        if hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)
        
        return {
            'prices': hist['Close'],
            'volumes': hist['Volume'],
            'current_price': float(hist['Close'].iloc[-1]),
            'data': hist
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def main():
    print("\n" + "="*80)
    print("ROBUSTNESS CALCULATION DIAGNOSTIC")
    print("="*80)
    
    ticker = "AAPL"
    print(f"\n🔍 Testing ticker: {ticker}")
    
    # Fetch data
    print("\n📊 Fetching data...")
    stock_data = fetch_stock_data(ticker, lookback_days=504)
    if stock_data is None:
        print("❌ Failed to fetch data")
        return
    
    prices = stock_data['prices']
    volumes = stock_data['volumes']
    print(f"   ✅ Fetched {len(prices)} days of data")
    print(f"   Date range: {prices.index[0].date()} to {prices.index[-1].date()}")
    
    # Fetch SPY
    spy_data = fetch_stock_data('SPY', lookback_days=504)
    if spy_data is None:
        print("❌ Failed to fetch SPY")
        return
    
    spy_prices = spy_data['prices']
    print(f"   ✅ Fetched {len(spy_prices)} days of SPY data")
    
    # Initialize engine
    print("\n🔧 Initializing FSS engine...")
    fss_engine = get_fss_engine()
    
    # Compute FSS
    print("\n📈 Computing FSS scores...")
    try:
        fss_data = fss_engine.compute_fss_v3(
            prices=pd.DataFrame({ticker: prices}),
            volumes=pd.DataFrame({ticker: volumes}),
            spy=spy_prices,
            vix=None
        )
        print(f"   ✅ FSS data computed")
        print(f"   Shape: {fss_data.shape}")
        print(f"   Columns: {fss_data.columns}")
        print(f"   Index range: {fss_data.index[0].date()} to {fss_data.index[-1].date()}")
        
        # Check if ticker is in columns
        if hasattr(fss_data.columns, 'levels'):
            ticker_in_cols = ticker in fss_data.columns.levels[1]
            print(f"   Ticker in columns: {ticker_in_cols}")
            if not ticker_in_cols:
                print(f"   Available tickers: {list(fss_data.columns.levels[1])}")
        else:
            print(f"   ⚠️  Columns don't have levels (unexpected structure)")
            
    except Exception as e:
        print(f"   ❌ FSS computation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check alignment
    print("\n🔗 Checking data alignment...")
    common_dates = fss_data.index.intersection(prices.index)
    print(f"   Common dates: {len(common_dates)}")
    print(f"   Need at least 60, preferably 252+")
    
    if len(common_dates) < 60:
        print(f"   ❌ Insufficient aligned data")
        return
    
    # Try robustness calculation
    print("\n🔬 Calculating robustness...")
    try:
        robustness = fss_engine.calculate_regime_robustness(
            ticker=ticker,
            fss_data=fss_data,
            prices=pd.DataFrame({ticker: prices}),
            spy=spy_prices,
            vix=None
        )
        print(f"   ✅ Robustness: {robustness:.4f}")
        if robustness == 0.5:
            print(f"   ⚠️  This is the default value - calculation may have failed")
    except Exception as e:
        print(f"   ❌ Robustness calculation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Try SSR calculation
    print("\n📊 Calculating SSR...")
    try:
        ssr = fss_engine.calculate_signal_stability_rating(
            ticker=ticker,
            fss_data=fss_data,
            prices=pd.DataFrame({ticker: prices})
        )
        print(f"   ✅ SSR: {ssr:.4f}")
        if ssr == 0.5 or ssr == 0.0:
            print(f"   ⚠️  This might be a default value - calculation may have failed")
    except Exception as e:
        print(f"   ❌ SSR calculation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Try get_stock_fss
    print("\n🎯 Testing get_stock_fss...")
    try:
        fss_result = fss_engine.get_stock_fss(
            ticker=ticker,
            fss_data=fss_data,
            regime="Expansion",
            prices=pd.DataFrame({ticker: prices}),
            spy=spy_prices,
            vix=None,
            calculate_robustness=True
        )
        print(f"   ✅ FSS Score: {fss_result.fss_score:.2f}")
        print(f"   ✅ Robustness: {fss_result.regime_robustness_score}")
        print(f"   ✅ SSR: {fss_result.signal_stability_rating}")
    except Exception as e:
        print(f"   ❌ get_stock_fss failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

