# Production Environment Setup Guide
This guide will help you configure your RichesReach application for production deployment.
## Prerequisites
Before setting up your production environment, ensure you have:
- [ ] AWS account with appropriate permissions
- [ ] Domain name registered
- [ ] SSL certificate (Let's Encrypt or AWS Certificate Manager)
- [ ] API keys for external services
- [ ] Production server (EC2, DigitalOcean, etc.)
## Quick Setup
### 1. Automated Setup (Recommended)
Run the automated setup script:
```bash
cd /path/to/RichesReach
python scripts/setup_production_env.py
```
This script will:
- Generate secure secret keys
- Create production environment files
- Configure API keys and database settings
- Set up security configurations
### 2. Manual Setup
If you prefer manual setup, follow the steps below.
## Environment Files Structure
```
RichesReach/
├── backend/
│ ├── .env # Production environment variables
│ ├── production.env.template # Template for production env
│ └── validate_env.py # Environment validation script
├── mobile/
│ └── env.production # Mobile app production config
└── scripts/
├── setup_production_env.py # Environment setup script
└── setup_production_database.py # Database setup script
```
## Backend Environment Configuration
### Required Environment Variables
Create a `.env` file in the `backend/` directory with the following variables:
```bash
# Django Core Settings
SECRET_KEY=your-super-secure-production-secret-key
DEBUG=False
ENVIRONMENT=production
DOMAIN_NAME=yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
# Database Configuration (AWS RDS PostgreSQL)
DB_NAME=richesreach_prod
DB_USER=postgres
DB_PASSWORD=your-secure-database-password
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432
# Redis Configuration (AWS ElastiCache)
REDIS_HOST=your-elasticache-endpoint.cache.amazonaws.com
REDIS_PORT=6379
REDIS_DB=0
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
# API Keys
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key
NEWS_API_KEY=your-news-api-key
OPENAI_API_KEY=your-openai-api-key
# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=us-east-1
# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
# Monitoring
SENTRY_DSN=your-sentry-dsn-here
LOG_LEVEL=INFO
```
## Mobile App Environment Configuration
Create an `env.production` file in the `mobile/` directory:
```bash
# API Endpoints
EXPO_PUBLIC_API_URL=https://api.yourdomain.com
EXPO_PUBLIC_GRAPHQL_URL=https://api.yourdomain.com/graphql
EXPO_PUBLIC_RUST_API_URL=https://api.yourdomain.com:3001
EXPO_PUBLIC_WS_URL=wss://api.yourdomain.com/ws
# App Configuration
EXPO_PUBLIC_ENVIRONMENT=production
EXPO_PUBLIC_APP_VERSION=1.0.0
EXPO_PUBLIC_BUILD_NUMBER=1
EXPO_PUBLIC_APP_NAME=RichesReach
# API Keys
EXPO_PUBLIC_ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key
EXPO_PUBLIC_NEWS_API_KEY=your-news-api-key
# Feature Flags
EXPO_PUBLIC_ENABLE_BIOMETRIC_AUTH=true
EXPO_PUBLIC_ENABLE_PUSH_NOTIFICATIONS=true
EXPO_PUBLIC_ENABLE_ANALYTICS=true
EXPO_PUBLIC_ENABLE_CRASH_REPORTING=true
# Monitoring
EXPO_PUBLIC_SENTRY_DSN=your-sentry-dsn-here
EXPO_PUBLIC_ANALYTICS_ID=your-analytics-id-here
# Security
EXPO_PUBLIC_ENABLE_SSL_PINNING=true
EXPO_PUBLIC_ENABLE_CERTIFICATE_PINNING=true
```
## Database Setup
### 1. AWS RDS PostgreSQL Setup
1. **Create RDS Instance**:
- Engine: PostgreSQL 14+
- Instance class: db.t3.micro (for testing) or db.t3.small (for production)
- Storage: 20GB minimum
- Enable encryption at rest
- Configure security groups
2. **Configure Database**:
```bash
# Run database setup script
python scripts/setup_production_database.py
```
3. **Manual Database Setup**:
```bash
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```
### 2. Redis Setup (AWS ElastiCache)
1. **Create ElastiCache Cluster**:
- Engine: Redis 6.x
- Node type: cache.t3.micro (for testing) or cache.t3.small (for production)
- Enable encryption in transit
- Configure security groups
## API Keys Setup
### Required API Keys
1. **Alpha Vantage** (Stock Data)
- Sign up: https://www.alphavantage.co/support/#api-key
- Free tier: 500 calls/day
- Production tier: $49.99/month
2. **News API** (Financial News)
- Sign up: https://newsapi.org/register
- Free tier: 100 requests/day
- Production tier: $449/month
3. **OpenAI** (AI Recommendations)
- Sign up: https://platform.openai.com/
- Pay-per-use pricing
### Optional API Keys
4. **Sentry** (Error Tracking)
- Sign up: https://sentry.io/
- Free tier: 5,000 errors/month
5. **AWS** (Infrastructure)
- S3 for static files
- RDS for database
- ElastiCache for Redis
## Security Configuration
### 1. SSL/TLS Setup
- Use Let's Encrypt for free SSL certificates
- Or AWS Certificate Manager for managed certificates
- Enable HTTPS redirects
- Configure HSTS headers
### 2. Environment Security
- Never commit `.env` files to version control
- Use strong, unique passwords
- Rotate API keys regularly
- Enable database encryption
- Use VPC for network isolation
### 3. Application Security
- Enable Django security middleware
- Configure CORS properly
- Use secure session cookies
- Implement rate limiting
- Enable CSRF protection
## Monitoring Setup
### 1. Error Tracking (Sentry)
```python
# Add to Django settings
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
sentry_sdk.init(
dsn="your-sentry-dsn",
integrations=[DjangoIntegration()],
traces_sample_rate=1.0,
send_default_pii=True
)
```
### 2. Logging Configuration
```python
# Add to Django settings
LOGGING = {
'version': 1,
'disable_existing_loggers': False,
'handlers': {
'file': {
'level': 'INFO',
'class': 'logging.FileHandler',
'filename': '/var/log/richesreach/django.log',
},
},
'loggers': {
'django': {
'handlers': ['file'],
'level': 'INFO',
'propagate': True,
},
},
}
```
## Deployment Checklist
### Pre-Deployment
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] SSL certificate installed
- [ ] API keys configured
- [ ] Monitoring setup
- [ ] Security settings enabled
### Post-Deployment
- [ ] Test all API endpoints
- [ ] Verify database connectivity
- [ ] Check error tracking
- [ ] Monitor performance
- [ ] Test mobile app connectivity
- [ ] Verify email functionality
## Validation Scripts
### Environment Validation
```bash
cd backend
python validate_env.py
```
### Database Connection Test
```bash
cd backend
python manage.py check --database default
```
### API Endpoint Test
```bash
curl -X POST https://api.yourdomain.com/graphql/ \
-H "Content-Type: application/json" \
-d '{"query": "query { __schema { queryType { name } } }"}'
```
## 🆘 Troubleshooting
### Common Issues
1. **Database Connection Failed**
- Check security groups
- Verify credentials
- Ensure RDS instance is running
2. **SSL Certificate Issues**
- Verify certificate is valid
- Check domain configuration
- Ensure HTTPS redirects are working
3. **API Key Errors**
- Verify keys are correct
- Check rate limits
- Ensure keys are active
4. **Static Files Not Loading**
- Run `collectstatic`
- Check S3 bucket permissions
- Verify AWS credentials
### Support
For additional help:
- Check Django logs: `/var/log/richesreach/django.log`
- Monitor Sentry for errors
- Review AWS CloudWatch logs
- Check Redis connection status
## Additional Resources
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [Redis Security Guide](https://redis.io/docs/manual/security/)
- [SSL/TLS Best Practices](https://ssl-config.mozilla.org/)
