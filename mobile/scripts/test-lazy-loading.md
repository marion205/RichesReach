# Testing Lazy Loading Implementation

## Quick Test Checklist

### 1. Visual Verification
- [ ] Navigate to AI Portfolio screen - should show loading indicator briefly
- [ ] Navigate to Options screen - should show loading indicator briefly
- [ ] Navigate to Stock Detail screen - should show loading indicator briefly
- [ ] Check console for lazy loading messages

### 2. Performance Check
- [ ] Initial app load should be faster
- [ ] Heavy screens load on-demand (not in initial bundle)
- [ ] Loading indicators appear before screen renders

### 3. Network Check (Flipper/DevTools)
- [ ] Verify lazy chunks are loaded separately
- [ ] Check bundle size reduction in network tab
- [ ] Verify no duplicate requests

## Expected Behavior

### ✅ Correct Behavior
- Initial app load: Fast (<2s)
- Navigating to lazy screen: Brief loading indicator → Screen appears
- Network tab: Shows separate chunk files loading

### ❌ Issues to Watch For
- Loading indicator never disappears (import error)
- Screen crashes on navigation (module not found)
- No loading indicator (Suspense not working)

## Debug Commands

```bash
# Check if lazy imports work
cd mobile
npx react-native start --reset-cache

# Check bundle for lazy chunks
npx react-native bundle --platform android --dev false --entry-file index.js --bundle-output bundle.js --verbose
```

## Common Issues & Fixes

### Issue: "Module not found" error
**Fix**: Check import path in lazy() - must be relative path string

### Issue: Loading indicator spins forever
**Fix**: Check if component exports default export correctly

### Issue: No performance improvement
**Fix**: Verify screens are actually lazy-loaded (not eagerly imported elsewhere)

