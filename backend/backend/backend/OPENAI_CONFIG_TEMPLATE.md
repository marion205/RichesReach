# OpenAI Configuration Templates

## Staging Environment (.env.staging)

```bash
# OpenAI Configuration - Staging
USE_OPENAI=true
OPENAI_API_KEY_STAGING=your_staging_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1200
OPENAI_TIMEOUT_MS=12000
OPENAI_ENABLE_FALLBACK=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/richesreach_staging

# Debug
DEBUG=true
```

## Production Environment (.env.prod)

```bash
# OpenAI Configuration - Production
USE_OPENAI=true
OPENAI_API_KEY_PROD=your_production_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1200
OPENAI_TIMEOUT_MS=12000
OPENAI_ENABLE_FALLBACK=true

# Database
DATABASE_URL=postgresql://user:password@prod-db:5432/richesreach_prod

# Debug
DEBUG=false
```

## Development Environment (.env.dev)

```bash
# OpenAI Configuration - Development (Mock Mode)
USE_OPENAI=false
OPENAI_ENABLE_FALLBACK=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/richesreach_dev

# Debug
DEBUG=true
```

## Quick Setup Instructions

1. **Create separate OpenAI API keys:**
   - Go to [OpenAI Platform](https://platform.openai.com/)
   - Create one key for staging, one for production
   - Add $10-25 prepay to each account
   - Set monthly/daily limits and email alerts

2. **Copy the appropriate template to `.env`:**
   ```bash
   # For staging testing
   cp OPENAI_CONFIG_TEMPLATE.md .env.staging
   # Edit .env.staging with your staging API key
   
   # For production
   cp OPENAI_CONFIG_TEMPLATE.md .env.prod
   # Edit .env.prod with your production API key
   ```

3. **Test the configuration:**
   ```bash
   # Test staging
   curl -X POST http://localhost:8000/api/ai-options/recommendations \
     -H "Content-Type: application/json" \
     -d '{"symbol":"AAPL","portfolio_value":10000,"time_horizon":30,"user_risk_tolerance":"medium"}'
   
   # Should return: "AI recommendations generated successfully using OpenAI"
   ```

4. **Monitor usage:**
   - Check OpenAI dashboard for token usage
   - Watch server logs for fallback triggers
   - Set up alerts for quota limits

## Safety Features

- ✅ **Feature Flag**: `USE_OPENAI` controls OpenAI usage
- ✅ **Environment Separation**: Different API keys for staging/prod
- ✅ **Automatic Fallback**: Falls back to mock data on any error
- ✅ **Timeout Protection**: 12-second timeout prevents hanging
- ✅ **Graceful Degradation**: App works even if OpenAI is down
- ✅ **Usage Monitoring**: Logs show which path was used
