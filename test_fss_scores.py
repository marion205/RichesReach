#!/usr/bin/env python3
"""
Test FSS v3.0 Scores
Quick test script to calculate and display FSS scores for sample stocks.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_service import get_fss_service
from core.fss_engine import get_fss_engine
from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_fss_scores():
    """Test FSS v3.0 calculation for sample stocks"""
    
    # Test stocks
    test_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    
    print("\n" + "="*80)
    print("FSS v3.0 Score Test")
    print("="*80)
    print(f"Testing stocks: {', '.join(test_stocks)}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    fss_service = get_fss_service()
    
    # Get FSS scores
    print("📊 Fetching market data and calculating FSS scores...\n")
    
    results = await fss_service.get_stocks_fss(test_stocks, use_cache=False)
    
    # Display results
    print("\n" + "="*80)
    print("FSS v3.0 Results")
    print("="*80 + "\n")
    
    for symbol in test_stocks:
        result = results.get(symbol)
        
        if result is None:
            print(f"❌ {symbol}: Failed to calculate FSS score")
            continue
        
        fss = result.get('fss_score', 0)
        trend = result.get('trend_score', 0)
        fundamental = result.get('fundamental_score', 0)
        capital_flow = result.get('capital_flow_score', 0)
        risk = result.get('risk_score', 0)
        confidence = result.get('confidence', 'unknown')
        regime = result.get('regime', 'unknown')
        safety_passed = result.get('passed_safety_filters', False)
        
        # Color coding
        if fss >= 75:
            status = "🟢 HIGH CONVICTION"
        elif fss >= 60:
            status = "🟡 WATCHLIST"
        else:
            status = "🔴 AVOID"
        
        print(f"{symbol}: {fss:.1f}/100 {status}")
        print(f"  ├─ Trend:        {trend:.1f}/100")
        print(f"  ├─ Fundamentals: {fundamental:.1f}/100")
        print(f"  ├─ Capital Flow: {capital_flow:.1f}/100")
        print(f"  ├─ Risk:         {risk:.1f}/100")
        print(f"  ├─ Confidence:   {confidence.upper()}")
        print(f"  ├─ Regime:       {regime}")
        print(f"  └─ Safety:       {'✅ Passed' if safety_passed else '❌ Failed'}")
        print()
    
    # Summary
    print("="*80)
    print("Summary")
    print("="*80)
    
    valid_results = [r for r in results.values() if r is not None]
    if valid_results:
        avg_fss = sum(r.get('fss_score', 0) for r in valid_results) / len(valid_results)
        high_conviction = [s for s, r in results.items() if r and r.get('fss_score', 0) >= 75]
        watchlist = [s for s, r in results.items() if r and 60 <= r.get('fss_score', 0) < 75]
        
        print(f"Average FSS Score: {avg_fss:.1f}/100")
        print(f"High Conviction (≥75): {', '.join(high_conviction) if high_conviction else 'None'}")
        print(f"Watchlist (60-74): {', '.join(watchlist) if watchlist else 'None'}")
        print(f"Market Regime: {valid_results[0].get('regime', 'Unknown')}")
    
    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80 + "\n")


async def test_single_stock(symbol: str):
    """Test FSS for a single stock with detailed breakdown"""
    
    print(f"\n{'='*80}")
    print(f"Detailed FSS Analysis: {symbol}")
    print(f"{'='*80}\n")
    
    fss_service = get_fss_service()
    
    print("📊 Fetching data...")
    result = await fss_service.get_stock_fss(symbol, use_cache=False)
    
    if result is None:
        print(f"❌ Failed to calculate FSS for {symbol}")
        return
    
    print(f"\n{'='*80}")
    print(f"FSS v3.0 Breakdown: {symbol}")
    print(f"{'='*80}\n")
    
    print(f"Overall FSS Score: {result['fss_score']:.1f}/100")
    print(f"\nComponent Scores:")
    print(f"  Trend:        {result['trend_score']:.1f}/100 (Risk-adjusted momentum)")
    print(f"  Fundamentals: {result['fundamental_score']:.1f}/100 (EPS, Revenue, Margins)")
    print(f"  Capital Flow: {result['capital_flow_score']:.1f}/100 (VPT, Volume, Accumulation)")
    print(f"  Risk:         {result['risk_score']:.1f}/100 (Volatility, Balance Sheet, Drawdown)")
    
    print(f"\nAnalysis:")
    print(f"  Confidence:   {result['confidence'].upper()}")
    print(f"  Regime:       {result['regime']}")
    print(f"  Safety:       {'✅ Passed' if result['passed_safety_filters'] else '❌ Failed'}")
    if not result['passed_safety_filters']:
        print(f"  Safety Reason: {result.get('safety_reason', 'Unknown')}")
    
    # Recommendation
    fss = result['fss_score']
    if fss >= 75:
        rec = "🟢 HIGH CONVICTION BUY"
        reason = "Strong across all components with high confidence"
    elif fss >= 60:
        rec = "🟡 WATCHLIST"
        reason = "Decent score, monitor for entry opportunity"
    else:
        rec = "🔴 AVOID"
        reason = "Low score indicates poor risk/reward"
    
    print(f"\nRecommendation: {rec}")
    print(f"Reason: {reason}")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test single stock
        symbol = sys.argv[1].upper()
        asyncio.run(test_single_stock(symbol))
    else:
        # Test multiple stocks
        asyncio.run(test_fss_scores())

