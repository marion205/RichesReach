#!/usr/bin/env python3
"""
FSS v3.0 Real Data Backtest
Runs comprehensive backtest with real historical data (2+ years).
Handles API rate limits with retries and caching.
"""
import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_engine import get_fss_engine
from core.fss_backtest import FSSBacktester
from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def fetch_data_with_retry(pipeline, request, max_retries=3, delay=60):
    """Fetch data with retry logic for rate limits"""
    for attempt in range(max_retries):
        try:
            async with pipeline:
                result = await pipeline.fetch_fss_data(request)
            return result
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = delay * (attempt + 1)
                    print(f"   ⏳ Rate limited. Waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                    await asyncio.sleep(wait_time)
                    continue
            raise
    return None


async def run_real_data_backtest():
    """Run comprehensive backtest with real historical data"""
    
    print("\n" + "="*80)
    print("FSS v3.0 Real Data Backtest (2+ Years)")
    print("="*80)
    print("Fetching real market data from Polygon/Alpaca...\n")
    
    # Test periods (2+ years of data)
    test_periods = [
        {
            "name": "2024 Full Year",
            "start": "2024-01-01",
            "end": "2024-12-31",
            "expected_regime": "Expansion"
        },
        {
            "name": "2023 Full Year",
            "start": "2023-01-01",
            "end": "2023-12-31",
            "expected_regime": "Expansion"
        },
        {
            "name": "2022 Full Year (Bear Market)",
            "start": "2022-01-01",
            "end": "2022-12-31",
            "expected_regime": "Crisis"
        }
    ]
    
    # Test universe (S&P 500 large caps)
    test_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META", "JNJ", "V", "JPM"]
    
    results = []
    pipeline = get_fss_data_pipeline()
    fss_engine = get_fss_engine()
    backtester = FSSBacktester(transaction_cost_bps=10.0)
    
    for period in test_periods:
        print(f"\n📊 Testing: {period['name']}")
        print(f"   Period: {period['start']} to {period['end']}")
        print("-" * 80)
        
        try:
            start_date = datetime.strptime(period['start'], "%Y-%m-%d")
            end_date = datetime.strptime(period['end'], "%Y-%m-%d")
            
            # Need extra buffer for technical indicators
            lookback_start = start_date - timedelta(days=400)
            
            print(f"   📥 Fetching data (this may take 1-2 minutes due to API limits)...")
            
            request = FSSDataRequest(
                tickers=test_stocks,
                lookback_days=600,  # Extra buffer for indicators
                include_fundamentals=False
            )
            
            # Fetch with retry logic
            data_result = await fetch_data_with_retry(pipeline, request, max_retries=3, delay=60)
            
            if data_result is None:
                print(f"   ❌ Failed to fetch data after retries")
                continue
            
            print(f"   ✅ Fetched {len(data_result.prices)} days of data")
            
            # Compute FSS on FULL dataset first
            print(f"   📈 Calculating FSS v3.0...")
            fss_full = fss_engine.compute_fss_v3(
                prices=data_result.prices,
                volumes=data_result.volumes,
                spy=data_result.spy,
                vix=data_result.vix
            )
            
            # Slice to test period
            try:
                prices_test = data_result.prices.loc[start_date:end_date]
                volumes_test = data_result.volumes.loc[start_date:end_date]
                spy_test = data_result.spy.loc[start_date:end_date]
                vix_test = data_result.vix.loc[start_date:end_date] if data_result.vix is not None else None
                fss_test = fss_full["FSS"].loc[start_date:end_date]
            except (KeyError, IndexError) as e:
                print(f"   ⚠️  Date range issue: {e}")
                continue
            
            if len(prices_test) < 50:
                print(f"   ⚠️  Insufficient data points ({len(prices_test)})")
                continue
            
            # Create daily regime series
            print(f"   🎯 Detecting market regimes...")
            regime_series = pd.Series(index=prices_test.index, dtype=object)
            for date in prices_test.index:
                date_idx = spy_test.index.get_loc(date)
                window_start = max(0, date_idx - 200)
                spy_window = spy_test.iloc[window_start:date_idx+1]
                vix_window = vix_test.iloc[window_start:date_idx+1] if vix_test is not None else None
                
                if len(spy_window) >= 200:
                    regime_result = fss_engine.detect_market_regime(spy_window, vix_window)
                    regime_series.loc[date] = regime_result.regime
                else:
                    regime_series.loc[date] = "Expansion"
            
            # Backtest: Always-In
            print(f"   🔄 Running Always-In backtest...")
            backtest_always_in = backtester.backtest_rank_strategy(
                prices=prices_test,
                fss=fss_test,
                spy=spy_test,
                rebalance_freq="M",
                top_n=5,
                cash_out_on_crisis=False
            )
            
            # Backtest: Regime-Aware
            print(f"   🛡️  Running Regime-Aware backtest...")
            backtest_result = backtester.backtest_rank_strategy(
                prices=prices_test,
                fss=fss_test,
                spy=spy_test,
                rebalance_freq="M",
                top_n=5,
                regime=regime_series,
                cash_out_on_crisis=True,
                cash_return_rate=0.04
            )
            
            # Calculate metrics
            safety_alpha = backtest_result.annual_return - backtest_always_in.annual_return
            dd_improvement = backtest_always_in.max_drawdown - backtest_result.max_drawdown
            
            # IC calculation
            horizons = [1, 5, 21]
            ic_results = {}
            for horizon in horizons:
                if horizon < len(prices_test) // 3:
                    forward_returns = backtester.forward_return(prices_test, horizon=horizon)
                    ic_series = backtester.calculate_ic(fss_test, forward_returns)
                    ic_results[f'ic_{horizon}d'] = ic_series.mean() if len(ic_series) > 0 else 0.0
            
            mean_ic = ic_results.get('ic_21d', ic_results.get('ic_5d', 0.0))
            
            # Store results
            result = {
                "period": period['name'],
                "regime": regime_series.iloc[-1] if len(regime_series) > 0 else "Unknown",
                "annual_return": backtest_result.annual_return,
                "annual_return_always_in": backtest_always_in.annual_return,
                "safety_alpha": safety_alpha,
                "sharpe_ratio": backtest_result.sharpe_ratio,
                "sharpe_ratio_always_in": backtest_always_in.sharpe_ratio,
                "max_drawdown": backtest_result.max_drawdown,
                "max_drawdown_always_in": backtest_always_in.max_drawdown,
                "dd_improvement": dd_improvement,
                "ic_mean": mean_ic,
                "alpha": backtest_result.alpha
            }
            results.append(result)
            
            # Display
            print(f"\n   📊 Results:")
            print(f"   Regime: {result['regime']}")
            print(f"   Annual Return (Regime-Aware): {backtest_result.annual_return*100:.1f}%")
            print(f"   Annual Return (Always-In): {backtest_always_in.annual_return*100:.1f}%")
            print(f"   Safety Alpha: {safety_alpha*100:.1f}% ⭐")
            print(f"   Sharpe Ratio: {backtest_result.sharpe_ratio:.2f} (vs {backtest_always_in.sharpe_ratio:.2f} Always-In)")
            print(f"   Max Drawdown: {backtest_result.max_drawdown*100:.1f}% (vs {backtest_always_in.max_drawdown*100:.1f}% Always-In)")
            print(f"   DD Improvement: {dd_improvement*100:.1f}% ⭐")
            print(f"   IC (21d): {mean_ic:.3f}")
            if backtest_result.alpha:
                print(f"   Alpha vs SPY: {backtest_result.alpha*100:.1f}%")
            
        except Exception as e:
            logger.error(f"Error in {period['name']}: {e}", exc_info=True)
            print(f"   ❌ Error: {e}")
            continue
    
    # Summary
    if results:
        print("\n" + "="*80)
        print("FSS v3.0 Real Data Backtest Summary")
        print("="*80)
        
        avg_return = np.mean([r['annual_return'] for r in results])
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in results])
        avg_ic = np.mean([r['ic_mean'] for r in results])
        avg_safety_alpha = np.mean([r['safety_alpha'] for r in results])
        avg_dd_improvement = np.mean([r['dd_improvement'] for r in results])
        avg_sharpe_improvement = np.mean([r['sharpe_ratio'] - r['sharpe_ratio_always_in'] for r in results])
        
        print(f"\nAverage Annual Return: {avg_return*100:.1f}%")
        print(f"Average Sharpe Ratio: {avg_sharpe:.2f}")
        print(f"Average IC (21d): {avg_ic:.3f}")
        print(f"\n🎯 Regime-Aware Cash-Out Benefits:")
        print(f"  Average Safety Alpha: {avg_safety_alpha*100:.1f}%")
        print(f"  Average DD Improvement: {avg_dd_improvement*100:.1f}%")
        print(f"  Average Sharpe Improvement: {avg_sharpe_improvement:.2f}")
        
        # Targets
        print("\n📊 Targets (Best-in-Class):")
        print(f"  Sharpe > 1.1: {'✅' if avg_sharpe > 1.1 else '❌'} ({avg_sharpe:.2f})")
        print(f"  IC > 0.10: {'✅' if avg_ic > 0.10 else '❌'} ({avg_ic:.3f})")
        print(f"  Safety Alpha > 2%: {'✅' if avg_safety_alpha > 0.02 else '❌'} ({avg_safety_alpha*100:.1f}%)")
        print(f"  DD Improvement > 30%: {'✅' if avg_dd_improvement > 0.30 else '❌'} ({avg_dd_improvement*100:.1f}%)")
        
        # Save results
        results_file = "fss_backtest_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")
    
    print("\n" + "="*80)
    print("✅ Real Data Backtest Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_real_data_backtest())

