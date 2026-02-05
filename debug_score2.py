import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')
django.setup()

from core.models import Stock
from decimal import Decimal

# Get a stock with enriched data
stock = Stock.objects.get(symbol='GOOGL')

print(f"\n=== Full Debug ===")
print(f"Symbol: {stock.symbol}")

fundamentals_score = 50

# 1. Market Cap
market_cap = getattr(stock, "market_cap", None)
print(f"\nMarket Cap:")
print(f"  Value: {market_cap}")
print(f"  Type: {type(market_cap)}")
print(f"  Truthy: {bool(market_cap)}")
if market_cap:
    mc = float(market_cap) if market_cap else 0
    print(f"  Float: {mc}")
    if mc >= 500_000_000_000:
        fundamentals_score += 20
        print(f"  ✓ +20 bonus")

# 2. Volatility
volatility = getattr(stock, "volatility", None)
print(f"\nVolatility:")
print(f"  Value: {volatility}")
print(f"  Type: {type(volatility)}")
print(f"  Truthy: {bool(volatility)}")
if volatility:
    vol = float(volatility) if volatility else 0
    print(f"  Float: {vol}")
    if vol < 20:
        fundamentals_score += 12
        print(f"  ✓ +12 bonus")

# 3. P/E
pe_ratio = getattr(stock, "pe_ratio", None)
print(f"\nP/E Ratio:")
print(f"  Value: {pe_ratio}")
print(f"  Type: {type(pe_ratio)}")
print(f"  Truthy: {bool(pe_ratio)}")
if pe_ratio:
    pe = float(pe_ratio) if pe_ratio else 0
    print(f"  Float: {pe}")
    if 8 <= pe < 25:
        fundamentals_score += 8
        print(f"  ✓ +8 bonus")

# 4. Sector
sector = getattr(stock, "sector", None)
print(f"\nSector:")
print(f"  Value: {sector}")
print(f"  Type: {type(sector)}")
print(f"  Truthy: {bool(sector)}")

sector_stability = {
    'Technology': 70,
    'Consumer Cyclical': 60,
    'Financial Services': 75,
    'Financial': 75,
    'Healthcare': 80,
    'Utilities': 85,
    'Consumer Defensive': 85,
    'Consumer Staples': 85,
    'Industrial': 65,
    'Energy': 55,
    'Materials': 50,
    'Real Estate': 65,
    'Communication Services': 60,
}

if sector:
    sector_boost = sector_stability.get(sector, 60)
    sector_score = (sector_boost - 50) / 3.5
    fundamentals_score += sector_score
    print(f"  ✓ +{sector_score:.1f} bonus (boost: {sector_boost})")

print(f"\nFinal fundamentals_score: {fundamentals_score}")
print(f"Final score calculation: ({fundamentals_score} * 0.5) + (50 + 0) * 0.5 = {(fundamentals_score * 0.5) + 25}")
