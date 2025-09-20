"""
Enterprise Configuration Management
Centralized configuration for all enterprise-level features
"""
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from django.conf import settings
from django.core.cache import cache
import json


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class APIConfig:
    """API configuration"""
    base_url: str
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit_per_minute: int = 60
    cache_ttl: int = 300


@dataclass
class DatabaseConfig:
    """Database configuration"""
    max_connections: int = 20
    connection_timeout: int = 30
    query_timeout: int = 60
    enable_query_logging: bool = False


@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret_key: str
    jwt_expiration_hours: int = 24
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    enable_2fa: bool = True
    session_timeout_hours: int = 8


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_metrics: bool = True
    metrics_retention_days: int = 30
    alert_email: Optional[str] = None
    enable_performance_tracking: bool = True
    slow_query_threshold_ms: int = 1000


class EnterpriseConfig:
    """Centralized enterprise configuration management"""
    
    def __init__(self):
        self.environment = Environment(os.getenv('ENVIRONMENT', 'development'))
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Initialize configurations
        self.api_configs = self._load_api_configs()
        self.database_config = self._load_database_config()
        self.security_config = self._load_security_config()
        self.monitoring_config = self._load_monitoring_config()
        
        # Setup logging
        self._setup_logging()
        
        # Validate configuration
        self._validate_config()
    
    def _load_api_configs(self) -> Dict[str, APIConfig]:
        """Load API configurations"""
        return {
            'alpha_vantage': APIConfig(
                base_url=os.getenv('ALPHA_VANTAGE_BASE_URL', 'https://www.alphavantage.co/query'),
                timeout=int(os.getenv('ALPHA_VANTAGE_TIMEOUT', '30')),
                retry_attempts=int(os.getenv('ALPHA_VANTAGE_RETRY_ATTEMPTS', '3')),
                rate_limit_per_minute=int(os.getenv('ALPHA_VANTAGE_RATE_LIMIT', '5')),
                cache_ttl=int(os.getenv('ALPHA_VANTAGE_CACHE_TTL', '300'))
            ),
            'finnhub': APIConfig(
                base_url=os.getenv('FINNHUB_BASE_URL', 'https://finnhub.io/api/v1'),
                timeout=int(os.getenv('FINNHUB_TIMEOUT', '30')),
                retry_attempts=int(os.getenv('FINNHUB_RETRY_ATTEMPTS', '3')),
                rate_limit_per_minute=int(os.getenv('FINNHUB_RATE_LIMIT', '60')),
                cache_ttl=int(os.getenv('FINNHUB_CACHE_TTL', '300'))
            ),
            'polygon': APIConfig(
                base_url=os.getenv('POLYGON_BASE_URL', 'https://api.polygon.io'),
                timeout=int(os.getenv('POLYGON_TIMEOUT', '30')),
                retry_attempts=int(os.getenv('POLYGON_RETRY_ATTEMPTS', '3')),
                rate_limit_per_minute=int(os.getenv('POLYGON_RATE_LIMIT', '5')),
                cache_ttl=int(os.getenv('POLYGON_CACHE_TTL', '300'))
            ),
            'iex': APIConfig(
                base_url=os.getenv('IEX_BASE_URL', 'https://cloud.iexapis.com/stable'),
                timeout=int(os.getenv('IEX_TIMEOUT', '30')),
                retry_attempts=int(os.getenv('IEX_RETRY_ATTEMPTS', '3')),
                rate_limit_per_minute=int(os.getenv('IEX_RATE_LIMIT', '100')),
                cache_ttl=int(os.getenv('IEX_CACHE_TTL', '300'))
            )
        }
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '20')),
            connection_timeout=int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
            query_timeout=int(os.getenv('DB_QUERY_TIMEOUT', '60')),
            enable_query_logging=os.getenv('DB_ENABLE_QUERY_LOGGING', 'False').lower() == 'true'
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if not jwt_secret:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        
        return SecurityConfig(
            jwt_secret_key=jwt_secret,
            jwt_expiration_hours=int(os.getenv('JWT_EXPIRATION_HOURS', '24')),
            password_min_length=int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            lockout_duration_minutes=int(os.getenv('LOCKOUT_DURATION_MINUTES', '30')),
            enable_2fa=os.getenv('ENABLE_2FA', 'True').lower() == 'true',
            session_timeout_hours=int(os.getenv('SESSION_TIMEOUT_HOURS', '8'))
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration"""
        return MonitoringConfig(
            enable_metrics=os.getenv('ENABLE_METRICS', 'True').lower() == 'true',
            metrics_retention_days=int(os.getenv('METRICS_RETENTION_DAYS', '30')),
            alert_email=os.getenv('ALERT_EMAIL'),
            enable_performance_tracking=os.getenv('ENABLE_PERFORMANCE_TRACKING', 'True').lower() == 'true',
            slow_query_threshold_ms=int(os.getenv('SLOW_QUERY_THRESHOLD_MS', '1000'))
        )
    
    def _setup_logging(self):
        """Setup enterprise-level logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/enterprise.log', mode='a')
            ]
        )
        
        # Configure specific loggers
        self._configure_logger('django.db.backends', 'WARNING')  # Reduce DB query noise
        self._configure_logger('urllib3', 'WARNING')  # Reduce HTTP noise
        self._configure_logger('requests', 'WARNING')  # Reduce requests noise
    
    def _configure_logger(self, logger_name: str, level: str):
        """Configure specific logger"""
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level))
    
    def _validate_config(self):
        """Validate configuration"""
        errors = []
        
        # Validate required environment variables
        required_vars = [
            'JWT_SECRET_KEY',
            'SECRET_KEY',
            'DATABASE_URL'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"Required environment variable {var} is not set")
        
        # Validate API keys
        api_keys = [
            'ALPHA_VANTAGE_API_KEY',
            'FINNHUB_API_KEY'
        ]
        
        for key in api_keys:
            if not os.getenv(key):
                errors.append(f"API key {key} is not set")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_api_config(self, service: str) -> APIConfig:
        """Get API configuration for a service"""
        if service not in self.api_configs:
            raise ValueError(f"Unknown API service: {service}")
        return self.api_configs[service]
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
    
    def get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key with prefix"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get configured logger"""
        return logging.getLogger(name)


# Global configuration instance
config = EnterpriseConfig()
