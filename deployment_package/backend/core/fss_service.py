# core/fss_service.py
"""
FSS Service - High-level service for FSS integration across the app
Provides easy access to FSS scores for stocks, portfolios, and recommendations.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from .fss_engine import get_fss_engine, get_safety_filter, FSSResult
from .fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
from .algorithm_service import get_algorithm_service

logger = logging.getLogger(__name__)


class FSSService:
    """
    High-level service for FSS integration.
    
    Provides:
    - Single stock FSS calculation
    - Batch stock FSS calculation
    - Portfolio FSS ranking
    - Cached FSS scores
    """
    
    def __init__(self):
        """Initialize FSS service"""
        self.fss_engine = get_fss_engine()
        self.data_pipeline = get_fss_data_pipeline()
        self.algorithm_service = get_algorithm_service()
        self.safety_filter = get_safety_filter()
        
        # Cache for FSS scores (in production, use Redis)
        self._fss_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 hour
    
    async def get_stock_fss(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get FSS score for a single stock.
        
        Args:
            symbol: Stock symbol
            use_cache: Whether to use cached score (default: True)
            
        Returns:
            Dictionary with FSS score and components, or None if error
        """
        # Check cache
        if use_cache and symbol in self._fss_cache:
            cached = self._fss_cache[symbol]
            age = (datetime.now() - cached.get('timestamp', datetime.min)).total_seconds()
            if age < self._cache_ttl:
                logger.debug(f"Using cached FSS for {symbol}")
                return cached.get('data')
        
        try:
            # Fetch data and calculate FSS
            async with self.data_pipeline:
                data_request = FSSDataRequest(
                    tickers=[symbol],
                    lookback_days=252,
                    include_fundamentals=True
                )
                data_result = await self.data_pipeline.fetch_fss_data(data_request)
            
            # Calculate FSS
            fss_data = self.fss_engine.compute_fss_v3(
                prices=data_result.prices,
                volumes=data_result.volumes,
                spy=data_result.spy,
                vix=data_result.vix,
                fundamentals_daily=data_result.fundamentals_daily
            )
            
            # Detect regime
            regime_result = self.fss_engine.detect_market_regime(
                data_result.spy,
                data_result.vix
            )
            
            # Check safety filters
            safety_passed, safety_reason = self.safety_filter.check_safety(
                ticker=symbol,
                volumes=data_result.volumes
            )
            
            # Get FSS result
            fss_result = self.fss_engine.get_stock_fss(
                ticker=symbol,
                fss_data=fss_data,
                regime=regime_result.regime,
                safety_passed=safety_passed,
                safety_reason=safety_reason
            )
            
            # Format for GraphQL
            result = {
                "fss_score": fss_result.fss_score,
                "trend_score": fss_result.trend_score,
                "fundamental_score": fss_result.fundamental_score,
                "capital_flow_score": fss_result.capital_flow_score,
                "risk_score": fss_result.risk_score,
                "confidence": fss_result.confidence,
                "regime": fss_result.regime,
                "passed_safety_filters": fss_result.passed_safety_filters,
                "safety_reason": fss_result.safety_reason,
                "last_updated": datetime.now()
            }
            
            # Cache result
            if use_cache:
                self._fss_cache[symbol] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
            
            return result
        
        except Exception as e:
            logger.error(f"Error calculating FSS for {symbol}: {e}", exc_info=True)
            return None
    
    async def get_stocks_fss(
        self,
        symbols: List[str],
        use_cache: bool = True
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get FSS scores for multiple stocks.
        
        Args:
            symbols: List of stock symbols
            use_cache: Whether to use cached scores
            
        Returns:
            Dictionary mapping symbol to FSS result
        """
        results = {}
        
        # Fetch in parallel
        tasks = [self.get_stock_fss(symbol, use_cache) for symbol in symbols]
        fss_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(symbols, fss_results):
            if isinstance(result, Exception):
                logger.warning(f"Error calculating FSS for {symbol}: {result}")
                results[symbol] = None
            else:
                results[symbol] = result
        
        return results
    
    def rank_stocks_by_fss(
        self,
        fss_results: Dict[str, Optional[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Rank stocks by FSS score.
        
        Args:
            fss_results: Dictionary of symbol -> FSS result
            
        Returns:
            List of stocks sorted by FSS score (highest first)
        """
        ranked = []
        
        for symbol, result in fss_results.items():
            if result and result.get('fss_score') is not None:
                ranked.append({
                    'symbol': symbol,
                    **result
                })
        
        # Sort by FSS score (descending)
        ranked.sort(key=lambda x: x.get('fss_score', 0), reverse=True)
        
        return ranked


# Singleton instance
_fss_service = None


def get_fss_service() -> FSSService:
    """Get singleton FSS service instance"""
    global _fss_service
    if _fss_service is None:
        _fss_service = FSSService()
    return _fss_service

