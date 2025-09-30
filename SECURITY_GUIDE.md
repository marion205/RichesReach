# 🔐 RichesReach Security Guide

## API Key Management

### ✅ **SECURE APPROACH** - Environment Variables

API keys should **NEVER** be hardcoded in source code or committed to version control. Instead, use environment variables:

#### **Local Development**
```bash
# 1. Copy the template
cp env.template .env

# 2. Edit .env with your actual API keys
nano .env

# 3. Run the setup script (automatically configures keys)
./setup-local-env.sh
```

#### **Production (AWS)**
```bash
# 1. Store secrets in AWS Secrets Manager
./setup-aws-secrets.sh

# 2. Deploy with secure configuration
./deploy-aws-secure.sh
```

### 🚫 **INSECURE APPROACH** - What NOT to do

```bash
# ❌ NEVER do this - hardcoded in source code
OPENAI_API_KEY = "sk-proj-abc123..."

# ❌ NEVER do this - in deployment scripts
echo "OPENAI_API_KEY=sk-proj-abc123" >> task-definition.json

# ❌ NEVER do this - committed to git
git add .env  # Contains real API keys
```

## Environment File Structure

### `.env` (Local Development)
```bash
# Django Configuration
DEBUG=False
SECRET_KEY=your-generated-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# API Keys (from your service providers)
POLYGON_API_KEY=your-actual-polygon-key
FINNHUB_API_KEY=your-actual-finnhub-key
NEWS_API_KEY=your-actual-news-key
OPENAI_API_KEY=your-actual-openai-key

# Configuration
USE_OPENAI=true
OPENAI_MODEL=gpt-4o-mini
REDIS_URL=redis://localhost:6379/0
```

### AWS Secrets Manager (Production)
- **Secret Name**: `richesreach/polygon-api-key`
- **Secret Name**: `richesreach/finnhub-api-key`
- **Secret Name**: `richesreach/openai-api-key`

## Security Best Practices

### 1. **Environment Variables**
- ✅ Store API keys in environment variables
- ✅ Use `.env` files for local development
- ✅ Use AWS Secrets Manager for production
- ✅ Never commit `.env` files to git

### 2. **Git Security**
- ✅ Add `.env` to `.gitignore`
- ✅ Use `env.template` for sharing configuration structure
- ✅ Remove API keys from deployment scripts before committing

### 3. **Production Security**
- ✅ Use AWS Secrets Manager for cloud deployments
- ✅ Rotate API keys regularly
- ✅ Monitor API key usage
- ✅ Use least-privilege access

## Quick Setup Commands

### **Local Development**
```bash
# Setup secure local environment
./setup-local-env.sh

# Start local server
cd backend/backend && python final_complete_server.py
```

### **AWS Production**
```bash
# Setup secure AWS deployment
./setup-aws-secrets.sh
./deploy-aws-secure.sh
```

## API Key Sources

### **Polygon API**
- **Website**: https://polygon.io/
- **Free Tier**: 5 API calls/minute
- **Paid Plans**: Starting at $99/month

### **Finnhub API**
- **Website**: https://finnhub.io/
- **Free Tier**: 60 API calls/minute
- **Paid Plans**: Starting at $9/month

### **OpenAI API**
- **Website**: https://openai.com/api/
- **Pricing**: Pay-per-use
- **Model**: gpt-4o-mini (recommended for cost efficiency)

### **News API**
- **Website**: https://newsapi.org/
- **Free Tier**: 1000 requests/day
- **Paid Plans**: Starting at $449/month

## Troubleshooting

### **API Key Not Working**
1. Check if key is correctly set in environment
2. Verify key is active and has sufficient quota
3. Check API provider dashboard for usage limits

### **Environment Variables Not Loading**
1. Ensure `.env` file is in the correct directory
2. Check file permissions (should be readable)
3. Restart the application after changing environment variables

### **AWS Secrets Not Accessible**
1. Verify ECS task has proper IAM permissions
2. Check secret ARN is correct in task definition
3. Ensure secrets exist in the correct AWS region

## Security Checklist

- [ ] API keys stored in environment variables
- [ ] `.env` file added to `.gitignore`
- [ ] No hardcoded secrets in source code
- [ ] AWS Secrets Manager configured for production
- [ ] API keys rotated regularly
- [ ] Monitoring enabled for API usage
- [ ] Least-privilege access configured
