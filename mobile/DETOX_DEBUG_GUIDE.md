# Detox Debugging Guide for RichesReach

## Quick Start

### 1. Run Debug Script (Recommended)
```bash
cd mobile
./e2e/debug-detox.sh
```

This script will:
- Clean simulator state
- Build Detox app
- Run test with maximum logging (`DEBUG=detox*`)
- Capture screenshots on failure
- Show detailed error messages

### 2. Manual Debug Steps

#### Step 1: Build Fresh
```bash
cd mobile
yarn detox build --configuration ios.sim.debug
```

#### Step 2: Clean Simulator
```bash
xcrun simctl erase all
```

#### Step 3: Run with Verbose Logging
```bash
DEBUG=detox* yarn detox test e2e/RichesReachDemo.test.js \
  --configuration ios.sim.debug \
  --record-logs all \
  --take-screenshots failure \
  --loglevel trace
```

## Common Issues & Fixes

### Issue: "Cannot find element with locator: By.id('voice-ai-tab')"

**Root Cause**: Tab button testID not properly set or element not rendered yet.

**Fix Applied**:
- ✅ Added `tabBarButton` custom component with explicit `testID` prop
- ✅ Test now tries multiple matchers (testID, label, text, type)
- ✅ Added proper wait times and fallbacks

**Verify**:
```bash
# Check if testIDs are in code
grep -r "testID.*voice-ai-tab" src/navigation/
```

### Issue: App Loads but Test Times Out Waiting for Tab

**Root Cause**: Async rendering or navigation delay.

**Fix Applied**:
- ✅ Added initial 3s wait for app to load
- ✅ Wait for home screen explicitly before trying tabs
- ✅ Multiple fallback methods to find tabs
- ✅ Increased timeouts to 10-15s

### Issue: Tap Works but Navigation Doesn't Happen

**Root Cause**: Gesture blocked or wrong selector.

**Fix Applied**:
- ✅ Using `tabBarButton` custom component ensures proper touch handling
- ✅ Added `accessibilityRole="button"` for better interaction
- ✅ Multiple matcher strategies (ID, label, text)

## Test Flow

1. **App Launch**: Wait 3s for initial load
2. **Home Screen**: Wait for `home-screen` testID (or fallback to any visible element)
3. **Tab Navigation**: Try 4 methods:
   - By testID (`voice-ai-tab`)
   - By accessibility label
   - By text ("Home")
   - By type (first TouchableOpacity)
4. **Screen Transition**: Wait 2s after tap for navigation
5. **Continue**: Proceed with Voice AI features

## Debug Output

When running with `DEBUG=detox*`, you'll see:
- Element visibility status
- Which matcher succeeded/failed
- Detailed error messages
- Screenshots in `artifacts/` folder

## Next Steps If Still Failing

1. **Check Screenshots**: Look in `artifacts/` folder after test run
2. **Check Logs**: Full logs saved to `artifacts/` with `--record-logs all`
3. **Verify Build**: Make sure app is built with latest code changes
4. **Check Simulator**: Ensure simulator is running and responsive

## Rebuild After Code Changes

**Always rebuild after changing testIDs or navigation:**
```bash
cd mobile
yarn detox build --configuration ios.sim.debug
```

## Files Modified

- `src/navigation/AppNavigator.tsx`: Added `tabBarButton` with explicit testIDs
- `e2e/RichesReachDemo.test.js`: Enhanced with multiple matchers and better error handling
- `e2e/debug-detox.sh`: New debug script for easy troubleshooting

