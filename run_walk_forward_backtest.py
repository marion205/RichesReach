#!/usr/bin/env python3
"""
Run Walk-Forward Backtest for Chan Portfolio Pipeline

Tests the complete pipeline on 5 years of historical data:
1. FSS Engine → FSS scores
2. Regime Robustness → Filter/rank by robustness
3. Chan Quant Signals → Kelly fractions
4. Portfolio Allocator → Correlation-aware weights
5. Walk-forward testing → No look-ahead bias

Usage:
    python3 run_walk_forward_backtest.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add deployment_package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package'))

from backend.core.walk_forward_backtest import WalkForwardBacktester, run_walk_forward_backtest_demo


async def main():
    """Main function to run walk-forward backtest"""
    print("\n" + "="*80)
    print("CHAN PORTFOLIO PIPELINE - WALK-FORWARD BACKTEST")
    print("="*80)
    print("\nTesting complete pipeline:")
    print("  1. FSS Engine → FSS scores")
    print("  2. Regime Robustness → Filter by robustness")
    print("  3. Chan Quant Signals → Kelly fractions")
    print("  4. Portfolio Allocator → Correlation-aware weights")
    print("  5. Walk-forward testing → No look-ahead bias")
    print("\n" + "="*80)
    
    # Test on diverse basket of stocks
    test_tickers = [
        "AAPL", "MSFT", "GOOGL",  # Tech
        "JPM", "BAC",              # Financials
        "JNJ", "PFE",              # Healthcare
        "V", "MA",                  # Payments
        "PG", "KO"                  # Consumer
    ]
    
    print(f"\n📊 Testing on {len(test_tickers)} tickers:")
    print(f"   {', '.join(test_tickers)}")
    
    backtester = WalkForwardBacktester(
        training_window_days=252,  # 1 year training
        testing_window_days=63,    # 3 months testing
        rebalance_freq="M",        # Monthly rebalancing
        min_robustness=0.5,        # Minimum robustness to include
        max_positions=8,            # Maximum 8 positions
        transaction_cost_bps=5.0   # 5 bps transaction cost
    )
    
    # 5-year backtest period
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    print(f"\n📅 Backtest Period: {start_date.date()} to {end_date.date()}")
    print(f"   Training Window: {backtester.training_window_days} days")
    print(f"   Testing Window:  {backtester.testing_window_days} days")
    print(f"   Rebalance Freq:  {backtester.rebalance_freq}")
    print(f"   Min Robustness:   {backtester.min_robustness}")
    print(f"   Max Positions:    {backtester.max_positions}")
    
    print("\n🚀 Starting walk-forward backtest...")
    print("   (This may take several minutes depending on data availability)\n")
    
    try:
        result = await backtester.run_walk_forward_backtest(
            tickers=test_tickers,
            start_date=start_date,
            end_date=end_date,
            benchmark_ticker="SPY"
        )
        
        # Print results
        backtester.print_results(result)
        
        # Additional analysis
        print("\n📈 Key Insights:")
        if result.alpha > 0:
            print(f"   ✅ Positive alpha: {result.alpha:.2%} vs SPY")
        else:
            print(f"   ⚠️  Negative alpha: {result.alpha:.2%} vs SPY")
        
        if result.sharpe_ratio > 1.0:
            print(f"   ✅ Strong Sharpe ratio: {result.sharpe_ratio:.2f}")
        elif result.sharpe_ratio > 0.5:
            print(f"   ⚠️  Moderate Sharpe ratio: {result.sharpe_ratio:.2f}")
        else:
            print(f"   ❌ Low Sharpe ratio: {result.sharpe_ratio:.2f}")
        
        if not result.robustness_vs_returns.empty:
            corr = result.robustness_vs_returns["robustness"].corr(result.robustness_vs_returns["forward_return"])
            if corr > 0.1:
                print(f"   ✅ Robustness correlates with returns: {corr:.3f}")
            else:
                print(f"   ⚠️  Weak robustness-return correlation: {corr:.3f}")
        
        if result.high_robustness_performance and result.low_robustness_performance:
            high_mean = result.high_robustness_performance.get("mean_return", 0.0)
            low_mean = result.low_robustness_performance.get("mean_return", 0.0)
            if high_mean > low_mean:
                print(f"   ✅ High robustness stocks outperform: {high_mean:.2%} vs {low_mean:.2%}")
            else:
                print(f"   ⚠️  High robustness stocks underperform: {high_mean:.2%} vs {low_mean:.2%}")
        
        print("\n" + "="*80)
        print("✅ WALK-FORWARD BACKTEST COMPLETE")
        print("="*80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(main())

