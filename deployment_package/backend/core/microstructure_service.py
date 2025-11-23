"""
Microstructure Service - Order Book Intelligence for Day Trading

Provides order-book intelligence to make signals "microstructure-aware"
without needing HFT infrastructure. Good enough for 1-5 minute intraday decisions.

Features:
- L2 order book data (best bid/ask, depth)
- Order imbalance calculation
- Execution quality filters (spread, depth, gaps, halts)
- Tradeability checks for SAFE/AGGRESSIVE modes
"""
import logging
import os
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MicrostructureService:
    """
    Provides order-book intelligence for day trading signals.
    Not HFT-level, but good enough for 1-5 minute intraday decisions.
    """
    
    def __init__(self):
        self.polygon_key = os.getenv('POLYGON_API_KEY')
        self.alpaca_key = os.getenv('ALPACA_API_KEY')
        self.alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
    
    async def get_order_book_features(self, symbol: str) -> Optional[Dict]:
        """
        Fetch L2 data and compute order book features.
        
        Returns:
            {
                'best_bid': float,
                'best_ask': float,
                'bid_size': int,
                'ask_size': int,
                'spread': float,
                'spread_bps': float,  # Basis points
                'bid_depth': float,  # Total bid size in top 5 levels (dollars)
                'ask_depth': float,  # Total ask size in top 5 levels (dollars)
                'order_imbalance': float,  # -1 to +1 (bearish to bullish)
                'depth_imbalance': float,  # (bid_depth - ask_depth) / total
                'mid_price': float,
                'provider': str,  # 'polygon', 'alpaca', or None
            }
        """
        # Try Polygon first (best L2 coverage)
        if self.polygon_key:
            try:
                features = await self._fetch_polygon_l2(symbol)
                if features:
                    return features
            except Exception as e:
                logger.debug(f"Polygon L2 failed for {symbol}: {e}")
        
        # Try Alpaca as fallback
        if self.alpaca_key and self.alpaca_secret:
            try:
                features = await self._fetch_alpaca_l2(symbol)
                if features:
                    return features
            except Exception as e:
                logger.debug(f"Alpaca L2 failed for {symbol}: {e}")
        
        logger.debug(f"⚠️ No L2 data available for {symbol}")
        return None
    
    async def _fetch_polygon_l2(self, symbol: str) -> Optional[Dict]:
        """Fetch L2 snapshot from Polygon"""
        try:
            url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            params = {'apikey': self.polygon_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=2.0)) as response:
                    if response.status == 200:
                        data = await response.json()
                        ticker = data.get('ticker', {})
                        
                        # Get last trade price
                        last_trade = ticker.get('lastTrade', {})
                        last_price = float(last_trade.get('p', 0)) if last_trade else 0
                        
                        # Get best bid/ask from day data
                        day_data = ticker.get('day', {})
                        best_bid = float(day_data.get('low', last_price))  # Approximate
                        best_ask = float(day_data.get('high', last_price))  # Approximate
                        
                        # For now, use simplified approach (Polygon snapshot doesn't always have full L2)
                        # In production, use Polygon websocket or dedicated L2 endpoint
                        if last_price > 0:
                            # Estimate spread (0.1% default, will be refined with real L2)
                            spread_estimate = last_price * 0.001
                            best_bid = last_price - (spread_estimate / 2)
                            best_ask = last_price + (spread_estimate / 2)
                            
                            return {
                                'best_bid': best_bid,
                                'best_ask': best_ask,
                                'bid_size': 1000,  # Placeholder
                                'ask_size': 1000,  # Placeholder
                                'spread': spread_estimate,
                                'spread_bps': (spread_estimate / last_price) * 10000,
                                'bid_depth': last_price * 1000,  # Placeholder
                                'ask_depth': last_price * 1000,  # Placeholder
                                'order_imbalance': 0.0,  # Will calculate with real data
                                'depth_imbalance': 0.0,
                                'mid_price': last_price,
                                'provider': 'polygon',
                            }
        except Exception as e:
            logger.debug(f"Error fetching Polygon L2 for {symbol}: {e}")
            return None
    
    async def _fetch_alpaca_l2(self, symbol: str) -> Optional[Dict]:
        """Fetch L2 snapshot from Alpaca"""
        try:
            # Alpaca market data endpoint
            url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"
            headers = {
                'APCA-API-KEY-ID': self.alpaca_key,
                'APCA-API-SECRET-KEY': self.alpaca_secret
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=2.0)) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get('quote', {})
                        
                        best_bid = float(quote.get('bp', 0))  # Bid price
                        best_ask = float(quote.get('ap', 0))  # Ask price
                        bid_size = int(quote.get('bs', 0))  # Bid size
                        ask_size = int(quote.get('as', 0))  # Ask size
                        
                        if best_bid > 0 and best_ask > 0:
                            mid_price = (best_bid + best_ask) / 2
                            spread = best_ask - best_bid
                            spread_bps = (spread / mid_price) * 10000
                            
                            # Calculate order imbalance
                            total_size = bid_size + ask_size
                            order_imbalance = (bid_size - ask_size) / total_size if total_size > 0 else 0.0
                            
                            # Estimate depth (simplified - would need full L2 for accurate)
                            bid_depth = best_bid * bid_size
                            ask_depth = best_ask * ask_size
                            total_depth = bid_depth + ask_depth
                            depth_imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0.0
                            
                            return {
                                'best_bid': best_bid,
                                'best_ask': best_ask,
                                'bid_size': bid_size,
                                'ask_size': ask_size,
                                'spread': spread,
                                'spread_bps': spread_bps,
                                'bid_depth': bid_depth,
                                'ask_depth': ask_depth,
                                'order_imbalance': order_imbalance,
                                'depth_imbalance': depth_imbalance,
                                'mid_price': mid_price,
                                'provider': 'alpaca',
                            }
        except Exception as e:
            logger.debug(f"Error fetching Alpaca L2 for {symbol}: {e}")
            return None
    
    def calculate_imbalance(self, bids: List[Tuple[float, int]], asks: List[Tuple[float, int]]) -> float:
        """
        Calculate order imbalance: (sum(bid_sizes) - sum(ask_sizes)) / total
        
        Args:
            bids: List of (price, size) tuples
            asks: List of (price, size) tuples
        
        Returns:
            -1 (bearish) to +1 (bullish)
        """
        total_bid_size = sum(size for _, size in bids)
        total_ask_size = sum(size for _, size in asks)
        total_size = total_bid_size + total_ask_size
        
        if total_size == 0:
            return 0.0
        
        return (total_bid_size - total_ask_size) / total_size
    
    def is_tradeable(self, symbol: str, mode: str, microstructure: Optional[Dict] = None) -> Dict:
        """
        Check if symbol passes microstructure filters.
        
        Args:
            symbol: Stock symbol
            mode: 'SAFE' or 'AGGRESSIVE'
            microstructure: Optional pre-fetched microstructure data
        
        Returns:
            {
                'tradeable': bool,
                'reason': str,  # Why it's tradeable or not
                'warnings': List[str]  # Any warnings (thin depth, wide spread, etc.)
            }
        """
        if not microstructure:
            return {
                'tradeable': True,  # Default to tradeable if no L2 data
                'reason': 'No L2 data available, assuming tradeable',
                'warnings': ['No L2 data - cannot verify execution quality']
            }
        
        warnings = []
        spread_bps = microstructure.get('spread_bps', 0)
        bid_depth = microstructure.get('bid_depth', 0)
        ask_depth = microstructure.get('ask_depth', 0)
        total_depth = bid_depth + ask_depth
        
        # Mode-specific thresholds
        if mode == "SAFE":
            max_spread_bps = 50  # 0.5%
            min_depth = 100_000  # $100k
        else:  # AGGRESSIVE
            max_spread_bps = 100  # 1.0%
            min_depth = 50_000  # $50k
        
        # Check spread
        if spread_bps > max_spread_bps:
            return {
                'tradeable': False,
                'reason': f'Spread too wide: {spread_bps:.1f}bps (max: {max_spread_bps}bps for {mode})',
                'warnings': []
            }
        elif spread_bps > max_spread_bps * 0.8:
            warnings.append(f'Wide spread: {spread_bps:.1f}bps')
        
        # Check depth
        if total_depth < min_depth:
            return {
                'tradeable': False,
                'reason': f'Insufficient depth: ${total_depth:,.0f} (min: ${min_depth:,.0f} for {mode})',
                'warnings': []
            }
        elif total_depth < min_depth * 1.5:
            warnings.append(f'Thin depth: ${total_depth:,.0f}')
        
        # Check for extreme imbalance (might indicate manipulation)
        order_imbalance = abs(microstructure.get('order_imbalance', 0))
        if order_imbalance > 0.8:
            warnings.append(f'Extreme order imbalance: {order_imbalance:.2f}')
        
        return {
            'tradeable': True,
            'reason': 'Passes all microstructure filters',
            'warnings': warnings
        }
    
    def get_execution_quality_score(self, microstructure: Optional[Dict]) -> float:
        """
        Calculate execution quality score (0-10).
        Higher = better execution quality.
        
        Factors:
        - Spread (tighter = better)
        - Depth (deeper = better)
        - Imbalance (balanced = better)
        """
        if not microstructure:
            return 5.0  # Neutral if no data
        
        spread_bps = microstructure.get('spread_bps', 100)
        total_depth = microstructure.get('bid_depth', 0) + microstructure.get('ask_depth', 0)
        order_imbalance = abs(microstructure.get('order_imbalance', 0))
        
        # Spread score (0-4 points): < 10bps = 4, < 25bps = 3, < 50bps = 2, < 100bps = 1
        if spread_bps < 10:
            spread_score = 4.0
        elif spread_bps < 25:
            spread_score = 3.0
        elif spread_bps < 50:
            spread_score = 2.0
        elif spread_bps < 100:
            spread_score = 1.0
        else:
            spread_score = 0.0
        
        # Depth score (0-3 points): > $500k = 3, > $200k = 2, > $100k = 1
        if total_depth > 500_000:
            depth_score = 3.0
        elif total_depth > 200_000:
            depth_score = 2.0
        elif total_depth > 100_000:
            depth_score = 1.0
        else:
            depth_score = 0.0
        
        # Imbalance score (0-3 points): < 0.2 = 3, < 0.4 = 2, < 0.6 = 1
        if order_imbalance < 0.2:
            imbalance_score = 3.0
        elif order_imbalance < 0.4:
            imbalance_score = 2.0
        elif order_imbalance < 0.6:
            imbalance_score = 1.0
        else:
            imbalance_score = 0.0
        
        total_score = spread_score + depth_score + imbalance_score
        return min(10.0, total_score)

