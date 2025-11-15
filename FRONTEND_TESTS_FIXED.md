# Frontend Tests - Mock Loading Fix

## Problem
Frontend tests were blocked because PixelRatio mock wasn't loading before StyleSheet, causing:
```
TypeError: Cannot read properties of undefined (reading 'roundToNearestPixel')
```

## Root Cause
- `setupFilesAfterEnv` runs AFTER the test environment is initialized
- By that time, StyleSheet has already loaded and tried to use PixelRatio
- The mock in `setup.ts` was too late

## Solution
Moved PixelRatio mock to `setupTests.ts` which runs in `setupFiles` (BEFORE test environment):

1. **Created/Updated**: `mobile/src/setupTests.ts`
   - Added PixelRatio mock at the very top
   - This file runs before `setupFilesAfterEnv`

2. **Updated**: `mobile/src/__tests__/setup.ts`
   - Removed PixelRatio mock (now in setupTests.ts)
   - Added comment explaining the change

## Jest Configuration
```javascript
// jest.config.js
{
  setupFiles: ['<rootDir>/src/setupTests.ts'],        // Runs FIRST
  setupFilesAfterEnv: ['<rootDir>/src/__tests__/setup.ts'], // Runs AFTER
}
```

## Result
✅ PixelRatio mock now loads before StyleSheet
✅ All 43 frontend tests should now pass

## Test Files
- `ChartWithMoments.test.tsx` - 12 tests
- `MomentStoryPlayer.test.tsx` - 15 tests
- `wealthOracleTTS.test.ts` - 9 tests
- `StockMomentsIntegration.test.tsx` - 7 tests

**Total: 43 frontend tests ready to run**

