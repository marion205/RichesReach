#!/usr/bin/env python3
"""
Comprehensive Test Suite for Pre-Market Scanner System
Runs all unit tests without requiring full Django test database
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

# Import Django
import django
django.setup()

# Now import our modules
from core.pre_market_scanner import PreMarketScanner
from core.pre_market_ml_learner import PreMarketMLearner, get_ml_learner
from core.pre_market_alerts import PreMarketAlertService, get_alert_service


class TestPreMarketScanner(unittest.TestCase):
    """Test PreMarketScanner"""
    
    def setUp(self):
        self.scanner = PreMarketScanner()
        with patch.dict(os.environ, {'POLYGON_API_KEY': 'test_key'}):
            self.scanner.polygon_key = 'test_key'
    
    def test_get_et_hour(self):
        """Test ET hour calculation"""
        et_hour = self.scanner._get_et_hour()
        self.assertIsInstance(et_hour, int)
        self.assertGreaterEqual(et_hour, 0)
        self.assertLess(et_hour, 24)
        print("✅ test_get_et_hour passed")
    
    def test_is_pre_market_hours(self):
        """Test pre-market hours detection"""
        result = self.scanner.is_pre_market_hours()
        self.assertIsInstance(result, bool)
        print("✅ test_is_pre_market_hours passed")
    
    def test_apply_pre_market_filters_safe(self):
        """Test filters in SAFE mode"""
        ticker = {
            'ticker': 'AAPL',
            'lastTrade': {'p': 150.0},
            'day': {'v': 3000000},
            'market_cap': 2500000000000,
            'pre_market_change_pct': 0.05,
        }
        passed, reasons = self.scanner.apply_pre_market_filters(ticker, mode='SAFE')
        self.assertIsInstance(passed, bool)
        self.assertIsInstance(reasons, list)
        print("✅ test_apply_pre_market_filters_safe passed")
    
    def test_apply_pre_market_filters_aggressive(self):
        """Test filters in AGGRESSIVE mode"""
        ticker = {
            'ticker': 'TSLA',
            'lastTrade': {'p': 250.0},
            'day': {'v': 800000},
            'market_cap': 800000000,
            'pre_market_change_pct': 0.15,
        }
        passed, reasons = self.scanner.apply_pre_market_filters(ticker, mode='AGGRESSIVE')
        self.assertIsInstance(passed, bool)
        print("✅ test_apply_pre_market_filters_aggressive passed")
    
    def test_generate_alert(self):
        """Test alert generation"""
        setups = [{
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_change_pct': 0.025,
            'pre_market_price': 150.0,
            'score': 7.5,
            'notes': 'Test setup',
        }]
        alert = self.scanner.generate_alert(setups)
        self.assertIsInstance(alert, str)
        self.assertIn('AAPL', alert)
        print("✅ test_generate_alert passed")
    
    def test_minutes_until_open(self):
        """Test minutes until open calculation"""
        minutes = self.scanner._minutes_until_open()
        self.assertIsInstance(minutes, int)
        self.assertGreaterEqual(minutes, 0)
        print("✅ test_minutes_until_open passed")


class TestPreMarketMLLearner(unittest.TestCase):
    """Test PreMarketMLearner"""
    
    def setUp(self):
        self.learner = PreMarketMLearner()
    
    def test_extract_features(self):
        """Test feature extraction"""
        pick = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_price': 150.0,
            'pre_market_change_pct': 0.025,
            'volume': 2000000,
            'market_cap': 2500000000000,
            'prev_close': 145.0,
        }
        features = self.learner.extract_features(pick)
        self.assertIsInstance(features, dict)
        self.assertIn('pre_market_change_pct', features)
        self.assertEqual(features['is_long'], 1)
        print("✅ test_extract_features passed")
    
    def test_record_pick_outcome(self):
        """Test recording outcomes"""
        pick = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_price': 150.0,
            'pre_market_change_pct': 0.025,
            'volume': 2000000,
            'market_cap': 2500000000000,
            'prev_close': 145.0,
        }
        outcome = {
            'success': True,
            'return_pct': 0.05,
            'hit_target': True,
            'hit_stop': False,
            'max_favorable': 0.08,
            'max_adverse': -0.02,
        }
        initial_count = len(self.learner.performance_history)
        self.learner.record_pick_outcome(pick, outcome)
        self.assertEqual(len(self.learner.performance_history), initial_count + 1)
        print("✅ test_record_pick_outcome passed")
    
    def test_heuristic_score(self):
        """Test heuristic scoring"""
        pick = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_price': 150.0,
            'pre_market_change_pct': 0.05,
            'volume': 2000000,
            'market_cap': 2500000000000,
            'prev_close': 145.0,
        }
        score = self.learner._heuristic_score(pick)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        print("✅ test_heuristic_score passed")
    
    def test_predict_success_probability(self):
        """Test success probability prediction"""
        pick = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_price': 150.0,
            'pre_market_change_pct': 0.05,
            'volume': 2000000,
            'market_cap': 2500000000000,
            'prev_close': 145.0,
        }
        # Remove model to test fallback
        self.learner.model = None
        self.learner.scaler = None
        prob = self.learner.predict_success_probability(pick)
        self.assertIsInstance(prob, float)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
        print("✅ test_predict_success_probability passed")
    
    def test_enhance_picks_with_ml(self):
        """Test ML enhancement"""
        picks = [{
            'symbol': 'AAPL',
            'side': 'LONG',
            'score': 7.5,
            'pre_market_price': 150.0,
            'pre_market_change_pct': 0.05,
            'volume': 2000000,
            'market_cap': 2500000000000,
            'prev_close': 145.0,
        }]
        enhanced = self.learner.enhance_picks_with_ml(picks)
        self.assertIsInstance(enhanced, list)
        self.assertEqual(len(enhanced), 1)
        self.assertIn('ml_success_probability', enhanced[0])
        print("✅ test_enhance_picks_with_ml passed")


class TestPreMarketAlerts(unittest.TestCase):
    """Test PreMarketAlertService"""
    
    def setUp(self):
        self.alert_service = PreMarketAlertService()
    
    def test_generate_email_text(self):
        """Test email text generation"""
        setups = [{
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_change_pct': 0.025,
            'pre_market_price': 150.0,
            'score': 7.5,
            'notes': 'Test setup',
        }]
        text = self.alert_service._generate_email_text(setups)
        self.assertIsInstance(text, str)
        self.assertIn('AAPL', text)
        print("✅ test_generate_email_text passed")
    
    def test_generate_email_html(self):
        """Test HTML email generation"""
        setups = [{
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_change_pct': 0.025,
            'pre_market_price': 150.0,
            'score': 7.5,
            'notes': 'Test setup',
        }]
        html = self.alert_service._generate_email_html(setups)
        self.assertIsInstance(html, str)
        self.assertIn('<html>', html)
        self.assertIn('AAPL', html)
        print("✅ test_generate_email_html passed")
    
    def test_send_push_notification(self):
        """Test push notification"""
        setups = [{
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_change_pct': 0.025,
            'pre_market_price': 150.0,
            'score': 7.5,
            'notes': 'Test setup',
        }]
        self.alert_service.push_notification_key = 'test_key'
        result = self.alert_service.send_push_notification(setups)
        self.assertIsInstance(result, bool)
        print("✅ test_send_push_notification passed")


def run_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("PRE-MARKET SCANNER TEST SUITE")
    print("="*80 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPreMarketScanner))
    suite.addTests(loader.loadTestsFromTestCase(TestPreMarketMLLearner))
    suite.addTests(loader.loadTestsFromTestCase(TestPreMarketAlerts))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    print("="*80 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

