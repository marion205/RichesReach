#!/usr/bin/env python3
"""
Test Pre-Market Scanner
Run this to see pre-market quality setups
"""
import requests
import json
from datetime import datetime
from typing import Dict, Optional

GRAPHQL_URL = "http://localhost:8000/graphql/"

def get_pre_market_picks(mode: str = "AGGRESSIVE", limit: int = 20) -> Optional[Dict]:
    """Get pre-market picks from GraphQL API"""
    query = """
    query GetPreMarketPicks($mode: String!, $limit: Int!) {
      preMarketPicks(mode: $mode, limit: $limit) {
        asOf
        mode
        picks {
          symbol
          side
          score
          preMarketPrice
          preMarketChangePct
          volume
          marketCap
          prevClose
          notes
          scannedAt
        }
        totalScanned
        minutesUntilOpen
      }
    }
    """
    
    payload = {
        "query": query,
        "variables": {"mode": mode, "limit": limit}
    }
    
    try:
        print(f"🔍 Fetching pre-market picks (mode: {mode})...")
        response = requests.post(GRAPHQL_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
                return None
            return data.get("data", {}).get("preMarketPicks")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Main function"""
    print("\n" + "="*100)
    print("PRE-MARKET SCANNER TEST")
    print("="*100)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for mode in ["SAFE", "AGGRESSIVE"]:
        print(f"\n{'#'*100}")
        print(f"# {mode} MODE PRE-MARKET SCAN")
        print(f"{'#'*100}\n")
        
        picks_data = get_pre_market_picks(mode, limit=20)
        
        if not picks_data:
            print(f"❌ No data returned for {mode} mode")
            continue
        
        as_of = picks_data.get('asOf', 'N/A')
        mode_name = picks_data.get('mode', mode)
        picks = picks_data.get('picks', [])
        total_scanned = picks_data.get('totalScanned', 0)
        minutes_until_open = picks_data.get('minutesUntilOpen', 0)
        
        print(f"Scanned: {as_of}")
        print(f"Mode: {mode_name}")
        print(f"Total Scanned: {total_scanned:,} symbols")
        print(f"Minutes Until Open: {minutes_until_open}")
        print(f"Quality Setups Found: {len(picks)}")
        print()
        
        if not picks:
            print("⚠️  No quality pre-market setups found")
            print("   This could mean:")
            print("   • Not in pre-market hours (4AM-9:30AM ET)")
            print("   • No movers meeting quality criteria")
            print("   • Market conditions don't favor pre-market setups")
            continue
        
        # Display picks
        print(f"{'='*100}")
        print(f"PRE-MARKET QUALITY SETUPS")
        print(f"{'='*100}")
        print(f"{'Symbol':<8} {'Side':<6} {'Score':<8} {'Change':<12} {'Price':<12} {'Volume':<15} {'Notes':<30}")
        print("-" * 100)
        
        for pick in picks:
            symbol = pick.get('symbol', 'N/A')
            side = pick.get('side', 'N/A')
            score = pick.get('score', 0)
            change = pick.get('preMarketChangePct', 0)
            price = pick.get('preMarketPrice', 0)
            volume = pick.get('volume', 0)
            notes = pick.get('notes', '')[:28]
            
            print(f"{symbol:<8} {side:<6} {score:<8.2f} {change:<12.2%} ${price:<11.2f} {volume:<15,} {notes:<30}")
        
        print()
        print("💡 These are quality setups to watch at market open (9:30 AM ET)")
        print("   Remember: Pre-market moves can reverse - use proper risk management!")
    
    print("\n" + "="*100)
    print("TEST COMPLETE")
    print("="*100)
    print()


if __name__ == "__main__":
    main()

