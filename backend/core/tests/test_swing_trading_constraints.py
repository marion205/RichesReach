"""
Test suite for swing trading database constraints and performance
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError, connection
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, date
import uuid

from core.models import (
    User, OHLCV, Signal, SignalLike, SignalComment, TraderScore,
    BacktestStrategy, BacktestResult, SwingWatchlist
)


class SwingTradingConstraintsTest(TestCase):
    """Test database constraints for swing trading models"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.test_timestamp = datetime.now()
        self.test_date = date.today()
    
    def test_ohlcv_non_negative_prices_and_volume(self):
        """Test OHLCV constraint: all prices and volume must be non-negative"""
        
        # Valid data should work
        valid_ohlcv = OHLCV.objects.create(
            symbol='AAPL',
            timestamp=self.test_timestamp,
            timeframe='1d',
            open_price=Decimal('150.00'),
            high_price=Decimal('155.00'),
            low_price=Decimal('148.00'),
            close_price=Decimal('152.00'),
            volume=1000000
        )
        self.assertIsNotNone(valid_ohlcv.id)
        
        # Test negative prices - should fail
        with self.assertRaises(IntegrityError):
            OHLCV.objects.create(
                symbol='AAPL',
                timestamp=self.test_timestamp,
                timeframe='1d',
                open_price=Decimal('-1.00'),  # Negative price
                high_price=Decimal('155.00'),
                low_price=Decimal('148.00'),
                close_price=Decimal('152.00'),
                volume=1000000
            )
        
        # Test negative volume - should fail
        with self.assertRaises(IntegrityError):
            OHLCV.objects.create(
                symbol='AAPL',
                timestamp=self.test_timestamp,
                timeframe='1d',
                open_price=Decimal('150.00'),
                high_price=Decimal('155.00'),
                low_price=Decimal('148.00'),
                close_price=Decimal('152.00'),
                volume=-1000  # Negative volume
            )
    
    def test_ohlcv_high_ge_low(self):
        """Test OHLCV constraint: high price must be >= low price"""
        
        # Valid data should work
        valid_ohlcv = OHLCV.objects.create(
            symbol='AAPL',
            timestamp=self.test_timestamp,
            timeframe='1d',
            open_price=Decimal('150.00'),
            high_price=Decimal('155.00'),
            low_price=Decimal('148.00'),
            close_price=Decimal('152.00'),
            volume=1000000
        )
        self.assertIsNotNone(valid_ohlcv.id)
        
        # Test high < low - should fail
        with self.assertRaises(IntegrityError):
            OHLCV.objects.create(
                symbol='AAPL',
                timestamp=self.test_timestamp,
                timeframe='1d',
                open_price=Decimal('150.00'),
                high_price=Decimal('145.00'),  # High < Low
                low_price=Decimal('148.00'),
                close_price=Decimal('152.00'),
                volume=1000000
            )
    
    def test_signal_prices_non_negative(self):
        """Test Signal constraint: all prices must be non-negative"""
        
        # Valid data should work
        valid_signal = Signal.objects.create(
            symbol='AAPL',
            timeframe='1d',
            triggered_at=self.test_timestamp,
            signal_type='rsi_rebound_long',
            entry_price=Decimal('150.00'),
            stop_price=Decimal('145.00'),
            target_price=Decimal('160.00'),
            ml_score=Decimal('0.75'),
            features={'rsi': 25.5, 'volume_surge': 1.8},
            thesis='RSI oversold with volume confirmation'
        )
        self.assertIsNotNone(valid_signal.id)
        
        # Test negative entry price - should fail
        with self.assertRaises(IntegrityError):
            Signal.objects.create(
                symbol='AAPL',
                timeframe='1d',
                triggered_at=self.test_timestamp,
                signal_type='rsi_rebound_long',
                entry_price=Decimal('-150.00'),  # Negative entry price
                stop_price=Decimal('145.00'),
                target_price=Decimal('160.00'),
                ml_score=Decimal('0.75'),
                features={'rsi': 25.5, 'volume_surge': 1.8},
                thesis='RSI oversold with volume confirmation'
            )
        
        # Test negative stop price - should fail
        with self.assertRaises(IntegrityError):
            Signal.objects.create(
                symbol='AAPL',
                timeframe='1d',
                triggered_at=self.test_timestamp,
                signal_type='rsi_rebound_long',
                entry_price=Decimal('150.00'),
                stop_price=Decimal('-145.00'),  # Negative stop price
                target_price=Decimal('160.00'),
                ml_score=Decimal('0.75'),
                features={'rsi': 25.5, 'volume_surge': 1.8},
                thesis='RSI oversold with volume confirmation'
            )
    
    def test_backtest_end_ge_start(self):
        """Test BacktestResult constraint: end_date must be >= start_date"""
        
        strategy = BacktestStrategy.objects.create(
            user=self.user,
            name='Test Strategy',
            strategy_type='ema_crossover',
            parameters={'ema_fast': 12, 'ema_slow': 26}
        )
        
        # Valid data should work
        valid_result = BacktestResult.objects.create(
            strategy=strategy,
            symbol='AAPL',
            timeframe='1d',
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            initial_capital=Decimal('10000.00'),
            final_capital=Decimal('12000.00'),
            total_return=Decimal('0.20'),
            annualized_return=Decimal('0.20'),
            max_drawdown=Decimal('0.05'),
            sharpe_ratio=Decimal('1.5'),
            win_rate=Decimal('0.60'),
            profit_factor=Decimal('1.8'),
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            avg_win=Decimal('0.02'),
            avg_loss=Decimal('-0.01'),
            equity_curve=[10000, 10200, 10150, 12000],
            trade_log=[]
        )
        self.assertIsNotNone(valid_result.id)
        
        # Test end_date < start_date - should fail
        with self.assertRaises(IntegrityError):
            BacktestResult.objects.create(
                strategy=strategy,
                symbol='AAPL',
                timeframe='1d',
                start_date=date(2023, 12, 31),
                end_date=date(2023, 1, 1),  # End < Start
                initial_capital=Decimal('10000.00'),
                final_capital=Decimal('12000.00'),
                total_return=Decimal('0.20'),
                annualized_return=Decimal('0.20'),
                max_drawdown=Decimal('0.05'),
                sharpe_ratio=Decimal('1.5'),
                win_rate=Decimal('0.60'),
                profit_factor=Decimal('1.8'),
                total_trades=100,
                winning_trades=60,
                losing_trades=40,
                avg_win=Decimal('0.02'),
                avg_loss=Decimal('-0.01'),
                equity_curve=[10000, 10200, 10150, 12000],
                trade_log=[]
            )
    
    def test_backtest_capital_non_negative(self):
        """Test BacktestResult constraint: capital values must be non-negative"""
        
        strategy = BacktestStrategy.objects.create(
            user=self.user,
            name='Test Strategy',
            strategy_type='ema_crossover',
            parameters={'ema_fast': 12, 'ema_slow': 26}
        )
        
        # Test negative initial capital - should fail
        with self.assertRaises(IntegrityError):
            BacktestResult.objects.create(
                strategy=strategy,
                symbol='AAPL',
                timeframe='1d',
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31),
                initial_capital=Decimal('-10000.00'),  # Negative capital
                final_capital=Decimal('12000.00'),
                total_return=Decimal('0.20'),
                annualized_return=Decimal('0.20'),
                max_drawdown=Decimal('0.05'),
                sharpe_ratio=Decimal('1.5'),
                win_rate=Decimal('0.60'),
                profit_factor=Decimal('1.8'),
                total_trades=100,
                winning_trades=60,
                losing_trades=40,
                avg_win=Decimal('0.02'),
                avg_loss=Decimal('-0.01'),
                equity_curve=[10000, 10200, 10150, 12000],
                trade_log=[]
            )
    
    def test_backtest_win_rate_bounds(self):
        """Test BacktestResult constraint: win_rate must be between 0 and 1"""
        
        strategy = BacktestStrategy.objects.create(
            user=self.user,
            name='Test Strategy',
            strategy_type='ema_crossover',
            parameters={'ema_fast': 12, 'ema_slow': 26}
        )
        
        # Test win_rate > 1 - should fail
        with self.assertRaises(IntegrityError):
            BacktestResult.objects.create(
                strategy=strategy,
                symbol='AAPL',
                timeframe='1d',
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31),
                initial_capital=Decimal('10000.00'),
                final_capital=Decimal('12000.00'),
                total_return=Decimal('0.20'),
                annualized_return=Decimal('0.20'),
                max_drawdown=Decimal('0.05'),
                sharpe_ratio=Decimal('1.5'),
                win_rate=Decimal('1.5'),  # Win rate > 1
                profit_factor=Decimal('1.8'),
                total_trades=100,
                winning_trades=60,
                losing_trades=40,
                avg_win=Decimal('0.02'),
                avg_loss=Decimal('-0.01'),
                equity_curve=[10000, 10200, 10150, 12000],
                trade_log=[]
            )
        
        # Test win_rate < 0 - should fail
        with self.assertRaises(IntegrityError):
            BacktestResult.objects.create(
                strategy=strategy,
                symbol='AAPL',
                timeframe='1d',
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31),
                initial_capital=Decimal('10000.00'),
                final_capital=Decimal('12000.00'),
                total_return=Decimal('0.20'),
                annualized_return=Decimal('0.20'),
                max_drawdown=Decimal('0.05'),
                sharpe_ratio=Decimal('1.5'),
                win_rate=Decimal('-0.1'),  # Win rate < 0
                profit_factor=Decimal('1.8'),
                total_trades=100,
                winning_trades=60,
                losing_trades=40,
                avg_win=Decimal('0.02'),
                avg_loss=Decimal('-0.01'),
                equity_curve=[10000, 10200, 10150, 12000],
                trade_log=[]
            )


class SwingTradingPerformanceTest(TestCase):
    """Test performance optimizations for swing trading queries"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test signals
        self.signals = []
        for i in range(100):
            signal = Signal.objects.create(
                symbol='AAPL',
                timeframe='1d',
                triggered_at=datetime.now(),
                signal_type='rsi_rebound_long',
                entry_price=Decimal('150.00'),
                stop_price=Decimal('145.00'),
                target_price=Decimal('160.00'),
                ml_score=Decimal('0.75'),
                features={'rsi': 25.5, 'volume_surge': 1.8, 'test_key': f'value_{i}'},
                thesis=f'Test signal {i}',
                is_active=i % 2 == 0  # Half active, half inactive
            )
            self.signals.append(signal)
    
    def test_active_signals_query_performance(self):
        """Test that active signals query uses partial index efficiently"""
        
        with connection.cursor() as cursor:
            # Check if we're on Postgres and have the partial index
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'core_signal' 
                AND indexname = 'core_signal_active_time_idx'
            """)
            
            if cursor.fetchone():
                # Test query plan for active signals
                cursor.execute("""
                    EXPLAIN ANALYZE
                    SELECT id FROM core_signal
                    WHERE is_active = TRUE
                    ORDER BY triggered_at DESC
                    LIMIT 50
                """)
                
                result = cursor.fetchall()
                plan_text = ' '.join([row[0] for row in result])
                
                # Should use the partial index
                self.assertIn('core_signal_active_time_idx', plan_text)
                self.assertIn('Index Scan', plan_text)
    
    def test_json_features_query_performance(self):
        """Test that JSON features query uses GIN index efficiently"""
        
        with connection.cursor() as cursor:
            # Check if we're on Postgres and have the GIN index
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'core_signal' 
                AND indexname = 'core_signal_features_gin_idx'
            """)
            
            if cursor.fetchone():
                # Test query plan for JSON features lookup
                cursor.execute("""
                    EXPLAIN ANALYZE
                    SELECT id FROM core_signal
                    WHERE features @> '{"test_key": "value_50"}'
                """)
                
                result = cursor.fetchall()
                plan_text = ' '.join([row[0] for row in result])
                
                # Should use the GIN index
                self.assertIn('core_signal_features_gin_idx', plan_text)
                self.assertIn('Bitmap Index Scan', plan_text)
    
    def test_social_activity_query_performance(self):
        """Test that social activity queries use proper indexes"""
        
        # Create test likes and comments
        for i, signal in enumerate(self.signals[:10]):
            SignalLike.objects.create(user=self.user, signal=signal)
            SignalComment.objects.create(
                user=self.user,
                signal=signal,
                content=f'Test comment {i}'
            )
        
        with connection.cursor() as cursor:
            # Test query plan for user activity
            cursor.execute("""
                EXPLAIN ANALYZE
                SELECT id FROM core_signallike
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, [self.user.id])
            
            result = cursor.fetchall()
            plan_text = ' '.join([row[0] for row in result])
            
            # Should use the user activity index
            self.assertIn('core_signallike_user_created_at_idx', plan_text)


class SwingTradingIntegrationTest(TestCase):
    """Integration tests for swing trading functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_signal_lifecycle(self):
        """Test complete signal lifecycle from creation to validation"""
        
        # Create signal
        signal = Signal.objects.create(
            symbol='AAPL',
            timeframe='1d',
            triggered_at=datetime.now(),
            signal_type='rsi_rebound_long',
            entry_price=Decimal('150.00'),
            stop_price=Decimal('145.00'),
            target_price=Decimal('160.00'),
            ml_score=Decimal('0.75'),
            features={'rsi': 25.5, 'volume_surge': 1.8},
            thesis='RSI oversold with volume confirmation',
            created_by=self.user
        )
        
        self.assertTrue(signal.is_active)
        self.assertFalse(signal.is_validated)
        
        # Add social interactions
        like = SignalLike.objects.create(user=self.user, signal=signal)
        comment = SignalComment.objects.create(
            user=self.user,
            signal=signal,
            content='Great signal!'
        )
        
        self.assertEqual(signal.likes_count, 1)
        self.assertEqual(signal.comments_count, 1)
        
        # Validate signal
        signal.is_validated = True
        signal.validation_price = Decimal('155.00')
        signal.validation_timestamp = datetime.now()
        signal.is_active = False
        signal.save()
        
        self.assertFalse(signal.is_active)
        self.assertTrue(signal.is_validated)
        self.assertEqual(signal.validation_price, Decimal('155.00'))
    
    def test_trader_score_calculation(self):
        """Test trader score calculation and leaderboard functionality"""
        
        # Create trader score
        trader_score = TraderScore.objects.create(
            user=self.user,
            accuracy_score=Decimal('0.75'),
            consistency_score=Decimal('0.80'),
            discipline_score=Decimal('0.70'),
            total_signals=100,
            validated_signals=80,
            win_rate=Decimal('0.60')
        )
        
        # Overall score should be calculated
        expected_overall = (0.75 * 0.4) + (0.80 * 0.3) + (0.70 * 0.3)
        self.assertEqual(trader_score.overall_score, Decimal(str(expected_overall)))
        
        # Test leaderboard query
        leaderboard = TraderScore.objects.order_by('-overall_score')
        self.assertIn(trader_score, leaderboard)
    
    def test_backtest_strategy_workflow(self):
        """Test complete backtest strategy workflow"""
        
        # Create strategy
        strategy = BacktestStrategy.objects.create(
            user=self.user,
            name='Test EMA Strategy',
            description='Simple EMA crossover strategy',
            strategy_type='ema_crossover',
            parameters={'ema_fast': 12, 'ema_slow': 26},
            is_public=True
        )
        
        # Create backtest result
        result = BacktestResult.objects.create(
            strategy=strategy,
            symbol='AAPL',
            timeframe='1d',
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            initial_capital=Decimal('10000.00'),
            final_capital=Decimal('12000.00'),
            total_return=Decimal('0.20'),
            annualized_return=Decimal('0.20'),
            max_drawdown=Decimal('0.05'),
            sharpe_ratio=Decimal('1.5'),
            win_rate=Decimal('0.60'),
            profit_factor=Decimal('1.8'),
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            avg_win=Decimal('0.02'),
            avg_loss=Decimal('-0.01'),
            equity_curve=[10000, 10200, 10150, 12000],
            trade_log=[]
        )
        
        # Update strategy with performance metrics
        strategy.total_return = result.total_return
        strategy.win_rate = result.win_rate
        strategy.max_drawdown = result.max_drawdown
        strategy.sharpe_ratio = result.sharpe_ratio
        strategy.total_trades = result.total_trades
        strategy.save()
        
        self.assertEqual(strategy.total_return, Decimal('0.20'))
        self.assertEqual(strategy.win_rate, Decimal('0.60'))
        
        # Test public strategy query
        public_strategies = BacktestStrategy.objects.filter(is_public=True)
        self.assertIn(strategy, public_strategies)


if __name__ == '__main__':
    pytest.main([__file__])
