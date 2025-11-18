# Performance Improvements Analysis

## 🔍 Identified Performance Issues

### 1. **GraphQL Query Optimization** ⚠️ HIGH IMPACT
**Issues:**
- Multiple queries using `cache-and-network` which always fetches from network
- Some queries don't skip when not needed
- Multiple parallel queries in TradingScreen that could be batched
- Quote query refetches on every symbol change

**Files:**
- `TradingScreen.tsx`: 6+ queries running simultaneously
- `StockScreen.tsx`: 5+ queries for different tabs
- `useAlpacaAccount.ts`, `useAlpacaPositions.ts`, `useAlpacaOrders.ts`: All use `cache-and-network`

**Impact:** High - Network requests on every render/mount

---

### 2. **List Rendering Optimization** ⚠️ MEDIUM IMPACT
**Issues:**
- `PositionsList` FlatList missing `getItemLayout` for better scroll performance
- `StockScreen` FlatList has optimizations but could add more
- Some lists render all items at once instead of virtualizing

**Files:**
- `PositionsList.tsx`: Missing `getItemLayout`, `removeClippedSubviews`
- `OrdersList.tsx`: Uses ScrollView instead of FlatList (less efficient for large lists)

**Impact:** Medium - Slower scrolling with many items

---

### 3. **Component Lazy Loading** ⚠️ MEDIUM IMPACT
**Issues:**
- Large components imported eagerly (StockDetailScreen, OrderModal, etc.)
- TradingScreen imports many heavy components upfront
- No code splitting for route-based screens

**Files:**
- `TradingScreen.tsx`: Imports all components eagerly
- `StockDetailScreen.tsx`: Large component (2000+ lines) loaded immediately
- `OrderModal.tsx`: Heavy component loaded even when modal not visible

**Impact:** Medium - Slower initial bundle load time

---

### 4. **Expensive Calculations** ⚠️ LOW-MEDIUM IMPACT
**Issues:**
- `StockScreen.listData` useMemo processes large arrays on every tab change
- OrderForm validation runs in useEffect (good) but could be debounced
- Some calculations not memoized

**Files:**
- `StockScreen.tsx`: `listData` useMemo processes AI recommendations, ML screening, etc.
- `OrderForm.tsx`: Validation runs on every input change (could debounce)

**Impact:** Low-Medium - Slight lag on tab switches

---

### 5. **Unnecessary Re-renders** ⚠️ LOW IMPACT
**Issues:**
- Some components not wrapped in React.memo
- Callbacks not memoized in some places
- Props changing unnecessarily

**Files:**
- `OrderModal.tsx`: May re-render unnecessarily
- `AccountSummaryCard.tsx`: Should check if memoized

**Impact:** Low - Minor performance impact

---

## 🚀 Recommended Improvements

### Priority 1: GraphQL Query Optimization (HIGH IMPACT)

1. **Change fetch policies:**
   ```typescript
   // Change from cache-and-network to cache-first for better performance
   fetchPolicy: 'cache-first', // Use cache, only fetch if stale
   nextFetchPolicy: 'cache-first', // Keep using cache
   ```

2. **Add proper skip conditions:**
   ```typescript
   skip: !accountId || !isVisible, // Don't fetch when not needed
   ```

3. **Batch queries where possible:**
   - Use `useQueries` hook for parallel queries
   - Combine related queries into single request

4. **Optimize quote fetching:**
   - Debounce quote requests when symbol changes
   - Use cache-first for quotes (they update frequently anyway)

### Priority 2: List Rendering (MEDIUM IMPACT)

1. **Add FlatList optimizations:**
   ```typescript
   <FlatList
     getItemLayout={(data, index) => ({
       length: ITEM_HEIGHT,
       offset: ITEM_HEIGHT * index,
       index,
     })}
     removeClippedSubviews={true}
     initialNumToRender={10}
     maxToRenderPerBatch={5}
     windowSize={10}
     updateCellsBatchingPeriod={50}
   />
   ```

2. **Convert ScrollView to FlatList:**
   - `OrdersList.tsx` uses ScrollView - convert to FlatList for better performance

### Priority 3: Code Splitting (MEDIUM IMPACT)

1. **Lazy load heavy components:**
   ```typescript
   const OrderModal = React.lazy(() => import('../components/OrderModal'));
   const StockDetailScreen = React.lazy(() => import('./StockDetailScreen'));
   ```

2. **Route-based code splitting:**
   - Split screens by route
   - Load only when navigated to

### Priority 4: Debounce & Throttle (LOW-MEDIUM IMPACT)

1. **Debounce validation:**
   ```typescript
   const debouncedValidation = useMemo(
     () => debounce(validateForm, 300),
     []
   );
   ```

2. **Throttle quote requests:**
   - Don't fetch quote on every keystroke
   - Wait for user to stop typing

### Priority 5: Memoization (LOW IMPACT)

1. **Wrap more components in React.memo**
2. **Memoize expensive callbacks**
3. **Use useMemo for derived data**

---

## 📊 Expected Performance Gains

| Improvement | Expected Gain | Effort |
|------------|---------------|--------|
| GraphQL cache-first | 40-60% faster loads | Low |
| FlatList optimizations | 30-50% smoother scrolling | Low |
| Code splitting | 20-30% faster initial load | Medium |
| Debounce validation | 10-20% less CPU usage | Low |
| Component memoization | 5-15% fewer re-renders | Low |

---

## 🎯 Quick Wins (Can implement immediately)

1. ✅ Change `cache-and-network` to `cache-first` in hooks
2. ✅ Add `getItemLayout` to PositionsList FlatList
3. ✅ Add `removeClippedSubviews` to all FlatLists
4. ✅ Debounce quote fetching in OrderForm
5. ✅ Convert OrdersList ScrollView to FlatList

---

## 📝 Implementation Order

1. **Phase 1 (Quick Wins):** GraphQL fetch policies, FlatList optimizations
2. **Phase 2 (Medium):** Code splitting, lazy loading
3. **Phase 3 (Polish):** Debouncing, additional memoization
