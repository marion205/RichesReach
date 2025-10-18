#!/bin/bash
set -euo pipefail

echo "🧪 Testing Local Authentication and Watchlist Functionality"
echo "============================================================"

# Test 1: Health check
echo "1. Testing Django server health..."
curl -s http://192.168.1.236:8000/healthz && echo " ✅ Django server is running"

# Test 2: Authentication
echo -e "\n2. Testing authentication..."
AUTH_RESPONSE=$(curl -s -X POST http://192.168.1.236:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation TokenAuth($email: String!, $password: String!) { tokenAuth(email: $email, password: $password) { token } }",
    "variables": {"email": "test@example.com", "password": "testpass123"}
  }')

echo "Auth response: $AUTH_RESPONSE"

# Extract token
TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.data.tokenAuth.token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Authentication failed"
  echo "Response: $AUTH_RESPONSE"
  exit 1
fi

echo "✅ Authentication successful"
echo "Token: ${TOKEN:0:20}..."

# Test 3: Add to watchlist
echo -e "\n3. Testing add to watchlist..."
WATCHLIST_RESPONSE=$(curl -s -X POST http://192.168.1.236:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: JWT $TOKEN" \
  -d '{
    "query": "mutation AddToWatchlist($symbol: String!, $companyName: String, $notes: String) { addToWatchlist(symbol: $symbol, companyName: $companyName, notes: $notes) { success message } }",
    "variables": {"symbol": "AAPL", "companyName": "Apple Inc.", "notes": "Test from local database"}
  }')

echo "Watchlist response: $WATCHLIST_RESPONSE"

SUCCESS=$(echo "$WATCHLIST_RESPONSE" | jq -r '.data.addToWatchlist.success // false')

if [ "$SUCCESS" = "true" ]; then
  echo "✅ Successfully added AAPL to watchlist"
else
  echo "❌ Failed to add to watchlist"
  MESSAGE=$(echo "$WATCHLIST_RESPONSE" | jq -r '.data.addToWatchlist.message // "Unknown error"')
  echo "Error: $MESSAGE"
fi

echo -e "\n🎉 Test completed!"
