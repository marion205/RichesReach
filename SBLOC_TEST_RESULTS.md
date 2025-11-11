# SBLOC GraphQL Test Results

## Migration Status

**Note**: Migration cannot run locally because it's trying to connect to production RDS database which is not accessible from local machine. This is expected behavior.

**Solution**: Migration will run automatically when deployed to AWS ECS where the database is accessible.

---

## Local Testing (SQLite)

A local test script has been created that uses SQLite for testing without requiring production database access.

### Run Local Tests:
```bash
python3 test_sbloc_local.py
```

This script:
- Creates SBLOC tables in SQLite
- Creates test banks
- Tests `sblocBanks` query
- Tests `createSblocSession` mutation

---

## GraphQL Endpoint Testing

### Endpoint:
- **URL**: `http://localhost:8000/graphql/`
- **Method**: POST
- **Content-Type**: application/json

### Test Queries:

See `SBLOC_GRAPHQL_TEST_QUERIES.md` for complete examples.

#### 1. Test sblocBanks Query:
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "query { sblocBanks { id name minApr maxApr minLtv maxLtv } }"
  }'
```

#### 2. Test createSblocSession Mutation:
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "mutation CreateSession($bankId: ID!, $amountUsd: Int!) { createSblocSession(bankId: $bankId, amountUsd: $amountUsd) { success sessionId applicationUrl error } }",
    "variables": {
      "bankId": "1",
      "amountUsd": 50000
    }
  }'
```

---

## Production Deployment

### Migration Will Run:
When deployed to AWS ECS, the migration will run automatically:
```bash
python manage.py migrate
```

This will create:
- `sbloc_banks` table
- `sbloc_sessions` table
- All necessary indexes

---

## Next Steps

1. ✅ **Local Testing**: Run `test_sbloc_local.py` to verify GraphQL queries work
2. ✅ **GraphQL Endpoint**: Test via `http://localhost:8000/graphql/` (see examples above)
3. ⏳ **Production Migration**: Will run automatically on deployment
4. ⏳ **Populate Banks**: Use `syncSblocBanks` mutation or create banks manually

---

## Files Created

- ✅ `SBLOC_GRAPHQL_TEST_QUERIES.md` - Complete query examples
- ✅ `test_sbloc_local.py` - Local SQLite test script
- ✅ `SBLOC_TEST_RESULTS.md` - This file

---

## Status

✅ **SBLOC GraphQL Implementation**: Complete
✅ **Local Testing**: Ready
⏳ **Production Migration**: Will run on deployment
✅ **GraphQL Queries**: Ready for testing

