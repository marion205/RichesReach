"""
Live Universe Generation for Day Trading
Real-time symbol selection based on volume, volatility, and momentum
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

from ..market.providers.base import MarketDataProvider, Quote, OHLCV
from ..market.providers.polygon import PolygonProvider


@dataclass
class UniverseCriteria:
    """Criteria for universe selection"""
    min_volume: int = 1_000_000
    min_price: float = 5.0
    max_price: float = 1000.0
    min_avg_volume: int = 500_000
    max_symbols: int = 50
    volatility_threshold: float = 0.02  # 2% minimum volatility
    momentum_threshold: float = 0.01  # 1% minimum momentum


@dataclass
class UniverseSymbol:
    """Symbol with universe metrics"""
    symbol: str
    price: float
    volume: int
    avg_volume: float
    volatility: float
    momentum: float
    spread_bps: float
    score: float
    last_updated: datetime


class LiveUniverseGenerator:
    """Generates live trading universe based on real-time criteria"""
    
    def __init__(self, market_data_provider: MarketDataProvider):
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        self.criteria = UniverseCriteria()
        self.universe_cache = {}
        self.last_update = None
        
        # Predefined universe of liquid symbols
        self.base_universe = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER", "LYFT", "SQ",
            "ZM", "ROKU", "PTON", "DOCU", "SNOW", "PLTR", "CRWD", "OKTA",
            "TWLO", "NET", "DDOG", "ESTC", "MDB", "WDAY", "NOW", "TEAM",
            "SPOT", "SHOP", "SQ", "ROKU", "ZM", "PTON", "DOCU", "SNOW"
        ]
    
    async def generate_universe(self, mode: str = "SAFE") -> List[UniverseSymbol]:
        """Generate live trading universe based on mode"""
        try:
            self.logger.info(f"🔍 Generating {mode} universe...")
            
            # Adjust criteria based on mode
            if mode == "AGGRESSIVE":
                self.criteria.min_volume = 500_000
                self.criteria.volatility_threshold = 0.03
                self.criteria.momentum_threshold = 0.015
            else:  # SAFE mode
                self.criteria.min_volume = 1_000_000
                self.criteria.volatility_threshold = 0.02
                self.criteria.momentum_threshold = 0.01
            
            # Get current quotes for base universe
            quotes = await self.market_data_provider.get_quotes(self.base_universe)
            
            # Calculate metrics for each symbol
            universe_symbols = []
            for symbol in self.base_universe:
                if symbol not in quotes:
                    continue
                
                quote = quotes[symbol]
                
                # Get historical data for metrics
                ohlcv_data = await self.market_data_provider.get_ohlcv(
                    symbol, "5m", limit=100
                )
                
                if len(ohlcv_data) < 20:  # Need minimum data
                    continue
                
                # Calculate metrics
                metrics = await self._calculate_symbol_metrics(symbol, quote, ohlcv_data)
                
                if self._meets_criteria(metrics):
                    universe_symbols.append(metrics)
            
            # Sort by score and limit
            universe_symbols.sort(key=lambda x: x.score, reverse=True)
            universe_symbols = universe_symbols[:self.criteria.max_symbols]
            
            self.universe_cache[mode] = universe_symbols
            self.last_update = datetime.now()
            
            self.logger.info(f"✅ Generated {len(universe_symbols)} symbols for {mode} universe")
            return universe_symbols
            
        except Exception as e:
            self.logger.error(f"❌ Universe generation failed: {e}")
            return []
    
    async def _calculate_symbol_metrics(
        self, 
        symbol: str, 
        quote: Quote, 
        ohlcv_data: List[OHLCV]
    ) -> UniverseSymbol:
        """Calculate comprehensive metrics for a symbol"""
        
        # Price and volume metrics
        current_price = quote.price
        current_volume = quote.volume
        
        # Calculate average volume (20-day)
        volumes = [candle.volume for candle in ohlcv_data[-20:]]
        avg_volume = np.mean(volumes) if volumes else current_volume
        
        # Calculate volatility (20-day standard deviation of returns)
        prices = [candle.close for candle in ohlcv_data[-20:]]
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns) if len(returns) > 1 else 0
        
        # Calculate momentum (5-day price change)
        if len(prices) >= 5:
            momentum = (prices[-1] - prices[-5]) / prices[-5]
        else:
            momentum = 0
        
        # Calculate spread in basis points
        spread_bps = ((quote.ask - quote.bid) / quote.bid) * 10000
        
        # Calculate composite score
        score = self._calculate_score(
            current_volume, avg_volume, volatility, momentum, spread_bps
        )
        
        return UniverseSymbol(
            symbol=symbol,
            price=current_price,
            volume=current_volume,
            avg_volume=avg_volume,
            volatility=volatility,
            momentum=momentum,
            spread_bps=spread_bps,
            score=score,
            last_updated=datetime.now()
        )
    
    def _calculate_score(
        self, 
        volume: int, 
        avg_volume: float, 
        volatility: float, 
        momentum: float, 
        spread_bps: float
    ) -> float:
        """Calculate composite score for symbol ranking"""
        
        # Volume score (higher is better)
        volume_score = min(volume / avg_volume, 3.0)  # Cap at 3x average
        
        # Volatility score (moderate volatility preferred)
        vol_score = 1.0 - abs(volatility - 0.025) / 0.025  # Peak at 2.5%
        vol_score = max(0, min(vol_score, 1.0))
        
        # Momentum score (absolute momentum)
        momentum_score = min(abs(momentum) * 10, 1.0)  # Scale momentum
        
        # Spread score (lower spread is better)
        spread_score = max(0, 1.0 - spread_bps / 50.0)  # Penalty for wide spreads
        
        # Composite score
        score = (
            volume_score * 0.3 +
            vol_score * 0.25 +
            momentum_score * 0.25 +
            spread_score * 0.2
        )
        
        return score
    
    def _meets_criteria(self, metrics: UniverseSymbol) -> bool:
        """Check if symbol meets universe criteria"""
        return (
            metrics.price >= self.criteria.min_price and
            metrics.price <= self.criteria.max_price and
            metrics.volume >= self.criteria.min_volume and
            metrics.avg_volume >= self.criteria.min_avg_volume and
            metrics.volatility >= self.criteria.volatility_threshold and
            abs(metrics.momentum) >= self.criteria.momentum_threshold
        )
    
    async def get_top_movers(self, limit: int = 10) -> List[UniverseSymbol]:
        """Get top moving symbols by momentum"""
        try:
            quotes = await self.market_data_provider.get_quotes(self.base_universe)
            movers = []
            
            for symbol, quote in quotes.items():
                ohlcv_data = await self.market_data_provider.get_ohlcv(
                    symbol, "5m", limit=20
                )
                
                if len(ohlcv_data) >= 5:
                    prices = [candle.close for candle in ohlcv_data[-5:]]
                    momentum = (prices[-1] - prices[0]) / prices[0]
                    
                    movers.append(UniverseSymbol(
                        symbol=symbol,
                        price=quote.price,
                        volume=quote.volume,
                        avg_volume=quote.volume,
                        volatility=0,
                        momentum=momentum,
                        spread_bps=0,
                        score=abs(momentum),
                        last_updated=datetime.now()
                    ))
            
            movers.sort(key=lambda x: x.score, reverse=True)
            return movers[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Top movers failed: {e}")
            return []
    
    async def get_volume_leaders(self, limit: int = 10) -> List[UniverseSymbol]:
        """Get symbols with highest volume"""
        try:
            quotes = await self.market_data_provider.get_quotes(self.base_universe)
            volume_leaders = []
            
            for symbol, quote in quotes.items():
                volume_leaders.append(UniverseSymbol(
                    symbol=symbol,
                    price=quote.price,
                    volume=quote.volume,
                    avg_volume=quote.volume,
                    volatility=0,
                    momentum=0,
                    spread_bps=0,
                    score=quote.volume,
                    last_updated=datetime.now()
                ))
            
            volume_leaders.sort(key=lambda x: x.score, reverse=True)
            return volume_leaders[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Volume leaders failed: {e}")
            return []
    
    def get_cached_universe(self, mode: str) -> List[UniverseSymbol]:
        """Get cached universe if recent"""
        if mode in self.universe_cache:
            cache_age = datetime.now() - self.last_update
            if cache_age < timedelta(minutes=5):  # 5-minute cache
                return self.universe_cache[mode]
        return []


# Factory function
async def create_universe_generator(api_key: str) -> LiveUniverseGenerator:
    """Create universe generator with Polygon provider"""
    provider = PolygonProvider(api_key=api_key)
    return LiveUniverseGenerator(provider)
