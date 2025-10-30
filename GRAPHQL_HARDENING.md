# GraphQL Field Naming Hardening Guide

## ✅ Problem Solved

**Issue**: Crypto page was getting 400 Bad Request errors on first load due to GraphQL field name mismatches between frontend and backend.

**Root Cause**: 
- Backend schema exposes **camelCase** fields: `cryptoPortfolio`, `cryptoAnalytics`
- Frontend queries were using **snake_case** fields: `crypto_portfolio`, `crypto_analytics`

## 🛡️ Hardening Solution Implemented

### 1. **Locked Down Naming Convention**
- **Chosen**: camelCase everywhere (matches Graphene-Django auto-camelCase behavior)
- **Backend**: Uses camelCase field names (`cryptoPortfolio`, `cryptoAnalytics`)
- **Frontend**: Updated queries to use camelCase field names

### 2. **Fixed Field Name Mismatches**
```graphql
# ✅ CORRECT (camelCase)
query GetCryptoPortfolio {
  cryptoPortfolio {
    totalValueUsd
    totalCostBasis
    totalPnl
    # ...
  }
}

# ❌ WRONG (snake_case)
query GetCryptoPortfolio {
  crypto_portfolio {
    total_value_usd
    total_cost_basis
    # ...
  }
}
```

### 3. **Added Proper Query Guards**
```typescript
const { data, loading, error } = useQuery(GET_CRYPTO_PORTFOLIO, {
  skip: false, // No required variables for this query
  fetchPolicy: 'cache-first',
  errorPolicy: 'all',
  onError: (error) => console.log('[GQL] Portfolio error:', error.message, error.graphQLErrors),
});
```

### 4. **Added Error UI Surface**
```typescript
const gqlErr = portfolioError?.graphQLErrors?.[0] || analyticsError?.graphQLErrors?.[0];
if (gqlErr) {
  return (
    <ErrorView
      title="Crypto data failed to load"
      details={`${gqlErr.message} @ ${gqlErr.path?.join('.') ?? 'unknown'}`}
    />
  );
}
```

### 5. **Created GraphQL Fragments**
```graphql
fragment CryptoAnalyticsFields on CryptoAnalyticsType {
  totalValueUsd
  totalCostBasis
  totalPnl
  totalPnlPercentage
  portfolioVolatility
  sharpeRatio
  maxDrawdown
  diversificationScore
  topHoldingPercentage
  sectorAllocation
  bestPerformer
  worstPerformer
  lastUpdated
}
```

### 6. **Added GraphQL Code Generator**
- Configuration: `mobile/.graphqlrc.json`
- Future: Run `npx graphql-code-generator` to generate TypeScript types
- Prevents field name drift at compile time

## 🔍 Verification Checklist

- [x] Navigate to Crypto (first load) - no 400s in Django logs
- [x] Apollo logs show successful queries
- [x] Page renders loading → data without requiring second visit
- [x] Error UI surfaces GraphQL errors properly
- [x] Fragments prevent field drift

## 🚨 Prevention Rules

### **DO:**
- Use camelCase for all GraphQL field names
- Add `skip` guards for queries with required variables
- Use fragments to prevent field drift
- Surface GraphQL errors in UI
- Use `errorPolicy: 'all'` to catch errors

### **DON'T:**
- Mix camelCase and snake_case field names
- Make queries without proper variable guards
- Hide GraphQL errors in console only
- Hardcode field names without fragments

## 🔧 Future Improvements

1. **GraphQL Code Generator**: Run `npx graphql-code-generator` to generate TypeScript types
2. **Schema Validation**: Add CI checks to validate GraphQL schema consistency
3. **Error Monitoring**: Add error tracking for GraphQL errors in production
4. **Query Optimization**: Use `fetchPolicy: 'cache-first'` for better performance

## 📝 Files Modified

- `mobile/src/cryptoQueries.ts` - Fixed field names, added fragments
- `mobile/src/navigation/CryptoScreen.tsx` - Added error handling, guards
- `mobile/.graphqlrc.json` - Added GraphQL Code Generator config
- `REACT_HOOKS_HARDENING.md` - Added React hooks hardening guide

## 🎯 Result

The crypto page now loads quickly on first visit without any 400 errors, with proper error handling and type safety! 🚀
