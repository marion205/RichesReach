#!/usr/bin/env python3
"""
Test the Production-Grade AI/ML Stock Recommendation System
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.ml_stock_recommender import ml_recommender
from core.models import User, Stock

def test_production_system():
    """Test the production-grade system with database data"""
    print("🚀 Testing Production-Grade RichesReach AI/ML System")
    print("=" * 60)
    
    # Get user
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return
    
    print(f"👤 Testing with user: {user.email}")
    
    # Test user profile
    profile = ml_recommender.get_user_profile(user)
    print(f"\n📊 User Profile:")
    print(f"   Income Level: {profile.income_level}")
    print(f"   Risk Tolerance: {profile.risk_tolerance}")
    print(f"   Portfolio Size: ${profile.portfolio_size:,.2f}")
    print(f"   Experience: {profile.experience_level}")
    
    # Test income parameters
    income_params = ml_recommender._income_params(profile)
    print(f"\n💰 Income Parameters:")
    for key, value in income_params.items():
        print(f"   {key}: {value}")
    
    # Test with database stocks (no API calls)
    print(f"\n📈 Testing with database stocks...")
    stocks = Stock.objects.all()[:5]
    print(f"Found {stocks.count()} stocks in database")
    
    for stock in stocks:
        print(f"\n🔍 Testing {stock.symbol}:")
        print(f"   Price: ${stock.current_price}")
        print(f"   Beginner Score: {stock.beginner_friendly_score}")
        print(f"   P/E Ratio: {stock.pe_ratio}")
        print(f"   Dividend Yield: {stock.dividend_yield}%")
        
        # Test affordability penalty
        affordability = ml_recommender._affordability_penalty(
            profile.portfolio_size, 
            float(stock.current_price or 0), 
            income_params["max_pos_pct"]
        )
        print(f"   Affordability Score: {affordability:.2f}")
        
        # Test liquidity penalty
        liquidity = ml_recommender._liquidity_penalty(
            stock, 
            income_params["min_liquidity_usd"]
        )
        print(f"   Liquidity Score: {liquidity:.2f}")
        
        # Test beginner score normalization
        norm_score = ml_recommender._normalize_beginner_score(stock.beginner_friendly_score)
        print(f"   Normalized Beginner Score: {norm_score:.1f}/10")
    
    # Test ML recommendations (will be empty without API data)
    print(f"\n🤖 Testing ML Recommendations...")
    try:
        recommendations = ml_recommender.generate_ml_recommendations(user, 3)
        print(f"Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.stock.symbol} - {rec.stock.company_name}")
            print(f"   Confidence: {rec.confidence_score:.1%}")
            print(f"   Risk Level: {rec.risk_level}")
            print(f"   Expected Return: {rec.expected_return:.1%}")
            print(f"   Reasoning: {rec.reasoning}")
            if "suggested_allocation_pct" in rec.ml_insights:
                print(f"   Suggested Allocation: {rec.ml_insights['suggested_allocation_pct']:.1%}")
    except Exception as e:
        print(f"❌ Error generating recommendations: {e}")
    
    # Test beginner-friendly stocks
    print(f"\n🌱 Testing Beginner-Friendly Stocks...")
    try:
        beginner_stocks = ml_recommender.get_beginner_friendly_stocks(user, 3)
        print(f"Generated {len(beginner_stocks)} beginner-friendly recommendations")
        
        for i, rec in enumerate(beginner_stocks, 1):
            print(f"\n{i}. {rec.stock.symbol} - {rec.stock.company_name}")
            print(f"   Confidence: {rec.confidence_score:.1%}")
            print(f"   Risk Level: {rec.risk_level}")
            print(f"   Expected Return: {rec.expected_return:.1%}")
            print(f"   Reasoning: {rec.reasoning}")
    except Exception as e:
        print(f"❌ Error generating beginner-friendly stocks: {e}")
    
    # Test ML service status
    print(f"\n🔧 ML Service Status:")
    try:
        status = ml_recommender.get_ml_service_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Error getting ML status: {e}")
    
    print(f"\n🎉 Production System Test Complete!")

if __name__ == "__main__":
    test_production_system()
