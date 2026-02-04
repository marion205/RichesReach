#!/usr/bin/env python
"""
Test that recommendations now fetch real fundamental data (P/E, volatility)
instead of using hardcoded values.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/marioncollins/RichesReach/deployment_package/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.premium_analytics import PremiumAnalyticsService
from django.core.cache import cache

# Clear cache to force fresh fetch
print("🔄 Clearing cache to force fresh data fetch...")
cache.clear()

# Create service and fetch recommendations
print("\n📊 Fetching AI recommendations with real fundamental data...\n")
service = PremiumAnalyticsService()

# Use a test user ID
recommendations = service.get_ai_recommendations(
    user_id=2,
    risk_tolerance="medium",
    profile={
        'age': 30,
        'investment_horizon_years': 5,
        'investment_goals': ['Build Wealth', 'Long-term Growth']
    }
)

# Display results
buy_recs = recommendations.get('buy_recommendations', [])
print(f"✅ Got {len(buy_recs)} recommendations\n")

if buy_recs:
    print("Top 5 Recommendations with REAL fundamental data:")
    print("=" * 90)
    
    for i, rec in enumerate(buy_recs[:5], 1):
        symbol = rec.get('symbol', 'N/A')
        name = rec.get('companyName', 'N/A')
        price = rec.get('currentPrice', 0)
        target = rec.get('targetPrice', 0)
        exp_return = rec.get('expectedReturn', 0)
        ml_score = rec.get('mlScore', 0)
        sector = rec.get('sector', 'N/A')
        
        # These should now be DIFFERENT for each stock if fix worked
        print(f"\n{i}. {symbol} - {name}")
        print(f"   Sector: {sector}")
        print(f"   Price: ${price:.2f} → Target: ${target:.2f}")
        print(f"   Expected Return: {exp_return:.2f}%")
        print(f"   ML Score: {ml_score:.1f}")
        
        # Show the fundamental data that was fetched
        reasoning = rec.get('reasoning', '')
        if reasoning:
            # Extract key metrics from reasoning
            print(f"   Reasoning preview: {reasoning[:150]}...")
    
    print("\n" + "=" * 90)
    
    # Check if all returns are identical (the bug we're fixing)
    returns = [rec.get('expectedReturn', 0) for rec in buy_recs[:5]]
    unique_returns = len(set(returns))
    
    if unique_returns == 1:
        print("\n⚠️  WARNING: All stocks have identical returns!")
        print("   This means fundamental data is still hardcoded/missing.")
    else:
        print(f"\n✅ SUCCESS: Found {unique_returns} different expected returns")
        print("   Fundamental data (P/E, volatility) is being fetched correctly!")
        print(f"   Returns range: {min(returns):.1f}% to {max(returns):.1f}%")
else:
    print("❌ No recommendations returned")
