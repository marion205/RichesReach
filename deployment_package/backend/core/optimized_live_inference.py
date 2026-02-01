"""
Optimized Live Hybrid Inference Pipeline
Sub-500ms latency target with WebSocket streaming and parallel processing.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import asyncio
import time
from collections import deque
import aiohttp

logger = logging.getLogger(__name__)


class OptimizedLiveInference:
    """
    Optimized live inference with WebSocket streaming and latency monitoring.
    Target: <500ms end-to-end latency.
    """
    
    def __init__(self, confidence_threshold: float = 0.78):
        """
        Initialize optimized inference pipeline.
        
        Args:
            confidence_threshold: Minimum confidence to execute
        """
        self.confidence_threshold = confidence_threshold
        
        # Initialize components
        from .lstm_data_fetcher import get_lstm_data_fetcher
        from .lstm_feature_extractor import get_lstm_feature_extractor
        from .hybrid_lstm_xgboost_trainer import get_hybrid_trainer
        
        self.data_fetcher = get_lstm_data_fetcher()
        self.lstm_extractor = get_lstm_feature_extractor()
        self.hybrid_trainer = get_hybrid_trainer()
        
        # Load models if available
        self.hybrid_trainer._load_models()
        
        # WebSocket connections (cached)
        self.ws_connections = {}
        self.price_cache = {}  # In-memory price cache (last 60 bars)
        self.cache_ttl = 1.0  # 1 second cache TTL
        
        # Latency monitoring
        self.latency_history = deque(maxlen=100)
        
    async def _get_price_via_websocket(self, symbol: str) -> Optional[Dict]:
        """
        Get price data via WebSocket (fastest method).
        Falls back to REST if WebSocket unavailable.
        """
        try:
            # Try WebSocket streaming service first
            from .websocket_streaming import get_websocket_service
            ws_service = get_websocket_service()
            
            # Get latest price from WebSocket cache
            price_data = ws_service.get_latest_price(symbol)
            if price_data:
                return price_data
            
            # Fallback: Use REST with caching
            cache_key = f"price_{symbol}"
            cached = self.price_cache.get(cache_key)
            
            if cached and (time.time() - cached['timestamp']) < self.cache_ttl:
                return cached['data']
            
            # Fetch fresh data
            # Use Alpaca streaming API or Polygon WebSocket
            price_data = await self._fetch_price_rest(symbol)
            
            # Cache it
            self.price_cache[cache_key] = {
                'data': price_data,
                'timestamp': time.time()
            }
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    async def _fetch_price_rest(self, symbol: str) -> Optional[Dict]:
        """Fetch price via REST API (fallback)"""
        try:
            # Use Alpaca or Polygon REST API
            # This is the slow path - should be <200ms
            import aiohttp
            
            # Alpaca example
            url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars/latest"
            headers = {
                'APCA-API-KEY-ID': '',  # From config
                'APCA-API-SECRET-KEY': ''
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=0.5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'price': data['bar']['c'],
                            'volume': data['bar']['v'],
                            'timestamp': data['bar']['t']
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"REST fetch error for {symbol}: {e}")
            return None
    
    async def generate_live_signal_optimized(
        self,
        symbol: str,
        use_alpaca: bool = True
    ) -> Dict[str, Any]:
        """
        Generate live signal with latency optimization.
        Target: <500ms end-to-end.
        
        Args:
            symbol: Stock symbol
            use_alpaca: Use Alpaca API
        
        Returns:
            Dict with action, confidence, reasoning, and latency metrics
        """
        start_time = time.time()
        latency_breakdown = {}
        
        try:
            # Step 1: Get price data (optimized, <100ms target)
            price_start = time.time()
            price_data = await self._get_price_via_websocket(symbol)
            latency_breakdown['price_fetch'] = (time.time() - price_start) * 1000
            
            if not price_data:
                return {
                    'symbol': symbol,
                    'action': 'ABSTAIN',
                    'confidence': 0.0,
                    'error': 'Price data unavailable',
                    'latency_ms': (time.time() - start_time) * 1000,
                    'latency_breakdown': latency_breakdown
                }
            
            # Step 2: Get cached LSTM sequence (if available, <10ms)
            # Otherwise fetch and cache
            lstm_start = time.time()
            lstm_input, alt_data_df = await self._get_hybrid_features_cached(symbol)
            latency_breakdown['feature_fetch'] = (time.time() - lstm_start) * 1000
            
            # Step 3: Extract LSTM features (<50ms target)
            lstm_extract_start = time.time()
            if self.lstm_extractor.is_available():
                temporal_momentum_score = self.lstm_extractor.extract_temporal_momentum_score(
                    lstm_input, symbol
                )
                alt_data_df['lstm_temporal_momentum_score'] = temporal_momentum_score
            else:
                alt_data_df['lstm_temporal_momentum_score'] = 0.0
                temporal_momentum_score = 0.0
            latency_breakdown['lstm_extraction'] = (time.time() - lstm_extract_start) * 1000
            
            # Step 4: XGBoost prediction (<100ms target)
            xgb_start = time.time()
            if self.hybrid_trainer.xgboost_model is not None:
                action, confidence = self.hybrid_trainer.predict_with_abstention(
                    alt_data_df,
                    confidence_threshold=self.confidence_threshold
                )
            else:
                action = 'ABSTAIN'
                confidence = 0.5
            latency_breakdown['xgboost_prediction'] = (time.time() - xgb_start) * 1000
            
            # Step 5: Generate reasoning (<10ms)
            reasoning_start = time.time()
            reasoning_parts = []
            if abs(temporal_momentum_score) > 0.1:
                reasoning_parts.append(f"LSTM momentum: {temporal_momentum_score:+.3f}")
            if confidence >= self.confidence_threshold:
                reasoning_parts.append(f"High confidence: {confidence:.2%}")
            else:
                reasoning_parts.append(f"Low confidence: {confidence:.2%} (abstaining)")
            latency_breakdown['reasoning'] = (time.time() - reasoning_start) * 1000
            
            total_latency = (time.time() - start_time) * 1000
            self.latency_history.append(total_latency)
            
            return {
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'temporal_momentum_score': temporal_momentum_score,
                'reasoning': ' | '.join(reasoning_parts) if reasoning_parts else 'Hybrid model prediction',
                'timestamp': datetime.now().isoformat(),
                'latency_ms': total_latency,
                'latency_breakdown': latency_breakdown,
                'price': price_data.get('price') if price_data else None
            }
            
        except Exception as e:
            logger.error(f"Error generating optimized signal for {symbol}: {e}")
            total_latency = (time.time() - start_time) * 1000
            return {
                'symbol': symbol,
                'action': 'ABSTAIN',
                'confidence': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'latency_ms': total_latency,
                'latency_breakdown': latency_breakdown
            }
    
    async def _get_hybrid_features_cached(self, symbol: str) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Get hybrid features with aggressive caching.
        Cache TTL: 1 second (for 1-minute bars).
        """
        cache_key = f"features_{symbol}"
        cached = self.price_cache.get(cache_key)
        
        if cached and (time.time() - cached['timestamp']) < self.cache_ttl:
            return cached['data']
        
        # Fetch fresh
        lstm_input, alt_data_df = await self.data_fetcher.get_hybrid_features(
            symbol, use_alpaca=True
        )
        
        # Cache it
        self.price_cache[cache_key] = {
            'data': (lstm_input, alt_data_df),
            'timestamp': time.time()
        }
        
        return lstm_input, alt_data_df
    
    async def generate_signals_batch_optimized(
        self,
        symbols: List[str],
        use_alpaca: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate signals for multiple symbols in parallel (optimized).
        Uses asyncio.gather for true parallelism.
        """
        # Warm up cache first
        await self.data_fetcher.warm_up(symbols)
        
        # Generate signals in parallel
        tasks = [
            self.generate_live_signal_optimized(symbol, use_alpaca)
            for symbol in symbols
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and log latency stats
        signals = []
        latencies = []
        
        for result in results:
            if isinstance(result, dict) and 'action' in result:
                signals.append(result)
                if 'latency_ms' in result:
                    latencies.append(result['latency_ms'])
            else:
                logger.warning(f"Error in batch signal generation: {result}")
        
        # Log latency statistics
        if latencies:
            avg_latency = np.mean(latencies)
            p95_latency = np.percentile(latencies, 95)
            p99_latency = np.percentile(latencies, 99)
            
            logger.info(f"Batch signal generation: {len(signals)}/{len(symbols)} successful")
            logger.info(f"Latency stats: avg={avg_latency:.1f}ms, p95={p95_latency:.1f}ms, p99={p99_latency:.1f}ms")
        
        return signals
    
    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics"""
        if not self.latency_history:
            return {}
        
        latencies = list(self.latency_history)
        return {
            'avg_ms': np.mean(latencies),
            'median_ms': np.median(latencies),
            'p95_ms': np.percentile(latencies, 95),
            'p99_ms': np.percentile(latencies, 99),
            'min_ms': np.min(latencies),
            'max_ms': np.max(latencies),
            'count': len(latencies)
        }


# Global instance
_optimized_inference = None

def get_optimized_inference(confidence_threshold: float = 0.78) -> OptimizedLiveInference:
    """Get global optimized inference instance"""
    global _optimized_inference
    if _optimized_inference is None:
        _optimized_inference = OptimizedLiveInference(confidence_threshold=confidence_threshold)
    return _optimized_inference

