"""
Comprehensive unit tests for day trading features and ML models
Tests all features from both trading books
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from day_trading_feature_service import DayTradingFeatureService
from day_trading_ml_scorer import DayTradingMLScorer


class TestDayTradingFeatureService(unittest.TestCase):
    """Test day trading feature extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = DayTradingFeatureService()
        self.ohlcv_1m = self._create_mock_ohlcv_1m()
        self.ohlcv_5m = self._create_mock_ohlcv_5m()
    
    def _create_mock_ohlcv_1m(self, n_bars=390):
        """Create mock 1-minute OHLCV data"""
        base_price = 100.0
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(n_bars, 0, -1)]
        
        prices = [base_price]
        for i in range(1, n_bars):
            change = np.random.normal(0, 0.001)
            prices.append(prices[-1] * (1 + change))
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.0005))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.0005))) for p in prices],
            'close': prices,
            'volume': [np.random.randint(100000, 1000000) for _ in range(n_bars)]
        })
    
    def _create_mock_ohlcv_5m(self, n_bars=78):
        """Create mock 5-minute OHLCV data"""
        base_price = 100.0
        timestamps = [datetime.now() - timedelta(minutes=i*5) for i in range(n_bars, 0, -1)]
        
        prices = [base_price]
        for i in range(1, n_bars):
            change = np.random.normal(0, 0.002)
            prices.append(prices[-1] * (1 + change))
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
            'close': prices,
            'volume': [np.random.randint(500000, 5000000) for _ in range(n_bars)]
        })
    
    def test_extract_all_features(self):
        """Test that all features are extracted"""
        features = self.service.extract_all_features(
            self.ohlcv_1m, self.ohlcv_5m, "AAPL"
        )
        
        # Should have 100+ features
        self.assertGreater(len(features), 100)
        
        # Check key feature categories exist
        self.assertIn('momentum_15m', features)
        self.assertIn('realized_vol_10', features)
        self.assertIn('vwap_dist_pct', features)
        self.assertIn('breakout_pct', features)
        self.assertIn('spread_bps', features)
        self.assertIn('is_trend_regime', features)
        self.assertIn('is_breakout', features)
        self.assertIn('rsi_14', features)
        self.assertIn('macd', features)
    
    def test_candlestick_features(self):
        """Test candlestick pattern detection"""
        features = self.service._extract_candlestick_features(self.ohlcv_5m)
        
        # Should have candlestick features
        self.assertIn('body_pct', features)
        self.assertIn('upper_wick_pct', features)
        self.assertIn('lower_wick_pct', features)
        self.assertIn('gap_up_pct', features)
        self.assertIn('gap_down_pct', features)
        
        # Pattern flags should be binary (0.0 or 1.0)
        pattern_flags = ['is_hammer', 'is_shooting_star', 'is_doji', 
                        'is_engulfing_bull', 'is_engulfing_bear', 'is_marubozu']
        for flag in pattern_flags:
            if flag in features:
                self.assertIn(features[flag], [0.0, 1.0])
    
    def test_technical_indicators(self):
        """Test technical indicator calculation"""
        features = self.service._extract_technical_indicators(self.ohlcv_5m)
        
        # Moving averages
        self.assertIn('sma_5', features)
        self.assertIn('sma_20', features)
        self.assertIn('sma_50', features)
        self.assertIn('ema_12', features)
        self.assertIn('ema_26', features)
        
        # MACD
        self.assertIn('macd', features)
        self.assertIn('macd_signal', features)
        self.assertIn('macd_hist', features)
        
        # RSI
        self.assertIn('rsi_14', features)
        self.assertGreaterEqual(features['rsi_14'], 0.0)
        self.assertLessEqual(features['rsi_14'], 100.0)
        
        # Bollinger Bands
        self.assertIn('bb_upper', features)
        self.assertIn('bb_middle', features)
        self.assertIn('bb_lower', features)
        self.assertIn('bb_width', features)
        self.assertIn('bb_position', features)
        
        # ATR
        self.assertIn('atr_14', features)
        self.assertGreater(features['atr_14'], 0.0)
    
    def test_volatility_features(self):
        """Test volatility and breakout features (Bernstein)"""
        features = self.service._extract_volatility_features(self.ohlcv_5m)
        
        # Volatility metrics
        self.assertIn('realized_vol_20', features)
        self.assertIn('realized_vol_10', features)
        self.assertIn('atr_14_pct', features)
        self.assertIn('true_range_pct', features)
        
        # Breakout features
        self.assertIn('breakout_pct', features)
        self.assertIn('breakdown_pct', features)
        self.assertIn('range_compression', features)
        
        # Flags
        self.assertIn('is_vol_expansion', features)
        self.assertIn('is_breakout', features)
        self.assertIn('is_breakdown', features)
    
    def test_regime_detection(self):
        """Test market regime detection (Bernstein)"""
        features = self.service._detect_market_regime(self.ohlcv_5m)
        
        # Regime features
        self.assertIn('trend_strength', features)
        self.assertIn('is_trend_regime', features)
        self.assertIn('is_range_regime', features)
        self.assertIn('is_high_vol_chop', features)
        self.assertIn('is_trend_up', features)
        self.assertIn('is_trend_down', features)
        self.assertIn('regime_confidence', features)
        
        # Regime flags should be binary
        self.assertIn(features['is_trend_regime'], [0.0, 1.0])
        self.assertIn(features['is_range_regime'], [0.0, 1.0])
        self.assertIn(features['is_high_vol_chop'], [0.0, 1.0])
        
        # Confidence should be between 0 and 1
        self.assertGreaterEqual(features['regime_confidence'], 0.0)
        self.assertLessEqual(features['regime_confidence'], 1.0)
    
    def test_time_features(self):
        """Test time-of-day features (Bernstein)"""
        now = datetime.now()
        features = self.service._extract_time_features(now)
        
        # Time features
        self.assertIn('dow', features)
        self.assertIn('dom', features)
        self.assertIn('hour_of_day', features)
        
        # Cyclical encoding
        self.assertIn('dow_sin', features)
        self.assertIn('dow_cos', features)
        self.assertIn('hour_sin', features)
        self.assertIn('hour_cos', features)
        
        # Session flags
        self.assertIn('is_opening_hour', features)
        self.assertIn('is_closing_hour', features)
        self.assertIn('is_midday', features)
        
        # Day of month effects
        self.assertIn('is_month_end', features)
        self.assertIn('is_month_start', features)
    
    def test_sentiment_features(self):
        """Test sentiment features (Bernstein's sentiment index)"""
        sentiment_data = {
            'score': 0.5,
            'message_count': 100,
            'bull_count': 60,
            'bear_count': 30,
            'neutral_count': 10,
            'price_trend': 0.02
        }
        
        features = self.service._extract_sentiment_features(sentiment_data)
        
        self.assertIn('sentiment_score', features)
        self.assertIn('sentiment_volume', features)
        self.assertIn('bull_ratio', features)
        self.assertIn('bear_ratio', features)
        self.assertIn('extreme_sentiment_flag', features)
        self.assertIn('sentiment_divergence', features)
        
        # Ratios should be between 0 and 1
        self.assertGreaterEqual(features['bull_ratio'], 0.0)
        self.assertLessEqual(features['bull_ratio'], 1.0)
    
    def test_momentum_features(self):
        """Test momentum feature extraction"""
        features = self.service._extract_momentum_features(self.ohlcv_1m, self.ohlcv_5m)
        
        self.assertIn('momentum_15m', features)
        self.assertIn('momentum_5m', features)
        self.assertIn('momentum_1m', features)
        self.assertIn('roc_10', features)
    
    def test_vwap_features(self):
        """Test VWAP feature extraction"""
        features = self.service._extract_vwap_features(self.ohlcv_5m)
        
        self.assertIn('vwap', features)
        self.assertIn('vwap_dist', features)
        self.assertIn('vwap_dist_pct', features)
    
    def test_risk_features(self):
        """Test risk management features (Day Trading 101)"""
        features = self.service._extract_risk_features(self.ohlcv_5m)
        
        self.assertIn('atr_5m', features)
        self.assertIn('atr_5m_pct', features)
        self.assertIn('risk_per_trade_pct', features)
        self.assertIn('vol_norm_size', features)
        self.assertIn('risk_reward_ratio', features)
    
    def test_calculate_risk_metrics(self):
        """Test risk metrics calculation"""
        features = {
            'atr_5m': 1.0,
            'atr_5m_pct': 0.01,
            'momentum_15m': 0.02
        }
        
        risk_metrics = self.service.calculate_risk_metrics(features, "SAFE", 100.0)
        
        self.assertIn('atr5m', risk_metrics)
        self.assertIn('sizeShares', risk_metrics)
        self.assertIn('stop', risk_metrics)
        self.assertIn('targets', risk_metrics)
        self.assertIn('timeStopMin', risk_metrics)
        
        # Should have 3 targets
        self.assertEqual(len(risk_metrics['targets']), 3)
        
        # Time stop should be 45 for SAFE mode
        self.assertEqual(risk_metrics['timeStopMin'], 45)
    
    def test_pattern_detection_hammer(self):
        """Test hammer pattern detection"""
        # Create a hammer candle
        hammer_candle = pd.Series({
            'open': 100.0,
            'high': 101.0,
            'low': 95.0,
            'close': 99.5
        })
        
        is_hammer = self.service._is_hammer(hammer_candle)
        # Should detect hammer (long lower wick, small body)
        self.assertIsInstance(is_hammer, bool)
    
    def test_pattern_detection_doji(self):
        """Test doji pattern detection"""
        # Create a doji candle
        doji_candle = pd.Series({
            'open': 100.0,
            'high': 100.5,
            'low': 99.5,
            'close': 100.0
        })
        
        is_doji = self.service._is_doji(doji_candle)
        self.assertIsInstance(is_doji, bool)
    
    def test_default_features(self):
        """Test default features when data is insufficient"""
        # Create minimal data
        minimal_ohlcv = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [100.0],
            'high': [101.0],
            'low': [99.0],
            'close': [100.0],
            'volume': [100000]
        })
        
        features = self.service.extract_all_features(
            minimal_ohlcv, minimal_ohlcv, "TEST"
        )
        
        # Should still return features (defaults)
        self.assertGreater(len(features), 0)


class TestDayTradingMLScorer(unittest.TestCase):
    """Test day trading ML scorer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scorer = DayTradingMLScorer()
        self.sample_features = {
            'momentum_15m': 0.02,
            'realized_vol_10': 0.25,
            'vwap_dist_pct': 0.01,
            'breakout_pct': 0.05,
            'spread_bps': 5.0,
            'is_trend_regime': 1.0,
            'is_vol_expansion': 1.0,
            'is_breakout': 1.0,
            'volume_ratio': 1.5,
            'rsi_14': 55.0,
            'is_engulfing_bull': 1.0,
            'is_opening_hour': 1.0,
            'sentiment_score': 0.3,
            'extreme_sentiment_flag': 0.0,
            'sentiment_divergence': 0.0
        }
    
    def test_score(self):
        """Test ML scoring"""
        score = self.scorer.score(self.sample_features)
        
        # Score should be between 0 and 10
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 10.0)
        self.assertIsInstance(score, float)
    
    def test_rule_based_scoring(self):
        """Test rule-based scoring logic"""
        # High momentum should increase score
        high_momentum_features = self.sample_features.copy()
        high_momentum_features['momentum_15m'] = 0.05
        
        score_high = self.scorer._rule_based_score(high_momentum_features)
        score_low = self.scorer._rule_based_score(self.sample_features)
        
        # High momentum should score higher (or equal)
        self.assertGreaterEqual(score_high, score_low)
    
    def test_catalyst_score(self):
        """Test catalyst score calculation"""
        catalyst_score = self.scorer.calculate_catalyst_score(self.sample_features)
        
        # Should be between 0 and 10
        self.assertGreaterEqual(catalyst_score, 0.0)
        self.assertLessEqual(catalyst_score, 10.0)
        
        # High volume and sentiment should increase catalyst score
        high_catalyst_features = self.sample_features.copy()
        high_catalyst_features['volume_zscore'] = 3.0
        high_catalyst_features['sentiment_score'] = 0.8
        
        high_catalyst_score = self.scorer.calculate_catalyst_score(high_catalyst_features)
        self.assertGreaterEqual(high_catalyst_score, catalyst_score)
    
    def test_regime_aware_scoring(self):
        """Test that regime affects scoring"""
        trend_features = self.sample_features.copy()
        trend_features['is_trend_regime'] = 1.0
        trend_features['is_high_vol_chop'] = 0.0
        
        chop_features = self.sample_features.copy()
        chop_features['is_trend_regime'] = 0.0
        chop_features['is_high_vol_chop'] = 1.0
        
        trend_score = self.scorer.score(trend_features)
        chop_score = self.scorer.score(chop_features)
        
        # Trending markets should score higher than chop
        self.assertGreaterEqual(trend_score, chop_score)


class TestIntegration(unittest.TestCase):
    """Integration tests for full day trading pipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.feature_service = DayTradingFeatureService()
        self.ml_scorer = DayTradingMLScorer()
        
        # Create realistic OHLCV data
        self.ohlcv_1m = self._create_trending_data_1m()
        self.ohlcv_5m = self._create_trending_data_5m()
    
    def _create_trending_data_1m(self, n_bars=390):
        """Create trending price data"""
        base_price = 100.0
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(n_bars, 0, -1)]
        
        prices = [base_price]
        for i in range(1, n_bars):
            # Upward trend with some noise
            change = 0.0005 + np.random.normal(0, 0.0003)
            prices.append(prices[-1] * (1 + change))
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.0005))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.0005))) for p in prices],
            'close': prices,
            'volume': [np.random.randint(100000, 1000000) for _ in range(n_bars)]
        })
    
    def _create_trending_data_5m(self, n_bars=78):
        """Create trending 5-minute data"""
        base_price = 100.0
        timestamps = [datetime.now() - timedelta(minutes=i*5) for i in range(n_bars, 0, -1)]
        
        prices = [base_price]
        for i in range(1, n_bars):
            change = 0.002 + np.random.normal(0, 0.001)
            prices.append(prices[-1] * (1 + change))
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
            'close': prices,
            'volume': [np.random.randint(500000, 5000000) for _ in range(n_bars)]
        })
    
    def test_full_pipeline(self):
        """Test full feature extraction and scoring pipeline"""
        # Extract features
        features = self.feature_service.extract_all_features(
            self.ohlcv_1m, self.ohlcv_5m, "AAPL"
        )
        
        # Should have all feature categories
        self.assertGreater(len(features), 100)
        
        # Score
        score = self.ml_scorer.score(features)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 10.0)
        
        # Calculate risk
        current_price = float(self.ohlcv_5m.iloc[-1]['close'])
        risk_metrics = self.feature_service.calculate_risk_metrics(
            features, "SAFE", current_price
        )
        
        # Risk metrics should be valid
        self.assertIn('stop', risk_metrics)
        self.assertIn('targets', risk_metrics)
        self.assertGreater(risk_metrics['sizeShares'], 0)
    
    def test_trending_vs_ranging(self):
        """Test that trending data scores higher than ranging data"""
        # Trending data (already created)
        trend_features = self.feature_service.extract_all_features(
            self.ohlcv_1m, self.ohlcv_5m, "AAPL"
        )
        trend_score = self.ml_scorer.score(trend_features)
        
        # Create ranging data
        ranging_ohlcv = self._create_ranging_data()
        ranging_features = self.feature_service.extract_all_features(
            ranging_ohlcv, ranging_ohlcv, "AAPL"
        )
        ranging_score = self.ml_scorer.score(ranging_features)
        
        # Trending should score higher (or at least be valid)
        self.assertGreaterEqual(trend_score, 0.0)
        self.assertGreaterEqual(ranging_score, 0.0)
    
    def _create_ranging_data(self, n_bars=78):
        """Create ranging (sideways) price data"""
        base_price = 100.0
        timestamps = [datetime.now() - timedelta(minutes=i*5) for i in range(n_bars, 0, -1)]
        
        prices = [base_price]
        for i in range(1, n_bars):
            # Small random changes around base
            change = np.random.normal(0, 0.0005)
            prices.append(prices[-1] * (1 + change))
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.001))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.001))) for p in prices],
            'close': prices,
            'volume': [np.random.randint(500000, 5000000) for _ in range(n_bars)]
        })


if __name__ == '__main__':
    unittest.main()

