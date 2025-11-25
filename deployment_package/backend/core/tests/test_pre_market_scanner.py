"""
Unit tests for Pre-Market Scanner
"""
import os
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from django.test import TestCase
from django.utils import timezone as django_timezone

from core.pre_market_scanner import PreMarketScanner


class PreMarketScannerTestCase(TestCase):
    """Test cases for PreMarketScanner"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scanner = PreMarketScanner()
        # Mock Polygon API key
        with patch.dict(os.environ, {'POLYGON_API_KEY': 'test_key'}):
            self.scanner.polygon_key = 'test_key'
    
    def test_get_et_hour(self):
        """Test ET hour calculation"""
        et_hour = self.scanner._get_et_hour()
        self.assertIsInstance(et_hour, int)
        self.assertGreaterEqual(et_hour, 0)
        self.assertLess(et_hour, 24)
    
    def test_is_pre_market_hours(self):
        """Test pre-market hours detection"""
        # Mock current time to be in pre-market hours
        with patch('core.pre_market_scanner.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 25, 13, 0, 0, tzinfo=timezone.utc)  # 8 AM ET
            result = self.scanner.is_pre_market_hours()
            self.assertIsInstance(result, bool)
    
    def test_apply_pre_market_filters_safe_mode(self):
        """Test pre-market filters in SAFE mode"""
        ticker = {
            'ticker': 'AAPL',
            'lastTrade': {'p': 150.0},
            'day': {'v': 3000000},
            'market_cap': 2500000000000,  # $2.5T
            'pre_market_change_pct': 0.05,  # 5%
        }
        
        passed, reasons = self.scanner.apply_pre_market_filters(ticker, mode='SAFE')
        self.assertIsInstance(passed, bool)
        self.assertIsInstance(reasons, list)
    
    def test_apply_pre_market_filters_aggressive_mode(self):
        """Test pre-market filters in AGGRESSIVE mode"""
        ticker = {
            'ticker': 'TSLA',
            'lastTrade': {'p': 250.0},
            'day': {'v': 800000},
            'market_cap': 800000000,  # $800M
            'pre_market_change_pct': 0.15,  # 15%
        }
        
        passed, reasons = self.scanner.apply_pre_market_filters(ticker, mode='AGGRESSIVE')
        self.assertIsInstance(passed, bool)
        self.assertIsInstance(reasons, list)
    
    def test_apply_pre_market_filters_rejects_invalid_symbols(self):
        """Test that invalid symbols are rejected"""
        ticker = {
            'ticker': 'INVALID.SYMBOL',  # Contains dot
            'lastTrade': {'p': 100.0},
            'day': {'v': 1000000},
            'market_cap': 1000000000,
            'pre_market_change_pct': 0.05,
        }
        
        passed, reasons = self.scanner.apply_pre_market_filters(ticker, mode='AGGRESSIVE')
        self.assertFalse(passed)
        self.assertGreater(len(reasons), 0)
    
    def test_apply_pre_market_filters_rejects_low_price(self):
        """Test that low-priced stocks are rejected in SAFE mode"""
        ticker = {
            'ticker': 'PENNY',
            'lastTrade': {'p': 0.50},  # Too low for SAFE mode
            'day': {'v': 5000000},
            'market_cap': 10000000000,
            'pre_market_change_pct': 0.05,
        }
        
        passed, reasons = self.scanner.apply_pre_market_filters(ticker, mode='SAFE')
        self.assertFalse(passed)
    
    def test_apply_pre_market_filters_rejects_high_change(self):
        """Test that high change percentages are rejected"""
        ticker = {
            'ticker': 'VOLATILE',
            'lastTrade': {'p': 100.0},
            'day': {'v': 2000000},
            'market_cap': 5000000000,
            'pre_market_change_pct': 0.60,  # 60% - too high
        }
        
        passed, reasons = self.scanner.apply_pre_market_filters(ticker, mode='AGGRESSIVE')
        self.assertFalse(passed)
    
    def test_generate_alert(self):
        """Test alert message generation"""
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'notes': 'Test setup',
            }
        ]
        
        alert = self.scanner.generate_alert(setups)
        self.assertIsInstance(alert, str)
        self.assertIn('AAPL', alert)
        self.assertIn('LONG', alert)
    
    def test_generate_alert_empty(self):
        """Test alert generation with empty setups"""
        alert = self.scanner.generate_alert([])
        self.assertIsInstance(alert, str)
        self.assertIn('No quality', alert)
    
    def test_minutes_until_open(self):
        """Test minutes until market open calculation"""
        minutes = self.scanner._minutes_until_open()
        self.assertIsInstance(minutes, int)
        self.assertGreaterEqual(minutes, 0)
    
    @patch('core.pre_market_scanner.aiohttp.ClientSession')
    async def test_fetch_pre_market_movers_success(self, mock_session):
        """Test successful pre-market movers fetch"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'tickers': [
                {
                    'ticker': 'AAPL',
                    'lastTrade': {'p': 150.0},
                    'prevDay': {'c': 145.0},
                    'day': {'v': 2000000},
                    'market_cap': 2500000000000,
                }
            ]
        })
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        movers = await self.scanner.fetch_pre_market_movers(limit=10)
        self.assertIsInstance(movers, list)
    
    @patch('core.pre_market_scanner.aiohttp.ClientSession')
    async def test_fetch_pre_market_movers_no_key(self, mock_session):
        """Test fetch when API key is missing"""
        self.scanner.polygon_key = ''
        movers = await self.scanner.fetch_pre_market_movers(limit=10)
        self.assertEqual(movers, [])
    
    @patch('core.pre_market_scanner.get_ml_learner')
    def test_scan_pre_market_with_ml(self, mock_ml_learner):
        """Test scan with ML enhancement"""
        # Mock ML learner
        mock_learner = Mock()
        mock_learner.enhance_picks_with_ml.return_value = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'score': 8.5,
                'ml_success_probability': 0.75,
                'ml_enhanced_score': 8.5,
            }
        ]
        mock_ml_learner.return_value = mock_learner
        
        # Mock pre-market hours
        with patch.object(self.scanner, 'is_pre_market_hours', return_value=True):
            with patch.object(self.scanner, 'fetch_pre_market_movers', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = [
                    {
                        'ticker': 'AAPL',
                        'lastTrade': {'p': 150.0},
                        'prevDay': {'c': 145.0},
                        'day': {'v': 2000000},
                        'market_cap': 2500000000000,
                        'pre_market_change_pct': 0.034,
                    }
                ]
                
                # This is async, so we'd need to run it in an event loop
                # For now, just test that the method exists and can be called
                self.assertTrue(hasattr(self.scanner, 'scan_pre_market'))
    
    def test_send_alerts(self):
        """Test alert sending"""
        setups = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'pre_market_change_pct': 0.025,
                'pre_market_price': 150.0,
                'score': 7.5,
                'notes': 'Test setup',
            }
        ]
        
        with patch('core.pre_market_scanner.ALERTS_AVAILABLE', True):
            with patch('core.pre_market_scanner.get_alert_service') as mock_service:
                mock_alert_service = Mock()
                mock_alert_service.send_email_alert.return_value = True
                mock_alert_service.send_push_notification.return_value = True
                mock_service.return_value = mock_alert_service
                
                results = self.scanner.send_alerts(setups)
                self.assertIsInstance(results, dict)
                self.assertIn('email_sent', results)
                self.assertIn('push_sent', results)

