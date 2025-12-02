# TomorrowScreen Test Suite

## Overview
Comprehensive test suite for the TomorrowScreen component covering all Phase 1, 2, and 3 features.

## Test Coverage

### Phase 1: Core Features ✅
- ✅ Loading skeleton on initial load
- ✅ Displays recommendations after loading
- ✅ Real-time price with change indicators
- ✅ Sparklines for price history
- ✅ Error banner on network failure
- ✅ Session indicators (RTH/ETH)

### Phase 2: Advanced Features ✅
- ✅ Toggle between list and heatmap view
- ✅ Top Movers badge display
- ✅ Unusual Volume badge display
- ✅ Contract info modal
- ✅ "Why Now" as bullet points

### Phase 3: Enhanced Features ✅
- ✅ Chart modal on card tap
- ✅ Filter recommendations by category
- ✅ Sort recommendations
- ✅ Add to watchlist
- ✅ Share recommendation
- ✅ Comparison view

### Additional Tests ✅
- ✅ Trade actions (place order)
- ✅ Trade confirmation modal
- ✅ Error handling (timeout, network errors)
- ✅ Dark mode support

## Running Tests

```bash
# Run all TomorrowScreen tests
cd mobile
npm test -- src/features/futures/screens/__tests__/TomorrowScreen.test.tsx

# Run with coverage
npm test -- src/features/futures/screens/__tests__/TomorrowScreen.test.tsx --coverage

# Run in watch mode
npm test -- --watch src/features/futures/screens/__tests__/TomorrowScreen.test.tsx
```

## Test Structure

The test file is organized into describe blocks:
1. **Phase 1: Core Features** - Basic functionality
2. **Phase 2: Advanced Features** - Heatmap, badges, modals
3. **Phase 3: Enhanced Features** - Chart, filters, watchlist, share, comparison
4. **Trade Actions** - Order placement
5. **Error Handling** - Network errors, timeouts
6. **Dark Mode** - Theme support

## Mocked Dependencies

- `FuturesService` - API calls
- `useWatchlist` - Watchlist hook
- `expo-haptics` - Haptic feedback
- `react-native-vector-icons/Feather` - Icons
- `SparkMini` - Chart component
- `react-native/Share` - Share API

## Notes

- Tests use `@testing-library/react-native` for rendering
- All async operations use `waitFor` for proper timing
- Mock data matches the structure used in the component
- Tests verify both UI rendering and user interactions

