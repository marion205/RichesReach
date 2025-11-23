# Mobile App Navigation Testing Guide

**Date**: November 21, 2025  
**Features**: Paper Trading, Signal Updates, Research Reports

---

## 🚀 Quick Start

### Prerequisites
1. **Backend Server Running**: `http://localhost:8000`
2. **Mobile App Running**: Expo/React Native app started
3. **User Logged In**: Test user authenticated

### Start Mobile App
```bash
cd mobile
npm start
# Or
npx expo start
```

---

## 📱 Navigation Paths

### 1. Paper Trading Screen

#### Path A: From Invest Hub
1. Open app → Navigate to **"Invest"** tab
2. Look for **"Paper Trading"** option
3. Tap to navigate

#### Path B: Direct Navigation (Programmatic)
```typescript
navigation.navigate('paper-trading')
// Or
navigation.navigate('Invest', { screen: 'paper-trading' })
```

#### Path C: From Day Trading
1. Navigate to **"Day Trading"** screen
2. Look for link/button to **"Paper Trading"**
3. Tap to navigate

**Expected Result**: 
- Screen loads with paper trading interface
- Shows account summary (balance, P&L, statistics)
- Shows positions list (may be empty)
- Shows orders list (may be empty)
- Has button to place new order

---

### 2. Signal Updates Screen

#### Path A: From Stock Detail Screen (Primary)
1. Navigate to any stock (e.g., "AAPL")
2. On **StockDetailScreen**, look for **signal icon** in header actions
3. Tap the **activity/activity icon** (📊) in top right
4. Should navigate to `signal-updates` with `{ symbol: "AAPL", mode: "single" }`

#### Path B: Direct Navigation
```typescript
navigation.navigate('signal-updates', { 
  symbol: 'AAPL', 
  mode: 'single' // or 'watchlist' or 'portfolio'
})
```

#### Path C: From Portfolio
1. Navigate to **Portfolio** screen
2. Look for **"Signal Updates"** or **"Signals"** option
3. Tap to navigate (should show portfolio signals)

**Expected Result**:
- Screen loads with signal data
- Shows fusion score
- Shows recommendation (BUY/SELL/HOLD)
- Shows individual signal scores (spending, options, earnings, insider)
- Shows alerts (if any)
- Has tabs/options for: Single Stock, Watchlist, Portfolio

---

### 3. Research Report Screen

#### Path A: From Stock Detail Screen (Primary)
1. Navigate to any stock (e.g., "AAPL")
2. On **StockDetailScreen**, look for **file-text icon** in header actions
3. Tap the **file-text icon** (📄) in top right
4. Should navigate to `research-report` with `{ symbol: "AAPL" }`

#### Path B: Direct Navigation
```typescript
navigation.navigate('research-report', { symbol: 'AAPL' })
```

**Expected Result**:
- Screen loads with research report
- Shows executive summary
- Shows all sections:
  - Overview
  - Financials
  - Technical Analysis
  - Fundamental Analysis
  - AI Insights
  - Consumer Strength
  - Risk Assessment
  - Recommendation
- Shows key metrics
- Has option to share/export (if implemented)

---

## ✅ Testing Checklist

### Paper Trading Screen

#### Navigation
- [ ] Can navigate to Paper Trading from Invest hub
- [ ] Screen loads without errors
- [ ] Header shows "Paper Trading" title
- [ ] Back button works

#### Account Summary
- [ ] Initial balance displays ($100,000 default)
- [ ] Current balance displays
- [ ] Total value displays
- [ ] P&L (profit/loss) displays
- [ ] Win rate displays (if trades exist)
- [ ] Statistics section shows:
  - Total trades
  - Winning trades
  - Losing trades

#### Positions
- [ ] Positions list displays (may be empty)
- [ ] Each position shows:
  - Stock symbol
  - Shares
  - Average price
  - Current price
  - Unrealized P&L
- [ ] Can scroll through positions

#### Orders
- [ ] Orders list displays (may be empty)
- [ ] Each order shows:
  - Stock symbol
  - Side (BUY/SELL)
  - Order type (MARKET/LIMIT)
  - Quantity
  - Status
  - Filled price (if filled)

#### Place Order
- [ ] "Place Order" button exists
- [ ] Can open order form
- [ ] Can select stock symbol
- [ ] Can select side (BUY/SELL)
- [ ] Can enter quantity
- [ ] Can select order type (MARKET/LIMIT)
- [ ] Can submit order
- [ ] Order appears in orders list after submission
- [ ] Position updates after order fills

#### Trade History
- [ ] Trade history section exists
- [ ] Shows completed trades
- [ ] Each trade shows:
  - Stock symbol
  - Side
  - Quantity
  - Price
  - Realized P&L

---

### Signal Updates Screen

#### Navigation
- [ ] Can navigate from StockDetailScreen
- [ ] Screen loads without errors
- [ ] Header shows "Signal Updates" title
- [ ] Back button works
- [ ] Receives correct symbol parameter

#### Single Stock View
- [ ] Stock symbol displays
- [ ] Fusion score displays (0-100)
- [ ] Recommendation displays (BUY/SELL/HOLD)
- [ ] Consumer strength score displays
- [ ] Individual signal scores display:
  - Spending score
  - Options score
  - Earnings score
  - Insider score
- [ ] Signal trends display (increasing/decreasing/stable)
- [ ] Alerts list displays (if any)
- [ ] Each alert shows:
  - Type
  - Severity
  - Message
  - Timestamp

#### Watchlist View
- [ ] Can switch to watchlist view
- [ ] Shows all watchlist stocks with strong signals
- [ ] Each stock shows fusion score and recommendation
- [ ] Can tap stock to see details

#### Portfolio View
- [ ] Can switch to portfolio view
- [ ] Shows portfolio signals summary:
  - Strong buy count
  - Strong sell count
  - Overall sentiment
  - Total positions
- [ ] Shows signals for each position

#### Data Loading
- [ ] Loading indicator shows while fetching
- [ ] Error message shows if fetch fails
- [ ] Pull-to-refresh works
- [ ] Data updates correctly

---

### Research Report Screen

#### Navigation
- [ ] Can navigate from StockDetailScreen
- [ ] Screen loads without errors
- [ ] Header shows "Research Report" title
- [ ] Back button works
- [ ] Receives correct symbol parameter

#### Report Sections
- [ ] Executive summary displays
- [ ] Overview section displays:
  - Company name
  - Symbol
  - Sector
  - Current price
  - Market cap
- [ ] Financials section displays:
  - P/E ratio
  - Dividend yield
  - Debt ratio
  - Volatility
- [ ] Technical analysis section displays
- [ ] Fundamental analysis section displays
- [ ] AI insights section displays:
  - Consumer strength score
  - Component scores
  - AI recommendation (if available)
- [ ] Consumer strength section displays:
  - Overall score
  - Component breakdown
  - Historical trend
  - Sector score
- [ ] Risk assessment section displays:
  - Overall risk level
  - Volatility
  - Recommendations
- [ ] Recommendation section displays:
  - Action (BUY/SELL/HOLD)
  - Confidence
  - Target price (if available)
  - Reasoning
  - Time horizon

#### Key Metrics
- [ ] Key metrics card displays:
  - Price
  - Market cap
  - P/E ratio
  - Consumer strength
  - Volatility
  - Sector

#### Report Type
- [ ] Can select report type (if implemented):
  - Quick
  - Comprehensive
  - Deep dive

#### Data Loading
- [ ] Loading indicator shows while generating report
- [ ] Error message shows if generation fails
- [ ] Report displays correctly after loading

---

## 🐛 Common Issues & Solutions

### Issue: Screen doesn't navigate
**Solution**: 
- Check navigation route name matches exactly
- Verify screen is registered in AppNavigator
- Check if nested navigation is needed (Invest stack)

### Issue: Screen loads but shows no data
**Solution**:
- Check backend server is running
- Check GraphQL queries are working
- Verify user is authenticated
- Check network requests in React Native debugger

### Issue: Parameter not received
**Solution**:
- Verify parameter is passed correctly: `{ symbol: "AAPL" }`
- Check route params in screen: `route.params.symbol`
- Verify navigation call includes params

### Issue: GraphQL errors
**Solution**:
- Check server logs for errors
- Verify GraphQL endpoint is accessible
- Check authentication token is valid
- Verify query syntax is correct

---

## 📊 Test Results Template

### Paper Trading
- **Navigation**: ✅ / ❌
- **Account Summary**: ✅ / ❌
- **Positions**: ✅ / ❌
- **Orders**: ✅ / ❌
- **Place Order**: ✅ / ❌
- **Trade History**: ✅ / ❌
- **Notes**: 

### Signal Updates
- **Navigation**: ✅ / ❌
- **Single Stock View**: ✅ / ❌
- **Watchlist View**: ✅ / ❌
- **Portfolio View**: ✅ / ❌
- **Data Loading**: ✅ / ❌
- **Notes**: 

### Research Report
- **Navigation**: ✅ / ❌
- **Report Sections**: ✅ / ❌
- **Key Metrics**: ✅ / ❌
- **Data Loading**: ✅ / ❌
- **Notes**: 

---

## 🎯 Quick Test Commands

### Test Navigation Programmatically

In React Native Debugger or console:

```javascript
// Navigate to Paper Trading
navigation.navigate('paper-trading')

// Navigate to Signal Updates
navigation.navigate('signal-updates', { symbol: 'AAPL', mode: 'single' })

// Navigate to Research Report
navigation.navigate('research-report', { symbol: 'AAPL' })
```

### Test from Stock Detail

1. Navigate to any stock (e.g., "AAPL")
2. Tap the **file-text icon** → Should go to Research Report
3. Go back, tap the **activity icon** → Should go to Signal Updates

---

## 📝 Expected Behavior

### Paper Trading
- **First Time**: Shows $100,000 starting balance, no positions, no orders
- **After Trade**: Shows updated balance, new position, order in history
- **P&L**: Updates in real-time as prices change

### Signal Updates
- **Single Stock**: Shows signals for that specific stock
- **Watchlist**: Shows stocks with fusion score > threshold
- **Portfolio**: Shows signals for all portfolio positions

### Research Report
- **Loading**: Shows loading indicator while generating
- **Content**: Comprehensive report with all sections
- **Data**: All metrics and scores populated

---

## ✅ Success Criteria

All features are working if:
1. ✅ Screens navigate correctly
2. ✅ Data loads and displays
3. ✅ No crashes or errors
4. ✅ UI is responsive
5. ✅ Back navigation works
6. ✅ Parameters are received correctly

---

**Ready to test!** 🚀

Start the mobile app and follow the navigation paths above.
