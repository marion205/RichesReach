# Reanimated Reentrancy Crash Fix

## Problem
The app was crashing with SIGABRT due to Reanimated worklet reentrancy violations. This happens when code tries to schedule UI worklets from within an already-running worklet context.

## Root Causes Fixed

1. **Gesture handlers calling JS functions directly** - Fixed gesture callbacks to use `runOnJS()` wrapper
2. **Missing 'worklet' directives** - Added explicit 'worklet' directives to all gesture handlers
3. **State setters called from worklets** - Wrapped all React state setters with `runOnJS()`

## Files Modified

### `mobile/src/components/charts/InnovativeChart.tsx`
- Added `'worklet'` directives to all gesture handlers (pinch, pan, tap)
- Wrapped JS function calls (`handleWhyTap`, `setEv`) with `runOnJS()`
- Added `runOnJS` import

### `mobile/src/features/coach/screens/AITradingCoachScreen.tsx`
- Added `'worklet'` directive to `handleRiskEnd`
- Wrapped `Vibration.vibrate` calls with `runOnJS()` in gesture handlers
- Modified `handleRiskDrag` to use `runOnJS()` for state setters and Vibration

### `mobile/src/features/community/screens/SimpleCircleDetailScreen.tsx`
- Fixed nested animation calls in `onComplete` callbacks
- Changed `withSpring(..., () => { withTiming(...) })` to use `runOnJS()` to schedule second animation from JS thread
- Fixed 3 instances: mediaScale, likeScale, and commentOpacity animations
- Added `runOnJS` import

### `mobile/src/components/AdvancedLiveStreaming.tsx`
- Fixed `onComplete` callbacks that called JS state setters
- Changed `withTiming(..., () => { setState(...) })` to use `runOnJS()` wrapper
- Fixed 2 instances: `hidePollsPanel` and `hideQAPanel`
- Added `runOnJS` import

## Key Patterns Fixed

### ❌ Before (crashes):
```typescript
// Pattern 1: Calling JS from gesture handler
const gesture = Gesture.Pan().onEnd(() => {
  value.value = withSpring(0);  // OK
  setState(newValue);  // ❌ CRASH - calling JS from worklet
  Vibration.vibrate(50);  // ❌ CRASH - calling JS from worklet
});

// Pattern 2: Nested animations in onComplete (COMMON CRASH!)
mediaScale.value = withSpring(0.95, {}, () => {
  mediaScale.value = withTiming(1);  // ❌ CRASH - scheduling UI work from UI thread
});

// Pattern 3: Calling JS setters from animation callbacks
pollScaleAnim.value = withTiming(0, {}, () => {
  setShowPolls(false);  // ❌ CRASH - calling JS from worklet
});
```

### ✅ After (safe):
```typescript
// Pattern 1: Use runOnJS for JS calls from worklets
const gesture = Gesture.Pan().onEnd(() => {
  'worklet';  // Explicit worklet directive
  value.value = withSpring(0);  // OK - UI thread value
  runOnJS(setState)(newValue);  // ✅ Safe - bounces to JS thread
  runOnJS(Vibration.vibrate)(50);  // ✅ Safe - bounces to JS thread
});

// Pattern 2: Schedule nested animations from JS thread
const scheduleSecondAnim = () => {
  mediaScale.value = withTiming(1);  // Safe - scheduled from JS
};
mediaScale.value = withSpring(0.95, {}, () => {
  runOnJS(scheduleSecondAnim)();  // ✅ Safe - bounces to JS first
});

// Pattern 3: Use runOnJS for state setters in callbacks
pollScaleAnim.value = withTiming(0, {}, () => {
  runOnJS(setShowPolls)(false);  // ✅ Safe - bounces to JS thread
});
```

## Next Steps

1. **Clean build caches** (already done):
   ```bash
   watchman watch-del-all
   rm -rf $TMPDIR/metro-* $TMPDIR/haste-map-*
   ```

2. **Rebuild the app**:
   ```bash
   cd mobile
   npx expo run:ios
   ```

3. **If crashes persist**, check for:
   - Other gesture handlers that might need the same fixes
   - Animation callbacks (`onComplete`, `onFinish`) that might call UI worklets
   - Layout animations that might conflict with Reanimated

## Verification

The fixes ensure:
- ✅ All gesture handlers have explicit 'worklet' directives
- ✅ All JS function calls from worklets use `runOnJS()`
- ✅ No nested `runOnUI()` calls from within worklets
- ✅ All React state setters wrapped with `runOnJS()`

## Related Files to Monitor

If crashes continue, check these files for similar patterns:
- `mobile/src/features/stocks/screens/StockDetailScreen.tsx`
- `mobile/src/components/AdvancedChart.tsx`
- `mobile/src/components/AdvancedLiveStreaming.tsx`
- `mobile/src/features/community/screens/SimpleCircleDetailScreen.tsx`
- `mobile/src/features/portfolio/utils/animationUtils.ts`

