"""
Unit tests for StockMoment worker
"""
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from core.stock_moment_worker import (
    PriceContext,
    Event,
    RawMomentJob,
    build_events_block,
    normalize_category,
    create_stock_moment_from_job,
)
from core.models import StockMoment, MomentCategory


class StockMomentWorkerTestCase(TestCase):
    """Tests for StockMoment worker functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.now = datetime.now(timezone.utc)
        self.symbol = "AAPL"
    
    def test_price_context_creation(self):
        """Test PriceContext dataclass"""
        context = PriceContext(
            start_price=150.0,
            end_price=155.0,
            pct_change=3.33,
            volume_vs_average="2.3x average"
        )
        
        self.assertEqual(context.start_price, 150.0)
        self.assertEqual(context.end_price, 155.0)
        self.assertEqual(context.pct_change, 3.33)
        self.assertEqual(context.volume_vs_average, "2.3x average")
    
    def test_event_creation(self):
        """Test Event dataclass"""
        event = Event(
            type="EARNINGS",
            time=self.now,
            headline="Strong Earnings",
            summary="Beat estimates",
            url="https://example.com/news"
        )
        
        self.assertEqual(event.type, "EARNINGS")
        self.assertEqual(event.time, self.now)
        self.assertEqual(event.headline, "Strong Earnings")
        self.assertEqual(event.summary, "Beat estimates")
        self.assertEqual(event.url, "https://example.com/news")
    
    def test_raw_moment_job_creation(self):
        """Test RawMomentJob dataclass"""
        price_context = PriceContext(
            start_price=150.0,
            end_price=155.0,
            pct_change=3.33,
            volume_vs_average="2.3x average"
        )
        events = [
            Event(
                type="EARNINGS",
                time=self.now,
                headline="Earnings",
                summary="Beat",
                url="https://example.com"
            )
        ]
        
        job = RawMomentJob(
            symbol=self.symbol,
            timestamp=self.now,
            price_context=price_context,
            events=events
        )
        
        self.assertEqual(job.symbol, self.symbol)
        self.assertEqual(job.timestamp, self.now)
        self.assertEqual(job.price_context, price_context)
        self.assertEqual(len(job.events), 1)
    
    def test_build_events_block(self):
        """Test build_events_block function"""
        events = [
            Event(
                type="EARNINGS",
                time=self.now,
                headline="Earnings Beat",
                summary="Beat estimates by 5%",
                url="https://example.com/1"
            ),
            Event(
                type="NEWS",
                time=self.now,
                headline="Product Launch",
                summary="New iPhone announced",
                url="https://example.com/2"
            )
        ]
        
        block = build_events_block(events)
        
        self.assertIn("EARNINGS", block)
        self.assertIn("Earnings Beat", block)
        self.assertIn("NEWS", block)
        self.assertIn("Product Launch", block)
        self.assertIn("https://example.com/1", block)
        self.assertIn("https://example.com/2", block)
    
    def test_build_events_block_empty(self):
        """Test build_events_block with empty events"""
        block = build_events_block([])
        self.assertIn("no specific events", block.lower())
    
    def test_normalize_category(self):
        """Test normalize_category function"""
        self.assertEqual(normalize_category("EARNINGS"), MomentCategory.EARNINGS)
        self.assertEqual(normalize_category("earnings"), MomentCategory.EARNINGS)
        self.assertEqual(normalize_category("Earnings"), MomentCategory.EARNINGS)
        self.assertEqual(normalize_category("NEWS"), MomentCategory.NEWS)
        self.assertEqual(normalize_category("INSIDER"), MomentCategory.INSIDER)
        self.assertEqual(normalize_category("MACRO"), MomentCategory.MACRO)
        self.assertEqual(normalize_category("SENTIMENT"), MomentCategory.SENTIMENT)
        self.assertEqual(normalize_category("UNKNOWN"), MomentCategory.OTHER)
        self.assertEqual(normalize_category(""), MomentCategory.OTHER)
    
    @patch('core.stock_moment_worker.call_llm_for_moment')
    def test_create_stock_moment_from_job_success(self, mock_llm):
        """Test creating StockMoment from job with successful LLM call"""
        # Mock LLM response
        mock_llm.return_value = {
            "title": "Strong Earnings Beat",
            "quick_summary": "Apple beat estimates by 5%",
            "deep_summary": "Apple Inc. reported strong earnings that exceeded analyst expectations...",
            "category": "EARNINGS",
            "importance_score": 0.85,
            "source_links": ["https://example.com/news"]
        }
        
        price_context = PriceContext(
            start_price=150.0,
            end_price=155.0,
            pct_change=3.33,
            volume_vs_average="2.3x average"
        )
        events = [
            Event(
                type="EARNINGS",
                time=self.now,
                headline="Earnings Beat",
                summary="Beat estimates",
                url="https://example.com/news"
            )
        ]
        
        job = RawMomentJob(
            symbol=self.symbol,
            timestamp=self.now,
            price_context=price_context,
            events=events
        )
        
        moment = create_stock_moment_from_job(job)
        
        self.assertIsNotNone(moment)
        self.assertIsInstance(moment, StockMoment)
        self.assertEqual(moment.symbol, self.symbol)
        self.assertEqual(moment.title, "Strong Earnings Beat")
        self.assertEqual(moment.category, MomentCategory.EARNINGS)
        self.assertEqual(moment.importance_score, 0.85)
        self.assertEqual(len(moment.source_links), 1)
        
        # Verify LLM was called
        mock_llm.assert_called_once()
    
    @patch('core.stock_moment_worker.call_llm_for_moment')
    def test_create_stock_moment_from_job_low_importance(self, mock_llm):
        """Test that low importance moments are skipped"""
        # Mock LLM response with low importance
        mock_llm.return_value = {
            "title": "Minor News",
            "quick_summary": "Minor update",
            "deep_summary": "Minor detail",
            "category": "NEWS",
            "importance_score": 0.2,  # Below threshold
            "source_links": []
        }
        
        price_context = PriceContext(
            start_price=150.0,
            end_price=150.5,
            pct_change=0.33,
            volume_vs_average="1.0x average"
        )
        events = [
            Event(
                type="NEWS",
                time=self.now,
                headline="Minor Update",
                summary="Small change",
                url="https://example.com"
            )
        ]
        
        job = RawMomentJob(
            symbol=self.symbol,
            timestamp=self.now,
            price_context=price_context,
            events=events
        )
        
        moment = create_stock_moment_from_job(job)
        
        # Should return None for low importance
        self.assertIsNone(moment)
    
    @patch('core.stock_moment_worker.call_llm_for_moment')
    def test_create_stock_moment_from_job_llm_error(self, mock_llm):
        """Test error handling when LLM call fails"""
        # Mock LLM to raise exception
        mock_llm.side_effect = Exception("LLM API error")
        
        price_context = PriceContext(
            start_price=150.0,
            end_price=155.0,
            pct_change=3.33,
            volume_vs_average="2.3x average"
        )
        events = [
            Event(
                type="EARNINGS",
                time=self.now,
                headline="Earnings",
                summary="Beat",
                url="https://example.com"
            )
        ]
        
        job = RawMomentJob(
            symbol=self.symbol,
            timestamp=self.now,
            price_context=price_context,
            events=events
        )
        
        # Should handle error gracefully
        moment = create_stock_moment_from_job(job)
        self.assertIsNone(moment)
    
    @patch('core.stock_moment_worker.call_llm_for_moment')
    def test_create_stock_moment_from_job_invalid_response(self, mock_llm):
        """Test handling of invalid LLM response"""
        # Mock LLM to return invalid response
        mock_llm.return_value = {
            "title": "Test",
            # Missing required fields
        }
        
        price_context = PriceContext(
            start_price=150.0,
            end_price=155.0,
            pct_change=3.33,
            volume_vs_average="2.3x average"
        )
        events = [
            Event(
                type="EARNINGS",
                time=self.now,
                headline="Earnings",
                summary="Beat",
                url="https://example.com"
            )
        ]
        
        job = RawMomentJob(
            symbol=self.symbol,
            timestamp=self.now,
            price_context=price_context,
            events=events
        )
        
        # Should handle invalid response gracefully
        moment = create_stock_moment_from_job(job)
        # May return None or handle gracefully
        # This depends on implementation details

