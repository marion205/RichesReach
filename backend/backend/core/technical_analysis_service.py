"""
Technical Analysis Service for Enhanced Stock Scoring
Provides comprehensive technical indicators and pattern recognition
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TechnicalAnalysisService:
    """
    Service for calculating technical indicators and patterns
    """
    
    def __init__(self):
        self.indicators = {}
        self.patterns = {}
    
    def calculate_all_indicators(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate all technical indicators for a stock
        Args:
            price_data: DataFrame with OHLCV data
        Returns:
            Dictionary containing all technical indicators
        """
        try:
            indicators = {}
            
            # Moving Averages
            indicators['sma_20'] = self._calculate_sma(price_data['close'], 20)
            indicators['sma_50'] = self._calculate_sma(price_data['close'], 50)
            indicators['ema_12'] = self._calculate_ema(price_data['close'], 12)
            indicators['ema_26'] = self._calculate_ema(price_data['close'], 26)
            
            # Momentum Indicators
            indicators['rsi'] = self._calculate_rsi(price_data['close'], 14)
            indicators['macd'] = self._calculate_macd(price_data['close'])
            indicators['stochastic'] = self._calculate_stochastic(price_data)
            
            # Volatility Indicators
            indicators['bollinger_bands'] = self._calculate_bollinger_bands(price_data['close'], 20)
            indicators['atr'] = self._calculate_atr(price_data, 14)
            
            # Volume Indicators
            indicators['volume_sma'] = self._calculate_sma(price_data['volume'], 20)
            indicators['volume_ratio'] = price_data['volume'].iloc[-1] / indicators['volume_sma']
            
            # Trend Indicators
            indicators['adx'] = self._calculate_adx(price_data, 14)
            indicators['cci'] = self._calculate_cci(price_data, 20)
            
            self.indicators = indicators
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_sma(self, series: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average"""
        try:
            return series.rolling(window=period).mean().iloc[-1]
        except:
            return 0.0
    
    def _calculate_ema(self, series: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        try:
            return series.ewm(span=period).mean().iloc[-1]
        except:
            return 0.0
    
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        try:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50.0
    
    def _calculate_macd(self, series: pd.Series) -> Dict[str, float]:
        """Calculate MACD"""
        try:
            ema_12 = self._calculate_ema(series, 12)
            ema_26 = self._calculate_ema(series, 26)
            macd_line = ema_12 - ema_26
            signal_line = self._calculate_ema(pd.Series([macd_line]), 9)
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        except:
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}
    
    def _calculate_stochastic(self, price_data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """Calculate Stochastic Oscillator"""
        try:
            low_min = price_data['low'].rolling(window=k_period).min()
            high_max = price_data['high'].rolling(window=k_period).max()
            k_percent = 100 * ((price_data['close'] - low_min) / (high_max - low_min))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                'k': k_percent.iloc[-1],
                'd': d_percent.iloc[-1]
            }
        except:
            return {'k': 50.0, 'd': 50.0}
    
    def _calculate_bollinger_bands(self, series: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        try:
            sma = self._calculate_sma(series, period)
            std = series.rolling(window=period).std().iloc[-1]
            
            return {
                'upper': sma + (std * std_dev),
                'middle': sma,
                'lower': sma - (std * std_dev)
            }
        except:
            return {'upper': 0.0, 'middle': 0.0, 'lower': 0.0}
    
    def _calculate_atr(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high_low = price_data['high'] - price_data['low']
            high_close = np.abs(price_data['high'] - price_data['close'].shift())
            low_close = np.abs(price_data['low'] - price_data['close'].shift())
            
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=period).mean()
            
            return atr.iloc[-1]
        except:
            return 0.0
    
    def _calculate_adx(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        try:
            # Simplified ADX calculation
            high_diff = price_data['high'].diff()
            low_diff = price_data['low'].diff()
            
            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            minus_dm = -low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
            
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / self._calculate_atr(price_data, period))
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / self._calculate_atr(price_data, period))
            
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            
            return adx.iloc[-1]
        except:
            return 25.0
    
    def _calculate_cci(self, price_data: pd.DataFrame, period: int = 20) -> float:
        """Calculate Commodity Channel Index"""
        try:
            typical_price = (price_data['high'] + price_data['low'] + price_data['close']) / 3
            sma_tp = typical_price.rolling(window=period).mean()
            mean_deviation = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
            
            cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
            return cci.iloc[-1]
        except:
            return 0.0
    
    def identify_patterns(self, price_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identify chart patterns
        Args:
            price_data: DataFrame with OHLCV data
        Returns:
            List of identified patterns
        """
        try:
            patterns = []
            
            # Simple pattern detection
            if len(price_data) >= 20:
                # Double Bottom
                if self._detect_double_bottom(price_data):
                    patterns.append({
                        'name': 'Double Bottom',
                        'type': 'reversal',
                        'signal': 'bullish',
                        'confidence': 0.75
                    })
                
                # Double Top
                if self._detect_double_top(price_data):
                    patterns.append({
                        'name': 'Double Top',
                        'type': 'reversal',
                        'signal': 'bearish',
                        'confidence': 0.75
                    })
                
                # Head and Shoulders
                if self._detect_head_shoulders(price_data):
                    patterns.append({
                        'name': 'Head and Shoulders',
                        'type': 'reversal',
                        'signal': 'bearish',
                        'confidence': 0.80
                    })
            
            self.patterns = patterns
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying patterns: {e}")
            return []
    
    def _detect_double_bottom(self, price_data: pd.DataFrame) -> bool:
        """Detect double bottom pattern"""
        try:
            if len(price_data) < 20:
                return False
            
            # Find local minima
            lows = price_data['low'].rolling(window=5, center=True).min()
            minima = price_data[price_data['low'] == lows]
            
            if len(minima) < 2:
                return False
            
            # Check if two minima are roughly equal and separated
            recent_minima = minima.tail(2)
            if len(recent_minima) < 2:
                return False
            
            price_diff = abs(recent_minima['low'].iloc[0] - recent_minima['low'].iloc[1])
            avg_price = (recent_minima['low'].iloc[0] + recent_minima['low'].iloc[1]) / 2
            
            return price_diff / avg_price < 0.02  # Within 2% of each other
            
        except:
            return False
    
    def _detect_double_top(self, price_data: pd.DataFrame) -> bool:
        """Detect double top pattern"""
        try:
            if len(price_data) < 20:
                return False
            
            # Find local maxima
            highs = price_data['high'].rolling(window=5, center=True).max()
            maxima = price_data[price_data['high'] == highs]
            
            if len(maxima) < 2:
                return False
            
            # Check if two maxima are roughly equal and separated
            recent_maxima = maxima.tail(2)
            if len(recent_maxima) < 2:
                return False
            
            price_diff = abs(recent_maxima['high'].iloc[0] - recent_maxima['high'].iloc[1])
            avg_price = (recent_maxima['high'].iloc[0] + recent_maxima['high'].iloc[1]) / 2
            
            return price_diff / avg_price < 0.02  # Within 2% of each other
            
        except:
            return False
    
    def _detect_head_shoulders(self, price_data: pd.DataFrame) -> bool:
        """Detect head and shoulders pattern"""
        try:
            if len(price_data) < 30:
                return False
            
            # Find local maxima
            highs = price_data['high'].rolling(window=5, center=True).max()
            maxima = price_data[price_data['high'] == highs]
            
            if len(maxima) < 3:
                return False
            
            # Get the three highest peaks
            recent_maxima = maxima.tail(3)
            if len(recent_maxima) < 3:
                return False
            
            # Check if middle peak is highest (head)
            peaks = recent_maxima['high'].values
            if peaks[1] > peaks[0] and peaks[1] > peaks[2]:
                # Check if shoulders are roughly equal
                shoulder_diff = abs(peaks[0] - peaks[2])
                avg_shoulder = (peaks[0] + peaks[2]) / 2
                return shoulder_diff / avg_shoulder < 0.05  # Within 5% of each other
            
            return False
            
        except:
            return False
    
    def get_signal_strength(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall signal strength based on indicators
        Args:
            indicators: Dictionary of technical indicators
        Returns:
            Dictionary with signal strength and recommendation
        """
        try:
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0
            
            # RSI signals
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi < 30:
                    bullish_signals += 1
                elif rsi > 70:
                    bearish_signals += 1
                total_signals += 1
            
            # MACD signals
            if 'macd' in indicators and isinstance(indicators['macd'], dict):
                macd = indicators['macd']
                if macd['macd'] > macd['signal']:
                    bullish_signals += 1
                else:
                    bearish_signals += 1
                total_signals += 1
            
            # Moving average signals
            if 'sma_20' in indicators and 'sma_50' in indicators:
                if indicators['sma_20'] > indicators['sma_50']:
                    bullish_signals += 1
                else:
                    bearish_signals += 1
                total_signals += 1
            
            # Calculate strength
            if total_signals == 0:
                strength = 0
                signal = 'neutral'
            else:
                bullish_ratio = bullish_signals / total_signals
                if bullish_ratio > 0.6:
                    strength = bullish_ratio
                    signal = 'bullish'
                elif bullish_ratio < 0.4:
                    strength = 1 - bullish_ratio
                    signal = 'bearish'
                else:
                    strength = 0.5
                    signal = 'neutral'
            
            return {
                'signal': signal,
                'strength': strength,
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals,
                'total_signals': total_signals
            }
            
        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return {
                'signal': 'neutral',
                'strength': 0.5,
                'bullish_signals': 0,
                'bearish_signals': 0,
                'total_signals': 0
            }


# Create singleton instance
technical_analysis_service = TechnicalAnalysisService()