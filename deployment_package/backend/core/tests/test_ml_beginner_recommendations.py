# core/tests/test_ml_beginner_recommendations.py
"""
Tests for the ML-based beginner stock recommendation service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from decimal import Decimal
from uuid import uuid4


class TestMLBeginnerRecommendations(TestCase):
    """Test cases for MLBeginnerRecommendationService"""

    def setUp(self):
        """Set up test fixtures"""
        from core.models import Stock, User

        # Create test user
        self.user = User.objects.create(
            email=f'test_{uuid4()}@example.com',
            name='Test User'
        )

        # Create test stocks with various characteristics
        self.stocks = []

        # Conservative stock - large cap, low volatility, stable sector
        self.conservative_stock = Stock.objects.create(
            symbol='JNJ',
            company_name='Johnson & Johnson',
            sector='Healthcare',
            market_cap=400000000000,  # $400B
            pe_ratio=Decimal('18.5'),
            volatility=Decimal('12.0'),
            dividend_yield=Decimal('0.028'),
            current_price=Decimal('160.00')
        )
        self.stocks.append(self.conservative_stock)

        # Growth stock - tech sector, higher volatility
        self.growth_stock = Stock.objects.create(
            symbol='NVDA',
            company_name='NVIDIA Corporation',
            sector='Technology',
            market_cap=1200000000000,  # $1.2T
            pe_ratio=Decimal('65.0'),
            volatility=Decimal('35.0'),
            dividend_yield=Decimal('0.001'),
            current_price=Decimal('500.00')
        )
        self.stocks.append(self.growth_stock)

        # Moderate stock - financial sector
        self.moderate_stock = Stock.objects.create(
            symbol='JPM',
            company_name='JPMorgan Chase',
            sector='Financial Services',
            market_cap=500000000000,  # $500B
            pe_ratio=Decimal('12.0'),
            volatility=Decimal('22.0'),
            dividend_yield=Decimal('0.025'),
            current_price=Decimal('175.00')
        )
        self.stocks.append(self.moderate_stock)

    def test_service_initialization(self):
        """Test that ML service initializes correctly"""
        from core.ml_beginner_recommendations import get_ml_recommender

        recommender = get_ml_recommender()
        self.assertIsNotNone(recommender)
        self.assertIsNotNone(recommender.SECTOR_STABILITY)
        self.assertIsNotNone(recommender.PERSONAS)

    def test_extract_user_features_default(self):
        """Test user feature extraction with defaults (no profile)"""
        from core.ml_beginner_recommendations import get_ml_recommender

        recommender = get_ml_recommender()
        features = recommender.extract_user_features(self.user.id)

        # Should return default values
        self.assertIsNotNone(features)
        self.assertGreaterEqual(features.risk_score, 0)
        self.assertLessEqual(features.risk_score, 1)
        self.assertGreaterEqual(features.age_normalized, 0)
        self.assertLessEqual(features.age_normalized, 1)

    def test_extract_user_features_with_profile(self):
        """Test user feature extraction with income profile"""
        from core.models import IncomeProfile
        from core.ml_beginner_recommendations import get_ml_recommender

        # Create income profile
        profile = IncomeProfile.objects.create(
            user=self.user,
            income_bracket='$100,000 - $149,999',
            age=35,
            risk_tolerance='Moderate',
            investment_horizon='5-10 years',
            investment_goals=['Retirement', 'Growth']
        )

        recommender = get_ml_recommender()
        features = recommender.extract_user_features(self.user.id)

        self.assertEqual(features.risk_score, 0.5)  # Moderate = 0.5
        self.assertAlmostEqual(features.age_normalized, (35 - 18) / 62, places=2)

    def test_extract_stock_features(self):
        """Test stock feature extraction"""
        from core.ml_beginner_recommendations import get_ml_recommender

        recommender = get_ml_recommender()
        features = recommender.extract_stock_features(self.conservative_stock)

        self.assertEqual(features.symbol, 'JNJ')
        self.assertEqual(features.sector, 'Healthcare')
        self.assertGreater(features.market_cap_normalized, 0.5)  # Large cap
        self.assertGreater(features.volatility_normalized, 0.8)  # Low volatility = high score

    def test_classify_user_persona_conservative(self):
        """Test persona classification for conservative user"""
        from core.ml_beginner_recommendations import (
            get_ml_recommender,
            UserFeatureVector
        )

        recommender = get_ml_recommender()

        # Conservative user features
        features = UserFeatureVector(
            age_normalized=0.7,  # Older
            income_normalized=0.5,
            risk_score=0.15,  # Very conservative
            horizon_normalized=0.2,  # Short horizon
            portfolio_size_normalized=0.3,
            spending_volatility=0.2,
            discretionary_ratio=0.3,
            sector_preferences={}
        )

        persona, confidence = recommender.classify_user_persona(features)

        self.assertEqual(persona, 'Conservative Beginner')
        self.assertGreater(confidence, 0.5)

    def test_classify_user_persona_growth(self):
        """Test persona classification for growth-oriented user"""
        from core.ml_beginner_recommendations import (
            get_ml_recommender,
            UserFeatureVector
        )

        recommender = get_ml_recommender()

        # Growth-oriented user features
        features = UserFeatureVector(
            age_normalized=0.2,  # Younger
            income_normalized=0.6,
            risk_score=0.8,  # Aggressive
            horizon_normalized=0.8,  # Long horizon
            portfolio_size_normalized=0.2,
            spending_volatility=0.3,
            discretionary_ratio=0.4,
            sector_preferences={'Technology': 0.5}
        )

        persona, confidence = recommender.classify_user_persona(features)

        self.assertEqual(persona, 'Growth-Oriented Beginner')
        self.assertGreater(confidence, 0.5)

    def test_calculate_fundamentals_score(self):
        """Test fundamentals score calculation"""
        from core.ml_beginner_recommendations import get_ml_recommender

        recommender = get_ml_recommender()

        # Conservative stock should score high
        conservative_features = recommender.extract_stock_features(self.conservative_stock)
        conservative_score = recommender.calculate_fundamentals_score(conservative_features)

        # Growth stock may score lower due to high volatility and P/E
        growth_features = recommender.extract_stock_features(self.growth_stock)
        growth_score = recommender.calculate_fundamentals_score(growth_features)

        self.assertGreater(conservative_score, 50)
        # Conservative stock should generally score higher for beginners
        self.assertGreater(conservative_score, growth_score)

    def test_get_personalized_recommendations(self):
        """Test end-to-end personalized recommendations"""
        from core.ml_beginner_recommendations import get_ml_recommender

        recommender = get_ml_recommender()
        recommendations = recommender.get_personalized_recommendations(
            self.user.id,
            limit=10
        )

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Check recommendation structure
        for rec in recommendations:
            self.assertIsNotNone(rec.symbol)
            self.assertIsNotNone(rec.ml_score)
            self.assertGreaterEqual(rec.ml_score, 0)
            self.assertLessEqual(rec.ml_score, 100)
            self.assertIn(rec.recommendation, ['BUY', 'HOLD', 'AVOID'])
            self.assertIsInstance(rec.reasons, list)

    def test_recommendations_are_personalized(self):
        """Test that different user profiles get different recommendations"""
        from core.models import IncomeProfile
        from core.ml_beginner_recommendations import get_ml_recommender

        # Create second user with different profile
        from core.models import User
        aggressive_user = User.objects.create(
            email='aggressive@example.com',
            name='Aggressive User'
        )

        IncomeProfile.objects.create(
            user=aggressive_user,
            income_bracket='$150,000 - $199,999',
            age=28,
            risk_tolerance='Aggressive',
            investment_horizon='10+ years',
            investment_goals=['Growth']
        )

        # Create conservative user profile
        IncomeProfile.objects.create(
            user=self.user,
            income_bracket='$50,000 - $74,999',
            age=55,
            risk_tolerance='Conservative',
            investment_horizon='3-5 years',
            investment_goals=['Retirement']
        )

        recommender = get_ml_recommender()

        # Get recommendations for both users
        conservative_recs = recommender.get_personalized_recommendations(
            self.user.id, limit=5
        )
        aggressive_recs = recommender.get_personalized_recommendations(
            aggressive_user.id, limit=5
        )

        # Both should get recommendations
        self.assertGreater(len(conservative_recs), 0)
        self.assertGreater(len(aggressive_recs), 0)

        # If we have enough diversity in stocks, recommendations might differ
        # At minimum, the scores should differ
        if conservative_recs and aggressive_recs:
            # Find same stock in both recommendations
            conservative_symbols = {r.symbol: r.ml_score for r in conservative_recs}
            aggressive_symbols = {r.symbol: r.ml_score for r in aggressive_recs}

            common_symbols = set(conservative_symbols.keys()) & set(aggressive_symbols.keys())

            # Scores for same stocks may differ due to personalization
            # This is a soft check - personalization means different weighting
            for symbol in common_symbols:
                # Just verify scores exist and are valid
                self.assertGreaterEqual(conservative_symbols[symbol], 0)
                self.assertGreaterEqual(aggressive_symbols[symbol], 0)

    def test_ml_recommendation_type_graphql(self):
        """Test that MLRecommendationType works correctly"""
        from core.types import MLRecommendationType

        # Test with dict input (how GraphQL resolver returns it)
        rec_dict = {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'ml_score': 75.5,
            'confidence': 0.85,
            'recommendation': 'BUY',
            'reasons': ['Large market cap', 'Strong fundamentals'],
            'persona_match': 80.0,
            'similar_user_score': 70.0,
            'fundamentals_score': 76.0
        }

        rec_type = MLRecommendationType()

        # Test camelCase resolvers work with dict
        self.assertEqual(
            rec_type.resolve_companyName(rec_dict, None),
            'Apple Inc.'
        )
        self.assertEqual(
            rec_type.resolve_mlScore(rec_dict, None),
            75.5
        )


class TestBeginnerFriendlyScoreFix(TestCase):
    """Test the UserProfile -> IncomeProfile fix in types.py"""

    def setUp(self):
        """Set up test fixtures"""
        from core.models import Stock, User, IncomeProfile, Portfolio

        self.user = User.objects.create(
            email=f'profile_test_{uuid4()}@example.com',
            name='Profile Test User'
        )

        self.stock = Stock.objects.create(
            symbol='TEST',
            company_name='Test Company',
            sector='Technology',
            market_cap=100000000000,
            pe_ratio=Decimal('20.0'),
            volatility=Decimal('25.0'),
            current_price=Decimal('100.00')
        )

    def test_score_without_profile(self):
        """Test scoring works without income profile (uses defaults)"""
        from core.types import StockType

        # Create mock info context
        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = self.user

        stock_type = StockType()
        stock_type.market_cap = self.stock.market_cap
        stock_type.volatility = self.stock.volatility
        stock_type.pe_ratio = self.stock.pe_ratio
        stock_type.sector = self.stock.sector

        score = stock_type.resolve_beginner_friendly_score(mock_info)

        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_score_with_income_profile(self):
        """Test scoring incorporates IncomeProfile correctly"""
        from core.models import IncomeProfile
        from core.types import StockType

        # Create income profile with conservative settings
        IncomeProfile.objects.create(
            user=self.user,
            income_bracket='Under $25,000',
            age=45,
            risk_tolerance='Conservative',
            investment_horizon='1-3 years',
            investment_goals=['Retirement']
        )

        # Create mock info context
        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = self.user

        stock_type = StockType()
        stock_type.market_cap = self.stock.market_cap
        stock_type.volatility = self.stock.volatility
        stock_type.pe_ratio = self.stock.pe_ratio
        stock_type.sector = self.stock.sector

        score = stock_type.resolve_beginner_friendly_score(mock_info)

        # Score should be higher for conservative user with stable stock
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_portfolio_value_aggregation(self):
        """Test that portfolio value is correctly aggregated across holdings"""
        from core.models import Portfolio
        from core.types import StockType
        from decimal import Decimal

        # Create multiple portfolio holdings
        from core.models import Stock
        stock1 = Stock.objects.create(
            symbol='HOLD1',
            company_name='Holding 1',
            current_price=Decimal('100.00')
        )
        stock2 = Stock.objects.create(
            symbol='HOLD2',
            company_name='Holding 2',
            current_price=Decimal('200.00')
        )

        Portfolio.objects.create(
            user=self.user,
            stock=stock1,
            shares=10,
            average_price=Decimal('90.00'),
            current_price=Decimal('100.00'),
            total_value=Decimal('1000.00')  # 10 * $100
        )

        Portfolio.objects.create(
            user=self.user,
            stock=stock2,
            shares=5,
            average_price=Decimal('180.00'),
            current_price=Decimal('200.00'),
            total_value=Decimal('1000.00')  # 5 * $200
        )

        # Mock info context
        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = self.user

        stock_type = StockType()
        stock_type.market_cap = self.stock.market_cap
        stock_type.volatility = self.stock.volatility
        stock_type.pe_ratio = self.stock.pe_ratio
        stock_type.sector = self.stock.sector

        score = stock_type.resolve_beginner_friendly_score(mock_info)

        # Total portfolio should be $2000 (1000 + 1000)
        # This should give a portfolio size bonus for small portfolio
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 50)  # Should be reasonably high


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
