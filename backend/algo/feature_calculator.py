"""
Real-Time Feature Calculation for Day Trading
Live calculation of technical indicators and trading signals
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..market.providers.base import MarketDataProvider, Quote, OHLCV


@dataclass
class TradingFeatures:
    """Real-time trading features"""
    symbol: str
    timestamp: datetime
    
    # Price-based features
    momentum_15m: float
    momentum_5m: float
    momentum_1m: float
    
    # Volume features
    rvol_10m: float
    rvol_5m: float
    volume_spike: float
    
    # Technical indicators
    rsi_14: float
    macd_signal: float
    bollinger_position: float
    vwap_distance: float
    
    # Market microstructure
    spread_bps: float
    bid_ask_ratio: float
    order_flow_imbalance: float
    
    # Volatility features
    atr_5m: float
    atr_15m: float
    volatility_regime: str
    
    # Breakout features
    breakout_pct: float
    resistance_level: float
    support_level: float
    
    # Catalyst features
    news_sentiment: float
    earnings_proximity: float
    catalyst_score: float
    
    # Composite score
    composite_score: float


class RealTimeFeatureCalculator:
    """Calculates real-time trading features"""
    
    def __init__(self, market_data_provider: MarketDataProvider):
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        
        # Feature calculation parameters
        self.params = {
            "momentum_periods": [1, 5, 15],  # minutes
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "bollinger_period": 20,
            "bollinger_std": 2,
            "atr_period": 14,
            "volume_lookback": 30
        }
    
    async def calculate_features(self, symbol: str) -> Optional[TradingFeatures]:
        """Calculate comprehensive trading features for a symbol"""
        try:
            # Get current quote
            quotes = await self.market_data_provider.get_quotes([symbol])
            if symbol not in quotes:
                return None
            
            quote = quotes[symbol]
            
            # Get historical OHLCV data
            ohlcv_data = await self.market_data_provider.get_ohlcv(
                symbol, "1m", limit=100
            )
            
            if len(ohlcv_data) < 50:  # Need minimum data
                return None
            
            # Calculate all features
            features = TradingFeatures(
                symbol=symbol,
                timestamp=datetime.now(),
                **await self._calculate_all_features(quote, ohlcv_data)
            )
            
            return features
            
        except Exception as e:
            self.logger.error(f"❌ Feature calculation failed for {symbol}: {e}")
            return None
    
    async def _calculate_all_features(
        self, 
        quote: Quote, 
        ohlcv_data: List[OHLCV]
    ) -> Dict:
        """Calculate all trading features"""
        
        prices = [candle.close for candle in ohlcv_data]
        volumes = [candle.volume for candle in ohlcv_data]
        highs = [candle.high for candle in ohlcv_data]
        lows = [candle.low for candle in ohlcv_data]
        
        # Momentum features
        momentum_features = self._calculate_momentum_features(prices)
        
        # Volume features
        volume_features = self._calculate_volume_features(volumes)
        
        # Technical indicators
        technical_features = self._calculate_technical_indicators(
            prices, highs, lows, volumes
        )
        
        # Market microstructure
        microstructure_features = self._calculate_microstructure_features(quote)
        
        # Volatility features
        volatility_features = self._calculate_volatility_features(
            highs, lows, prices
        )
        
        # Breakout features
        breakout_features = self._calculate_breakout_features(prices, highs, lows)
        
        # Catalyst features (mock for now)
        catalyst_features = self._calculate_catalyst_features(quote.symbol)
        
        # Combine all features
        all_features = {
            **momentum_features,
            **volume_features,
            **technical_features,
            **microstructure_features,
            **volatility_features,
            **breakout_features,
            **catalyst_features
        }
        
        # Calculate composite score
        all_features["composite_score"] = self._calculate_composite_score(all_features)
        
        return all_features
    
    def _calculate_momentum_features(self, prices: List[float]) -> Dict:
        """Calculate momentum features"""
        current_price = prices[-1]
        
        momentum_15m = (current_price - prices[-15]) / prices[-15] if len(prices) >= 15 else 0
        momentum_5m = (current_price - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        momentum_1m = (current_price - prices[-1]) / prices[-1] if len(prices) >= 1 else 0
        
        return {
            "momentum_15m": momentum_15m,
            "momentum_5m": momentum_5m,
            "momentum_1m": momentum_1m
        }
    
    def _calculate_volume_features(self, volumes: List[int]) -> Dict:
        """Calculate volume-based features"""
        if len(volumes) < 10:
            return {
                "rvol_10m": 1.0,
                "rvol_5m": 1.0,
                "volume_spike": 1.0
            }
        
        # Relative volume (recent vs average)
        recent_volume_10m = sum(volumes[-10:])
        avg_volume_10m = np.mean([sum(volumes[i:i+10]) for i in range(len(volumes)-20, len(volumes)-10)])
        rvol_10m = recent_volume_10m / max(avg_volume_10m, 1)
        
        recent_volume_5m = sum(volumes[-5:])
        avg_volume_5m = np.mean([sum(volumes[i:i+5]) for i in range(len(volumes)-15, len(volumes)-5)])
        rvol_5m = recent_volume_5m / max(avg_volume_5m, 1)
        
        # Volume spike (current vs recent average)
        current_volume = volumes[-1]
        recent_avg = np.mean(volumes[-10:])
        volume_spike = current_volume / max(recent_avg, 1)
        
        return {
            "rvol_10m": rvol_10m,
            "rvol_5m": rvol_5m,
            "volume_spike": volume_spike
        }
    
    def _calculate_technical_indicators(
        self, 
        prices: List[float], 
        highs: List[float], 
        lows: List[float], 
        volumes: List[int]
    ) -> Dict:
        """Calculate technical indicators"""
        
        # RSI
        rsi_14 = self._calculate_rsi(prices, 14)
        
        # MACD
        macd_signal = self._calculate_macd_signal(prices)
        
        # Bollinger Bands position
        bollinger_position = self._calculate_bollinger_position(prices)
        
        # VWAP distance
        vwap_distance = self._calculate_vwap_distance(prices, volumes)
        
        return {
            "rsi_14": rsi_14,
            "macd_signal": macd_signal,
            "bollinger_position": bollinger_position,
            "vwap_distance": vwap_distance
        }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd_signal(self, prices: List[float]) -> float:
        """Calculate MACD signal"""
        if len(prices) < 26:
            return 0.0
        
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd = ema_12 - ema_26
        
        # MACD signal line (9-period EMA of MACD)
        macd_values = [macd] * len(prices)  # Simplified
        signal = self._calculate_ema(macd_values, 9)
        
        return macd - signal
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1]
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_position(self, prices: List[float]) -> float:
        """Calculate position within Bollinger Bands"""
        if len(prices) < 20:
            return 0.5
        
        sma = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        
        current_price = prices[-1]
        
        if upper_band == lower_band:
            return 0.5
        
        position = (current_price - lower_band) / (upper_band - lower_band)
        return max(0, min(1, position))
    
    def _calculate_vwap_distance(self, prices: List[float], volumes: List[int]) -> float:
        """Calculate distance from VWAP"""
        if len(prices) != len(volumes):
            return 0.0
        
        pv = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)
        
        if total_volume == 0:
            return 0.0
        
        vwap = pv / total_volume
        current_price = prices[-1]
        
        return (current_price - vwap) / vwap
    
    def _calculate_microstructure_features(self, quote: Quote) -> Dict:
        """Calculate market microstructure features"""
        
        # Spread in basis points
        spread_bps = ((quote.ask - quote.bid) / quote.bid) * 10000
        
        # Bid-ask ratio
        bid_ask_ratio = quote.bid / quote.ask if quote.ask > 0 else 1.0
        
        # Order flow imbalance (mock)
        order_flow_imbalance = np.random.uniform(-0.5, 0.5)
        
        return {
            "spread_bps": spread_bps,
            "bid_ask_ratio": bid_ask_ratio,
            "order_flow_imbalance": order_flow_imbalance
        }
    
    def _calculate_volatility_features(
        self, 
        highs: List[float], 
        lows: List[float], 
        prices: List[float]
    ) -> Dict:
        """Calculate volatility features"""
        
        # ATR (Average True Range)
        atr_5m = self._calculate_atr(highs, lows, prices, 5)
        atr_15m = self._calculate_atr(highs, lows, prices, 15)
        
        # Volatility regime
        volatility_regime = self._determine_volatility_regime(atr_5m, atr_15m)
        
        return {
            "atr_5m": atr_5m,
            "atr_15m": atr_15m,
            "volatility_regime": volatility_regime
        }
    
    def _calculate_atr(
        self, 
        highs: List[float], 
        lows: List[float], 
        prices: List[float], 
        period: int
    ) -> float:
        """Calculate Average True Range"""
        if len(highs) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - prices[i-1])
            tr3 = abs(lows[i] - prices[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        if len(true_ranges) < period:
            return np.mean(true_ranges) if true_ranges else 0.0
        
        return np.mean(true_ranges[-period:])
    
    def _determine_volatility_regime(self, atr_5m: float, atr_15m: float) -> str:
        """Determine volatility regime"""
        if atr_5m > atr_15m * 1.5:
            return "HIGH"
        elif atr_5m < atr_15m * 0.7:
            return "LOW"
        else:
            return "NORMAL"
    
    def _calculate_breakout_features(
        self, 
        prices: List[float], 
        highs: List[float], 
        lows: List[float]
    ) -> Dict:
        """Calculate breakout features"""
        
        if len(prices) < 20:
            return {
                "breakout_pct": 0.0,
                "resistance_level": prices[-1],
                "support_level": prices[-1]
            }
        
        # Breakout percentage
        current_price = prices[-1]
        recent_high = max(highs[-20:])
        breakout_pct = (current_price - recent_high) / recent_high
        
        # Support and resistance levels
        resistance_level = max(highs[-20:])
        support_level = min(lows[-20:])
        
        return {
            "breakout_pct": breakout_pct,
            "resistance_level": resistance_level,
            "support_level": support_level
        }
    
    def _calculate_catalyst_features(self, symbol: str) -> Dict:
        """Calculate catalyst features (mock implementation)"""
        
        # Mock news sentiment
        news_sentiment = np.random.uniform(-1, 1)
        
        # Mock earnings proximity
        earnings_proximity = np.random.uniform(0, 1)
        
        # Composite catalyst score
        catalyst_score = (news_sentiment + earnings_proximity) / 2
        
        return {
            "news_sentiment": news_sentiment,
            "earnings_proximity": earnings_proximity,
            "catalyst_score": catalyst_score
        }
    
    def _calculate_composite_score(self, features: Dict) -> float:
        """Calculate composite trading score"""
        
        # Weighted combination of features
        score = (
            features["momentum_15m"] * 0.2 +
            features["rvol_10m"] * 0.15 +
            features["breakout_pct"] * 0.15 +
            features["catalyst_score"] * 0.1 +
            features["macd_signal"] * 0.1 +
            (1 - features["spread_bps"] / 100) * 0.1 +  # Lower spread is better
            features["volume_spike"] * 0.1 +
            features["atr_5m"] * 0.1
        )
        
        # Normalize to 0-1 range
        return max(0, min(1, (score + 1) / 2))


# Factory function
async def create_feature_calculator(api_key: str) -> RealTimeFeatureCalculator:
    """Create feature calculator with Polygon provider"""
    from ..market.providers.polygon import PolygonProvider
    provider = PolygonProvider(api_key=api_key)
    return RealTimeFeatureCalculator(provider)
