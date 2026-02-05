import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')
django.setup()

from core.models import Stock

# Get a stock with enriched data
stock = Stock.objects.get(symbol='GOOGL')

print(f"\n=== Debugging Score Calculation ===")
print(f"Symbol: {stock.symbol}")
print(f"Market Cap: {stock.market_cap} (type: {type(stock.market_cap)})")
print(f"P/E Ratio: {stock.pe_ratio} (type: {type(stock.pe_ratio)})")
print(f"Volatility: {stock.volatility} (type: {type(stock.volatility)})")
print(f"Sector: {stock.sector}")
print(f"Beginner Friendly Score (stored): {stock.beginner_friendly_score}")

# Check stored value logic
stored = getattr(stock, "beginner_friendly_score", None)
print(f"\nStored value: {stored}")
if stored is not None and int(stored) >= 40:
    print(f"✓ Returning early with stored value: {int(stored)}")
else:
    print(f"✗ Will recalculate (stored={stored})")

# Manual calculation
score = 50
fundamentals_score = 50

# Market cap
market_cap = getattr(stock, "market_cap", None)
print(f"\nMarket Cap check: {market_cap}")
if market_cap:
    mc = float(market_cap) if market_cap else 0
    print(f"  float(market_cap)={mc}")
    if mc >= 500_000_000_000:
        fundamentals_score += 20
        print(f"  +20 (>= $500B)")
    elif mc >= 100_000_000_000:
        fundamentals_score += 18
        print(f"  +18 (>= $100B)")

# Volatility
volatility = getattr(stock, "volatility", None)
print(f"\nVolatility check: {volatility} (type: {type(volatility)})")
if volatility:
    vol = float(volatility) if volatility else 0
    print(f"  float(volatility)={vol}")
    if vol < 15:
        fundamentals_score += 15
        print(f"  +15 (< 15%)")
    elif vol < 20:
        fundamentals_score += 12
        print(f"  +12 (< 20%)")
    elif vol < 25:
        fundamentals_score += 8
        print(f"  +8 (< 25%)")

# P/E
pe_ratio = getattr(stock, "pe_ratio", None)
print(f"\nP/E check: {pe_ratio}")
if pe_ratio:
    pe = float(pe_ratio) if pe_ratio else 0
    print(f"  float(pe_ratio)={pe}")
    if 10 <= pe <= 20:
        fundamentals_score += 10
        print(f"  +10 (10-20)")
    elif 8 <= pe < 25:
        fundamentals_score += 8
        print(f"  +8 (8-25)")

print(f"\nFundamentals score: {fundamentals_score}")
