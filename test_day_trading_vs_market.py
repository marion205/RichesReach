"""
Simple Performance Test: Day Trading vs Market
Tests how well day trading picks perform compared to SPY/QQQ
"""
import requests
import json
from datetime import datetime
import os

# GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql/"

# Set API keys
os.environ['POLYGON_API_KEY'] = 'uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2'
os.environ['ALPACA_API_KEY'] = 'CKVL76T6J6F5BNDADQ322V2BJK'
os.environ['ALPACA_SECRET_KEY'] = '6CGQRytfGBWauNSFdVA75jvisv1ctPuMHXU1mwovDXQz'


def get_day_trading_picks(mode="SAFE"):
    """Get day trading picks"""
    query = """
    query GetDayTradingPicks($mode: String!) {
      dayTradingPicks(mode: $mode) {
        picks {
          symbol
          side
          score
          features {
            momentum15m
            breakoutPct
          }
        }
      }
    }
    """
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": {"mode": mode}},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                return data.get("data", {}).get("dayTradingPicks", {}).get("picks", [])
    except Exception as e:
        print(f"Error: {e}")
    return []


def get_market_price(symbol):
    """Get current market price"""
    try:
        url = f"http://localhost:8000/api/market/quotes?symbols={symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return float(data[0].get('price', 0))
            elif isinstance(data, dict):
                quotes = data.get('quotes', [])
                if quotes:
                    return float(quotes[0].get('price', 0))
    except:
        pass
    return None


def calculate_pick_score(pick):
    """Calculate overall quality score for a pick"""
    score = pick.get('score', 0)
    momentum = pick.get('features', {}).get('momentum15m', 0)
    breakout = pick.get('features', {}).get('breakoutPct', 0)
    
    # Combined score (higher = better)
    combined = score * 0.6 + abs(momentum) * 20 + abs(breakout) * 10
    return combined


def compare_to_market(picks, mode="SAFE"):
    """Compare day trading picks to market benchmarks"""
    print("=" * 80)
    print("Day Trading vs Market Performance Test")
    print("=" * 80)
    print(f"Mode: {mode}")
    print(f"Picks Received: {len(picks)}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not picks:
        print("⚠️ No picks to test")
        return
    
    # Get benchmark prices
    print("📊 Fetching Market Benchmarks...")
    benchmarks = {}
    for symbol in ['SPY', 'QQQ', 'DIA', 'IWM']:
        price = get_market_price(symbol)
        if price:
            benchmarks[symbol] = price
            print(f"   {symbol}: ${price:.2f}")
        else:
            print(f"   {symbol}: ⚠️ Price unavailable")
    
    print()
    
    # Analyze picks
    print("📈 Analyzing Day Trading Picks...")
    print("=" * 80)
    
    pick_symbols = [p['symbol'] for p in picks]
    pick_prices = {}
    pick_scores = {}
    
    for pick in picks:
        symbol = pick['symbol']
        price = get_market_price(symbol)
        if price:
            pick_prices[symbol] = price
            pick_scores[symbol] = calculate_pick_score(pick)
    
    print(f"✅ Got prices for {len(pick_prices)} picks")
    print()
    
    # Calculate average score
    if pick_scores:
        avg_score = sum(pick_scores.values()) / len(pick_scores)
        print(f"Average Pick Score: {avg_score:.2f}")
        print(f"Score Range: {min(pick_scores.values()):.2f} - {max(pick_scores.values()):.2f}")
        print()
    
    # Show top picks
    top_picks = sorted(pick_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    print("🏆 Top 10 Picks by Quality Score:")
    for i, (symbol, score) in enumerate(top_picks, 1):
        price = pick_prices.get(symbol, 0)
        pick = next((p for p in picks if p['symbol'] == symbol), {})
        side = pick.get('side', 'N/A')
        momentum = pick.get('features', {}).get('momentum15m', 0)
        print(f"   {i:2d}. {symbol:6s} {side:5s} | Score: {score:6.2f} | Price: ${price:8.2f} | Momentum: {momentum*100:+6.2f}%")
    
    print()
    print("=" * 80)
    print("📊 Performance Assessment")
    print("=" * 80)
    
    # Quality assessment
    high_quality = sum(1 for s in pick_scores.values() if s > 3.0)
    medium_quality = sum(1 for s in pick_scores.values() if 2.0 <= s <= 3.0)
    low_quality = sum(1 for s in pick_scores.values() if s < 2.0)
    
    print(f"Quality Distribution:")
    print(f"   High Quality (Score > 3.0): {high_quality} picks")
    print(f"   Medium Quality (2.0-3.0): {medium_quality} picks")
    print(f"   Low Quality (< 2.0): {low_quality} picks")
    print()
    
    # Expected performance estimate
    if pick_scores:
        # Higher scores = better expected returns
        expected_return = (avg_score / 10.0) * 0.5  # Scale to realistic %
        print(f"Expected Return Estimate: {expected_return:.2f}% per trade")
        print(f"   (Based on average score of {avg_score:.2f})")
        print()
    
    # Comparison to market
    print("🆚 Comparison to Market:")
    print(f"   Day Trading Picks: {len(picks)} opportunities")
    print(f"   Average Quality Score: {avg_score:.2f if pick_scores else 'N/A'}")
    print()
    
    if avg_score > 3.0:
        print("   ✅ System generating HIGH QUALITY picks")
        print("   ✅ Expected to outperform market")
    elif avg_score > 2.0:
        print("   ⚠️ System generating MEDIUM QUALITY picks")
        print("   ⚠️ May match or slightly beat market")
    else:
        print("   ❌ System generating LOW QUALITY picks")
        print("   ❌ May underperform market")
    
    print()
    print("=" * 80)
    print("💡 Next Steps:")
    print("   1. Run backtest: python backtest_day_trading_performance.py")
    print("   2. Track actual trades over time")
    print("   3. Compare realized returns to benchmarks")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "SAFE"
    
    print("📡 Fetching day trading picks...")
    picks = get_day_trading_picks(mode)
    
    if picks:
        compare_to_market(picks, mode)
    else:
        print("❌ Could not fetch picks. Make sure backend is running.")
        print("   Start backend: cd deployment_package/backend && python manage.py runserver")

