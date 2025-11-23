# Quick Test Start Guide

## 🚀 Start Server & Run Tests

### Step 1: Start the Backend Server

```bash
cd deployment_package/backend
source venv/bin/activate
python manage.py runserver
```

**Keep this terminal open** - the server needs to keep running.

### Step 2: In a New Terminal, Run Tests

```bash
cd /Users/marioncollins/RichesReach
python3 test_competitive_moat_features.py
```

---

## 📋 What Gets Tested

The test script automatically tests:

1. **Paper Trading**:
   - ✅ `paperAccountSummary` query
   - ✅ `paperPositions` query
   - ✅ `paperOrders` query
   - ✅ `paperTradeHistory` query
   - ✅ `placePaperOrder` mutation

2. **Signal Fusion**:
   - ✅ `signalUpdates` query
   - ✅ `watchlistSignals` query
   - ✅ `portfolioSignals` query

3. **Research Reports**:
   - ✅ `generateResearchReport` mutation

4. **Consumer Strength**:
   - ✅ `consumerStrength` query
   - ✅ `consumerStrengthHistory` query
   - ✅ `sectorComparison` query

---

## 📱 Mobile App Testing

After backend tests pass, test the mobile app:

1. **Start Mobile App**:
   ```bash
   cd mobile
   npm start
   ```

2. **Test Navigation**:
   - Navigate to Paper Trading screen
   - Navigate to Signal Updates screen
   - Navigate to Research Report screen

3. **Test Features**:
   - Place a paper trade
   - View signal updates for a stock
   - Generate a research report

---

## ✅ Expected Results

- **✅ Pass**: Feature works correctly
- **⚠️ Warning**: Feature works but returns empty data (normal if no data exists)
- **❌ Fail**: Feature has errors (needs fixing)

**Note**: Warnings are OK - they just mean there's no data yet (e.g., no paper trades, empty watchlist).

---

## 🐛 If Tests Fail

1. **Check server is running**: `curl http://localhost:8000/health`
2. **Check server logs** for errors
3. **Verify database** has test data (stocks, users)
4. **Check authentication** - test user may need to be created

---

**Ready to test!** 🚀

