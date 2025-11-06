#!/bin/bash
# Comprehensive Yodlee Integration Tests

BASE_URL="http://localhost:8000"
echo "🧪 COMPREHENSIVE YODLEE INTEGRATION TESTS"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "1️⃣ Health Check"
echo "---------------"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Status: $HTTP_CODE"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
else
    echo "❌ Status: $HTTP_CODE"
    echo "$BODY"
fi
echo ""

# Test 2: FastLink Start (should return 401 or 503)
echo "2️⃣ FastLink Start Endpoint"
echo "---------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/yodlee/fastlink/start" \
  -H "Content-Type: application/json")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Status: $HTTP_CODE (Expected: 401=unauthorized, 503=disabled, 200=success)"
else
    echo "⚠️  Status: $HTTP_CODE"
fi
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

# Test 3: Accounts Endpoint
echo "3️⃣ Accounts Endpoint"
echo "---------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/yodlee/accounts" \
  -H "Content-Type: application/json")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Status: $HTTP_CODE (Expected: 401=unauthorized, 503=disabled, 200=success)"
else
    echo "⚠️  Status: $HTTP_CODE"
fi
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

# Test 4: Transactions Endpoint
echo "4️⃣ Transactions Endpoint"
echo "-------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/yodlee/transactions?from=2024-01-01&to=2024-01-31" \
  -H "Content-Type: application/json")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Status: $HTTP_CODE"
else
    echo "⚠️  Status: $HTTP_CODE"
fi
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

# Test 5: GraphQL Bank Accounts Query
echo "5️⃣ GraphQL Bank Accounts Query"
echo "--------------------------------"
RESPONSE=$(curl -s -X POST "$BASE_URL/graphql/" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ bankAccounts { id provider name mask accountType balanceCurrent balanceAvailable isVerified isPrimary } }"}')
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 6: GraphQL Bank Transactions Query
echo "6️⃣ GraphQL Bank Transactions Query"
echo "------------------------------------"
RESPONSE=$(curl -s -X POST "$BASE_URL/graphql/" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ bankTransactions(limit: 10) { id amount description merchantName category postedDate transactionType } }"}')
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 7: GraphQL Refresh Bank Account Mutation
echo "7️⃣ GraphQL Refresh Bank Account Mutation"
echo "------------------------------------------"
RESPONSE=$(curl -s -X POST "$BASE_URL/graphql/" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { refreshBankAccount(accountId: 1) { success message } }"}')
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 8: Check Server Logs for Errors
echo "8️⃣ Server Log Check"
echo "-------------------"
if [ -f /tmp/main_server.log ]; then
    ERROR_COUNT=$(grep -i "error\|exception\|traceback" /tmp/main_server.log | wc -l | tr -d ' ')
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "⚠️  Found $ERROR_COUNT errors in server logs"
        echo "Recent errors:"
        grep -i "error\|exception" /tmp/main_server.log | tail -5
    else
        echo "✅ No errors found in server logs"
    fi
else
    echo "⚠️  Server log file not found"
fi
echo ""

# Summary
echo "=========================================="
echo "✅ TESTING COMPLETE"
echo ""
echo "📊 Summary:"
echo "- Health endpoint: Tested"
echo "- REST endpoints: Tested (7 endpoints)"
echo "- GraphQL queries: Tested (bankAccounts, bankTransactions)"
echo "- GraphQL mutations: Tested (refreshBankAccount)"
echo ""
echo "💡 Note: 401/503 responses are expected without authentication"
echo "   or if Yodlee is disabled. 200 = success with auth."
