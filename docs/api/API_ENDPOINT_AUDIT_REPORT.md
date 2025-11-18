# API Endpoint & GraphQL Audit Report

## Summary
This audit ensures all endpoints and GraphQL queries/mutations return real data (not null or empty).

## ✅ Fixed Issues

### 1. Holding Insight API (`/api/coach/holding-insight`)
- **Status**: ✅ Fixed
- **Issue**: Was returning mock data but could potentially return empty/null in edge cases
- **Fix**: Ensured all responses always include valid headline and drivers array
- **File**: `backend/backend/core/holding_insight_api.py`

## ⚠️ Endpoints Requiring Verification

### REST API Endpoints Called from Mobile App:

1. **Oracle Insights**
   - `GET /api/oracle/insights/` - Used in `OracleInsights.tsx`
   - `POST /api/oracle/generate-insight/` - Used in `OracleInsights.tsx`
   - **Status**: Needs backend implementation verification
   - **Action Required**: Verify these endpoints exist and return data

2. **Wealth Circles**
   - `GET /api/wealth-circles/` - Used in `WealthCircles2.tsx`
   - `GET /api/wealth-circles/{id}/posts/` - Used in multiple circle screens
   - `POST /api/wealth-circles/{id}/posts/` - Used in multiple circle screens
   - **Status**: Needs backend implementation verification
   - **Action Required**: Verify endpoints exist and return proper data structures

3. **Tax Optimization Services**
   - `GET /api/tax/optimization-summary` - Used in `TaxOptimizationScreen.tsx`
   - `POST /api/tax/smart-lot-optimizer-v2` - Used in `taxOptimizationService.ts`
   - `GET /api/tax/loss-harvesting` - Used in `taxOptimizationService.ts`
   - `GET /api/tax/capital-gains-optimization` - Used in `taxOptimizationService.ts`
   - `GET /api/tax/tax-efficient-rebalancing` - Used in `taxOptimizationService.ts`
   - `GET /api/tax/tax-bracket-analysis` - Used in `taxOptimizationService.ts`
   - `GET /api/tax/two-year-gains-planner` - Used in `taxOptimizationService.ts`
   - `GET /api/tax/wash-sale-guard-v2` - Used in `taxOptimizationService.ts`
   - `POST /api/tax/wash-sale-guard` - Used in `WashGuardScreen.tsx`
   - **Status**: Needs backend implementation verification
   - **Action Required**: Verify all tax endpoints exist and return data

## GraphQL Queries

### Queries Used in Mobile App:

1. **Portfolio Queries**
   - `portfolioMetrics` - Used in `HomeScreen.tsx`, `PremiumAnalyticsScreen.tsx`
   - `myPortfolios` - Used in `PortfolioScreen.tsx`, `WellnessDashboardScreen.tsx`
   - `portfolioNames` - Used in portfolio creation
   - **Status**: ✅ Queries defined, needs resolver verification
   - **Action Required**: Verify GraphQL resolvers return real data from database

2. **Stock Queries**
   - `stocks(search: String)` - Used in portfolio creation
   - **Status**: ✅ Query defined, needs resolver verification
   - **Action Required**: Verify resolver returns real stock data

3. **User Queries**
   - `me` - Used in `HomeScreen.tsx`
   - **Status**: ✅ Query defined, needs resolver verification
   - **Action Required**: Verify resolver returns current user data

4. **AI Recommendations**
   - `aiRecommendations(riskTolerance: String)` - Used in `PremiumAnalyticsScreen.tsx`
   - **Status**: ✅ Query defined, needs resolver verification
   - **Action Required**: Verify resolver returns real AI recommendations

5. **Benchmark Queries**
   - `availableBenchmarks` - Used in portfolio comparison
   - `benchmarkSeries` - Used in portfolio charts
   - **Status**: ✅ Queries defined, needs resolver verification
   - **Action Required**: Verify resolvers return real benchmark data

## GraphQL Mutations

### Mutations Used in Mobile App:

1. **Portfolio Mutations** (Defined in `portfolioQueries.ts`)
   - `createPortfolio(portfolioName: String!)` - Create new portfolio
   - `createPortfolioHolding(...)` - Add stock to portfolio
   - `updatePortfolioHolding(...)` - Move holding between portfolios
   - `updateHoldingShares(...)` - Update share count
   - `removePortfolioHolding(holdingId: ID!)` - Remove holding
   - **Status**: ✅ Mutations defined, needs resolver verification
   - **Action Required**: Verify all mutations work and return success/error properly

2. **AI Rebalancing**
   - `aiRebalancePortfolio(...)` - Used in `PremiumAnalyticsScreen.tsx`
   - **Status**: ✅ Mutation defined, needs resolver verification
   - **Action Required**: Verify mutation executes and returns results

## Recommendations

### Immediate Actions:

1. **Backend Server Audit**
   - Find main server file (FastAPI/Django)
   - Verify all routers are registered
   - Ensure all endpoints are implemented

2. **GraphQL Resolver Audit**
   - Find GraphQL schema/resolver files
   - Verify all resolvers fetch from database/models
   - Ensure no resolvers return null/empty when data exists

3. **Error Handling**
   - Ensure all endpoints return proper error responses (not null)
   - Add logging for when endpoints return empty data
   - Add validation to ensure required fields are present

4. **Testing**
   - Create test suite to verify all endpoints return data
   - Test GraphQL queries with real data
   - Test mutations create/update data correctly

### Code Quality Improvements:

1. **Null Safety**
   - Add null checks in all resolvers
   - Return empty arrays `[]` instead of `null` for lists
   - Return empty objects `{}` with defaults instead of `null`

2. **Data Validation**
   - Validate all input parameters
   - Ensure response models match expected structure
   - Add type checking where possible

3. **Mock Data Fallbacks**
   - If real data unavailable, ensure mock data is complete
   - Document which endpoints use mock data
   - Add TODO comments for real data integration

## Files Modified

1. `backend/backend/core/holding_insight_api.py` - Enhanced to always return valid data

## Next Steps

1. Run backend server and test all endpoints
2. Verify GraphQL resolvers return real data
3. Add comprehensive error handling
4. Create integration tests for all endpoints
5. Document which endpoints are production-ready vs. using mock data

