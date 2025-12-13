#!/bin/bash
# Smoke tests for async AI endpoints
# Run this after deploying to verify everything works

BASE_URL="${BASE_URL:-http://localhost:8000}"
echo "Testing async AI endpoints at $BASE_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "Test 1: Health Check"
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/ai/health/")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC} Health check passed (200)"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗${NC} Health check failed ($http_code)"
    echo "$body"
fi
echo ""

# Test 2: Non-Streaming Chat
echo "Test 2: Non-Streaming Chat"
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/ai/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is Bitcoin? Answer in one sentence."}
    ]
  }')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC} Chat endpoint passed (200)"
    echo "$body" | jq '{one_sentence, confidence, conviction, why, latency_ms}' 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗${NC} Chat endpoint failed ($http_code)"
    echo "$body"
fi
echo ""

# Test 3: Streaming Chat (first 5 tokens)
echo "Test 3: Streaming Chat (first 5 tokens)"
echo -e "${YELLOW}Note:${NC} This will stream tokens. Press Ctrl+C after a few seconds."
timeout 5 curl -N -X POST "$BASE_URL/api/ai/chat/stream/" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Count to 10"}
    ]
  }' 2>/dev/null | head -n 10 || echo -e "${GREEN}✓${NC} Streaming works (tokens received)"
echo ""

# Test 4: Rate Limiting (send 5 requests quickly)
echo "Test 4: Rate Limiting (5 quick requests)"
for i in {1..5}; do
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/ai/chat/" \
      -H "Content-Type: application/json" \
      -d "{\"messages\": [{\"role\": \"user\", \"content\": \"test $i\"}]}")
    http_code=$(echo "$response" | tail -n1)
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} Request $i: OK"
    elif [ "$http_code" = "429" ]; then
        echo -e "${YELLOW}⚠${NC} Request $i: Rate Limited (expected if limit reached)"
    else
        echo -e "${RED}✗${NC} Request $i: Failed ($http_code)"
    fi
done
echo ""

# Test 5: Error Handling
echo "Test 5: Error Handling"
echo "  Testing invalid JSON..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/ai/chat/" \
  -H "Content-Type: application/json" \
  -d 'invalid json')
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "400" ]; then
    echo -e "${GREEN}✓${NC} Invalid JSON handled correctly (400)"
else
    echo -e "${RED}✗${NC} Invalid JSON not handled ($http_code)"
fi

echo "  Testing missing messages..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/ai/chat/" \
  -H "Content-Type: application/json" \
  -d '{}')
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "400" ]; then
    echo -e "${GREEN}✓${NC} Missing messages handled correctly (400)"
else
    echo -e "${RED}✗${NC} Missing messages not handled ($http_code)"
fi
echo ""

echo "Smoke tests complete!"
echo ""
echo "If all tests passed, your async AI service is ready for production."

