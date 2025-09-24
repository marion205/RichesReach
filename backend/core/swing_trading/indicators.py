"""
Technical Indicators for Swing Trading
Professional-grade implementation with proper error handling and validation
"""
import numpy as np
import pandas as pd
from typing import Union, Optional, Tuple
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Professional technical indicators implementation for swing trading
    """
    
    @staticmethod
    def ema(series: pd.Series, span: int, adjust: bool = False) -> pd.Series:
        """
        Exponential Moving Average
        
        Args:
            series: Price series (typically close prices)
            span: Period for EMA calculation
            adjust: Whether to use adjust=False for traditional EMA
            
        Returns:
            EMA series
        """
        if len(series) < span:
            logger.warning(f"Insufficient data for EMA({span}): {len(series)} points")
            return pd.Series(index=series.index, dtype=float)
        
        try:
            return series.ewm(span=span, adjust=adjust).mean()
        except Exception as e:
            logger.error(f"EMA calculation error: {e}")
            return pd.Series(index=series.index, dtype=float)
    
    @staticmethod
    def sma(series: pd.Series, window: int) -> pd.Series:
        """
        Simple Moving Average
        
        Args:
            series: Price series
            window: Period for SMA calculation
            
        Returns:
            SMA series
        """
        if len(series) < window:
            logger.warning(f"Insufficient data for SMA({window}): {len(series)} points")
            return pd.Series(index=series.index, dtype=float)
        
        try:
            return series.rolling(window=window).mean()
        except Exception as e:
            logger.error(f"SMA calculation error: {e}")
            return pd.Series(index=series.index, dtype=float)
    
    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index
        
        Args:
            series: Price series (typically close prices)
            period: RSI period (default 14)
            
        Returns:
            RSI series (0-100)
        """
        if len(series) < period + 1:
            logger.warning(f"Insufficient data for RSI({period}): {len(series)} points")
            return pd.Series(index=series.index, dtype=float)
        
        try:
            # Convert to float and handle NaN values
            s = series.astype(float)
            delta = s.diff()
            
            # Separate gains and losses
            up = delta.clip(lower=0)
            down = (-delta.clip(upper=0))
            
            # Calculate average gains and losses
            avg_up = up.rolling(window=period).mean()
            avg_down = down.rolling(window=period).mean()
            
            # Calculate RS and RSI
            rs = avg_up / avg_down.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            
            # Fill NaN values with 50 (neutral RSI)
            rsi = rsi.fillna(50.0)
            
            return rsi
            
        except Exception as e:
            logger.error(f"RSI calculation error: {e}")
            return pd.Series(index=series.index, dtype=float).fillna(50.0)
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average True Range
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period (default 14)
            
        Returns:
            ATR series
        """
        if len(df) < period + 1:
            logger.warning(f"Insufficient data for ATR({period}): {len(df)} points")
            return pd.Series(index=df.index, dtype=float)
        
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            
            # Calculate True Range components
            high_low = high - low
            high_close_prev = (high - close.shift()).abs()
            low_close_prev = (low - close.shift()).abs()
            
            # True Range is the maximum of the three
            tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
            
            # ATR is the moving average of True Range
            atr = tr.rolling(window=period).mean()
            
            return atr.fillna(method='bfill')
            
        except Exception as e:
            logger.error(f"ATR calculation error: {e}")
            return pd.Series(index=df.index, dtype=float)
    
    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        
        Args:
            series: Price series
            period: Period for moving average
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        if len(series) < period:
            logger.warning(f"Insufficient data for Bollinger Bands({period}): {len(series)} points")
            empty = pd.Series(index=series.index, dtype=float)
            return empty, empty, empty
        
        try:
            middle = series.rolling(window=period).mean()
            std = series.rolling(window=period).std()
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return upper, middle, lower
            
        except Exception as e:
            logger.error(f"Bollinger Bands calculation error: {e}")
            empty = pd.Series(index=series.index, dtype=float)
            return empty, empty, empty
    
    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)
        
        Args:
            series: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        if len(series) < slow:
            logger.warning(f"Insufficient data for MACD({fast},{slow},{signal}): {len(series)} points")
            empty = pd.Series(index=series.index, dtype=float)
            return empty, empty, empty
        
        try:
            ema_fast = TechnicalIndicators.ema(series, fast)
            ema_slow = TechnicalIndicators.ema(series, slow)
            
            macd_line = ema_fast - ema_slow
            signal_line = TechnicalIndicators.ema(macd_line, signal)
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
            
        except Exception as e:
            logger.error(f"MACD calculation error: {e}")
            empty = pd.Series(index=series.index, dtype=float)
            return empty, empty, empty
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            k_period: %K period
            d_period: %D period (SMA of %K)
            
        Returns:
            Tuple of (%K, %D)
        """
        if len(close) < k_period:
            logger.warning(f"Insufficient data for Stochastic({k_period},{d_period}): {len(close)} points")
            empty = pd.Series(index=close.index, dtype=float)
            return empty, empty
        
        try:
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return k_percent, d_percent
            
        except Exception as e:
            logger.error(f"Stochastic calculation error: {e}")
            empty = pd.Series(index=close.index, dtype=float)
            return empty, empty
    
    @staticmethod
    def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Volume Simple Moving Average
        
        Args:
            volume: Volume series
            period: SMA period
            
        Returns:
            Volume SMA series
        """
        if len(volume) < period:
            logger.warning(f"Insufficient data for Volume SMA({period}): {len(volume)} points")
            return pd.Series(index=volume.index, dtype=float)
        
        try:
            return volume.rolling(window=period).mean()
        except Exception as e:
            logger.error(f"Volume SMA calculation error: {e}")
            return pd.Series(index=volume.index, dtype=float)
    
    @staticmethod
    def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Volume ratio (current volume / average volume)
        
        Args:
            volume: Volume series
            period: Period for average volume calculation
            
        Returns:
            Volume ratio series
        """
        if len(volume) < period:
            logger.warning(f"Insufficient data for Volume Ratio({period}): {len(volume)} points")
            return pd.Series(index=volume.index, dtype=float)
        
        try:
            avg_volume = TechnicalIndicators.volume_sma(volume, period)
            return volume / avg_volume
        except Exception as e:
            logger.error(f"Volume ratio calculation error: {e}")
            return pd.Series(index=volume.index, dtype=float)
    
    @staticmethod
    def support_resistance(df: pd.DataFrame, window: int = 20, min_touches: int = 2) -> Tuple[pd.Series, pd.Series]:
        """
        Identify support and resistance levels
        
        Args:
            df: DataFrame with 'high', 'low' columns
            window: Window for local extrema detection
            min_touches: Minimum touches to confirm level
            
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            
            # Find local maxima and minima
            resistance = high.rolling(window=window, center=True).max() == high
            support = low.rolling(window=window, center=True).min() == low
            
            return support, resistance
            
        except Exception as e:
            logger.error(f"Support/Resistance calculation error: {e}")
            empty = pd.Series(index=df.index, dtype=bool)
            return empty, empty


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators for a DataFrame
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all indicators added
    """
    result_df = df.copy()
    
    try:
        # Price-based indicators
        result_df['ema_12'] = TechnicalIndicators.ema(df['close'], 12)
        result_df['ema_26'] = TechnicalIndicators.ema(df['close'], 26)
        result_df['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
        result_df['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
        
        # Momentum indicators
        result_df['rsi_14'] = TechnicalIndicators.rsi(df['close'], 14)
        result_df['macd'], result_df['macd_signal'], result_df['macd_histogram'] = TechnicalIndicators.macd(df['close'])
        result_df['stoch_k'], result_df['stoch_d'] = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
        
        # Volatility indicators
        result_df['atr_14'] = TechnicalIndicators.atr(df, 14)
        result_df['bb_upper'], result_df['bb_middle'], result_df['bb_lower'] = TechnicalIndicators.bollinger_bands(df['close'])
        
        # Volume indicators
        result_df['volume_sma_20'] = TechnicalIndicators.volume_sma(df['volume'], 20)
        result_df['volume_ratio'] = TechnicalIndicators.volume_ratio(df['volume'], 20)
        
        # Derived indicators
        result_df['ema_diff'] = (result_df['ema_12'] - result_df['ema_26']) / result_df['close']
        result_df['price_vs_sma20'] = (result_df['close'] - result_df['sma_20']) / result_df['sma_20']
        result_df['bb_position'] = (result_df['close'] - result_df['bb_lower']) / (result_df['bb_upper'] - result_df['bb_lower'])
        
        # Support and resistance
        result_df['support'], result_df['resistance'] = TechnicalIndicators.support_resistance(df)
        
        logger.info(f"Successfully calculated indicators for {len(df)} data points")
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
    
    return result_df


def validate_ohlcv_data(df: pd.DataFrame) -> bool:
    """
    Validate OHLCV data quality
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        True if data is valid, False otherwise
    """
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    # Check required columns
    if not all(col in df.columns for col in required_columns):
        logger.error(f"Missing required columns: {required_columns}")
        return False
    
    # Check for sufficient data
    if len(df) < 50:
        logger.warning(f"Insufficient data points: {len(df)}")
        return False
    
    # Check for null values
    if df[required_columns].isnull().any().any():
        logger.warning("Found null values in OHLCV data")
        return False
    
    # Check price relationships
    if not (df['high'] >= df['low']).all():
        logger.error("High prices are not always >= Low prices")
        return False
    
    if not (df['high'] >= df['open']).all():
        logger.error("High prices are not always >= Open prices")
        return False
    
    if not (df['high'] >= df['close']).all():
        logger.error("High prices are not always >= Close prices")
        return False
    
    if not (df['low'] <= df['open']).all():
        logger.error("Low prices are not always <= Open prices")
        return False
    
    if not (df['low'] <= df['close']).all():
        logger.error("Low prices are not always <= Close prices")
        return False
    
    # Check for negative prices
    if (df[['open', 'high', 'low', 'close']] <= 0).any().any():
        logger.error("Found non-positive prices")
        return False
    
    # Check for negative volume
    if (df['volume'] < 0).any():
        logger.error("Found negative volume")
        return False
    
    logger.info("OHLCV data validation passed")
    return True
