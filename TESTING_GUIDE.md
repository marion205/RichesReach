# Testing Guide: Competitive Moat Features

**Date**: November 21, 2025  
**Branch**: `feature/competitive-moat-enhancements`

---

## 🚀 Quick Start

### 1. Start the Server

```bash
cd deployment_package/backend
source venv/bin/activate
python manage.py runserver
```

The server should start on `http://localhost:8000`

### 2. Run Automated Tests

```bash
# From project root
python3 test_competitive_moat_features.py
```

This will test:
- ✅ Paper Trading GraphQL endpoints
- ✅ Signal Fusion queries
- ✅ Research Report generation
- ✅ Consumer Strength queries

---

## 📋 Manual Testing

### Prerequisites

1. **Server Running**: `http://localhost:8000`
2. **Authentication**: You'll need a JWT token (test user should exist)
3. **Test Stock**: Ensure "AAPL" exists in database (or use another symbol)

### Get Authentication Token

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { tokenAuth(username: \"test@richesreach.com\", password: \"testpass123\") { token } }"
  }'
```

Save the token from the response.

---

## 📊 Paper Trading Tests

### 1. Get Paper Account Summary

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { paperAccountSummary { account { id initialBalance currentBalance totalValue totalPnl winRate } positions { id stockSymbol shares averagePrice } statistics { totalTrades winningTrades winRate } } }"
  }'
```

**Expected**: Account summary with balance, positions, and statistics

### 2. Get Paper Positions

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { paperPositions { id stockSymbol shares averagePrice currentPrice unrealizedPnl } }"
  }'
```

**Expected**: List of positions (may be empty if no trades yet)

### 3. Place Paper Order

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "mutation { placePaperOrder(symbol: \"AAPL\", side: \"BUY\", quantity: 10, orderType: \"MARKET\") { success order { id stockSymbol side quantity status filledPrice } error } }"
  }'
```

**Expected**: Order placed successfully (or error if stock not in DB)

### 4. Get Paper Orders

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { paperOrders { id stockSymbol side orderType quantity status filledPrice createdAt } }"
  }'
```

**Expected**: List of orders

---

## 🔔 Signal Fusion Tests

### 1. Get Signal Updates for Stock

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { signalUpdates(symbol: \"AAPL\", lookbackHours: 24) { symbol fusionScore recommendation consumerStrength alerts { type severity message } } }"
  }'
```

**Expected**: Signal updates with fusion score, recommendation, and alerts

### 2. Get Watchlist Signals

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { watchlistSignals(threshold: 70.0) { symbol fusionScore recommendation alerts { type severity message } } }"
  }'
```

**Expected**: List of stocks with strong signals (may be empty if no watchlist)

### 3. Get Portfolio Signals

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { portfolioSignals(threshold: 60.0) { portfolioSignals strongBuyCount strongSellCount overallSentiment totalPositions } }"
  }'
```

**Expected**: Portfolio signal summary with sentiment and counts

---

## 📄 Research Report Tests

### Generate Research Report

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "mutation { generateResearchReport(symbol: \"AAPL\", reportType: \"comprehensive\") { success report { symbol companyName reportType executiveSummary sections { overview financials recommendation } keyMetrics } error } }"
  }'
```

**Expected**: Comprehensive research report with all sections

---

## 💪 Consumer Strength Tests

### 1. Get Consumer Strength

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { consumerStrength(symbol: \"AAPL\") { overallScore spendingScore optionsScore earningsScore insiderScore spendingGrowth sectorScore components { spending { score growth } options { score } } } }"
  }'
```

**Expected**: Consumer strength scores with component breakdown

### 2. Get Consumer Strength History

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { consumerStrengthHistory(symbol: \"AAPL\", days: 30) { overallScore spendingScore optionsScore earningsScore } }"
  }'
```

**Expected**: Historical scores (may return only current score if history not implemented)

### 3. Get Sector Comparison

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { sectorComparison(symbol: \"AAPL\") { stockScore sectorAverage sectorRank percentile sectorName totalInSector } }"
  }'
```

**Expected**: Sector comparison with rank and percentile

---

## 📱 Mobile App Testing

### Navigation Tests

1. **Paper Trading Screen**:
   - Navigate: `Invest` → `Paper Trading`
   - Should show account summary, positions, orders
   - Test placing an order

2. **Signal Updates Screen**:
   - Navigate: From `StockDetailScreen` → `Signal Updates`
   - Should show fusion score, recommendation, alerts
   - Test portfolio and watchlist views

3. **Research Report Screen**:
   - Navigate: From `StockDetailScreen` → `Research Report`
   - Should display full report with all sections

### Test Checklist

- [ ] Paper Trading screen loads
- [ ] Can view account summary
- [ ] Can view positions (if any)
- [ ] Can place a paper order
- [ ] Signal Updates screen loads
- [ ] Signal data displays correctly
- [ ] Research Report screen loads
- [ ] Report sections display correctly
- [ ] Navigation works from StockDetailScreen

---

## 🐛 Troubleshooting

### Server Not Running
```bash
# Check if server is running
curl http://localhost:8000/health

# Start server
cd deployment_package/backend
source venv/bin/activate
python manage.py runserver
```

### Authentication Fails
- Check if test user exists
- Verify password is correct
- Check server logs for errors

### Stock Not Found
- Ensure stock exists in database
- Try with a different symbol (e.g., "MSFT", "GOOGL")
- Check database connection

### Empty Results
- Some queries may return empty arrays if no data exists (this is normal)
- Paper trading: No positions/orders if no trades made yet
- Watchlist signals: Empty if watchlist is empty
- Portfolio signals: Empty if no portfolio positions

### GraphQL Errors
- Check server logs for detailed error messages
- Verify query syntax is correct
- Ensure all required fields are provided

---

## ✅ Success Criteria

### Paper Trading
- ✅ Account summary query works
- ✅ Positions query works (may be empty)
- ✅ Orders query works (may be empty)
- ✅ Place order mutation works (or returns helpful error)
- ✅ Trade history query works

### Signal Fusion
- ✅ Signal updates query returns data
- ✅ Watchlist signals query works (may be empty)
- ✅ Portfolio signals query works (may be empty)

### Research Reports
- ✅ Generate report mutation works
- ✅ Report contains all sections
- ✅ Report data is valid

### Consumer Strength
- ✅ Consumer strength query returns scores
- ✅ History query works (may return only current)
- ✅ Sector comparison query works

---

## 📊 Expected Test Results

When running `test_competitive_moat_features.py`:

- **Passed**: ✅ All queries/mutations execute successfully
- **Warnings**: ⚠️  Queries work but return empty data (normal if no data exists)
- **Failed**: ❌ Queries fail with errors (needs investigation)

**Note**: Warnings are expected for:
- Empty positions/orders (if no trades made)
- Empty watchlist signals (if watchlist is empty)
- Empty portfolio signals (if no portfolio)

---

## 🎯 Next Steps After Testing

1. **If all tests pass**: Ready to commit!
2. **If tests fail**: Review errors and fix issues
3. **If warnings**: Normal if no data exists, can proceed

---

**Status**: Ready for testing! 🚀

