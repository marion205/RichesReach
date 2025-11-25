#!/usr/bin/env python3
"""
Backtest Looser Mode - Simulate dropping volatility max to 15%
See drawdown vs. win rate tradeoff
"""
import requests
import json
from datetime import datetime, date
from typing import Dict, List, Optional

GRAPHQL_URL = "http://localhost:8000/graphql/"

# Simulated looser mode parameters
LOOSER_MODE_PARAMS = {
    "max_volatility": 0.15,  # 15% instead of 8%
    "max_change_pct": 0.40,  # 40% instead of 30%
    "min_market_cap": 500_000_000,  # $500M instead of $1B
    "min_volume": 500_000,  # 500K instead of 1M
}

def get_day_trading_picks(mode: str = "AGGRESSIVE") -> Optional[Dict]:
    """Get current picks for comparison"""
    query = """
    query GetDayTradingPicks($mode: String!) {
      dayTradingPicks(mode: $mode) {
        asOf
        mode
        picks {
          symbol
          side
          score
          features {
            momentum15m
            rvol10m
            vwapDist
            breakoutPct
            spreadBps
            catalystScore
          }
          risk {
            atr5m
            sizeShares
            stop
            targets
            timeStopMin
          }
          notes
        }
        universeSize
        qualityThreshold
      }
    }
    """
    
    payload = {
        "query": query,
        "variables": {"mode": mode}
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                return None
            return data.get("data", {}).get("dayTradingPicks")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def simulate_looser_mode(picks_data: Dict) -> Dict:
    """Simulate what picks would be included with looser filters"""
    picks = picks_data.get("picks", [])
    
    # For each pick, estimate if it would still pass with looser filters
    # In reality, you'd re-run the algorithm with new params
    # This is a simulation based on current picks
    
    print("\n" + "="*100)
    print("LOOSER MODE SIMULATION")
    print("="*100)
    print()
    print("📊 PARAMETER COMPARISON:")
    print(f"   Current AGGRESSIVE:")
    print(f"     • Max Volatility: 8%")
    print(f"     • Max Change %: 30%")
    print(f"     • Min Market Cap: $1B")
    print(f"     • Min Volume: 1M shares")
    print()
    print(f"   Looser Mode:")
    print(f"     • Max Volatility: {LOOSER_MODE_PARAMS['max_volatility']:.0%}")
    print(f"     • Max Change %: {LOOSER_MODE_PARAMS['max_change_pct']:.0%}")
    print(f"     • Min Market Cap: ${LOOSER_MODE_PARAMS['min_market_cap']:,}")
    print(f"     • Min Volume: {LOOSER_MODE_PARAMS['min_volume']:,} shares")
    print()
    
    # Estimate additional picks (this is theoretical)
    # In reality, you'd need to re-scan the universe with new filters
    current_count = len(picks)
    estimated_additional = int(current_count * 0.5)  # Rough estimate: 50% more picks
    
    print(f"📈 ESTIMATED IMPACT:")
    print(f"   • Current Picks: {current_count}")
    print(f"   • Estimated Additional: ~{estimated_additional}")
    print(f"   • Total Estimated: ~{current_count + estimated_additional}")
    print()
    
    print(f"⚠️  TRADEOFFS:")
    print(f"   ✅ PROS:")
    print(f"     • More opportunities (catch more moves)")
    print(f"     • Might catch some quality setups that were borderline")
    print(f"     • Higher potential returns (if you catch the right ones)")
    print()
    print(f"   ❌ CONS:")
    print(f"     • Higher drawdown risk (more volatile stocks)")
    print(f"     • Stop losses less reliable (wider stops needed)")
    print(f"     • More false signals (lower quality)")
    print(f"     • Slippage risk (lower volume stocks)")
    print()
    
    return {
        "current_picks": current_count,
        "estimated_additional": estimated_additional,
        "estimated_total": current_count + estimated_additional,
        "params": LOOSER_MODE_PARAMS
    }


def main():
    print("\n" + "="*100)
    print("BACKTEST LOOSER MODE")
    print("="*100)
    print(f"Date: {date.today().isoformat()}")
    print()
    
    picks_data = get_day_trading_picks("AGGRESSIVE")
    
    if not picks_data:
        print("❌ Could not fetch picks")
        return
    
    result = simulate_looser_mode(picks_data)
    
    print("="*100)
    print("RECOMMENDATION")
    print("="*100)
    print()
    print("💡 To properly backtest looser mode:")
    print("   1. Create a new mode: 'LOOSER' or 'VERY_AGGRESSIVE'")
    print("   2. Run it for 30 days alongside AGGRESSIVE")
    print("   3. Compare:")
    print("      • Win rate")
    print("      • Average return")
    print("      • Max drawdown")
    print("      • Sharpe ratio")
    print("      • Number of trades")
    print()
    print("   4. If looser mode shows better risk-adjusted returns, consider it")
    print("   5. If not, stick with current filters (they're protecting you)")
    print()
    print("🎯 Remember: More trades ≠ Better returns")
    print("   Quality > Quantity. Consistency > Home runs.")
    print()


if __name__ == "__main__":
    main()

