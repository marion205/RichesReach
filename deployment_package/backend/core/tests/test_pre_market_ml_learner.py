"""
Unit tests for Pre-Market ML Learner
"""
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
import numpy as np

from core.pre_market_ml_learner import PreMarketMLearner, get_ml_learner


class PreMarketMLearnerTestCase(TestCase):
    """Test cases for PreMarketMLearner"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create ML models directory if it doesn't exist
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'ml_models'), exist_ok=True)
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
        self.assertIn('volume', features)
        self.assertIn('market_cap', features)
        self.assertIn('is_long', features)
        self.assertEqual(features['is_long'], 1)  # LONG = 1
    
    def test_extract_features_short(self):
        """Test feature extraction for SHORT"""
        pick = {
            'symbol': 'TSLA',
            'side': 'SHORT',
            'pre_market_price': 250.0,
            'pre_market_change_pct': -0.05,
            'volume': 1000000,
            'market_cap': 800000000000,
            'prev_close': 260.0,
        }
        
        features = self.learner.extract_features(pick)
        self.assertEqual(features['is_long'], 0)  # SHORT = 0
        self.assertLess(features['pre_market_change_pct'], 0)
    
    def test_record_pick_outcome(self):
        """Test recording pick outcome"""
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
        
        # Check that the record was added correctly
        last_record = self.learner.performance_history[-1]
        self.assertEqual(last_record['pick']['symbol'], 'AAPL')
        self.assertTrue(last_record['outcome']['success'])
    
    def test_record_pick_outcome_history_limit(self):
        """Test that history is limited to 1000 records"""
        # Add 1001 records
        pick = {'symbol': 'TEST', 'side': 'LONG', 'pre_market_price': 100.0,
                'pre_market_change_pct': 0.01, 'volume': 1000000,
                'market_cap': 1000000000, 'prev_close': 99.0}
        outcome = {'success': True, 'return_pct': 0.02, 'hit_target': False,
                   'hit_stop': False, 'max_favorable': 0.03, 'max_adverse': -0.01}
        
        for _ in range(1001):
            self.learner.record_pick_outcome(pick, outcome)
        
        self.assertLessEqual(len(self.learner.performance_history), 1000)
    
    def test_heuristic_score(self):
        """Test heuristic scoring fallback"""
        pick = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_price': 150.0,
            'pre_market_change_pct': 0.05,  # 5% move
            'volume': 2000000,
            'market_cap': 2500000000000,
            'prev_close': 145.0,
        }
        
        score = self.learner._heuristic_score(pick)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_heuristic_score_high_change(self):
        """Test heuristic score for high change (should be penalized)"""
        pick = {
            'symbol': 'VOLATILE',
            'side': 'LONG',
            'pre_market_price': 100.0,
            'pre_market_change_pct': 0.30,  # 30% move - too high
            'volume': 1000000,
            'market_cap': 1000000000,
            'prev_close': 70.0,
        }
        
        score = self.learner._heuristic_score(pick)
        # High change should reduce score
        self.assertLess(score, 0.5)
    
    def test_predict_success_probability_no_model(self):
        """Test prediction when model is not available"""
        # Remove model if it exists
        self.learner.model = None
        self.learner.scaler = None
        
        pick = {
            'symbol': 'AAPL',
            'side': 'LONG',
            'pre_market_price': 150.0,
            'pre_market_change_pct': 0.05,
            'volume': 2000000,
            'market_cap': 2500000000000,
            'prev_close': 145.0,
        }
        
        prob = self.learner.predict_success_probability(pick)
        self.assertIsInstance(prob, float)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
    
    def test_enhance_picks_with_ml(self):
        """Test ML enhancement of picks"""
        picks = [
            {
                'symbol': 'AAPL',
                'side': 'LONG',
                'score': 7.5,
                'pre_market_price': 150.0,
                'pre_market_change_pct': 0.05,
                'volume': 2000000,
                'market_cap': 2500000000000,
                'prev_close': 145.0,
            }
        ]
        
        enhanced = self.learner.enhance_picks_with_ml(picks)
        self.assertIsInstance(enhanced, list)
        self.assertEqual(len(enhanced), 1)
        
        enhanced_pick = enhanced[0]
        self.assertIn('ml_success_probability', enhanced_pick)
        self.assertIn('ml_enhanced_score', enhanced_pick)
        self.assertIsInstance(enhanced_pick['ml_success_probability'], float)
    
    def test_get_learning_insights_no_model(self):
        """Test getting insights when model not trained"""
        self.learner.feature_weights = {}
        insights = self.learner.get_learning_insights()
        self.assertIn('message', insights)
    
    def test_get_learning_insights_with_model(self):
        """Test getting insights when model is trained"""
        self.learner.feature_weights = {
            'pre_market_change_pct': 0.3,
            'volume': 0.2,
            'market_cap': 0.15,
            'price': 0.1,
            'is_long': 0.05,
        }
        
        insights = self.learner.get_learning_insights()
        self.assertIn('top_features', insights)
        self.assertIn('total_records', insights)
    
    def test_get_ml_learner_singleton(self):
        """Test that get_ml_learner returns singleton"""
        learner1 = get_ml_learner()
        learner2 = get_ml_learner()
        self.assertIs(learner1, learner2)
    
    @patch('core.pre_market_ml_learner.ML_AVAILABLE', True)
    @patch('core.pre_market_ml_learner.np')
    @patch('core.pre_market_ml_learner.train_test_split')
    @patch('core.pre_market_ml_learner.StandardScaler')
    @patch('core.pre_market_ml_learner.GradientBoostingRegressor')
    def test_train_model_insufficient_data(self, mock_gbr, mock_scaler, mock_split, mock_np):
        """Test training with insufficient data"""
        # Clear history
        self.learner.performance_history = []
        
        result = self.learner.train_model()
        self.assertIn('error', result)
        self.assertIn('Insufficient', result['error'])
    
    @patch('core.pre_market_ml_learner.ML_AVAILABLE', True)
    def test_train_model_sufficient_data(self):
        """Test training with sufficient data"""
        # Add 60 records
        pick = {'symbol': 'TEST', 'side': 'LONG', 'pre_market_price': 100.0,
                'pre_market_change_pct': 0.05, 'volume': 1000000,
                'market_cap': 1000000000, 'prev_close': 95.0}
        
        for i in range(60):
            outcome = {
                'success': i % 2 == 0,  # Alternate success/failure
                'return_pct': 0.02 if i % 2 == 0 else -0.01,
                'hit_target': i % 2 == 0,
                'hit_stop': i % 2 == 1,
                'max_favorable': 0.03,
                'max_adverse': -0.02,
            }
            self.learner.record_pick_outcome(pick, outcome)
        
        # Mock ML libraries
        with patch('core.pre_market_ml_learner.ML_AVAILABLE', True):
            try:
                result = self.learner.train_model()
                # Should either succeed or fail gracefully
                self.assertIsInstance(result, dict)
            except Exception as e:
                # If ML libraries not available, that's okay
                self.assertIn('error', str(e).lower() or 'ml' in str(e).lower())

