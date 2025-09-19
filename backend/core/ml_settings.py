"""
ML Service Settings Configuration
Handles Django settings configuration for ML service integration
"""
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def get_ml_config():
    """Get ML service configuration from Django settings"""
    try:
        return settings.ML_SERVICE_CONFIG
    except AttributeError:
        # Fallback configuration if not set
        return {
            'ENABLED': True,
            'MODEL_PATH': 'backend/ml_models/',
            'CACHE_TIMEOUT': 3600,
            'BATCH_SIZE': 100,
            'MAX_CONCURRENT_REQUESTS': 10,
            'FALLBACK_TO_RULES': True,
            'LOG_LEVEL': 'INFO',
            'ENABLE_OPTIMIZATION': True,
            'ENABLE_RISK_METRICS': True,
            'ENABLE_TRANSACTION_COSTS': True,
        }

def get_pit_config():
    """Get point-in-time data configuration"""
    try:
        return settings.POINT_IN_TIME_CONFIG
    except AttributeError:
        return {
            'ENABLED': True,
            'SNAPSHOT_FREQUENCY': 'daily',
            'RETENTION_DAYS': 90,
            'BATCH_SIZE': 1000,
            'ENABLE_CORPORATE_ACTIONS': True,
        }

def get_institutional_config():
    """Get institutional features configuration"""
    try:
        return settings.INSTITUTIONAL_CONFIG
    except AttributeError:
        return {
            'ENABLED': True,
            'REQUIRE_AUTHENTICATION': True,
            'RATE_LIMIT_PER_USER': 100,
            'ENABLE_AUDIT_TRAIL': True,
            'ENABLE_DRY_RUN': True,
            'MAX_UNIVERSE_SIZE': 2000,
            'DEFAULT_CONSTRAINTS': {
                'max_weight_per_name': 0.10,
                'max_sector_weight': 0.30,
                'max_turnover': 0.25,
                'min_liquidity_score': 0.0,
                'risk_aversion': 5.0,
                'cost_aversion': 1.0,
                'cvar_confidence': 0.95,
                'long_only': True,
            }
        }

def get_monitoring_config():
    """Get monitoring configuration"""
    try:
        return settings.MONITORING_CONFIG
    except AttributeError:
        return {
            'ENABLED': True,
            'LOG_LEVEL': 'INFO',
            'ENABLE_METRICS': True,
            'ENABLE_ALERTS': True,
            'METRICS_RETENTION_DAYS': 30,
            'ALERT_EMAIL': '',
            'SLACK_WEBHOOK': '',
            'HEALTH_CHECK_INTERVAL': 60,
        }

def is_ml_enabled():
    """Check if ML service is enabled"""
    config = get_ml_config()
    return config.get('ENABLED', False)

def is_pit_enabled():
    """Check if point-in-time data is enabled"""
    config = get_pit_config()
    return config.get('ENABLED', False)

def is_institutional_enabled():
    """Check if institutional features are enabled"""
    config = get_institutional_config()
    return config.get('ENABLED', False)

def is_monitoring_enabled():
    """Check if monitoring is enabled"""
    config = get_monitoring_config()
    return config.get('ENABLED', False)

def get_openai_key():
    """Get OpenAI API key"""
    try:
        return settings.OPENAI_API_KEY
    except AttributeError:
        return os.getenv('OPENAI_API_KEY')

def validate_ml_config():
    """Validate ML configuration"""
    config = get_ml_config()
    
    if not config.get('ENABLED', False):
        return True, "ML service is disabled"
    
    # Check required settings
    if not get_openai_key():
        return False, "OPENAI_API_KEY is required for ML service"
    
    # Check model path exists
    model_path = config.get('MODEL_PATH', '')
    if model_path and not os.path.exists(model_path):
        return False, f"Model path does not exist: {model_path}"
    
    return True, "ML configuration is valid"

def get_redis_config():
    """Get Redis configuration for ML caching"""
    try:
        return {
            'host': settings.REDIS_HOST,
            'port': settings.REDIS_PORT,
            'db': settings.REDIS_DB,
            'password': settings.REDIS_PASSWORD,
        }
    except AttributeError:
        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'password': os.getenv('REDIS_PASSWORD', None),
        }

def get_database_config():
    """Get database configuration for ML data storage"""
    try:
        return settings.DATABASES['default']
    except (AttributeError, KeyError):
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }

# ML Service Status
class MLServiceStatus:
    """ML Service status checker"""
    
    @staticmethod
    def get_status():
        """Get comprehensive ML service status"""
        status = {
            'ml_enabled': is_ml_enabled(),
            'pit_enabled': is_pit_enabled(),
            'institutional_enabled': is_institutional_enabled(),
            'monitoring_enabled': is_monitoring_enabled(),
            'openai_configured': bool(get_openai_key()),
            'redis_configured': bool(get_redis_config().get('host')),
            'database_configured': bool(get_database_config()),
        }
        
        # Validate configuration
        is_valid, message = validate_ml_config()
        status['config_valid'] = is_valid
        status['config_message'] = message
        
        # Overall status
        status['overall_status'] = 'healthy' if all([
            status['ml_enabled'],
            status['openai_configured'],
            status['redis_configured'],
            status['database_configured'],
            status['config_valid']
        ]) else 'degraded'
        
        return status
    
    @staticmethod
    def get_health_check():
        """Get health check for monitoring"""
        status = MLServiceStatus.get_status()
        
        return {
            'status': status['overall_status'],
            'timestamp': os.getenv('TIMESTAMP', 'unknown'),
            'version': '1.0.0',
            'components': {
                'ml_service': 'healthy' if status['ml_enabled'] else 'disabled',
                'point_in_time': 'healthy' if status['pit_enabled'] else 'disabled',
                'institutional': 'healthy' if status['institutional_enabled'] else 'disabled',
                'monitoring': 'healthy' if status['monitoring_enabled'] else 'disabled',
                'openai': 'healthy' if status['openai_configured'] else 'unconfigured',
                'redis': 'healthy' if status['redis_configured'] else 'unconfigured',
                'database': 'healthy' if status['database_configured'] else 'unconfigured',
            },
            'config_validation': {
                'valid': status['config_valid'],
                'message': status['config_message']
            }
        }
