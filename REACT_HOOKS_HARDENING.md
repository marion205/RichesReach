# React Hooks Hardening Guide

## ✅ Hardening Checklist Implemented

### 1. Top-level hooks only
- ✅ All hooks called unconditionally at component top
- ✅ No early returns before hooks
- ✅ `useChartSeries` moved to top level

### 2. No nested hook calls
- ✅ No hooks inside callbacks, conditionals, or loops
- ✅ All hooks called in same order every render

### 3. Stable derived values
- ✅ `hasChartData`, `isResearchTab`, `isChartLoading` computed after hooks
- ✅ `useMemo` deps are stable (`[rows, indicators]`)
- ✅ Chart component has stable key for remounting

## 🔧 ESLint Guardrails

### Configuration (`mobile/.eslintrc.js`)
```javascript
{
  "plugins": ["react-hooks"],
  "rules": {
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

### Pre-commit Hook (`.husky/pre-commit`)
- Runs ESLint on mobile app before every commit
- Prevents React hooks violations from being committed
- Fails commit if violations found

## 🚨 Common Violations to Avoid

### ❌ Wrong - Conditional hooks
```javascript
// DON'T DO THIS
if (someCondition) {
  const data = useQuery(SOME_QUERY);
}
```

### ❌ Wrong - Hooks in callbacks
```javascript
// DON'T DO THIS
const handleClick = () => {
  const data = useQuery(SOME_QUERY);
};
```

### ❌ Wrong - Early returns before hooks
```javascript
// DON'T DO THIS
if (error) {
  return <Error />; // This skips hooks below
}
const data = useQuery(SOME_QUERY);
```

### ✅ Correct - Top-level hooks
```javascript
// DO THIS
const data = useQuery(SOME_QUERY);
const hasData = data?.length > 0;

if (error) {
  return <Error />; // Safe to return after all hooks
}
```

## 🎯 Chart Component Pattern

### ✅ Bulletproof Chart Implementation
```javascript
export function StockDetailScreen({ route }) {
  // ✅ Top-level hooks only
  const { symbol, range } = route.params;
  const { data: chartData, loading, error } = useChartQuery({ 
    variables: { symbol, range } 
  });
  const chartSeries = useChartSeries(chartData);
  
  // ✅ Derived values after hooks
  const hasData = chartSeries.length > 0;
  const isLoading = loading || !chartData;

  // ✅ Safe early return after all hooks
  if (error) {
    return <ErrorView message={error.message} />;
  }

  return (
    <>
      {isLoading && <Spinner />}
      {!isLoading && !hasData && <EmptyState />}
      {!isLoading && hasData && (
        <AdvancedChart
          key={`${symbol}-${range}`}  // Forces remount on change
          candles={chartSeries.map(s => ({
            time: s.t,
            open: s.o ?? s.c,
            high: s.h ?? s.c,
            low: s.l ?? s.c,
            close: s.c,
            volume: s.v ?? 0
          }))}
        />
      )}
    </>
  );
}
```

## 🔍 Debugging Hooks Errors

If you see "Rendered more hooks than during the previous render":

1. **Check hook order**: All hooks must be called in same order every render
2. **Check early returns**: No returns before all hooks are called
3. **Check conditionals**: No hooks inside if/ternary statements
4. **Check loops**: No hooks inside for/while loops
5. **Check callbacks**: No hooks inside event handlers or render functions

## 🛡️ Prevention Tools

- **ESLint**: Catches violations at development time
- **Pre-commit**: Prevents violations from being committed
- **Code review**: Manual check for hook patterns
- **Testing**: Ensure hooks work across all component states

## 📝 Testing Checklist

- [ ] Component renders without hooks errors
- [ ] All tabs work without breaking hook order
- [ ] Chart data loads and displays correctly
- [ ] No console errors about hook violations
- [ ] ESLint passes without warnings
