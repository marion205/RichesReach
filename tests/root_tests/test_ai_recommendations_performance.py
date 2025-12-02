#!/usr/bin/env python3
"""
Test script for AI Recommendations resolver performance
Tests the dynamic ML scoring implementation
"""

import os
import sys
import time
import django
from pathlib import Path

# Setup Django
backend_path = Path(__file__).parent / 'deployment_package' / 'backend'
sys.path.insert(0, str(backend_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from core.models import Stock, IncomeProfile
from core.queries import Query
from core.types import ProfileInput
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

def create_test_user():
    """Create or get test user"""
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={'name': 'Test User'}
    )
    return user

def create_test_stocks(count=50):
    """Create test stocks in database"""
    stocks_created = 0
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'V', 'JNJ']
    
    for i in range(count):
        symbol = f'TEST{i:03d}' if i >= len(test_symbols) else test_symbols[i % len(test_symbols)]
        
        stock, created = Stock.objects.get_or_create(
            symbol=symbol,
            defaults={
                'company_name': f'Test Company {i}',
                'sector': 'Technology' if i % 2 == 0 else 'Healthcare',
                'market_cap': 100000000000 + (i * 1000000000),  # $100B+
                'pe_ratio': 20.0 + (i % 10),
                'dividend_yield': 0.02 + (i % 5) * 0.01,
                'current_price': 100.0 + (i * 5),
                'beginner_friendly_score': 65 + (i % 20),
            }
        )
        if created:
            stocks_created += 1
    
    logger.info(f"Created {stocks_created} new test stocks")
    return stocks_created

def test_ai_recommendations_basic():
    """Test basic AI recommendations functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic AI Recommendations")
    print("="*60)
    
    user = create_test_user()
    factory = RequestFactory()
    request = factory.post('/graphql/')
    request.user = user
    
    # Create mock context
    class MockInfo:
        def __init__(self):
            self.context = type('Context', (), {'user': user})()
    
    info = MockInfo()
    query = Query()
    
    # Test with default profile
    start_time = time.time()
    result = query.resolve_ai_recommendations(
        info,
        profile=None,
        using_defaults=True
    )
    elapsed = time.time() - start_time
    
    print(f"✅ Query completed in {elapsed:.3f}s")
    print(f"   Buy recommendations: {len(result.buy_recommendations) if hasattr(result, 'buy_recommendations') else 0}")
    
    if hasattr(result, 'buy_recommendations') and result.buy_recommendations:
        print(f"\n   Top 3 recommendations:")
        for i, rec in enumerate(result.buy_recommendations[:3], 1):
            symbol = rec.get('symbol') if isinstance(rec, dict) else getattr(rec, 'symbol', 'N/A')
            confidence = rec.get('confidence') if isinstance(rec, dict) else getattr(rec, 'confidence', 0)
            print(f"   {i}. {symbol}: {confidence:.2%} confidence")
    
    return elapsed, result

def test_ai_recommendations_with_profile():
    """Test AI recommendations with custom profile"""
    print("\n" + "="*60)
    print("TEST 2: AI Recommendations with Custom Profile")
    print("="*60)
    
    user = create_test_user()
    
    class MockInfo:
        def __init__(self):
            self.context = type('Context', (), {'user': user})()
    
    info = MockInfo()
    query = Query()
    
    # Create profile input
    profile = ProfileInput(
        age=35,
        incomeBracket="$50,000 - $100,000",
        investmentGoals=["Wealth Building", "Retirement"],
        investmentHorizonYears=10,
        riskTolerance="Moderate"
    )
    
    start_time = time.time()
    result = query.resolve_ai_recommendations(
        info,
        profile=profile,
        using_defaults=False
    )
    elapsed = time.time() - start_time
    
    print(f"✅ Query completed in {elapsed:.3f}s")
    print(f"   Buy recommendations: {len(result.buy_recommendations) if hasattr(result, 'buy_recommendations') else 0}")
    
    return elapsed, result

def test_ai_recommendations_performance():
    """Test performance with multiple calls"""
    print("\n" + "="*60)
    print("TEST 3: Performance Test (10 calls)")
    print("="*60)
    
    user = create_test_user()
    
    class MockInfo:
        def __init__(self):
            self.context = type('Context', (), {'user': user})()
    
    info = MockInfo()
    query = Query()
    
    times = []
    for i in range(10):
        start_time = time.time()
        result = query.resolve_ai_recommendations(
            info,
            profile=None,
            using_defaults=True
        )
        elapsed = time.time() - start_time
        times.append(elapsed)
        print(f"   Call {i+1}: {elapsed:.3f}s - {len(result.buy_recommendations) if hasattr(result, 'buy_recommendations') else 0} recommendations")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n   Average: {avg_time:.3f}s")
    print(f"   Min: {min_time:.3f}s")
    print(f"   Max: {max_time:.3f}s")
    
    return times

def test_ml_scoring_quality():
    """Test ML scoring quality"""
    print("\n" + "="*60)
    print("TEST 4: ML Scoring Quality Check")
    print("="*60)
    
    user = create_test_user()
    
    class MockInfo:
        def __init__(self):
            self.context = type('Context', (), {'user': user})()
    
    info = MockInfo()
    query = Query()
    
    result = query.resolve_ai_recommendations(
        info,
        profile=None,
        using_defaults=True
    )
    
    if hasattr(result, 'buy_recommendations') and result.buy_recommendations:
        scores = []
        for rec in result.buy_recommendations:
            confidence = rec.get('confidence') if isinstance(rec, dict) else getattr(rec, 'confidence', 0)
            scores.append(confidence)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0
        
        print(f"   Total recommendations: {len(scores)}")
        print(f"   Average confidence: {avg_score:.2%}")
        print(f"   Min confidence: {min_score:.2%}")
        print(f"   Max confidence: {max_score:.2%}")
        print(f"   All scores >= 0.6: {all(s >= 0.6 for s in scores)}")
        
        return scores
    else:
        print("   ⚠️ No recommendations returned")
        return []

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI RECOMMENDATIONS PERFORMANCE TEST")
    print("="*60)
    
    # Ensure we have test stocks
    print("\n📊 Setting up test data...")
    stocks_count = Stock.objects.filter(current_price__isnull=False, current_price__gt=0).count()
    if stocks_count < 20:
        print(f"   Creating test stocks (current: {stocks_count})...")
        create_test_stocks(50)
    else:
        print(f"   Using existing stocks: {stocks_count}")
    
    # Run tests
    try:
        # Test 1: Basic functionality
        elapsed1, result1 = test_ai_recommendations_basic()
        
        # Test 2: With profile
        elapsed2, result2 = test_ai_recommendations_with_profile()
        
        # Test 3: Performance
        times = test_ai_recommendations_performance()
        
        # Test 4: Quality
        scores = test_ml_scoring_quality()
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"✅ Basic test: {elapsed1:.3f}s")
        print(f"✅ Profile test: {elapsed2:.3f}s")
        print(f"✅ Performance: {sum(times)/len(times):.3f}s avg")
        print(f"✅ Quality: {len(scores)} recommendations, avg confidence: {sum(scores)/len(scores):.2%}" if scores else "⚠️ No recommendations")
        
        # Performance assessment
        avg_time = sum(times) / len(times) if times else elapsed1
        if avg_time < 1.0:
            print(f"\n🚀 EXCELLENT: Average response time < 1s")
        elif avg_time < 2.0:
            print(f"\n✅ GOOD: Average response time < 2s")
        elif avg_time < 5.0:
            print(f"\n⚠️ ACCEPTABLE: Average response time < 5s")
        else:
            print(f"\n❌ SLOW: Average response time >= 5s")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

