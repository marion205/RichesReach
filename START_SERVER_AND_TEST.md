# Start Server and Test SBLOC GraphQL

## Quick Start

### 1. Start the Server

Open a terminal and run:
```bash
cd /Users/marioncollins/RichesReach
python3 main_server.py
```

The server will start on `http://localhost:8000`

You should see output like:
```
🚀 Starting RichesReach Main Server...
📡 Available endpoints:
   • GET /health - Health check
   • POST /graphql/ - GraphQL endpoint
🌐 Server running on http://localhost:8000
📊 GraphQL Playground: http://localhost:8000/graphql
```

**Keep this terminal open** - the server needs to keep running.

---

### 2. Test GraphQL Queries

Open a **new terminal** and run the test script:

```bash
cd /Users/marioncollins/RichesReach
./test_graphql_sbloc.sh
```

Or test manually:

#### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

#### Test 2: sblocBanks Query (No Auth - May Return Empty)
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { sblocBanks { id name minApr maxApr minLtv maxLtv minLoanUsd } }"
  }'
```

#### Test 3: Get JWT Token
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { tokenAuth(username: \"test@richesreach.com\", password: \"testpass123\") { token } }"
  }'
```

#### Test 4: sblocBanks Query (With Auth)
```bash
# Replace YOUR_TOKEN with the token from Test 3
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "query { sblocBanks { id name minApr maxApr minLtv maxLtv minLoanUsd } }"
  }'
```

#### Test 5: createSblocSession Mutation
```bash
# Replace YOUR_TOKEN with the token from Test 3
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "mutation CreateSession($bankId: ID!, $amountUsd: Int!) { createSblocSession(bankId: $bankId, amountUsd: $amountUsd) { success sessionId applicationUrl error } }",
    "variables": {
      "bankId": "1",
      "amountUsd": 50000
    }
  }'
```

---

## Expected Results

### sblocBanks Query
**If no banks exist yet** (expected before migration):
```json
{
  "data": {
    "sblocBanks": []
  }
}
```

**If banks exist**:
```json
{
  "data": {
    "sblocBanks": [
      {
        "id": "1",
        "name": "Test Bank",
        "minApr": 0.05,
        "maxApr": 0.08,
        "minLtv": 0.5,
        "maxLtv": 0.7,
        "minLoanUsd": 10000
      }
    ]
  }
}
```

### createSblocSession Mutation
**If bank exists**:
```json
{
  "data": {
    "createSblocSession": {
      "success": true,
      "sessionId": "uuid-here",
      "applicationUrl": "https://example.com/sbloc/apply?session=uuid-here",
      "error": null
    }
  }
}
```

**If bank doesn't exist**:
```json
{
  "data": {
    "createSblocSession": {
      "success": false,
      "sessionId": null,
      "applicationUrl": null,
      "error": "SBLOC bank not found"
    }
  }
}
```

---

## Troubleshooting

### Server Won't Start
- Check if port 8000 is already in use: `lsof -ti:8000`
- Kill existing process: `kill -9 $(lsof -ti:8000)`
- Check for Python errors in the terminal

### GraphQL Returns Errors
- Make sure server is running
- Check authentication token is valid
- Verify query syntax is correct

### No Banks Returned
- This is expected before migration runs
- Migration will run automatically on AWS ECS deployment
- After migration, create banks via Django admin or shell

### Authentication Fails
- User may not exist - create test user first
- Check username/password are correct
- Verify JWT is being sent in Authorization header

---

## Migration Status

**Important**: The migration cannot run locally because it's trying to connect to the production RDS database which is not accessible from your local machine.

**Solution**: The migration will run automatically when deployed to AWS ECS where the database is accessible.

**Migration File**: `deployment_package/backend/core/migrations/0021_add_sbloc_models.py`

---

## Next Steps

1. ✅ Start server: `python3 main_server.py`
2. ✅ Test GraphQL queries (see examples above)
3. ⏳ Migration will run automatically on AWS ECS deployment
4. ⏳ Create test banks after migration (via Django admin or shell)

---

## Files Reference

- **Test Script**: `test_graphql_sbloc.sh`
- **Query Examples**: `SBLOC_GRAPHQL_TEST_QUERIES.md`
- **Complete Guide**: `WEEK2_MIGRATION_AND_TESTING.md`

---

**Status**: Ready to test! Start the server and run the test script.

