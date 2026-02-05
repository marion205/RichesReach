import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')
django.setup()

from core.models import Stock
from core.types import StockType

# Get a stock with enriched data
stock = Stock.objects.get(symbol='GOOGL')

print(f"\n=== Stock Data ===")
print(f"Symbol: {stock.symbol}")
print(f"Market Cap: ${stock.market_cap:,}")
print(f"P/E Ratio: {stock.pe_ratio}")
print(f"Volatility: {stock.volatility}%")
print(f"Sector: {stock.sector}")

# Calculate score
stock_type = StockType(stock)

# Mock info context
class MockUser:
    id = 1
    is_anonymous = False

class MockContext:
    user = MockUser()

class MockInfo:
    context = MockContext()

info = MockInfo()

score = stock_type.resolve_beginner_friendly_score(info)
print(f"\n=== Beginner Friendly Score ===")
print(f"Score: {score}")
print(f"Recommendation: {'BUY' if score >= 60 else 'HOLD' if score >= 40 else 'AVOID'}")

# Test with multiple stocks
print(f"\n=== All Stocks ===")
for stock in Stock.objects.all()[:10]:
    stock_type = StockType(stock)
    score = stock_type.resolve_beginner_friendly_score(info)
    print(f"{stock.symbol}: {score} - {stock.market_cap} cap, {stock.pe_ratio} P/E, {stock.volatility}% vol, {stock.sector}")
