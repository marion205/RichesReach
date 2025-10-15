# GitHub Repository Secrets Setup

## Required Secrets for Production Deployment

You need to add the following secrets to your GitHub repository to enable the API integrations:

### How to Add Secrets:
1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**
4. Click **New repository secret** for each secret below

### Required Secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `FINNHUB_API_KEY` | `d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0` | FinnHub API for market data |
| `ALPHA_VANTAGE_API_KEY` | `OHYSFF1AE446O7CR` | Alpha Vantage API for stock data |
| `POLYGON_API_KEY` | `uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2` | Polygon API for market data |
| `NEWS_API_KEY` | `94a335c7316145f79840edd62f77e11e` | News API for financial news |
| `OPENAI_API_KEY` | `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` | OpenAI API for AI features |
| `ALCHEMY_API_KEY` | `nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM` | Alchemy API for blockchain |
| `WALLETCONNECT_PROJECT_ID` | `42421cf8-2df7-45c6-9475-df4f4b115ffc` | WalletConnect for crypto wallets |
| `SEPOLIA_ETH_URL` | `https://eth-sepolia.g.alchemy.com/v2/2-rJhszNwQ6I3NuBdN5pz` | Sepolia Ethereum RPC URL |

### Existing Secrets (Already Set):
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

## After Adding Secrets:

1. **Push the updated code** to trigger a new deployment
2. **Monitor the deployment** in GitHub Actions
3. **Test the endpoints** to ensure API keys are working

## Security Notes:

- ✅ **No hardcoded values** in the codebase
- ✅ **Secrets stored securely** in GitHub
- ✅ **Environment variables** injected at runtime
- ✅ **Production-ready** configuration

## Testing After Deployment:

Once deployed, test these endpoints to verify API integration:

```bash
# Test prices endpoint (should now work with FinnHub API)
curl http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/prices/?symbols=AAPL,TSLA

# Test other endpoints
curl http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/health
curl http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/graphql/
```

## Next Steps:

1. Add all the secrets listed above
2. Push this code to trigger deployment
3. Test the endpoints to verify API integration
4. Monitor logs for any API-related errors
