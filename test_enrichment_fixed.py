import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')
django.setup()

# Clear cache first
from django.core.cache import cache
cache.clear()
print("Cache cleared")

from core.graphql.queries.market_data import MarketDataQuery
from core.models import Stock

# Test the enrichment
stocks = list(Stock.objects.filter(symbol__in=['AAPL', 'GOOGL', 'JPM'])[:3])
print(f"\nStocks before enrichment:")
for s in stocks:
    print(f"  {s.symbol}: PE={s.pe_ratio}, Cap={s.market_cap}, Sector={s.sector}")

print("\n=== Running enrichment ===")
MarketDataQuery._enrich_stocks_with_fundamentals(stocks)

# Refresh from DB
stocks = Stock.objects.filter(symbol__in=[s.symbol for s in stocks])
print(f"\nStocks after enrichment (from DB):")
for s in stocks:
    print(f"  {s.symbol}: PE={s.pe_ratio}, Cap={s.market_cap}, Sector={s.sector}")
