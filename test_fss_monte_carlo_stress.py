#!/usr/bin/env python3
"""
Monte Carlo Stress Test for FSS v3.0
Simulates flash crash scenarios (2020-style) during different market regimes.
"""
import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_engine import get_fss_engine
from core.fss_backtest import get_fss_backtester
from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def monte_carlo_stress_test():
    """Run Monte Carlo stress test simulating flash crashes"""
    
    print("\n" + "="*80)
    print("FSS v3.0 Monte Carlo Stress Test")
    print("="*80)
    print("Simulating 2020-style flash crashes during different regimes...\n")
    
    # Test stocks
    test_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    
    # Fetch base data
    print("📊 Fetching market data...")
    pipeline = get_fss_data_pipeline()
    
    try:
        async with pipeline:
            request = FSSDataRequest(
                tickers=test_stocks,
                lookback_days=252,
                include_fundamentals=False
            )
            data_result = await pipeline.fetch_fss_data(request)
        
        if len(data_result.prices) < 200:
            print("❌ Insufficient data for stress test")
            return
        
        fss_engine = get_fss_engine()
        backtester = get_fss_backtester(transaction_cost_bps=10.0)
        
        # Compute FSS on full dataset
        fss_full = fss_engine.compute_fss_v3(
            prices=data_result.prices,
            volumes=data_result.volumes,
            spy=data_result.spy,
            vix=data_result.vix
        )
        
        # Stress test scenarios
        scenarios = [
            {
                "name": "Flash Crash (2020-style)",
                "shock_magnitude": -0.15,  # -15% over 2 days
                "shock_duration": 2,
                "recovery_days": 10
            },
            {
                "name": "Gradual Decline",
                "shock_magnitude": -0.20,  # -20% over 10 days
                "shock_duration": 10,
                "recovery_days": 20
            },
            {
                "name": "Volatility Spike",
                "shock_magnitude": -0.10,  # -10% with high vol
                "shock_duration": 5,
                "recovery_days": 15
            }
        ]
        
        results = []
        
        for scenario in scenarios:
            print(f"\n🌪️  Scenario: {scenario['name']}")
            print("-" * 80)
            
            # Create shocked data
            prices_shocked = data_result.prices.copy()
            spy_shocked = data_result.spy.copy()
            vix_shocked = data_result.vix.copy() if data_result.vix is not None else None
            
            # Apply shock at midpoint
            shock_start = len(prices_shocked) // 2
            shock_end = shock_start + scenario['shock_duration']
            recovery_end = shock_end + scenario['recovery_days']
            
            # Shock SPY
            for i in range(shock_start, min(shock_end, len(spy_shocked))):
                if i < len(spy_shocked):
                    daily_shock = scenario['shock_magnitude'] / scenario['shock_duration']
                    spy_shocked.iloc[i] = spy_shocked.iloc[i-1] * (1 + daily_shock)
            
            # Shock all stocks (with beta > 1)
            for ticker in prices_shocked.columns:
                for i in range(shock_start, min(shock_end, len(prices_shocked))):
                    if i < len(prices_shocked):
                        # Stocks drop more than market (beta ~1.2)
                        stock_shock = scenario['shock_magnitude'] * 1.2 / scenario['shock_duration']
                        prices_shocked.iloc[i, prices_shocked.columns.get_loc(ticker)] = \
                            prices_shocked.iloc[i-1, prices_shocked.columns.get_loc(ticker)] * (1 + stock_shock)
            
            # Spike VIX during shock
            if vix_shocked is not None:
                for i in range(shock_start, min(shock_end, len(vix_shocked))):
                    if i < len(vix_shocked):
                        vix_shocked.iloc[i] = min(80, vix_shocked.iloc[i-1] * 1.5)  # Cap at 80
            
            # Recovery phase (gradual)
            recovery_rate = abs(scenario['shock_magnitude']) / scenario['recovery_days']
            for i in range(shock_end, min(recovery_end, len(spy_shocked))):
                if i < len(spy_shocked):
                    spy_shocked.iloc[i] = spy_shocked.iloc[i-1] * (1 + recovery_rate * 0.5)
            
            # Recalculate FSS on shocked data
            fss_shocked = fss_engine.compute_fss_v3(
                prices=prices_shocked,
                volumes=data_result.volumes,
                spy=spy_shocked,
                vix=vix_shocked
            )
            
            # Backtest on shocked data
            backtest_shocked = backtester.backtest_rank_strategy(
                prices=prices_shocked,
                fss=fss_shocked["FSS"],
                spy=spy_shocked,
                rebalance_freq="M",
                top_n=5
            )
            
            # Compare to baseline (no shock)
            backtest_baseline = backtester.backtest_rank_strategy(
                prices=data_result.prices,
                fss=fss_full["FSS"],
                spy=data_result.spy,
                rebalance_freq="M",
                top_n=5
            )
            
            # Calculate impact
            portfolio_loss = backtest_shocked.max_drawdown - backtest_baseline.max_drawdown
            return_impact = backtest_shocked.annual_return - backtest_baseline.annual_return
            
            # Check if safety filters triggered
            from core.fss_engine import get_safety_filter
            safety_filter = get_safety_filter()
            
            safety_triggered = 0
            for ticker in test_stocks:
                volumes_shocked = data_result.volumes.iloc[shock_start:shock_end, 
                                                          data_result.volumes.columns.get_loc(ticker)]
                safety_passed, reason = safety_filter.check_safety(ticker, volumes_shocked)
                if not safety_passed:
                    safety_triggered += 1
            
            result = {
                "scenario": scenario['name'],
                "baseline_return": backtest_baseline.annual_return,
                "shocked_return": backtest_shocked.annual_return,
                "return_impact": return_impact,
                "baseline_dd": backtest_baseline.max_drawdown,
                "shocked_dd": backtest_shocked.max_drawdown,
                "dd_impact": portfolio_loss,
                "safety_filters_triggered": safety_triggered,
                "total_stocks": len(test_stocks)
            }
            results.append(result)
            
            # Display
            print(f"  Baseline Return: {backtest_baseline.annual_return*100:.1f}%")
            print(f"  Shocked Return: {backtest_shocked.annual_return*100:.1f}%")
            print(f"  Return Impact: {return_impact*100:.1f}%")
            print(f"  Baseline Max DD: {backtest_baseline.max_drawdown*100:.1f}%")
            print(f"  Shocked Max DD: {backtest_shocked.max_drawdown*100:.1f}%")
            print(f"  DD Impact: {portfolio_loss*100:.1f}%")
            print(f"  Safety Filters Triggered: {safety_triggered}/{len(test_stocks)}")
            
            if abs(portfolio_loss) > 0.05:  # > 5% additional drawdown
                print("  ⚠️  WARNING: Significant drawdown increase")
            else:
                print("  ✅ Drawdown impact is manageable")
        
        # Summary
        print("\n" + "="*80)
        print("Stress Test Summary")
        print("="*80)
        
        avg_dd_impact = np.mean([abs(r['dd_impact']) for r in results])
        avg_return_impact = np.mean([abs(r['return_impact']) for r in results])
        avg_safety_triggered = np.mean([r['safety_filters_triggered'] for r in results])
        
        print(f"Average Drawdown Impact: {avg_dd_impact*100:.1f}%")
        print(f"Average Return Impact: {avg_return_impact*100:.1f}%")
        print(f"Average Safety Filters Triggered: {avg_safety_triggered:.1f}/{len(test_stocks)}")
        
        if avg_dd_impact < 0.05:
            print("\n✅ FSS v3.0 shows resilience to flash crashes")
        else:
            print("\n⚠️  FSS v3.0 may need additional tail risk protection")
        
        print("\n" + "="*80)
        print("✅ Monte Carlo Stress Test Complete!")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Stress test error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(monte_carlo_stress_test())

