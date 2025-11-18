# API Endpoint & GraphQL Audit Checklist

## REST API Endpoints

### ✅ Verified Endpoints
1. `/api/coach/holding-insight` (GET) - Returns mock data (needs real AI integration)
   - Status: Returns mock insights based on ticker
   - File: `backend/backend/core/holding_insight_api.py`

### ⚠️ Endpoints to Verify (Need Backend Implementation)
2. `/api/oracle/insights/` (GET) - Oracle insights
3. `/api/oracle/generate-insight/` (POST) - Generate insight
4. `/api/wealth-circles/` (GET) - Wealth circles list
5. `/api/wealth-circles/{id}/posts/` (GET) - Get posts
6. `/api/wealth-circles/{id}/posts/` (POST) - Create post
7. `/api/tax/optimization-summary` (GET)
8. `/api/tax/smart-lot-optimizer-v2` (POST)
9. `/api/tax/loss-harvesting` (GET)
10. `/api/tax/capital-gains-optimization` (GET)
11. `/api/tax/tax-efficient-rebalancing` (GET)
12. `/api/tax/tax-bracket-analysis` (GET)
13. `/api/tax/two-year-gains-planner` (GET)
14. `/api/tax/wash-sale-guard-v2` (GET)
15. `/api/tax/wash-sale-guard` (POST)

## GraphQL Queries

### Queries Used in Mobile App:
1. `portfolioMetrics` - Portfolio metrics
2. `myPortfolios` - User portfolios
3. `portfolioNames` - Portfolio names
4. `stocks` - Stock search
5. `me` - Current user
6. `aiRecommendations` - AI recommendations
7. `availableBenchmarks` - Benchmark data
8. `benchmarkSeries` - Benchmark time series

## GraphQL Mutations

### Mutations Used in Mobile App:
1. `createPortfolio` - Create new portfolio
2. `createPortfolioHolding` - Add stock to portfolio
3. `updatePortfolioHolding` - Move holding to different portfolio
4. `updateHoldingShares` - Update shares count
5. `removePortfolioHolding` - Remove holding
6. `aiRebalancePortfolio` - AI rebalancing

## Issues Found

1. **Holding Insight API** - Returns mock data instead of real AI insights
2. **Oracle Insights API** - Need to verify implementation
3. **Tax Optimization APIs** - Need to verify all endpoints return data
4. **GraphQL Resolvers** - Need to verify all return real data, not null

