"""
Unit tests for StockMoment GraphQL queries
"""
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import StockMoment, MomentCategory
from core.graphql.queries.discussions import DiscussionsQuery
from core.types import ChartRangeEnum


class StockMomentQueriesTestCase(TestCase):
    """Tests for StockMoment GraphQL queries"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.now = timezone.make_aware(datetime(2024, 8, 1, 12, 0, 0))
        self.symbol = "AAPL"
        self.query = DiscussionsQuery()
        
        # Create test moments
        self.moment_1m = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now - timedelta(days=10),
            importance_score=0.8,
            category=MomentCategory.EARNINGS,
            title="Earnings Beat",
            quick_summary="Beat estimates",
            deep_summary="Detailed earnings analysis",
        )
        
        self.moment_3m = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now - timedelta(days=60),
            importance_score=0.7,
            category=MomentCategory.NEWS,
            title="Product Launch",
            quick_summary="New product",
            deep_summary="Product launch details",
        )
        
        self.moment_6m = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now - timedelta(days=120),
            importance_score=0.6,
            category=MomentCategory.INSIDER,
            title="Insider Buy",
            quick_summary="Insider purchase",
            deep_summary="Insider transaction details",
        )
        
        self.moment_ytd = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=datetime(self.now.year, 1, 15, tzinfo=self.now.tzinfo),
            importance_score=0.9,
            category=MomentCategory.MACRO,
            title="Macro Event",
            quick_summary="Macro impact",
            deep_summary="Macro event details",
        )
        
        self.moment_1y = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now - timedelta(days=200),
            importance_score=0.5,
            category=MomentCategory.SENTIMENT,
            title="Sentiment Shift",
            quick_summary="Sentiment change",
            deep_summary="Sentiment analysis",
        )
        
        # Create moment for different symbol
        self.other_moment = StockMoment.objects.create(
            symbol="TSLA",
            timestamp=self.now - timedelta(days=10),
            importance_score=0.8,
            category=MomentCategory.NEWS,
            title="TSLA News",
            quick_summary="Tesla news",
            deep_summary="Tesla news details",
        )
    
    def test_resolve_stock_moments_one_month(self):
        """Test resolving moments for ONE_MONTH range"""
        moments = self.query.resolve_stock_moments(
            None,  # info
            self.symbol,
            ChartRangeEnum.ONE_MONTH
        )
        
        # Should only include moment_1m (10 days ago)
        self.assertEqual(len(moments), 1)
        self.assertEqual(moments[0].id, self.moment_1m.id)
    
    def test_resolve_stock_moments_three_months(self):
        """Test resolving moments for THREE_MONTHS range"""
        moments = self.query.resolve_stock_moments(
            None,
            self.symbol,
            ChartRangeEnum.THREE_MONTHS
        )
        
        # Should include moment_1m and moment_3m
        self.assertEqual(len(moments), 2)
        moment_ids = [m.id for m in moments]
        self.assertIn(self.moment_1m.id, moment_ids)
        self.assertIn(self.moment_3m.id, moment_ids)
    
    def test_resolve_stock_moments_six_months(self):
        """Test resolving moments for SIX_MONTHS range"""
        moments = self.query.resolve_stock_moments(
            None,
            self.symbol,
            ChartRangeEnum.SIX_MONTHS
        )
        
        # Should include moment_1m, moment_3m, and moment_6m
        self.assertEqual(len(moments), 3)
        moment_ids = [m.id for m in moments]
        self.assertIn(self.moment_1m.id, moment_ids)
        self.assertIn(self.moment_3m.id, moment_ids)
        self.assertIn(self.moment_6m.id, moment_ids)
    
    def test_resolve_stock_moments_year_to_date(self):
        """Test resolving moments for YEAR_TO_DATE range"""
        moments = self.query.resolve_stock_moments(
            None,
            self.symbol,
            ChartRangeEnum.YEAR_TO_DATE
        )
        
        # Should include all moments in the current year
        self.assertEqual(len(moments), 5)
        moment_ids = [m.id for m in moments]
        self.assertIn(self.moment_1m.id, moment_ids)
        self.assertIn(self.moment_3m.id, moment_ids)
        self.assertIn(self.moment_6m.id, moment_ids)
        self.assertIn(self.moment_ytd.id, moment_ids)
        self.assertIn(self.moment_1y.id, moment_ids)
    
    def test_resolve_stock_moments_one_year(self):
        """Test resolving moments for ONE_YEAR range"""
        moments = self.query.resolve_stock_moments(
            None,
            self.symbol,
            ChartRangeEnum.ONE_YEAR
        )
        
        # Should include all moments except moment_1y (200 days > 365)
        # Actually, 200 days is < 365, so it should be included
        self.assertGreaterEqual(len(moments), 4)
        moment_ids = [m.id for m in moments]
        self.assertIn(self.moment_1m.id, moment_ids)
        self.assertIn(self.moment_3m.id, moment_ids)
        self.assertIn(self.moment_6m.id, moment_ids)
        self.assertIn(self.moment_1y.id, moment_ids)
    
    def test_resolve_stock_moments_symbol_filtering(self):
        """Test that moments are filtered by symbol"""
        moments = self.query.resolve_stock_moments(
            None,
            "TSLA",
            ChartRangeEnum.ONE_MONTH
        )
        
        # Should only return TSLA moments
        self.assertEqual(len(moments), 1)
        self.assertEqual(moments[0].symbol, "TSLA")
        self.assertEqual(moments[0].id, self.other_moment.id)
    
    def test_resolve_stock_moments_ordering(self):
        """Test that moments are ordered by timestamp"""
        moments = self.query.resolve_stock_moments(
            None,
            self.symbol,
            ChartRangeEnum.SIX_MONTHS
        )
        
        # Should be ordered by timestamp (ascending)
        timestamps = [m.timestamp for m in moments]
        self.assertEqual(timestamps, sorted(timestamps))
    
    def test_resolve_stock_moments_empty_result(self):
        """Test resolving moments for symbol with no moments"""
        moments = self.query.resolve_stock_moments(
            None,
            "NONEXISTENT",
            ChartRangeEnum.ONE_MONTH
        )
        
        self.assertEqual(len(moments), 0)
        self.assertEqual(list(moments), [])
    
    def test_resolve_stock_moments_case_insensitive(self):
        """Test that symbol matching is case-insensitive (via upper())"""
        moments = self.query.resolve_stock_moments(
            None,
            "aapl",  # lowercase
            ChartRangeEnum.ONE_MONTH
        )
        
        # Should still find AAPL moments
        self.assertEqual(len(moments), 1)
        self.assertEqual(moments[0].symbol, self.symbol)
    
    def test_resolve_stock_moments_error_handling(self):
        """Test error handling in resolver"""
        # This should not raise an exception
        moments = self.query.resolve_stock_moments(
            None,
            None,  # Invalid input
            ChartRangeEnum.ONE_MONTH
        )
        
        # Should return empty list on error
        self.assertEqual(len(moments), 0)

