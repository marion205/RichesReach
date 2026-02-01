"""
Speed Optimization Service
Centralized service for managing all speed optimizations:
- WebSocket streaming activation
- Model optimization (ONNX/TensorRT)
- Latency monitoring and alerting
- Cache management
"""
import logging
import os
import time
from typing import Dict, List, Optional, Any
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class SpeedOptimizationService:
    """
    Centralized speed optimization service.
    Manages WebSocket streaming, model optimization, and latency monitoring.
    """
    
    def __init__(self):
        self.websocket_active = False
        self.model_optimized = False
        self.cloud_locality_enabled = False
        self.latency_target_ms = 500.0
        self.latency_history = deque(maxlen=1000)
        self.alert_threshold_ms = 1000.0  # Alert if latency exceeds 1s
        
        # Initialize WebSocket service
        self._init_websocket()
        
        # Check for optimized models
        self._check_model_optimization()
        
        # Check cloud locality status
        self._check_cloud_locality_status()
    
    def _init_websocket(self):
        """Initialize WebSocket streaming service"""
        try:
            from .websocket_streaming import get_websocket_service
            self.ws_service = get_websocket_service()
            logger.info("✅ WebSocket service initialized")
        except Exception as e:
            logger.warning(f"⚠️ WebSocket service not available: {e}")
            self.ws_service = None
    
    def _check_model_optimization(self):
        """Check if models are optimized (ONNX/TensorRT)"""
        try:
            # Check for ONNX models
            model_dir = os.path.join(os.path.dirname(__file__), 'models')
            onnx_lstm = os.path.exists(os.path.join(model_dir, 'lstm_extractor.onnx'))
            onnx_xgb = os.path.exists(os.path.join(model_dir, 'xgboost_model.onnx'))
            
            if onnx_lstm and onnx_xgb:
                self.model_optimized = True
                logger.info("✅ ONNX models detected - using optimized inference")
            else:
                logger.info("ℹ️ Using standard models (ONNX conversion recommended)")
        except Exception as e:
            logger.warning(f"⚠️ Could not check model optimization: {e}")
    
    async def start_websocket_streaming(
        self,
        symbols: List[str],
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> bool:
        """
        Start WebSocket streaming for given symbols.
        
        Args:
            symbols: List of stock symbols to stream
            api_key: Alpaca API key (or from env)
            api_secret: Alpaca API secret (or from env)
        
        Returns:
            True if streaming started successfully
        """
        if not self.ws_service:
            logger.error("❌ WebSocket service not available")
            return False
        
        try:
            # Get API credentials from env if not provided
            if not api_key:
                api_key = os.getenv('ALPACA_API_KEY')
            if not api_secret:
                api_secret = os.getenv('ALPACA_API_SECRET')
            
            if not api_key or not api_secret:
                logger.warning("⚠️ Alpaca API credentials not found - WebSocket streaming disabled")
                return False
            
            # Connect to Alpaca WebSocket
            success = await self.ws_service.connect_alpaca(
                symbols=symbols,
                api_key=api_key,
                api_secret=api_secret
            )
            
            if success:
                self.websocket_active = True
                logger.info(f"✅ WebSocket streaming active for {len(symbols)} symbols")
                return True
            else:
                logger.error("❌ Failed to start WebSocket streaming")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting WebSocket streaming: {e}", exc_info=True)
            return False
    
    def record_latency(self, latency_ms: float, operation: str = "inference"):
        """
        Record latency for monitoring and alerting.
        
        Args:
            latency_ms: Latency in milliseconds
            operation: Operation name (e.g., "inference", "price_fetch")
        """
        self.latency_history.append({
            'latency_ms': latency_ms,
            'operation': operation,
            'timestamp': datetime.now()
        })
        
        # Alert if latency exceeds threshold
        if latency_ms > self.alert_threshold_ms:
            logger.warning(
                f"⚠️ High latency detected: {latency_ms:.1f}ms for {operation} "
                f"(threshold: {self.alert_threshold_ms}ms)"
            )
    
    def get_latency_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get latency statistics.
        
        Args:
            operation: Filter by operation name (optional)
        
        Returns:
            Dict with latency statistics
        """
        if not self.latency_history:
            return {
                'count': 0,
                'avg_ms': 0.0,
                'median_ms': 0.0,
                'p95_ms': 0.0,
                'p99_ms': 0.0,
                'max_ms': 0.0,
                'below_target': 0.0  # % below 500ms target
            }
        
        # Filter by operation if specified
        latencies = [
            h['latency_ms'] for h in self.latency_history
            if not operation or h['operation'] == operation
        ]
        
        if not latencies:
            return {'count': 0}
        
        import numpy as np
        
        latencies_array = np.array(latencies)
        below_target = np.sum(latencies_array < self.latency_target_ms) / len(latencies) * 100
        
        return {
            'count': len(latencies),
            'avg_ms': float(np.mean(latencies)),
            'median_ms': float(np.median(latencies)),
            'p95_ms': float(np.percentile(latencies, 95)),
            'p99_ms': float(np.percentile(latencies, 99)),
            'min_ms': float(np.min(latencies)),
            'max_ms': float(np.max(latencies)),
            'below_target': float(below_target),
            'target_ms': self.latency_target_ms
        }
    
    def _check_websocket_status(self):
        """Check if WebSocket is actually active"""
        if self.ws_service:
            try:
                # Check if WebSocket service reports as active
                if hasattr(self.ws_service, 'is_websocket_active'):
                    self.websocket_active = self.ws_service.is_websocket_active()
                elif hasattr(self.ws_service, 'is_active'):
                    self.websocket_active = self.ws_service.is_active
                elif len(self.ws_service.connections) > 0:
                    self.websocket_active = True
            except Exception as e:
                logger.warning(f"Could not check WebSocket status: {e}")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """
        Get current optimization status.
        
        Returns:
            Dict with optimization status
        """
        # Check actual WebSocket status
        self._check_websocket_status()
        self._check_cloud_locality_status()
        
        latency_stats = self.get_latency_stats()
        
        return {
            'websocket_active': self.websocket_active,
            'model_optimized': self.model_optimized,
            'cloud_locality_enabled': self.cloud_locality_enabled,
            'latency_target_ms': self.latency_target_ms,
            'current_avg_latency_ms': latency_stats.get('avg_ms', 0.0),
            'below_target_percent': latency_stats.get('below_target', 0.0),
            'recommendations': self._get_recommendations(latency_stats)
        }
    
    def _get_recommendations(self, latency_stats: Dict[str, Any]) -> List[str]:
        """Get optimization recommendations based on current performance"""
        recommendations = []
        
        avg_latency = latency_stats.get('avg_ms', 0.0)
        below_target = latency_stats.get('below_target', 0.0)
        
        if not self.websocket_active:
            recommendations.append("Activate WebSocket streaming for <50ms price updates")
        
        if not self.model_optimized:
            recommendations.append("Convert models to ONNX format for faster inference")
        
        if avg_latency > self.latency_target_ms:
            recommendations.append(f"Current latency ({avg_latency:.1f}ms) exceeds target ({self.latency_target_ms}ms)")
        
        if below_target < 90.0:
            recommendations.append(f"Only {below_target:.1f}% of requests below target - consider optimization")
        
        if not recommendations:
            recommendations.append("✅ Performance is optimal!")
        
        return recommendations


# Global instance
_speed_optimization_service = None

def get_speed_optimization_service() -> SpeedOptimizationService:
    """Get global speed optimization service instance"""
    global _speed_optimization_service
    if _speed_optimization_service is None:
        _speed_optimization_service = SpeedOptimizationService()
    return _speed_optimization_service

