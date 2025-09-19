#!/usr/bin/env python3
"""
Test the Beginner-Friendly Stocks System
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.ml_stock_recommender import ml_recommender
from core.models import User

def test_beginner_stocks():
    """Test the beginner-friendly stocks system"""
    print("🌱 Testing RichesReach Beginner-Friendly Stocks System")
    print("=" * 60)
    
    # Get user
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return
    
    print(f"👤 Testing with user: {user.email}")
    
    try:
        # Test beginner-friendly stocks
        beginner_stocks = ml_recommender.get_beginner_friendly_stocks(user, 5)
        print(f"\n✅ Generated {len(beginner_stocks)} beginner-friendly recommendations:")
        print("=" * 60)
        
        for i, rec in enumerate(beginner_stocks, 1):
            print(f"\n{i}. {rec.stock.symbol} - {rec.stock.company_name}")
            print(f"   💰 Price: ${rec.stock.current_price:.2f}")
            print(f"   🌱 Beginner Score: {rec.stock.beginner_friendly_score}/100")
            print(f"   🎯 Confidence: {rec.confidence_score:.1%}")
            print(f"   ⚠️  Risk Level: {rec.risk_level}")
            print(f"   📈 Expected Return: {rec.expected_return:.1%}")
            print(f"   🧠 Reasoning: {rec.reasoning}")
            print(f"   💵 Income Level: {rec.ml_insights.get('income_level', 'unknown')}")
            print(f"   📊 P/E Ratio: {rec.stock.pe_ratio}")
            print(f"   💸 Dividend Yield: {rec.stock.dividend_yield:.2f}%" if rec.stock.dividend_yield else "   💸 Dividend Yield: N/A")
            print("-" * 60)
        
        print("\n🎉 Beginner-Friendly Stocks Test Complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_beginner_stocks()
