# 🔑 API Keys Management Guide

This guide covers how to securely manage API keys for your RichesReach application in production.

## 🚨 Security Best Practices

### 1. Never Commit API Keys
- ❌ **NEVER** commit API keys to version control
- ✅ Use environment variables
- ✅ Use secure key management services
- ✅ Rotate keys regularly

### 2. Key Storage
- Store keys in environment variables
- Use AWS Secrets Manager for production
- Use HashiCorp Vault for enterprise
- Never hardcode keys in source code

### 3. Key Rotation
- Rotate keys every 90 days
- Monitor key usage
- Have backup keys ready
- Test new keys before deploying

## 📋 Required API Keys

### 1. Alpha Vantage (Stock Data)
**Purpose**: Real-time stock quotes, historical data, market indicators

**Setup**:
1. Sign up at https://www.alphavantage.co/support/#api-key
2. Get your free API key
3. Add to environment: `ALPHA_VANTAGE_API_KEY=your-key-here`

**Rate Limits**:
- Free: 5 calls/minute, 500 calls/day
- Premium: 75,000 calls/day ($49.99/month)

**Usage in Code**:
```python
# backend/richesreach/settings.py
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
```

### 2. News API (Financial News)
**Purpose**: Financial news, market sentiment, company updates

**Setup**:
1. Sign up at https://newsapi.org/register
2. Get your free API key
3. Add to environment: `NEWS_API_KEY=your-key-here`

**Rate Limits**:
- Free: 100 requests/day
- Business: 10,000 requests/day ($449/month)

**Usage in Code**:
```python
# backend/richesreach/settings.py
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
```

### 3. OpenAI (AI Recommendations)
**Purpose**: AI-powered portfolio recommendations, market analysis

**Setup**:
1. Sign up at https://platform.openai.com/
2. Create API key
3. Add to environment: `OPENAI_API_KEY=your-key-here`

**Rate Limits**:
- Pay-per-use pricing
- Monitor usage in OpenAI dashboard

**Usage in Code**:
```python
# backend/richesreach/settings.py
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
```

## 🔧 Environment Configuration

### Backend (.env file)
```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
NEWS_API_KEY=your-news-api-key
OPENAI_API_KEY=your-openai-key

# Optional APIs
FINNHUB_API_KEY=your-finnhub-key
POLYGON_API_KEY=your-polygon-key
IEX_CLOUD_API_KEY=your-iex-key
```

### Mobile App (env.production)
```bash
# Public API Keys (be careful with these)
EXPO_PUBLIC_ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
EXPO_PUBLIC_NEWS_API_KEY=your-news-api-key

# Note: Never expose sensitive keys in mobile apps
# Use backend proxy for sensitive operations
```

## 🛡️ Security Implementation

### 1. Backend API Key Validation
```python
# backend/core/utils.py
import os
from django.core.exceptions import ImproperlyConfigured

def get_required_env_var(var_name):
    """Get required environment variable or raise error"""
    value = os.getenv(var_name)
    if not value:
        raise ImproperlyConfigured(f"Required environment variable {var_name} not set")
    return value

# Usage
ALPHA_VANTAGE_API_KEY = get_required_env_var('ALPHA_VANTAGE_API_KEY')
```

### 2. API Key Encryption (Optional)
```python
# backend/core/encryption.py
from cryptography.fernet import Fernet
import base64

class APIKeyEncryption:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt_key(self, api_key):
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt_key(self, encrypted_key):
        return self.cipher.decrypt(encrypted_key.encode()).decode()
```

### 3. Rate Limiting
```python
# backend/core/rate_limiter.py
import time
from django.core.cache import cache

class APIRateLimiter:
    def __init__(self, api_name, max_requests, time_window):
        self.api_name = api_name
        self.max_requests = max_requests
        self.time_window = time_window
    
    def is_rate_limited(self, identifier):
        key = f"rate_limit:{self.api_name}:{identifier}"
        current_requests = cache.get(key, 0)
        
        if current_requests >= self.max_requests:
            return True
        
        cache.set(key, current_requests + 1, self.time_window)
        return False
```

## 🔄 Key Rotation Process

### 1. Preparation
```bash
# 1. Generate new API keys
# 2. Test new keys in staging environment
# 3. Prepare rollback plan
# 4. Notify team of maintenance window
```

### 2. Deployment
```bash
# 1. Update environment variables
# 2. Deploy new configuration
# 3. Verify API functionality
# 4. Monitor for errors
```

### 3. Cleanup
```bash
# 1. Revoke old API keys
# 2. Update documentation
# 3. Update monitoring alerts
# 4. Log rotation completion
```

## 📊 Monitoring & Alerting

### 1. API Usage Monitoring
```python
# backend/core/monitoring.py
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

class APIMonitor:
    def log_api_call(self, api_name, endpoint, status_code, response_time):
        logger.info(f"API Call: {api_name} {endpoint} - {status_code} - {response_time}ms")
        
        # Track usage for rate limiting
        key = f"api_usage:{api_name}:{time.strftime('%Y-%m-%d')}"
        cache.incr(key, 1)
```

### 2. Error Alerting
```python
# backend/core/alerts.py
import sentry_sdk

def alert_api_error(api_name, error_message):
    sentry_sdk.capture_message(
        f"API Error: {api_name} - {error_message}",
        level="error"
    )
```

### 3. Usage Tracking
```python
# backend/core/usage_tracker.py
from django.core.cache import cache
from datetime import datetime, timedelta

class APIUsageTracker:
    def track_usage(self, api_name, endpoint):
        today = datetime.now().strftime('%Y-%m-%d')
        key = f"usage:{api_name}:{today}"
        
        usage = cache.get(key, {})
        usage[endpoint] = usage.get(endpoint, 0) + 1
        cache.set(key, usage, 86400)  # 24 hours
```

## 🚨 Emergency Procedures

### 1. Key Compromise
```bash
# Immediate actions:
# 1. Revoke compromised key
# 2. Generate new key
# 3. Update environment variables
# 4. Deploy immediately
# 5. Monitor for unauthorized usage
```

### 2. Rate Limit Exceeded
```bash
# Immediate actions:
# 1. Check usage patterns
# 2. Implement additional caching
# 3. Consider upgrading API plan
# 4. Implement circuit breaker
```

### 3. API Service Down
```bash
# Immediate actions:
# 1. Check service status
# 2. Enable fallback data sources
# 3. Notify users of degraded service
# 4. Monitor for service restoration
```

## 📚 Additional Resources

### API Documentation
- [Alpha Vantage API](https://www.alphavantage.co/documentation/)
- [News API](https://newsapi.org/docs)
- [OpenAI API](https://platform.openai.com/docs)

### Security Resources
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [HashiCorp Vault](https://www.vaultproject.io/)

### Monitoring Tools
- [Sentry](https://sentry.io/) - Error tracking
- [DataDog](https://www.datadoghq.com/) - APM and monitoring
- [New Relic](https://newrelic.com/) - Application monitoring

## ✅ Checklist

### Setup
- [ ] All required API keys obtained
- [ ] Keys stored in environment variables
- [ ] Keys tested in staging environment
- [ ] Rate limiting implemented
- [ ] Monitoring configured

### Security
- [ ] Keys not committed to version control
- [ ] Keys encrypted in transit
- [ ] Access logs enabled
- [ ] Regular key rotation scheduled
- [ ] Emergency procedures documented

### Monitoring
- [ ] Usage tracking implemented
- [ ] Error alerting configured
- [ ] Rate limit monitoring active
- [ ] Performance metrics collected
- [ ] Cost monitoring enabled
