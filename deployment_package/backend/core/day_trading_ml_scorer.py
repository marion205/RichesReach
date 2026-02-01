"""
Day Trading ML Scorer
Specialized ML model for day trading picks with book-based features
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import pickle
import os

logger = logging.getLogger(__name__)


class DayTradingMLScorer:
    """
    ML model scorer specifically for day trading.
    Uses features from both trading books to score intraday trading opportunities.
    """
    
    def __init__(self):
        """Initialize the ML scorer"""
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_version = "v1.0"
        self.ml_learner = None
        self.lstm_extractor = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize or load the ML model"""
        # Initialize LSTM feature extractor (hybrid approach)
        try:
            from .lstm_feature_extractor import get_lstm_feature_extractor
            self.lstm_extractor = get_lstm_feature_extractor()
            if self.lstm_extractor.is_available():
                logger.info("✅ LSTM feature extractor available (hybrid LSTM → Tree)")
        except Exception as e:
            logger.debug(f"LSTM feature extractor not available: {e}")
        
        # Try to use ML learner first (learns from past performance)
        try:
            from .day_trading_ml_learner import get_day_trading_ml_learner
            self.ml_learner = get_day_trading_ml_learner()
            if self.ml_learner.model is not None:
                logger.info("✅ Using ML learner model (learns from past performance)")
                return
        except Exception as e:
            logger.debug(f"ML learner not available: {e}")
        
        # Fallback: Try to load pre-trained model
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'models', 'day_trading_model.pkl')
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data.get('model')
                    self.scaler = model_data.get('scaler')
                    self.feature_names = model_data.get('feature_names')
                    logger.info("Loaded pre-trained day trading model")
                    return
        except Exception as e:
            logger.warning(f"Could not load pre-trained model: {e}")
        
        # Initialize with simple rule-based scoring as fallback
        logger.info("Using rule-based day trading scorer (ML model not available)")
        self.model = None
        self.scaler = None
    
    def score(self, features: Dict[str, float], mode: str = 'SAFE', side: str = 'LONG', price_data: Optional[pd.DataFrame] = None, symbol: Optional[str] = None) -> float:
        """
        Score a trading opportunity based on features.
        Uses ML learner if available (learns from past performance).
        Now includes LSTM features for hybrid approach (if available).
        
        Args:
            features: Dictionary of extracted features
            mode: 'SAFE' or 'AGGRESSIVE' (for ML learner)
            side: 'LONG' or 'SHORT' (for ML learner)
            price_data: Optional DataFrame with OHLCV data for LSTM feature extraction
            symbol: Optional symbol for LSTM feature extraction
        
        Returns:
            Score from 0.0 to 10.0 (higher = better opportunity)
        """
        # Enhance features with LSTM if available (hybrid approach)
        if self.lstm_extractor and self.lstm_extractor.is_available() and price_data is not None and symbol:
            try:
                lstm_features = self.lstm_extractor.extract_features(price_data, symbol)
                # Merge LSTM features into main features dict
                features = {**features, **lstm_features}
                logger.debug(f"🎯 LSTM features added for {symbol}: {len(lstm_features)} features")
            except Exception as e:
                logger.debug(f"LSTM feature extraction failed: {e}")
        
        # First, get base score from rule-based or static ML
        if self.model is not None and self.scaler is not None:
            base_score = self._ml_score(features)
        else:
            base_score = self._rule_based_score(features)
        
        # Enhance with ML learner if available (learns from past performance)
        if self.ml_learner and self.ml_learner.model is not None:
            try:
                # Add mode and side to features for ML learner
                features_with_meta = features.copy()
                features_with_meta['mode'] = mode
                features_with_meta['side'] = side
                features_with_meta['score'] = base_score
                
                # Enhance score using learned patterns
                enhanced_score = self.ml_learner.enhance_score_with_ml(base_score, features_with_meta)
                ml_prob = self.ml_learner.predict_success_probability(features_with_meta)
                logger.debug(f"🎯 ML-enhanced: base={base_score:.2f} → enhanced={enhanced_score:.2f} (ML prob={ml_prob:.2%})")
                return enhanced_score
            except Exception as e:
                logger.debug(f"ML learner enhancement failed: {e}, using base score")
                return base_score
        
        return base_score
    
    def _ml_score(self, features: Dict[str, float]) -> float:
        """Score using trained ML model"""
        try:
            # Convert features to array in correct order
            feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
            feature_array = feature_array.reshape(1, -1)
            
            # Scale features
            feature_scaled = self.scaler.transform(feature_array)
            
            # Predict
            prediction = self.model.predict(feature_scaled)[0]
            
            # Convert to 0-10 scale
            score = max(0.0, min(10.0, prediction * 10))
            return float(score)
        except Exception as e:
            logger.error(f"Error in ML scoring: {e}")
            return self._rule_based_score(features)
    
    def _rule_based_score(self, features: Dict[str, float]) -> float:
        """
        Enhanced rule-based scoring for better performance.
        Optimized to achieve >55% win rate and >0.5% avg return.
        """
        score = 0.0
        
        # 1. Momentum (15m) - CRITICAL: Strong momentum = higher win rate
        momentum_15m = features.get('momentum_15m', 0.0)
        momentum_strength = abs(momentum_15m)
        
        # Strong momentum is the #1 predictor of success
        if momentum_strength > 0.03:  # > 3% move = very strong
            score += 3.0
        elif momentum_strength > 0.02:  # > 2% move = strong
            score += 2.5
        elif momentum_strength > 0.01:  # > 1% move = moderate
            score += 1.5
        elif momentum_strength > 0.005:  # > 0.5% move = weak
            score += 0.5
        else:
            score -= 1.0  # No momentum = avoid
        
        # 2. Regime (CRITICAL: Only trade in good regimes)
        is_trend_regime = features.get('is_trend_regime', 0.0)
        is_range_regime = features.get('is_range_regime', 0.0)
        is_high_vol_chop = features.get('is_high_vol_chop', 0.0)
        regime_confidence = features.get('regime_confidence', 0.5)
        
        # Strong penalty for bad regimes
        if is_high_vol_chop > 0.5:
            score -= 2.0  # Strong penalty - avoid chop
            return max(0.0, score)  # Early exit for bad regimes
        
        if is_trend_regime > 0.5 and regime_confidence > 0.7:
            score += 3.0  # Strong trending market = best
        elif is_trend_regime > 0.5:
            score += 2.0  # Trending market = good
        elif is_range_regime > 0.5:
            score += 0.5  # Range = okay but not great
        else:
            score -= 0.5  # Unknown regime = risky
        
        # 3. Breakout strength (Bernstein) - High correlation with success
        breakout_pct = features.get('breakout_pct', 0.0)
        if breakout_pct > 0.15:  # Very strong breakout
            score += 3.0
        elif breakout_pct > 0.10:  # Strong breakout
            score += 2.5
        elif breakout_pct > 0.05:  # Moderate breakout
            score += 1.5
        elif breakout_pct > 0.02:  # Weak breakout
            score += 0.5
        
        # 4. Volatility expansion (Bernstein) - Good for entries
        is_vol_expansion = features.get('is_vol_expansion', 0.0)
        if is_vol_expansion > 0.5:
            score += 2.0  # Volatility expansion = opportunity
        
        # 5. Volume (CRITICAL: High volume = better execution)
        volume_ratio = features.get('volume_ratio', 1.0)
        volume_zscore = features.get('volume_zscore', 0.0)
        
        if volume_ratio > 2.5:  # Very high volume
            score += 2.5
        elif volume_ratio > 2.0:
            score += 2.0
        elif volume_ratio > 1.5:
            score += 1.0
        elif volume_ratio < 0.8:  # Low volume = avoid
            score -= 1.0
        
        # Volume z-score (statistical significance)
        if volume_zscore > 2.0:  # 2+ standard deviations above mean
            score += 1.5
        
        # 6. RSI (CRITICAL: Avoid extremes, prefer middle)
        rsi_14 = features.get('rsi_14', 50.0)
        if 40 < rsi_14 < 60:  # Sweet spot
            score += 2.0
        elif 30 < rsi_14 < 70:  # Acceptable range
            score += 1.0
        elif rsi_14 < 25 or rsi_14 > 75:  # Extreme = very risky
            score -= 2.0
        else:  # Near extremes
            score -= 1.0
        
        # 7. Candlestick patterns (Duarte) - Strong patterns = higher win rate
        is_three_white_soldiers = features.get('is_three_white_soldiers', 0.0)
        is_engulfing_bull = features.get('is_engulfing_bull', 0.0)
        is_engulfing_bear = features.get('is_engulfing_bear', 0.0)
        is_hammer = features.get('is_hammer', 0.0)
        is_doji = features.get('is_doji', 0.0)
        
        # Strong patterns
        if is_three_white_soldiers > 0.5:
            score += 2.5  # Very bullish pattern
        elif is_engulfing_bull > 0.5:
            score += 2.0  # Bullish reversal
        elif is_engulfing_bear > 0.5:
            score -= 1.0  # Bearish reversal (bad for longs)
        elif is_hammer > 0.5:
            score += 1.5  # Bullish reversal pattern
        elif is_doji > 0.5:
            score -= 0.5  # Indecision = avoid
        
        # 8. VWAP position (Price above VWAP = bullish momentum)
        vwap_dist_pct = features.get('vwap_dist_pct', 0.0)
        if vwap_dist_pct > 0.02:  # 2% above VWAP = strong
            score += 1.5
        elif vwap_dist_pct > 0.01:  # 1% above VWAP = good
            score += 1.0
        elif vwap_dist_pct < -0.01:  # Below VWAP = weak
            score -= 0.5
        
        # 9. MACD (Trend confirmation)
        macd_hist = features.get('macd_hist', 0.0)
        if macd_hist > 0.1:  # Strong bullish momentum
            score += 1.5
        elif macd_hist > 0:
            score += 0.5
        elif macd_hist < -0.1:  # Strong bearish momentum
            score -= 1.0
        
        # 10. Bollinger Bands (Mean reversion or breakout)
        bb_position = features.get('bb_position', 0.5)
        price_at_bb_upper = features.get('price_at_bb_upper', 0.0)
        price_at_bb_lower = features.get('price_at_bb_lower', 0.0)
        
        if price_at_bb_lower > 0.5:  # Oversold = potential bounce
            score += 1.0
        elif price_at_bb_upper > 0.5:  # Overbought = risky
            score -= 0.5
        elif 0.3 < bb_position < 0.7:  # Middle = good
            score += 0.5
        
        # 11. Sentiment divergence (Contrarian opportunity)
        sentiment_divergence = features.get('sentiment_divergence', 0.0)
        if sentiment_divergence > 0.5:
            score += 1.5  # Price and sentiment diverge = opportunity
        
        # 12. Time of day (Opening/closing hours have more opportunity)
        is_opening_hour = features.get('is_opening_hour', 0.0)
        is_closing_hour = features.get('is_closing_hour', 0.0)
        is_midday = features.get('is_midday', 0.0)
        
        if is_opening_hour > 0.5:  # Opening hour = high volatility
            score += 1.0
        elif is_closing_hour > 0.5:  # Closing hour = momentum
            score += 0.5
        elif is_midday > 0.5:  # Midday = often choppy
            score -= 0.5
        
        # 13. Trend strength (Stronger trends = better)
        trend_strength = features.get('trend_strength', 0.0)
        if trend_strength > 0.03:  # Very strong trend
            score += 1.5
        elif trend_strength > 0.02:  # Strong trend
            score += 1.0
        
        # 14. Price position vs SMAs (Trend confirmation)
        price_above_sma20 = features.get('price_above_sma20', 0.0)
        price_above_sma50 = features.get('price_above_sma50', 0.0)
        sma20_above_sma50 = features.get('sma20_above_sma50', 0.0)
        
        if price_above_sma20 > 0.5 and price_above_sma50 > 0.5 and sma20_above_sma50 > 0.5:
            score += 2.0  # Strong uptrend
        elif price_above_sma20 > 0.5:
            score += 1.0  # Above short-term MA
        
        # 15. Quality filters (Penalize low-quality setups)
        # Low momentum + low volume + no pattern = bad
        if momentum_strength < 0.005 and volume_ratio < 1.2 and is_engulfing_bull < 0.5:
            score -= 2.0  # Low quality setup
        
        # Normalize to 0-10 scale
        score = max(0.0, min(10.0, score))
        
        return float(score)
    
    def calculate_catalyst_score(self, features: Dict[str, float]) -> float:
        """
        Enhanced catalyst score for better trade selection
        """
        score = 0.0
        
        # Sentiment (strong sentiment = catalyst)
        sentiment_score = features.get('sentiment_score', 0.0)
        sentiment_volume = features.get('sentiment_volume', 0.0)
        
        if abs(sentiment_score) > 0.5:  # Strong sentiment
            score += 3.0
        elif abs(sentiment_score) > 0.3:
            score += 2.0
        
        if sentiment_volume > 100:  # High sentiment volume
            score += 1.0
        
        # Volume spike (CRITICAL: Volume confirms catalysts)
        volume_zscore = features.get('volume_zscore', 0.0)
        volume_ratio = features.get('volume_ratio', 1.0)
        
        if volume_zscore > 3.0:  # Extreme volume spike
            score += 3.0
        elif volume_zscore > 2.0:
            score += 2.5
        elif volume_zscore > 1.0:
            score += 1.5
        
        if volume_ratio > 3.0:  # 3x average volume
            score += 2.0
        elif volume_ratio > 2.0:
            score += 1.5
        
        # Breakout (strong breakout = catalyst)
        breakout_pct = features.get('breakout_pct', 0.0)
        if breakout_pct > 0.15:
            score += 3.0
        elif breakout_pct > 0.10:
            score += 2.0
        elif breakout_pct > 0.05:
            score += 1.0
        
        if features.get('is_breakout', 0.0) > 0.5:
            score += 1.5
        
        # Pattern (strong patterns = catalysts)
        if features.get('is_three_white_soldiers', 0.0) > 0.5:
            score += 2.5  # Very strong pattern
        elif features.get('is_engulfing_bull', 0.0) > 0.5:
            score += 2.0
        elif features.get('is_engulfing_bear', 0.0) > 0.5:
            score += 1.5
        elif features.get('is_hammer', 0.0) > 0.5:
            score += 1.0
        
        # Volatility expansion (volatility spike = catalyst)
        if features.get('is_vol_expansion', 0.0) > 0.5:
            score += 1.5
        
        # Momentum (strong momentum = catalyst)
        momentum = abs(features.get('momentum_15m', 0.0))
        if momentum > 0.03:
            score += 2.0
        elif momentum > 0.02:
            score += 1.5
        
        return min(10.0, score)

