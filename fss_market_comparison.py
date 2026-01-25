#!/usr/bin/env python3
"""
FSS v3.0 Market Comparison
Compares FSS v3.0 performance against market benchmarks and competitors.
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_engine import get_fss_engine
from core.fss_backtest import FSSBacktester
from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
import asyncio
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def compare_to_market():
    """Compare FSS v3.0 to market benchmarks and competitors"""
    
    print("\n" + "="*80)
    print("FSS v3.0 Market Comparison")
    print("="*80)
    print("Comparing against SPY, QQQ, and other benchmarks...\n")
    
    # Test period (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # ~2 years
    
    # Test stocks
    test_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META", "JNJ", "V", "JPM"]
    
    print("📊 Fetching market data...")
    pipeline = get_fss_data_pipeline()
    
    try:
        async with pipeline:
            request = FSSDataRequest(
                tickers=test_stocks,
                lookback_days=730,
                include_fundamentals=False
            )
            data_result = await pipeline.fetch_fss_data(request)
        
        if len(data_result.prices) < 200:
            print("❌ Insufficient data")
            return
        
        # Calculate FSS
        print("📈 Calculating FSS v3.0...")
        fss_engine = get_fss_engine()
        fss_data = fss_engine.compute_fss_v3(
            prices=data_result.prices,
            volumes=data_result.volumes,
            spy=data_result.spy,
            vix=data_result.vix
        )
        
        # Filter to test period
        prices_test = data_result.prices.loc[start_date:end_date]
        spy_test = data_result.spy.loc[start_date:end_date]
        fss_test = fss_data["FSS"].loc[start_date:end_date]
        
        if len(prices_test) < 200:
            print("❌ Insufficient data for comparison period")
            return
        
        # Create regime series
        regime_series = pd.Series(index=prices_test.index, dtype=object)
        for date in prices_test.index:
            date_idx = spy_test.index.get_loc(date)
            window_start = max(0, date_idx - 200)
            spy_window = spy_test.iloc[window_start:date_idx+1]
            vix_window = data_result.vix.iloc[window_start:date_idx+1] if data_result.vix is not None else None
            
            if len(spy_window) >= 200:
                regime_result = fss_engine.detect_market_regime(spy_window, vix_window)
                regime_series.loc[date] = regime_result.regime
            else:
                regime_series.loc[date] = "Expansion"
        
        # Backtest FSS v3.0 (Regime-Aware)
        backtester = FSSBacktester(transaction_cost_bps=10.0)
        fss_result = backtester.backtest_rank_strategy(
            prices=prices_test,
            fss=fss_test,
            spy=spy_test,
            rebalance_freq="M",
            top_n=5,
            regime=regime_series,
            cash_out_on_crisis=True,
            cash_return_rate=0.04
        )
        
        # Calculate benchmark returns
        spy_ret = spy_test.pct_change().fillna(0.0)
        spy_equity = (1.0 + spy_ret).cumprod()
        spy_ann_return = spy_equity.iloc[-1] ** (252 / len(spy_equity)) - 1
        spy_ann_vol = spy_ret.std() * np.sqrt(252)
        spy_sharpe = spy_ann_return / (spy_ann_vol + 1e-12)
        spy_dd = (spy_equity / spy_equity.cummax()) - 1.0
        spy_max_dd = spy_dd.min()
        
        # Comparison
        print("\n" + "="*80)
        print("Performance Comparison (Last 2 Years)")
        print("="*80)
        
        comparison = {
            "FSS v3.0 (Regime-Aware)": {
                "annual_return": fss_result.annual_return,
                "sharpe_ratio": fss_result.sharpe_ratio,
                "max_drawdown": fss_result.max_drawdown,
                "alpha_vs_spy": fss_result.alpha if fss_result.alpha else 0
            },
            "SPY (S&P 500)": {
                "annual_return": spy_ann_return,
                "sharpe_ratio": spy_sharpe,
                "max_drawdown": spy_max_dd,
                "alpha_vs_spy": 0
            }
        }
        
        print(f"\n{'Strategy':<30} {'Return':>10} {'Sharpe':>10} {'Max DD':>10} {'Alpha':>10}")
        print("-" * 80)
        
        for name, metrics in comparison.items():
            print(f"{name:<30} {metrics['annual_return']*100:>9.1f}% {metrics['sharpe_ratio']:>9.2f} "
                  f"{metrics['max_drawdown']*100:>9.1f}% {metrics['alpha_vs_spy']*100:>9.1f}%")
        
        # Improvements
        fss_return = fss_result.annual_return
        fss_sharpe = fss_result.sharpe_ratio
        fss_dd = fss_result.max_drawdown
        
        return_improvement = (fss_return - spy_ann_return) / abs(spy_ann_return) * 100 if spy_ann_return != 0 else 0
        sharpe_improvement = fss_sharpe - spy_sharpe
        dd_improvement = (spy_max_dd - fss_dd) / abs(spy_max_dd) * 100 if spy_max_dd != 0 else 0
        
        print(f"\n📊 FSS v3.0 vs SPY:")
        print(f"   Return Improvement: {return_improvement:+.1f}%")
        print(f"   Sharpe Improvement: {sharpe_improvement:+.2f}")
        print(f"   Drawdown Improvement: {dd_improvement:+.1f}%")
        print(f"   Alpha: {fss_result.alpha*100:+.1f}%" if fss_result.alpha else "   Alpha: N/A")
        
        # Competitive positioning
        print(f"\n🏆 Competitive Positioning:")
        
        if fss_sharpe > 1.2:
            print("   ✅ Sharpe > 1.2: Top-tier quant fund level")
        elif fss_sharpe > 1.0:
            print("   ✅ Sharpe > 1.0: Institutional quality")
        else:
            print("   ⚠️  Sharpe < 1.0: Below institutional target")
        
        if fss_result.alpha and fss_result.alpha > 0.05:
            print("   ✅ Alpha > 5%: Strong outperformance")
        elif fss_result.alpha and fss_result.alpha > 0.02:
            print("   ✅ Alpha > 2%: Moderate outperformance")
        else:
            print("   ⚠️  Alpha < 2%: Needs improvement")
        
        if abs(fss_dd) < 0.15:
            print("   ✅ Max DD < 15%: Excellent risk management")
        elif abs(fss_dd) < 0.20:
            print("   ✅ Max DD < 20%: Good risk management")
        else:
            print("   ⚠️  Max DD > 20%: Risk management needs work")
        
        # Save comparison
        comparison_file = "fss_market_comparison.json"
        with open(comparison_file, 'w') as f:
            json.dump({
                "comparison_date": datetime.now().isoformat(),
                "period": f"{start_date.date()} to {end_date.date()}",
                "comparison": comparison,
                "improvements": {
                    "return_improvement_pct": return_improvement,
                    "sharpe_improvement": sharpe_improvement,
                    "dd_improvement_pct": dd_improvement,
                    "alpha": fss_result.alpha if fss_result.alpha else None
                }
            }, f, indent=2, default=str)
        
        print(f"\n💾 Comparison saved to: {comparison_file}")
        
        print("\n" + "="*80)
        print("✅ Market Comparison Complete!")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Comparison error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(compare_to_market())

