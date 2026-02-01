"""
Enhanced Alternative Data Service
Integrates Twitter/X, Reddit, StockTwits, and Options Flow for comprehensive ML features.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.core.cache import cache

from .deep_social_sentiment_service import get_deep_social_sentiment_service
from .hybrid_ml_predictor import OptionsFlowFeatures
from .options_service import OptionsAnalysisService

logger = logging.getLogger(__name__)


class EnhancedAlternativeDataService:
    """
    Enhanced alternative data service combining all sources.
    Provides unified interface for ML models.
    """
    
    def __init__(self):
        self.social_sentiment_service = get_deep_social_sentiment_service()
        self.options_features = OptionsFlowFeatures()
        self.options_analysis = OptionsAnalysisService()
        self.cache_ttl = 300  # 5 minutes
    
    async def get_all_features(
        self,
        symbol: str,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        Get all alternative data features for a symbol.
        
        Args:
            symbol: Stock symbol
            hours_back: Hours of history to fetch
        
        Returns:
            Dictionary with all alternative data features
        """
        cache_key = f"alt_data_{symbol}_{hours_back}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Fetch all data sources in parallel
            social_data, options_data = await asyncio.gather(
                self._get_social_sentiment_features(symbol, hours_back),
                self._get_options_flow_features(symbol),
                return_exceptions=True
            )
            
            # Combine features
            features = {}
            
            # Social sentiment features
            if isinstance(social_data, dict):
                features.update(social_data)
            else:
                logger.warning(f"Social sentiment error for {symbol}: {social_data}")
                features.update(self._get_default_social_features())
            
            # Options flow features
            if isinstance(options_data, dict):
                features.update(options_data)
            else:
                logger.warning(f"Options flow error for {symbol}: {options_data}")
                features.update(self._get_default_options_features())
            
            # Cache results
            cache.set(cache_key, features, self.cache_ttl)
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting alternative data for {symbol}: {e}")
            # Return default features
            features = {}
            features.update(self._get_default_social_features())
            features.update(self._get_default_options_features())
            return features
    
    async def _get_social_sentiment_features(
        self,
        symbol: str,
        hours_back: int
    ) -> Dict[str, float]:
        """Get social sentiment features"""
        try:
            if not self.social_sentiment_service:
                return self._get_default_social_features()
            
            sentiment_data = await self.social_sentiment_service.get_comprehensive_sentiment(
                symbol, hours_back=hours_back
            )
            
            return {
                'social_sentiment': float(sentiment_data.sentiment_score),
                'social_volume': float(sentiment_data.volume),
                'social_engagement': float(sentiment_data.engagement_score),
                'social_momentum': float(sentiment_data.momentum),
                'social_divergence': float(sentiment_data.divergence),
                'twitter_sentiment': float(sentiment_data.sentiment_score),  # Primary platform
                'reddit_sentiment': float(sentiment_data.sentiment_score),  # Aggregated
                'stocktwits_sentiment': float(sentiment_data.sentiment_score),  # Aggregated
            }
        except Exception as e:
            logger.debug(f"Social sentiment not available for {symbol}: {e}")
            return self._get_default_social_features()
    
    async def _get_options_flow_features(self, symbol: str) -> Dict[str, float]:
        """Get options flow features"""
        try:
            options_features = await self.options_features.get_options_features(symbol)
            return options_features
        except Exception as e:
            logger.debug(f"Options flow not available for {symbol}: {e}")
            return self._get_default_options_features()
    
    def _get_default_social_features(self) -> Dict[str, float]:
        """Default social sentiment features when data unavailable"""
        return {
            'social_sentiment': 0.0,
            'social_volume': 0.0,
            'social_engagement': 0.0,
            'social_momentum': 0.0,
            'social_divergence': 0.0,
            'twitter_sentiment': 0.0,
            'reddit_sentiment': 0.0,
            'stocktwits_sentiment': 0.0,
        }
    
    def _get_default_options_features(self) -> Dict[str, float]:
        """Default options flow features when data unavailable"""
        return {
            'put_call_ratio': 1.0,
            'call_bias': 0.0,
            'unusual_volume_pct': 0.0,
            'call_volume_ratio': 0.5,
            'put_volume_ratio': 0.5,
            'avg_unusual_score': 0.5,
            'sweep_detection': 0.0,
            'iv_rank': 0.5,
            'skew': 0.0,
            'bearish_skew': 0.0,
        }
    
    async def get_batch_features(
        self,
        symbols: List[str],
        hours_back: int = 24
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get alternative data features for multiple symbols in parallel.
        
        Args:
            symbols: List of stock symbols
            hours_back: Hours of history to fetch
        
        Returns:
            Dictionary mapping symbol to features
        """
        # Fetch all symbols in parallel
        tasks = [self.get_all_features(symbol, hours_back) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        batch_features = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, dict):
                batch_features[symbol] = result
            else:
                logger.warning(f"Error getting features for {symbol}: {result}")
                # Use default features
                features = {}
                features.update(self._get_default_social_features())
                features.update(self._get_default_options_features())
                batch_features[symbol] = features
        
        return batch_features


# Global instance
_enhanced_alt_data_service = None

def get_enhanced_alternative_data_service() -> EnhancedAlternativeDataService:
    """Get global enhanced alternative data service instance"""
    global _enhanced_alt_data_service
    if _enhanced_alt_data_service is None:
        _enhanced_alt_data_service = EnhancedAlternativeDataService()
    return _enhanced_alt_data_service

