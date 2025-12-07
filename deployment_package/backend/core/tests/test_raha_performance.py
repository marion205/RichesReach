"""
RAHA Performance Tests
End-to-end tests to validate all performance optimizations work correctly
"""
import pytest
import time
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Count
from unittest.mock import patch, MagicMock

from ..raha_models import Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun
from ..raha_queries import RAHAQueries
from ..signal_performance_models import SignalPerformance, DayTradingSignal

User = get_user_model()


class RAHAPerformanceTests(TestCase):
    """Test suite for RAHA performance optimizations"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        
        # Create test strategy
        self.strategy = Strategy.objects.create(
            slug='test-strategy',
            name='Test Strategy',
            category='MOMENTUM',
            market_type='STOCKS',
            enabled=True
        )
        
        self.strategy_version = StrategyVersion.objects.create(
            strategy=self.strategy,
            version=1,
            logic_ref='TEST_v1',
            is_default=True
        )
        
        # Create user strategy settings
        self.user_settings = UserStrategySettings.objects.create(
            user=self.user,
            strategy_version=self.strategy_version,
            enabled=True
        )
        
        # Create test signals
        self.signals = []
        for i in range(20):
            signal = RAHASignal.objects.create(
                user=self.user,
                strategy_version=self.strategy_version,
                symbol='AAPL',
                signal_type='ENTRY_LONG',
                price=150.0 + i,
                confidence_score=0.7 + (i * 0.01),
                stop_loss=145.0,
                take_profit=160.0
            )
            self.signals.append(signal)
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
    
    def test_n1_query_fix_strategies(self):
        """Test that resolve_strategies uses select_related (no N+1 queries)"""
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = self.user
        
        # Count database queries
        with self.assertNumQueries(1):  # Should be 1 query with select_related
            result = queries.resolve_strategies(info, include_custom=False)
            # Access related objects to trigger N+1 if not using select_related
            for strategy in result:
                _ = strategy.created_by  # This would cause N+1 without select_related
    
    def test_n1_query_fix_raha_signals(self):
        """Test that resolve_raha_signals uses select_related (no N+1 queries)"""
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = self.user
        
        # Count database queries
        with self.assertNumQueries(1):  # Should be 1 query with select_related
            result = queries.resolve_raha_signals(info, symbol='AAPL', limit=10)
            # Access related objects to trigger N+1 if not using select_related
            for signal in result:
                _ = signal.strategy_version.strategy.name  # This would cause N+1 without select_related
    
    def test_n1_query_fix_user_backtests(self):
        """Test that resolve_user_backtests uses select_related (no N+1 queries)"""
        # Create test backtest
        backtest = RAHABacktestRun.objects.create(
            user=self.user,
            strategy_version=self.strategy_version,
            symbol='AAPL',
            start_date='2024-01-01',
            end_date='2024-01-31',
            status='COMPLETED'
        )
        
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = self.user
        
        # Count database queries
        with self.assertNumQueries(1):  # Should be 1 query with select_related
            result = queries.resolve_user_backtests(info, limit=10)
            # Access related objects to trigger N+1 if not using select_related
            for bt in result:
                _ = bt.strategy_version.strategy.name  # This would cause N+1 without select_related
    
    def test_query_caching_strategies(self):
        """Test that resolve_strategies caches results"""
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = self.user
        
        # First call - should hit database
        with self.assertNumQueries(1):
            result1 = queries.resolve_strategies(info)
        
        # Second call - should use cache (0 queries)
        with self.assertNumQueries(0):
            result2 = queries.resolve_strategies(info)
        
        # Results should be the same
        self.assertEqual(len(result1), len(result2))
    
    def test_query_caching_raha_signals(self):
        """Test that resolve_raha_signals caches first page"""
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = self.user
        
        # First call - should hit database
        with self.assertNumQueries(1):
            result1 = queries.resolve_raha_signals(info, symbol='AAPL', limit=10, offset=0)
        
        # Second call (first page) - should use cache (0 queries)
        with self.assertNumQueries(0):
            result2 = queries.resolve_raha_signals(info, symbol='AAPL', limit=10, offset=0)
        
        # Results should be the same
        self.assertEqual(len(result1), len(result2))
        
        # Third call (second page) - should hit database (not cached)
        with self.assertNumQueries(1):
            result3 = queries.resolve_raha_signals(info, symbol='AAPL', limit=10, offset=10)
    
    def test_query_caching_metrics(self):
        """Test that resolve_raha_metrics caches results"""
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = self.user
        
        # First call - should hit database
        result1 = queries.resolve_raha_metrics(info, str(self.strategy_version.id))
        self.assertIsNotNone(result1)
        
        # Second call - should use cache
        result2 = queries.resolve_raha_metrics(info, str(self.strategy_version.id))
        self.assertIsNotNone(result2)
        
        # Results should be the same
        self.assertEqual(result1.total_signals, result2.total_signals)
    
    def test_database_indexes_exist(self):
        """Test that database indexes were created"""
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check for RAHASignal indexes
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'raha_signals' 
                AND indexname LIKE 'raha_signal%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            # Verify expected indexes exist
            expected_indexes = [
                'raha_signal_user_symbol_time_idx',
                'raha_signal_user_strategy_time_idx',
                'raha_signal_symbol_timeframe_time_idx'
            ]
            
            for expected in expected_indexes:
                self.assertIn(expected, indexes, f"Index {expected} not found")
    
    def test_query_performance_improvement(self):
        """Test that queries are faster with optimizations"""
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = self.user
        
        # Measure query time
        start_time = time.time()
        result = queries.resolve_raha_signals(
            info, 
            symbol='AAPL', 
            limit=20
        )
        query_time = time.time() - start_time
        
        # Query should complete in reasonable time (< 100ms for 20 signals)
        self.assertLess(query_time, 0.1, f"Query took {query_time:.3f}s, expected < 0.1s")
        self.assertEqual(len(result), 20)
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated correctly"""
        from ..raha_query_cache import get_cache_key
        
        key1 = get_cache_key('test_query', 1, param1='value1', param2='value2')
        key2 = get_cache_key('test_query', 1, param1='value1', param2='value2')
        key3 = get_cache_key('test_query', 1, param1='value1', param2='value3')
        
        # Same parameters should generate same key
        self.assertEqual(key1, key2)
        
        # Different parameters should generate different key
        self.assertNotEqual(key1, key3)
    
    def test_cache_timeout_configuration(self):
        """Test that cache timeouts are configured correctly"""
        from ..raha_query_cache import CACHE_TIMEOUTS
        
        # Verify all expected timeouts are defined
        expected_timeouts = [
            'strategies', 'strategy', 'user_strategy_settings',
            'raha_signals', 'backtest_run', 'user_backtests',
            'raha_metrics', 'strategy_dashboard', 'ml_models',
            'strategy_blends', 'notification_preferences', 'auto_trading_settings'
        ]
        
        for timeout_key in expected_timeouts:
            self.assertIn(timeout_key, CACHE_TIMEOUTS)
            self.assertIsInstance(CACHE_TIMEOUTS[timeout_key], int)
            self.assertGreater(CACHE_TIMEOUTS[timeout_key], 0)
    
    def test_pagination_performance(self):
        """Test that pagination works efficiently"""
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = self.user
        
        # Test first page
        with self.assertNumQueries(1):
            page1 = queries.resolve_raha_signals(info, symbol='AAPL', limit=10, offset=0)
        
        # Test second page (should be separate query, not cached)
        with self.assertNumQueries(1):
            page2 = queries.resolve_raha_signals(info, symbol='AAPL', limit=10, offset=10)
        
        # Both pages should have results (we created 20 signals)
        self.assertEqual(len(page1), 10)
        self.assertEqual(len(page2), 10)
        
        # Results should be different (different signals)
        if len(page1) > 0 and len(page2) > 0:
            self.assertNotEqual(page1[0].id, page2[0].id)
    
    def test_select_related_in_dashboard_service(self):
        """Test that dashboard service uses select_related"""
        from ..raha_dashboard_service import RAHADashboardService
        
        service = RAHADashboardService()
        
        # Count queries when getting dashboard data
        # Expected queries:
        # 1. User settings with select_related
        # 2. Signals count
        # 3. Day trading signal IDs
        # 4. AVG confidence (from metrics fallback)
        # 5. Backtest with select_related
        # Total: 5 queries (optimized - would be more without select_related)
        initial_queries = len(connection.queries)
        dashboard_data = service.get_strategy_dashboard_data(self.user)
        final_queries = len(connection.queries)
        query_count = final_queries - initial_queries
        
        # Should be 5 queries (optimized) - would be 10+ without select_related
        self.assertLessEqual(query_count, 6, f"Expected <= 6 queries, got {query_count}")
        
        # Access related objects to verify select_related works (no N+1)
        for item in dashboard_data:
            # This would cause N+1 without select_related, but we already loaded it
            _ = item.get('strategy_name')


@pytest.mark.django_db
class RAHAPerformanceBenchmarkTests:
    """Benchmark tests to measure performance improvements"""
    
    def test_benchmark_raha_signals_query(self, django_user_model):
        """Benchmark RAHA signals query performance"""
        user = django_user_model.objects.create_user(
            email='benchmark@example.com',
            password='testpass123'
        )
        
        # Create many signals
        strategy = Strategy.objects.create(
            slug='benchmark-strategy',
            name='Benchmark Strategy',
            category='MOMENTUM',
            market_type='STOCKS',
            enabled=True
        )
        
        strategy_version = StrategyVersion.objects.create(
            strategy=strategy,
            version=1,
            logic_ref='BENCHMARK_v1',
            is_default=True
        )
        
        # Create 100 signals
        for i in range(100):
            RAHASignal.objects.create(
                user=user,
                strategy_version=strategy_version,
                symbol='AAPL',
                signal_type='ENTRY_LONG',
                price=150.0 + i,
                confidence_score=0.7
            )
        
        queries = RAHAQueries()
        info = MagicMock()
        info.context.user = user
        
        # Measure query time
        start_time = time.time()
        result = queries.resolve_raha_signals(info, limit=20)
        query_time = time.time() - start_time
        
        # Should be fast even with 100 signals
        assert query_time < 0.1, f"Query took {query_time:.3f}s, expected < 0.1s"
        assert len(result) == 20

