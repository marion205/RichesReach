"""
Unit tests for StockMoment model
"""
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import StockMoment, MomentCategory


class StockMomentModelTestCase(TestCase):
    """Tests for StockMoment model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.now = timezone.now()
        self.symbol = "AAPL"
    
    def test_create_stock_moment(self):
        """Test creating a stock moment"""
        moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            importance_score=0.85,
            category=MomentCategory.EARNINGS,
            title="Strong Q4 Earnings Beat",
            quick_summary="Apple reported earnings that beat estimates by 5%.",
            deep_summary="Apple Inc. reported fourth-quarter earnings that exceeded analyst expectations by 5%, driven by strong iPhone sales and services revenue growth. The company's revenue reached $89.5 billion, up 8% year-over-year.",
            source_links=["https://example.com/news1", "https://example.com/filing"],
            impact_1d=3.2,
            impact_7d=5.8,
        )
        
        self.assertEqual(moment.symbol, self.symbol)
        self.assertEqual(moment.importance_score, 0.85)
        self.assertEqual(moment.category, MomentCategory.EARNINGS)
        self.assertEqual(moment.title, "Strong Q4 Earnings Beat")
        self.assertIsNotNone(moment.id)
        self.assertIsNotNone(moment.created_at)
        self.assertIsNotNone(moment.updated_at)
        self.assertEqual(len(moment.source_links), 2)
        self.assertEqual(moment.impact_1d, 3.2)
        self.assertEqual(moment.impact_7d, 5.8)
    
    def test_stock_moment_str(self):
        """Test stock moment string representation"""
        moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            category=MomentCategory.NEWS,
            title="Product Launch",
            quick_summary="New product announced",
            deep_summary="Detailed description",
        )
        
        expected_str = f"{self.symbol} @ {self.now} ({MomentCategory.NEWS})"
        self.assertEqual(str(moment), expected_str)
    
    def test_stock_moment_defaults(self):
        """Test stock moment default values"""
        moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            title="Test Moment",
            quick_summary="Quick",
            deep_summary="Deep",
        )
        
        self.assertEqual(moment.importance_score, 0.0)
        self.assertEqual(moment.category, MomentCategory.OTHER)
        self.assertEqual(moment.source_links, [])
        self.assertIsNone(moment.impact_1d)
        self.assertIsNone(moment.impact_7d)
    
    def test_stock_moment_ordering(self):
        """Test stock moment ordering by symbol and timestamp"""
        # Create moments in reverse chronological order
        moment1 = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now - timedelta(days=2),
            title="Older Moment",
            quick_summary="Old",
            deep_summary="Old detail",
        )
        moment2 = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            title="Newer Moment",
            quick_summary="New",
            deep_summary="New detail",
        )
        
        moments = list(StockMoment.objects.filter(symbol=self.symbol))
        # Should be ordered by symbol, then -timestamp (newest first)
        self.assertEqual(moments[0].timestamp, moment2.timestamp)
        self.assertEqual(moments[1].timestamp, moment1.timestamp)
    
    def test_stock_moment_category_choices(self):
        """Test all category choices are valid"""
        categories = [
            MomentCategory.EARNINGS,
            MomentCategory.NEWS,
            MomentCategory.INSIDER,
            MomentCategory.MACRO,
            MomentCategory.SENTIMENT,
            MomentCategory.OTHER,
        ]
        
        for category in categories:
            moment = StockMoment.objects.create(
                symbol=self.symbol,
                timestamp=self.now,
                category=category,
                title=f"Test {category}",
                quick_summary="Test",
                deep_summary="Test detail",
            )
            self.assertEqual(moment.category, category)
    
    def test_stock_moment_filtering_by_symbol(self):
        """Test filtering moments by symbol"""
        StockMoment.objects.create(
            symbol="AAPL",
            timestamp=self.now,
            title="AAPL Moment",
            quick_summary="Apple",
            deep_summary="Apple detail",
        )
        StockMoment.objects.create(
            symbol="TSLA",
            timestamp=self.now,
            title="TSLA Moment",
            quick_summary="Tesla",
            deep_summary="Tesla detail",
        )
        
        aapl_moments = StockMoment.objects.filter(symbol="AAPL")
        self.assertEqual(aapl_moments.count(), 1)
        self.assertEqual(aapl_moments.first().symbol, "AAPL")
        
        tsla_moments = StockMoment.objects.filter(symbol="TSLA")
        self.assertEqual(tsla_moments.count(), 1)
        self.assertEqual(tsla_moments.first().symbol, "TSLA")
    
    def test_stock_moment_filtering_by_timestamp(self):
        """Test filtering moments by timestamp range"""
        old_moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now - timedelta(days=60),
            title="Old Moment",
            quick_summary="Old",
            deep_summary="Old detail",
        )
        recent_moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now - timedelta(days=10),
            title="Recent Moment",
            quick_summary="Recent",
            deep_summary="Recent detail",
        )
        
        # Filter for last 30 days
        start_date = self.now - timedelta(days=30)
        recent_moments = StockMoment.objects.filter(
            symbol=self.symbol,
            timestamp__gte=start_date
        )
        
        self.assertEqual(recent_moments.count(), 1)
        self.assertEqual(recent_moments.first().id, recent_moment.id)
    
    def test_stock_moment_source_links_json(self):
        """Test source_links JSON field"""
        moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            title="Test",
            quick_summary="Test",
            deep_summary="Test",
            source_links=["https://example.com/1", "https://example.com/2"],
        )
        
        self.assertEqual(len(moment.source_links), 2)
        self.assertIn("https://example.com/1", moment.source_links)
        self.assertIn("https://example.com/2", moment.source_links)
        
        # Update source links
        moment.source_links.append("https://example.com/3")
        moment.save()
        moment.refresh_from_db()
        self.assertEqual(len(moment.source_links), 3)
    
    def test_stock_moment_importance_score_range(self):
        """Test importance_score can be any float value"""
        # Low importance
        low_moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            importance_score=0.1,
            title="Low",
            quick_summary="Low",
            deep_summary="Low",
        )
        
        # High importance
        high_moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            importance_score=0.99,
            title="High",
            quick_summary="High",
            deep_summary="High",
        )
        
        self.assertEqual(low_moment.importance_score, 0.1)
        self.assertEqual(high_moment.importance_score, 0.99)
    
    def test_stock_moment_impact_fields(self):
        """Test impact_1d and impact_7d fields"""
        moment = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            title="Test",
            quick_summary="Test",
            deep_summary="Test",
            impact_1d=-2.5,  # Negative impact
            impact_7d=4.3,   # Positive impact
        )
        
        self.assertEqual(moment.impact_1d, -2.5)
        self.assertEqual(moment.impact_7d, 4.3)
        
        # Can be None
        moment_no_impact = StockMoment.objects.create(
            symbol=self.symbol,
            timestamp=self.now,
            title="No Impact",
            quick_summary="No",
            deep_summary="No",
        )
        self.assertIsNone(moment_no_impact.impact_1d)
        self.assertIsNone(moment_no_impact.impact_7d)

