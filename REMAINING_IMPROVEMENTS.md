# 📋 Remaining Improvements

**Status**: ✅ Critical items completed, remaining work prioritized

---

## ✅ What We've Completed

1. ✅ **Security**: Removed hardcoded API keys from source files
2. ✅ **Console.logs**: Fixed `apolloFactory.ts` (24+ statements)
3. ✅ **TypeScript Types**: Fixed `usePlaceOrder.ts` and `types/index.ts`

---

## 🔴 HIGH PRIORITY (Should Fix Soon)

### 1. **More Console.logs in Stocks Feature**

**Status**: Mostly using `logger` already, but need to check:
- `StockMomentsIntegration.tsx` - 1 console statement
- `PriceChartScreen.tsx` - 1 console statement

**Action**: Quick fix - replace remaining console.* with logger.*

---

### 2. **TypeScript `any` Types in Stocks Feature**

**Count**: **93 matches** across **18 files**

**Top Priority Files**:
- `StockScreen.tsx` - 22 `any` types
- `StockDetailScreen.tsx` - 30 `any` types  
- `ResearchScreen.tsx` - 6 `any` types
- `MarketDataService.ts` - 7 `any` types
- `OrdersList.tsx` - 8 `any` types

**Common Patterns**:
```typescript
// ❌ Current
const data = (watchlistQ.data as any)?.myWatchlist ?? [];
const toMs = (t: any) => typeof t === 'number' ? ... : ...;
const mapped = rows.map((r: any) => ({ ... }));

// ✅ Should be
interface WatchlistData {
  myWatchlist: WatchlistItem[];
}
const data = (watchlistQ.data as WatchlistData)?.myWatchlist ?? [];
const toMs = (t: string | number) => typeof t === 'number' ? ... : ...;
const mapped = rows.map((r: GqlBar) => ({ ... }));
```

**Impact**: Medium - affects type safety but not critical for functionality

---

### 3. **TypeScript Strict Mode**

**Status**: Still disabled in `mobile/tsconfig.json`

**Current**:
```json
"strict": false,
"noImplicitAny": false,
```

**Recommendation**: Enable gradually, one check at a time

**Migration Strategy**:
1. Start with `"noImplicitAny": true` (fixes most issues)
2. Then `"strictNullChecks": true`
3. Then full `"strict": true`

**Impact**: High - but requires fixing many existing errors first

---

## 🟡 MEDIUM PRIORITY

### 4. **Console.logs Across Entire Codebase**

**Remaining**: ~1,300+ console statements across 194 files

**Top Offenders** (outside stocks feature):
- `AIPortfolioScreen.tsx` - 84+ console statements
- `SecureMarketDataService.ts` - 30+ console statements
- `TradingOfflineCache.ts` - 20+ console statements
- `HomeScreen.tsx` - 32 console statements

**Action**: Replace systematically, starting with most critical files

---

### 5. **TODO/FIXME Comments**

**Count**: 28 matches across 19 files

**Files with TODOs**:
- `StockScreen.tsx` - 7 TODOs
- `PriceChartScreen.tsx` - 2 TODOs
- `AIPortfolioScreen.tsx` - 1 TODO
- `DayTradingScreen.tsx` - 1 TODO

**Action**: Review each TODO and either:
- Implement it
- Create GitHub issue
- Remove if no longer relevant

---

### 6. **TypeScript Suppressions**

**Count**: 22 matches of `@ts-ignore` or `@ts-nocheck`

**Action**: Replace with proper types or `@ts-expect-error` with explanation

---

## 🟢 LOW PRIORITY (Nice to Have)

### 7. **Test Coverage**

**Current**: 30 test files

**Recommendation**: Add more tests for:
- Trading operations
- Authentication flows
- Critical business logic

---

### 8. **Code Duplication**

**Examples**:
- Mock data in multiple places
- Similar error handling patterns
- Duplicate validation logic

**Action**: Extract to shared utilities

---

## 📊 Priority Ranking

### Do Next (This Week):
1. ✅ **DONE**: Security fixes
2. ✅ **DONE**: Console.logs in apolloFactory.ts
3. ✅ **DONE**: TypeScript types in usePlaceOrder.ts
4. 🔄 **NEXT**: Fix remaining console.logs in stocks feature (2 files)
5. 🔄 **NEXT**: Fix `any` types in StockScreen.tsx (22 instances)

### Do Soon (This Month):
6. Fix `any` types in other stocks files
7. Replace console.logs in top offenders (AIPortfolioScreen, etc.)
8. Review and fix TODO/FIXME comments

### Do Later (Next Quarter):
9. Enable TypeScript strict mode gradually
10. Increase test coverage
11. Reduce code duplication

---

## 🎯 Quick Wins (Can Do Today)

1. **Fix 2 remaining console.logs in stocks feature** (5 minutes)
   - `StockMomentsIntegration.tsx`
   - `PriceChartScreen.tsx`

2. **Fix `any` types in StockScreen.tsx** (30-60 minutes)
   - Create proper interfaces for chart data
   - Fix `toMs` and `toNum` function types
   - Fix `watchlistQ.data as any` pattern

3. **Add ESLint rule to prevent new console.logs** (5 minutes)
   ```json
   "no-console": ["error", { "allow": ["error"] }]
   ```

---

## 📝 Summary

**Completed**: 3/3 critical items ✅
- Security fixes
- Console.logs in critical file
- TypeScript types in trading hooks

**Remaining**: 
- ~1,300 console.logs (mostly in non-critical files)
- ~1,364 `any` types (93 in stocks feature)
- TypeScript strict mode disabled
- 28 TODOs
- 22 TypeScript suppressions

**Recommendation**: 
- Focus on stocks feature first (highest risk)
- Then tackle other high-traffic screens
- Enable strict mode gradually over time

---

**Next Steps**: Would you like me to:
1. Fix the 2 remaining console.logs in stocks feature?
2. Fix `any` types in StockScreen.tsx?
3. Add ESLint rule to prevent new console.logs?
4. Something else?

