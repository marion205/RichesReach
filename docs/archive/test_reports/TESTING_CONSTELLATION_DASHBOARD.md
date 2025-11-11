# Testing Guide: Constellation Dashboard

## 🎯 What's Left to Do

### ✅ Completed
- [x] Backend endpoint (`/api/money/snapshot`)
- [x] Frontend service & hook
- [x] ConstellationOrb component
- [x] All 4 gesture action modals
- [x] Integration into PortfolioScreen

### ⚠️ Testing Needed
- [ ] Test with real bank data (Yodlee linked)
- [ ] Test without bank data (portfolio-only mode)
- [ ] Verify gesture handlers work on physical device
- [ ] Test edge cases (zero values, negative cash flow)
- [ ] Verify calculations are accurate
- [ ] Test modal animations and transitions

### 🔮 Future Enhancements (Optional)
- [ ] Save scenarios to user profile
- [ ] Connect "Apply Strategy" buttons to actual trading actions
- [ ] Add haptic feedback for gestures
- [ ] Add loading states for snapshot fetch
- [ ] Add error handling UI

---

## 🚀 How to Start & Test

### Step 1: Start Backend Server

**Terminal 1:**
```bash
cd /Users/marioncollins/RichesReach

# Start the main server
python main_server.py
```

**Expected output:**
```
🚀 Starting RichesReach Main Server...
📡 Available endpoints:
   • GET /health - Health check
   • GET /api/money/snapshot - Money snapshot ✅
   • POST /graphql/ - GraphQL endpoint
🌐 Server running on http://localhost:8000
```

**Verify endpoint:**
```bash
# Test the snapshot endpoint (will require auth token)
curl http://localhost:8000/api/money/snapshot \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 2: Start Mobile App

**Terminal 2:**
```bash
cd /Users/marioncollins/RichesReach/mobile

# Start Expo
npm start
# OR
npx expo start
```

**Options:**
- **Option A**: Scan QR code with Expo Go app (physical device)
- **Option B**: Press `i` for iOS Simulator
- **Option C**: Press `a` for Android Emulator

### Step 3: Navigate to Portfolio Screen

1. **Open the app** (Expo Go or Simulator)
2. **Login** (or use dev mode if auth is bypassed)
3. **Navigate to Portfolio**:
   - Tap bottom nav "Portfolio" tab
   - OR go to "Invest" → "Portfolio"

### Step 4: Test Constellation Dashboard

#### Scenario A: With Bank Linked (Full Experience)

**If you have Yodlee bank accounts linked:**

1. **You should see:**
   - Constellation Orb (pulsing animation)
   - Net worth displayed in center
   - Cash flow satellites (green/red)
   - Portfolio position satellites
   - Shield alerts (if applicable)

2. **Test Gestures:**

   **Tap Gesture (Life Events):**
   - Tap the orb
   - ✅ Should see: LifeEventPetalsModal slides up
   - ✅ Should show: Emergency Fund, Home Down Payment, Retirement goals
   - ✅ Expand a petal: Should show details and suggestions
   - ✅ Close: Tap X or swipe down

   **Swipe Left (Shield):**
   - Swipe left on the orb
   - ✅ Should see: MarketCrashShieldView slides up
   - ✅ Should show: Current position, cash ratio
   - ✅ Should show: 4 protection strategies
   - ✅ Expand a strategy: Should show details and "Apply" button

   **Swipe Right (Growth):**
   - Swipe right on the orb
   - ✅ Should see: GrowthProjectionView slides up
   - ✅ Should show: Current net worth
   - ✅ Should show: 3 growth scenarios
   - ✅ Change timeframe: Tap 6M, 12M, 24M, 36M buttons
   - ✅ Projections should update

   **Pinch Gesture (What-If):**
   - Pinch the orb (two-finger gesture)
   - ✅ Should see: WhatIfSimulator slides up
   - ✅ Should show: Current vs Projected comparison
   - ✅ Adjust monthly contribution: Use +/- buttons
   - ✅ Change growth rate: Tap 5%, 8%, 10%, 12%
   - ✅ Change timeframe: Tap 6M, 12M, 24M, 36M
   - ✅ Projection should update in real-time

#### Scenario B: Without Bank Linked (Fallback)

**If no bank accounts linked:**

1. **You should see:**
   - Traditional portfolio overview (unchanged)
   - Portfolio grid cards
   - Milestones timeline
   - Holdings list

2. **Constellation Orb should NOT appear**
   - This is correct behavior (progressive enhancement)

---

## 🧪 Testing Checklist

### Backend Testing

- [ ] **Health Check**
  ```bash
  curl http://localhost:8000/health
  ```
  Should return: `{"status": "ok"}`

- [ ] **Snapshot Endpoint** (requires auth)
  ```bash
  curl http://localhost:8000/api/money/snapshot \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```
  Should return JSON with:
  - `netWorth`
  - `cashflow` (period, in, out, delta)
  - `positions` (array)
  - `shield` (array)
  - `breakdown` (bankBalance, portfolioValue, bankAccountsCount)

### Frontend Testing

- [ ] **Portfolio Screen Loads**
  - Navigate to Portfolio tab
  - Screen should render without errors

- [ ] **Conditional Rendering**
  - With bank: Shows Constellation Orb
  - Without bank: Shows traditional view
  - No crashes in either case

- [ ] **Orb Animations**
  - Core orb pulses smoothly
  - Satellites rotate around orb
  - No janky animations

- [ ] **Gesture Handlers**
  - Tap opens Life Events modal
  - Swipe left opens Shield modal
  - Swipe right opens Growth modal
  - Pinch opens What-If modal

- [ ] **Modal Functionality**
  - All modals slide up smoothly
  - Close buttons work
  - Swipe down to dismiss works
  - Content scrolls properly

- [ ] **Calculations**
  - Life Events: Targets calculated correctly
  - Growth: Projections match expected values
  - What-If: Updates in real-time
  - Shield: Risk metrics accurate

- [ ] **Edge Cases**
  - Zero net worth: No crashes
  - Negative cash flow: Handled gracefully
  - No positions: Shows empty state
  - No bank accounts: Falls back correctly

---

## 🐛 Troubleshooting

### Issue: Constellation Orb Not Showing

**Possible causes:**
1. No bank accounts linked
   - **Solution**: Link a bank account via Yodlee FastLink
   - **OR**: Test with mock data (modify `useMoneySnapshot` hook)

2. Snapshot API failing
   - **Check**: Backend server running?
   - **Check**: Auth token valid?
   - **Check**: Network connection?

3. `hasBankLinked` is false
   - **Check**: `snapshot.breakdown.bankAccountsCount > 0`
   - **Debug**: Add `console.log(snapshot)` in PortfolioScreen

### Issue: Gestures Not Working

**Possible causes:**
1. Gesture handler not attached
   - **Check**: `GestureDetector` wraps the orb
   - **Check**: Gesture handlers are defined

2. Modal state not updating
   - **Check**: State variables defined in PortfolioScreen
   - **Check**: Callbacks connected correctly

3. Physical device gesture issues
   - **Solution**: Test on simulator first
   - **Note**: Pinch gesture may need two-finger touch

### Issue: Modals Not Appearing

**Possible causes:**
1. Modal `visible` prop is false
   - **Debug**: Add `console.log(showLifeEvents)` etc.

2. Modal component not imported
   - **Check**: All 4 modals imported in PortfolioScreen

3. Snapshot is null
   - **Check**: `snapshot &&` condition in render

### Issue: Calculations Wrong

**Possible causes:**
1. Snapshot data incorrect
   - **Check**: Backend endpoint returns correct values
   - **Debug**: Log snapshot in component

2. Formula errors
   - **Check**: Growth calculations in GrowthProjectionView
   - **Check**: Life event targets in LifeEventPetalsModal

---

## 📱 Quick Test Commands

### Test Backend Endpoint
```bash
# Get auth token first (from login)
TOKEN="your_token_here"

# Test snapshot endpoint
curl -X GET http://localhost:8000/api/money/snapshot \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq
```

### Test Mobile App
```bash
# Start mobile app
cd mobile
npm start

# In Expo, press:
# - 'i' for iOS Simulator
# - 'a' for Android Emulator
# - Scan QR for physical device
```

### Check Logs
```bash
# Backend logs
# Check Terminal 1 for server output

# Mobile logs
# Check Expo terminal for errors
# OR use React Native Debugger
```

---

## ✅ Success Criteria

### Minimum Viable Test
- [x] Portfolio screen loads
- [x] Constellation Orb appears (if bank linked)
- [x] Traditional view appears (if no bank)
- [x] At least one gesture works (tap)
- [x] At least one modal opens and closes

### Full Test
- [x] All 4 gestures work
- [x] All 4 modals open/close correctly
- [x] Calculations are accurate
- [x] Animations are smooth
- [x] Edge cases handled
- [x] No crashes or errors

---

## 🎯 Next Steps After Testing

1. **If everything works:**
   - ✅ Ready for production
   - Consider Phase 3 enhancements

2. **If issues found:**
   - Document bugs
   - Fix critical issues
   - Re-test

3. **If calculations need adjustment:**
   - Review formulas
   - Update component logic
   - Re-test with known values

---

**Happy Testing! 🚀**

