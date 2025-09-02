# 🔑 API Keys Setup Guide for Live Market Data

## 🚀 Quick Start

1. **Copy the .env file** to your project root
2. **Get API keys** from the services below
3. **Replace placeholder values** in .env file
4. **Set ENVIRONMENT=production** to enable live data
5. **Run the training script** to build models with real data

## 📊 Financial Data APIs

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

## 📰 Alternative Data APIs

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

## 🔧 Configuration Steps

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

## 📈 Data Sources by Feature

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

## 💰 Cost Considerations

### Free Tiers (Recommended for Start)
- **Alpha Vantage**: 500 calls/day
- **Finnhub**: 60 calls/minute
- **Quandl**: 50 calls/minute
- **News API**: 100 requests/day

### Paid Tiers (For Production)
- **Alpha Vantage**: $49.99/month (75,000 calls/day)
- **Finnhub**: $9.99/month (1,000 calls/minute)
- **Polygon**: $29/month (5 calls/second)

## 🚨 Rate Limiting Best Practices

1. **Implement caching** (already built-in)
2. **Batch API calls** when possible
3. **Use multiple providers** for redundancy
4. **Monitor usage** to avoid overages
5. **Implement fallbacks** to synthetic data

## 🔒 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** (.env file)
3. **Rotate keys regularly**
4. **Monitor API usage** for anomalies
5. **Implement rate limiting** in your code

## 📊 Expected Data Quality

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

## 🎯 Next Steps After Setup

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

**Ready to enable live market intelligence! 🚀**
