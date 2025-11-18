# TradingScreen Refactor - Testing Checklist ✅

## Pre-Test Setup

### ✅ Services Running
- [x] Backend server running (main_server.py)
- [x] Expo/Metro bundler running
- [ ] App loaded in simulator/device

## Test Scenarios

### 1. Navigation & Initial Load
- [ ] Navigate to Trading screen from Home
- [ ] Verify header displays correctly (back button, title, action buttons)
- [ ] Verify tabs display (Overview / Orders)
- [ ] Check for any console errors on initial load

### 2. Account Summary Card
- [ ] Verify skeleton loader appears during initial load
- [ ] Verify account data displays correctly (portfolio value, equity, buying power, cash)
- [ ] Verify Alpaca account status displays (if connected)
- [ ] Verify KYC prompt appears if account not approved
- [ ] Check that refresh button works

### 3. Positions List
- [ ] Verify skeleton loaders appear (3 rows) during loading
- [ ] Verify positions display correctly with:
  - Symbol
  - Quantity and current price
  - P&L (unrealized gain/loss)
  - Sparkline chart
  - Market value
- [ ] Verify empty state displays when no positions
- [ ] Test pull-to-refresh functionality

### 4. Orders List (Orders Tab)
- [ ] Switch to Orders tab
- [ ] Verify filter buttons work (All, Open, Filled, Cancelled)
- [ ] Verify orders are grouped by time (Today, This Week, Earlier)
- [ ] Verify order details display:
  - Symbol, side (Buy/Sell), order type
  - Quantity, price, stop price
  - Status with correct color/icon
  - Created timestamp
- [ ] Test cancel order button (for pending orders)
- [ ] Verify skeleton loaders during loading

### 5. Place Order Modal
- [ ] Click "Order" button in header
- [ ] Verify modal opens smoothly
- [ ] Test order type selection (Market, Limit, Stop Loss)
- [ ] Test side selection (Buy, Sell)
- [ ] Enter symbol (e.g., AAPL)
- [ ] Verify quote data loads and displays (bid/ask)
- [ ] Verify order total estimate calculates correctly:
  - For market orders: shows current ask/bid
  - For limit orders: shows limit price or estimate
  - For stop orders: shows stop price or estimate
- [ ] Enter quantity
- [ ] Verify validation works (empty symbol, invalid quantity)
- [ ] Test SBLOC alternative prompt (for sell orders with gains)
- [ ] Test form reset when modal closes

### 6. Alpaca Connect Flow
- [ ] Try to place order without Alpaca account
- [ ] Verify Alpaca Connect modal appears
- [ ] Test "I have an account" flow
- [ ] Test "I need to create one" flow
- [ ] Verify modal closes correctly

### 7. Performance Checks
- [ ] Check React DevTools Profiler for re-renders:
  - AccountSummaryCard should not re-render unnecessarily
  - PositionsList should not re-render when positions unchanged
  - OrdersList should not re-render when orders unchanged
- [ ] Verify smooth scrolling (no jank)
- [ ] Check initial load time
- [ ] Verify skeleton loaders appear quickly

### 8. Error Handling
- [ ] Test with network disconnected (should show error gracefully)
- [ ] Test with invalid API responses
- [ ] Verify error messages are user-friendly

### 9. Styling & UI
- [ ] Verify all cards have proper shadows and borders
- [ ] Verify colors are consistent
- [ ] Verify spacing is correct
- [ ] Verify text is readable
- [ ] Check on different screen sizes (if possible)

## Expected Behavior

### Skeleton Loaders
- Should appear immediately when loading
- Should have subtle shimmer animation
- Should match the layout of actual content

### Memoization
- Components should not re-render when props haven't changed
- Use React DevTools Profiler to verify

### Performance
- Initial load should be fast (< 2 seconds)
- Scrolling should be smooth (60fps)
- No noticeable lag when switching tabs

## Known Issues to Watch For

1. **Quote Loading**: May take a moment on first symbol entry
2. **Modal Timing**: Small delay when closing order modal before showing connect modal (intentional)
3. **Mock Data**: Falls back to mock data after 5-second timeout if API unavailable

## Success Criteria

✅ All components render correctly
✅ No console errors
✅ Skeleton loaders appear during loading
✅ Smooth performance (no jank)
✅ All interactions work as expected
✅ Memoization prevents unnecessary re-renders

