"""
RAHA Strategy Engine
Implements the 4 core mechanical strategies: ORB, Momentum, Supply/Demand, Fade ORB
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal

from .raha_models import StrategyVersion
from .day_trading_feature_service import DayTradingFeatureService

logger = logging.getLogger(__name__)


class RAHAStrategyEngine:
    """
    Core strategy engine that implements mechanical trading strategies.
    Uses existing DayTradingFeatureService for feature extraction.
    """
    
    def __init__(self):
        self.feature_service = DayTradingFeatureService()
    
    def _fetch_ohlcv_data(self, symbol: str, timeframe: str, lookback_candles: int) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a symbol using existing infrastructure.
        Falls back to mock data if real data unavailable.
        """
        try:
            # Try to use existing _get_intraday_data function
            from .queries import _get_intraday_data
            import asyncio
            
            # Run async function
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(_get_intraday_data(symbol))
            if result and isinstance(result, tuple) and len(result) >= 2:
                ohlcv_1m, ohlcv_5m = result[0], result[1]
                
                # Select appropriate timeframe
                if timeframe in ['1m', '1']:
                    return ohlcv_1m
                elif timeframe in ['5m', '5']:
                    return ohlcv_5m
                else:
                    # Resample to requested timeframe
                    timeframe_minutes = self._parse_timeframe(timeframe)
                    if timeframe_minutes:
                        ohlcv_1m.set_index('timestamp', inplace=True)
                        resampled = ohlcv_1m.resample(f'{timeframe_minutes}T').agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }).reset_index()
                        return resampled.tail(lookback_candles)
            
            return None
        except Exception as e:
            logger.warning(f"Could not fetch OHLCV data for {symbol}: {e}")
            return None
    
    def _parse_timeframe(self, timeframe: str) -> Optional[int]:
        """Parse timeframe string to minutes (e.g., '5m' -> 5, '15m' -> 15)"""
        timeframe = timeframe.lower().strip()
        if timeframe.endswith('m'):
            try:
                return int(timeframe[:-1])
            except ValueError:
                pass
        elif timeframe.endswith('h'):
            try:
                return int(timeframe[:-1]) * 60
            except ValueError:
                pass
        return None
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        try:
            if len(df) < period + 1:
                return None
            
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            
            tr_list = []
            for i in range(1, len(df)):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr_list.append(tr)
            
            if len(tr_list) < period:
                return None
            
            atr = np.mean(tr_list[-period:])
            return float(atr)
        except Exception as e:
            logger.warning(f"Error calculating ATR: {e}")
            return None
    
    def _calculate_vwap(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate Volume Weighted Average Price"""
        try:
            if len(df) == 0:
                return None
            
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            vwap = (typical_price * df['volume']).sum() / df['volume'].sum()
            return float(vwap)
        except Exception as e:
            logger.warning(f"Error calculating VWAP: {e}")
            return None
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        try:
            if len(df) < period + 1:
                return None
            
            close = df['close'].values
            deltas = np.diff(close)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi)
        except Exception as e:
            logger.warning(f"Error calculating RSI: {e}")
            return None
    
    def _identify_swing_points(self, df: pd.DataFrame, lookback: int = 5) -> tuple:
        """Identify swing highs and lows (fractals)"""
        try:
            if len(df) < lookback * 2 + 1:
                return [], []
            
            highs = df['high'].values
            lows = df['low'].values
            
            swing_highs = []
            swing_lows = []
            
            for i in range(lookback, len(df) - lookback):
                # Swing high: current high is highest in lookback window
                if highs[i] == max(highs[i-lookback:i+lookback+1]):
                    swing_highs.append(float(highs[i]))
                
                # Swing low: current low is lowest in lookback window
                if lows[i] == min(lows[i-lookback:i+lookback+1]):
                    swing_lows.append(float(lows[i]))
            
            return swing_highs, swing_lows
        except Exception as e:
            logger.warning(f"Error identifying swing points: {e}")
            return [], []
    
    def _calculate_momentum(self, df: pd.DataFrame, period: int = 5) -> Optional[float]:
        """Calculate price momentum (rate of change)"""
        try:
            if len(df) < period + 1:
                return None
            
            close = df['close'].values
            momentum = ((close[-1] - close[-period-1]) / close[-period-1]) * 100
            return float(momentum)
        except Exception as e:
            logger.warning(f"Error calculating momentum: {e}")
            return None
    
    def _calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(df) < slow + signal:
                return None, None, None
            
            close = df['close'].values
            
            # Calculate EMAs
            ema_fast = pd.Series(close).ewm(span=fast, adjust=False).mean()
            ema_slow = pd.Series(close).ewm(span=slow, adjust=False).mean()
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line (EMA of MACD)
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
        except Exception as e:
            logger.warning(f"Error calculating MACD: {e}")
            return None, None, None
    
    def generate_signals(
        self,
        strategy_version: StrategyVersion,
        symbol: str,
        timeframe: str = "5m",
        lookback_candles: int = 500,
        parameters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate signals for a strategy version.
        
        Args:
            strategy_version: StrategyVersion instance
            symbol: Stock symbol
            timeframe: Candle timeframe (1m, 5m, 15m, etc.)
            lookback_candles: Number of historical candles to analyze
            parameters: Strategy-specific parameters
        
        Returns:
            List of signal dictionaries
        """
        logic_ref = strategy_version.logic_ref
        
        # Route to appropriate strategy implementation
        if logic_ref.startswith('ORB'):
            return self._generate_orb_signals(symbol, timeframe, lookback_candles, parameters or {})
        elif logic_ref.startswith('MOMENTUM'):
            return self._generate_momentum_signals(symbol, timeframe, lookback_candles, parameters or {})
        elif logic_ref.startswith('SUPPLY_DEMAND') or logic_ref.startswith('S_D'):
            return self._generate_supply_demand_signals(symbol, timeframe, lookback_candles, parameters or {})
        elif logic_ref.startswith('FADE'):
            return self._generate_fade_orb_signals(symbol, timeframe, lookback_candles, parameters or {})
        else:
            logger.warning(f"Unknown strategy logic_ref: {logic_ref}")
            return []
    
    def _generate_orb_signals(
        self,
        symbol: str,
        timeframe: str,
        lookback_candles: int,
        parameters: Dict
    ) -> List[Dict[str, Any]]:
        """
        Opening Range Breakout (PJ Trades style)
        
        Logic:
        1. Define ORB range (first N minutes of session)
        2. Skip choppy days (range < min_range_atr_pct * ATR)
        3. Long breakout: close > orb_high with volume > threshold
        4. Short breakout: close < orb_low with volume > threshold
        """
        # Default parameters
        orb_minutes = parameters.get('orb_minutes', 15)
        min_range_atr_pct = parameters.get('min_range_atr_pct', 0.5)
        volume_multiplier = parameters.get('volume_multiplier', 1.5)
        risk_per_trade = parameters.get('risk_per_trade', 0.01)
        take_profit_r = parameters.get('take_profit_r', 2.0)
        
        logger.info(f"Generating ORB signals for {symbol} (ORB={orb_minutes}m, timeframe={timeframe})")
        
        try:
            # Fetch OHLCV data using existing infrastructure
            ohlcv_df = self._fetch_ohlcv_data(symbol, timeframe, lookback_candles)
            if ohlcv_df is None or len(ohlcv_df) < 20:
                logger.warning(f"Insufficient data for {symbol}")
                return []
            
            # Calculate timeframe multiplier (minutes per candle)
            timeframe_minutes = self._parse_timeframe(timeframe)
            if timeframe_minutes is None:
                logger.error(f"Unsupported timeframe: {timeframe}")
                return []
            
            # Calculate ORB range (first N minutes of session)
            orb_candles = max(1, int(orb_minutes / timeframe_minutes))
            if len(ohlcv_df) < orb_candles + 5:
                return []
            
            orb_slice = ohlcv_df.head(orb_candles)
            orb_high = orb_slice['high'].max()
            orb_low = orb_slice['low'].min()
            orb_range = orb_high - orb_low
            orb_mid = (orb_high + orb_low) / 2
            
            # Calculate ATR for range filter
            atr = self._calculate_atr(ohlcv_df, period=14)
            if atr is None or atr == 0:
                return []
            
            # Skip choppy days
            if orb_range < (min_range_atr_pct * atr):
                logger.debug(f"Skipping {symbol}: choppy day (range={orb_range:.2f}, ATR={atr:.2f})")
                return []
            
            # Calculate average volume
            avg_volume = ohlcv_df['volume'].rolling(20).mean().iloc[-1]
            if pd.isna(avg_volume) or avg_volume == 0:
                avg_volume = ohlcv_df['volume'].mean()
            
            signals = []
            current_candle = ohlcv_df.iloc[-1]
            current_price = float(current_candle['close'])
            current_volume = float(current_candle['volume'])
            
            # Check for long breakout
            if current_price > orb_high and current_volume > (volume_multiplier * avg_volume):
                risk = current_price - orb_low
                if risk > 0:
                    stop_loss = orb_low
                    take_profit = current_price + (take_profit_r * risk)
                    confidence = min(0.95, 0.5 + (current_volume / (volume_multiplier * avg_volume) - 1) * 0.3)
                    
                    signals.append({
                        'signal_type': 'ENTRY_LONG',
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'confidence_score': confidence,
                        'meta': {
                            'orb_high': orb_high,
                            'orb_low': orb_low,
                            'orb_range': orb_range,
                            'volume_surge': current_volume / avg_volume,
                            'risk_r': risk / atr if atr > 0 else 0,
                        }
                    })
            
            # Check for short breakout
            elif current_price < orb_low and current_volume > (volume_multiplier * avg_volume):
                risk = orb_high - current_price
                if risk > 0:
                    stop_loss = orb_high
                    take_profit = current_price - (take_profit_r * risk)
                    confidence = min(0.95, 0.5 + (current_volume / (volume_multiplier * avg_volume) - 1) * 0.3)
                    
                    signals.append({
                        'signal_type': 'ENTRY_SHORT',
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'confidence_score': confidence,
                        'meta': {
                            'orb_high': orb_high,
                            'orb_low': orb_low,
                            'orb_range': orb_range,
                            'volume_surge': current_volume / avg_volume,
                            'risk_r': risk / atr if atr > 0 else 0,
                        }
                    })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating ORB signals for {symbol}: {e}", exc_info=True)
            return []
    
    def _generate_momentum_signals(
        self,
        symbol: str,
        timeframe: str,
        lookback_candles: int,
        parameters: Dict
    ) -> List[Dict[str, Any]]:
        """
        Momentum Breakout (Ross Cameron style)
        
        Logic:
        1. Pre-market gapper > 15%
        2. Volume surge > 2x average
        3. 5-min breakout above VWAP
        4. RSI > 60 for longs
        """
        gap_threshold = parameters.get('gap_threshold', 15.0)  # 15%
        volume_multiplier = parameters.get('volume_multiplier', 2.0)
        risk_per_trade = parameters.get('risk_per_trade', 0.01)
        take_profit_r = parameters.get('take_profit_r', 2.0)
        rsi_threshold = parameters.get('rsi_threshold', 60.0)
        
        logger.info(f"Generating Momentum signals for {symbol} (gap>{gap_threshold}%, timeframe={timeframe})")
        
        try:
            ohlcv_df = self._fetch_ohlcv_data(symbol, timeframe, lookback_candles)
            if ohlcv_df is None or len(ohlcv_df) < 20:
                logger.warning(f"Insufficient data for {symbol}")
                return []
            
            # Calculate gap (pre-market to current)
            if len(ohlcv_df) < 2:
                return []
            
            # Get previous day's close (approximate from first candle)
            prev_close = float(ohlcv_df.iloc[0]['open'])
            current_price = float(ohlcv_df.iloc[-1]['close'])
            gap_pct = ((current_price - prev_close) / prev_close) * 100
            
            # Check gap threshold
            if abs(gap_pct) < gap_threshold:
                logger.debug(f"Skipping {symbol}: gap {gap_pct:.2f}% < threshold {gap_threshold}%")
                return []
            
            # Calculate VWAP
            vwap = self._calculate_vwap(ohlcv_df)
            if vwap is None:
                return []
            
            # Calculate RSI
            rsi = self._calculate_rsi(ohlcv_df, period=14)
            if rsi is None:
                return []
            
            # Calculate average volume
            avg_volume = ohlcv_df['volume'].rolling(20).mean().iloc[-1]
            if pd.isna(avg_volume) or avg_volume == 0:
                avg_volume = ohlcv_df['volume'].mean()
            
            current_volume = float(ohlcv_df.iloc[-1]['volume'])
            atr = self._calculate_atr(ohlcv_df, period=14)
            if atr is None or atr == 0:
                return []
            
            signals = []
            
            # Long momentum setup
            if gap_pct > gap_threshold and current_price > vwap and rsi > rsi_threshold and current_volume > (volume_multiplier * avg_volume):
                risk = current_price - (current_price - 2 * atr)  # Stop below recent low
                if risk > 0:
                    stop_loss = current_price - 2 * atr
                    take_profit = current_price + (take_profit_r * risk)
                    confidence = min(0.95, 0.5 + (gap_pct / gap_threshold - 1) * 0.2 + (current_volume / (volume_multiplier * avg_volume) - 1) * 0.2)
                    
                    signals.append({
                        'signal_type': 'ENTRY_LONG',
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'confidence_score': confidence,
                        'meta': {
                            'gap_pct': gap_pct,
                            'vwap': vwap,
                            'rsi': rsi,
                            'volume_surge': current_volume / avg_volume,
                            'risk_r': risk / atr if atr > 0 else 0,
                        }
                    })
            
            # Short momentum setup (gap down)
            elif gap_pct < -gap_threshold and current_price < vwap and rsi < (100 - rsi_threshold) and current_volume > (volume_multiplier * avg_volume):
                risk = (current_price + 2 * atr) - current_price
                if risk > 0:
                    stop_loss = current_price + 2 * atr
                    take_profit = current_price - (take_profit_r * risk)
                    confidence = min(0.95, 0.5 + (abs(gap_pct) / gap_threshold - 1) * 0.2 + (current_volume / (volume_multiplier * avg_volume) - 1) * 0.2)
                    
                    signals.append({
                        'signal_type': 'ENTRY_SHORT',
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'confidence_score': confidence,
                        'meta': {
                            'gap_pct': gap_pct,
                            'vwap': vwap,
                            'rsi': rsi,
                            'volume_surge': current_volume / avg_volume,
                            'risk_r': risk / atr if atr > 0 else 0,
                        }
                    })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating Momentum signals for {symbol}: {e}", exc_info=True)
            return []
    
    def _generate_supply_demand_signals(
        self,
        symbol: str,
        timeframe: str,
        lookback_candles: int,
        parameters: Dict
    ) -> List[Dict[str, Any]]:
        """
        Supply/Demand Zone Reversal (Steven Hart style)
        
        Logic:
        1. Identify S/D zones (swing fractals)
        2. Pin bar rejection at zone edge
        3. Momentum confirmation
        4. 1:2 RR minimum
        """
        risk_reward_ratio = parameters.get('risk_reward_ratio', 2.0)
        risk_per_trade = parameters.get('risk_per_trade', 0.01)
        zone_lookback = parameters.get('zone_lookback', 20)
        
        logger.info(f"Generating Supply/Demand signals for {symbol} (RR={risk_reward_ratio}, timeframe={timeframe})")
        
        try:
            ohlcv_df = self._fetch_ohlcv_data(symbol, timeframe, lookback_candles)
            if ohlcv_df is None or len(ohlcv_df) < zone_lookback + 5:
                logger.warning(f"Insufficient data for {symbol}")
                return []
            
            # Identify swing highs and lows (fractals)
            swing_highs, swing_lows = self._identify_swing_points(ohlcv_df, lookback=zone_lookback)
            
            if not swing_highs and not swing_lows:
                return []
            
            current_candle = ohlcv_df.iloc[-1]
            current_price = float(current_candle['close'])
            current_high = float(current_candle['high'])
            current_low = float(current_candle['low'])
            current_open = float(current_candle['open'])
            
            # Detect pin bar (body < 30% of range, long wick)
            candle_range = current_high - current_low
            body_size = abs(current_price - current_open)
            is_pin_bar = candle_range > 0 and (body_size / candle_range) < 0.3
            
            atr = self._calculate_atr(ohlcv_df, period=14)
            if atr is None or atr == 0:
                return []
            
            signals = []
            
            # Check for demand zone (support) - pin bar with long lower wick near swing low
            for swing_low in swing_lows:
                zone_top = swing_low + (0.5 * atr)  # Zone extends 0.5 ATR above swing low
                zone_bottom = swing_low - (0.5 * atr)  # Zone extends 0.5 ATR below swing low
                
                if zone_bottom <= current_price <= zone_top and is_pin_bar:
                    lower_wick = min(current_open, current_close) - current_low
                    upper_wick = current_high - max(current_open, current_close)
                    
                    # Pin bar with long lower wick (bullish rejection)
                    if lower_wick > upper_wick * 2 and lower_wick > (candle_range * 0.4):
                        # Calculate momentum (price velocity)
                        momentum = self._calculate_momentum(ohlcv_df, period=5)
                        if momentum and momentum > 0:  # Upward momentum
                            risk = current_price - zone_bottom
                            if risk > 0:
                                stop_loss = zone_bottom
                                take_profit = current_price + (risk_reward_ratio * risk)
                                confidence = min(0.95, 0.6 + (lower_wick / candle_range) * 0.2)
                                
                                signals.append({
                                    'signal_type': 'ENTRY_LONG',
                                    'price': current_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'confidence_score': confidence,
                                    'meta': {
                                        'zone_type': 'demand',
                                        'zone_top': zone_top,
                                        'zone_bottom': zone_bottom,
                                        'pin_bar_ratio': lower_wick / candle_range,
                                        'momentum': momentum,
                                        'risk_r': risk / atr if atr > 0 else 0,
                                    }
                                })
            
            # Check for supply zone (resistance) - pin bar with long upper wick near swing high
            for swing_high in swing_highs:
                zone_top = swing_high + (0.5 * atr)
                zone_bottom = swing_high - (0.5 * atr)
                
                if zone_bottom <= current_price <= zone_top and is_pin_bar:
                    lower_wick = min(current_open, current_close) - current_low
                    upper_wick = current_high - max(current_open, current_close)
                    
                    # Pin bar with long upper wick (bearish rejection)
                    if upper_wick > lower_wick * 2 and upper_wick > (candle_range * 0.4):
                        momentum = self._calculate_momentum(ohlcv_df, period=5)
                        if momentum and momentum < 0:  # Downward momentum
                            risk = zone_top - current_price
                            if risk > 0:
                                stop_loss = zone_top
                                take_profit = current_price - (risk_reward_ratio * risk)
                                confidence = min(0.95, 0.6 + (upper_wick / candle_range) * 0.2)
                                
                                signals.append({
                                    'signal_type': 'ENTRY_SHORT',
                                    'price': current_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'confidence_score': confidence,
                                    'meta': {
                                        'zone_type': 'supply',
                                        'zone_top': zone_top,
                                        'zone_bottom': zone_bottom,
                                        'pin_bar_ratio': upper_wick / candle_range,
                                        'momentum': momentum,
                                        'risk_r': risk / atr if atr > 0 else 0,
                                    }
                                })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating Supply/Demand signals for {symbol}: {e}", exc_info=True)
            return []
    
    def _generate_fade_orb_signals(
        self,
        symbol: str,
        timeframe: str,
        lookback_candles: int,
        parameters: Dict
    ) -> List[Dict[str, Any]]:
        """
        Fade ORB (Trading Champ style - inverse ORB)
        
        Logic:
        1. Detect false ORB breakout
        2. Enter opposite direction on 50% retrace
        3. MACD divergence confirmation
        4. 1:3 RR target
        """
        risk_reward_ratio = parameters.get('risk_reward_ratio', 3.0)
        risk_per_trade = parameters.get('risk_per_trade', 0.01)
        orb_minutes = parameters.get('orb_minutes', 15)
        retrace_pct = parameters.get('retrace_pct', 0.5)  # 50% retrace
        
        logger.info(f"Generating Fade ORB signals for {symbol} (RR={risk_reward_ratio}, timeframe={timeframe})")
        
        try:
            ohlcv_df = self._fetch_ohlcv_data(symbol, timeframe, lookback_candles)
            if ohlcv_df is None or len(ohlcv_df) < 20:
                logger.warning(f"Insufficient data for {symbol}")
                return []
            
            timeframe_minutes = self._parse_timeframe(timeframe)
            if timeframe_minutes is None:
                return []
            
            # Calculate ORB range
            orb_candles = max(1, int(orb_minutes / timeframe_minutes))
            if len(ohlcv_df) < orb_candles + 10:
                return []
            
            orb_slice = ohlcv_df.head(orb_candles)
            orb_high = orb_slice['high'].max()
            orb_low = orb_slice['low'].min()
            orb_range = orb_high - orb_low
            orb_mid = (orb_high + orb_low) / 2
            
            # Look for false breakout (price breaks ORB then retraces)
            post_orb_df = ohlcv_df.iloc[orb_candles:]
            if len(post_orb_df) < 5:
                return []
            
            # Check if there was a breakout
            breakout_high = post_orb_df['high'].max()
            breakout_low = post_orb_df['low'].min()
            current_price = float(ohlcv_df.iloc[-1]['close'])
            
            atr = self._calculate_atr(ohlcv_df, period=14)
            if atr is None or atr == 0:
                return []
            
            # Calculate MACD for divergence
            macd_line, signal_line, histogram = self._calculate_macd(ohlcv_df)
            
            signals = []
            
            # False breakout to the upside (fade long)
            if breakout_high > orb_high and current_price < orb_high:
                # Check if price retraced 50% of the breakout
                breakout_range = breakout_high - orb_high
                retrace_level = orb_high - (retrace_pct * breakout_range)
                
                if current_price <= retrace_level:
                    # Check for MACD bearish divergence (price made higher high, MACD made lower high)
                    if macd_line is not None and len(macd_line) >= 2:
                        recent_macd = macd_line.iloc[-1]
                        prev_macd = macd_line.iloc[-2]
                        
                        # Bearish divergence: price up but MACD down
                        if recent_macd < prev_macd:
                            risk = orb_high - current_price
                            if risk > 0:
                                stop_loss = orb_high + (0.5 * atr)  # Stop above ORB high
                                take_profit = current_price - (risk_reward_ratio * risk)
                                confidence = min(0.95, 0.65 + (breakout_range / orb_range) * 0.2)
                                
                                signals.append({
                                    'signal_type': 'ENTRY_SHORT',
                                    'price': current_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'confidence_score': confidence,
                                    'meta': {
                                        'orb_high': orb_high,
                                        'orb_low': orb_low,
                                        'breakout_high': breakout_high,
                                        'retrace_pct': retrace_pct,
                                        'macd_divergence': 'bearish',
                                        'risk_r': risk / atr if atr > 0 else 0,
                                    }
                                })
            
            # False breakout to the downside (fade short)
            elif breakout_low < orb_low and current_price > orb_low:
                breakout_range = orb_low - breakout_low
                retrace_level = orb_low + (retrace_pct * breakout_range)
                
                if current_price >= retrace_level:
                    if macd_line is not None and len(macd_line) >= 2:
                        recent_macd = macd_line.iloc[-1]
                        prev_macd = macd_line.iloc[-2]
                        
                        # Bullish divergence: price down but MACD up
                        if recent_macd > prev_macd:
                            risk = current_price - orb_low
                            if risk > 0:
                                stop_loss = orb_low - (0.5 * atr)  # Stop below ORB low
                                take_profit = current_price + (risk_reward_ratio * risk)
                                confidence = min(0.95, 0.65 + (breakout_range / orb_range) * 0.2)
                                
                                signals.append({
                                    'signal_type': 'ENTRY_LONG',
                                    'price': current_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'confidence_score': confidence,
                                    'meta': {
                                        'orb_high': orb_high,
                                        'orb_low': orb_low,
                                        'breakout_low': breakout_low,
                                        'retrace_pct': retrace_pct,
                                        'macd_divergence': 'bullish',
                                        'risk_r': risk / atr if atr > 0 else 0,
                                    }
                                })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating Fade ORB signals for {symbol}: {e}", exc_info=True)
            return []


class RAHAOrchestrator:
    """
    ML Orchestration Layer
    Combines multiple strategies with user behavior and regime detection
    """
    
    def __init__(self):
        self.strategy_engine = RAHAStrategyEngine()
    
    def orchestrate_signals(
        self,
        user,
        symbol: str,
        timeframe: str = "5m",
        enabled_strategies: Optional[List[StrategyVersion]] = None
    ) -> List[Dict[str, Any]]:
        """
        Orchestrate signals from multiple strategies with ML personalization.
        
        Args:
            user: User instance
            symbol: Stock symbol
            timeframe: Candle timeframe
            enabled_strategies: List of user's enabled strategies
        
        Returns:
            Unified list of signals with confidence scores
        """
        if not enabled_strategies:
            from .raha_models import UserStrategySettings
            settings = UserStrategySettings.objects.filter(user=user, enabled=True)
            enabled_strategies = [s.strategy_version for s in settings]
        
        all_signals = []
        
        # Generate signals from each enabled strategy
        for strategy_version in enabled_strategies:
            try:
                # Get user's parameters with optimal params fallback
                # Priority: user override > Optuna-optimized > hardcoded default
                from .raha_models import UserStrategySettings
                try:
                    user_settings = UserStrategySettings.objects.get(
                        user=user,
                        strategy_version=strategy_version,
                        enabled=True
                    )
                    user_params = user_settings.parameters or {}
                except UserStrategySettings.DoesNotExist:
                    user_params = {}

                # Load Optuna-optimized params from strategy version config
                optimal_params = {}
                if strategy_version.config_schema:
                    optimal_params = strategy_version.config_schema.get('optimal_params', {})

                # Merge: optimal params as base, user overrides on top
                parameters = {**optimal_params, **user_params}
                
                # Generate signals
                signals = self.strategy_engine.generate_signals(
                    strategy_version=strategy_version,
                    symbol=symbol,
                    timeframe=timeframe,
                    parameters=parameters
                )
                
                # Add strategy metadata
                for signal in signals:
                    signal['strategy_name'] = strategy_version.strategy.name
                    signal['strategy_version_id'] = str(strategy_version.id)
                
                all_signals.extend(signals)
            except Exception as e:
                logger.error(f"Error generating signals for {strategy_version.strategy.name}: {e}", exc_info=True)
        
        # ML orchestration
        if all_signals:
            # 1. Regime detection
            regime = self._detect_regime(symbol, timeframe)
            
            # 2. User behavior scoring
            behavior_score = self._score_user_behavior(user, symbol)
            
            # 3. Confidence adjustment based on regime and behavior
            for signal in all_signals:
                original_confidence = signal.get('confidence_score', 0.5)
                
                # Adjust for regime
                regime_multiplier = self._get_regime_multiplier(signal, regime)
                
                # Adjust for user behavior
                behavior_multiplier = 0.8 + (behavior_score * 0.4)  # 0.8 to 1.2 range
                
                # Final confidence
                adjusted_confidence = original_confidence * regime_multiplier * behavior_multiplier
                signal['confidence_score'] = min(0.95, max(0.1, adjusted_confidence))
                signal['meta'] = signal.get('meta', {})
                signal['meta']['regime'] = regime
                signal['meta']['behavior_score'] = behavior_score
                signal['meta']['original_confidence'] = original_confidence
            
            # 4. Filter and rank signals
            all_signals = sorted(all_signals, key=lambda x: x.get('confidence_score', 0), reverse=True)
            # Keep top 5 signals per symbol
            all_signals = all_signals[:5]
        
        return all_signals
    
    def _detect_regime(self, symbol: str, timeframe: str) -> str:
        """Detect market regime using DayTradingFeatureService"""
        try:
            ohlcv_df = self.strategy_engine._fetch_ohlcv_data(symbol, timeframe, 100)
            if ohlcv_df is None or len(ohlcv_df) < 20:
                return 'UNKNOWN'
            
            # Resample to 1m and 5m if needed
            ohlcv_1m = ohlcv_df
            ohlcv_5m = ohlcv_df
            
            if timeframe not in ['1m', '1']:
                # Resample to 1m for feature extraction
                if 'timestamp' in ohlcv_df.columns:
                    ohlcv_df.set_index('timestamp', inplace=True)
                ohlcv_1m = ohlcv_df.resample('1T').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).reset_index()
            
            if timeframe not in ['5m', '5']:
                # Resample to 5m
                if 'timestamp' in ohlcv_df.columns:
                    ohlcv_df.set_index('timestamp', inplace=True)
                ohlcv_5m = ohlcv_df.resample('5T').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).reset_index()
            
            # Use feature service to detect regime
            features = self.strategy_engine.feature_service.extract_all_features(
                ohlcv_1m, ohlcv_5m, symbol
            )
            
            is_trend = features.get('is_trend_regime', 0.0) > 0.5
            is_range = features.get('is_range_regime', 0.0) > 0.5
            is_volatile = features.get('volatility_regime', 0.0) > 0.5
            
            if is_trend:
                return 'TRENDING'
            elif is_range:
                return 'RANGING'
            elif is_volatile:
                return 'VOLATILE'
            else:
                return 'NEUTRAL'
        except Exception as e:
            logger.warning(f"Error detecting regime for {symbol}: {e}")
            return 'UNKNOWN'
    
    def _score_user_behavior(self, user, symbol: str) -> float:
        """Score user behavior (0.0 to 1.0) based on historical performance"""
        try:
            from .signal_performance_models import SignalPerformance, DayTradingSignal
            
            # Get user's recent signal performance
            recent_signals = DayTradingSignal.objects.filter(
                user=user,
                symbol=symbol
            ).order_by('-created_at')[:20]
            
            if not recent_signals.exists():
                return 0.5  # Neutral score for new users
            
            # Get performance outcomes
            signal_ids = [s.id for s in recent_signals]
            performances = SignalPerformance.objects.filter(
                signal_id__in=signal_ids
            )
            
            if not performances.exists():
                return 0.5
            
            # Calculate win rate
            wins = performances.filter(outcome='WIN').count()
            total = performances.count()
            win_rate = wins / total if total > 0 else 0.5
            
            # Calculate average R-multiple
            avg_pnl = performances.aggregate(avg=Avg('pnl_percent'))['avg'] or 0
            # Normalize to 0-1 (assuming -10% to +10% range)
            normalized_pnl = max(0, min(1, (avg_pnl + 10) / 20))
            
            # Combined score (weighted: 60% win rate, 40% avg P&L)
            behavior_score = (win_rate * 0.6) + (normalized_pnl * 0.4)
            
            return float(behavior_score)
        except Exception as e:
            logger.warning(f"Error scoring user behavior: {e}")
            return 0.5
    
    def _get_regime_multiplier(self, signal: Dict, regime: str) -> float:
        """Get confidence multiplier based on regime fit"""
        signal_type = signal.get('signal_type', '')
        strategy_name = signal.get('strategy_name', '').lower()
        
        # Regime-specific multipliers
        multipliers = {
            'TRENDING': {
                'momentum': 1.2,  # Momentum strategies excel in trends
                'orb': 1.0,
                'supply_demand': 0.9,
                'fade': 0.7,  # Fades struggle in trends
            },
            'RANGING': {
                'momentum': 0.8,
                'orb': 0.9,
                'supply_demand': 1.1,  # S/D zones work well in ranges
                'fade': 1.2,  # Fades excel in ranges
            },
            'VOLATILE': {
                'momentum': 1.1,
                'orb': 1.0,
                'supply_demand': 0.9,
                'fade': 0.8,
            },
            'NEUTRAL': {
                'momentum': 1.0,
                'orb': 1.0,
                'supply_demand': 1.0,
                'fade': 1.0,
            }
        }
        
        # Determine strategy type
        if 'momentum' in strategy_name:
            strategy_key = 'momentum'
        elif 'orb' in strategy_name and 'fade' not in strategy_name:
            strategy_key = 'orb'
        elif 'supply' in strategy_name or 'demand' in strategy_name:
            strategy_key = 'supply_demand'
        elif 'fade' in strategy_name:
            strategy_key = 'fade'
        else:
            strategy_key = 'orb'  # Default
        
        return multipliers.get(regime, {}).get(strategy_key, 1.0)

