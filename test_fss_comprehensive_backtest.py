#!/usr/bin/env python3
"""
Comprehensive FSS Backtest
Tests FSS v3.0 across multiple time periods and regimes.
"""
import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_engine import get_fss_engine
from core.fss_backtest import get_fss_backtester
from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_monte_carlo_stress_test(
    prices: pd.DataFrame,
    spy: pd.Series,
    crash_magnitude: float = -0.15,
    duration_days: int = 5,
    crash_start_idx: int = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Injects a synthetic 'Flash Crash' into the data to test FSS reaction.
    
    Args:
        prices: Price DataFrame
        spy: SPY benchmark Series
        crash_magnitude: Magnitude of crash (e.g., -0.15 for -15%)
        duration_days: Number of days over which crash occurs
        crash_start_idx: Optional specific index to start crash (if None, random)
    
    Returns:
        Stressed prices and SPY
    """
    stressed_prices = prices.copy()
    stressed_spy = spy.copy()
    
    # Pick a random point in the middle of the series to start the crash
    if crash_start_idx is None:
        crash_start_idx = np.random.randint(len(prices) // 4, len(prices) // 2)
    
    # Ensure we don't go out of bounds
    crash_end_idx = min(crash_start_idx + duration_days, len(prices))
    
    # Simulate a rapid decay over 'duration_days'
    for i in range(crash_end_idx - crash_start_idx):
        idx = crash_start_idx + i
        if idx >= len(prices):
            break
        
        # Daily impact (cumulative)
        daily_impact = 1 + (crash_magnitude / duration_days) * (i + 1)
        
        # Apply to all stocks (with beta > 1 for individual stocks)
        for ticker in stressed_prices.columns:
            stock_beta = 1.2  # Stocks drop more than market
            stock_impact = 1 + (crash_magnitude * stock_beta / duration_days) * (i + 1)
            if idx > 0:
                stressed_prices.iloc[idx, stressed_prices.columns.get_loc(ticker)] = \
                    stressed_prices.iloc[idx-1, stressed_prices.columns.get_loc(ticker)] * stock_impact
        
        # Apply to SPY
        if idx > 0:
            stressed_spy.iloc[idx] = stressed_spy.iloc[idx-1] * daily_impact
    
    return stressed_prices, stressed_spy


def measure_regime_latency(
    spy: pd.Series,
    vix: pd.Series,
    fss_engine,
    crash_start_idx: int,
    crash_duration: int,
    window_size: int = 200
) -> dict:
    """
    Measure how quickly FSS detects regime shift to Crisis.
    
    Returns:
        dict with detection_day, latency_days, detected_correctly
    """
    detection_day = None
    detected_correctly = False
    
    # Check regime detection day by day after crash starts
    for day_offset in range(crash_duration + 10):  # Check up to 10 days after crash
        check_idx = crash_start_idx + day_offset
        
        if check_idx < window_size or check_idx >= len(spy):
            continue
        
        # Get rolling window
        spy_window = spy.iloc[check_idx - window_size:check_idx + 1]
        vix_window = vix.iloc[check_idx - window_size:check_idx + 1] if vix is not None else None
        
        if len(spy_window) < window_size:
            continue
        
        # Detect regime
        regime_result = fss_engine.detect_market_regime(spy_window, vix_window)
        
        # Check if Crisis detected
        if regime_result.regime == "Crisis":
            if detection_day is None:
                detection_day = day_offset
                detected_correctly = True
            break
    
    latency_days = detection_day if detection_day is not None else crash_duration + 10
    
    return {
        "detection_day": detection_day,
        "latency_days": latency_days,
        "detected_correctly": detected_correctly,
        "regime_shift_speed": "Fast" if latency_days <= 2 else "Medium" if latency_days <= 5 else "Slow"
    }


async def comprehensive_backtest():
    """Run comprehensive backtest across multiple periods"""
    
    print("\n" + "="*80)
    print("FSS v3.0 Comprehensive Backtest")
    print("="*80 + "\n")
    
    # Test periods (recent market cycles)
    test_periods = [
        {
            "name": "2024 Bull Market",
            "start": "2024-01-01",
            "end": "2024-12-31",
            "expected_regime": "Expansion"
        },
        {
            "name": "2023 Recovery",
            "start": "2023-01-01",
            "end": "2023-12-31",
            "expected_regime": "Expansion"
        },
        {
            "name": "2022 Bear Market",
            "start": "2022-01-01",
            "end": "2022-12-31",
            "expected_regime": "Crisis"
        }
    ]
    
    # Test universe
    test_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META", "JNJ", "V", "JPM"]
    
    results = []
    
    for period in test_periods:
        print(f"\n📊 Testing: {period['name']}")
        print(f"   Period: {period['start']} to {period['end']}")
        print("-" * 80)
        
        try:
            # Fetch data for period
            pipeline = get_fss_data_pipeline()
            async with pipeline:
                # Calculate lookback (need 252 days before start)
                start_date = datetime.strptime(period['start'], "%Y-%m-%d")
                lookback_start = start_date - timedelta(days=400)  # Extra buffer
                
                request = FSSDataRequest(
                    tickers=test_stocks,
                    lookback_days=400,  # Enough to cover period + lookback
                    include_fundamentals=False
                )
                
                data_result = await pipeline.fetch_fss_data(request)
            
            # CRITICAL FIX: Compute FSS on FULL dataset first (including buffer)
            # This ensures technical indicators (MAs, volatility) have history to work with
            fss_engine = get_fss_engine()
            fss_full = fss_engine.compute_fss_v3(
                prices=data_result.prices,  # Full dataset
                volumes=data_result.volumes,  # Full dataset
                spy=data_result.spy,  # Full dataset
                vix=data_result.vix  # Full dataset
            )
            
            # NOW slice to test period (after indicators are "warmed up")
            end_date = datetime.strptime(period['end'], "%Y-%m-%d")
            
            # Use date-based slicing to ensure clean period boundaries
            try:
                prices_test = data_result.prices.loc[start_date:end_date]
                volumes_test = data_result.volumes.loc[start_date:end_date]
                spy_test = data_result.spy.loc[start_date:end_date]
                vix_test = data_result.vix.loc[start_date:end_date] if data_result.vix is not None else None
                fss_test = fss_full["FSS"].loc[start_date:end_date]
            except KeyError:
                print(f"   ⚠️  Date range not found in data")
                continue
            
            if len(prices_test) < 50:
                print(f"   ⚠️  Insufficient data points ({len(prices_test)})")
                continue
            
            # Detect regime on test period (daily regime series)
            # Create daily regime series for the test period
            regime_series = pd.Series(index=prices_test.index, dtype=object)
            for date in prices_test.index:
                # Use rolling window ending at this date
                date_idx = spy_test.index.get_loc(date)
                window_start = max(0, date_idx - 200)
                spy_window = spy_test.iloc[window_start:date_idx+1]
                vix_window = vix_test.iloc[window_start:date_idx+1] if vix_test is not None else None
                
                if len(spy_window) >= 200:
                    regime_result = fss_engine.detect_market_regime(spy_window, vix_window)
                    regime_series.loc[date] = regime_result.regime
                else:
                    regime_series.loc[date] = "Expansion"  # Default
            
            # Backtest TWICE: Always-In vs Regime-Aware
            backtester = get_fss_backtester(transaction_cost_bps=10.0)  # 10 bps for slippage + spread
            
            # 1. Always-In (baseline)
            backtest_always_in = backtester.backtest_rank_strategy(
                prices=prices_test,
                fss=fss_test,
                spy=spy_test,
                rebalance_freq="M",
                top_n=5,
                cash_out_on_crisis=False  # Always invested
            )
            
            # 2. Regime-Aware (with cash-out)
            backtest_result = backtester.backtest_rank_strategy(
                prices=prices_test,
                fss=fss_test,
                spy=spy_test,
                rebalance_freq="M",
                top_n=5,
                regime=regime_series,
                cash_out_on_crisis=True,  # Go to cash during Crisis/Deflation
                cash_return_rate=0.04  # 4% annual risk-free rate
            )
            
            # Calculate "Safety Alpha" (improvement from regime-aware cash-out)
            safety_alpha = backtest_result.annual_return - backtest_always_in.annual_return
            dd_improvement = backtest_always_in.max_drawdown - backtest_result.max_drawdown
            
            # Calculate Multi-Horizon IC (1-day, 5-day, 21-day) - avoid look-ahead trap
            # Use shorter horizons that fit within test period
            ic_results = {}
            ic_std_results = {}
            ic_tstats = {}
            
            # Only use horizons that fit in the test period
            max_horizon = min(63, len(prices_test) // 3)  # Don't use more than 1/3 of period
            horizons = [h for h in [1, 5, 21, 63] if h <= max_horizon]
            
            for horizon in horizons:
                forward_returns = backtester.forward_return(prices_test, horizon=horizon)
                ic_series = backtester.calculate_ic(fss_test, forward_returns)
                
                if len(ic_series) > 0:
                    mean_ic = ic_series.mean()
                    std_ic = ic_series.std()
                    t_stat = mean_ic / (std_ic / np.sqrt(len(ic_series))) if std_ic > 0 else 0
                    
                    ic_results[f'ic_{horizon}d'] = mean_ic
                    ic_std_results[f'ic_{horizon}d'] = std_ic
                    ic_tstats[f'ic_{horizon}d'] = t_stat
                else:
                    ic_results[f'ic_{horizon}d'] = 0.0
                    ic_std_results[f'ic_{horizon}d'] = 0.0
                    ic_tstats[f'ic_{horizon}d'] = 0.0
            
            # Primary IC: Use 21-day (1 month) as it's more stable than 1-day but fits in test period
            mean_ic = ic_results.get('ic_21d', ic_results.get('ic_5d', 0.0))
            ic_std = ic_std_results.get('ic_21d', ic_std_results.get('ic_5d', 0.0))
            ic_tstat = ic_tstats.get('ic_21d', ic_tstats.get('ic_5d', 0.0))
            
            # Calculate Return on Turnover (ROT) - already included in backtest_result
            # Transaction costs are already applied in backtest_rank_strategy
            # Calculate additional metrics
            estimated_turnover = backtest_result.turnover.mean() * 252 if hasattr(backtest_result, 'turnover') else 12 * 0.5
            net_return = backtest_result.annual_return  # Already net of transaction costs
            rot = net_return / estimated_turnover if estimated_turnover > 0 else 0
            
            # Calculate IC Stability Score (standard deviation and t-stat)
            # High IC with low std = stable signal
            ic_stability = 1.0 / (1.0 + ic_std) if ic_std > 0 else 0.0  # Higher is better
            
            # Calculate IC decay (from 1-day to longest horizon)
            first_ic = ic_results.get('ic_1d', 0.0)
            ic_decay = (first_ic - mean_ic) / first_ic if first_ic != 0 else 0
            
            # Initialize safety alpha variables (will be set if regime-aware backtest runs)
            safety_alpha = 0.0
            dd_improvement = 0.0
            backtest_always_in = None
            
            # Store results
            period_result = {
                "period": period['name'],
                "regime": regime_series.iloc[-1] if len(regime_series) > 0 else "Unknown",
                "annual_return": backtest_result.annual_return,
                "annual_return_always_in": backtest_always_in.annual_return,
                "safety_alpha": safety_alpha,
                "net_return": net_return,
                "sharpe_ratio": backtest_result.sharpe_ratio,
                "sharpe_ratio_always_in": backtest_always_in.sharpe_ratio,
                "max_drawdown": backtest_result.max_drawdown,
                "max_drawdown_always_in": backtest_always_in.max_drawdown,
                "dd_improvement": dd_improvement,
                "alpha": backtest_result.alpha,
                "ic_1d": ic_results.get('ic_1d', 0.0),
                "ic_5d": ic_results.get('ic_5d', 0.0),
                "ic_21d": ic_results.get('ic_21d', 0.0),
                "ic_63d": ic_results.get('ic_63d', 0.0),
                "ic_mean": mean_ic,
                "ic_std": ic_std,
                "ic_tstat": ic_tstat,
                "ic_stability": ic_stability,
                "ic_decay": ic_decay,
                "win_rate": backtest_result.win_rate,
                "return_on_turnover": rot,
                "turnover": estimated_turnover
            }
            results.append(period_result)
            
            # Display
            print(f"   Regime: {period_result['regime']}")
            print(f"   Annual Return: {backtest_result.annual_return*100:.1f}% (Regime-Aware)")
            print(f"   Annual Return (Always-In): {backtest_always_in.annual_return*100:.1f}%")
            print(f"   Safety Alpha: {safety_alpha*100:.1f}% (improvement from cash-out)")
            print(f"   Sharpe Ratio: {backtest_result.sharpe_ratio:.2f} (vs {backtest_always_in.sharpe_ratio:.2f} Always-In)")
            print(f"   Max Drawdown: {backtest_result.max_drawdown*100:.1f}% (vs {backtest_always_in.max_drawdown*100:.1f}% Always-In)")
            print(f"   DD Improvement: {dd_improvement*100:.1f}% (reduction from cash-out)")
            print(f"   Alpha vs SPY: {backtest_result.alpha*100:.1f}%" if backtest_result.alpha else "   Alpha: N/A")
            
            # Multi-horizon IC display
            ic_display = []
            for h in horizons:
                ic_val = ic_results.get(f'ic_{h}d', 0.0)
                t_val = ic_tstats.get(f'ic_{h}d', 0.0)
                sig = "✅" if abs(t_val) > 2.0 else "❌"
                ic_display.append(f"{h}d:{ic_val:.3f}(t={t_val:.1f}){sig}")
            print(f"   IC Multi-Horizon: {' | '.join(ic_display)}")
            
            print(f"   IC Stability (1/(1+std)): {ic_stability:.3f}")
            print(f"   IC Decay (1d→21d): {ic_decay*100:.1f}%")
            print(f"   Return on Turnover: {rot*100:.2f}%")
            print(f"   Win Rate: {backtest_result.win_rate*100:.1f}%")
            
            # --- MONTE CARLO STRESS TEST ---
            print(f"\n   🔥 Running Stress Test: Simulated Flash Crash")
            
            # Apply stress test (15% crash over 5 days)
            crash_magnitude = -0.15
            crash_duration = 5
            crash_start_idx = len(prices_test) // 3  # Start crash at 1/3 into period
            
            stressed_prices, stressed_spy = apply_monte_carlo_stress_test(
                prices_test,
                spy_test,
                crash_magnitude=crash_magnitude,
                duration_days=crash_duration,
                crash_start_idx=crash_start_idx
            )
            
            # Recalculate FSS on stressed data (need full buffer again)
            # Recompute on full dataset with stressed prices inserted
            prices_stressed_full = data_result.prices.copy()
            prices_stressed_full.loc[prices_test.index] = stressed_prices
            
            spy_stressed_full = data_result.spy.copy()
            spy_stressed_full.loc[spy_test.index] = stressed_spy
            
            # Recompute FSS on full stressed dataset
            fss_stressed_full = fss_engine.compute_fss_v3(
                prices=prices_stressed_full,
                volumes=data_result.volumes,
                spy=spy_stressed_full,
                vix=data_result.vix
            )
            
            # Slice to test period
            fss_stressed = fss_stressed_full["FSS"].loc[start_date:end_date]
            
            # Detect regime on stressed data
            regime_stressed = fss_engine.detect_market_regime(stressed_spy, vix_test)
            
            # Measure regime latency (how fast does it detect Crisis?)
            regime_latency = measure_regime_latency(
                stressed_spy,
                vix_test,
                fss_engine,
                crash_start_idx,
                crash_duration
            )
            
            # Create regime series for stressed data (with cash-out)
            regime_stressed_series = pd.Series(regime_stressed.regime, index=stressed_prices.index)
            
            # Run backtest on stressed data (with cash-out on crisis)
            stress_result = backtester.backtest_rank_strategy(
                prices=stressed_prices,
                fss=fss_stressed,
                spy=stressed_spy,
                rebalance_freq="M",
                top_n=5,
                regime=regime_stressed_series,
                cash_out_on_crisis=True  # Go to cash when Crisis detected
            )
            
            # Calculate Recovery Factor (Robustness Ratio)
            # How much worse is stressed drawdown vs baseline?
            if backtest_result.max_drawdown != 0:
                recovery_ratio = abs(stress_result.max_drawdown / backtest_result.max_drawdown)
            else:
                recovery_ratio = float('inf') if stress_result.max_drawdown < 0 else 1.0
            
            # Drawdown sensitivity
            dd_impact = stress_result.max_drawdown - backtest_result.max_drawdown
            
            # Store stress test results
            period_result.update({
                "stress_max_dd": stress_result.max_drawdown,
                "stress_annual_return": stress_result.annual_return,
                "stress_sharpe": stress_result.sharpe_ratio,
                "recovery_ratio": recovery_ratio,
                "dd_impact": dd_impact,
                "regime_detected": regime_stressed.regime,
                "regime_latency_days": regime_latency["latency_days"],
                "regime_shift_speed": regime_latency["regime_shift_speed"],
                "crisis_detected": regime_latency["detected_correctly"]
            })
            
            # Display stress test results
            print(f"   Stress Max DD: {stress_result.max_drawdown*100:.1f}% (vs {backtest_result.max_drawdown*100:.1f}% baseline)")
            print(f"   DD Impact: {dd_impact*100:.1f}%")
            print(f"   Recovery Ratio: {recovery_ratio:.2f}x")
            print(f"   Regime Detected: {regime_stressed.regime}")
            print(f"   Regime Latency: {regime_latency['latency_days']} days ({regime_latency['regime_shift_speed']})")
            print(f"   Crisis Detected: {'✅' if regime_latency['detected_correctly'] else '❌'}")
            
            if recovery_ratio > 2.0:
                print("   ⚠️  WARNING: High drawdown sensitivity - portfolio vulnerable to crashes")
            elif recovery_ratio < 1.5:
                print("   ✅ Good: Portfolio shows resilience to flash crashes")
            
            if regime_latency['latency_days'] > 5:
                print("   ⚠️  WARNING: Slow regime detection - may miss early warning signals")
            elif regime_latency['latency_days'] <= 2:
                print("   ✅ Excellent: Fast regime detection")
            
        except Exception as e:
            logger.error(f"Error in {period['name']}: {e}", exc_info=True)
            print(f"   ❌ Error: {e}")
            continue
    
    # Summary
    if results:
        print("\n" + "="*80)
        print("Summary Across All Periods")
        print("="*80)
        
        avg_return = np.mean([r['annual_return'] for r in results])
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in results])
        avg_ic = np.mean([r['ic_mean'] for r in results])
        avg_ic_std = np.mean([r['ic_std'] for r in results])
        avg_ic_tstat = np.mean([r['ic_tstat'] for r in results])
        avg_ic_stability = np.mean([r['ic_stability'] for r in results])
        avg_alpha = np.mean([r['alpha'] for r in results if r['alpha']])
        avg_rot = np.mean([r['return_on_turnover'] for r in results])
        avg_safety_alpha = np.mean([r.get('safety_alpha', 0) for r in results])
        avg_dd_improvement = np.mean([r.get('dd_improvement', 0) for r in results])
        avg_sharpe_improvement = np.mean([r.get('sharpe_ratio', 0) - r.get('sharpe_ratio_always_in', 0) for r in results])
        
        # Stress test averages
        stress_results = [r for r in results if 'stress_max_dd' in r]
        if stress_results:
            avg_stress_dd = np.mean([r['stress_max_dd'] for r in stress_results])
            avg_recovery_ratio = np.mean([r['recovery_ratio'] for r in stress_results])
            avg_regime_latency = np.mean([r['regime_latency_days'] for r in stress_results])
            crisis_detection_rate = np.mean([1 if r.get('crisis_detected') else 0 for r in stress_results])
        
        print(f"Average Annual Return: {avg_return*100:.1f}%")
        print(f"Average Sharpe Ratio: {avg_sharpe:.2f}")
        print(f"Average IC (21d): {avg_ic:.3f} (std: {avg_ic_std:.3f})")
        print(f"Average IC t-stat: {avg_ic_tstat:.2f}")
        print(f"Average IC Stability: {avg_ic_stability:.3f}")
        print(f"Average Alpha: {avg_alpha*100:.1f}%" if avg_alpha else "Average Alpha: N/A")
        print(f"Average Return on Turnover: {avg_rot*100:.2f}%")
        print(f"\nRegime-Aware Cash-Out Benefits:")
        print(f"  Average Safety Alpha: {avg_safety_alpha*100:.1f}%")
        print(f"  Average DD Improvement: {avg_dd_improvement*100:.1f}%")
        print(f"  Average Sharpe Improvement: {avg_sharpe_improvement:.2f}")
        
        if stress_results:
            print(f"\nStress Test Results:")
            print(f"  Average Stress Max DD: {avg_stress_dd*100:.1f}%")
            print(f"  Average Recovery Ratio: {avg_recovery_ratio:.2f}x")
            print(f"  Average Regime Latency: {avg_regime_latency:.1f} days")
            print(f"  Crisis Detection Rate: {crisis_detection_rate*100:.1f}%")
        
        # Targets (2026 Best-in-Class Standards)
        print("\nTargets (Best-in-Class):")
        print(f"  Sharpe > 1.1: {'✅' if avg_sharpe > 1.1 else '❌'} ({avg_sharpe:.2f})")
        print(f"  IC > 0.10: {'✅' if avg_ic > 0.10 else '❌'} ({avg_ic:.3f})")
        print(f"  IC t-stat > 2.0: {'✅' if avg_ic_tstat > 2.0 else '❌'} ({avg_ic_tstat:.2f})")
        print(f"  IC Stability > 0.5: {'✅' if avg_ic_stability > 0.5 else '❌'} ({avg_ic_stability:.3f})")
        print(f"  Alpha > 5%: {'✅' if avg_alpha and avg_alpha > 0.05 else '❌'} ({avg_alpha*100:.1f}% if available)")
        print(f"  ROT > 5%: {'✅' if avg_rot > 0.05 else '❌'} ({avg_rot*100:.2f}%)")
        
        if stress_results:
            print(f"\nStress Test Targets:")
            print(f"  Recovery Ratio < 1.5x: {'✅' if avg_recovery_ratio < 1.5 else '❌'} ({avg_recovery_ratio:.2f}x)")
            print(f"  Regime Latency ≤ 2 days: {'✅' if avg_regime_latency <= 2 else '❌'} ({avg_regime_latency:.1f} days)")
            print(f"  Crisis Detection Rate > 80%: {'✅' if crisis_detection_rate > 0.80 else '❌'} ({crisis_detection_rate*100:.1f}%)")
    
    print("\n" + "="*80)
    print("✅ Comprehensive Backtest Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(comprehensive_backtest())

