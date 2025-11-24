"""
Seed script to populate database with test data for GraphQL testing.

Run with:
    python manage.py shell < seed_data.py
    OR
    cd deployment_package/backend && source venv/bin/activate && python -c "import django; django.setup(); exec(open('seed_data.py').read())"
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Stock, Watchlist, Portfolio

User = get_user_model()

print("🌱 Seeding database with test data...")

# Create or get demo user
user, created = User.objects.get_or_create(
    email="demo@example.com",
    defaults={
        "username": "demo",
        "name": "Demo User"
    }
)
if created:
    user.set_password("demo123")
    user.save()
    print(f"✅ Created user: {user.email}")
else:
    print(f"✅ Using existing user: {user.email}")

# Create stocks
stocks_data = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
]

created_stocks = []
for stock_data in stocks_data:
    stock, created = Stock.objects.get_or_create(
        symbol=stock_data["symbol"],
        defaults={
            "company_name": stock_data["name"],
            "sector": stock_data["sector"],
            "market_cap": 0,
            "pe_ratio": 0,
            "dividend_yield": 0,
            "beginner_friendly_score": 5,
        }
    )
    created_stocks.append(stock)
    if created:
        print(f"✅ Created stock: {stock.symbol}")
    else:
        print(f"✅ Using existing stock: {stock.symbol}")

# Create watchlist
watchlist, created = Watchlist.objects.get_or_create(
    user=user,
    stock=created_stocks[0],  # AAPL
    defaults={"notes": "Demo watchlist item"}
)
if created:
    print(f"✅ Created watchlist item: {watchlist.stock.symbol}")
else:
    print(f"✅ Watchlist item already exists: {watchlist.stock.symbol}")

# Add more stocks to watchlist
for stock in created_stocks[1:3]:  # MSFT and GOOGL
    watchlist_item, created = Watchlist.objects.get_or_create(
        user=user,
        stock=stock,
        defaults={"notes": f"Added {stock.symbol} to watchlist"}
    )
    if created:
        print(f"✅ Added {stock.symbol} to watchlist")

# Note: Portfolio model is actually the holding itself (user + stock + shares)
# There's no separate "portfolio" container, just holdings
print("✅ Portfolio model represents holdings directly (no separate portfolio container)")

# Create portfolio holdings (Portfolio model is the holding itself)
holdings_data = [
    {"stock": created_stocks[0], "shares": 10, "average_price": 150.0},  # AAPL
    {"stock": created_stocks[1], "shares": 5, "average_price": 300.0},   # MSFT
]

for holding_data in holdings_data:
    holding, created = Portfolio.objects.get_or_create(
        user=user,
        stock=holding_data["stock"],
        defaults={
            "shares": holding_data["shares"],
            "average_price": holding_data["average_price"]
        }
    )
    if created:
        print(f"✅ Created portfolio holding: {holding.stock.symbol} ({holding.shares} shares)")
    else:
        print(f"✅ Portfolio holding already exists: {holding.stock.symbol}")

print("\n✅ Seed data complete!")
print(f"\n📊 Summary:")
print(f"   - User: {user.email} (ID: {user.id})")
print(f"   - Stocks: {len(created_stocks)}")
print(f"   - Watchlist items: {Watchlist.objects.filter(user=user).count()}")
print(f"   - Portfolio holdings: {Portfolio.objects.filter(user=user).count()}")

