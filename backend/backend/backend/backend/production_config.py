"""
Production Configuration for RichesReach
This file contains production-ready settings and API configurations
"""

import os

# Production API Keys
PRODUCTION_API_KEYS = {
    'ALPHA_VANTAGE_API_KEY': 'OHYSFF1AE446O7CR',
    'FINNHUB_API_KEY': 'd2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0',
    'NEWS_API_KEY': '94a335c7316145f79840edd62f77e11e',
    'POLYGON_API_KEY': 'uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2',
    'OPENAI_API_KEY': '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',

    'USE_SBLOC_AGGREGATOR': True,
    'USE_SBLOC_MOCK': False,
}

# Production Settings
PRODUCTION_SETTINGS = {
    'DEBUG': False,
    'ALLOWED_HOSTS': [
        'app.richesreach.net',
        'riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com',
        'localhost'
    ],
    'CORS_ALLOWED_ORIGINS': [
        'https://app.richesreach.net',
        'https://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com'
    ],
    'SECURE_SSL_REDIRECT': True,
    'SECURE_HSTS_SECONDS': 31536000,
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
    'USE_FINNHUB': True,
    'DISABLE_ALPHA_VANTAGE': False,
    'USE_OPENAI': True,
    'USE_YODLEE': True,
    'API_RATE_LIMIT_ENABLED': True,
    'API_RATE_LIMIT_REQUESTS_PER_MINUTE': 60,
    'LOG_LEVEL': 'INFO'
}

def apply_production_config():
    """Apply production configuration to environment variables"""
    for key, value in PRODUCTION_API_KEYS.items():
        os.environ[key] = value
    
    for key, value in PRODUCTION_SETTINGS.items():
        os.environ[key] = str(value)
    
    print("✅ Production configuration applied successfully")

if __name__ == "__main__":
    apply_production_config()