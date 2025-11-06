# Yodlee Setup Instructions

## ✅ Environment Variables Created

Created `.env.yodlee` file with all required configuration. Copy these to your main `.env` file.

## 📋 Setup Steps

### 1. Install Dependencies

```bash
# Required for token encryption
pip install cryptography

# Optional - for async tasks
pip install celery

# Optional - for AWS KMS encryption
pip install boto3
```

### 2. Configure Environment Variables

Copy variables from `deployment_package/backend/.env.yodlee` to your main `.env` file, or export them:

```bash
export USE_YODLEE=true
export YODLEE_BASE_URL=https://sandbox.api.yodlee.com/ysl
export YODLEE_CLIENT_ID=your_client_id
export YODLEE_SECRET=your_client_secret
export YODLEE_APP_ID=your_app_id
export YODLEE_FASTLINK_URL=https://fastlink.yodlee.com
export YODLEE_WEBHOOK_SECRET=your_webhook_secret
```

### 3. Generate Encryption Key (if using Fernet)

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and set it as `BANK_TOKEN_ENC_KEY` in your `.env` file.

### 4. Run Migrations (when Django is available)

```bash
cd deployment_package/backend

# Activate virtual environment if using one
# source venv/bin/activate  # or your venv path

# Create migrations
python manage.py makemigrations core

# Apply migrations
python manage.py migrate
```

This will create the following tables:
- `bank_provider_accounts`
- `bank_accounts`
- `bank_transactions`
- `bank_webhook_events`

### 5. Test Endpoints

Once Django is running and migrations are applied:

```bash
# Test FastLink start
curl -X GET http://localhost:8000/api/yodlee/fastlink/start \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test accounts endpoint
curl -X GET http://localhost:8000/api/yodlee/accounts \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test GraphQL
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ bankAccounts { id provider name balanceCurrent } }"}'
```

## 🔧 Configuration Details

### Yodlee Credentials

You'll need to get these from Yodlee:
1. **Client ID** - Your Yodlee API client ID
2. **Client Secret** - Your Yodlee API secret
3. **App ID** - Your Yodlee application ID
4. **Webhook Secret** - For webhook signature verification

### Encryption Methods

**Fernet (Recommended for development):**
- Simple to set up
- Requires `cryptography` library
- Key stored in environment variable

**AWS KMS (Recommended for production):**
- More secure
- Requires AWS credentials
- Key stored in AWS KMS

### Retry Logic

Configure retry behavior:
- `YODLEE_MAX_RETRIES=3` - Max retry attempts
- `YODLEE_RETRY_DELAY=1` - Initial delay in seconds
- `YODLEE_TIMEOUT=10` - Request timeout in seconds

## 📝 Notes

- **Django Required**: Migrations need Django to be installed and available
- **Virtual Environment**: If using a virtual environment, activate it before running migrations
- **Production**: Use production Yodlee URLs and credentials in production
- **Security**: Never commit `.env` files with real credentials to git

## 🚀 Next Steps

1. ✅ Environment variables configured (`.env.yodlee`)
2. ⏳ Install dependencies (`pip install cryptography`)
3. ⏳ Run migrations (when Django is available)
4. ⏳ Configure Yodlee credentials
5. ⏳ Test endpoints

## 📚 Documentation

- `YODLEE_IMPLEMENTATION_COMPLETE.md` - Full implementation guide
- `YODLEE_ENHANCEMENTS_COMPLETE.md` - Enhancements documentation
- `BANK_INTEGRATIONS_STATUS.md` - Integration status

