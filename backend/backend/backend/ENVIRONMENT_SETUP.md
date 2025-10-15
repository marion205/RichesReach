# Environment Setup Guide

## API Keys Configuration

All API keys are now configured via environment variables for security. **Never commit API keys to the repository.**

### Required Environment Variables

Copy `env.template` to `.env` and fill in your actual API keys:

```bash
cp env.template .env
```

### API Keys Needed

1. **OpenAI API Key** - For AI recommendations
   - Get from: https://platform.openai.com/api-keys
   - Set: `OPENAI_API_KEY=sk-...`

2. **Alpha Vantage API Key** - For stock market data
   - Get from: https://www.alphavantage.co/support/#api-key
   - Set: `ALPHA_VANTAGE_API_KEY=...`

3. **Finnhub API Key** - For real-time market data
   - Get from: https://finnhub.io/register
   - Set: `FINNHUB_API_KEY=...`

4. **Polygon API Key** - For options data
   - Get from: https://polygon.io/
   - Set: `POLYGON_API_KEY=...`

5. **News API Key** - For financial news
   - Get from: https://newsapi.org/
   - Set: `NEWS_API_KEY=...`

### Production Deployment

For production (AWS ECS), set these environment variables in:

1. **AWS Secrets Manager** (recommended)
2. **ECS Task Definition** environment variables
3. **ECS Task Definition** secrets (for sensitive data)

### Local Development

Create a `.env` file in the `backend/backend/` directory:

```bash
cd backend/backend
cp ../env.template .env
# Edit .env with your actual API keys
```

### Security Notes

- ✅ API keys are read from environment variables only
- ✅ No hardcoded API keys in the codebase
- ✅ Template files show required variables without actual keys
- ✅ Production uses AWS Secrets Manager
- ❌ Never commit `.env` files to git
- ❌ Never put API keys in code comments or documentation

### Verification

To verify your setup:

```bash
# Check if environment variables are loaded
python manage.py shell
>>> import os
>>> print("OpenAI Key:", "SET" if os.getenv('OPENAI_API_KEY') else "NOT SET")
>>> print("Finnhub Key:", "SET" if os.getenv('FINNHUB_API_KEY') else "NOT SET")
```
