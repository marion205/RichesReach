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
        try:
            from django.conf import settings
            if getattr(settings, 'ENABLE_HMM_REGIME', False):
                from .ensemble_regime_detector import EnsembleRegimeDetector
                self.detector = EnsembleRegimeDetector()
                logger.info("Using EnsembleRegimeDetector (rule-based + HMM)")
            else:
                self.detector = RegimeDetector()
        except Exception:
            self.detector = RegimeDetector()

        self.cache = cache_backend or {}
        self.lookback_days = lookback_days
        self.polygon_service = PolygonOptionsFlowService()

        logger.info(f"RegimeDetectionService initialized (lookback={lookback_days}d)")
    
    def get_market_data_for_symbol(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV + implied volatility + realized volatility for regime detection.

        Uses Polygon.io daily aggregates for OHLCV and options reference data for IV.

        Args:
            symbol: Stock ticker (e.g., "AAPL")

        Returns:
            DataFrame with columns: ['close', 'high', 'low', 'iv', 'rv', 'volume']
            indexed by date, or None if data unavailable
        """
        import os
        import requests
        import numpy as np

        polygon_api_key = os.getenv('POLYGON_API_KEY', '')
        if not polygon_api_key:
            logger.warning("No POLYGON_API_KEY configured, cannot fetch market data")
            return None

        try:
            # 1. Fetch OHLCV daily bars from Polygon (lookback + buffer for weekends)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 15)

            url = (
                f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/"
                f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            )
            params = {'apiKey': polygon_api_key, 'sort': 'asc', 'limit': 50000}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('status') != 'OK':
                logger.warning(f"Polygon API error for {symbol}: {data.get('message')}")
                return None

            results = data.get('results', [])
            if len(results) < 10:
                logger.warning(f"Insufficient OHLCV data for {symbol}: only {len(results)} bars")
                return None

            # Build DataFrame from Polygon bars
            rows = []
            for bar in results:
                rows.append({
                    'date': datetime.utcfromtimestamp(bar.get('t', 0) / 1000).strftime('%Y-%m-%d'),
                    'close': float(bar.get('c', 0)),
                    'high': float(bar.get('h', 0)),
                    'low': float(bar.get('l', 0)),
                    'volume': int(bar.get('v', 0)),
                })

            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # 2. Calculate realized volatility (rolling 30-day window, annualized)
            df['returns'] = df['close'].pct_change()
            df['rv'] = df['returns'].rolling(window=30, min_periods=10).std() * np.sqrt(252)
            df['rv'] = df['rv'].fillna(method='bfill').fillna(0.18)  # Default 18% RV

            # 3. Get ATM IV from options data
            atm_iv = self._fetch_atm_iv(symbol, polygon_api_key)
            # IV is typically higher than RV; use RV * 1.1 as fallback
            df['iv'] = atm_iv if atm_iv > 0 else df['rv'] * 1.1

            # Drop helper columns, keep required
            df = df.drop(columns=['returns'], errors='ignore')

            # Trim to lookback window
            df = df.tail(self.lookback_days)

            required_cols = ['close', 'high', 'low', 'iv', 'rv', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = 0.0

            logger.info(f"Fetched {len(df)} days of regime data for {symbol}")
            return df[required_cols]

        except requests.RequestException as e:
            logger.error(f"Polygon API request error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error building market data for {symbol}: {e}", exc_info=True)
            return None

    def _fetch_atm_iv(self, symbol: str, api_key: str) -> float:
        """
        Fetch ATM implied volatility from Polygon options contracts.

        Uses PolygonOptionsFlowService to get contracts, then extracts
        median IV as an ATM proxy.

        Args:
            symbol: Stock ticker
            api_key: Polygon API key

        Returns:
            ATM implied volatility (0-1 scale), or 0.0 if unavailable
        """
        import numpy as np

        try:
            contracts_data = self.polygon_service._get_options_contracts(symbol)
            if not contracts_data:
                return 0.0

            iv_values = []
            for contract in contracts_data:
                iv = contract.get('implied_volatility')
                if iv and float(iv) > 0:
                    iv_values.append(float(iv))

            if not iv_values:
                return 0.0

            atm_iv = float(np.median(iv_values))
            logger.debug(f"ATM IV for {symbol}: {atm_iv:.4f} (from {len(iv_values)} contracts)")
            return atm_iv

        except Exception as e:
            logger.debug(f"Could not fetch ATM IV for {symbol}: {e}")
            return 0.0
    
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
            # Record regime change event for ADTS adaptive discounting
            try:
                from .regime_change_models import RegimeChangeEvent
                from django.utils import timezone as tz
                RegimeChangeEvent.objects.create(
                    symbol=symbol,
                    previous_regime=self.detector.previous_regime or 'NEUTRAL',
                    new_regime=regime,
                    detected_at=tz.now(),
                    confidence=1.0,
                )
            except Exception as e:
                logger.debug(f"Could not record regime change event: {e}")

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
        import time

        results = {}

        for idx, symbol in enumerate(symbols):
            # Rate limiting: Polygon free tier = 5 req/min
            # Each symbol uses ~2 requests (OHLCV + contracts), so pause every 2 symbols
            if idx > 0 and idx % 2 == 0:
                time.sleep(12)

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
