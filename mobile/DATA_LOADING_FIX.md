# "No Usable Data Found" - Fix Guide

## 🔍 Issue

The app loads but shows "no usable data found" - this means the app can't connect to the backend API.

## ✅ Quick Fixes

### Option 1: Use Production API (Recommended)

The app is trying to connect to `localhost:8000` by default, but you need to point it to production:

**Set Environment Variable**:
```bash
cd mobile
export EXPO_PUBLIC_API_BASE_URL=https://api.richesreach.com
npx expo start --clear
```

**Or create `.env` file in `mobile/` directory**:
```
EXPO_PUBLIC_API_BASE_URL=https://api.richesreach.com
```

### Option 2: Run Local Backend

If you want to use local backend:

```bash
# In one terminal
python3 main_server.py

# In another terminal
cd mobile
export EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
npx expo start --clear
```

**Note**: For physical devices, use your Mac's LAN IP instead of `localhost`:
```bash
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.XXX:8000
```

### Option 3: Check Current Configuration

The app logs the API URL on startup. Check the console for:
```
[API_BASE at runtime] ...
[API_BASE] ... -> resolved to: ...
```

---

## 🔧 Configuration Files

### Current API Config (`mobile/src/config/api.ts`)

The app uses this priority:
1. `EXPO_PUBLIC_API_BASE_URL` environment variable
2. `Constants.expoConfig?.extra?.API_BASE`
3. Defaults to `http://localhost:8000`

### GraphQL URL

Automatically set to: `${API_BASE}/graphql/`

---

## 🧪 Test API Connection

### Test Production API
```bash
curl https://api.richesreach.com/health/
```

Expected: `{"ok": true, "mode": "full", "production": true}`

### Test GraphQL
```bash
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

Expected: `{"data":{"__typename":"Query"}}`

---

## 📱 For Expo Go

**Expo Go** needs the API URL to be accessible from your device:

1. **Production API** (Recommended):
   ```bash
   export EXPO_PUBLIC_API_BASE_URL=https://api.richesreach.com
   ```

2. **Local Development** (Physical Device):
   - Find your Mac's IP: `ifconfig | grep "inet " | grep -v 127.0.0.1`
   - Use that IP: `export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.XXX:8000`
   - Make sure backend is running: `python3 main_server.py`

3. **Local Development** (Simulator):
   ```bash
   export EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

---

## 🚀 Quick Start

**For Production API**:
```bash
cd mobile
export EXPO_PUBLIC_API_BASE_URL=https://api.richesreach.com
npx expo start --clear
```

**For Local Backend**:
```bash
# Terminal 1: Start backend
python3 main_server.py

# Terminal 2: Start mobile app
cd mobile
export EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
npx expo start --clear
```

---

## ✅ Verification

After setting the API URL, check the console logs:
- `[API_BASE at runtime]` should show the correct URL
- `[ApolloFactory] Creating client with GraphQL URL:` should show the GraphQL endpoint
- No connection errors in console

---

## 🎯 Summary

**Problem**: App defaults to `localhost:8000` which isn't accessible

**Solution**: Set `EXPO_PUBLIC_API_BASE_URL` to production API or your local server

**Quick Fix**:
```bash
export EXPO_PUBLIC_API_BASE_URL=https://api.richesreach.com
npx expo start --clear
```

