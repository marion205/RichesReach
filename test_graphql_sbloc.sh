#!/bin/bash
# Test SBLOC GraphQL Queries
# This script tests the SBLOC GraphQL endpoints

echo "=========================================="
echo "SBLOC GraphQL Testing"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

GRAPHQL_URL="http://localhost:8000/graphql/"

# Test 1: Health Check
echo "1. Testing Health Endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Server is running${NC}"
    echo "   Response: $HEALTH"
else
    echo -e "${RED}❌ Server is not running${NC}"
    echo "   Please start the server: python main_server.py"
    exit 1
fi
echo ""

# Test 2: GraphQL Endpoint Available
echo "2. Testing GraphQL Endpoint..."
GRAPHQL_TEST=$(curl -s -X POST "$GRAPHQL_URL" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}')
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ GraphQL endpoint is accessible${NC}"
else
    echo -e "${RED}❌ GraphQL endpoint not accessible${NC}"
    exit 1
fi
echo ""

# Test 3: sblocBanks Query (without auth - should return empty or error)
echo "3. Testing sblocBanks Query (no auth)..."
SBLOC_BANKS=$(curl -s -X POST "$GRAPHQL_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { sblocBanks { id name minApr maxApr minLtv maxLtv minLoanUsd } }"
  }')
echo "   Response:"
echo "$SBLOC_BANKS" | python3 -m json.tool 2>/dev/null || echo "$SBLOC_BANKS"
echo ""

# Test 4: Get JWT Token
echo "4. Testing Authentication..."
TOKEN_RESPONSE=$(curl -s -X POST "$GRAPHQL_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { tokenAuth(username: \"test@richesreach.com\", password: \"testpass123\") { token } }"
  }')
TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('tokenAuth', {}).get('token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ] && [ "$TOKEN" != "None" ]; then
    echo -e "${GREEN}✅ Authentication successful${NC}"
    echo "   Token: ${TOKEN:0:20}..."
else
    echo -e "${YELLOW}⚠️  Authentication failed (user may not exist)${NC}"
    echo "   Response: $TOKEN_RESPONSE"
    TOKEN=""
fi
echo ""

# Test 5: sblocBanks Query (with auth)
if [ -n "$TOKEN" ] && [ "$TOKEN" != "None" ]; then
    echo "5. Testing sblocBanks Query (with auth)..."
    SBLOC_BANKS_AUTH=$(curl -s -X POST "$GRAPHQL_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "query": "query { sblocBanks { id name minApr maxApr minLtv maxLtv minLoanUsd } }"
      }')
    echo "   Response:"
    echo "$SBLOC_BANKS_AUTH" | python3 -m json.tool 2>/dev/null || echo "$SBLOC_BANKS_AUTH"
    echo ""
fi

# Test 6: createSblocSession Mutation (with auth)
if [ -n "$TOKEN" ] && [ "$TOKEN" != "None" ]; then
    echo "6. Testing createSblocSession Mutation (with auth)..."
    CREATE_SESSION=$(curl -s -X POST "$GRAPHQL_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "query": "mutation CreateSession($bankId: ID!, $amountUsd: Int!) { createSblocSession(bankId: $bankId, amountUsd: $amountUsd) { success sessionId applicationUrl error } }",
        "variables": {
          "bankId": "1",
          "amountUsd": 50000
        }
      }')
    echo "   Response:"
    echo "$CREATE_SESSION" | python3 -m json.tool 2>/dev/null || echo "$CREATE_SESSION"
    echo ""
fi

echo "=========================================="
echo "Testing Complete"
echo "=========================================="
echo ""
echo "📝 Note: Migration will run automatically on AWS ECS deployment"
echo "📝 See SBLOC_GRAPHQL_TEST_QUERIES.md for more examples"

