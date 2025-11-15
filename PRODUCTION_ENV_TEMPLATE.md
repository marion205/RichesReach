# Production Environment Variables Template

**⚠️ IMPORTANT**: This is a template. Copy to `.env` and fill in your actual production values.
**🔒 SECURITY**: Never commit `.env` files to version control!

---

## 📋 Week 1: Environment Setup Checklist

Use this template to create your production `.env` file in `deployment_package/backend/.env`

---

## 🔐 Django Core Settings

```bash
# Generate a new SECRET_KEY for production (DO NOT use development key)
# Run: python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=your-generated-secret-key-here

DEBUG=False
ENVIRONMENT=production

# Your production domain(s) - comma separated
ALLOWED_HOSTS=api.richesreach.com,www.richesreach.com,richesreach.com

# Domain name
DOMAIN_NAME=richesreach.com
```

---

## 🗄️ Database Configuration (AWS RDS PostgreSQL)

```bash
# Production database connection
DB_NAME=richesreach_prod
DB_USER=your-db-user
DB_PASSWORD=your-secure-db-password
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432

# Alternative: Use DATABASE_URL format
DATABASE_URL=postgresql://your-db-user:your-secure-db-password@your-rds-endpoint.region.rds.amazonaws.com:5432/richesreach_prod
```

---

## 🔴 Redis Configuration (AWS ElastiCache)

```bash
REDIS_HOST=your-elasticache-endpoint.cache.amazonaws.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-redis-password-if-required

# Celery Configuration
CELERY_BROKER_URL=redis://:your-redis-password-if-required@your-elasticache-endpoint.cache.amazonaws.com:6379/0
CELERY_RESULT_BACKEND=redis://:your-redis-password-if-required@your-elasticache-endpoint.cache.amazonaws.com:6379/1
```

---

## 🤖 AI & ML Services

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-production-openai-key
OPENAI_MODEL=gpt-4o
USE_OPENAI=true
```

---

## 📊 Market Data APIs

```bash
# Finnhub
FINNHUB_API_KEY=your-finnhub-production-key

# Polygon.io
POLYGON_API_KEY=your-polygon-production-key

# Alpha Vantage
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-production-key

# News API
NEWS_API_KEY=your-news-api-production-key

# IEX Cloud (if using)
IEX_CLOUD_API_KEY=your-iex-cloud-production-key

# Quandl (if using)
QUANDL_API_KEY=your-quandl-production-key
```

---

## 💼 Broker & Trading APIs

```bash
# Alpaca Broker API (PRODUCTION)
ALPACA_BROKER_API_KEY=your-alpaca-broker-production-key
ALPACA_BROKER_API_SECRET=your-alpaca-broker-production-secret
ALPACA_BROKER_BASE_URL=https://broker-api.alpaca.markets
ALPACA_WEBHOOK_SECRET=your-alpaca-webhook-secret

# Alpaca Trading API (if using)
ALPACA_API_KEY=your-alpaca-trading-key
ALPACA_API_SECRET=your-alpaca-trading-secret
ALPACA_BASE_URL=https://api.alpaca.markets
```

---

## 🏦 Banking Integration (Yodlee)

```bash
# Yodlee Configuration
USE_YODLEE=true
YODLEE_BASE_URL=https://api.yodlee.com/ysl  # Production URL (not sandbox)
YODLEE_CLIENT_ID=your-yodlee-client-id
YODLEE_SECRET=your-yodlee-client-secret
YODLEE_APP_ID=your-yodlee-app-id
YODLEE_FASTLINK_URL=https://fastlink.yodlee.com
YODLEE_WEBHOOK_SECRET=your-yodlee-webhook-secret

# Token Encryption
BANK_TOKEN_ENCRYPTION=fernet
BANK_TOKEN_ENC_KEY=your-encryption-key-here
# Generate key: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 💰 SBLOC Integration

```bash
USE_SBLOC_MOCK=false
USE_SBLOC_AGGREGATOR=true
# Add SBLOC aggregator API keys if needed
```

---

## ☁️ AWS Configuration

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_ACCOUNT_ID=498606688292
AWS_REGION=us-east-1

# S3 Configuration
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=us-east-1
DATA_LAKE_BUCKET=riches-reach-ai-datalake-20251005

# KMS (if using for encryption)
AWS_KMS_KEY_ID=arn:aws:kms:us-east-1:498606688292:key/your-key-id
```

---

## 📧 Email Configuration

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@richesreach.com
```

---

## 🌐 Frontend & API URLs

```bash
# Production API URL
API_BASE_URL=https://api.richesreach.com
FRONTEND_URL=https://app.richesreach.com

# WebSocket
WS_URL=wss://api.richesreach.com/ws/
```

---

## 🔒 Security Settings

```bash
# SSL/TLS
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CORS (if needed)
CORS_ALLOWED_ORIGINS=https://app.richesreach.com,https://www.richesreach.com
```

---

## 🐛 Monitoring & Error Tracking

```bash
# Sentry (Error Tracking)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/your-project-id

# Application Performance Monitoring (optional)
APM_ENABLED=true
APM_SERVICE_NAME=richesreach-backend
```

---

## 🔗 Blockchain/Web3 (if using)

```bash
# WalletConnect
WALLETCONNECT_PROJECT_ID=42421cf8-2df7-45c6-9475-df4f4b115ffc

# Alchemy
ALCHEMY_API_KEY=your-alchemy-production-key
SEPOLIA_ETH_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your-key
```

---

## 📡 Streaming & Kafka Configuration

```bash
# Enable Kafka for real-time data streaming
KAFKA_ENABLED=true
KAFKA_BOOTSTRAP_SERVERS=b-3.richesreachkafka.kbr9fv.c4.kafka.us-east-1.amazonaws.com:9094,b-2.richesreachkafka.kbr9fv.c4.kafka.us-east-1.amazonaws.com:9094,b-1.richesreachkafka.kbr9fv.c4.kafka.us-east-1.amazonaws.com:9094
KAFKA_GROUP_ID=riches-reach-producer
KAFKA_TOPIC_PREFIX=richesreach
ENABLE_STREAMING=true
STREAMING_MODE=production
```

**Kafka Topics:**
- `market-data` - Real-time stock prices
- `technical-indicators` - Calculated technical indicators
- `ml-predictions` - AI model predictions
- `user-events` - User interactions

---

## 🗄️ Data Lake Configuration (S3)

```bash
# S3 Data Lake for long-term storage
DATA_LAKE_BUCKET=riches-reach-ai-datalake-20251005
AWS_S3_REGION_NAME=us-east-1
```

**Data Lake Structure:**
- `raw/` - Original data from sources (Polygon, Finnhub, etc.)
- `processed/` - Cleaned/transformed data and ML features
- `curated/` - Analytics-ready data and summaries
- `metadata/` - Schemas and data lineage

**Lifecycle Policies:**
- 30 days → Standard-IA (Infrequent Access)
- 90 days → Glacier (Archive)
- 365 days → Deep Archive

---

## 🎯 Feature Flags

```bash
# Enable/disable features
ENABLE_ML_SERVICES=true
ENABLE_MONITORING=true
ENABLE_STREAMING=true
```

---

## 📝 Quick Setup Commands

### 1. Generate Django SECRET_KEY
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Generate Fernet Encryption Key (for banking tokens)
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Create .env file
```bash
cd deployment_package/backend
cp ../PRODUCTION_ENV_TEMPLATE.md .env
# Then edit .env and fill in all values
```

### 4. Verify .env is in .gitignore
```bash
# Make sure .env is in .gitignore
echo ".env" >> .gitignore
```

---

## ✅ Verification Checklist

After creating your `.env` file, verify:

- [ ] SECRET_KEY is generated (not from development)
- [ ] DEBUG=False
- [ ] All API keys are production keys (not sandbox/test)
- [ ] Database credentials are correct
- [ ] Redis credentials are correct
- [ ] AWS credentials are correct
- [ ] Domain names match your production domains
- [ ] SSL/TLS settings are enabled
- [ ] .env file is in .gitignore
- [ ] No secrets committed to version control

---

## 🚨 Security Reminders

1. **Never commit `.env` files** to version control
2. **Use different keys** for production vs development
3. **Rotate keys regularly** (especially if exposed)
4. **Use AWS Secrets Manager** or similar for sensitive values
5. **Limit access** to production environment variables
6. **Monitor for leaks** in logs, error messages, etc.

---

*Last Updated: November 2024*

