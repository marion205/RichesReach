#!/usr/bin/env python
"""
Calculate proper beginner-friendly scores for all stocks based on:
- Market cap (larger = better for beginners)
- Volatility (lower = better for beginners)  
- P/E ratio (reasonable = better)
- Sector (less volatile sectors = better)
"""
import os
import sys
import django

sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import Stock

# Stability score for each sector (higher = more stable/beginner-friendly)
SECTOR_STABILITY = {
    'Technology': 70,
    'Consumer Cyclical': 60,
    'Financial Services': 75,
    'Healthcare': 80,
    'Utilities': 85,
    'Consumer Defensive': 85,
    'Industrial': 65,
    'Energy': 55,
    'Materials': 50,
    'Real Estate': 65,
    'Communication Services': 60,
}

def calculate_beginner_score(stock):
    """Calculate a beginner-friendly score 0-100 based on stock characteristics."""
    score = 50  # Base score
    
    # 1. Market Cap (Large caps are safer for beginners)
    market_cap = stock.market_cap
    if market_cap:
        if market_cap >= 500_000_000_000:  # $500B+
            score += 20
        elif market_cap >= 100_000_000_000:  # $100B+
            score += 18
        elif market_cap >= 50_000_000_000:  # $50B+
            score += 16
        elif market_cap >= 10_000_000_000:  # $10B+
            score += 12
        elif market_cap >= 2_000_000_000:  # $2B+
            score += 8
        elif market_cap >= 1_000_000_000:  # $1B+
            score += 5
        else:
            score -= 10  # Small caps are riskier
    
    # 2. Volatility (Lower volatility = more beginner-friendly)
    volatility = stock.volatility
    if volatility:
        vol_f = float(volatility)
        if vol_f < 15:
            score += 15  # Very stable
        elif vol_f < 20:
            score += 12  # Stable
        elif vol_f < 25:
            score += 8   # Moderate
        elif vol_f < 35:
            score += 3   # Volatile
        else:
            score -= 5   # Very volatile
    
    # 3. P/E Ratio (Reasonable P/E = more beginner-friendly)
    pe_ratio = stock.pe_ratio
    if pe_ratio:
        pe_f = float(pe_ratio)
        if 10 <= pe_f <= 20:
            score += 10  # Sweet spot
        elif 8 <= pe_f < 25:
            score += 8   # Good range
        elif 5 <= pe_f < 30:
            score += 5   # Acceptable
        elif pe_f > 50 or pe_f < 0:
            score -= 5   # Extreme/negative
    
    # 4. Sector stability
    sector = stock.sector
    if sector:
        sector_boost = SECTOR_STABILITY.get(sector, 60)
        # Normalize to 0-20 point bonus
        sector_score = (sector_boost - 50) / 3.5  # Maps 50->0, 85->10
        score += sector_score
    
    # Clamp to 0-100
    return max(0, min(100, int(round(score))))


print("Calculating beginner-friendly scores for all stocks...\n")

# First, fetch real market data for all stocks
print("Fetching real market data from Polygon API...\n")
from core.premium_analytics import PremiumAnalyticsService
import os

polygon_key = os.getenv('POLYGON_API_KEY')
if not polygon_key:
    print("⚠️  POLYGON_API_KEY not set, using existing database values")
else:
    service = PremiumAnalyticsService()
    
    # Get current snapshot data
    import requests
    symbols = list(Stock.objects.values_list('symbol', flat=True))
    
    if symbols:
        ticker_str = ','.join(symbols)
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
        params = {'tickers': ticker_str, 'apiKey': polygon_key}
        
        try:
            response = requests.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                for ticker_snap in data.get('tickers', []):
                    symbol = ticker_snap.get('ticker', '')
                    try:
                        stock = Stock.objects.get(symbol=symbol)
                        
                        # Update price
                        day_data = ticker_snap.get('day', {})
                        price = day_data.get('c') or ticker_snap.get('prevDay', {}).get('c')
                        if price:
                            stock.current_price = price
                        
                        print(f"  {symbol}: Updated price to ${price:.2f}" if price else f"  {symbol}: No price data")
                        stock.save(update_fields=['current_price'])
                    except Stock.DoesNotExist:
                        pass
            else:
                print(f"⚠️  Polygon API error: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Error fetching Polygon data: {e}")

print("\n" + "="*80)
print("Calculating beginner-friendly scores for all stocks...\n")

stocks = Stock.objects.all()
updated_count = 0

for stock in stocks:
    old_score = stock.beginner_friendly_score
    new_score = calculate_beginner_score(stock)
    
    stock.beginner_friendly_score = new_score
    stock.save(update_fields=['beginner_friendly_score'])
    updated_count += 1
    
    print(f"{stock.symbol:6} | {stock.company_name[:25]:25} | Old: {old_score:3} → New: {new_score:3} | " +
          f"Cap: {stock.market_cap or 0:15,.0f} | Vol: {stock.volatility or 0:6.2f}% | P/E: {stock.pe_ratio or 0:6.2f}")

print(f"\n✅ Updated {updated_count} stocks")

# Show distribution
print("\nScore distribution:")
for threshold in [0, 20, 40, 60, 80, 100]:
    count = Stock.objects.filter(beginner_friendly_score__gte=threshold, beginner_friendly_score__lt=threshold+20).count()
    if threshold < 100:
        print(f"  {threshold:3}-{threshold+19:3}: {count:2} stocks")
