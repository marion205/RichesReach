# 🔐 SECRET ROTATION GUIDE

## 🚨 **CRITICAL: Keys Exposed in Chat**

The following API keys were exposed in our conversation and **MUST be rotated immediately**:

### **Exposed Keys:**
- **Finnhub API Key**: `d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0`
- **Polygon API Key**: `K0A7XYLDNXHNQ1WI`
- **Alpha Vantage API Key**: `OHYSFF1AE446O7CR`
- **OpenAI API Key**: `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`
- **Alchemy API Key**: `nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM`
- **WalletConnect Project ID**: `42421cf8-2df7-45c6-9475-df4f4b115ffc`
- **News API Key**: `94a335c7316145f79840edd62f77e11e`

---

## 🔄 **STEP-BY-STEP ROTATION PROCESS**

### **Step 1: Get New Keys from Providers**

#### **1.1 Finnhub**
1. Go to: https://finnhub.io/account
2. Log in to your account
3. Navigate to API Keys section
4. Generate a new API key
5. **Copy the new key**

#### **1.2 Polygon.io**
1. Go to: https://polygon.io/dashboard
2. Log in to your account
3. Navigate to API Keys section
4. Generate a new API key
5. **Copy the new key**

#### **1.3 Alpha Vantage**
1. Go to: https://www.alphavantage.co/support/#api-key
2. Log in to your account
3. Generate a new API key
4. **Copy the new key**

#### **1.4 OpenAI**
1. Go to: https://platform.openai.com/api-keys
2. Log in to your account
3. Create a new API key
4. **Copy the new key**

#### **1.5 Alchemy**
1. Go to: https://dashboard.alchemy.com/
2. Log in to your account
3. Navigate to API Keys section
4. Generate a new API key
5. **Copy the new key**

#### **1.6 WalletConnect**
1. Go to: https://cloud.walletconnect.com/
2. Log in to your account
3. Navigate to your project
4. Generate a new Project ID
5. **Copy the new Project ID**

#### **1.7 News API**
1. Go to: https://newsapi.org/account
2. Log in to your account
3. Generate a new API key
4. **Copy the new key**

---

### **Step 2: Rotate Keys in AWS Secrets Manager**

Once you have the new keys, use the rotation script:

```bash
# Rotate each key (replace NEW_KEY with your actual new key)
./rotate_secrets_manual.sh finnhub_api_key "YOUR_NEW_FINNHUB_KEY"
./rotate_secrets_manual.sh polygon_api_key "YOUR_NEW_POLYGON_KEY"
./rotate_secrets_manual.sh alpha_vantage_key "YOUR_NEW_ALPHA_VANTAGE_KEY"
./rotate_secrets_manual.sh openai_api_key "YOUR_NEW_OPENAI_KEY"
./rotate_secrets_manual.sh alchemy_key "YOUR_NEW_ALCHEMY_KEY"
./rotate_secrets_manual.sh walletconnect_id "YOUR_NEW_WALLETCONNECT_ID"
./rotate_secrets_manual.sh newsapi_key "YOUR_NEW_NEWSAPI_KEY"
```

---

### **Step 3: Verify Rotation**

After rotating each key, verify it was updated:

```bash
# Verify a specific secret
aws secretsmanager get-secret-value \
  --secret-id richesreach/production/finnhub_api_key \
  --query 'SecretString' --output text | jq -r '.value'
```

---

### **Step 4: Update Your Local Environment**

Update your local development environment with the new keys:

```bash
# Update your .env file or environment variables
export FINNHUB_API_KEY="YOUR_NEW_FINNHUB_KEY"
export POLYGON_API_KEY="YOUR_NEW_POLYGON_KEY"
export ALPHA_VANTAGE_API_KEY="YOUR_NEW_ALPHA_VANTAGE_KEY"
export OPENAI_API_KEY="YOUR_NEW_OPENAI_KEY"
export ALCHEMY_API_KEY="YOUR_NEW_ALCHEMY_KEY"
export WALLETCONNECT_PROJECT_ID="YOUR_NEW_WALLETCONNECT_ID"
export NEWS_API_KEY="YOUR_NEW_NEWSAPI_KEY"
```

---

### **Step 5: Test Your Application**

Restart your server and test that everything works:

```bash
# Restart your server with new keys
cd backend && python3 -m uvicorn backend.final_complete_server:app --host 0.0.0.0 --port 8000 --reload

# Test the health endpoint
curl http://localhost:8000/health

# Test GraphQL endpoints
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { dayTradingPicks { symbol name score } }"}'
```

---

## 🛡️ **SECURITY BEST PRACTICES**

### **After Rotation:**
1. **Delete old keys** from provider dashboards
2. **Monitor usage** for any unauthorized access
3. **Set up alerts** for unusual API usage
4. **Review access logs** for the past 24 hours

### **Going Forward:**
1. **Never share keys** in chat or code
2. **Use environment variables** for local development
3. **Use AWS Secrets Manager** for production
4. **Rotate keys regularly** (every 30-90 days)
5. **Monitor key usage** and set up alerts

---

## 🆘 **EMERGENCY PROCEDURES**

### **If You Suspect Compromise:**
1. **Immediately rotate** all affected keys
2. **Check usage logs** for unauthorized access
3. **Contact providers** if you see suspicious activity
4. **Review all recent deployments** for exposed keys

### **Rollback Procedure:**
If a new key doesn't work, you can rollback to the previous version:

```bash
# Get previous version
aws secretsmanager get-secret-value \
  --secret-id richesreach/production/finnhub_api_key \
  --version-stage AWSPREVIOUS

# Promote previous version to current
aws secretsmanager update-secret-version-stage \
  --secret-id richesreach/production/finnhub_api_key \
  --version-stage AWSCURRENT \
  --move-to-version-id PREVIOUS_VERSION_ID
```

---

## 📞 **SUPPORT**

If you need help with the rotation process:
1. Check the AWS Secrets Manager console
2. Review the rotation script logs
3. Test with a non-critical secret first
4. Contact me for assistance

**Remember: Security is everyone's responsibility. Let's keep your RichesReach platform secure!** 🔐
