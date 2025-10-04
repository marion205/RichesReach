# RichesReach Development Quick Start

## 🚀 Get Started in 5 Minutes

### 1. Switch to Development Branch
```bash
git checkout development
```

### 2. Start the Mock Backend Server
```bash
cd backend/backend
source ../.venv/bin/activate
python3 working_test_server.py
```

The server will start on `http://192.168.1.236:8000` with:
- ✅ Complete GraphQL API mock
- ✅ 5 mock stocks with ML scoring
- ✅ AI recommendations with detailed analysis
- ✅ Trading account, positions, and orders
- ✅ Research hub with technical analysis

### 3. Start the Mobile App
```bash
cd mobile
npx expo start
```

### 4. Test the App
- Open Expo Go on your phone
- Scan the QR code
- Navigate to different screens:
  - **Browse All**: Shows 5 mock stocks
  - **Beginner**: AI-recommended stocks
  - **Research**: Detailed stock analysis
  - **Trading**: Account and positions
  - **AI Portfolio**: Portfolio metrics

## 🎯 What You Get

### Mock Data Available
- **Stocks**: AAPL, MSFT, GOOGL, TSLA, AMZN
- **AI Scores**: Beginner-friendly scoring with detailed breakdowns
- **Trading Data**: Mock account with $50,000 buying power
- **Research**: Technical analysis, sentiment, market regime
- **Portfolio**: Mock portfolio with performance metrics

### Features Working
- ✅ Stock browsing and search
- ✅ AI recommendations
- ✅ Trading interface
- ✅ Research analysis
- ✅ Portfolio management
- ✅ Error handling with graceful fallbacks

## 🛠️ Development Features

### Mock GraphQL Endpoints
- `stocks` - Browse all stocks
- `beginnerFriendlyStocks` - AI-recommended stocks
- `researchHub` - Detailed stock research
- `stockChartData` - Price charts and indicators
- `tradingAccount` - Account information
- `tradingPositions` - Current holdings
- `tradingOrders` - Order history

### Error Handling
- Network errors gracefully handled
- Mock data fallbacks for all screens
- No more empty screens or crashes
- Perfect for screenshots and demos

## 📱 Perfect for
- **Screenshots**: All screens show rich data
- **Demos**: Professional-looking app
- **Testing**: Comprehensive mock data
- **Development**: No backend dependencies

## 🔧 Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9

# Restart server
python3 working_test_server.py
```

### App Can't Connect
- Ensure phone and computer are on same WiFi
- Check server is running on `192.168.1.236:8000`
- Verify health endpoint: `http://192.168.1.236:8000/health`

### No Data Showing
- Check server logs for errors
- Verify GraphQL queries are working
- Ensure mock data is being returned

## 🎨 Customization

### Add More Mock Stocks
Edit `backend/backend/working_test_server.py` and add to the `all_stocks` array.

### Modify AI Scores
Update the `beginnerScoreBreakdown` in the mock data.

### Change API Endpoints
Update `mobile/src/config/api.ts` for different endpoints.

## 📚 Next Steps

1. **Take Screenshots**: All screens now show professional data
2. **Test Features**: Navigate through all app sections
3. **Customize Data**: Modify mock data as needed
4. **Deploy to Production**: Switch to `main` branch when ready

## 🆘 Need Help?

- Check the server logs for detailed error messages
- Verify network connectivity between phone and computer
- Ensure all dependencies are installed
- Review the mock data structure in the server file

Happy developing! 🚀
