"""
Advanced Intraday Features Calculator
Sophisticated technical analysis with machine learning features
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

from ..market.providers.base import MarketDataProvider, Quote, OHLCV


@dataclass
class AdvancedFeatures:
    """Advanced intraday trading features"""
    symbol: str
    timestamp: datetime
    
    # Price Action Features
    price_momentum: Dict[str, float]
    volatility_features: Dict[str, float]
    trend_features: Dict[str, float]
    
    # Volume Profile Features
    volume_profile: Dict[str, float]
    order_flow: Dict[str, float]
    liquidity_features: Dict[str, float]
    
    # Technical Indicators (Advanced)
    oscillators: Dict[str, float]
    trend_indicators: Dict[str, float]
    volatility_indicators: Dict[str, float]
    
    # Market Microstructure
    microstructure: Dict[str, float]
    spread_analysis: Dict[str, float]
    depth_analysis: Dict[str, float]
    
    # Machine Learning Features
    ml_features: Dict[str, float]
    anomaly_scores: Dict[str, float]
    pattern_recognition: Dict[str, float]
    
    # Cross-Asset Features
    sector_correlation: Dict[str, float]
    market_regime: Dict[str, float]
    macro_features: Dict[str, float]
    
    # Composite Scores
    composite_score: float
    confidence_score: float
    risk_score: float


class AdvancedIntradayCalculator:
    """Advanced intraday feature calculator with ML capabilities"""
    
    def __init__(self, market_data_provider: MarketDataProvider):
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        
        # Feature calculation parameters
        self.params = {
            "lookback_periods": [5, 10, 20, 50, 100],
            "volatility_windows": [5, 10, 20],
            "volume_windows": [5, 10, 20],
            "correlation_periods": [20, 50],
            "ml_features": ["price_change", "volume_change", "volatility", "momentum"]
        }
        
        # Initialize ML models
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        
        # Feature cache for performance
        self.feature_cache = {}
        self.cache_ttl = timedelta(minutes=1)
    
    async def calculate_advanced_features(self, symbol: str) -> Optional[AdvancedFeatures]:
        """Calculate comprehensive advanced features"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            if cache_key in self.feature_cache:
                cached_time, features = self.feature_cache[cache_key]
                if datetime.now() - cached_time < self.cache_ttl:
                    return features
            
            # Get market data
            quotes = await self.market_data_provider.get_quotes([symbol])
            if symbol not in quotes:
                return None
            
            quote = quotes[symbol]
            
            # Get extended historical data
            ohlcv_data = await self.market_data_provider.get_ohlcv(
                symbol, "1m", limit=200
            )
            
            if len(ohlcv_data) < 50:
                return None
            
            # Convert to pandas DataFrame for easier analysis
            df = self._ohlcv_to_dataframe(ohlcv_data)
            
            # Calculate all feature categories
            features = AdvancedFeatures(
                symbol=symbol,
                timestamp=datetime.now(),
                **await self._calculate_all_advanced_features(df, quote)
            )
            
            # Cache the results
            self.feature_cache[cache_key] = (datetime.now(), features)
            
            return features
            
        except Exception as e:
            self.logger.error(f"❌ Advanced feature calculation failed for {symbol}: {e}")
            return None
    
    def _ohlcv_to_dataframe(self, ohlcv_data: List[OHLCV]) -> pd.DataFrame:
        """Convert OHLCV data to pandas DataFrame"""
        data = []
        for candle in ohlcv_data:
            data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Calculate additional columns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['hl2'] = (df['high'] + df['low']) / 2
        df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
        df['ohlc4'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        return df
    
    async def _calculate_all_advanced_features(
        self, 
        df: pd.DataFrame, 
        quote: Quote
    ) -> Dict[str, Any]:
        """Calculate all advanced feature categories"""
        
        # Price Action Features
        price_features = self._calculate_price_action_features(df)
        
        # Volume Profile Features
        volume_features = self._calculate_volume_profile_features(df)
        
        # Technical Indicators
        technical_features = self._calculate_advanced_technical_indicators(df)
        
        # Market Microstructure
        microstructure_features = self._calculate_microstructure_features(df, quote)
        
        # Machine Learning Features
        ml_features = self._calculate_ml_features(df)
        
        # Cross-Asset Features
        cross_asset_features = await self._calculate_cross_asset_features(df.index[-1])
        
        # Composite Scores
        composite_scores = self._calculate_composite_scores(
            price_features, volume_features, technical_features, 
            microstructure_features, ml_features
        )
        
        return {
            **price_features,
            **volume_features,
            **technical_features,
            **microstructure_features,
            **ml_features,
            **cross_asset_features,
            **composite_scores
        }
    
    def _calculate_price_action_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate advanced price action features"""
        
        # Multi-timeframe momentum
        momentum_features = {}
        for period in self.params["lookback_periods"]:
            if len(df) >= period:
                momentum_features[f"momentum_{period}"] = df['close'].pct_change(period).iloc[-1]
                momentum_features[f"momentum_ma_{period}"] = df['close'].rolling(period).mean().iloc[-1]
        
        # Volatility features
        volatility_features = {}
        for window in self.params["volatility_windows"]:
            if len(df) >= window:
                returns = df['returns'].dropna()
                volatility_features[f"volatility_{window}"] = returns.rolling(window).std().iloc[-1]
                volatility_features[f"volatility_annualized_{window}"] = volatility_features[f"volatility_{window}"] * np.sqrt(252 * 24 * 60)  # Annualized for 1-min data
        
        # Trend features
        trend_features = {}
        if len(df) >= 20:
            # Linear regression slope
            x = np.arange(len(df))
            y = df['close'].values
            slope, _, r_value, _, _ = stats.linregress(x, y)
            trend_features['trend_slope'] = slope
            trend_features['trend_r_squared'] = r_value ** 2
            
            # Price position in range
            high_20 = df['high'].rolling(20).max().iloc[-1]
            low_20 = df['low'].rolling(20).min().iloc[-1]
            current_price = df['close'].iloc[-1]
            trend_features['price_position'] = (current_price - low_20) / (high_20 - low_20) if high_20 != low_20 else 0.5
        
        return {
            "price_momentum": momentum_features,
            "volatility_features": volatility_features,
            "trend_features": trend_features
        }
    
    def _calculate_volume_profile_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume profile and order flow features"""
        
        volume_features = {}
        
        # Volume-weighted features
        for window in self.params["volume_windows"]:
            if len(df) >= window:
                vwap = (df['close'] * df['volume']).rolling(window).sum() / df['volume'].rolling(window).sum()
                volume_features[f"vwap_{window}"] = vwap.iloc[-1]
                volume_features[f"vwap_distance_{window}"] = (df['close'].iloc[-1] - vwap.iloc[-1]) / vwap.iloc[-1]
        
        # Volume profile analysis
        if len(df) >= 50:
            # Volume at price levels
            price_bins = pd.cut(df['close'], bins=10)
            volume_profile = df.groupby(price_bins)['volume'].sum()
            volume_features['volume_profile_skew'] = stats.skew(volume_profile.values)
            volume_features['volume_profile_kurtosis'] = stats.kurtosis(volume_profile.values)
        
        # Order flow features
        order_flow_features = {}
        if len(df) >= 20:
            # Buy/sell pressure estimation
            price_changes = df['close'].diff()
            volume_changes = df['volume'].diff()
            
            # Simple order flow proxy
            buy_volume = df[price_changes > 0]['volume'].sum()
            sell_volume = df[price_changes < 0]['volume'].sum()
            order_flow_features['buy_sell_ratio'] = buy_volume / (sell_volume + 1e-8)
            order_flow_features['net_order_flow'] = (buy_volume - sell_volume) / (buy_volume + sell_volume + 1e-8)
        
        # Liquidity features
        liquidity_features = {}
        if len(df) >= 10:
            # Volume stability
            volume_std = df['volume'].rolling(10).std().iloc[-1]
            volume_mean = df['volume'].rolling(10).mean().iloc[-1]
            liquidity_features['volume_stability'] = 1 - (volume_std / volume_mean) if volume_mean > 0 else 0
            
            # Volume trend
            volume_trend = df['volume'].rolling(10).apply(lambda x: stats.linregress(range(len(x)), x)[0]).iloc[-1]
            liquidity_features['volume_trend'] = volume_trend
        
        return {
            "volume_profile": volume_features,
            "order_flow": order_flow_features,
            "liquidity_features": liquidity_features
        }
    
    def _calculate_advanced_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate advanced technical indicators"""
        
        oscillators = {}
        trend_indicators = {}
        volatility_indicators = {}
        
        if len(df) >= 14:
            # RSI with multiple periods
            for period in [14, 21, 34]:
                if len(df) >= period:
                    rsi = self._calculate_rsi(df['close'], period)
                    oscillators[f"rsi_{period}"] = rsi
            
            # Stochastic Oscillator
            if len(df) >= 14:
                stoch_k, stoch_d = self._calculate_stochastic(df, 14, 3)
                oscillators['stoch_k'] = stoch_k
                oscillators['stoch_d'] = stoch_d
            
            # Williams %R
            if len(df) >= 14:
                williams_r = self._calculate_williams_r(df, 14)
                oscillators['williams_r'] = williams_r
        
        if len(df) >= 20:
            # MACD with multiple settings
            macd_line, signal_line, histogram = self._calculate_macd(df['close'], 12, 26, 9)
            trend_indicators['macd_line'] = macd_line
            trend_indicators['macd_signal'] = signal_line
            trend_indicators['macd_histogram'] = histogram
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df['close'], 20, 2)
            trend_indicators['bb_upper'] = bb_upper
            trend_indicators['bb_middle'] = bb_middle
            trend_indicators['bb_lower'] = bb_lower
            trend_indicators['bb_position'] = (df['close'].iloc[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
            trend_indicators['bb_width'] = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
        
        if len(df) >= 14:
            # ATR
            atr = self._calculate_atr(df, 14)
            volatility_indicators['atr'] = atr
            volatility_indicators['atr_percent'] = atr / df['close'].iloc[-1] if df['close'].iloc[-1] > 0 else 0
            
            # Average True Range Percentage
            volatility_indicators['atrp'] = (atr / df['close'].iloc[-1]) * 100 if df['close'].iloc[-1] > 0 else 0
        
        return {
            "oscillators": oscillators,
            "trend_indicators": trend_indicators,
            "volatility_indicators": volatility_indicators
        }
    
    def _calculate_microstructure_features(self, df: pd.DataFrame, quote: Quote) -> Dict[str, Any]:
        """Calculate market microstructure features"""
        
        microstructure = {}
        spread_analysis = {}
        depth_analysis = {}
        
        # Spread analysis
        if quote.ask > 0 and quote.bid > 0:
            spread = quote.ask - quote.bid
            mid_price = (quote.ask + quote.bid) / 2
            spread_analysis['spread_absolute'] = spread
            spread_analysis['spread_bps'] = (spread / mid_price) * 10000
            spread_analysis['spread_percent'] = (spread / mid_price) * 100
            
            # Effective spread estimation
            if len(df) >= 10:
                price_changes = df['close'].diff().abs()
                avg_price_change = price_changes.rolling(10).mean().iloc[-1]
                spread_analysis['effective_spread_ratio'] = spread / avg_price_change if avg_price_change > 0 else 0
        
        # Depth analysis (mock - would use real Level 2 data)
        depth_analysis['bid_depth'] = quote.bid_size if hasattr(quote, 'bid_size') else 1000
        depth_analysis['ask_depth'] = quote.ask_size if hasattr(quote, 'ask_size') else 1000
        depth_analysis['depth_imbalance'] = (depth_analysis['bid_depth'] - depth_analysis['ask_depth']) / (depth_analysis['bid_depth'] + depth_analysis['ask_depth'])
        
        # Price impact estimation
        if len(df) >= 20:
            volume_changes = df['volume'].diff()
            price_changes = df['close'].diff()
            correlation = price_changes.corr(volume_changes)
            microstructure['price_volume_correlation'] = correlation if not pd.isna(correlation) else 0
        
        return {
            "microstructure": microstructure,
            "spread_analysis": spread_analysis,
            "depth_analysis": depth_analysis
        }
    
    def _calculate_ml_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate machine learning features"""
        
        ml_features = {}
        anomaly_scores = {}
        pattern_recognition = {}
        
        if len(df) >= 50:
            # Feature engineering for ML
            features_df = pd.DataFrame()
            features_df['price_change'] = df['close'].pct_change()
            features_df['volume_change'] = df['volume'].pct_change()
            features_df['volatility'] = df['returns'].rolling(10).std()
            features_df['momentum'] = df['close'].pct_change(5)
            
            # Remove NaN values
            features_df = features_df.dropna()
            
            if len(features_df) >= 20:
                # Anomaly detection
                try:
                    anomaly_scores['isolation_forest'] = self.isolation_forest.fit_predict(features_df.values[-20:])[-1]
                except:
                    anomaly_scores['isolation_forest'] = 0
                
                # Statistical features
                ml_features['price_skewness'] = stats.skew(features_df['price_change'].values)
                ml_features['price_kurtosis'] = stats.kurtosis(features_df['price_change'].values)
                ml_features['volume_skewness'] = stats.skew(features_df['volume_change'].values)
                ml_features['volume_kurtosis'] = stats.kurtosis(features_df['volume_change'].values)
        
        # Pattern recognition
        if len(df) >= 20:
            # Support and resistance levels
            highs = df['high'].rolling(20).max()
            lows = df['low'].rolling(20).min()
            current_price = df['close'].iloc[-1]
            
            pattern_recognition['support_distance'] = (current_price - lows.iloc[-1]) / current_price
            pattern_recognition['resistance_distance'] = (highs.iloc[-1] - current_price) / current_price
            
            # Breakout detection
            pattern_recognition['breakout_strength'] = (current_price - highs.iloc[-2]) / highs.iloc[-2] if len(highs) >= 2 else 0
        
        return {
            "ml_features": ml_features,
            "anomaly_scores": anomaly_scores,
            "pattern_recognition": pattern_recognition
        }
    
    async def _calculate_cross_asset_features(self, timestamp: datetime) -> Dict[str, Any]:
        """Calculate cross-asset and macro features"""
        
        # Mock implementation - would integrate with real macro data
        sector_correlation = {
            'tech_correlation': np.random.uniform(0.6, 0.9),
            'finance_correlation': np.random.uniform(0.4, 0.7),
            'energy_correlation': np.random.uniform(0.3, 0.6)
        }
        
        market_regime = {
            'vix_level': np.random.uniform(15, 25),
            'treasury_yield': np.random.uniform(3.5, 4.5),
            'dollar_strength': np.random.uniform(-0.1, 0.1)
        }
        
        macro_features = {
            'economic_sentiment': np.random.uniform(0.4, 0.8),
            'risk_appetite': np.random.uniform(0.3, 0.7),
            'liquidity_conditions': np.random.uniform(0.5, 0.9)
        }
        
        return {
            "sector_correlation": sector_correlation,
            "market_regime": market_regime,
            "macro_features": macro_features
        }
    
    def _calculate_composite_scores(
        self, 
        price_features: Dict, 
        volume_features: Dict, 
        technical_features: Dict,
        microstructure_features: Dict, 
        ml_features: Dict
    ) -> Dict[str, float]:
        """Calculate composite scores"""
        
        # Extract key features for scoring
        momentum_score = 0
        volume_score = 0
        technical_score = 0
        microstructure_score = 0
        ml_score = 0
        
        # Price momentum scoring
        if 'price_momentum' in price_features:
            momentum_values = [v for v in price_features['price_momentum'].values() if not pd.isna(v)]
            if momentum_values:
                momentum_score = np.mean(momentum_values)
        
        # Volume scoring
        if 'volume_profile' in volume_features:
            vwap_distance = volume_features['volume_profile'].get('vwap_distance_10', 0)
            volume_score = max(0, min(1, 1 - abs(vwap_distance) * 10))
        
        # Technical scoring
        if 'oscillators' in technical_features:
            rsi_14 = technical_features['oscillators'].get('rsi_14', 50)
            technical_score = 1 - abs(rsi_14 - 50) / 50
        
        # Microstructure scoring
        if 'spread_analysis' in microstructure_features:
            spread_bps = microstructure_features['spread_analysis'].get('spread_bps', 10)
            microstructure_score = max(0, 1 - spread_bps / 20)
        
        # ML scoring
        if 'pattern_recognition' in ml_features:
            breakout_strength = ml_features['pattern_recognition'].get('breakout_strength', 0)
            ml_score = max(0, min(1, abs(breakout_strength) * 10))
        
        # Composite score
        composite_score = (
            momentum_score * 0.25 +
            volume_score * 0.2 +
            technical_score * 0.2 +
            microstructure_score * 0.2 +
            ml_score * 0.15
        )
        
        # Confidence score (based on feature quality)
        confidence_score = min(0.95, composite_score + 0.1)
        
        # Risk score (inverse of confidence)
        risk_score = max(0.05, 1 - confidence_score)
        
        return {
            "composite_score": composite_score,
            "confidence_score": confidence_score,
            "risk_score": risk_score
        }
    
    # Helper methods for technical indicators
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator"""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent.iloc[-1], d_percent.iloc[-1]
    
    def _calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Williams %R"""
        high_max = df['high'].rolling(window=period).max()
        low_min = df['low'].rolling(window=period).min()
        williams_r = -100 * ((high_max - df['close']) / (high_max - low_min))
        return williams_r.iloc[-1]
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band.iloc[-1], sma.iloc[-1], lower_band.iloc[-1]
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr.iloc[-1]


# Factory function
async def create_advanced_calculator(api_key: str) -> AdvancedIntradayCalculator:
    """Create advanced calculator with Polygon provider"""
    from ..market.providers.polygon import PolygonProvider
    provider = PolygonProvider(api_key=api_key)
    return AdvancedIntradayCalculator(provider)
