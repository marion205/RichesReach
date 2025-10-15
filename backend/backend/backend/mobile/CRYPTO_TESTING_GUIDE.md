# 🚀 Crypto UI Testing Guide

## **Quick Start**

### **1. Start All Services**
```bash
# Terminal 1: Crypto API Server
python3 backend/mock_crypto_server.py &

# Terminal 2: Repay API Server  
python3 backend/mock_repay_server.py &

# Terminal 3: Run Tests
./test-crypto-ui.sh
```

### **2. Test in React Native App**

#### **Update Apollo Client Configuration**
```typescript
// In your Apollo Client setup
const client = new ApolloClient({
  uri: 'http://localhost:8127/graphql', // Crypto API
  cache: new InMemoryCache(),
});

// For repay operations
const repayClient = new ApolloClient({
  uri: 'http://localhost:8128/graphql', // Repay API
  cache: new InMemoryCache(),
});
```

#### **Update API Base URLs**
```typescript
// In your API configuration
export const API_CONFIG = {
  CRYPTO_BASE_URL: 'http://localhost:8127',
  REPAY_BASE_URL: 'http://localhost:8128',
};
```

## **🧪 Testing Scenarios**

### **1. Portfolio Testing**
- **Total Value**: $104,843.54
- **PnL**: -1.56% (bearish market)
- **Holdings**: 3 assets (BTC, ETH, SOL)
- **Features to Test**:
  - Balance masking toggle
  - LTV state display
  - Holding row taps
  - Refresh functionality

### **2. Trading Testing**
- **Available Coins**: BTC, ETH, SOL, ADA, DOT
- **Price Data**: Real-time mock prices
- **Features to Test**:
  - Buy/Sell toggle
  - Order types (Market, Limit)
  - Time in Force options
  - Balance validation
  - Fee calculations

### **3. SBLOC Testing**
- **Active Loans**: 2 loans ($5K BTC, $2.5K ETH)
- **Interest Rates**: 5-6% APR
- **Features to Test**:
  - LTV risk meter
  - Quick LTV targets
  - Add collateral flow
  - Repay loan flow

### **4. ML Signals Testing**
- **Current Signal**: BTC BIG_DOWN_DAY (45.7%)
- **Confidence**: MEDIUM
- **Sentiment**: Bearish
- **Features to Test**:
  - Symbol selection
  - Generate prediction
  - Auto-refresh (30s)
  - Error handling

### **5. Collateral Health Testing**
- **Risk Levels**: SAFE, CAUTION, AT_RISK, DANGER
- **Per-Asset Breakdown**: Available
- **Features to Test**:
  - Asset row taps
  - LTV calculations
  - Risk indicators
  - Modal navigation

## **📱 Component Testing Checklist**

### **CryptoPortfolioCard**
- [ ] Displays total value correctly
- [ ] Shows PnL with proper colors
- [ ] Toggle balance masking works
- [ ] Holdings list scrolls properly
- [ ] Tap holding rows opens details
- [ ] Refresh button works
- [ ] LTV state chip displays

### **CryptoTradingCard**
- [ ] Buy/Sell toggle works
- [ ] Symbol selection updates price
- [ ] Order type selection works
- [ ] Time in Force options work
- [ ] Amount input validation
- [ ] Fee calculation display
- [ ] Max button works
- [ ] Preset percentages work
- [ ] Confirmation modal works

### **CryptoSBLOCCard**
- [ ] LTV risk meter displays
- [ ] Quick LTV targets work
- [ ] Available balance shows
- [ ] Top up button works
- [ ] Start loan button works
- [ ] Loan list displays correctly

### **CryptoMLSignalsCard**
- [ ] Symbol selection works
- [ ] Generate button works
- [ ] Signal data displays
- [ ] Auto-refresh works (30s)
- [ ] Error state shows retry
- [ ] Loading skeleton shows

### **CollateralHealthCard**
- [ ] Overall LTV displays
- [ ] Per-asset rows show
- [ ] Asset row taps work
- [ ] Risk colors correct
- [ ] Totals calculation correct

### **LoanManagementModal**
- [ ] Modal opens/closes
- [ ] Loan list filters by symbol
- [ ] Repay flow works
- [ ] Add collateral works
- [ ] Loading states work

## **🔧 Debugging Tips**

### **Common Issues**
1. **CORS Errors**: Make sure both servers are running
2. **Network Errors**: Check localhost URLs in config
3. **GraphQL Errors**: Verify query syntax
4. **State Issues**: Check React hooks dependencies

### **Console Logging**
```typescript
// Enable debug logging
console.log('Crypto API Response:', data);
console.log('Portfolio Data:', portfolio);
console.log('ML Signal:', signal);
```

### **Performance Monitoring**
```typescript
// Monitor API response times
const startTime = Date.now();
// ... API call
const endTime = Date.now();
console.log(`API Response Time: ${endTime - startTime}ms`);
```

## **📊 Test Data Reference**

### **Portfolio Data**
```json
{
  "total_value_usd": 104843.54,
  "total_pnl": -1634.50,
  "total_pnl_percentage": -1.56,
  "holdings": [
    {
      "symbol": "BTC",
      "quantity": 1.5,
      "current_value": 70472.91,
      "unrealized_pnl_percentage": 12.5
    },
    {
      "symbol": "ETH", 
      "quantity": 5.0,
      "current_value": 17001.25,
      "unrealized_pnl_percentage": -8.3
    },
    {
      "symbol": "SOL",
      "quantity": 100.0,
      "current_value": 15075.00,
      "unrealized_pnl_percentage": -5.2
    }
  ]
}
```

### **ML Signal Data**
```json
{
  "symbol": "BTC",
  "predictionType": "BIG_DOWN_DAY",
  "probability": 0.457,
  "confidenceLevel": "MEDIUM",
  "sentiment": "Bearish",
  "sentimentDescription": "Weakness at key levels and declining momentum.",
  "featuresUsed": {
    "rsi_14": 35.2,
    "macd_signal": -0.15,
    "volume_z": 0.8
  }
}
```

### **SBLOC Loans Data**
```json
{
  "loans": [
    {
      "id": "loan_1",
      "status": "ACTIVE",
      "loanAmount": 5000.0,
      "interestRate": 0.05,
      "cryptocurrency": {"symbol": "BTC"}
    },
    {
      "id": "loan_2", 
      "status": "ACTIVE",
      "loanAmount": 2500.0,
      "interestRate": 0.06,
      "cryptocurrency": {"symbol": "ETH"}
    }
  ]
}
```

## **🚀 Ready to Test!**

Your crypto UI is now fully set up for testing with:
- ✅ **2 Mock API servers** running
- ✅ **Realistic test data** loaded
- ✅ **All endpoints** verified
- ✅ **GraphQL mutations** working
- ✅ **Performance monitoring** enabled

**Start testing your React Native app now!** 🎉
