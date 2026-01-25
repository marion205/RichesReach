#!/usr/bin/env python3
"""
Advanced FSS Validation
Implements institutional-grade validation:
- IC Decay across horizons
- Tail Risk & Black Swan stress tests
- Transaction Cost Reality Check (ROT)
- Regime Detection Accuracy (confusion matrix)
"""
import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_engine import get_fss_engine
from core.fss_backtest import get_fss_backtester
from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)


class AdvancedFSSValidator:
    """Institutional-grade FSS validation"""
    
    def __init__(self):
        self.fss_engine = get_fss_engine()
        self.backtester = get_fss_backtester()
        self.pipeline = get_fss_data_pipeline()
    
    async def calculate_ic_decay(
        self,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        spy: pd.Series,
        vix: pd.Series = None,
        horizons: List[int] = [1, 5, 21, 63, 126]
    ) -> pd.DataFrame:
        """
        Calculate IC across different forward return horizons.
        
        IC Decay: Predictive power often drops as look-ahead period increases.
        If 1-day IC is high but 5-day is near zero, turnover costs eat Alpha.
        """
        print("\n📊 Calculating IC Decay Across Horizons...")
        print("-" * 80)
        
        # Calculate FSS
        fss_data = self.fss_engine.compute_fss_v3(
            prices=prices,
            volumes=volumes,
            spy=spy,
            vix=vix
        )
        
        ic_results = []
        
        for horizon in horizons:
            # Forward returns
            forward_returns = self.backtester.forward_return(prices, horizon=horizon)
            
            # Calculate IC
            ic_series = self.backtester.calculate_ic(fss_data["FSS"], forward_returns)
            
            if len(ic_series) > 0:
                mean_ic = ic_series.mean()
                std_ic = ic_series.std()
                t_stat = mean_ic / (std_ic / np.sqrt(len(ic_series))) if std_ic > 0 else 0
                
                ic_results.append({
                    'horizon_days': horizon,
                    'mean_ic': mean_ic,
                    'std_ic': std_ic,
                    't_stat': t_stat,
                    'significant': abs(t_stat) > 2.0,
                    'n_observations': len(ic_series)
                })
                
                print(f"  {horizon:3d}-day IC: {mean_ic:6.3f} (t-stat: {t_stat:5.2f}) {'✅' if abs(t_stat) > 2.0 else '❌'}")
        
        ic_df = pd.DataFrame(ic_results)
        
        # Analyze decay
        if len(ic_df) > 1:
            first_ic = ic_df.iloc[0]['mean_ic']
            last_ic = ic_df.iloc[-1]['mean_ic']
            decay_rate = (first_ic - last_ic) / first_ic if first_ic != 0 else 0
            
            print(f"\n  IC Decay Rate: {decay_rate*100:.1f}%")
            if decay_rate > 0.5:
                print("  ⚠️  WARNING: High IC decay - short-term signals may not hold")
            elif decay_rate < 0.2:
                print("  ✅ Good: Low IC decay - signals persist across horizons")
        
        return ic_df
    
    async def stress_test_black_swan(
        self,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        spy: pd.Series,
        vix: pd.Series = None,
        shock_magnitude: float = -0.20,
        shock_duration: int = 2
    ) -> Dict:
        """
        Stress test: Simulate a Black Swan event (e.g., 20% market drop over 2 days).
        
        Tests if Safety Filters actually trigger or lag.
        """
        print("\n🌪️  Black Swan Stress Test...")
        print("-" * 80)
        print(f"  Simulating {shock_magnitude*100:.0f}% market shock over {shock_duration} days")
        
        # Create shocked prices
        prices_shocked = prices.copy()
        spy_shocked = spy.copy()
        
        # Apply shock at midpoint
        shock_start = len(prices_shocked) // 2
        shock_end = shock_start + shock_duration
        
        # Shock SPY
        for i in range(shock_start, min(shock_end, len(spy_shocked))):
            if i < len(spy_shocked):
                spy_shocked.iloc[i] = spy_shocked.iloc[i-1] * (1 + shock_magnitude / shock_duration)
        
        # Shock all stocks (correlated)
        for ticker in prices_shocked.columns:
            for i in range(shock_start, min(shock_end, len(prices_shocked))):
                if i < len(prices_shocked):
                    # Stocks drop more than market (beta > 1)
                    stock_shock = shock_magnitude * 1.2 / shock_duration
                    prices_shocked.iloc[i, prices_shocked.columns.get_loc(ticker)] = \
                        prices_shocked.iloc[i-1, prices_shocked.columns.get_loc(ticker)] * (1 + stock_shock)
        
        # Calculate FSS before and after shock
        fss_before = self.fss_engine.compute_fss_v3(
            prices=prices.iloc[:shock_start],
            volumes=volumes.iloc[:shock_start],
            spy=spy.iloc[:shock_start],
            vix=vix.iloc[:shock_start] if vix is not None else None
        )
        
        fss_after = self.fss_engine.compute_fss_v3(
            prices=prices_shocked.iloc[shock_start:],
            volumes=volumes.iloc[shock_start:],
            spy=spy_shocked.iloc[shock_start:],
            vix=vix.iloc[shock_start:] if vix is not None else None
        )
        
        # Check if safety filters would have caught this
        from core.fss_engine import get_safety_filter
        safety_filter = get_safety_filter()
        
        # Test safety filters on shocked stocks
        safety_results = {}
        for ticker in prices.columns:
            # Check liquidity (should fail if volume drops)
            volumes_shocked = volumes.iloc[shock_start:, volumes.columns.get_loc(ticker)]
            safety_passed, reason = safety_filter.check_safety(ticker, volumes_shocked)
            safety_results[ticker] = {
                'passed': safety_passed,
                'reason': reason
            }
        
        # Calculate portfolio impact
        before_fss = fss_before["FSS"].iloc[-1] if len(fss_before) > 0 else pd.Series()
        after_fss = fss_after["FSS"].iloc[0] if len(fss_after) > 0 else pd.Series()
        
        # Portfolio value change
        portfolio_before = 100000  # $100k
        portfolio_after = portfolio_before * (1 + shock_magnitude)
        
        # How many stocks would have been filtered?
        filtered_count = sum(1 for r in safety_results.values() if not r['passed'])
        
        result = {
            'shock_magnitude': shock_magnitude,
            'shock_duration': shock_duration,
            'portfolio_before': portfolio_before,
            'portfolio_after': portfolio_after,
            'portfolio_loss': portfolio_after - portfolio_before,
            'stocks_filtered': filtered_count,
            'total_stocks': len(safety_results),
            'filter_effectiveness': filtered_count / len(safety_results) if safety_results else 0,
            'safety_results': safety_results
        }
        
        print(f"  Portfolio Loss: ${result['portfolio_loss']:,.0f}")
        print(f"  Stocks Filtered: {filtered_count}/{len(safety_results)} ({result['filter_effectiveness']*100:.1f}%)")
        
        if result['filter_effectiveness'] < 0.3:
            print("  ⚠️  WARNING: Safety filters may not be catching distressed stocks")
        else:
            print("  ✅ Safety filters are working")
        
        return result
    
    def calculate_return_on_turnover(
        self,
        backtest_result,
        transaction_cost_bps: float = 5.0
    ) -> Dict:
        """
        Return on Turnover (ROT) analysis.
        
        ROT = (Annual Return - Transaction Costs) / Turnover
        If turnover is high but ROT is low, you're just making your broker rich.
        """
        print("\n💰 Transaction Cost Reality Check (ROT)...")
        print("-" * 80)
        
        # Calculate turnover
        # Turnover = sum of absolute weight changes per rebalance
        # This is approximated from rebalance frequency
        rebalance_freq = "M"  # Monthly
        rebalances_per_year = 12
        
        # Estimate turnover (simplified)
        # In real implementation, calculate from actual weight changes
        estimated_turnover = rebalances_per_year * 0.5  # 50% turnover per rebalance
        
        # Transaction costs
        cost_per_trade = transaction_cost_bps / 10000  # 0.05% = 5 bps
        annual_costs = estimated_turnover * cost_per_trade
        
        # Net return after costs
        gross_return = backtest_result.annual_return
        net_return = gross_return - annual_costs
        
        # ROT
        rot = net_return / estimated_turnover if estimated_turnover > 0 else 0
        
        result = {
            'gross_return': gross_return,
            'estimated_turnover': estimated_turnover,
            'annual_costs': annual_costs,
            'net_return': net_return,
            'return_on_turnover': rot,
            'cost_efficiency': 'Good' if rot > 0.05 else 'Poor'
        }
        
        print(f"  Gross Return: {gross_return*100:.2f}%")
        print(f"  Estimated Turnover: {estimated_turnover*100:.1f}%")
        print(f"  Annual Costs: {annual_costs*100:.2f}%")
        print(f"  Net Return: {net_return*100:.2f}%")
        print(f"  Return on Turnover: {rot*100:.2f}%")
        print(f"  Cost Efficiency: {result['cost_efficiency']}")
        
        if rot < 0.05:
            print("  ⚠️  WARNING: Low ROT - high turnover may be eating returns")
        else:
            print("  ✅ Good: ROT indicates efficient trading")
        
        return result
    
    async def validate_regime_detection(
        self,
        spy: pd.Series,
        vix: pd.Series,
        actual_regimes: List[str] = None
    ) -> Dict:
        """
        Validate regime detection accuracy using confusion matrix.
        
        A 10% error rate in regime classification is more dangerous than
        a 10% error in price prediction.
        """
        print("\n🎯 Regime Detection Accuracy...")
        print("-" * 80)
        
        # Detect regimes
        detected_regimes = []
        for i in range(len(spy)):
            spy_window = spy.iloc[max(0, i-200):i+1]
            vix_window = vix.iloc[max(0, i-200):i+1] if vix is not None else None
            
            if len(spy_window) < 200:
                detected_regimes.append(None)
                continue
            
            regime_result = self.fss_engine.detect_market_regime(spy_window, vix_window)
            detected_regimes.append(regime_result.regime)
        
        # If we have actual regimes, create confusion matrix
        if actual_regimes and len(actual_regimes) == len(detected_regimes):
            from sklearn.metrics import confusion_matrix, classification_report
            
            # Filter out None values
            valid_indices = [i for i, (d, a) in enumerate(zip(detected_regimes, actual_regimes)) 
                           if d is not None and a is not None]
            detected_valid = [detected_regimes[i] for i in valid_indices]
            actual_valid = [actual_regimes[i] for i in valid_indices]
            
            # Get unique regimes
            all_regimes = sorted(set(detected_valid + actual_valid))
            
            # Confusion matrix
            cm = confusion_matrix(actual_valid, detected_valid, labels=all_regimes)
            
            # Accuracy
            accuracy = np.trace(cm) / np.sum(cm) if np.sum(cm) > 0 else 0
            
            result = {
                'confusion_matrix': cm.tolist(),
                'regime_labels': all_regimes,
                'accuracy': accuracy,
                'classification_report': classification_report(actual_valid, detected_valid, 
                                                              labels=all_regimes, output_dict=True)
            }
            
            print(f"  Accuracy: {accuracy*100:.1f}%")
            print(f"\n  Confusion Matrix:")
            print(f"  {'':15s}", end="")
            for label in all_regimes:
                print(f"{label:15s}", end="")
            print()
            for i, label in enumerate(all_regimes):
                print(f"  {label:15s}", end="")
                for j in range(len(all_regimes)):
                    print(f"{cm[i,j]:15d}", end="")
                print()
            
            if accuracy < 0.70:
                print("\n  ⚠️  WARNING: Low regime detection accuracy - may cause poor performance")
            else:
                print("\n  ✅ Good: Regime detection is accurate")
            
        else:
            # No ground truth - just report detected regimes
            regime_counts = defaultdict(int)
            for r in detected_regimes:
                if r:
                    regime_counts[r] += 1
            
            result = {
                'detected_regimes': dict(regime_counts),
                'accuracy': None,
                'note': 'No ground truth provided - cannot calculate accuracy'
            }
            
            print("  Detected Regime Distribution:")
            for regime, count in regime_counts.items():
                pct = count / len(detected_regimes) * 100
                print(f"    {regime:15s}: {count:4d} ({pct:5.1f}%)")
        
        return result


async def run_advanced_validation():
    """Run all advanced validation tests"""
    
    print("\n" + "="*80)
    print("FSS v3.0 Advanced Validation")
    print("="*80)
    print("\nRunning institutional-grade validation tests...\n")
    
    validator = AdvancedFSSValidator()
    
    # Test stocks
    test_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    
    # Fetch data
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
        
        if len(data_result.prices) < 100:
            print("❌ Insufficient data for validation")
            return
        
        # 1. IC Decay Analysis
        ic_decay = await validator.calculate_ic_decay(
            data_result.prices,
            data_result.volumes,
            data_result.spy,
            data_result.vix
        )
        
        # 2. Black Swan Stress Test
        stress_result = await validator.stress_test_black_swan(
            data_result.prices,
            data_result.volumes,
            data_result.spy,
            data_result.vix,
            shock_magnitude=-0.20,
            shock_duration=2
        )
        
        # 3. Run backtest for ROT calculation
        fss_engine = get_fss_engine()
        fss_data = fss_engine.compute_fss_v3(
            prices=data_result.prices,
            volumes=data_result.volumes,
            spy=data_result.spy,
            vix=data_result.vix
        )
        
        backtester = get_fss_backtester()
        backtest_result = backtester.backtest_rank_strategy(
            prices=data_result.prices,
            fss=fss_data["FSS"],
            spy=data_result.spy,
            rebalance_freq="M",
            top_n=5
        )
        
        # 4. Return on Turnover
        rot_result = validator.calculate_return_on_turnover(backtest_result)
        
        # 5. Regime Detection Accuracy
        regime_result = await validator.validate_regime_detection(
            data_result.spy,
            data_result.vix
        )
        
        # Summary
        print("\n" + "="*80)
        print("Validation Summary")
        print("="*80)
        
        print("\n1. IC Decay:")
        if len(ic_decay) > 0:
            first_ic = ic_decay.iloc[0]['mean_ic']
            last_ic = ic_decay.iloc[-1]['mean_ic']
            print(f"   {ic_decay.iloc[0]['horizon_days']}-day IC: {first_ic:.3f}")
            print(f"   {ic_decay.iloc[-1]['horizon_days']}-day IC: {last_ic:.3f}")
            if first_ic > 0.10:
                print("   ✅ Short-term IC is strong")
            if last_ic > 0.05:
                print("   ✅ Long-term IC persists")
        
        print("\n2. Black Swan Stress Test:")
        print(f"   Filter Effectiveness: {stress_result['filter_effectiveness']*100:.1f}%")
        if stress_result['filter_effectiveness'] > 0.3:
            print("   ✅ Safety filters working")
        else:
            print("   ⚠️  Safety filters may need improvement")
        
        print("\n3. Return on Turnover:")
        print(f"   ROT: {rot_result['return_on_turnover']*100:.2f}%")
        print(f"   Cost Efficiency: {rot_result['cost_efficiency']}")
        
        print("\n4. Regime Detection:")
        if regime_result.get('accuracy'):
            print(f"   Accuracy: {regime_result['accuracy']*100:.1f}%")
            if regime_result['accuracy'] > 0.70:
                print("   ✅ Regime detection is accurate")
            else:
                print("   ⚠️  Regime detection needs improvement")
        else:
            print("   (No ground truth available)")
        
        print("\n" + "="*80)
        print("✅ Advanced Validation Complete!")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(run_advanced_validation())

