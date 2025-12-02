#!/bin/bash
# Test Yodlee Endpoints Script

BASE_URL="http://localhost:8000"
echo "🧪 Testing Yodlee Endpoints"
echo "============================"
echo ""

# Test 1: Health Check
echo "1️⃣ Testing Health Endpoint..."
curl -s "$BASE_URL/health" | jq '.' 2>/dev/null || curl -s "$BASE_URL/health"
echo ""
echo ""

# Test 2: FastLink Start (requires auth)
echo "2️⃣ Testing FastLink Start Endpoint..."
echo "⚠️  Note: This requires authentication. Response should show 401 or 503 if Yodlee disabled."
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/yodlee/fastlink/start" \
  -H "Content-Type: application/json")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY" | jq '.' 2>/dev/null || echo "Response: $BODY"
echo ""

# Test 3: Accounts Endpoint (requires auth)
echo "3️⃣ Testing Accounts Endpoint..."
echo "⚠️  Note: This requires authentication."
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/yodlee/accounts" \
  -H "Content-Type: application/json")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY" | jq '.' 2>/dev/null || echo "Response: $BODY"
echo ""

# Test 4: GraphQL Query
echo "4️⃣ Testing GraphQL Bank Accounts Query..."
curl -s -X POST "$BASE_URL/graphql/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { bankAccounts { id provider name mask accountType balanceCurrent isVerified isPrimary } }"
  }' | jq '.' 2>/dev/null || echo "GraphQL response received"
echo ""

echo "✅ Testing complete!"
echo ""
echo "📝 Notes:"
echo "- Endpoints require authentication (Bearer token)"
echo "- If you see 503, check USE_YODLEE=true in .env"
echo "- If you see 401, authentication is required"
echo "- If you see 404, check that endpoints are registered in main_server.py"

