"""
Enterprise Options Service Configuration
"""
from typing import Dict, Any
import os
from dataclasses import dataclass

@dataclass
class OptionsConfig:
    """Configuration for enterprise options service"""
    
    # API Keys
    finnhub_api_key: str = os.getenv('FINNHUB_API_KEY', '')
    alpha_vantage_api_key: str = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    iex_cloud_api_key: str = os.getenv('IEX_CLOUD_API_KEY', '')
    polygon_api_key: str = os.getenv('POLYGON_API_KEY', '')
    
    # Redis Configuration
    redis_url: str = os.getenv('REDIS_URL', 'redis://process.env.REDIS_HOST || "localhost:6379"')
    cache_ttl: int = int(os.getenv('OPTIONS_CACHE_TTL', '30'))
    
    # Rate Limiting
    max_requests_per_minute: int = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '100'))
    max_requests_per_hour: int = int(os.getenv('MAX_REQUESTS_PER_HOUR', '1000'))
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '5'))
    circuit_breaker_recovery_timeout: int = int(os.getenv('CIRCUIT_BREAKER_TIMEOUT', '60'))
    
    # Performance
    request_timeout: float = float(os.getenv('REQUEST_TIMEOUT', '10.0'))
    max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
    connection_pool_size: int = int(os.getenv('CONNECTION_POOL_SIZE', '100'))
    
    # Data Quality
    min_data_quality_score: float = float(os.getenv('MIN_DATA_QUALITY_SCORE', '0.7'))
    max_strikes_per_expiration: int = int(os.getenv('MAX_STRIKES_PER_EXPIRATION', '50'))
    
    # Monitoring
    enable_metrics: bool = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    enable_tracing: bool = os.getenv('ENABLE_TRACING', 'true').lower() == 'true'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'finnhub_api_key': self.finnhub_api_key,
            'alpha_vantage_api_key': self.alpha_vantage_api_key,
            'iex_cloud_api_key': self.iex_cloud_api_key,
            'polygon_api_key': self.polygon_api_key,
            'redis_url': self.redis_url,
            'cache_ttl': self.cache_ttl,
            'max_requests_per_minute': self.max_requests_per_minute,
            'max_requests_per_hour': self.max_requests_per_hour,
            'circuit_breaker_failure_threshold': self.circuit_breaker_failure_threshold,
            'circuit_breaker_recovery_timeout': self.circuit_breaker_recovery_timeout,
            'request_timeout': self.request_timeout,
            'max_retries': self.max_retries,
            'connection_pool_size': self.connection_pool_size,
            'min_data_quality_score': self.min_data_quality_score,
            'max_strikes_per_expiration': self.max_strikes_per_expiration,
            'enable_metrics': self.enable_metrics,
            'enable_tracing': self.enable_tracing
        }
