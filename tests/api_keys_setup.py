#!/usr/bin/env python3
"""
API Keys Setup Script for Live Market Data
Configure real API keys to enable live market intelligence
"""
import os
import sys
from pathlib import Path
def create_env_file():
"""Create .env file with API key templates"""
env_content = """# ============================================================================
# LIVE MARKET DATA API KEYS
# ============================================================================
# Get these keys from the respective services to enable live market data
# ============================================================================
# FINANCIAL DATA APIs
# ============================================================================
# Alpha Vantage - Stock quotes, forex, economic data
# Free tier: 5 calls/minute, 500 calls/day
# Get key: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
# Finnhub - Real-time market data, news, sentiment
# Free tier: 60 calls/minute
# Get key: https://finnhub.io/register
FINNHUB_API_KEY=your_finnhub_key_here
# Quandl - Economic and financial datasets
# Free tier: 50 calls/minute
# Get key: https://www.quandl.com/account/api
QUANDL_API_KEY=your_quandl_key_here
# Polygon - Market data, news, financial statements
# Free tier: 5 calls/minute
# Get key: https://polygon.io/
POLYGON_API_KEY=your_polygon_key_here
# IEX Cloud - Financial data and analytics
# Free tier: 100 calls/minute
# Get key: https://iexcloud.io/cloud-login#/register
IEX_CLOUD_API_KEY=your_iex_cloud_key_here
# ============================================================================
# ALTERNATIVE DATA APIs
# ============================================================================
# News API - Financial news and sentiment
# Free tier: 100 requests/day
# Get key: https://newsapi.org/register
NEWS_API_KEY=your_news_api_key_here
# Twitter API - Social media sentiment (optional)
# Requires Twitter Developer account
# Get key: https://developer.twitter.com/
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
# Sentiment Analysis API (optional)
# Various providers available
SENTIMENT_API_KEY=your_sentiment_api_key_here
# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================
# Set to 'production' to use real APIs, 'development' for synthetic data
ENVIRONMENT=development
# Cache duration in seconds (5 minutes for live data)
CACHE_DURATION=300
# Rate limiting (calls per minute per API)
ALPHA_VANTAGE_RATE_LIMIT=5
FINNHUB_RATE_LIMIT=60
QUANDL_RATE_LIMIT=50
POLYGON_RATE_LIMIT=5
IEX_CLOUD_RATE_LIMIT=100
NEWS_API_RATE_LIMIT=2
# ============================================================================
# MODEL TRAINING CONFIGURATION
# ============================================================================
# Historical data period for training (days)
HISTORICAL_DATA_DAYS=365
# Training data update frequency (hours)
TRAINING_UPDATE_FREQUENCY=24
# Model retraining threshold (accuracy drop %)
MODEL_RETRAIN_THRESHOLD=5.0
# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================
# Enable SSL verification for API calls
ENABLE_SSL_VERIFICATION=true
# API key encryption (optional)
ENCRYPT_API_KEYS=false
"""
env_file = Path('.env')
if env_file.exists():
print(f" .env file already exists. Backing up to .env.backup")
env_file.rename('.env.backup')
with open('.env', 'w') as f:
f.write(env_content)
print(f" Created .env file with API key templates")
print(f" File location: {env_file.absolute()}")
return env_file
def create_api_keys_guide():
"""Create a comprehensive guide for obtaining API keys"""
guide_content = """# API Keys Setup Guide for Live Market Data
## Quick Start
1. **Copy the .env file** to your project root
2. **Get API keys** from the services below
3. **Replace placeholder values** in .env file
4. **Set ENVIRONMENT=production** to enable live data
5. **Run the training script** to build models with real data
## Financial Data APIs
### Alpha Vantage
- **Website**: https://www.alphavantage.co/
- **Free Tier**: 5 calls/minute, 500 calls/day
- **Features**: Stock quotes, forex, economic indicators
- **Get Key**: 
1. Go to https://www.alphavantage.co/support/#api-key
2. Fill out the form
3. Receive key instantly via email
### Finnhub
- **Website**: https://finnhub.io/
- **Free Tier**: 60 calls/minute
- **Features**: Real-time stock data, news, sentiment
- **Get Key**:
1. Visit https://finnhub.io/register
2. Create account
3. Get API key from dashboard
### Quandl
- **Website**: https://www.quandl.com/
- **Free Tier**: 50 calls/minute
- **Features**: Economic data, financial statements
- **Get Key**:
1. Go to https://www.quandl.com/account/api
2. Sign up for account
3. Generate API key
### Polygon
- **Website**: https://polygon.io/
- **Free Tier**: 5 calls/minute
- **Features**: Market data, news, financials
- **Get Key**:
1. Visit https://polygon.io/
2. Create account
3. Get API key from dashboard
### IEX Cloud
- **Website**: https://iexcloud.io/
- **Free Tier**: 100 calls/minute
- **Features**: Financial data, analytics
- **Get Key**:
1. Go to https://iexcloud.io/cloud-login#/register
2. Sign up
3. Get API key from account
## Alternative Data APIs
### News API
- **Website**: https://newsapi.org/
- **Free Tier**: 100 requests/day
- **Features**: Financial news, sentiment analysis
- **Get Key**:
1. Visit https://newsapi.org/register
2. Create account
3. Get API key instantly
### Twitter API (Optional)
- **Website**: https://developer.twitter.com/
- **Features**: Social media sentiment
- **Get Key**:
1. Apply for Twitter Developer account
2. Create app
3. Generate bearer token
## Configuration Steps
### 1. Update .env File
```bash
# Replace placeholder values with real API keys
ALPHA_VANTAGE_API_KEY=abc123def456
FINNHUB_API_KEY=xyz789uvw012
QUANDL_API_KEY=def456ghi789
# ... etc
```
### 2. Enable Production Mode
```bash
# Change from development to production
ENVIRONMENT=production
```
### 3. Test API Connections
```bash
python3 test_api_connections.py
```
### 4. Train Models with Real Data
```bash
python3 train_with_real_data.py
```
## Data Sources by Feature
### Market Indicators
- **VIX**: Alpha Vantage, Yahoo Finance
- **Bond Yields**: Alpha Vantage, Quandl
- **Currency**: Alpha Vantage, Polygon
### Economic Data
- **GDP**: Quandl (FRED), Alpha Vantage
- **Inflation**: Quandl (FRED), Alpha Vantage
- **Employment**: Quandl (FRED), Alpha Vantage
### Sector Performance
- **ETF Data**: Alpha Vantage, Finnhub, IEX Cloud
- **Sector Analysis**: Polygon, Alpha Vantage
### Alternative Data
- **News**: News API, Alpha Vantage
- **Sentiment**: News API, Twitter API
- **Earnings**: Polygon, Alpha Vantage
## Cost Considerations
### Free Tiers (Recommended for Start)
- **Alpha Vantage**: 500 calls/day
- **Finnhub**: 60 calls/minute
- **Quandl**: 50 calls/minute
- **News API**: 100 requests/day
### Paid Tiers (For Production)
- **Alpha Vantage**: $49.99/month (75,000 calls/day)
- **Finnhub**: $9.99/month (1,000 calls/minute)
- **Polygon**: $29/month (5 calls/second)
## Rate Limiting Best Practices
1. **Implement caching** (already built-in)
2. **Batch API calls** when possible
3. **Use multiple providers** for redundancy
4. **Monitor usage** to avoid overages
5. **Implement fallbacks** to synthetic data
## Security Best Practices
1. **Never commit API keys** to version control
2. **Use environment variables** (.env file)
3. **Rotate keys regularly**
4. **Monitor API usage** for anomalies
5. **Implement rate limiting** in your code
## Expected Data Quality
### Real-time Data
- **Stock Prices**: 15-minute delay (free) to real-time (paid)
- **Market Data**: 1-5 minute delay
- **Economic Data**: Daily/weekly updates
- **News**: Real-time to 1-hour delay
### Data Accuracy
- **Stock Prices**: 99.9%+ accuracy
- **Economic Data**: Official government sources
- **News**: Multiple sources for verification
- **Sentiment**: AI-powered analysis
## Next Steps After Setup
1. **Test all API connections**
2. **Train models with historical data**
3. **Deploy to production**
4. **Monitor data quality**
5. **Optimize rate limiting**
6. **Scale based on usage**
## 🆘 Troubleshooting
### Common Issues
- **SSL Certificate Errors**: Set ENABLE_SSL_VERIFICATION=false
- **Rate Limit Exceeded**: Check API limits and implement caching
- **Invalid API Key**: Verify key format and permissions
- **Data Not Available**: Check API documentation for data availability
### Support Resources
- **Alpha Vantage**: https://www.alphavantage.co/support/
- **Finnhub**: https://finnhub.io/support
- **Quandl**: https://www.quandl.com/help/api
- **Polygon**: https://polygon.io/support
- **IEX Cloud**: https://iexcloud.io/support
---
**Ready to enable live market intelligence! **
"""
guide_file = Path('API_KEYS_SETUP_GUIDE.md')
with open(guide_file, 'w') as f:
f.write(guide_content)
print(f" Created comprehensive API setup guide")
print(f" File location: {guide_file.absolute()}")
return guide_file
def create_test_script():
"""Create a script to test API connections"""
test_script_content = """#!/usr/bin/env python3
\"\"\"
Test API Connections Script
Verify all configured API keys are working
\"\"\"
import os
import asyncio
import sys
from pathlib import Path
# Add core directory to path
sys.path.append(str(Path(__file__).parent / 'core'))
from advanced_market_data_service import AdvancedMarketDataService
async def test_api_connections():
\"\"\"Test all configured API connections\"\"\"
print(" Testing API Connections...")
print("=" * 50)
# Initialize service
service = AdvancedMarketDataService()
# Test each data source
tests = [
("VIX Data", service.get_real_time_vix),
("Bond Yields", service.get_real_time_bond_yields),
("Currency Data", service.get_real_time_currency_strength),
("Economic Indicators", service.get_economic_indicators),
("Sector Performance", service.get_sector_performance),
("Alternative Data", service.get_alternative_data)
]
results = {}
for test_name, test_func in tests:
print(f"\\n Testing {test_name}...")
try:
if asyncio.iscoroutinefunction(test_func):
result = await test_func()
else:
result = test_func()
if result:
print(f" {test_name}: SUCCESS")
print(f" Source: {getattr(result, 'source', 'N/A')}")
print(f" Confidence: {getattr(result, 'confidence', 'N/A')}")
results[test_name] = "SUCCESS"
else:
print(f" {test_name}: NO DATA")
results[test_name] = "NO DATA"
except Exception as e:
print(f" {test_name}: FAILED")
print(f" Error: {str(e)}")
results[test_name] = "FAILED"
# Summary
print("\\n" + "=" * 50)
print(" API Connection Test Summary")
print("=" * 50)
success_count = sum(1 for r in results.values() if r == "SUCCESS")
total_count = len(results)
for test_name, result in results.items():
status_emoji = "" if result == "SUCCESS" else "" if result == "NO DATA" else ""
print(f"{status_emoji} {test_name}: {result}")
print(f"\\n Overall: {success_count}/{total_count} APIs working")
if success_count == total_count:
print(" All APIs working! Ready for live market data!")
elif success_count > 0:
print(" Some APIs working. Check failed connections.")
else:
print(" No APIs working. Check API keys and configuration.")
# Close service
await service.close()
return results
if __name__ == "__main__":
asyncio.run(test_api_connections())
"""
test_file = Path('test_api_connections.py')
with open(test_file, 'w') as f:
f.write(test_script_content)
# Make executable
test_file.chmod(0o755)
print(f" Created API connection test script")
print(f" File location: {test_file.absolute()}")
return test_file
def main():
"""Main setup function"""
print(" API Keys Setup for Live Market Data")
print("=" * 50)
try:
# Create .env file
env_file = create_env_file()
# Create setup guide
guide_file = create_api_keys_guide()
# Create test script
test_file = create_test_script()
print("\\n Setup Complete!")
print("=" * 50)
print(" Next Steps:")
print("1. Edit .env file with your API keys")
print("2. Get API keys from the services listed in the guide")
print("3. Test connections: python3 test_api_connections.py")
print("4. Set ENVIRONMENT=production in .env")
print("5. Train models with real data")
print("\\n Documentation:")
print(f" API Setup Guide: {guide_file.name}")
print(f" Environment Config: {env_file.name}")
print(f" Test Script: {test_file.name}")
print("\\n Pro Tips:")
print(" • Start with free tiers to test")
print(" • Use multiple providers for redundancy")
print(" • Implement proper rate limiting")
print(" • Monitor API usage and costs")
return True
except Exception as e:
print(f" Setup failed: {e}")
return False
if __name__ == "__main__":
main()
