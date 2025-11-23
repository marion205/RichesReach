"""
Swing Trading Engine - Phase 2: Breadth of Alphas
Generates 2-5 day swing trading signals using daily bars and multi-day patterns.
"""
import os
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class SwingTradingEngine:
    """
    Generates swing trading signals (2-5 day holds) using three strategies:
    1. Swing Momentum: Catch multi-day moves
    2. Swing Breakout: Enter on EOD breakouts
    3. Swing Mean Reversion: Fade extremes
    """
    
    def __init__(self):
        self.polygon_key = os.getenv('POLYGON_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        # Core universe for swing trading (large-cap, liquid stocks)
        self.core_universe = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ',
            'WMT', 'PG', 'MA', 'UNH', 'HD', 'DIS', 'BAC', 'ADBE', 'NFLX', 'CRM',
            'PYPL', 'INTC', 'CMCSA', 'PEP', 'TMO', 'COST', 'AVGO', 'CSCO', 'ABT', 'NKE',
            'MRK', 'TXN', 'QCOM', 'ACN', 'DHR', 'VZ', 'LIN', 'NEE', 'WFC', 'PM'
        ]
    
    async def generate_swing_signals(
        self,
        strategy: str = 'MOMENTUM',
        limit: int = 5,
        use_dynamic_discovery: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate swing trading signals for the specified strategy.
        
        Args:
            strategy: 'MOMENTUM', 'BREAKOUT', or 'MEAN_REVERSION'
            limit: Maximum number of signals to return
            use_dynamic_discovery: Whether to use dynamic universe from Polygon movers
        
        Returns:
            List of signal dictionaries
        """
        cache_key = f"swing_trading:{strategy}:v1:dynamic_{use_dynamic_discovery}"
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"✅ Cache hit for {strategy} swing signals")
            return cached
        
        logger.info(f"Generating {strategy} swing signals (limit={limit})")
        
        # Get universe
        universe_source = 'DYNAMIC_MOVERS' if use_dynamic_discovery else 'CORE'
        universe = []
        
        if use_dynamic_discovery:
            universe = await self._get_dynamic_universe_from_polygon()
            if not universe or len(universe) < 10:
                universe = self.core_universe
                universe_source = 'CORE'
        else:
            universe = self.core_universe
        
        # Fetch daily data for all symbols in parallel
        start_time = datetime.now()
        tasks = [self._fetch_daily_data(symbol) for symbol in universe[:50]]  # Limit to 50 for performance
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process signals based on strategy
        signals = []
        provider_counts = {'polygon': 0, 'finnhub': 0, 'alpha_vantage': 0}
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue
            if result and result[0] is not None:
                symbol, daily_bars, provider = result
                if provider:
                    provider_counts[provider] = provider_counts.get(provider, 0) + 1
                
                # Generate signal based on strategy
                signal = None
                if strategy == 'MOMENTUM':
                    signal = await self._generate_momentum_signal(symbol, daily_bars)
                elif strategy == 'BREAKOUT':
                    signal = await self._generate_breakout_signal(symbol, daily_bars)
                elif strategy == 'MEAN_REVERSION':
                    signal = await self._generate_mean_reversion_signal(symbol, daily_bars)
                
                if signal:
                    signal['universe_source'] = universe_source
                    signals.append(signal)
        
        # Sort by score and limit
        signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        signals = signals[:limit]
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            "SwingTradingSignalsSummary",
            extra={
                "strategy": strategy,
                "universe_size": len(universe),
                "qualified": len(signals),
                "returned": len(signals),
                "provider_counts": provider_counts,
                "duration_ms": int(elapsed * 1000),
                "universe_source": universe_source,
            },
        )
        
        # Cache for 1 hour (daily data changes less frequently)
        if signals:
            cache.set(cache_key, signals, 3600)
        
        return signals
    
    async def _get_dynamic_universe_from_polygon(self, max_symbols: int = 100) -> List[str]:
        """Get dynamic universe from Polygon top movers (similar to day trading)."""
        if not self.polygon_key:
            return []
        
        try:
            url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/gainers"
            params = {'apiKey': self.polygon_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        symbols = []
                        for item in results[:max_symbols]:
                            ticker = item.get('ticker', {}).get('ticker', '')
                            if ticker and len(ticker) <= 5:  # Valid ticker
                                price = item.get('lastQuote', {}).get('last', {}).get('price', 0) or \
                                        item.get('day', {}).get('c', 0)
                                volume = item.get('day', {}).get('v', 0)
                                
                                # Basic filters for swing trading
                                if price >= 5 and price <= 500 and volume >= 500_000:
                                    symbols.append(ticker)
                        
                        return symbols[:max_symbols]
        except Exception as e:
            logger.debug(f"Dynamic universe fetch failed: {e}")
        
        return []
    
    async def _fetch_daily_data(self, symbol: str) -> Tuple[Optional[str], Optional[List], Optional[str]]:
        """Fetch daily bars for a symbol. Returns (symbol, bars, provider) or (None, None, None)."""
        # Try Polygon first
        if self.polygon_key:
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
                params = {
                    'adjusted': 'true',
                    'sort': 'asc',
                    'limit': 30,
                    'apiKey': self.polygon_key
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=2.0)) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = data.get('results', [])
                            if results and len(results) >= 10:  # Need at least 10 days
                                return (symbol, results, 'polygon')
            except Exception as e:
                logger.debug(f"Polygon daily data failed for {symbol}: {e}")
        
        # Try Finnhub as fallback
        if self.finnhub_key:
            try:
                end_timestamp = int(datetime.now().timestamp())
                start_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())
                url = f"https://finnhub.io/api/v1/stock/candle"
                params = {
                    'symbol': symbol,
                    'resolution': 'D',
                    'from': start_timestamp,
                    'to': end_timestamp,
                    'token': self.finnhub_key
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=2.0)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('s') == 'ok' and data.get('c'):
                                closes = data.get('c', [])
                                opens = data.get('o', [])
                                highs = data.get('h', [])
                                lows = data.get('l', [])
                                volumes = data.get('v', [])
                                timestamps = data.get('t', [])
                                
                                if len(closes) >= 10:
                                    bars = []
                                    for i in range(len(closes)):
                                        bars.append({
                                            't': timestamps[i] * 1000,  # Convert to ms
                                            'o': opens[i],
                                            'h': highs[i],
                                            'l': lows[i],
                                            'c': closes[i],
                                            'v': volumes[i]
                                        })
                                    return (symbol, bars, 'finnhub')
            except Exception as e:
                logger.debug(f"Finnhub daily data failed for {symbol}: {e}")
        
        return (None, None, None)
    
    async def _generate_momentum_signal(self, symbol: str, bars: List[Dict]) -> Optional[Dict[str, Any]]:
        """Generate swing momentum signal (catch multi-day moves)."""
        if not bars or len(bars) < 10:
            return None
        
        try:
            # Calculate 5-day momentum
            current_price = float(bars[-1].get('c', 0))
            price_5d_ago = float(bars[-6].get('c', current_price)) if len(bars) >= 6 else current_price
            momentum_5d = (current_price - price_5d_ago) / price_5d_ago if price_5d_ago > 0 else 0
            
            # Calculate relative volume (5-day avg vs 20-day avg)
            recent_volumes = [float(b.get('v', 0)) for b in bars[-5:]]
            older_volumes = [float(b.get('v', 0)) for b in bars[-20:-5]] if len(bars) >= 20 else recent_volumes
            avg_recent_vol = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            avg_older_vol = sum(older_volumes) / len(older_volumes) if older_volumes else avg_recent_vol
            rvol_5d = (avg_recent_vol / avg_older_vol) if avg_older_vol > 0 else 1.0
            
            # Calculate ATR (1-day)
            high_low_spreads = []
            for bar in bars[-10:]:
                high = float(bar.get('h', current_price))
                low = float(bar.get('l', current_price))
                if high > 0 and low > 0:
                    high_low_spreads.append(high - low)
            atr_1d = sum(high_low_spreads) / len(high_low_spreads) if high_low_spreads else current_price * 0.02
            
            # Filter: Need positive momentum and volume confirmation
            if momentum_5d < 0.02 or rvol_5d < 1.2:  # At least 2% momentum, 20% volume increase
                return None
            
            # Determine side
            side = 'LONG' if momentum_5d > 0 else 'SHORT'
            
            # Calculate score
            momentum_score = abs(momentum_5d) * 100  # Scale to 0-10 range
            volume_score = min(5.0, (rvol_5d - 1.0) * 5)  # Volume boost
            score = momentum_score + volume_score
            
            # Risk parameters (2-5 day hold)
            stop_pct = 0.04  # 4% stop for swing trades
            stop = round(current_price * (1 - stop_pct) if side == 'LONG' else current_price * (1 + stop_pct), 2)
            
            target1_pct = 0.06  # 6% first target
            target2_pct = 0.10  # 10% second target
            targets = [
                round(current_price * (1 + target1_pct) if side == 'LONG' else current_price * (1 - target1_pct), 2),
                round(current_price * (1 + target2_pct) if side == 'LONG' else current_price * (1 - target2_pct), 2)
            ]
            
            return {
                'symbol': symbol,
                'side': side,
                'strategy': 'MOMENTUM',
                'score': round(score, 2),
                'features': {
                    'momentum5d': round(momentum_5d, 4),
                    'rvol5d': round(rvol_5d, 2),
                    'atr1d': round(atr_1d, 2),
                    'breakoutStrength': round(abs(momentum_5d), 4),
                },
                'risk': {
                    'atr1d': round(atr_1d, 2),
                    'sizeShares': 100,
                    'stop': stop,
                    'targets': targets,
                    'holdDays': 3  # Expected 3-day hold
                },
                'entry_price': current_price,
                'notes': f"Momentum: {momentum_5d*100:.1f}% over 5 days, {rvol_5d:.1f}x volume"
            }
        except Exception as e:
            logger.debug(f"Error generating momentum signal for {symbol}: {e}")
            return None
    
    async def _generate_breakout_signal(self, symbol: str, bars: List[Dict]) -> Optional[Dict[str, Any]]:
        """Generate swing breakout signal (enter on EOD breakouts)."""
        if not bars or len(bars) < 20:
            return None
        
        try:
            current_price = float(bars[-1].get('c', 0))
            current_high = float(bars[-1].get('h', current_price))
            
            # Find 20-day high
            highs_20d = [float(b.get('h', 0)) for b in bars[-20:]]
            high_20d = max(highs_20d) if highs_20d else current_price
            
            # Check if breaking above 20-day high
            breakout_strength = (current_high - high_20d) / high_20d if high_20d > 0 else 0
            
            if breakout_strength < 0.01:  # Need at least 1% breakout
                return None
            
            # Volume confirmation
            recent_volumes = [float(b.get('v', 0)) for b in bars[-5:]]
            older_volumes = [float(b.get('v', 0)) for b in bars[-20:-5]]
            avg_recent_vol = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            avg_older_vol = sum(older_volumes) / len(older_volumes) if older_volumes else avg_recent_vol
            rvol_5d = (avg_recent_vol / avg_older_vol) if avg_older_vol > 0 else 1.0
            
            if rvol_5d < 1.3:  # Need 30% volume increase
                return None
            
            # Calculate ATR
            high_low_spreads = []
            for bar in bars[-10:]:
                high = float(bar.get('h', current_price))
                low = float(bar.get('l', current_price))
                if high > 0 and low > 0:
                    high_low_spreads.append(high - low)
            atr_1d = sum(high_low_spreads) / len(high_low_spreads) if high_low_spreads else current_price * 0.02
            
            side = 'LONG'  # Breakouts are typically long
            
            # Score based on breakout strength and volume
            breakout_score = breakout_strength * 200  # Scale
            volume_score = min(5.0, (rvol_5d - 1.0) * 5)
            score = breakout_score + volume_score
            
            # Risk parameters
            stop_pct = 0.035  # 3.5% stop
            stop = round(current_price * (1 - stop_pct), 2)
            
            target1_pct = 0.07  # 7% first target
            target2_pct = 0.12  # 12% second target
            targets = [
                round(current_price * (1 + target1_pct), 2),
                round(current_price * (1 + target2_pct), 2)
            ]
            
            return {
                'symbol': symbol,
                'side': side,
                'strategy': 'BREAKOUT',
                'score': round(score, 2),
                'features': {
                    'breakoutStrength': round(breakout_strength, 4),
                    'rvol5d': round(rvol_5d, 2),
                    'atr1d': round(atr_1d, 2),
                    'high20d': round(high_20d, 2),
                },
                'risk': {
                    'atr1d': round(atr_1d, 2),
                    'sizeShares': 100,
                    'stop': stop,
                    'targets': targets,
                    'holdDays': 4  # Expected 4-day hold
                },
                'entry_price': current_price,
                'notes': f"Breakout: {breakout_strength*100:.1f}% above 20d high, {rvol_5d:.1f}x volume"
            }
        except Exception as e:
            logger.debug(f"Error generating breakout signal for {symbol}: {e}")
            return None
    
    async def _generate_mean_reversion_signal(self, symbol: str, bars: List[Dict]) -> Optional[Dict[str, Any]]:
        """Generate swing mean reversion signal (fade extremes)."""
        if not bars or len(bars) < 20:
            return None
        
        try:
            current_price = float(bars[-1].get('c', 0))
            
            # Calculate 20-day moving average
            closes_20d = [float(b.get('c', 0)) for b in bars[-20:]]
            ma_20d = sum(closes_20d) / len(closes_20d) if closes_20d else current_price
            
            # Distance from MA
            dist_from_ma = (current_price - ma_20d) / ma_20d if ma_20d > 0 else 0
            
            # Look for extreme moves (oversold or overbought)
            # For mean reversion, we want stocks that have moved too far from MA
            if abs(dist_from_ma) < 0.05:  # Need at least 5% deviation
                return None
            
            # RSI-like calculation (simplified)
            gains = []
            losses = []
            for i in range(1, min(15, len(bars))):
                change = float(bars[-i].get('c', 0)) - float(bars[-i-1].get('c', 0))
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0.01  # Avoid division by zero
            rs = avg_gain / avg_loss if avg_loss > 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            # Mean reversion: fade overbought (RSI > 70) or oversold (RSI < 30)
            if rsi > 70:
                side = 'SHORT'  # Fade overbought
                reversion_potential = (rsi - 50) / 50  # How extreme
            elif rsi < 30:
                side = 'LONG'  # Fade oversold
                reversion_potential = (50 - rsi) / 50
            else:
                return None  # Not extreme enough
            
            # Calculate ATR
            high_low_spreads = []
            for bar in bars[-10:]:
                high = float(bar.get('h', current_price))
                low = float(bar.get('l', current_price))
                if high > 0 and low > 0:
                    high_low_spreads.append(high - low)
            atr_1d = sum(high_low_spreads) / len(high_low_spreads) if high_low_spreads else current_price * 0.02
            
            # Score based on RSI extremity and distance from MA
            rsi_score = reversion_potential * 10
            ma_score = min(5.0, abs(dist_from_ma) * 50)
            score = rsi_score + ma_score
            
            # Risk parameters (tighter stops for mean reversion)
            stop_pct = 0.03  # 3% stop
            stop = round(current_price * (1 - stop_pct) if side == 'LONG' else current_price * (1 + stop_pct), 2)
            
            target1_pct = 0.05  # 5% first target (mean reversion targets are smaller)
            target2_pct = 0.08  # 8% second target
            targets = [
                round(current_price * (1 + target1_pct) if side == 'LONG' else current_price * (1 - target1_pct), 2),
                round(current_price * (1 + target2_pct) if side == 'LONG' else current_price * (1 - target2_pct), 2)
            ]
            
            return {
                'symbol': symbol,
                'side': side,
                'strategy': 'MEAN_REVERSION',
                'score': round(score, 2),
                'features': {
                    'rsi': round(rsi, 2),
                    'distFromMA20': round(dist_from_ma, 4),
                    'atr1d': round(atr_1d, 2),
                    'reversionPotential': round(reversion_potential, 4),
                },
                'risk': {
                    'atr1d': round(atr_1d, 2),
                    'sizeShares': 100,
                    'stop': stop,
                    'targets': targets,
                    'holdDays': 2  # Expected 2-day hold (mean reversion is faster)
                },
                'entry_price': current_price,
                'notes': f"Mean reversion: RSI {rsi:.1f}, {dist_from_ma*100:.1f}% from MA20"
            }
        except Exception as e:
            logger.debug(f"Error generating mean reversion signal for {symbol}: {e}")
            return None

