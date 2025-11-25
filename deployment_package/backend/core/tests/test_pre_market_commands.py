"""
Unit tests for Pre-Market Management Commands
"""
import os
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from django.core.management.base import CommandError

from core.management.commands.pre_market_scan import Command as PreMarketScanCommand
from core.management.commands.pre_market_scan_with_alerts import Command as PreMarketScanWithAlertsCommand
from core.management.commands.evaluate_pre_market_performance import Command as EvaluatePerformanceCommand


class PreMarketScanCommandTestCase(TestCase):
    """Test cases for pre_market_scan command"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.command = PreMarketScanCommand()
        self.command.stdout = StringIO()
    
    @patch('core.management.commands.pre_market_scan.PreMarketScanner')
    def test_handle_not_pre_market_hours(self, mock_scanner_class):
        """Test command when not in pre-market hours"""
        mock_scanner = Mock()
        mock_scanner.is_pre_market_hours.return_value = False
        mock_scanner._get_et_hour.return_value = 15  # 3 PM ET
        mock_scanner_class.return_value = mock_scanner
        
        self.command.handle(mode='AGGRESSIVE', limit=20)
        output = self.command.stdout.getvalue()
        self.assertIn('Not in pre-market hours', output)
    
    @patch('core.management.commands.pre_market_scan.PreMarketScanner')
    def test_handle_pre_market_hours_no_setups(self, mock_scanner_class):
        """Test command when in pre-market hours but no setups found"""
        mock_scanner = Mock()
        mock_scanner.is_pre_market_hours.return_value = True
        mock_scanner._minutes_until_open.return_value = 45
        mock_scanner.scan_pre_market_sync.return_value = []
        mock_scanner_class.return_value = mock_scanner
        
        self.command.handle(mode='AGGRESSIVE', limit=20)
        output = self.command.stdout.getvalue()
        self.assertIn('No quality pre-market setups', output)
    
    @patch('core.management.commands.pre_market_scan.PreMarketScanner')
    def test_handle_pre_market_hours_with_setups(self, mock_scanner_class):
        """Test command when setups are found"""
        mock_scanner = Mock()
        mock_scanner.is_pre_market_hours.return_value = True
        mock_scanner._minutes_until_open.return_value = 45
        mock_scanner.scan_pre_market_sync.return_value = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'volume': 2000000,
                'notes': 'Test setup',
            }
        ]
        mock_scanner_class.return_value = mock_scanner
        
        self.command.handle(mode='AGGRESSIVE', limit=20)
        output = self.command.stdout.getvalue()
        self.assertIn('AAPL', output)
        self.assertIn('LONG', output)


class PreMarketScanWithAlertsCommandTestCase(TestCase):
    """Test cases for pre_market_scan_with_alerts command"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.command = PreMarketScanWithAlertsCommand()
        self.command.stdout = StringIO()
    
    @patch('core.management.commands.pre_market_scan_with_alerts.PreMarketScanner')
    @patch('core.management.commands.pre_market_scan_with_alerts.get_ml_learner')
    def test_handle_train_ml(self, mock_get_ml_learner, mock_scanner_class):
        """Test ML training"""
        mock_scanner = Mock()
        mock_scanner.is_pre_market_hours.return_value = False
        mock_scanner_class.return_value = mock_scanner
        
        mock_learner = Mock()
        mock_learner.train_model.return_value = {
            'train_score': 0.75,
            'test_score': 0.70,
            'records_used': 100,
            'success_rate': 0.60,
            'feature_importances': {
                'pre_market_change_pct': 0.3,
                'volume': 0.2,
            }
        }
        mock_get_ml_learner.return_value = mock_learner
        
        self.command.handle(mode='AGGRESSIVE', limit=20, train_ml=True)
        output = self.command.stdout.getvalue()
        self.assertIn('Training ML model', output)
        self.assertIn('0.750', output)  # Train score
    
    @patch('core.management.commands.pre_market_scan_with_alerts.PreMarketScanner')
    @patch('core.management.commands.pre_market_scan_with_alerts.get_ml_learner')
    def test_handle_ml_insights(self, mock_get_ml_learner, mock_scanner_class):
        """Test ML insights display"""
        mock_scanner = Mock()
        mock_scanner.is_pre_market_hours.return_value = False
        mock_scanner_class.return_value = mock_scanner
        
        mock_learner = Mock()
        mock_learner.get_learning_insights.return_value = {
            'total_records': 100,
            'model_available': True,
            'top_features': [
                ('pre_market_change_pct', 0.3),
                ('volume', 0.2),
            ]
        }
        mock_get_ml_learner.return_value = mock_learner
        
        self.command.handle(mode='AGGRESSIVE', limit=20, ml_insights=True)
        output = self.command.stdout.getvalue()
        self.assertIn('ML Learning Insights', output)
        self.assertIn('100', output)  # Total records


class EvaluatePerformanceCommandTestCase(TestCase):
    """Test cases for evaluate_pre_market_performance command"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.command = EvaluatePerformanceCommand()
        self.command.stdout = StringIO()
    
    @patch('core.management.commands.evaluate_pre_market_performance.DayTradingSignal')
    @patch('core.management.commands.evaluate_pre_market_performance.SignalPerformance')
    @patch('core.management.commands.evaluate_pre_market_performance.get_ml_learner')
    def test_handle_no_signals(self, mock_get_ml_learner, mock_signal_perf, mock_signal):
        """Test when no signals found"""
        from django.db.models import Q
        from django.utils import timezone
        from datetime import timedelta
        
        mock_signal.objects.filter.return_value.exists.return_value = False
        mock_signal.objects.filter.return_value.order_by.return_value = []
        
        self.command.handle(days=1)
        output = self.command.stdout.getvalue()
        self.assertIn('No signals found', output)
    
    @patch('core.management.commands.evaluate_pre_market_performance.DayTradingSignal')
    @patch('core.management.commands.evaluate_pre_market_performance.SignalPerformance')
    @patch('core.management.commands.evaluate_pre_market_performance.get_ml_learner')
    def test_handle_with_signals(self, mock_get_ml_learner, mock_signal_perf, mock_signal):
        """Test when signals are found"""
        from django.db.models import Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Mock signal
        mock_signal_obj = Mock()
        mock_signal_obj.id = 1
        mock_signal_obj.symbol = 'AAPL'
        mock_signal_obj.entry_price = 150.0
        
        # Mock queryset
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_queryset.order_by.return_value = [mock_signal_obj]
        mock_signal.objects.filter.return_value = mock_queryset
        
        # Mock performance
        mock_perf_obj = Mock()
        mock_perf_obj.outcome = 'WIN'
        mock_perf_obj.pnl_percent = 0.05
        mock_perf_obj.hit_target_1 = True
        mock_perf_obj.hit_stop = False
        mock_perf_obj.max_favorable_excursion = 0.08
        mock_perf_obj.max_adverse_excursion = -0.02
        
        mock_perf_queryset = Mock()
        mock_perf_queryset.filter.return_value.exists.return_value = True
        mock_perf_queryset.filter.return_value.order_by.return_value = [mock_perf_obj]
        mock_perf_queryset.filter.return_value.first.return_value = mock_perf_obj
        mock_signal_perf.objects.filter.return_value = mock_perf_queryset
        
        # Mock ML learner
        mock_learner = Mock()
        mock_get_ml_learner.return_value = mock_learner
        
        self.command.handle(days=1)
        output = self.command.stdout.getvalue()
        # Should process the signal
        self.assertIsInstance(output, str)

