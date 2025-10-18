#!/bin/bash
set -euo pipefail

echo "🧪 Comprehensive Authentication and Watchlist Test"
echo "=================================================="

# Configuration
cd /Users/marioncollins/RichesReach/backend/backend/backend/backend
export DJANGO_SETTINGS_MODULE="richesreach.settings_local_db"
BASE="http://127.0.0.1:8000/graphql/"

echo "Using GraphQL endpoint: $BASE"
echo "Using Django settings: $DJANGO_SETTINGS_MODULE"

# 1) Create test user (idempotent)
echo -e "\n1️⃣ Creating test user..."
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
U=get_user_model()
u,created=U.objects.get_or_create(email='test@example.com', defaults={'username':'test_user'})
if created: 
    u.set_password('testpass123')
    u.save()
    print('✅ User created:', u.email)
else:
    print('✅ User exists:', u.email)
"

# 2) Get JWT (try email first, then username if needed)
echo -e "\n2️⃣ Testing authentication (email)..."
curl -sS -H "Content-Type: application/json" -X POST "$BASE" -d '{
  "query":"mutation TokenAuth($email:String!,$password:String!){ tokenAuth(email:$email,password:$password){ token } }",
  "variables":{"email":"test@example.com","password":"testpass123"}
}' | tee /tmp/token_email.json

echo -e "\n2️⃣ Testing authentication (username)..."
curl -sS -H "Content-Type: application/json" -X POST "$BASE" -d '{
  "query":"mutation TokenAuth($username:String!,$password:String!){ tokenAuth(username:$username,password:$password){ token } }",
  "variables":{"username":"test_user","password":"testpass123"}
}' | tee /tmp/token_username.json

# 3) Extract the token (email result preferred, fallback to username)
echo -e "\n3️⃣ Extracting JWT token..."
TOKEN="$(python3 - <<'PY'
import json,sys
def pick(p):
  try:
    j=json.load(open(p))
    # graphql-jwt uses 'tokenAuth':{'token':...}
    return j.get('data',{}).get('tokenAuth',{}).get('token')
  except: return None
t=pick('/tmp/token_email.json') or pick('/tmp/token_username.json')
print(t or '')
PY
)"

if [ -z "$TOKEN" ]; then
  echo "❌ No token found. Check the two tokenAuth responses above."
  echo "Email response:"
  cat /tmp/token_email.json
  echo -e "\nUsername response:"
  cat /tmp/token_username.json
  exit 1
fi

echo "✅ TOKEN acquired (${#TOKEN} chars)"
echo "Token preview: ${TOKEN:0:20}..."

# 4) Add to watchlist (try both Authorization schemes commonly used)
echo -e "\n4️⃣ Testing addToWatchlist via Authorization: JWT..."
JWT_RESPONSE=$(curl -sS -H "Content-Type: application/json" -H "Authorization: JWT $TOKEN" -X POST "$BASE" -d '{
  "query":"mutation AddToWatchlist($symbol:String!,$companyName:String,$notes:String){ addToWatchlist(symbol:$symbol,companyName:$companyName,notes:$notes){ success message } }",
  "variables":{"symbol":"AAPL","companyName":"Apple Inc.","notes":"Local test (JWT)"}
}')
echo "$JWT_RESPONSE"

echo -e "\n4️⃣ Testing addToWatchlist via Authorization: Bearer..."
BEARER_RESPONSE=$(curl -sS -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -X POST "$BASE" -d '{
  "query":"mutation AddToWatchlist($symbol:String!,$companyName:String,$notes:String){ addToWatchlist(symbol:$symbol,companyName:$companyName,notes:$notes){ success message } }",
  "variables":{"symbol":"MSFT","companyName":"Microsoft Corporation","notes":"Local test (Bearer)"}
}')
echo "$BEARER_RESPONSE"

# 5) Verify DB
echo -e "\n5️⃣ Verifying database..."
python3 manage.py shell -c "
from core.models import WatchlistItem
qs=WatchlistItem.objects.all()
print('Total watchlist items:', qs.count())
for i in qs:
    print(f'  - {i.stock.symbol} - {getattr(i.stock,\"company_name\",None)} - {i.added_at}')
"

# 6) Test results summary
echo -e "\n📊 Test Results Summary:"
echo "========================="

# Check JWT response
JWT_SUCCESS=$(echo "$JWT_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('data',{}).get('addToWatchlist',{}).get('success',False))" 2>/dev/null || echo "false")
if [ "$JWT_SUCCESS" = "true" ]; then
    echo "✅ JWT Authorization: SUCCESS"
else
    echo "❌ JWT Authorization: FAILED"
fi

# Check Bearer response  
BEARER_SUCCESS=$(echo "$BEARER_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('data',{}).get('addToWatchlist',{}).get('success',False))" 2>/dev/null || echo "false")
if [ "$BEARER_SUCCESS" = "true" ]; then
    echo "✅ Bearer Authorization: SUCCESS"
else
    echo "❌ Bearer Authorization: FAILED"
fi

echo -e "\n🎉 Test completed!"
echo "If both authorization methods work, your local environment is ready for production deployment!"
