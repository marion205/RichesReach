#!/usr/bin/env python3
"""
Compare Day Trading Algorithm Picks vs Actual Results
Saves today's picks and allows comparison with actual market performance
"""
import requests
import json
from datetime import datetime, date
from typing import Dict, List, Optional
import os
import asyncio
import aiohttp

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql/"

# Directory to store pick records
PICKS_DIR = "day_trading_picks_history"

def ensure_picks_dir():
    """Ensure the picks directory exists"""
    if not os.path.exists(PICKS_DIR):
        os.makedirs(PICKS_DIR)
        print(f"📁 Created directory: {PICKS_DIR}")

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
    
    try:
        response = requests.post(GRAPHQL_URL, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
                return None
            return data.get("data", {}).get("dayTradingPicks")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching picks: {e}")
        return None


def save_picks(picks_data: Dict, mode: str):
    """Save picks to a JSON file for later comparison"""
    ensure_picks_dir()
    
    today = date.today().isoformat()
    filename = f"{PICKS_DIR}/picks_{today}_{mode}.json"
    
    # Add metadata
    record = {
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "picks": picks_data.get("picks", []),
        "metadata": {
            "asOf": picks_data.get("asOf"),
            "universeSize": picks_data.get("universeSize"),
            "qualityThreshold": picks_data.get("qualityThreshold"),
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(record, f, indent=2)
    
    print(f"💾 Saved picks to: {filename}")
    return filename


def display_picks_summary(picks_data: Dict, mode: str):
    """Display a summary of picks in a comparison-friendly format"""
    picks = picks_data.get("picks", [])
    
    if not picks:
        print(f"\n⚠️  No picks found for {mode} mode")
        return
    
    print(f"\n{'='*100}")
    print(f"DAY TRADING PICKS - {mode} MODE")
    print(f"{'='*100}")
    print(f"Generated: {picks_data.get('asOf', 'N/A')}")
    print(f"Universe Scanned: {picks_data.get('universeSize', 0):,} symbols")
    print(f"Quality Threshold: {picks_data.get('qualityThreshold', 0):.2f}")
    print(f"Total Picks: {len(picks)}")
    print()
    
    print(f"{'Symbol':<8} {'Side':<6} {'Score':<8} {'Entry Price':<15} {'Stop':<12} {'Target 1':<12} {'Target 2':<12} {'Notes':<30}")
    print("-" * 100)
    
    for pick in picks:
        symbol = pick.get('symbol', 'N/A')
        side = pick.get('side', 'N/A')
        score = pick.get('score', 0)
        
        # Get current price (you'll need to fetch this separately or note it manually)
        # For now, we'll use the stop price as reference
        risk = pick.get('risk', {})
        stop = risk.get('stop', 0)
        targets = risk.get('targets', [])
        target1 = targets[0] if len(targets) > 0 else 0
        target2 = targets[1] if len(targets) > 1 else 0
        
        notes = pick.get('notes', '')[:28]  # Truncate for display
        
        # Calculate entry price estimate (midpoint between stop and first target for LONG, reverse for SHORT)
        if side == "LONG" and stop > 0 and target1 > 0:
            entry_estimate = (stop + target1) / 2
        elif side == "SHORT" and stop > 0 and target1 > 0:
            entry_estimate = (stop + target1) / 2
        else:
            entry_estimate = 0
        
        print(f"{symbol:<8} {side:<6} {score:<8.2f} ${entry_estimate:<14.2f} ${stop:<11.2f} ${target1:<11.2f} ${target2:<11.2f} {notes:<30}")
    
    print()
    print("📝 IMPORTANT: Note the actual entry prices when you check these stocks!")
    print("   Entry price = current market price at time of pick")
    print()


async def fetch_price_from_alpaca(symbol: str) -> Optional[float]:
    """Fetch current price from Alpaca API"""
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    if not api_key or not api_secret:
        return None
    
    try:
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars/latest"
        headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    bar = data.get('bar', {})
                    if bar:
                        return float(bar.get('c', 0))  # Close price
    except Exception as e:
        print(f"⚠️  Alpaca error for {symbol}: {e}")
    return None


async def fetch_price_from_polygon(symbol: str) -> Optional[float]:
    """Fetch current price from Polygon API"""
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        return None
    
    try:
        url = f"https://api.polygon.io/v2/last/trade/{symbol}"
        params = {'apiKey': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', {})
                    if results:
                        return float(results.get('p', 0))  # Price
    except Exception as e:
        print(f"⚠️  Polygon error for {symbol}: {e}")
    return None


async def fetch_single_price(symbol: str) -> Optional[float]:
    """Fetch price for a single symbol from available APIs"""
    # Try Alpaca first
    price = await fetch_price_from_alpaca(symbol)
    if price:
        return price
    
    # Fallback to Polygon
    price = await fetch_price_from_polygon(symbol)
    if price:
        return price
    
    return None


async def get_current_prices_async(picks: List[Dict]) -> Dict[str, float]:
    """Get current prices for all picks using real market data APIs"""
    symbols = [pick['symbol'] for pick in picks if 'symbol' in pick]
    prices = {}
    
    # Fetch all prices concurrently
    tasks = [fetch_single_price(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for symbol, result in zip(symbols, results):
        if isinstance(result, Exception):
            print(f"⚠️  Error fetching price for {symbol}: {result}")
        elif result:
            prices[symbol] = result
    
    return prices


def get_current_prices(picks: List[Dict]) -> Dict[str, float]:
    """Get current prices for all picks (wrapper for async function)"""
    try:
        return asyncio.run(get_current_prices_async(picks))
    except Exception as e:
        print(f"⚠️  Error fetching prices: {e}")
        return {}


def main():
    """Main function"""
    print("\n" + "="*100)
    print("DAY TRADING ALGORITHM - PICK COMPARISON TOOL")
    print("="*100)
    print(f"Date: {date.today().isoformat()}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Test both modes
    for mode in ["SAFE", "AGGRESSIVE"]:
        print(f"\n{'#'*100}")
        print(f"# {mode} MODE")
        print(f"{'#'*100}")
        
        picks_data = get_day_trading_picks(mode)
        
        if not picks_data:
            print(f"❌ No data returned for {mode} mode")
            continue
        
        # Display summary
        display_picks_summary(picks_data, mode)
        
        # Save picks for later comparison
        if picks_data.get("picks"):
            save_picks(picks_data, mode)
    
    print("\n" + "="*100)
    print("NEXT STEPS FOR COMPARISON:")
    print("="*100)
    print("1. 📊 Note the entry prices (current market price for each symbol)")
    print("2. ⏰ Check these stocks at end of trading day")
    print("3. 📈 Compare actual returns vs. predicted targets")
    print("4. ✅ Track which picks hit targets vs. stopped out")
    print("5. 📝 Calculate win rate and average return")
    print()
    print("💾 Picks saved in: day_trading_picks_history/")
    print("   Use these files to compare with actual results later")
    print()


if __name__ == "__main__":
    main()

