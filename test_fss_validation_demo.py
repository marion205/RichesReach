#!/usr/bin/env python3
"""
FSS v3.0 Validation Demo
Demonstrates comprehensive validation with synthetic data to show the framework.
"""
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_engine import get_fss_engine
from core.fss_backtest import get_fss_backtester
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def generate_realistic_market_data(n_days=500, n_stocks=10, seed=42):
    """Generate realistic market data with different regimes"""
    np.random.seed(seed)
    dates = pd.bdate_range(end=datetime.now(), periods=n_days)
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META", "JNJ", "V", "JPM"][:n_stocks]
    
    # Create different market regimes
    regime_changes = {
        0: "Expansion",      # Days 0-150: Bull market
        150: "Parabolic",    # Days 150-200: High growth
        200: "Crisis",       # Days 200-300: Crash
        300: "Deflation",    # Days 300-400: Slow decline
        400: "Expansion",    # Days 400+: Recovery
    }
    
    prices_dict = {}
    volumes_dict = {}
    
    for ticker in tickers:
        prices = []
        volumes = []
        base_price = 150.0
        
        for i, date in enumerate(dates):
            # Determine current regime
            current_regime = "Expansion"
            for change_day, regime in sorted(regime_changes.items()):
                if i >= change_day:
                    current_regime = regime
            
            # Generate returns based on regime
            if current_regime == "Expansion":
                daily_ret = np.random.normal(0.0006, 0.018, 1)[0]
            elif current_regime == "Parabolic":
                daily_ret = np.random.normal(0.0012, 0.025, 1)[0]
            elif current_regime == "Crisis":
                daily_ret = np.random.normal(-0.002, 0.035, 1)[0]
            elif current_regime == "Deflation":
                daily_ret = np.random.normal(-0.0005, 0.015, 1)[0]
            else:
                daily_ret = np.random.normal(0.0004, 0.020, 1)[0]
            
            # Update price
            if i == 0:
                price = base_price
            else:
                price = prices[-1] * (1 + daily_ret)
            
            prices.append(price)
            
            # Volume (higher during crisis)
            base_vol = 50_000_000
            if current_regime == "Crisis":
                vol_mult = np.random.uniform(1.5, 3.0)
            else:
                vol_mult = np.random.uniform(0.8, 1.2)
            volumes.append(base_vol * vol_mult)
        
        prices_dict[ticker] = pd.Series(prices, index=dates)
        volumes_dict[ticker] = pd.Series(volumes, index=dates)
    
    prices_df = pd.DataFrame(prices_dict)
    volumes_df = pd.DataFrame(volumes_dict)
    
    # SPY benchmark
    spy_rets = []
    for i in range(n_days):
        current_regime = "Expansion"
        for change_day, regime in sorted(regime_changes.items()):
            if i >= change_day:
                current_regime = regime
        
        if current_regime == "Expansion":
            ret = np.random.normal(0.0004, 0.015, 1)[0]
        elif current_regime == "Parabolic":
            ret = np.random.normal(0.0008, 0.020, 1)[0]
        elif current_regime == "Crisis":
            ret = np.random.normal(-0.0015, 0.025, 1)[0]
        elif current_regime == "Deflation":
            ret = np.random.normal(-0.0003, 0.012, 1)[0]
        else:
            ret = np.random.normal(0.0003, 0.018, 1)[0]
        spy_rets.append(ret)
    
    spy = pd.Series(400 * np.exp(np.cumsum(spy_rets)), index=dates)
    
    # VIX (higher during crisis)
    vix = []
    for i in range(n_days):
        current_regime = "Expansion"
        for change_day, regime in sorted(regime_changes.items()):
            if i >= change_day:
                current_regime = regime
        
        if current_regime == "Crisis":
            vix_val = np.random.uniform(30, 50)
        elif current_regime == "Parabolic":
            vix_val = np.random.uniform(20, 30)
        elif current_regime == "Deflation":
            vix_val = np.random.uniform(15, 25)
        else:
            vix_val = np.random.uniform(12, 20)
        vix.append(vix_val)
    
    vix_series = pd.Series(vix, index=dates)
    
    return prices_df, volumes_df, spy, vix_series


def run_validation_demo():
    """Run comprehensive validation demo"""
    
    print("\n" + "="*80)
    print("FSS v3.0 Comprehensive Validation Demo")
    print("="*80)
    print("Using synthetic data to demonstrate validation framework\n")
    
    # Generate data
    print("📊 Generating realistic market data with multiple regimes...")
    prices, volumes, spy, vix = generate_realistic_market_data(n_days=500, n_stocks=10)
    print(f"   ✅ Generated {len(prices)} days of data for {len(prices.columns)} stocks\n")
    
    # Calculate FSS
    print("📈 Calculating FSS v3.0 scores...")
    fss_engine = get_fss_engine()
    fss_data = fss_engine.compute_fss_v3(
        prices=prices,
        volumes=volumes,
        spy=spy,
        vix=vix
    )
    print("   ✅ FSS calculation complete\n")
    
    # Test periods
    test_periods = [
        {"name": "Bull Market (Days 0-150)", "start": 0, "end": 150, "expected_regime": "Expansion"},
        {"name": "Parabolic (Days 150-200)", "start": 150, "end": 200, "expected_regime": "Parabolic"},
        {"name": "Crisis (Days 200-300)", "start": 200, "end": 300, "expected_regime": "Crisis"},
        {"name": "Recovery (Days 400-500)", "start": 400, "end": 500, "expected_regime": "Expansion"},
    ]
    
    from core.fss_backtest import FSSBacktester
    backtester = FSSBacktester(transaction_cost_bps=10.0)
    results = []
    
    for period in test_periods:
        print(f"\n📊 Testing: {period['name']}")
        print("-" * 80)
        
        # Slice data
        prices_period = prices.iloc[period['start']:period['end']]
        volumes_period = volumes.iloc[period['start']:period['end']]
        spy_period = spy.iloc[period['start']:period['end']]
        vix_period = vix.iloc[period['start']:period['end']]
        fss_period = fss_data["FSS"].iloc[period['start']:period['end']]
        
        if len(prices_period) < 50:
            print(f"   ⚠️  Insufficient data points")
            continue
        
        # Create daily regime series
        regime_series = pd.Series(index=prices_period.index, dtype=object)
        for i, date in enumerate(prices_period.index):
            date_idx = spy_period.index.get_loc(date)
            window_start = max(0, date_idx - 200)
            spy_window = spy_period.iloc[window_start:date_idx+1]
            vix_window = vix_period.iloc[window_start:date_idx+1]
            
            if len(spy_window) >= 200:
                regime_result = fss_engine.detect_market_regime(spy_window, vix_window)
                regime_series.loc[date] = regime_result.regime
            else:
                regime_series.loc[date] = "Expansion"
        
        # 1. Always-In backtest
        backtest_always_in = backtester.backtest_rank_strategy(
            prices=prices_period,
            fss=fss_period,
            spy=spy_period,
            rebalance_freq="M",
            top_n=5,
            cash_out_on_crisis=False
        )
        
        # 2. Regime-Aware backtest
        backtest_result = backtester.backtest_rank_strategy(
            prices=prices_period,
            fss=fss_period,
            spy=spy_period,
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
            if horizon < len(prices_period) // 3:
                forward_returns = backtester.forward_return(prices_period, horizon=horizon)
                ic_series = backtester.calculate_ic(fss_period, forward_returns)
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
        print(f"   Regime: {result['regime']}")
        print(f"   Annual Return (Regime-Aware): {backtest_result.annual_return*100:.1f}%")
        print(f"   Annual Return (Always-In): {backtest_always_in.annual_return*100:.1f}%")
        print(f"   Safety Alpha: {safety_alpha*100:.1f}% (improvement from cash-out)")
        print(f"   Sharpe Ratio: {backtest_result.sharpe_ratio:.2f} (vs {backtest_always_in.sharpe_ratio:.2f} Always-In)")
        print(f"   Max Drawdown: {backtest_result.max_drawdown*100:.1f}% (vs {backtest_always_in.max_drawdown*100:.1f}% Always-In)")
        print(f"   DD Improvement: {dd_improvement*100:.1f}% (reduction)")
        print(f"   IC (21d): {mean_ic:.3f}")
        if backtest_result.alpha:
            print(f"   Alpha vs SPY: {backtest_result.alpha*100:.1f}%")
    
    # Summary
    if results:
        print("\n" + "="*80)
        print("Validation Summary")
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
        print(f"\nRegime-Aware Cash-Out Benefits:")
        print(f"  Average Safety Alpha: {avg_safety_alpha*100:.1f}%")
        print(f"  Average DD Improvement: {avg_dd_improvement*100:.1f}%")
        print(f"  Average Sharpe Improvement: {avg_sharpe_improvement:.2f}")
        
        # Targets
        print("\nTargets (Best-in-Class):")
        print(f"  Sharpe > 1.1: {'✅' if avg_sharpe > 1.1 else '❌'} ({avg_sharpe:.2f})")
        print(f"  IC > 0.10: {'✅' if avg_ic > 0.10 else '❌'} ({avg_ic:.3f})")
        print(f"  Safety Alpha > 2%: {'✅' if avg_safety_alpha > 0.02 else '❌'} ({avg_safety_alpha*100:.1f}%)")
        print(f"  DD Improvement > 30%: {'✅' if avg_dd_improvement > 0.30 else '❌'} ({avg_dd_improvement*100:.1f}%)")
    
    print("\n" + "="*80)
    print("✅ Validation Demo Complete!")
    print("="*80)
    print("\nNote: This uses synthetic data. Real results will vary based on:")
    print("  - Actual market conditions")
    print("  - Real fundamental data")
    print("  - Current market regime")
    print("  - API data availability\n")


if __name__ == "__main__":
    run_validation_demo()

