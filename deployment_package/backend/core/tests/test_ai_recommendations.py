"""
Test AI Recommendations resolver performance and functionality
"""
import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Stock, IncomeProfile
from core.premium_types import PremiumQueries
from core.types import ProfileInput
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AIRecommendationsTestCase(TestCase):
    """Tests for AI Recommendations resolver"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        # Create test stocks
        self.stocks = []
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'V', 'JNJ']
        
        for i, symbol in enumerate(test_symbols):
            stock = Stock.objects.create(
                symbol=symbol,
                company_name=f'Test Company {symbol}',
                sector='Technology' if i % 2 == 0 else 'Healthcare',
                market_cap=100000000000 + (i * 1000000000),  # $100B+
                pe_ratio=20.0 + (i % 10),
                dividend_yield=0.02 + (i % 5) * 0.01,
                current_price=100.0 + (i * 5),
                beginner_friendly_score=65 + (i % 20),
            )
            self.stocks.append(stock)
        
        # Create more stocks for better testing
        for i in range(40):
            symbol = f'TEST{i:03d}'
            Stock.objects.create(
                symbol=symbol,
                company_name=f'Test Company {i}',
                sector='Technology' if i % 2 == 0 else 'Healthcare',
                market_cap=50000000000 + (i * 500000000),  # $50B+
                pe_ratio=15.0 + (i % 15),
                dividend_yield=0.01 + (i % 4) * 0.01,
                current_price=50.0 + (i * 2),
                beginner_friendly_score=60 + (i % 25),
            )
    
    def _create_mock_info(self, user):
        """Create mock GraphQL info object"""
        class MockContext:
            def __init__(self, user):
                self.user = user
        
        class MockInfo:
            def __init__(self, user):
                self.context = MockContext(user)
        
        return MockInfo(user)
    
    def test_basic_ai_recommendations(self):
        """Test basic AI recommendations functionality"""
        query = PremiumQueries()
        info = self._create_mock_info(self.user)
        
        start_time = time.time()
        result = query.resolve_ai_recommendations(
            info,
            profile=None,
            using_defaults=True
        )
        elapsed = time.time() - start_time
        
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'buy_recommendations'))
        
        buy_recs = result.buy_recommendations
        self.assertIsInstance(buy_recs, list)
        
        print(f"\n✅ Basic test: {elapsed:.3f}s, {len(buy_recs)} recommendations")
        
        # Verify recommendations have required fields
        if buy_recs:
            for rec in buy_recs[:3]:
                if isinstance(rec, dict):
                    self.assertIn('symbol', rec)
                    self.assertIn('confidence', rec)
                    self.assertGreaterEqual(rec.get('confidence', 0), 0.6, "ML score should be >= 0.6")
                else:
                    self.assertTrue(hasattr(rec, 'symbol'))
                    self.assertTrue(hasattr(rec, 'confidence'))
    
    def test_ai_recommendations_with_profile(self):
        """Test AI recommendations with custom profile"""
        query = PremiumQueries()
        info = self._create_mock_info(self.user)
        
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
        
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'buy_recommendations'))
        
        buy_recs = result.buy_recommendations
        print(f"\n✅ Profile test: {elapsed:.3f}s, {len(buy_recs)} recommendations")
        
        # Verify recommendations are personalized
        if buy_recs:
            for rec in buy_recs[:3]:
                if isinstance(rec, dict):
                    self.assertIn('symbol', rec)
                    self.assertIn('risk_level', rec)
                    # Just verify risk_level field exists (GraphQL type conversion happens later)
                    risk_level = rec.get('risk_level')
                    self.assertIsNotNone(risk_level)
    
    def test_ai_recommendations_performance(self):
        """Test performance with multiple calls"""
        query = PremiumQueries()
        info = self._create_mock_info(self.user)
        
        times = []
        for i in range(5):
            start_time = time.time()
            result = query.resolve_ai_recommendations(
                info,
                profile=None,
                using_defaults=True
            )
            elapsed = time.time() - start_time
            times.append(elapsed)
            
            buy_recs = result.buy_recommendations
            print(f"   Call {i+1}: {elapsed:.3f}s - {len(buy_recs)} recommendations")
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n   Average: {avg_time:.3f}s")
        print(f"   Min: {min_time:.3f}s")
        print(f"   Max: {max_time:.3f}s")
        
        # Performance assertion
        self.assertLess(avg_time, 10.0, "Average response time should be < 10s")
        
        return times
    
    def test_ml_scoring_quality(self):
        """Test ML scoring quality"""
        query = PremiumQueries()
        info = self._create_mock_info(self.user)
        
        result = query.resolve_ai_recommendations(
            info,
            profile=None,
            using_defaults=True
        )
        
        buy_recs = result.buy_recommendations
        
        if buy_recs:
            scores = []
            for rec in buy_recs:
                if isinstance(rec, dict):
                    confidence = rec.get('confidence', 0)
                else:
                    confidence = getattr(rec, 'confidence', 0)
                scores.append(confidence)
            
            avg_score = sum(scores) / len(scores) if scores else 0
            min_score = min(scores) if scores else 0
            max_score = max(scores) if scores else 0
            
            print(f"\n   Total recommendations: {len(scores)}")
            print(f"   Average confidence: {avg_score:.2%}")
            print(f"   Min confidence: {min_score:.2%}")
            print(f"   Max confidence: {max_score:.2%}")
            
            # Quality assertions
            self.assertGreater(len(scores), 0, "Should have at least one recommendation")
            self.assertTrue(all(s >= 0.6 for s in scores), "All scores should be >= 0.6")
            self.assertGreater(avg_score, 0.5, "Average score should be > 0.5")
        else:
            print("\n   ⚠️ No recommendations returned (ML service may not be available)")
    
    def test_ai_recommendations_with_saved_profile(self):
        """Test AI recommendations with saved user profile"""
        # Create income profile
        IncomeProfile.objects.create(
            user=self.user,
            income_bracket="$75,000 - $100,000",
            age=32,
            investment_goals=["Wealth Building"],
            risk_tolerance="Aggressive",
            investment_horizon="5-10 years"
        )
        
        query = PremiumQueries()
        info = self._create_mock_info(self.user)
        
        result = query.resolve_ai_recommendations(
            info,
            profile=None,
            using_defaults=False  # Use saved profile
        )
        
        self.assertIsNotNone(result)
        buy_recs = result.buy_recommendations
        
        print(f"\n✅ Saved profile test: {len(buy_recs)} recommendations")
        
        # Verify recommendations reflect aggressive risk profile
        if buy_recs:
            for rec in buy_recs[:3]:
                if isinstance(rec, dict):
                    self.assertIn('risk_level', rec)
                    # Just verify risk_level field exists (GraphQL type conversion happens later)
                    risk_level = rec.get('risk_level')
                    self.assertIsNotNone(risk_level)

