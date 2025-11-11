"""
Monitoring Setup for RichesReach
Configures Sentry for error tracking and basic monitoring
"""
import os
import logging

logger = logging.getLogger(__name__)

def setup_sentry():
    """Set up Sentry for error tracking"""
    sentry_dsn = os.getenv('SENTRY_DSN', '')
    
    if not sentry_dsn:
        logger.warning("SENTRY_DSN not set - Sentry error tracking disabled")
        return None
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        
        environment = os.getenv('ENVIRONMENT', 'production')
        release = os.getenv('RELEASE_VERSION', '1.0.0')
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=release,
            integrations=[
                DjangoIntegration(
                    transaction_style='url',
                    middleware_spans=True,
                    signals_spans=True,
                ),
                FastApiIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
            send_default_pii=False,  # Don't send PII by default
            before_send=lambda event, hint: filter_sensitive_data(event, hint),
        )
        
        logger.info("✅ Sentry initialized successfully")
        return sentry_sdk
        
    except ImportError:
        logger.warning("sentry-sdk not installed - install with: pip install sentry-sdk[fastapi,django]")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return None


def filter_sensitive_data(event, hint):
    """Filter sensitive data from Sentry events"""
    # Remove sensitive fields
    if 'request' in event:
        if 'data' in event['request']:
            # Filter out passwords, tokens, etc.
            sensitive_keys = ['password', 'token', 'api_key', 'secret', 'authorization']
            if isinstance(event['request']['data'], dict):
                for key in sensitive_keys:
                    if key in event['request']['data']:
                        event['request']['data'][key] = '[FILTERED]'
    
    # Filter headers
    if 'request' in event and 'headers' in event['request']:
        sensitive_headers = ['authorization', 'x-api-key', 'cookie']
        for header in sensitive_headers:
            if header in event['request']['headers']:
                event['request']['headers'][header] = '[FILTERED]'
    
    return event


def setup_logging():
    """Set up structured logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_format = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'
    
    if log_format == 'json':
        import json
        import logging
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': self.formatTime(record),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                }
                
                if record.exc_info:
                    log_data['exception'] = self.formatException(record.exc_info)
                
                return json.dumps(log_data)
        
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logging.root.addHandler(handler)
        logging.root.setLevel(getattr(logging, log_level))
    else:
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    logger.info(f"Logging configured: level={log_level}, format={log_format}")


def get_health_metrics():
    """Get basic health metrics"""
    import psutil
    import time
    
    return {
        'timestamp': time.time(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
    }


# Initialize on import
def init_monitoring():
    """Initialize all monitoring"""
    setup_logging()
    sentry = setup_sentry()
    return sentry

