# AI Recommendations Performance Test Summary

## Test Implementation

A comprehensive test suite has been created at:
- `deployment_package/backend/core/tests/test_ai_recommendations.py`

## Test Coverage

### 1. Basic Functionality Test
- ✅ Verifies resolver returns results
- ✅ Checks `buy_recommendations` field exists
- ✅ Validates recommendation structure
- ✅ Ensures ML scores >= 0.6 (filter threshold)

### 2. Profile Personalization Test
- ✅ Tests with custom profile input
- ✅ Verifies risk tolerance is applied
- ✅ Checks profile fields are used correctly

### 3. Performance Test
- ✅ Runs 5 consecutive calls
- ✅ Measures response time
- ✅ Calculates average, min, max times
- ✅ Asserts average < 10s

### 4. ML Scoring Quality Test
- ✅ Verifies all scores >= 0.6
- ✅ Checks average score > 0.5
- ✅ Validates score distribution

### 5. Saved Profile Test
- ✅ Tests with IncomeProfile from database
- ✅ Verifies saved profile is used
- ✅ Checks risk tolerance is reflected

## Expected Performance Metrics

### Response Time Targets:
- **Excellent**: < 1.0s average
- **Good**: < 2.0s average
- **Acceptable**: < 5.0s average
- **Slow**: >= 5.0s average

### Quality Metrics:
- **ML Score Threshold**: >= 0.6 (60% confidence)
- **Minimum Recommendations**: At least 1 (if stocks available)
- **Average Score**: > 0.5 (50% confidence)

## How to Run Tests

### Option 1: Django Test Runner
```bash
cd deployment_package/backend
python manage.py test core.tests.test_ai_recommendations -v 2
```

### Option 2: Pytest
```bash
cd deployment_package/backend
pytest core/tests/test_ai_recommendations.py -v
```

### Option 3: Manual GraphQL Test
```bash
# Start backend server
cd deployment_package/backend
python manage.py runserver

# In another terminal, test GraphQL query
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { aiRecommendations(usingDefaults: true) { buyRecommendations { symbol companyName confidence reasoning targetPrice currentPrice expectedReturn } } }"
  }'
```

## Implementation Verification

### Code Changes Made:
1. ✅ Updated `resolve_ai_recommendations` to fetch stocks dynamically
2. ✅ Integrated `ai_service.score_stocks_ml()` for ML scoring
3. ✅ Added filtering by ML score >= 0.6
4. ✅ Returns top 10 recommendations
5. ✅ Includes spending habits personalization (optional)
6. ✅ Uses `premium_types.AIRecommendationsType` for proper response format

### Key Features:
- **Dynamic**: No pre-generation required
- **ML-Powered**: Real-time scoring with user profile
- **Personalized**: Risk tolerance, goals, age, income
- **Performance**: Limits to 100 stocks for scoring
- **Quality**: Filters by confidence threshold

## Potential Issues to Monitor

1. **ML Service Availability**
   - If ML service unavailable, falls back gracefully
   - May return empty recommendations if fallback fails

2. **Database Stock Count**
   - Needs at least some stocks with `current_price > 0`
   - Test creates 50 test stocks if needed

3. **Performance with Large Datasets**
   - Currently limits to 100 stocks
   - May need optimization if database has 1000+ stocks

4. **Spending Habits Service**
   - Optional feature, won't break if unavailable
   - Logs warning but continues

## Next Steps

1. **Run Tests**: Execute test suite when Django environment is available
2. **Monitor Performance**: Track response times in production
3. **Optimize if Needed**: Consider caching or reducing stock limit
4. **Add More Tests**: Test edge cases (no stocks, ML service down, etc.)

## Test Results (To Be Run)

Once tests are executed, results will show:
- Response time performance
- ML scoring quality
- Recommendation count
- Error handling
- Profile personalization effectiveness

---

**Status**: Test suite created and ready to run. Implementation is complete and should perform well based on code analysis.

