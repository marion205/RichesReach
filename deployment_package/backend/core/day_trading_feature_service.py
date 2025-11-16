"""
Day Trading Feature Service
Implements features from "Day Trading 101" (Joe Duarte) and "The Ultimate Day Trader" (Jacob Bernstein)
Converts trading book concepts into ML-ready features
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import math

logger = logging.getLogger(__name__)


class DayTradingFeatureService:
    """
    Extracts day trading features from OHLCV data based on proven trading strategies.
    Combines concepts from both trading books into quantifiable ML features.
    """
    
    def __init__(self):
        """Initialize the feature service"""
        self.pattern_cache = {}  # Cache pattern detection results
    
    def extract_all_features(
        self,
        ohlcv_1m: pd.DataFrame,
        ohlcv_5m: pd.DataFrame,
        symbol: str,
        sentiment_data: Optional[Dict] = None,
        current_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Extract all features for a symbol at current time.
        
        Args:
            ohlcv_1m: 1-minute OHLCV data (last 390 bars = 6.5 hours)
            ohlcv_5m: 5-minute OHLCV data (last 78 bars = 6.5 hours)
            symbol: Stock symbol
            sentiment_data: Optional sentiment data from social feeds
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Dictionary of all features (100+ features)
        """
        if current_time is None:
            current_time = datetime.now()
        
        features = {}
        
        # Ensure we have enough data
        if len(ohlcv_1m) < 20 or len(ohlcv_5m) < 20:
            logger.warning(f"Insufficient data for {symbol}: 1m={len(ohlcv_1m)}, 5m={len(ohlcv_5m)}")
            return self._get_default_features()
        
        # Use most recent data
        ohlcv_1m = ohlcv_1m.tail(390).copy()
        ohlcv_5m = ohlcv_5m.tail(78).copy()
        
        # 1. Candlestick Pattern Features (Day Trading 101)
        features.update(self._extract_candlestick_features(ohlcv_5m))
        
        # 2. Classic Technical Indicators (Day Trading 101)
        features.update(self._extract_technical_indicators(ohlcv_5m))
        
        # 3. Volatility & Breakout Features (Ultimate Day Trader)
        features.update(self._extract_volatility_features(ohlcv_5m))
        
        # 4. Regime Detection (Ultimate Day Trader)
        features.update(self._detect_market_regime(ohlcv_5m))
        
        # 5. Time-of-Day Features (Ultimate Day Trader)
        features.update(self._extract_time_features(current_time))
        
        # 6. Sentiment Features (Ultimate Day Trader - Sentiment Index)
        if sentiment_data:
            features.update(self._extract_sentiment_features(sentiment_data))
        else:
            features.update(self._get_default_sentiment_features())
        
        # 7. Momentum & Volume Features
        features.update(self._extract_momentum_features(ohlcv_1m, ohlcv_5m))
        
        # 8. VWAP Features
        features.update(self._extract_vwap_features(ohlcv_5m))
        
        # 9. Spread & Liquidity Features
        features.update(self._extract_liquidity_features(ohlcv_5m))
        
        # 10. Risk Management Features (Day Trading 101)
        features.update(self._extract_risk_features(ohlcv_5m))
        
        return features
    
    def _extract_candlestick_features(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Extract candlestick pattern features from "Day Trading 101"
        Returns binary flags and ratios for pattern detection
        """
        if len(ohlcv) < 2:
            return self._get_default_candlestick_features()
        
        features = {}
        latest = ohlcv.iloc[-1]
        prev = ohlcv.iloc[-2] if len(ohlcv) >= 2 else latest
        
        open_price = float(latest['open'])
        high_price = float(latest['high'])
        low_price = float(latest['low'])
        close_price = float(latest['close'])
        prev_close = float(prev['close'])
        
        # Body and wick ratios
        body = abs(close_price - open_price)
        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price
        total_range = high_price - low_price
        
        if open_price > 0:
            features['body_pct'] = body / open_price
            features['upper_wick_pct'] = upper_wick / open_price if upper_wick > 0 else 0.0
            features['lower_wick_pct'] = lower_wick / open_price if lower_wick > 0 else 0.0
            features['range_pct'] = total_range / open_price
        else:
            features['body_pct'] = 0.0
            features['upper_wick_pct'] = 0.0
            features['lower_wick_pct'] = 0.0
            features['range_pct'] = 0.0
        
        # Gap features
        if prev_close > 0:
            gap = open_price - prev_close
            features['gap_up_pct'] = max(0, gap / prev_close) if gap > 0 else 0.0
            features['gap_down_pct'] = abs(min(0, gap / prev_close)) if gap < 0 else 0.0
        else:
            features['gap_up_pct'] = 0.0
            features['gap_down_pct'] = 0.0
        
        # Pattern detection (binary flags)
        features['is_hammer'] = float(self._is_hammer(latest))
        features['is_shooting_star'] = float(self._is_shooting_star(latest))
        features['is_doji'] = float(self._is_doji(latest))
        features['is_engulfing_bull'] = float(self._is_bullish_engulfing(latest, prev))
        features['is_engulfing_bear'] = float(self._is_bearish_engulfing(latest, prev))
        features['is_marubozu'] = float(self._is_marubozu(latest))
        features['is_spinning_top'] = float(self._is_spinning_top(latest))
        features['is_hanging_man'] = float(self._is_hanging_man(latest, prev))
        features['is_inverted_hammer'] = float(self._is_inverted_hammer(latest))
        
        # Multi-bar patterns (need 3+ bars)
        if len(ohlcv) >= 3:
            features['is_three_white_soldiers'] = float(self._is_three_white_soldiers(ohlcv.tail(3)))
            features['is_three_black_crows'] = float(self._is_three_black_crows(ohlcv.tail(3)))
        else:
            features['is_three_white_soldiers'] = 0.0
            features['is_three_black_crows'] = 0.0
        
        return features
    
    def _extract_technical_indicators(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Extract classic technical indicators from "Day Trading 101"
        """
        if len(ohlcv) < 20:
            return self._get_default_technical_features()
        
        features = {}
        closes = ohlcv['close'].values
        opens = ohlcv['open'].values
        highs = ohlcv['high'].values
        lows = ohlcv['low'].values
        volumes = ohlcv['volume'].values
        current_price = float(closes[-1])
        
        # Moving Averages
        features['sma_5'] = float(np.mean(closes[-5:])) if len(closes) >= 5 else current_price
        features['sma_10'] = float(np.mean(closes[-10:])) if len(closes) >= 10 else current_price
        features['sma_20'] = float(np.mean(closes[-20:])) if len(closes) >= 20 else current_price
        features['sma_50'] = float(np.mean(closes[-50:])) if len(closes) >= 50 else current_price
        
        # EMA (simplified - using weighted average)
        features['ema_12'] = float(self._calculate_ema(closes, 12))
        features['ema_26'] = float(self._calculate_ema(closes, 26))
        
        # MACD
        macd = features['ema_12'] - features['ema_26']
        features['macd'] = macd
        features['macd_signal'] = macd * 0.9  # Simplified signal line
        features['macd_hist'] = macd - features['macd_signal']
        
        # RSI
        features['rsi_14'] = float(self._calculate_rsi(closes, 14))
        
        # Bollinger Bands
        if len(closes) >= 20:
            sma_20 = features['sma_20']
            std_20 = float(np.std(closes[-20:]))
            features['bb_upper'] = sma_20 + (2 * std_20)
            features['bb_middle'] = sma_20
            features['bb_lower'] = sma_20 - (2 * std_20)
            features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / sma_20 if sma_20 > 0 else 0.0
            features['bb_position'] = (current_price - features['bb_lower']) / (features['bb_upper'] - features['bb_lower']) if (features['bb_upper'] - features['bb_lower']) > 0 else 0.5
        else:
            features['bb_upper'] = current_price * 1.02
            features['bb_middle'] = current_price
            features['bb_lower'] = current_price * 0.98
            features['bb_width'] = 0.04
            features['bb_position'] = 0.5
        
        # Stochastic Oscillator
        if len(closes) >= 14:
            high_14 = float(np.max(highs[-14:]))
            low_14 = float(np.min(lows[-14:]))
            if high_14 != low_14:
                features['stoch_k'] = ((current_price - low_14) / (high_14 - low_14)) * 100
            else:
                features['stoch_k'] = 50.0
            # Simplified %D (3-period SMA of %K)
            if len(closes) >= 17:
                k_values = [((closes[i] - float(np.min(lows[i-13:i+1]))) / (float(np.max(highs[i-13:i+1])) - float(np.min(lows[i-13:i+1]))) * 100) if (float(np.max(highs[i-13:i+1])) - float(np.min(lows[i-13:i+1]))) > 0 else 50.0 for i in range(-3, 0)]
                features['stoch_d'] = float(np.mean(k_values))
            else:
                features['stoch_d'] = features['stoch_k']
        else:
            features['stoch_k'] = 50.0
            features['stoch_d'] = 50.0
        
        # ATR (Average True Range)
        if len(ohlcv) >= 14:
            true_ranges = []
            for i in range(1, min(15, len(ohlcv))):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_ranges.append(max(tr1, tr2, tr3))
            features['atr_14'] = float(np.mean(true_ranges))
        else:
            features['atr_14'] = current_price * 0.02  # Default 2%
        
        # Volume features
        if len(volumes) >= 20:
            avg_volume = float(np.mean(volumes[-20:]))
            current_volume = float(volumes[-1])
            features['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1.0
            features['volume_zscore'] = (current_volume - avg_volume) / (float(np.std(volumes[-20:])) + 1e-6)
        else:
            features['volume_ratio'] = 1.0
            features['volume_zscore'] = 0.0
        
        # Indicator state flags
        features['price_above_sma20'] = 1.0 if current_price > features['sma_20'] else 0.0
        features['price_above_sma50'] = 1.0 if current_price > features['sma_50'] else 0.0
        features['sma20_above_sma50'] = 1.0 if features['sma_20'] > features['sma_50'] else 0.0
        features['rsi_overbought'] = 1.0 if features['rsi_14'] > 70 else 0.0
        features['rsi_oversold'] = 1.0 if features['rsi_14'] < 30 else 0.0
        features['price_at_bb_upper'] = 1.0 if current_price >= features['bb_upper'] * 0.995 else 0.0
        features['price_at_bb_lower'] = 1.0 if current_price <= features['bb_lower'] * 1.005 else 0.0
        
        return features
    
    def _extract_volatility_features(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Extract volatility and breakout features from "The Ultimate Day Trader"
        Bernstein's volatility expansion/contraction concepts
        """
        if len(ohlcv) < 20:
            return self._get_default_volatility_features()
        
        features = {}
        closes = ohlcv['close'].values
        highs = ohlcv['high'].values
        lows = ohlcv['low'].values
        current_price = float(closes[-1])
        
        # Realized volatility
        if len(closes) >= 20:
            returns = np.diff(closes[-20:]) / closes[-21:-1]
            features['realized_vol_20'] = float(np.std(returns)) * np.sqrt(252)  # Annualized
            features['realized_vol_10'] = float(np.std(returns[-10:])) * np.sqrt(252) if len(returns) >= 10 else features['realized_vol_20']
        else:
            features['realized_vol_20'] = 0.2  # Default 20% vol
            features['realized_vol_10'] = 0.2
        
        # ATR as percentage
        atr = self._calculate_atr(ohlcv, 14)
        features['atr_14_pct'] = atr / current_price if current_price > 0 else 0.02
        features['atr_5_pct'] = self._calculate_atr(ohlcv, 5) / current_price if current_price > 0 else 0.02
        
        # True range percentage
        latest = ohlcv.iloc[-1]
        features['true_range_pct'] = (float(latest['high']) - float(latest['low'])) / current_price if current_price > 0 else 0.0
        
        # Breakout strength (Bernstein's concept)
        if len(ohlcv) >= 20:
            prior_high_20 = float(np.max(highs[-20:]))
            prior_low_20 = float(np.min(lows[-20:]))
            prior_range_20 = prior_high_20 - prior_low_20
            
            if prior_range_20 > 0:
                features['breakout_pct'] = (current_price - prior_high_20) / prior_range_20
                features['breakdown_pct'] = (current_price - prior_low_20) / prior_range_20
            else:
                features['breakout_pct'] = 0.0
                features['breakdown_pct'] = 0.0
            
            # Prior range for context
            if len(ohlcv) >= 60:
                prior_range_60 = float(np.max(highs[-60:])) - float(np.min(lows[-60:]))
                features['range_compression'] = prior_range_20 / prior_range_60 if prior_range_60 > 0 else 1.0
            else:
                features['range_compression'] = 1.0
        else:
            features['breakout_pct'] = 0.0
            features['breakdown_pct'] = 0.0
            features['range_compression'] = 1.0
        
        # Volatility expansion flags
        if len(ohlcv) >= 50:
            atr_history = [self._calculate_atr(ohlcv.iloc[:i+14], 14) / float(ohlcv.iloc[i+13]['close']) 
                          for i in range(len(ohlcv) - 50, len(ohlcv) - 13)]
            if atr_history:
                atr_p80 = np.percentile(atr_history, 80)
                features['is_vol_expansion'] = 1.0 if features['atr_14_pct'] > atr_p80 else 0.0
            else:
                features['is_vol_expansion'] = 0.0
        else:
            features['is_vol_expansion'] = 0.0
        
        # Breakout flags
        features['is_breakout'] = 1.0 if features['breakout_pct'] > 0.1 else 0.0  # 10% above prior high
        features['is_breakdown'] = 1.0 if features['breakdown_pct'] < -0.1 else 0.0  # 10% below prior low
        
        return features
    
    def _detect_market_regime(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Detect market regime from "The Ultimate Day Trader"
        Classifies: trend_up, trend_down, range, high_vol_chop
        """
        if len(ohlcv) < 50:
            return self._get_default_regime_features()
        
        features = {}
        closes = ohlcv['close'].values
        current_price = float(closes[-1])
        
        # Calculate SMAs
        sma_20 = float(np.mean(closes[-20:]))
        sma_50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else sma_20
        
        # Trend strength
        trend_strength = abs(sma_20 - sma_50) / current_price if current_price > 0 else 0.0
        features['trend_strength'] = trend_strength
        
        # Range compression
        if len(ohlcv) >= 60:
            highs = ohlcv['high'].values
            lows = ohlcv['low'].values
            prior_range_20 = float(np.max(highs[-20:])) - float(np.min(lows[-20:]))
            prior_range_60 = float(np.max(highs[-60:])) - float(np.min(lows[-60:]))
            range_compression = prior_range_20 / prior_range_60 if prior_range_60 > 0 else 1.0
        else:
            range_compression = 1.0
        
        # ATR percentage
        atr_pct = self._calculate_atr(ohlcv, 14) / current_price if current_price > 0 else 0.02
        
        # Regime classification
        is_trending = trend_strength > 0.02  # 2% difference
        is_ranging = trend_strength < 0.01 and atr_pct < 0.015  # Low trend, low vol
        is_chop = atr_pct > 0.02 and trend_strength < 0.01  # High vol, low trend
        
        features['is_trend_regime'] = 1.0 if is_trending else 0.0
        features['is_range_regime'] = 1.0 if is_ranging else 0.0
        features['is_high_vol_chop'] = 1.0 if is_chop else 0.0
        
        # Trend direction
        price_vs_sma20 = (current_price - sma_20) / sma_20 if sma_20 > 0 else 0.0
        features['is_trend_up'] = 1.0 if price_vs_sma20 > 0.005 else 0.0  # 0.5% above SMA20
        features['is_trend_down'] = 1.0 if price_vs_sma20 < -0.005 else 0.0  # 0.5% below SMA20
        
        # Regime confidence
        if is_trending:
            features['regime_confidence'] = min(1.0, trend_strength * 10)  # Higher trend = higher confidence
        elif is_ranging:
            features['regime_confidence'] = 0.7  # Moderate confidence in range
        elif is_chop:
            features['regime_confidence'] = 0.3  # Low confidence in chop
        else:
            features['regime_confidence'] = 0.5  # Neutral
        
        return features
    
    def _extract_time_features(self, current_time: datetime) -> Dict[str, float]:
        """
        Extract time-of-day and seasonal features from "The Ultimate Day Trader"
        Bernstein's observation that certain times/days behave differently
        """
        features = {}
        
        # Day of week (0=Monday, 6=Sunday)
        dow = current_time.weekday()
        features['dow'] = float(dow)
        features['dom'] = float(current_time.day) / 31.0  # Day of month normalized
        
        # Hour of day
        hour = current_time.hour + (current_time.minute / 60.0)
        features['hour_of_day'] = hour / 24.0
        
        # Cyclical encoding (sin/cos for ML models)
        features['dow_sin'] = math.sin(2 * math.pi * dow / 7)
        features['dow_cos'] = math.cos(2 * math.pi * dow / 7)
        features['hour_sin'] = math.sin(2 * math.pi * hour / 24)
        features['hour_cos'] = math.cos(2 * math.pi * hour / 24)
        
        # Trading session flags
        features['is_opening_hour'] = 1.0 if 9.5 <= hour < 10.5 else 0.0  # 9:30-10:30
        features['is_closing_hour'] = 1.0 if 15.5 <= hour < 16.0 else 0.0  # 3:30-4:00
        features['is_midday'] = 1.0 if 12.0 <= hour < 14.0 else 0.0  # 12:00-2:00
        features['is_pre_market'] = 1.0 if 4.0 <= hour < 9.5 else 0.0  # 4:00-9:30
        features['is_after_hours'] = 1.0 if hour >= 16.0 or hour < 4.0 else 0.0
        
        # Day of month effects
        features['is_month_end'] = 1.0 if current_time.day >= 28 else 0.0
        features['is_month_start'] = 1.0 if current_time.day <= 3 else 0.0
        features['is_week_start'] = 1.0 if dow == 0 else 0.0  # Monday
        features['is_week_end'] = 1.0 if dow == 4 else 0.0  # Friday
        
        return features
    
    def _extract_sentiment_features(self, sentiment_data: Dict) -> Dict[str, float]:
        """
        Extract sentiment features from "The Ultimate Day Trader"
        Bernstein's Daily Sentiment Index concept
        """
        features = {}
        
        # Basic sentiment score
        features['sentiment_score'] = float(sentiment_data.get('score', 0.0))  # -1 to 1
        features['sentiment_volume'] = float(sentiment_data.get('message_count', 0))
        
        # Bull/bear ratio
        bull_count = float(sentiment_data.get('bull_count', 0))
        bear_count = float(sentiment_data.get('bear_count', 0))
        neutral_count = float(sentiment_data.get('neutral_count', 0))
        total = bull_count + bear_count + neutral_count
        
        if total > 0:
            features['bull_ratio'] = bull_count / total
            features['bear_ratio'] = bear_count / total
        else:
            features['bull_ratio'] = 0.5
            features['bear_ratio'] = 0.5
        
        # Extreme sentiment flags (crowd psychology)
        features['extreme_sentiment_flag'] = 1.0 if (features['bull_ratio'] > 0.85 or features['bull_ratio'] < 0.15) else 0.0
        features['extreme_bullish'] = 1.0 if features['bull_ratio'] > 0.85 else 0.0
        features['extreme_bearish'] = 1.0 if features['bull_ratio'] < 0.15 else 0.0
        
        # Sentiment divergence (price vs sentiment)
        price_trend = float(sentiment_data.get('price_trend', 0.0))  # Recent price change
        sentiment_trend = features['sentiment_score']
        features['sentiment_divergence'] = 1.0 if (price_trend * sentiment_trend < 0) else 0.0  # Opposite directions
        
        return features
    
    def _extract_momentum_features(self, ohlcv_1m: pd.DataFrame, ohlcv_5m: pd.DataFrame) -> Dict[str, float]:
        """
        Extract momentum features for day trading
        """
        features = {}
        
        # 15-minute momentum (from frontend expectation)
        if len(ohlcv_5m) >= 3:  # 3 * 5min = 15min
            closes_5m = ohlcv_5m['close'].values
            features['momentum_15m'] = (closes_5m[-1] - closes_5m[-3]) / closes_5m[-3] if closes_5m[-3] > 0 else 0.0
        else:
            features['momentum_15m'] = 0.0
        
        # 5-minute momentum
        if len(ohlcv_5m) >= 2:
            closes_5m = ohlcv_5m['close'].values
            features['momentum_5m'] = (closes_5m[-1] - closes_5m[-2]) / closes_5m[-2] if closes_5m[-2] > 0 else 0.0
        else:
            features['momentum_5m'] = 0.0
        
        # 1-minute momentum
        if len(ohlcv_1m) >= 2:
            closes_1m = ohlcv_1m['close'].values
            features['momentum_1m'] = (closes_1m[-1] - closes_1m[-2]) / closes_1m[-2] if closes_1m[-2] > 0 else 0.0
        else:
            features['momentum_1m'] = 0.0
        
        # Rate of Change (ROC)
        if len(ohlcv_5m) >= 10:
            closes_5m = ohlcv_5m['close'].values
            features['roc_10'] = (closes_5m[-1] - closes_5m[-10]) / closes_5m[-10] if closes_5m[-10] > 0 else 0.0
        else:
            features['roc_10'] = 0.0
        
        return features
    
    def _extract_vwap_features(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Extract VWAP (Volume Weighted Average Price) features
        """
        if len(ohlcv) < 2:
            return {'vwap': 0.0, 'vwap_dist': 0.0, 'vwap_dist_pct': 0.0}
        
        features = {}
        current_price = float(ohlcv.iloc[-1]['close'])
        
        # Calculate VWAP (typically for the day, but we'll use available data)
        typical_price = (ohlcv['high'] + ohlcv['low'] + ohlcv['close']) / 3
        vwap = (typical_price * ohlcv['volume']).sum() / ohlcv['volume'].sum() if ohlcv['volume'].sum() > 0 else current_price
        
        features['vwap'] = float(vwap)
        features['vwap_dist'] = current_price - vwap
        features['vwap_dist_pct'] = (current_price - vwap) / vwap if vwap > 0 else 0.0
        
        # VWAP position
        if len(ohlcv) >= 20:
            vwap_20 = (typical_price[-20:] * ohlcv['volume'].iloc[-20:]).sum() / ohlcv['volume'].iloc[-20:].sum()
            features['vwap_dist_20'] = current_price - float(vwap_20)
            features['vwap_dist_pct_20'] = (current_price - float(vwap_20)) / float(vwap_20) if vwap_20 > 0 else 0.0
        else:
            features['vwap_dist_20'] = features['vwap_dist']
            features['vwap_dist_pct_20'] = features['vwap_dist_pct']
        
        return features
    
    def _extract_liquidity_features(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Extract spread and liquidity features
        """
        features = {}
        
        # Spread (bid-ask spread in basis points)
        # We'll estimate from high-low range
        if len(ohlcv) >= 1:
            latest = ohlcv.iloc[-1]
            high = float(latest['high'])
            low = float(latest['low'])
            close = float(latest['close'])
            
            # Estimate spread as % of price (typical intraday spread)
            estimated_spread = (high - low) / close if close > 0 else 0.0
            features['spread_bps'] = estimated_spread * 10000  # Convert to basis points
        else:
            features['spread_bps'] = 5.0  # Default 5 bps
        
        # Volume-based liquidity
        if len(ohlcv) >= 20:
            volumes = ohlcv['volume'].values
            avg_volume = float(np.mean(volumes[-20:]))
            features['liquidity_score'] = min(1.0, avg_volume / 1000000)  # Normalize to 1M shares
        else:
            features['liquidity_score'] = 0.5
        
        return features
    
    def _extract_risk_features(self, ohlcv: pd.DataFrame) -> Dict[str, float]:
        """
        Extract risk management features from "Day Trading 101"
        """
        if len(ohlcv) < 5:
            return {'atr_5m': 0.0, 'risk_per_trade_pct': 0.005}
        
        features = {}
        current_price = float(ohlcv.iloc[-1]['close'])
        
        # ATR for 5-minute bars (for day trading)
        features['atr_5m'] = self._calculate_atr(ohlcv.tail(5), 5)
        features['atr_5m_pct'] = features['atr_5m'] / current_price if current_price > 0 else 0.01
        
        # Risk per trade (from book: 0.5% for SAFE, 1.2% for AGGRESSIVE)
        features['risk_per_trade_pct'] = 0.005  # Default 0.5%
        
        # Position sizing (volatility-normalized)
        if features['atr_5m'] > 0:
            features['vol_norm_size'] = features['risk_per_trade_pct'] / features['atr_5m_pct']
        else:
            features['vol_norm_size'] = 1.0
        
        # Risk/reward ratio
        features['risk_reward_ratio'] = 2.0  # Default 2:1 R:R
        
        return features
    
    def calculate_risk_metrics(
        self,
        features: Dict[str, float],
        mode: str = "SAFE",
        current_price: float = 100.0
    ) -> Dict[str, Any]:
        """
        Calculate risk metrics for a trade (stop, targets, position size)
        Based on "Day Trading 101" risk management rules
        """
        atr_5m = features.get('atr_5m', current_price * 0.01)
        atr_5m_pct = features.get('atr_5m_pct', 0.01)
        
        # Risk per trade based on mode
        risk_pct = 0.005 if mode == "SAFE" else 0.012  # 0.5% or 1.2%
        
        # Stop loss (1.5x ATR for SAFE, 2x ATR for AGGRESSIVE)
        stop_multiplier = 1.5 if mode == "SAFE" else 2.0
        stop_distance = atr_5m * stop_multiplier
        stop_pct = atr_5m_pct * stop_multiplier
        
        # Determine side (LONG or SHORT)
        momentum = features.get('momentum_15m', 0.0)
        side = 'LONG' if momentum > 0 else 'SHORT'
        
        if side == 'LONG':
            stop_price = current_price - stop_distance
            # Targets (2:1, 3:1, 4:1 R:R)
            target1 = current_price + (stop_distance * 2)
            target2 = current_price + (stop_distance * 3)
            target3 = current_price + (stop_distance * 4)
        else:
            stop_price = current_price + stop_distance
            target1 = current_price - (stop_distance * 2)
            target2 = current_price - (stop_distance * 3)
            target3 = current_price - (stop_distance * 4)
        
        # Position sizing
        risk_amount = current_price * risk_pct
        shares = int(risk_amount / stop_distance) if stop_distance > 0 else 0
        
        # Time stop (from book: 45min for SAFE, 25min for AGGRESSIVE)
        time_stop_min = 45 if mode == "SAFE" else 25
        
        return {
            'atr5m': float(atr_5m),
            'sizeShares': shares,
            'stop': float(stop_price),
            'targets': [float(target1), float(target2), float(target3)],
            'timeStopMin': time_stop_min
        }
    
    # Helper methods for pattern detection
    
    def _is_hammer(self, candle: pd.Series) -> bool:
        """Detect hammer pattern"""
        body = abs(float(candle['close']) - float(candle['open']))
        lower_wick = min(float(candle['open']), float(candle['close'])) - float(candle['low'])
        upper_wick = float(candle['high']) - max(float(candle['open']), float(candle['close']))
        total_range = float(candle['high']) - float(candle['low'])
        
        if total_range == 0:
            return False
        
        return (lower_wick > 2 * body) and (upper_wick < body * 0.5) and (body > 0)
    
    def _is_shooting_star(self, candle: pd.Series) -> bool:
        """Detect shooting star pattern"""
        body = abs(float(candle['close']) - float(candle['open']))
        upper_wick = float(candle['high']) - max(float(candle['open']), float(candle['close']))
        lower_wick = min(float(candle['open']), float(candle['close'])) - float(candle['low'])
        total_range = float(candle['high']) - float(candle['low'])
        
        if total_range == 0:
            return False
        
        return (upper_wick > 2 * body) and (lower_wick < body * 0.5) and (body > 0)
    
    def _is_doji(self, candle: pd.Series) -> bool:
        """Detect doji pattern"""
        body = abs(float(candle['close']) - float(candle['open']))
        total_range = float(candle['high']) - float(candle['low'])
        
        if total_range == 0:
            return False
        
        return body < (total_range * 0.1)  # Body is less than 10% of range
    
    def _is_bullish_engulfing(self, current: pd.Series, prev: pd.Series) -> bool:
        """Detect bullish engulfing pattern"""
        prev_body = float(prev['close']) - float(prev['open'])
        curr_body = float(current['close']) - float(current['open'])
        
        return (prev_body < 0) and (curr_body > 0) and \
               (float(current['open']) < float(prev['close'])) and \
               (float(current['close']) > float(prev['open']))
    
    def _is_bearish_engulfing(self, current: pd.Series, prev: pd.Series) -> bool:
        """Detect bearish engulfing pattern"""
        prev_body = float(prev['close']) - float(prev['open'])
        curr_body = float(current['close']) - float(current['open'])
        
        return (prev_body > 0) and (curr_body < 0) and \
               (float(current['open']) > float(prev['close'])) and \
               (float(current['close']) < float(prev['open']))
    
    def _is_marubozu(self, candle: pd.Series) -> bool:
        """Detect marubozu pattern (no wicks)"""
        body = abs(float(candle['close']) - float(candle['open']))
        total_range = float(candle['high']) - float(candle['low'])
        
        if total_range == 0:
            return False
        
        return body > (total_range * 0.95)  # Body is 95%+ of range
    
    def _is_spinning_top(self, candle: pd.Series) -> bool:
        """Detect spinning top pattern"""
        body = abs(float(candle['close']) - float(candle['open']))
        upper_wick = float(candle['high']) - max(float(candle['open']), float(candle['close']))
        lower_wick = min(float(candle['open']), float(candle['close'])) - float(candle['low'])
        total_range = float(candle['high']) - float(candle['low'])
        
        if total_range == 0:
            return False
        
        return (body < total_range * 0.3) and (upper_wick > body) and (lower_wick > body)
    
    def _is_hanging_man(self, candle: pd.Series, prev: pd.Series) -> bool:
        """Detect hanging man pattern (bearish reversal)"""
        body = abs(float(candle['close']) - float(candle['open']))
        lower_wick = min(float(candle['open']), float(candle['close'])) - float(candle['low'])
        total_range = float(candle['high']) - float(candle['low'])
        prev_close = float(prev['close'])
        curr_close = float(candle['close'])
        
        if total_range == 0:
            return False
        
        # Hanging man: small body, long lower wick, at top of uptrend
        is_at_top = curr_close > prev_close
        return is_at_top and (lower_wick > 2 * body) and (body < total_range * 0.3)
    
    def _is_inverted_hammer(self, candle: pd.Series) -> bool:
        """Detect inverted hammer pattern"""
        body = abs(float(candle['close']) - float(candle['open']))
        upper_wick = float(candle['high']) - max(float(candle['open']), float(candle['close']))
        lower_wick = min(float(candle['open']), float(candle['close'])) - float(candle['low'])
        total_range = float(candle['high']) - float(candle['low'])
        
        if total_range == 0:
            return False
        
        return (upper_wick > 2 * body) and (lower_wick < body * 0.5) and (body > 0)
    
    def _is_three_white_soldiers(self, candles: pd.DataFrame) -> bool:
        """Detect three white soldiers pattern (bullish)"""
        if len(candles) < 3:
            return False
        
        bodies = [float(candles.iloc[i]['close']) - float(candles.iloc[i]['open']) 
                 for i in range(-3, 0)]
        closes = [float(candles.iloc[i]['close']) for i in range(-3, 0)]
        
        return all(b > 0 for b in bodies) and \
               all(closes[i] > closes[i-1] for i in range(1, 3)) and \
               all(closes[i] > float(candles.iloc[i-3+i]['open']) for i in range(3))
    
    def _is_three_black_crows(self, candles: pd.DataFrame) -> bool:
        """Detect three black crows pattern (bearish)"""
        if len(candles) < 3:
            return False
        
        bodies = [float(candles.iloc[i]['close']) - float(candles.iloc[i]['open']) 
                 for i in range(-3, 0)]
        closes = [float(candles.iloc[i]['close']) for i in range(-3, 0)]
        
        return all(b < 0 for b in bodies) and \
               all(closes[i] < closes[i-1] for i in range(1, 3)) and \
               all(closes[i] < float(candles.iloc[i-3+i]['open']) for i in range(3))
    
    # Technical indicator calculations
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return float(np.mean(prices))
        
        # Simple EMA calculation
        multiplier = 2.0 / (period + 1)
        ema = float(prices[0])
        for price in prices[1:period]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains) if len(gains) > 0 else 0.0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    def _calculate_atr(self, ohlcv: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(ohlcv) < 2:
            return 0.0
        
        true_ranges = []
        for i in range(1, min(period + 1, len(ohlcv))):
            high = float(ohlcv.iloc[i]['high'])
            low = float(ohlcv.iloc[i]['low'])
            prev_close = float(ohlcv.iloc[i-1]['close'])
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            true_ranges.append(max(tr1, tr2, tr3))
        
        return float(np.mean(true_ranges)) if true_ranges else 0.0
    
    # Default feature methods (for when data is insufficient)
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default features when data is insufficient"""
        features = {}
        features.update(self._get_default_candlestick_features())
        features.update(self._get_default_technical_features())
        features.update(self._get_default_volatility_features())
        features.update(self._get_default_regime_features())
        features.update(self._get_default_sentiment_features())
        features.update({
            'momentum_15m': 0.0,
            'momentum_5m': 0.0,
            'momentum_1m': 0.0,
            'roc_10': 0.0,
            'vwap': 0.0,
            'vwap_dist': 0.0,
            'vwap_dist_pct': 0.0,
            'spread_bps': 5.0,
            'liquidity_score': 0.5,
            'atr_5m': 0.0,
            'risk_per_trade_pct': 0.005
        })
        return features
    
    def _get_default_candlestick_features(self) -> Dict[str, float]:
        return {
            'body_pct': 0.0, 'upper_wick_pct': 0.0, 'lower_wick_pct': 0.0, 'range_pct': 0.0,
            'gap_up_pct': 0.0, 'gap_down_pct': 0.0,
            'is_hammer': 0.0, 'is_shooting_star': 0.0, 'is_doji': 0.0,
            'is_engulfing_bull': 0.0, 'is_engulfing_bear': 0.0, 'is_marubozu': 0.0,
            'is_spinning_top': 0.0, 'is_hanging_man': 0.0, 'is_inverted_hammer': 0.0,
            'is_three_white_soldiers': 0.0, 'is_three_black_crows': 0.0
        }
    
    def _get_default_technical_features(self) -> Dict[str, float]:
        return {
            'sma_5': 0.0, 'sma_10': 0.0, 'sma_20': 0.0, 'sma_50': 0.0,
            'ema_12': 0.0, 'ema_26': 0.0,
            'macd': 0.0, 'macd_signal': 0.0, 'macd_hist': 0.0,
            'rsi_14': 50.0,
            'bb_upper': 0.0, 'bb_middle': 0.0, 'bb_lower': 0.0, 'bb_width': 0.0, 'bb_position': 0.5,
            'stoch_k': 50.0, 'stoch_d': 50.0,
            'atr_14': 0.0,
            'volume_ratio': 1.0, 'volume_zscore': 0.0,
            'price_above_sma20': 0.0, 'price_above_sma50': 0.0, 'sma20_above_sma50': 0.0,
            'rsi_overbought': 0.0, 'rsi_oversold': 0.0,
            'price_at_bb_upper': 0.0, 'price_at_bb_lower': 0.0
        }
    
    def _get_default_volatility_features(self) -> Dict[str, float]:
        return {
            'realized_vol_20': 0.2, 'realized_vol_10': 0.2,
            'atr_14_pct': 0.02, 'atr_5_pct': 0.02, 'true_range_pct': 0.0,
            'breakout_pct': 0.0, 'breakdown_pct': 0.0, 'range_compression': 1.0,
            'is_vol_expansion': 0.0, 'is_breakout': 0.0, 'is_breakdown': 0.0
        }
    
    def _get_default_regime_features(self) -> Dict[str, float]:
        return {
            'trend_strength': 0.0,
            'is_trend_regime': 0.0, 'is_range_regime': 0.0, 'is_high_vol_chop': 0.0,
            'is_trend_up': 0.0, 'is_trend_down': 0.0,
            'regime_confidence': 0.5
        }
    
    def _get_default_sentiment_features(self) -> Dict[str, float]:
        return {
            'sentiment_score': 0.0, 'sentiment_volume': 0.0,
            'bull_ratio': 0.5, 'bear_ratio': 0.5,
            'extreme_sentiment_flag': 0.0, 'extreme_bullish': 0.0, 'extreme_bearish': 0.0,
            'sentiment_divergence': 0.0
        }

