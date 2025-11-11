# Monitor Expo Logs - Data Loading Debug

## 🔍 What to Watch For

After scanning QR code and app loads, watch Expo terminal for:

### ✅ Good Signs

**1. API Base URL Confirmation**:
```
[API_BASE at runtime] http://192.168.1.240:8000
[API_BASE] ... -> resolved to: http://192.168.1.240:8000
```

**2. Apollo Client Initialization**:
```
[ApolloFactory] Creating client with GraphQL URL: http://192.168.1.240:8000/graphql/
[ApolloProvider] Apollo client created successfully
```

**3. Authentication Status**:
```
🔐 Apollo Client: Adding Bearer token to request
🔐 Apollo Client: Token length: ...
```
OR (if not logged in):
```
🔐 Apollo Client: No token found in AsyncStorage
```

**4. GraphQL Queries**:
```
[GQL] GetMe (query) -> http://192.168.1.240:8000/graphql/
[GQL] GetPortfolioMetrics (query) -> http://192.168.1.240:8000/graphql/
```

**5. Successful Responses**:
```
✅ AI Recommendations Query Completed: ...
✅ User data loaded
```

### ⚠️ Bad Signs

**1. Missing API Base**:
```
[API_BASE at runtime] undefined
```
→ **Fix**: Check .env file

**2. Connection Errors**:
```
Network request failed
Fetch error: ...
CORS error
```
→ **Fix**: Check server is running, firewall, network

**3. Authentication Errors**:
```
🔐 Apollo Client: No token found
❌ Error loading user profile: ...
```
→ **Fix**: Login first

**4. Empty Data**:
```
[GQL] GetMe (query) -> ... (returns empty)
{"data":{},"errors":[]}
```
→ **Fix**: User not logged in or no data in database

**5. 404 Errors**:
```
404 Not Found
/graphql/ endpoint not found
```
→ **Fix**: Check server routes

---

## 📋 Quick Checklist

### Before Scanning QR

- [ ] `.env.local` or `.env` exists in `mobile/` directory
- [ ] `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000` is set
- [ ] Backend server is running (`python3 main_server.py`)
- [ ] Server responds: `curl http://192.168.1.240:8000/health/`

### After Scanning QR

- [ ] App loads (no crash)
- [ ] See `[API_BASE at runtime]` in logs
- [ ] See Apollo client initialization
- [ ] See GraphQL queries being made
- [ ] Check authentication status

---

## 🧪 Test Backend from Phone Browser

**On your phone** (same WiFi network):

1. **Health Check**:
   ```
   http://192.168.1.240:8000/health/
   ```
   Expected: `{"ok": true, "mode": "simple"}`

2. **GraphQL Test**:
   ```
   http://192.168.1.240:8000/graphql/
   ```
   (This won't work in browser - needs POST request)

3. **If health works but app doesn't**:
   - Network issue between phone and Mac
   - Firewall blocking
   - Wrong WiFi network

---

## 🔧 Common Fixes

### Fix 1: Missing .env File

```bash
cd mobile
echo "EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000" > .env.local
npx expo start --clear
```

### Fix 2: Wrong API URL

```bash
cd mobile
cat .env.local
# Should show: EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
# If wrong, fix it:
echo "EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000" > .env.local
npx expo start --clear
```

### Fix 3: Server Not Running

```bash
# Check if running
ps aux | grep main_server.py

# If not, start it:
cd /Users/marioncollins/RichesReach
python3 main_server.py
```

### Fix 4: User Not Logged In

**Login credentials**:
- Email: `test@example.com`
- Password: `testpass123`

After login, check for:
```
🔐 Apollo Client: Adding Bearer token
```

---

## 📸 What to Share

If still stuck, share:

1. **Expo terminal output** (after app loads):
   - Copy/paste the logs
   - Especially lines with `[API_BASE]`, `[GQL]`, `🔐`, errors

2. **Phone browser test**:
   - Screenshot or result of `http://192.168.1.240:8000/health/`

3. **App behavior**:
   - Does app load?
   - Does login screen appear?
   - What error message (if any)?

---

## 🎯 Expected Flow

1. **App loads** → Shows login screen or home
2. **API connects** → Logs show `[API_BASE at runtime]`
3. **User logs in** → Token stored, queries start
4. **Data loads** → GraphQL queries return data
5. **UI updates** → App shows data

**If step 2 fails** → Env/config issue  
**If step 3 fails** → Need to login  
**If step 4 fails** → Backend/data issue  

---

**Ready to monitor!** Scan QR and watch the logs! 🔍

