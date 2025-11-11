# Server Status

## Server Started

**Command**: `python3 main_server.py`  
**Status**: Running in background  
**Port**: 8000  
**URL**: `http://localhost:8000`

---

## Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### GraphQL Endpoint
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

---

## Test SBLOC GraphQL

### Test sblocBanks Query
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { sblocBanks { id name minApr maxApr minLtv maxLtv minLoanUsd } }"
  }'
```

### Test with Authentication
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { tokenAuth(username: \"test@richesreach.com\", password: \"testpass123\") { token } }"}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('tokenAuth', {}).get('token', ''))" 2>/dev/null)

# Query with token
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "query { sblocBanks { id name } }"}'
```

---

## Automated Testing

Run the test script:
```bash
./test_graphql_sbloc.sh
```

---

## Server Logs

Check server output in the terminal where you started it, or check for any errors.

---

## Stop Server

To stop the server:
```bash
# Find process
lsof -ti:8000

# Kill process
kill -9 $(lsof -ti:8000)
```

---

**Status**: Server is running and ready for GraphQL testing!
