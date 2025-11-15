# Key Moments Feature - Unit Tests

## Overview

Comprehensive unit tests for all Key Moments features including backend models, GraphQL queries, worker functions, and frontend components.

## Backend Tests

### 1. `test_stock_moment_models.py`
**Location**: `deployment_package/backend/core/tests/test_stock_moment_models.py`

**Tests**:
- ✅ Model creation with all fields
- ✅ String representation
- ✅ Default values
- ✅ Ordering by symbol and timestamp
- ✅ Category choices validation
- ✅ Symbol filtering
- ✅ Timestamp range filtering
- ✅ JSON field (source_links) handling
- ✅ Importance score range
- ✅ Impact fields (1d, 7d)

**Run**: `python manage.py test core.tests.test_stock_moment_models`

### 2. `test_stock_moment_queries.py`
**Location**: `deployment_package/backend/core/tests/test_stock_moment_queries.py`

**Tests**:
- ✅ ONE_MONTH range filtering
- ✅ THREE_MONTHS range filtering
- ✅ SIX_MONTHS range filtering
- ✅ YEAR_TO_DATE range filtering
- ✅ ONE_YEAR range filtering
- ✅ Symbol filtering
- ✅ Timestamp ordering
- ✅ Empty result handling
- ✅ Case-insensitive symbol matching
- ✅ Error handling

**Run**: `python manage.py test core.tests.test_stock_moment_queries`

### 3. `test_stock_moment_worker.py`
**Location**: `deployment_package/backend/core/tests/test_stock_moment_worker.py`

**Tests**:
- ✅ PriceContext dataclass
- ✅ Event dataclass
- ✅ RawMomentJob dataclass
- ✅ build_events_block function
- ✅ normalize_category function
- ✅ create_stock_moment_from_job (success)
- ✅ create_stock_moment_from_job (low importance skip)
- ✅ create_stock_moment_from_job (LLM error handling)
- ✅ create_stock_moment_from_job (invalid response)

**Run**: `python manage.py test core.tests.test_stock_moment_worker`

## Frontend Tests

### 4. `ChartWithMoments.test.tsx`
**Location**: `mobile/src/components/charts/__tests__/ChartWithMoments.test.tsx`

**Tests**:
- ✅ Chart rendering with price series
- ✅ Moment dots rendering
- ✅ onMomentChange callback
- ✅ Haptic feedback on selection
- ✅ Long-press detection (500ms)
- ✅ Long-press cancellation on move
- ✅ Long-press cancellation on release
- ✅ Moment card display
- ✅ Detail modal opening
- ✅ External activeMomentId control
- ✅ Empty data handling

**Run**: `npm test -- ChartWithMoments.test.tsx`

### 5. `MomentStoryPlayer.test.tsx`
**Location**: `mobile/src/components/charts/__tests__/MomentStoryPlayer.test.tsx`

**Tests**:
- ✅ Visibility rendering
- ✅ Intro slide with/without enableIntro
- ✅ Analytics event firing (open/close)
- ✅ onMomentChange callback
- ✅ Haptic feedback on moment change
- ✅ Play/pause toggle
- ✅ Next/previous navigation
- ✅ Custom speakFn integration
- ✅ Custom stopFn integration
- ✅ Listened moments tracking
- ✅ Success haptic on completion
- ✅ Custom intro text
- ✅ Empty moments handling

**Run**: `npm test -- MomentStoryPlayer.test.tsx`

### 6. `wealthOracleTTS.test.ts`
**Location**: `mobile/src/services/__tests__/wealthOracleTTS.test.ts`

**Tests**:
- ✅ TTS API call with correct parameters
- ✅ Audio playback from returned URL
- ✅ Stop current sound before playing new
- ✅ TTS API error handling
- ✅ Missing audio_url handling
- ✅ Network error handling
- ✅ stopWealthOracle function
- ✅ Stop when no sound playing
- ✅ Stop error handling

**Run**: `npm test -- wealthOracleTTS.test.ts`

### 7. `StockMomentsIntegration.test.tsx`
**Location**: `mobile/src/features/stocks/screens/__tests__/StockMomentsIntegration.test.tsx`

**Tests**:
- ✅ Loading state
- ✅ Chart rendering after GraphQL load
- ✅ Story mode from button (with intro)
- ✅ Story mode from long-press (no intro)
- ✅ GraphQL error handling
- ✅ Empty moments handling
- ✅ Analytics handler integration

**Run**: `npm test -- StockMomentsIntegration.test.tsx`

## Running All Tests

### Backend Tests
```bash
cd deployment_package/backend
python manage.py test core.tests.test_stock_moment_models
python manage.py test core.tests.test_stock_moment_queries
python manage.py test core.tests.test_stock_moment_worker
```

Or run all stock moment tests:
```bash
python manage.py test core.tests.test_stock_moment
```

### Frontend Tests
```bash
cd mobile
npm test -- --testPathPattern="ChartWithMoments|MomentStoryPlayer|StockMomentsIntegration|wealthOracleTTS"
```

Or run individually:
```bash
npm test -- ChartWithMoments.test.tsx
npm test -- MomentStoryPlayer.test.tsx
npm test -- wealthOracleTTS.test.ts
npm test -- StockMomentsIntegration.test.tsx
```

### With Coverage
```bash
# Backend
python manage.py test core.tests.test_stock_moment --with-coverage

# Frontend
npm test -- --coverage --testPathPattern="ChartWithMoments|MomentStoryPlayer|StockMomentsIntegration|wealthOracleTTS"
```

## Test Coverage

### Backend Coverage
- **Models**: 100% field coverage
- **Queries**: All range types, filtering, ordering
- **Worker**: All dataclasses, functions, error paths

### Frontend Coverage
- **Components**: Rendering, interactions, callbacks
- **Services**: API calls, error handling, state management
- **Integration**: GraphQL, analytics, story mode flows

## Test Dependencies

### Backend
- Django TestCase
- unittest.mock
- django.utils.timezone

### Frontend
- @testing-library/react-native
- @apollo/client/testing (MockedProvider)
- jest
- expo-haptics (mocked)
- expo-speech (mocked)
- expo-av (mocked)

## Notes

- All tests use mocks for external dependencies (APIs, native modules)
- Tests are isolated and don't require running services
- Frontend tests use fake timers for long-press detection
- GraphQL tests use MockedProvider for isolated testing
- Worker tests mock OpenAI API calls

## Continuous Integration

These tests should be run in CI/CD pipeline:
1. Backend tests on Django test runner
2. Frontend tests on Jest
3. Coverage reports generated
4. Tests must pass before merge

## Future Test Additions

- Integration tests for full flow
- E2E tests for user interactions
- Performance tests for large datasets
- Accessibility tests for voice features

