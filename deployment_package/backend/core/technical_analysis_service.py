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
            indicators.update(self._calculate_moving_averages(price_data))
            # Momentum Indicators
            indicators.update(self._calculate_momentum_indicators(price_data))
            # Volatility Indicators
            indicators.update(self._calculate_volatility_indicators(price_data))
            # Volume Indicators
            indicators.update(self._calculate_volume_indicators(price_data))
            # Trend Indicators
            indicators.update(self._calculate_trend_indicators(price_data))
            # Support/Resistance
            indicators.update(self._calculate_support_resistance(price_data))
            # Pattern Recognition
            indicators.update(self._identify_patterns(price_data))
            return indicators
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}

    def _calculate_moving_averages(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate various moving averages"""
        try:
            close = data['close'].values
            ma_5 = np.mean(close[-5:]) if len(close) >= 5 else close[-1]
            ma_10 = np.mean(close[-10:]) if len(close) >= 10 else close[-1]
            ma_20 = np.mean(close[-20:]) if len(close) >= 20 else close[-1]
            ma_50 = np.mean(close[-50:]) if len(close) >= 50 else close[-1]
            ma_200 = np.mean(close[-200:]) if len(close) >= 200 else close[-1]
            return {
                'ma_5': ma_5,
                'ma_10': ma_10,
                'ma_20': ma_20,
                'ma_50': ma_50,
                'ma_200': ma_200,
                'ma_5_above_20': ma_5 > ma_20,
                'ma_20_above_50': ma_20 > ma_50,
                'price_above_200': close[-1] > ma_200,
            }
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return {}

    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate momentum indicators"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            # RSI (Relative Strength Index)
            rsi_14 = self._calculate_rsi(close, 14)
            rsi_21 = self._calculate_rsi(close, 21)
            # MACD
            macd_line, macd_signal, macd_histogram = self._calculate_macd(close)
            # Stochastic Oscillator
            stoch_k, stoch_d = self._calculate_stochastic(high, low, close)
            # Williams %R
            williams_r = self._calculate_williams_r(high, low, close)
            return {
                'rsi_14': rsi_14,
                'rsi_21': rsi_21,
                'rsi_oversold': rsi_14 < 30,
                'rsi_overbought': rsi_14 > 70,
                'macd_line': macd_line,
                'macd_signal': macd_signal,
                'macd_histogram': macd_histogram,
                'macd_bullish': macd_line > macd_signal,
                'stoch_k': stoch_k,
                'stoch_d': stoch_d,
                'stoch_oversold': stoch_k < 20,
                'stoch_overbought': stoch_k > 80,
                'williams_r': williams_r,
                'williams_oversold': williams_r < -80,
                'williams_overbought': williams_r > -20,
            }
        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {e}")
            return {}

    def _calculate_volatility_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate volatility indicators"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close)
            # Average True Range (ATR)
            atr = self._calculate_atr(high, low, close)
            # Historical Volatility
            hist_vol = self._calculate_historical_volatility(close)
            # Price position relative to Bollinger Bands
            current_price = close[-1]
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
            return {
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'bb_position': bb_position,
                'bb_squeeze': (bb_upper - bb_lower) / bb_middle < 0.1,
                'atr': atr,
                'atr_percent': atr / current_price * 100,
                'historical_volatility': hist_vol,
                'price_near_bb_upper': bb_position > 0.8,
                'price_near_bb_lower': bb_position < 0.2,
            }
        except Exception as e:
            logger.error(f"Error calculating volatility indicators: {e}")
            return {}

    def _calculate_volume_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate volume-based indicators"""
        try:
            close = data['close'].values
            volume = data['volume'].values
            # Volume Moving Averages
            volume_ma_20 = np.mean(volume[-20:]) if len(volume) >= 20 else volume[-1]
            volume_ma_50 = np.mean(volume[-50:]) if len(volume) >= 50 else volume[-1]
            # On-Balance Volume (OBV)
            obv = self._calculate_obv(close, volume)
            # Volume Price Trend (VPT)
            vpt = self._calculate_vpt(close, volume)
            # Money Flow Index
            mfi = self._calculate_money_flow_index(data)
            current_volume = volume[-1]
            return {
                'volume_ma_20': volume_ma_20,
                'volume_ma_50': volume_ma_50,
                'volume_ratio': current_volume / volume_ma_20 if volume_ma_20 > 0 else 1.0,
                'high_volume': current_volume > volume_ma_20 * 1.5,
                'low_volume': current_volume < volume_ma_20 * 0.5,
                'obv': obv,
                'obv_trend': obv > np.mean([obv[-20:] if len(obv) >= 20 else obv]),
                'vpt': vpt,
                'mfi': mfi,
                'mfi_oversold': mfi < 20,
                'mfi_overbought': mfi > 80,
            }
        except Exception as e:
            logger.error(f"Error calculating volume indicators: {e}")
            return {}

    def _calculate_trend_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate trend indicators"""
        try:
            close = data['close'].values
            # ADX (Average Directional Index)
            adx = self._calculate_adx(data)
            # Parabolic SAR
            sar = self._calculate_parabolic_sar(data)
            # Ichimoku Cloud
            ichimoku = self._calculate_ichimoku(data)
            # Trend Strength
            trend_strength = self._calculate_trend_strength(close)
            return {
                'adx': adx,
                'trend_strong': adx > 25,
                'trend_weak': adx < 20,
                'parabolic_sar': sar,
                'price_above_sar': close[-1] > sar,
                'ichimoku_tenkan': ichimoku.get('tenkan', 0),
                'ichimoku_kijun': ichimoku.get('kijun', 0),
                'ichimoku_senkou_a': ichimoku.get('senkou_a', 0),
                'ichimoku_senkou_b': ichimoku.get('senkou_b', 0),
                'trend_strength': trend_strength,
                'trend_direction': 'up' if trend_strength > 0.6 else 'down' if trend_strength < 0.4 else 'sideways',
            }
        except Exception as e:
            logger.error(f"Error calculating trend indicators: {e}")
            return {}

    def _calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            # Pivot Points
            pivot = (high[-1] + low[-1] + close[-1]) / 3
            r1 = 2 * pivot - low[-1]
            s1 = 2 * pivot - high[-1]
            r2 = pivot + (high[-1] - low[-1])
            s2 = pivot - (high[-1] - low[-1])
            # Recent highs and lows
            recent_high = np.max(high[-20:]) if len(high) >= 20 else high[-1]
            recent_low = np.min(low[-20:]) if len(low) >= 20 else low[-1]
            current_price = close[-1]
            return {
                'pivot': pivot,
                'resistance_1': r1,
                'resistance_2': r2,
                'support_1': s1,
                'support_2': s2,
                'recent_high': recent_high,
                'recent_low': recent_low,
                'distance_to_resistance': (r1 - current_price) / current_price * 100,
                'distance_to_support': (current_price - s1) / current_price * 100,
                'near_resistance': current_price > r1 * 0.98,
                'near_support': current_price < s1 * 1.02,
            }
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {}

    def _identify_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Identify chart patterns"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            patterns = {}
            # Double Top/Bottom
            patterns['double_top'] = self._detect_double_top(high, low)
            patterns['double_bottom'] = self._detect_double_bottom(high, low)
            # Head and Shoulders
            patterns['head_shoulders'] = self._detect_head_shoulders(high, low)
            patterns['inverse_head_shoulders'] = self._detect_inverse_head_shoulders(high, low)
            # Triangle Patterns
            patterns['ascending_triangle'] = self._detect_ascending_triangle(high, low)
            patterns['descending_triangle'] = self._detect_descending_triangle(high, low)
            patterns['symmetrical_triangle'] = self._detect_symmetrical_triangle(high, low)
            # Flag and Pennant
            patterns['bull_flag'] = self._detect_bull_flag(high, low, close)
            patterns['bear_flag'] = self._detect_bear_flag(high, low, close)
            # Cup and Handle
            patterns['cup_handle'] = self._detect_cup_handle(high, low, close)
            return patterns
        except Exception as e:
            logger.error(f"Error identifying patterns: {e}")
            return {}

    # Helper methods for indicator calculations

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gains = np.mean(gains[-period:])
        avg_losses = np.mean(losses[-period:])
        if avg_losses == 0:
            return 100.0
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        macd_signal = self._calculate_ema(np.array([macd_line]), signal)
        macd_histogram = macd_line - macd_signal
        return macd_line, macd_signal, macd_histogram

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1]
        alpha = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        return ema

    def _calculate_stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator"""
        if len(high) < period:
            return 50.0, 50.0
        highest_high = np.max(high[-period:])
        lowest_low = np.min(low[-period:])
        if highest_high == lowest_low:
            return 50.0, 50.0
        k = 100 * (close[-1] - lowest_low) / (highest_high - lowest_low)
        d = np.mean([k])  # Simplified %D calculation
        return k, d

    def _calculate_williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate Williams %R"""
        if len(high) < period:
            return -50.0
        highest_high = np.max(high[-period:])
        lowest_low = np.min(low[-period:])
        if highest_high == lowest_low:
            return -50.0
        williams_r = -100 * (highest_high - close[-1]) / (highest_high - lowest_low)
        return williams_r

    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return prices[-1], prices[-1], prices[-1]
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        return upper, sma, lower

    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(high) < 2:
            return 0.0
        true_ranges = []
        for i in range(1, len(high)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i - 1])
            tr3 = abs(low[i] - close[i - 1])
            true_ranges.append(max(tr1, tr2, tr3))
        if len(true_ranges) < period:
            return np.mean(true_ranges)
        return np.mean(true_ranges[-period:])

    def _calculate_historical_volatility(self, prices: np.ndarray, period: int = 252) -> float:
        """Calculate historical volatility (annualized)"""
        if len(prices) < 2:
            return 0.0
        returns = np.diff(np.log(prices))
        if len(returns) < period:
            period = len(returns)
        return np.std(returns[-period:]) * np.sqrt(252)  # Annualized

    def _calculate_obv(self, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Calculate On-Balance Volume"""
        obv = np.zeros_like(close)
        obv[0] = volume[0]
        for i in range(1, len(close)):
            if close[i] > close[i - 1]:
                obv[i] = obv[i - 1] + volume[i]
            elif close[i] < close[i - 1]:
                obv[i] = obv[i - 1] - volume[i]
            else:
                obv[i] = obv[i - 1]
        return obv

    def _calculate_vpt(self, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Calculate Volume Price Trend"""
        vpt = np.zeros_like(close)
        vpt[0] = volume[0]
        for i in range(1, len(close)):
            price_change = (close[i] - close[i - 1]) / close[i - 1]
            vpt[i] = vpt[i - 1] + (volume[i] * price_change)
        return vpt

    def _calculate_money_flow_index(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Money Flow Index"""
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            volume = data['volume'].values
            if len(high) < period + 1:
                return 50.0
            typical_price = (high + low + close) / 3
            money_flow = typical_price * volume
            positive_flow = 0
            negative_flow = 0
            for i in range(1, len(typical_price)):
                if typical_price[i] > typical_price[i - 1]:
                    positive_flow += money_flow[i]
                elif typical_price[i] < typical_price[i - 1]:
                    negative_flow += money_flow[i]
            if negative_flow == 0:
                return 100.0
            money_ratio = positive_flow / negative_flow
            mfi = 100 - (100 / (1 + money_ratio))
            return mfi
        except Exception as e:
            logger.error(f"Error calculating MFI: {e}")
            return 50.0

    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            if len(high) < period + 1:
                return 25.0
            # Directional Movement calculation
            plus_dm = np.zeros(len(high))
            minus_dm = np.zeros(len(high))
            tr_arr = np.zeros(len(high))
            for i in range(1, len(high)):
                up_move = high[i] - high[i - 1]
                down_move = low[i - 1] - low[i]
                plus_dm[i] = up_move if (up_move > down_move and up_move > 0) else 0.0
                minus_dm[i] = down_move if (down_move > up_move and down_move > 0) else 0.0
                tr_arr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
            # Smoothed averages (Wilder's method)
            atr = np.mean(tr_arr[1:period + 1])
            plus_di_val = np.mean(plus_dm[1:period + 1])
            minus_di_val = np.mean(minus_dm[1:period + 1])
            dx_values = []
            for i in range(period + 1, len(high)):
                atr = atr - (atr / period) + tr_arr[i]
                plus_di_val = plus_di_val - (plus_di_val / period) + plus_dm[i]
                minus_di_val = minus_di_val - (minus_di_val / period) + minus_dm[i]
                if atr > 0:
                    plus_di = 100.0 * plus_di_val / atr
                    minus_di = 100.0 * minus_di_val / atr
                else:
                    plus_di = 0.0
                    minus_di = 0.0
                di_sum = plus_di + minus_di
                dx = (abs(plus_di - minus_di) / di_sum * 100.0) if di_sum > 0 else 0.0
                dx_values.append(dx)
            if not dx_values:
                return 25.0
            if len(dx_values) >= period:
                adx = np.mean(dx_values[-period:])
            else:
                adx = np.mean(dx_values)
            return min(100.0, max(0.0, adx))
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            return 25.0

    def _calculate_parabolic_sar(self, data: pd.DataFrame) -> float:
        """Calculate Parabolic SAR (returns the most recent SAR value)"""
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            if len(high) < 2:
                return close[-1]
            af_start = 0.02
            af_max = 0.20
            af_step = 0.02
            # Initial trend: bullish if second close > first close
            bullish = close[1] > close[0]
            sar = low[0] if bullish else high[0]
            ep = high[0] if bullish else low[0]
            af = af_start
            for i in range(1, len(high)):
                prev_sar = sar
                sar = prev_sar + af * (ep - prev_sar)
                if bullish:
                    sar = min(sar, low[i - 1])
                    if i >= 2:
                        sar = min(sar, low[i - 2])
                    if low[i] < sar:
                        bullish = False
                        sar = ep
                        ep = low[i]
                        af = af_start
                    else:
                        if high[i] > ep:
                            ep = high[i]
                            af = min(af + af_step, af_max)
                else:
                    sar = max(sar, high[i - 1])
                    if i >= 2:
                        sar = max(sar, high[i - 2])
                    if high[i] > sar:
                        bullish = True
                        sar = ep
                        ep = high[i]
                        af = af_start
                    else:
                        if low[i] < ep:
                            ep = low[i]
                            af = min(af + af_step, af_max)
            return sar
        except Exception as e:
            logger.error(f"Error calculating Parabolic SAR: {e}")
            return close[-1]

    def _calculate_ichimoku(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate Ichimoku Cloud components"""
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            if len(high) < 26:
                return {}
            tenkan = (np.max(high[-9:]) + np.min(low[-9:])) / 2
            kijun = (np.max(high[-26:]) + np.min(low[-26:])) / 2
            senkou_a = (tenkan + kijun) / 2
            senkou_b = (np.max(high[-52:]) + np.min(low[-52:])) / 2
            return {
                'tenkan': tenkan,
                'kijun': kijun,
                'senkou_a': senkou_a,
                'senkou_b': senkou_b,
            }
        except Exception as e:
            logger.error(f"Error calculating Ichimoku: {e}")
            return {}

    def _calculate_trend_strength(self, prices: np.ndarray) -> float:
        """Calculate trend strength (0-1)"""
        try:
            if len(prices) < 20:
                return 0.5
            # Linear regression slope
            x = np.arange(len(prices[-20:]))
            y = prices[-20:]
            slope = np.polyfit(x, y, 1)[0]
            max_slope = np.std(y) * 2  # Normalize slope
            trend_strength = min(1.0, max(0.0, (slope / max_slope + 1) / 2))
            return trend_strength
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.5

    # ----------------------------------------------------------------
    # Pattern detection methods — deterministic heuristic detection
    # ----------------------------------------------------------------

    @staticmethod
    def _find_local_peaks(arr: np.ndarray, order: int = 5) -> List[int]:
        """Find indices of local maxima."""
        peaks = []
        for i in range(order, len(arr) - order):
            if all(arr[i] >= arr[i - j] for j in range(1, order + 1)) and \
               all(arr[i] >= arr[i + j] for j in range(1, order + 1)):
                peaks.append(i)
        return peaks

    @staticmethod
    def _find_local_troughs(arr: np.ndarray, order: int = 5) -> List[int]:
        """Find indices of local minima."""
        troughs = []
        for i in range(order, len(arr) - order):
            if all(arr[i] <= arr[i - j] for j in range(1, order + 1)) and \
               all(arr[i] <= arr[i + j] for j in range(1, order + 1)):
                troughs.append(i)
        return troughs

    def _detect_double_top(self, high: np.ndarray, low: np.ndarray) -> bool:
        """Detect double top pattern: two peaks at roughly the same level with a trough between."""
        if len(high) < 20:
            return False
        peaks = self._find_local_peaks(high, order=3)
        if len(peaks) < 2:
            return False
        # Check the two most recent peaks
        p1, p2 = peaks[-2], peaks[-1]
        tolerance = 0.02 * high[p1]  # 2% tolerance
        if abs(high[p1] - high[p2]) < tolerance and p2 - p1 >= 5:
            # Ensure there's a meaningful trough between them
            trough_val = np.min(low[p1:p2 + 1])
            drop_pct = (high[p1] - trough_val) / high[p1]
            return drop_pct > 0.02  # At least 2% dip between peaks
        return False

    def _detect_double_bottom(self, high: np.ndarray, low: np.ndarray) -> bool:
        """Detect double bottom pattern: two troughs at roughly the same level."""
        if len(low) < 20:
            return False
        troughs = self._find_local_troughs(low, order=3)
        if len(troughs) < 2:
            return False
        t1, t2 = troughs[-2], troughs[-1]
        tolerance = 0.02 * low[t1]
        if abs(low[t1] - low[t2]) < tolerance and t2 - t1 >= 5:
            peak_val = np.max(high[t1:t2 + 1])
            rise_pct = (peak_val - low[t1]) / low[t1]
            return rise_pct > 0.02
        return False

    def _detect_head_shoulders(self, high: np.ndarray, low: np.ndarray) -> bool:
        """Detect head and shoulders: left shoulder, higher head, right shoulder at similar level."""
        if len(high) < 30:
            return False
        peaks = self._find_local_peaks(high, order=3)
        if len(peaks) < 3:
            return False
        # Check last 3 peaks
        for i in range(len(peaks) - 2):
            left, head, right = peaks[i], peaks[i + 1], peaks[i + 2]
            if high[head] > high[left] and high[head] > high[right]:
                shoulder_tol = 0.03 * high[left]
                if abs(high[left] - high[right]) < shoulder_tol:
                    return True
        return False

    def _detect_inverse_head_shoulders(self, high: np.ndarray, low: np.ndarray) -> bool:
        """Detect inverse head and shoulders: left trough, deeper head trough, right trough."""
        if len(low) < 30:
            return False
        troughs = self._find_local_troughs(low, order=3)
        if len(troughs) < 3:
            return False
        for i in range(len(troughs) - 2):
            left, head, right = troughs[i], troughs[i + 1], troughs[i + 2]
            if low[head] < low[left] and low[head] < low[right]:
                shoulder_tol = 0.03 * low[left]
                if abs(low[left] - low[right]) < shoulder_tol:
                    return True
        return False

    def _detect_ascending_triangle(self, high: np.ndarray, low: np.ndarray) -> bool:
        """Detect ascending triangle: flat resistance with rising support (lows trending up)."""
        if len(high) < 20:
            return False
        window = 20
        recent_high = high[-window:]
        recent_low = low[-window:]
        peaks = self._find_local_peaks(recent_high, order=2)
        troughs = self._find_local_troughs(recent_low, order=2)
        if len(peaks) < 2 or len(troughs) < 2:
            return False
        # Flat resistance: peaks within 1.5% of each other
        peak_vals = recent_high[peaks]
        if np.ptp(peak_vals) / np.mean(peak_vals) > 0.015:
            return False
        # Rising lows: later troughs higher than earlier ones
        trough_vals = recent_low[troughs]
        if len(trough_vals) >= 2 and trough_vals[-1] > trough_vals[0]:
            return True
        return False

    def _detect_descending_triangle(self, high: np.ndarray, low: np.ndarray) -> bool:
        """Detect descending triangle: flat support with declining resistance."""
        if len(high) < 20:
            return False
        window = 20
        recent_high = high[-window:]
        recent_low = low[-window:]
        peaks = self._find_local_peaks(recent_high, order=2)
        troughs = self._find_local_troughs(recent_low, order=2)
        if len(peaks) < 2 or len(troughs) < 2:
            return False
        # Flat support
        trough_vals = recent_low[troughs]
        if np.ptp(trough_vals) / np.mean(trough_vals) > 0.015:
            return False
        # Declining highs
        peak_vals = recent_high[peaks]
        if len(peak_vals) >= 2 and peak_vals[-1] < peak_vals[0]:
            return True
        return False

    def _detect_symmetrical_triangle(self, high: np.ndarray, low: np.ndarray) -> bool:
        """Detect symmetrical triangle: converging highs and lows."""
        if len(high) < 20:
            return False
        window = 20
        recent_high = high[-window:]
        recent_low = low[-window:]
        peaks = self._find_local_peaks(recent_high, order=2)
        troughs = self._find_local_troughs(recent_low, order=2)
        if len(peaks) < 2 or len(troughs) < 2:
            return False
        peak_vals = recent_high[peaks]
        trough_vals = recent_low[troughs]
        declining_highs = peak_vals[-1] < peak_vals[0]
        rising_lows = trough_vals[-1] > trough_vals[0]
        return declining_highs and rising_lows

    def _detect_bull_flag(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> bool:
        """Detect bull flag: sharp uptrend (pole) followed by tight downward-sloping consolidation."""
        if len(close) < 15:
            return False
        # Pole: strong rise in first portion
        pole = close[-15:-8]
        flag = close[-8:]
        if len(pole) < 2 or len(flag) < 2:
            return False
        pole_return = (pole[-1] - pole[0]) / pole[0]
        flag_return = (flag[-1] - flag[0]) / flag[0]
        # Pole should rise > 3%, flag should slightly decline or be flat
        if pole_return > 0.03 and -0.02 < flag_return < 0.01:
            # Flag should have lower volatility than pole
            pole_range = (np.max(high[-15:-8]) - np.min(low[-15:-8])) / np.mean(close[-15:-8])
            flag_range = (np.max(high[-8:]) - np.min(low[-8:])) / np.mean(close[-8:])
            return flag_range < pole_range * 0.6
        return False

    def _detect_bear_flag(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> bool:
        """Detect bear flag: sharp downtrend (pole) followed by tight upward-sloping consolidation."""
        if len(close) < 15:
            return False
        pole = close[-15:-8]
        flag = close[-8:]
        if len(pole) < 2 or len(flag) < 2:
            return False
        pole_return = (pole[-1] - pole[0]) / pole[0]
        flag_return = (flag[-1] - flag[0]) / flag[0]
        if pole_return < -0.03 and -0.01 < flag_return < 0.02:
            pole_range = (np.max(high[-15:-8]) - np.min(low[-15:-8])) / np.mean(close[-15:-8])
            flag_range = (np.max(high[-8:]) - np.min(low[-8:])) / np.mean(close[-8:])
            return flag_range < pole_range * 0.6
        return False

    def _detect_cup_handle(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> bool:
        """Detect cup and handle: U-shaped recovery with small pullback at the end."""
        if len(close) < 40:
            return False
        # Look at last 40 bars
        cup = close[-40:-5]
        handle = close[-5:]
        if len(cup) < 10:
            return False
        # Cup: should form a U — starts high, dips, recovers to near start
        cup_start = cup[0]
        cup_end = cup[-1]
        cup_min = np.min(cup)
        cup_depth = (cup_start - cup_min) / cup_start
        recovery = (cup_end - cup_min) / (cup_start - cup_min) if cup_start != cup_min else 0
        # Handle: small pullback from the cup rim
        handle_pullback = (handle[0] - np.min(handle)) / handle[0] if handle[0] > 0 else 0
        # Cup should drop 5-30%, recover 80%+, handle pullback < 50% of cup depth
        return (0.05 < cup_depth < 0.30 and
                recovery > 0.80 and
                handle_pullback < cup_depth * 0.5)
