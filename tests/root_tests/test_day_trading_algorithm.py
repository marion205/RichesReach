#!/usr/bin/env python3
"""
Test Day Trading Algorithm - Get Today's Picks
Run this to see what stocks your algorithm would pick today
"""
import requests
import json
from datetime import datetime
from typing import Dict, Optional

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql/"

def get_day_trading_picks(mode: str = "SAFE") -> Optional[Dict]:
    """Get day trading picks from GraphQL API"""
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
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🔍 Fetching {mode} mode day trading picks...")
        response = requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
                return None
            return data.get("data", {}).get("dayTradingPicks")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error fetching picks: {e}")
        return None


def format_pick(pick: Dict, index: int) -> str:
    """Format a single pick for display"""
    symbol = pick.get('symbol', 'N/A')
    side = pick.get('side', 'N/A')
    score = pick.get('score', 0)
    
    features = pick.get('features', {})
    momentum = features.get('momentum15m', 0)
    rvol = features.get('rvol10m', 0)
    vwap_dist = features.get('vwapDist', 0)
    breakout = features.get('breakoutPct', 0)
    spread = features.get('spreadBps', 0)
    catalyst = features.get('catalystScore', 0)
    
    risk = pick.get('risk', {})
    atr = risk.get('atr5m', 0)
    size = risk.get('sizeShares', 0)
    stop = risk.get('stop', 0)
    targets = risk.get('targets', [])
    time_stop = risk.get('timeStopMin', 0)
    
    notes = pick.get('notes', '')
    
    output = f"""
{'='*80}
[{index}] {symbol} - {side}
{'='*80}
Score: {score:.2f}

Features:
  • Momentum (15m): {momentum:.4f}
  • Realized Vol (10m): {rvol:.4f}
  • VWAP Distance: {vwap_dist:.4f}
  • Breakout %: {breakout:.2%}
  • Spread (bps): {spread:.2f}
  • Catalyst Score: {catalyst:.2f}

Risk Management:
  • ATR (5m): ${atr:.2f}
  • Position Size: {size:,} shares
  • Stop Loss: ${stop:.2f}
  • Targets: {', '.join([f'${t:.2f}' for t in targets]) if targets else 'N/A'}
  • Time Stop: {time_stop} minutes

Notes: {notes}
"""
    return output


def main():
    """Main function to test day trading algorithm"""
    print("\n" + "="*80)
    print("DAY TRADING ALGORITHM TEST")
    print("="*80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test both modes
    for mode in ["SAFE", "AGGRESSIVE"]:
        print(f"\n{'#'*80}")
        print(f"# {mode} MODE PICKS")
        print(f"{'#'*80}\n")
        
        picks_data = get_day_trading_picks(mode)
        
        if not picks_data:
            print(f"❌ No data returned for {mode} mode")
            continue
        
        as_of = picks_data.get('asOf', 'N/A')
        mode_name = picks_data.get('mode', mode)
        picks = picks_data.get('picks', [])
        universe_size = picks_data.get('universeSize', 0)
        quality_threshold = picks_data.get('qualityThreshold', 0)
        
        print(f"Generated: {as_of}")
        print(f"Mode: {mode_name}")
        print(f"Universe Size: {universe_size:,} symbols")
        print(f"Quality Threshold: {quality_threshold:.2f}")
        print(f"Picks Generated: {len(picks)}")
        print()
        
        if not picks:
            print("⚠️  No qualifying picks found for this mode.")
            print("   This could mean:")
            print("   • Market conditions don't meet criteria")
            print("   • Quality threshold is too high")
            print("   • No liquid stocks available")
            continue
        
        # Display all picks
        for i, pick in enumerate(picks, 1):
            print(format_pick(pick, i))
        
        # Summary table
        print(f"\n{'='*80}")
        print("SUMMARY TABLE")
        print(f"{'='*80}")
        print(f"{'#':<4} {'Symbol':<8} {'Side':<6} {'Score':<8} {'Momentum':<12} {'Stop':<10} {'Targets':<20}")
        print("-" * 80)
        
        for i, pick in enumerate(picks, 1):
            symbol = pick.get('symbol', 'N/A')
            side = pick.get('side', 'N/A')
            score = pick.get('score', 0)
            momentum = pick.get('features', {}).get('momentum15m', 0)
            stop = pick.get('risk', {}).get('stop', 0)
            targets = pick.get('risk', {}).get('targets', [])
            targets_str = f"${targets[0]:.2f}" if targets else "N/A"
            
            print(f"{i:<4} {symbol:<8} {side:<6} {score:<8.2f} {momentum:<12.4f} ${stop:<9.2f} {targets_str:<20}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\n💡 To compare with actual results:")
    print("   1. Note the entry prices (current market price)")
    print("   2. Check these stocks' performance at end of day")
    print("   3. Compare actual returns vs. predicted targets")
    print("   4. Track win rate and average return")
    print()


if __name__ == "__main__":
    main()

