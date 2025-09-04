# 🔑 API Keys Setup Guide - RichesReach

## Your Existing API Keys

Great! You already have:
- ✅ **News API** - For financial news feed
- ✅ **Alpha Vantage** - For stock market data
- ✅ **Finnhub** - For real-time stock prices

## 🚀 Quick Setup Steps

### 1. Create Environment File
Create a file called `.env` in your `backend` directory:

```bash
cd backend
cp env.example .env
```

### 2. Add Your API Keys
Edit the `.env` file and replace the placeholder values:

```bash
# Your actual API keys
NEWS_API_KEY=your-actual-news-api-key
ALPHA_VANTAGE_API_KEY=your-actual-alpha-vantage-key
FINNHUB_API_KEY=your-actual-finnhub-key

# Optional: OpenAI for AI features
OPENAI_API_KEY=your-openai-key-if-you-have-one
```

### 3. Test Your APIs
Let's verify your API keys work:

```bash
# Test News API
curl "https://newsapi.org/v2/everything?q=stocks&apiKey=YOUR_NEWS_API_KEY"

# Test Alpha Vantage
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_ALPHA_VANTAGE_KEY"

# Test Finnhub
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_FINNHUB_KEY"
```

## 📊 What Each API Does

### News API
- **Purpose**: Financial news articles
- **Features**: Real-time news, categories (markets, crypto, economy)
- **Usage**: News feed in your app

### Alpha Vantage
- **Purpose**: Historical stock data, technical indicators
- **Features**: 5+ years of data, 50+ technical indicators
- **Usage**: Stock analysis, portfolio calculations

### Finnhub
- **Purpose**: Real-time stock prices
- **Features**: Live quotes, market data
- **Usage**: Current stock prices, price alerts

## 🔧 Backend Configuration

Your Django backend is already configured to use these APIs. Just add the keys to your `.env` file and restart the server:

```bash
cd backend
source ../.venv/bin/activate
python manage.py runserver
```

## 📱 Mobile App Configuration

The mobile app will automatically use the backend APIs once configured. No changes needed to the mobile app code.

## 🚀 Ready for Deployment

With your API keys configured, you're ready to deploy! Your app will have:

- ✅ Real-time stock prices
- ✅ Financial news feed
- ✅ Historical data analysis
- ✅ Portfolio tracking
- ✅ AI recommendations (if you add OpenAI)

## 💰 API Usage Costs

- **News API**: 1,000 requests/day free
- **Alpha Vantage**: 5 requests/minute, 500/day free
- **Finnhub**: 60 requests/minute free

For production, you might want to upgrade to paid plans for higher limits.

## 🔒 Security Notes

- Never commit your `.env` file to Git
- Use different keys for development and production
- Monitor your API usage to avoid overages

---

**Next Step**: Add your API keys to the `.env` file and test the app!
