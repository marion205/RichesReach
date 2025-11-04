# 🔬 Incremental Testing Plan

## Current Status: ALL FEATURES DISABLED

- ❌ Chart disabled
- ❌ GestureNavigation disabled
- ✅ GestureHandlerRootView enabled (needed for basic gestures)
- ✅ App should be stable and responsive

---

## Testing Order (One at a Time)

### Step 1: Test GestureHandlerRootView (Already Enabled)
**Status**: ✅ Currently enabled

If app crashes → disable this first
```tsx
// In App.tsx, comment out:
// <GestureHandlerRootView style={styles.container}>
// Replace with:
<View style={styles.container}>
```

---

### Step 2: Test GestureNavigation
**File**: `mobile/src/App.tsx`  
**Location**: Line ~659

**To Enable**:
1. Uncomment the `<GestureNavigation>` wrapper
2. Uncomment the closing `</GestureNavigation>` tag
3. Reload app (⌘R)
4. Test: Try swiping left/right on screen

**If crash**: GestureNavigation has an issue - keep disabled and move to Step 3

---

### Step 3: Test Chart (Without Benchmark Data)
**File**: `mobile/src/navigation/HomeScreen.tsx`  
**Location**: Line ~1078

**To Enable**:
1. Change `{false && chartData.series.length > 0 && (` to `{chartData.series.length > 0 && (`
2. Remove the placeholder View below
3. Reload app (⌘R)
4. Test: Scroll to chart section, see if it loads

**If crash**: Chart component has an issue - we'll fix it

---

### Step 4: Test Chart GestureDetector
**File**: `mobile/src/components/charts/InnovativeChart.tsx`  
**Location**: Line ~482

**Currently**: GestureDetector is enabled

**To Test Separately**:
1. If chart loads but crashes on interaction
2. Comment out `<GestureDetector>` wrapper
3. Test if chart displays without gestures

---

## Quick Enable/Disable Commands

### Enable GestureNavigation
```tsx
// In App.tsx - UNCOMMENT these:
<GestureNavigation 
  onNavigate={navigateTo} 
  currentScreen={currentScreen}
>
...
</GestureNavigation>
```

### Enable Chart
```tsx
// In HomeScreen.tsx - CHANGE:
{chartData.series.length > 0 && (
// Remove the placeholder View below it
```

---

## Testing Checklist

After each step, verify:
- [ ] App loads without crash
- [ ] No freezing
- [ ] Smooth scrolling
- [ ] Interactive elements work
- [ ] No console errors

If ANY step causes a crash → stop, disable that feature, and report which step it was.

---

## Expected Results

1. **Step 1** (GestureHandlerRootView): Should work (needed for React Native gestures)
2. **Step 2** (GestureNavigation): Might work (simple swipe handler)
3. **Step 3** (Chart display): Should work (we optimized it)
4. **Step 4** (Chart gestures): Might work (but was disabled before)

---

## Ready to Test!

Start with Step 1 verification, then proceed step by step.
Tell me which step causes the crash and I'll fix it!

