# Production Real Data Setup Guide

## 🎯 Overview
This guide ensures your production environment uses **real data** instead of mock data, with PostgreSQL database and live market data APIs.

## ✅ Current Status
Your system is already configured to use real data when properly configured. The issue is ensuring the right environment variables are set in production.

## 🔧 Required Production Environment Variables

### 1. Database Configuration (PostgreSQL)
```bash
# Option 1: Use DATABASE_URL (Recommended)
DATABASE_URL=postgresql://username:password@your-postgres-host:5432/richesreach_prod

# Option 2: Use individual variables
DJANGO_DB_ENGINE=django.db.backends.postgresql
DJANGO_DB_NAME=richesreach_prod
DJANGO_DB_USER=your_db_user
DJANGO_DB_PASSWORD=your_db_password
DJANGO_DB_HOST=your-postgres-host
DJANGO_DB_PORT=5432
```

### 2. Real Market Data API Keys
```bash
# Required for real market data (get these from service providers)
POLYGON_API_KEY=your-polygon-api-key-here
FINNHUB_API_KEY=your-finnhub-api-key-here
NEWS_API_KEY=your-news-api-key-here

# Enable real data sources
USE_FINNHUB=true
DISABLE_ALPHA_VANTAGE=true
```

### 3. Disable Mock Data Services
```bash
# Disable all mock data services
USE_OPENAI=true                    # Only if you want AI features
USE_YODLEE=false                   # Disable mock bank linking
USE_SBLOC_MOCK=false              # Disable mock SBLOC
USE_SBLOC_AGGREGATOR=true         # Use real SBLOC if available
```

### 4. Production Security Settings
```bash
DEBUG=false
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=your-domain.com,app.richesreach.net
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_CONTENT_TYPE_NOSNIFF=true
SECURE_BROWSER_XSS_FILTER=true
X_FRAME_OPTIONS=DENY
```

### 5. Redis Configuration (for caching)
```bash
REDIS_URL=redis://your-redis-host:6379/0
# OR individual variables:
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-redis-password
```

## 🚨 Current Issues to Fix

### Issue 1: RealDataService Session Error
From your logs:
```
WARNING richesreach: Failed to get real quote for AAPL: 'RealDataService' object has no attribute '_session'
```

**Solution:** The RealDataService needs proper initialization. This is likely happening because the service isn't being imported/used correctly.

### Issue 2: Missing API Keys
If you see:
```
WARNING: No API keys configured. Using mock data.
```

**Solution:** Set the required API keys in your production environment.

## 📋 Production Deployment Checklist

### Before Deployment:
- [ ] Set all required environment variables
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching
- [ ] Obtain API keys from:
  - [Polygon.io](https://polygon.io/) for market data
  - [Finnhub](https://finnhub.io/) for real-time quotes
  - [NewsAPI](https://newsapi.org/) for news data
- [ ] Test database connectivity
- [ ] Test API key validity

### During Deployment:
- [ ] Use production deployment scripts (`deploy-*.sh`)
- [ ] Verify environment variables are loaded
- [ ] Check database migrations
- [ ] Test health endpoints

### After Deployment:
- [ ] Verify real data is being fetched
- [ ] Check logs for any mock data warnings
- [ ] Test key functionality (stock quotes, portfolio data)
- [ ] Monitor API rate limits

## 🔍 Verification Commands

### Check if real data is working:
```bash
# Test health endpoint
curl https://your-domain.com/health

# Test GraphQL with real data
curl -X POST https://your-domain.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { stocks(limit: 1) { symbol currentPrice } }"}'
```

### Check logs for mock data warnings:
```bash
# Look for these warning messages:
grep -i "mock\|fallback" /var/log/your-app.log
```

## 🛠️ API Key Setup

### 1. Polygon.io
- Sign up at [polygon.io](https://polygon.io/)
- Get your API key from the dashboard
- Set `POLYGON_API_KEY=your-key-here`

### 2. Finnhub
- Sign up at [finnhub.io](https://finnhub.io/)
- Get your API key from the dashboard
- Set `FINNHUB_API_KEY=your-key-here`

### 3. NewsAPI
- Sign up at [newsapi.org](https://newsapi.org/)
- Get your API key from the dashboard
- Set `NEWS_API_KEY=your-key-here`

## 📊 Expected Behavior

### With Real Data:
- Stock prices update in real-time
- Company profiles show actual data
- News feeds show real financial news
- Portfolio values reflect actual market prices

### Without Real Data (Mock Mode):
- You'll see warning messages in logs
- Data will be static or simulated
- Performance may be limited

## 🚀 Quick Production Setup

1. **Set environment variables** in your production environment
2. **Deploy using production scripts**:
   ```bash
   ./deploy_production_clean.sh
   ```
3. **Verify real data**:
   ```bash
   curl https://your-domain.com/health
   ```
4. **Check logs** for any mock data warnings

## 📞 Support

If you're still seeing mock data in production:
1. Check your environment variables are set correctly
2. Verify API keys are valid and have sufficient quota
3. Check logs for specific error messages
4. Ensure PostgreSQL database is accessible

---

**Note:** This guide assumes you're using the standard deployment process. If you're using a different deployment method, adjust accordingly.
