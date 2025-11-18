# Quick Test Guide - Refactored TradingScreen 🚀

## ✅ Services Status
- ✅ Backend running (main_server.py)
- ✅ Metro bundler running (port 8081)
- ✅ Ready to test!

## 🎯 Quick Test Steps

### 1. Open the App
- If using **iOS Simulator**: Press `i` in the Expo terminal
- If using **Expo Go**: Scan the QR code
- If using **Dev Client**: App should already be open

### 2. Navigate to Trading Screen
- From Home screen, navigate to Trading
- Or use navigation: `navigateTo('trading')`

### 3. What to Look For

#### ✅ Initial Load
- **Skeleton loaders** should appear immediately (not spinners!)
- Account summary shows animated skeleton
- Positions show 3 skeleton rows
- Smooth, professional loading experience

#### ✅ Account Summary
- Portfolio value, equity, buying power, cash display
- Grid layout looks clean
- Alpaca account status (if applicable)
- Refresh button works

#### ✅ Positions List
- Positions display with:
  - Symbol and quantity
  - Sparkline chart
  - P&L percentage (green/red)
  - Market value
- Empty state if no positions
- Pull-to-refresh works

#### ✅ Orders Tab
- Switch to "Orders" tab
- Filter buttons work (All, Open, Filled, Cancelled)
- Orders grouped by time
- Cancel button for pending orders

#### ✅ Place Order
- Click "Order" button in header
- Modal opens smoothly
- Try different order types (Market, Limit, Stop)
- Enter symbol (e.g., AAPL)
- **Watch for**: Quote loads, order total calculates
- SBLOC prompt for sell orders with gains

#### ✅ Alpaca Connect
- Try placing order without account
- Connect modal should appear
- Test both "Have account" and "Need account" flows

## 🔍 Performance Checks

### React DevTools Profiler (Optional)
1. Open React DevTools
2. Start Profiler
3. Interact with screen (switch tabs, refresh)
4. Stop Profiler
5. **Check**: Components should NOT re-render unnecessarily
   - AccountSummaryCard: Only re-renders when account data changes
   - PositionsList: Only re-renders when positions change
   - OrdersList: Only re-renders when orders/filter changes

### Console Logs
Watch for:
- ✅ No errors
- ✅ GraphQL queries executing
- ✅ Data loading successfully
- ⚠️ Any warnings (should be minimal)

## 🐛 Common Issues & Fixes

### Skeleton Loaders Not Showing
- **Check**: Are you seeing spinners instead?
- **Fix**: Clear cache and restart: `npx expo start --clear`

### Components Re-rendering Too Much
- **Check**: Use React DevTools Profiler
- **Fix**: Verify memo comparison functions are working

### Modal Not Opening
- **Check**: Console for errors
- **Fix**: Verify OrderModal component is imported correctly

### Quote Not Loading
- **Check**: Network tab in DevTools
- **Fix**: Verify backend is running and GraphQL endpoint works

## 📊 Success Indicators

✅ **Skeleton loaders** appear (not spinners)
✅ **Smooth scrolling** (no jank)
✅ **Fast initial load** (< 2 seconds)
✅ **No console errors**
✅ **All interactions work**
✅ **Memoization working** (check Profiler)

## 🎉 Expected Experience

The refactored screen should feel:
- **Faster** - Skeleton loaders provide instant feedback
- **Smoother** - No unnecessary re-renders
- **Cleaner** - Better organized code, easier to maintain
- **Professional** - Polished loading states

---

**Ready to test!** Open the app and navigate to Trading screen. 🚀

