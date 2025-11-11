# Comprehensive Debug Guide - "No Usable Data Found"

## 🎯 Quick Debug Script

**Run this to check everything**:
```bash
cd /Users/marioncollins/RichesReach
./DEBUG_DATA_ISSUE.sh
```

This will check:
- ✅ Environment configuration
- ✅ Backend connectivity
- ✅ GraphQL endpoints
- ✅ Server status
- ✅ Recent logs
- ✅ Network configuration
- ✅ Database users

---

## 📋 Manual Debug Steps

### Step 1: Capture Expo Logs

**After scanning QR and app loads**, copy-paste from Expo terminal:

**Look for**:
```
[API_BASE] ... -> resolved to: http://192.168.1.240:8000
🔧 API Configuration: { API_HTTP: '...', API_GRAPHQL: '...' }
[ApolloFactory] Creating client with GraphQL URL: ...
[GQL] GetMe (query) -> ...
🔐 Apollo Client: ...
```

**Share**: All logs from `[API_BASE]` onward

---

### Step 2: Monitor Backend Logs

**In a new terminal**:
```bash
tail -f /tmp/richesreach_server.log | grep "192.168.1.240"
```

**Then**:
1. Scan QR code
2. Interact with app (try to load data)
3. Watch for incoming requests

**Look for**:
- `POST /graphql/` requests
- GraphQL query names (GetMe, GetPortfolioMetrics, etc.)
- Error responses (401, 403, 500)
- Empty data responses

**Share**: 5-10 relevant lines

---

### Step 3: Test from Phone Browser

**On your phone** (same WiFi):

1. **Health Check**:
   ```
   http://192.168.1.240:8000/health/
   ```
   **Expected**: `{"ok": true, "mode": "simple"}`

2. **If health works but app doesn't**:
   - Network issue between phone and Mac
   - Firewall blocking
   - Wrong WiFi network

**Share**: Screenshot or result

---

### Step 4: Test GraphQL Playground

**On Mac browser**:
```
http://localhost:8000/graphql/
```

**Or use curl**:
```bash
# Test without auth
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ me { id email } }"}'

# Should return empty or error (no auth)
```

**Then test with auth** (if you have a token):
```bash
# Get token first (if login endpoint works)
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}' | jq -r '.token')

# Test with token
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "{ me { id email } }"}'
```

**Share**: Results of both tests

---

### Step 5: Check Token in App

**Add temporary debug code** to check token:

**In mobile app** (e.g., `mobile/src/App.tsx` or wherever data is fetched):

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Add this in a useEffect or component
useEffect(() => {
  const checkToken = async () => {
    const token = await AsyncStorage.getItem('token');
    const authToken = await AsyncStorage.getItem('authToken');
    console.log('[TOKEN CHECK] token:', token ? 'Present' : 'Missing');
    console.log('[TOKEN CHECK] authToken:', authToken ? 'Present' : 'Missing');
    console.log('[TOKEN CHECK] All keys:', await AsyncStorage.getAllKeys());
  };
  checkToken();
}, []);
```

**Restart Expo**, rescan QR, check console for token logs.

**Share**: Token check results

---

## 🔍 Likely Culprits & Fixes

| Symptom | Probable Cause | Quick Fix |
|---------|---------------|-----------|
| **No `[API_BASE]` log** | Env not loading | `cd mobile && rm -rf node_modules/.cache && npx expo start --clear` |
| **No token found** | Skipped login | Force login flow or check login screen |
| **Network request failed** | CORS/network | Check firewall, same WiFi, or use tunnel mode |
| **Empty `{"data":{}}`** | No data for user | Login first, or seed test data |
| **Logs show query but error** | GraphQL schema mismatch | Check backend logs for query errors |
| **401/403 errors** | Authentication failed | Login again, check token validity |

---

## 🧪 Quick Tests

### Test 1: Environment Loading
```bash
cd mobile
cat .env.local
# Should show: EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
```

### Test 2: Backend Health
```bash
curl http://192.168.1.240:8000/health/
# Should return: {"ok": true, "mode": "simple"}
```

### Test 3: GraphQL Basic
```bash
curl -X POST http://192.168.1.240:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
# Should return: {"data":{"__typename":"Query"}}
```

### Test 4: GraphQL with Auth
```bash
# First get token (if login works)
curl -X POST http://192.168.1.240:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Then use token in GraphQL query
curl -X POST http://192.168.1.240:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "{ me { id email } }"}'
```

---

## 📸 What to Share

**Please share**:

1. **Expo terminal logs** (after app loads):
   - Copy-paste from `[API_BASE]` onward
   - Include any errors or GraphQL lines

2. **Backend logs** (5-10 lines):
   - From `tail -f /tmp/richesreach_server.log`
   - Show incoming requests when app loads

3. **Phone browser test**:
   - Result of `http://192.168.1.240:8000/health/`
   - Screenshot or text

4. **App behavior**:
   - Does login screen appear?
   - What error message (if any)?
   - Does it show spinner or blank screen?

5. **Token check** (if you added the debug code):
   - Results from `[TOKEN CHECK]` logs

---

## 🎯 Expected Flow

1. **App loads** → Shows login screen OR home
2. **API connects** → Logs show `[API_BASE at runtime]`
3. **User logs in** → Token stored, queries start
4. **Data loads** → GraphQL queries return data
5. **UI updates** → App shows data

**If step 2 fails** → Env/config issue  
**If step 3 fails** → Need to login  
**If step 4 fails** → Backend/data issue  

---

## 🚀 Quick Fixes

### Fix 1: Clear Cache & Restart
```bash
cd mobile
rm -rf node_modules/.cache
npx expo start --clear
```

### Fix 2: Verify .env
```bash
cd mobile
echo "EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000" > .env.local
npx expo start --clear
```

### Fix 3: Use Tunnel Mode (if network issues)
```bash
cd mobile
npx expo start --tunnel
```

### Fix 4: Force Login
- Navigate to login screen manually
- Login with: `test@example.com` / `testpass123`
- Check console for token confirmation

---

**Run the debug script and share the results!** 🔍

