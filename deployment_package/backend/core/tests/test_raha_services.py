"""
Unit tests for RAHA services
Tests strategy engine, backtest service, and notification service
"""
import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from core import raha_models
if not hasattr(raha_models, 'NotificationPreferences'):
    pytest.skip("NotificationPreferences model not available", allow_module_level=True)

from core.raha_models import Strategy, StrategyVersion, UserStrategySettings, RAHASignal, RAHABacktestRun, NotificationPreferences
from core.raha_strategy_engine import RAHAStrategyEngine
from core.raha_backtest_service import RAHABacktestService
from core.raha_notification_service import RAHANotificationService

User = get_user_model()


class TestRAHAStrategyEngine(TestCase):
    """Test RAHA Strategy Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        # Create a test strategy
        self.strategy = Strategy.objects.create(
            slug='test-orb',
            name='Test ORB Strategy',
            category='MOMENTUM',
            description='Test strategy',
            market_type='STOCKS',
            timeframe_supported=['5m', '15m'],
            enabled=True
        )
        
        self.strategy_version = StrategyVersion.objects.create(
            strategy=self.strategy,
            version=1.0,
            is_default=True,
            config_schema={'atr_multiplier': {'type': 'float', 'default': 2.0}},
            logic_ref='orb'
        )
        
        self.engine = RAHAStrategyEngine()
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly"""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.feature_service)
    
    @patch('core.raha_strategy_engine.RAHAStrategyEngine._fetch_ohlcv_data')
    def test_generate_signals_orb(self, mock_fetch):
        """Test ORB signal generation"""
        # Mock OHLCV data
        import pandas as pd
        from datetime import datetime
        
        mock_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(minutes=i) for i in range(20, 0, -1)],
            'open': [100.0 + i * 0.1 for i in range(20)],
            'high': [100.5 + i * 0.1 for i in range(20)],
            'low': [99.5 + i * 0.1 for i in range(20)],
            'close': [100.2 + i * 0.1 for i in range(20)],
            'volume': [1000000] * 20
        })
        mock_fetch.return_value = mock_data
        
        signals = self.engine.generate_signals(
            strategy_version=self.strategy_version,
            symbol='AAPL',
            timeframe='5m',
            lookback_candles=20
        )
        
        self.assertIsInstance(signals, list)
        # Signals may be empty if conditions aren't met, which is fine
    
    def test_parse_timeframe(self):
        """Test timeframe parsing"""
        self.assertEqual(self.engine._parse_timeframe('5m'), 5)
        self.assertEqual(self.engine._parse_timeframe('15m'), 15)
        self.assertEqual(self.engine._parse_timeframe('1h'), 60)
        self.assertIsNone(self.engine._parse_timeframe('invalid'))
    
    def test_calculate_atr(self):
        """Test ATR calculation"""
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame({
            'high': [100.5, 101.0, 100.8, 101.2, 101.5],
            'low': [99.5, 100.0, 99.8, 100.2, 100.5],
            'close': [100.0, 100.5, 100.3, 100.8, 101.0]
        })
        
        atr = self.engine._calculate_atr(df, period=3)
        self.assertIsNotNone(atr)
        self.assertGreater(atr, 0)


class TestRAHABacktestService(TestCase):
    """Test RAHA Backtest Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        self.strategy = Strategy.objects.create(
            slug='test-strategy',
            name='Test Strategy',
            category='MOMENTUM',
            description='Test',
            market_type='STOCKS',
            timeframe_supported=['5m'],
            enabled=True
        )
        
        self.strategy_version = StrategyVersion.objects.create(
            strategy=self.strategy,
            version=1.0,
            is_default=True,
            config_schema={},
            logic_ref='momentum'
        )
        
        self.service = RAHABacktestService()
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.paper_trading)
        self.assertIsNotNone(self.service.strategy_engine)
    
    @patch('core.raha_backtest_service.RAHABacktestService._fetch_historical_data')
    @patch('core.raha_backtest_service.RAHAStrategyEngine.generate_signals')
    def test_run_backtest(self, mock_signals, mock_fetch):
        """Test backtest execution"""
        # Create backtest run
        backtest = RAHABacktestRun.objects.create(
            user=self.user,
            strategy_version=self.strategy_version,
            symbol='AAPL',
            timeframe='5m',
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            status='PENDING'
        )
        
        # Mock historical data
        import pandas as pd
        from datetime import datetime
        
        mock_data = pd.DataFrame({
            'date': [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)],
            'open': [100.0] * 30,
            'high': [101.0] * 30,
            'low': [99.0] * 30,
            'close': [100.5] * 30,
            'volume': [1000000] * 30
        })
        mock_fetch.return_value = mock_data
        
        # Mock signals
        mock_signals.return_value = []
        
        # Run backtest
        result = self.service.run_backtest(str(backtest.id))
        
        self.assertEqual(result.status, 'COMPLETED')
        self.assertIsNotNone(result.metrics)
        self.assertIsNotNone(result.equity_curve)
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        from core.paper_trading_service import PaperTradingService
        paper_trading = PaperTradingService()
        account = paper_trading.get_or_create_account(self.user, Decimal('10000.00'))
        
        trade_log = [
            {'pnl': 100.0, 'pnl_percent': 1.0, 'r_multiple': 1.0},
            {'pnl': -50.0, 'pnl_percent': -0.5, 'r_multiple': -0.5},
            {'pnl': 150.0, 'pnl_percent': 1.5, 'r_multiple': 1.5},
        ]
        
        metrics = self.service._calculate_metrics(trade_log, Decimal('10000.00'), account)
        
        self.assertIn('win_rate', metrics)
        self.assertIn('total_pnl_percent', metrics)
        self.assertIn('expectancy', metrics)
        self.assertGreater(metrics['win_rate'], 0)


class TestRAHANotificationService(TestCase):
    """Test RAHA Notification Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        self.service = RAHANotificationService()
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.expo_push_url, "https://exp.host/--/api/v2/push/send")
    
    def test_get_user_preferences(self):
        """Test getting user preferences"""
        prefs = self.service._get_user_preferences(self.user)
        self.assertIsNotNone(prefs)
        self.assertEqual(prefs.user, self.user)
    
    def test_is_quiet_hours(self):
        """Test quiet hours detection"""
        prefs = NotificationPreferences.objects.create(
            user=self.user,
            quiet_hours_enabled=True,
            quiet_hours_start=timezone.now().time().replace(hour=22, minute=0),
            quiet_hours_end=timezone.now().time().replace(hour=8, minute=0)
        )
        
        # This will depend on current time, so just test the method exists
        result = self.service._is_quiet_hours(prefs)
        self.assertIsInstance(result, bool)
    
    @patch('core.raha_notification_service.requests.post')
    def test_send_push_notification(self, mock_post):
        """Test sending push notification"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'status': 'ok'}}
        mock_post.return_value = mock_response
        
        result = self.service._send_push_notification(
            push_token='ExponentPushToken[test]',
            title='Test',
            body='Test notification'
        )
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    def test_should_notify_signal(self):
        """Test signal notification logic"""
        prefs = NotificationPreferences.objects.create(
            user=self.user,
            push_enabled=True,
            signal_notifications_enabled=True,
            signal_confidence_threshold=Decimal('0.70'),
            push_token='ExponentPushToken[test]'
        )
        
        # Create a high-confidence signal
        signal = Mock()
        signal.confidence_score = Decimal('0.85')
        signal.symbol = 'AAPL'
        
        should_notify = self.service._should_notify_signal(prefs, signal)
        self.assertTrue(should_notify)
        
        # Low confidence signal
        signal.confidence_score = Decimal('0.50')
        should_notify = self.service._should_notify_signal(prefs, signal)
        self.assertFalse(should_notify)


if __name__ == '__main__':
    unittest.main()

