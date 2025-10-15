#!/usr/bin/env python3
"""
Test the ML Stock Recommendation System
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.ml_stock_recommender import ml_recommender
from core.models import User

def test_ml_system():
    """Test the complete ML recommendation system"""
    print("🤖 Testing RichesReach AI/ML Stock Recommendation System")
    print("=" * 60)
    
    # Get user
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return
    
    print(f"👤 Testing with user: {user.email}")
    
    try:
        # Generate recommendations
        recommendations = ml_recommender.generate_ml_recommendations(user, 5)
        print(f"\n✅ Generated {len(recommendations)} AI recommendations:")
        print("=" * 60)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.stock.symbol} - {rec.stock.company_name}")
            print(f"   💰 Price: ${rec.stock.current_price:.2f}")
            print(f"   🎯 Confidence: {rec.confidence_score:.1%}")
            print(f"   ⚠️  Risk Level: {rec.risk_level}")
            print(f"   📈 Expected Return: {rec.expected_return:.1%}")
            print(f"   🧠 AI Reasoning: {rec.reasoning}")
            print(f"   📊 ML Insights: {rec.ml_insights}")
            print("-" * 60)
        
        # Test ML service status
        print("\n🔧 ML Service Status:")
        status = ml_recommender.get_ml_service_status()
        print(f"   Status: {status}")
        
        print("\n🎉 ML System Test Complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ml_system()
