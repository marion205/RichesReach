"""
Market Data Service Integration for Regime Detection

This module connects the RegimeDetector to the market data polling loop,
ensuring regime classification updates on each market close.

Regime state is cached (Redis/in-memory) for fast lookup by:
- Strategy Router (selects eligible strategies based on regime)
- Alert system (tracks regime shifts)
- UI (displays active regime and Flight Manual)
"""

import logging
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from datetime import datetime, timedelta
import json

from .options_regime_detector import RegimeDetector
from .polygon_options_flow_service import PolygonOptionsFlowService

logger = logging.getLogger(__name__)


class RegimeDetectionService:
    """
    Service that runs regime detection on market data and manages cache.
    
    Responsibilities:
    1. Fetch market data for a symbol (OHLCV + IV/RV)
    2. Run RegimeDetector on the data
    3. Cache regime state in Redis (or in-memory dict)
    4. Return regime + Flight Manual for UI/routing
    5. Emit alerts on regime shifts
    """
    
    def __init__(self, cache_backend: Optional[Any] = None, lookback_days: int = 60):
        """
        Initialize the RegimeDetectionService.
        
        Args:
            cache_backend: Redis client or dict-like cache (defaults to in-memory dict)
            lookback_days: Historical days to fetch for regime detection
        """
        self.detector = RegimeDetector()
        self.cache = cache_backend or {}
        self.lookback_days = lookback_days
        self.polygon_service = PolygonOptionsFlowService()
        
        logger.info(f"RegimeDetectionService initialized (lookback={lookback_days}d)")
    
    def get_market_data_for_symbol(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV + implied volatility + realized volatility for regime detection.
        
        This integrates with your existing market data provider (Polygon API, etc.)
        
        Args:
            symbol: Stock ticker (e.g., "AAPL")
        
        Returns:
            DataFrame with columns: ['close', 'high', 'low', 'iv', 'rv', 'volume']
            or None if data unavailable
        """
        # TODO: Implement actual data fetching
        # This is a placeholder that shows expected data structure
        
        # Expected flow:
        # 1. Query Polygon historical bars for symbol (last 60 days)
        # 2. Query options IV surface (use ATM IV as proxy for 30-day IV)
        # 3. Calculate realized vol (std dev of returns over rolling 30-day window)
        # 4. Combine into DataFrame
        
        logger.debug(f"Fetching market data for {symbol} (lookback={self.lookback_days}d)")
        
        # Placeholder: would be replaced with actual API calls
        return None
    
    def update_regime(self, symbol: str, df: pd.DataFrame) -> Tuple[str, bool, str]:
        """
        Update regime detection for a symbol based on latest market data.
        
        Args:
            symbol: Stock ticker
            df: DataFrame with OHLCV + iv, rv
        
        Returns:
            Tuple of (regime, is_shift, description)
        """
        # Calculate indicators
        df = self.detector.calculate_indicators(df)
        
        # Detect regime (with hysteresis)
        regime, is_shift, description = self.detector.detect_regime(df)
        
        # Cache the result
        self._cache_regime(symbol, regime, description)
        
        if is_shift:
            logger.warning(f"🔔 REGIME SHIFT for {symbol}: {regime}")
            # Alert system will pick this up via the shift flag
        
        return regime, is_shift, description
    
    def get_regime(self, symbol: str) -> Dict[str, Any]:
        """
        Get cached regime state for a symbol.
        
        Args:
            symbol: Stock ticker
        
        Returns:
            Dict with:
            - regime: Current regime string
            - description: Human explanation
            - timestamp: When last updated
            - state: Full RegimeDetector state (for diagnostics)
        """
        cache_key = f"regime:{symbol}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Default if not in cache
        return {
            "regime": "NEUTRAL",
            "description": "No regime data available",
            "timestamp": None,
            "state": None,
        }
    
    def _cache_regime(self, symbol: str, regime: str, description: str, ttl_seconds: int = 3600):
        """
        Cache regime state with TTL.
        
        Args:
            symbol: Stock ticker
            regime: Current regime
            description: Human description
            ttl_seconds: Cache TTL (default 1 hour)
        """
        cache_key = f"regime:{symbol}"
        
        cached_value = {
            "regime": regime,
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
            "state": self.detector.get_regime_state(),
        }
        
        if hasattr(self.cache, 'setex'):
            # Redis client
            self.cache.setex(cache_key, ttl_seconds, json.dumps(cached_value))
        else:
            # Dict-like cache
            self.cache[cache_key] = cached_value
        
        logger.debug(f"Cached regime for {symbol}: {regime}")
    
    def batch_update_regimes(self, symbols: list) -> Dict[str, Tuple[str, bool, str]]:
        """
        Update regimes for multiple symbols (useful for daily market open).
        
        Args:
            symbols: List of tickers
        
        Returns:
            Dict mapping symbol → (regime, is_shift, description)
        """
        results = {}
        
        for symbol in symbols:
            try:
                df = self.get_market_data_for_symbol(symbol)
                if df is not None:
                    regime, is_shift, description = self.update_regime(symbol, df)
                    results[symbol] = (regime, is_shift, description)
                    
                    if is_shift:
                        logger.warning(f"Regime shift detected for {symbol}: {regime}")
                else:
                    logger.warning(f"No market data available for {symbol}")
                    results[symbol] = ("NEUTRAL", False, "Data unavailable")
            except Exception as e:
                logger.error(f"Failed to update regime for {symbol}: {e}")
                results[symbol] = ("NEUTRAL", False, f"Error: {str(e)}")
        
        return results


# --- Integration with Market Data Polling ---

class MarketDataRegimePoller:
    """
    Polls market data on a schedule and updates regime detection.
    
    This would be integrated into your existing market data polling service.
    Expected to run once per market close (4 PM ET).
    """
    
    def __init__(self, regime_service: RegimeDetectionService, 
                 symbols: list = None):
        """
        Args:
            regime_service: RegimeDetectionService instance
            symbols: List of symbols to monitor (defaults to top 100 stocks)
        """
        self.regime_service = regime_service
        self.symbols = symbols or [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX",
            "JNJ", "JPM", "V", "WMT", "PG", "KO", "DIS", "MCD",
        ]  # Example watchlist
        
        logger.info(f"MarketDataRegimePoller initialized for {len(self.symbols)} symbols")
    
    def poll_and_update(self) -> Dict[str, Dict[str, Any]]:
        """
        Poll market data and update regimes for all watched symbols.
        
        This method is called once per market close.
        
        Returns:
            Dict with regime updates and shift alerts
        """
        logger.info(f"Running regime detection for {len(self.symbols)} symbols...")
        
        regime_updates = {}
        shifts = []
        
        for symbol in self.symbols:
            regime_data = self.regime_service.get_regime(symbol)
            regime_updates[symbol] = regime_data
            
            # Track which symbols had regime shifts
            if regime_data.get("state", {}).get("current_regime") != regime_data.get("state", {}).get("previous_regime"):
                shifts.append({
                    "symbol": symbol,
                    "new_regime": regime_data["regime"],
                    "description": regime_data["description"],
                })
        
        logger.info(f"Regime updates complete. Shifts: {len(shifts)}")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "regime_updates": regime_updates,
            "regime_shifts": shifts,
        }


# --- Helper for Strategy Router Integration ---

def get_eligible_strategies_for_regime(regime: str, config: Dict) -> list:
    """
    Look up which strategies are eligible for a given regime.
    
    Uses the playbooks.json config file as source of truth.
    
    Args:
        regime: Regime string (e.g., "CRASH_PANIC")
        config: Playbooks config dict (loaded from options_playbooks.json)
    
    Returns:
        List of eligible strategy names
    """
    playbook = config.get("regimes", {}).get(regime, {})
    return playbook.get("eligible_strategies", [])
