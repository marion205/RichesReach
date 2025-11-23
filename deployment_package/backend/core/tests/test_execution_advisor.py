"""
Unit tests for ExecutionAdvisor
"""
import unittest
from decimal import Decimal
from core.execution_advisor import ExecutionAdvisor


class TestExecutionAdvisor(unittest.TestCase):
    
    def setUp(self):
        self.advisor = ExecutionAdvisor()
    
    def test_suggest_day_trading_order_wide_spread(self):
        """Test order suggestion for day trading with wide spread"""
        signal = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'entry_price': 150.0,
            'risk': {
                'stop': 147.0,
                'targets': [153.0, 156.0],
                'sizeShares': 100,
            },
            'features': {
                'spreadBps': 25.0,  # Wide spread
                'executionQualityScore': 4.0,  # Low quality
            }
        }
        
        suggestion = self.advisor.suggest_order(signal, 'day_trading')
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['order_type'], 'LIMIT')
        self.assertIn('price_band', suggestion)
        self.assertEqual(len(suggestion['price_band']), 2)
        self.assertIn('rationale', suggestion)
    
    def test_suggest_day_trading_order_tight_spread(self):
        """Test order suggestion for day trading with tight spread"""
        signal = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'entry_price': 150.0,
            'risk': {
                'stop': 147.0,
                'targets': [153.0, 156.0],
                'sizeShares': 100,
            },
            'features': {
                'spreadBps': 5.0,  # Tight spread
                'executionQualityScore': 8.0,  # High quality
            }
        }
        
        suggestion = self.advisor.suggest_order(signal, 'day_trading')
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['order_type'], 'LIMIT')
        self.assertEqual(suggestion['time_in_force'], 'IOC')  # Should use IOC for tight spread
        self.assertIn('price_band', suggestion)
    
    def test_suggest_swing_trading_order(self):
        """Test order suggestion for swing trading"""
        signal = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'entry_price': 150.0,
            'risk': {
                'stop': 145.0,
                'targets': [160.0, 170.0],
                'sizeShares': 100,
            },
            'features': {
                'spreadBps': 15.0,
            }
        }
        
        suggestion = self.advisor.suggest_order(signal, 'swing_trading')
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['order_type'], 'LIMIT')
        self.assertEqual(suggestion['time_in_force'], 'DAY')  # Swing trades use DAY
        self.assertIn('bracket_legs', suggestion)
    
    def test_bracket_legs_generation(self):
        """Test bracket legs generation"""
        signal = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'entry_price': 150.0,
            'risk': {
                'stop': 147.0,
                'targets': [153.0, 156.0],
                'sizeShares': 100,
            },
            'features': {
                'spreadBps': 5.0,
            }
        }
        
        suggestion = self.advisor.suggest_order(signal, 'day_trading')
        bracket_legs = suggestion.get('bracket_legs', {})
        
        self.assertIn('stop', bracket_legs)
        self.assertIn('target1', bracket_legs)
        self.assertEqual(bracket_legs['stop'], 147.0)
        self.assertEqual(bracket_legs['target1'], 153.0)
    
    def test_entry_timing_suggestion_enter_now(self):
        """Test entry timing suggestion when price is at entry"""
        signal = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'entry_price': 150.0,
            'risk': {
                'stop': 147.0,
                'targets': [153.0, 156.0],
            }
        }
        
        suggestion = self.advisor.suggest_entry_timing(signal, 150.05)  # Very close to entry
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['recommendation'], 'ENTER_NOW')
        self.assertIsNone(suggestion.get('wait_reason'))
    
    def test_entry_timing_suggestion_wait(self):
        """Test entry timing suggestion when price moved away"""
        signal = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'entry_price': 150.0,
            'risk': {
                'stop': 147.0,
                'targets': [153.0, 156.0],
            }
        }
        
        suggestion = self.advisor.suggest_entry_timing(signal, 151.0)  # Moved up 1%
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['recommendation'], 'WAIT_FOR_PULLBACK')
        self.assertIsNotNone(suggestion.get('wait_reason'))
        self.assertIsNotNone(suggestion.get('pullback_target'))


if __name__ == '__main__':
    unittest.main()

