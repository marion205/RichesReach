#!/usr/bin/env python3
"""
Detailed diagnostic to see exactly where robustness calculation fails.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package'))

from backend.core.fss_engine import get_fss_engine

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
    print("DETAILED ROBUSTNESS DIAGNOSTIC")
    print("="*80)
    
    ticker = "AAPL"
    
    # Fetch data
    stock_data = fetch_stock_data(ticker, lookback_days=504)
    prices = stock_data['prices']
    volumes = stock_data['volumes']
    
    spy_data = fetch_stock_data('SPY', lookback_days=504)
    spy_prices = spy_data['prices']
    
    # Compute FSS
    fss_engine = get_fss_engine()
    fss_data = fss_engine.compute_fss_v3(
        prices=pd.DataFrame({ticker: prices}),
        volumes=pd.DataFrame({ticker: volumes}),
        spy=spy_prices,
        vix=None
    )
    
    # Manually trace through robustness calculation
    print("\n🔬 Tracing robustness calculation...")
    
    # Step 1: Check ticker in columns
    if ticker not in fss_data.columns.levels[1] or ticker not in pd.DataFrame({ticker: prices}).columns:
        print("   ❌ Ticker not found in fss_data or prices")
        return
    print("   ✅ Ticker found in both")
    
    # Step 2: Get FSS scores and prices
    fss_scores = fss_data[("FSS", ticker)]
    ticker_prices = pd.DataFrame({ticker: prices})[ticker]
    
    print(f"   FSS scores length: {len(fss_scores)}")
    print(f"   Prices length: {len(ticker_prices)}")
    
    # Step 3: Align dates
    common_dates = fss_scores.index.intersection(ticker_prices.index)
    print(f"   Common dates: {len(common_dates)}")
    
    if len(common_dates) < 60:
        print("   ❌ Less than 60 common dates")
        return
    
    fss_aligned = fss_scores.loc[common_dates]
    prices_aligned = ticker_prices.loc[common_dates]
    
    # Step 4: Calculate forward returns
    forward_returns = prices_aligned.pct_change(21).shift(-21).dropna()
    fss_for_returns = fss_aligned.loc[forward_returns.index]
    
    print(f"   Forward returns length: {len(forward_returns)}")
    print(f"   FSS for returns length: {len(fss_for_returns)}")
    
    # Step 5: Build history
    lookback_days = 252
    history_rows = []
    
    for date in fss_for_returns.index[:lookback_days]:
        if date not in spy_prices.index:
            continue
        date_idx = spy_prices.index.get_loc(date)
        if date_idx < 200:
            continue
        
        # Calculate regime
        spy_window = spy_prices.iloc[max(0, date_idx - 200):date_idx + 1]
        regime_result = fss_engine.detect_market_regime(spy_window, None)
        regime = regime_result.regime
        
        fss_val = fss_for_returns.loc[date]
        forward_ret = forward_returns.loc[date]
        
        history_rows.append({
            "regime": regime,
            "fss_score": fss_val,
            "forward_ret": forward_ret
        })
    
    print(f"   History rows: {len(history_rows)}")
    
    if len(history_rows) < 20:
        print("   ❌ Less than 20 history rows")
        return
    
    history_df = pd.DataFrame(history_rows)
    
    # Step 6: Check regimes
    unique_regimes = history_df["regime"].nunique()
    print(f"   Unique regimes: {unique_regimes}")
    print(f"   Regime distribution:")
    print(history_df["regime"].value_counts())
    
    if unique_regimes < 2:
        print("   ❌ Less than 2 regimes")
        return
    
    # Step 7: Try internal calculation
    print("\n   📊 Running internal robustness calculation...")
    try:
        robustness = fss_engine._calculate_regime_robustness_from_history(history_df)
        print(f"   ✅ Internal robustness: {robustness:.4f}")
    except Exception as e:
        print(f"   ❌ Internal calculation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

