#!/usr/bin/env python3
"""
Threshold Sweep Analysis

Tests robustness thresholds from 0.5 to 0.9 and calculates:
- Median returns (less sensitive to outliers)
- Bootstrap confidence intervals
- Performance metrics by threshold

Usage:
    python3 run_threshold_sweep_analysis.py
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from scipy import stats

# Add deployment_package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package'))

from backend.core.walk_forward_backtest import WalkForwardBacktester

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not available. Install with: pip install yfinance")


def bootstrap_ci(
    data: np.ndarray,
    statistic_func,
    n_bootstrap: int = 1000,
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence interval.
    
    Args:
        data: Array of observations
        statistic_func: Function to calculate statistic (e.g., np.mean, np.median)
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level (default: 0.95)
    
    Returns:
        (statistic, lower_ci, upper_ci)
    """
    if len(data) == 0:
        return 0.0, 0.0, 0.0
    
    # Calculate statistic on original data
    stat = statistic_func(data)
    
    # Bootstrap samples
    n = len(data)
    bootstrap_stats = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        bootstrap_sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stat = statistic_func(bootstrap_sample)
        bootstrap_stats.append(bootstrap_stat)
    
    bootstrap_stats = np.array(bootstrap_stats)
    
    # Calculate confidence interval
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    lower_ci = np.percentile(bootstrap_stats, lower_percentile)
    upper_ci = np.percentile(bootstrap_stats, upper_percentile)
    
    return stat, lower_ci, upper_ci


def run_threshold_sweep(
    tickers: List[str],
    start_date: datetime,
    end_date: datetime,
    thresholds: List[float] = None
) -> pd.DataFrame:
    """Run threshold sweep analysis"""
    
    if thresholds is None:
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    print("\n" + "="*80)
    print("THRESHOLD SWEEP ANALYSIS")
    print("="*80)
    print(f"\n📅 Period: {start_date.date()} to {end_date.date()}")
    print(f"📊 Tickers: {len(tickers)}")
    print(f"🔍 Thresholds: {thresholds}")
    
    results = []
    
    for threshold in thresholds:
        print(f"\n{'='*80}")
        print(f"Testing Robustness Threshold: {threshold}")
        print(f"{'='*80}")
        
        try:
            # Run walk-forward backtest with this threshold
            backtester = WalkForwardBacktester(
                training_window_days=252,
                testing_window_days=63,
                rebalance_freq="M",
                min_robustness=threshold,
                max_positions=10,
                transaction_cost_bps=5.0
            )
            
            # Note: This will use synthetic data if yfinance not available
            # For real data, we'd need to modify the backtester to accept data
            result = await backtester.run_walk_forward_backtest(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                benchmark_ticker="SPY"
            )
            
            if result is None:
                print(f"   ⚠️  No results for threshold {threshold}")
                continue
            
            # Extract robustness vs returns data
            robustness_df = result.robustness_vs_returns
            
            if robustness_df.empty:
                print(f"   ⚠️  No robustness data for threshold {threshold}")
                continue
            
            # Filter by threshold
            high_rob = robustness_df[robustness_df["robustness"] >= threshold]
            low_rob = robustness_df[robustness_df["robustness"] < threshold]
            
            # Calculate statistics for high robustness bucket
            if len(high_rob) > 0:
                high_returns = high_rob["forward_return"].values
                
                # Mean and CI
                mean_ret, mean_lower, mean_upper = bootstrap_ci(
                    high_returns, np.mean, n_bootstrap=1000
                )
                
                # Median and CI
                median_ret, median_lower, median_upper = bootstrap_ci(
                    high_returns, np.median, n_bootstrap=1000
                )
                
                # Win rate
                win_rate = (high_returns > 0).mean()
                win_rate_ci_lower = stats.binom.interval(0.95, len(high_returns), win_rate)[0] / len(high_returns)
                win_rate_ci_upper = stats.binom.interval(0.95, len(high_returns), win_rate)[1] / len(high_returns)
                
                high_rob_stats = {
                    "count": len(high_rob),
                    "mean_return": mean_ret,
                    "mean_lower_ci": mean_lower,
                    "mean_upper_ci": mean_upper,
                    "median_return": median_ret,
                    "median_lower_ci": median_lower,
                    "median_upper_ci": median_upper,
                    "win_rate": win_rate,
                    "win_rate_lower_ci": win_rate_ci_lower,
                    "win_rate_upper_ci": win_rate_ci_upper,
                    "std_return": np.std(high_returns)
                }
            else:
                high_rob_stats = {
                    "count": 0,
                    "mean_return": 0.0,
                    "mean_lower_ci": 0.0,
                    "mean_upper_ci": 0.0,
                    "median_return": 0.0,
                    "median_lower_ci": 0.0,
                    "median_upper_ci": 0.0,
                    "win_rate": 0.0,
                    "win_rate_lower_ci": 0.0,
                    "win_rate_upper_ci": 0.0,
                    "std_return": 0.0
                }
            
            # Calculate statistics for low robustness bucket
            if len(low_rob) > 0:
                low_returns = low_rob["forward_return"].values
                
                mean_ret, mean_lower, mean_upper = bootstrap_ci(
                    low_returns, np.mean, n_bootstrap=1000
                )
                
                median_ret, median_lower, median_upper = bootstrap_ci(
                    low_returns, np.median, n_bootstrap=1000
                )
                
                win_rate = (low_returns > 0).mean()
                win_rate_ci_lower = stats.binom.interval(0.95, len(low_returns), win_rate)[0] / len(low_returns)
                win_rate_ci_upper = stats.binom.interval(0.95, len(low_returns), win_rate)[1] / len(low_returns)
                
                low_rob_stats = {
                    "count": len(low_rob),
                    "mean_return": mean_ret,
                    "mean_lower_ci": mean_lower,
                    "mean_upper_ci": mean_upper,
                    "median_return": median_ret,
                    "median_lower_ci": median_lower,
                    "median_upper_ci": median_upper,
                    "win_rate": win_rate,
                    "win_rate_lower_ci": win_rate_ci_lower,
                    "win_rate_upper_ci": win_rate_ci_upper,
                    "std_return": np.std(low_returns)
                }
            else:
                low_rob_stats = {
                    "count": 0,
                    "mean_return": 0.0,
                    "mean_lower_ci": 0.0,
                    "mean_upper_ci": 0.0,
                    "median_return": 0.0,
                    "median_lower_ci": 0.0,
                    "median_upper_ci": 0.0,
                    "win_rate": 0.0,
                    "win_rate_lower_ci": 0.0,
                    "win_rate_upper_ci": 0.0,
                    "std_return": 0.0
                }
            
            # Overall portfolio performance
            results.append({
                "threshold": threshold,
                "high_rob_count": high_rob_stats["count"],
                "high_rob_mean": high_rob_stats["mean_return"],
                "high_rob_mean_lower": high_rob_stats["mean_lower_ci"],
                "high_rob_mean_upper": high_rob_stats["mean_upper_ci"],
                "high_rob_median": high_rob_stats["median_return"],
                "high_rob_median_lower": high_rob_stats["median_lower_ci"],
                "high_rob_median_upper": high_rob_stats["median_upper_ci"],
                "high_rob_win_rate": high_rob_stats["win_rate"],
                "high_rob_win_rate_lower": high_rob_stats["win_rate_lower_ci"],
                "high_rob_win_rate_upper": high_rob_stats["win_rate_upper_ci"],
                "low_rob_count": low_rob_stats["count"],
                "low_rob_mean": low_rob_stats["mean_return"],
                "low_rob_mean_lower": low_rob_stats["mean_lower_ci"],
                "low_rob_mean_upper": low_rob_stats["mean_upper_ci"],
                "low_rob_median": low_rob_stats["median_return"],
                "low_rob_median_lower": low_rob_stats["median_lower_ci"],
                "low_rob_median_upper": low_rob_stats["median_upper_ci"],
                "low_rob_win_rate": low_rob_stats["win_rate"],
                "low_rob_win_rate_lower": low_rob_stats["win_rate_lower_ci"],
                "low_rob_win_rate_upper": low_rob_stats["win_rate_upper_ci"],
                "outperformance_mean": high_rob_stats["mean_return"] - low_rob_stats["mean_return"],
                "outperformance_median": high_rob_stats["median_return"] - low_rob_stats["median_return"],
                "portfolio_annual_return": result.annual_return,
                "portfolio_sharpe": result.sharpe_ratio,
                "portfolio_alpha": result.alpha
            })
            
            # Print summary
            print(f"\n📊 Results for Threshold {threshold}:")
            print(f"   High Robustness (≥{threshold}):")
            print(f"     Count: {high_rob_stats['count']}")
            print(f"     Mean Return: {high_rob_stats['mean_return']:.4f} [{high_rob_stats['mean_lower_ci']:.4f}, {high_rob_stats['mean_upper_ci']:.4f}]")
            print(f"     Median Return: {high_rob_stats['median_return']:.4f} [{high_rob_stats['median_lower_ci']:.4f}, {high_rob_stats['median_upper_ci']:.4f}]")
            print(f"     Win Rate: {high_rob_stats['win_rate']:.2%} [{high_rob_stats['win_rate_lower_ci']:.2%}, {high_rob_stats['win_rate_upper_ci']:.2%}]")
            print(f"   Low Robustness (<{threshold}):")
            print(f"     Count: {low_rob_stats['count']}")
            print(f"     Mean Return: {low_rob_stats['mean_return']:.4f} [{low_rob_stats['mean_lower_ci']:.4f}, {low_rob_stats['mean_upper_ci']:.4f}]")
            print(f"     Median Return: {low_rob_stats['median_return']:.4f} [{low_rob_stats['median_lower_ci']:.4f}, {low_rob_stats['median_upper_ci']:.4f}]")
            print(f"     Win Rate: {low_rob_stats['win_rate']:.2%} [{low_rob_stats['win_rate_lower_ci']:.2%}, {low_rob_stats['win_rate_upper_ci']:.2%}]")
            print(f"   Outperformance:")
            print(f"     Mean: {high_rob_stats['mean_return'] - low_rob_stats['mean_return']:.4f}")
            print(f"     Median: {high_rob_stats['median_return'] - low_rob_stats['median_return']:.4f}")
            
        except Exception as e:
            print(f"   ❌ Error at threshold {threshold}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not results:
        print("\n❌ No results generated")
        return pd.DataFrame()
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Print summary table
    print("\n" + "="*80)
    print("THRESHOLD SWEEP SUMMARY")
    print("="*80)
    print("\nThreshold | High N | High Median [CI] | Low N | Low Median [CI] | Outperf")
    print("-" * 80)
    
    for _, row in results_df.iterrows():
        high_ci = f"[{row['high_rob_median_lower']:.3f}, {row['high_rob_median_upper']:.3f}]"
        low_ci = f"[{row['low_rob_median_lower']:.3f}, {row['low_rob_median_upper']:.3f}]"
        print(f"{row['threshold']:>9.1f} | {row['high_rob_count']:>6.0f} | {row['high_rob_median']:>7.4f} {high_ci:>20} | "
              f"{row['low_rob_count']:>5.0f} | {row['low_rob_median']:>7.4f} {low_ci:>20} | "
              f"{row['outperformance_median']:>7.4f}")
    
    # Save results
    output_file = f"threshold_sweep_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n📄 Results saved to: {output_file}")
    
    return results_df


async def main():
    """Main function"""
    # Test on smaller universe for speed
    test_tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ", "V", "PG", "MA"]
    
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    results_df = await run_threshold_sweep(
        tickers=test_tickers,
        start_date=start_date,
        end_date=end_date,
        thresholds=thresholds
    )
    
    if not results_df.empty:
        print("\n✅ Threshold sweep complete!")
    else:
        print("\n❌ Threshold sweep failed")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

