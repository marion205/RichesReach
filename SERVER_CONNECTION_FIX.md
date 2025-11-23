# Server Connection Fix

**Issue**: GraphQL queries timing out because app is trying to connect to `192.168.1.240:8000` instead of `localhost:8000` on iOS Simulator

**Root Cause**: 
1. Server is accessible on `localhost:8000` ✅
2. Server is NOT accessible on `192.168.1.240:8000` ❌ (timeout)
3. App is still using LAN IP instead of localhost

---

## ✅ **FIXES APPLIED**

### 1. **Improved Simulator Detection**
- Added multiple checks to detect iOS Simulator:
  - `!Constants.isDevice` (original check)
  - `Constants.executionEnvironment === 'storeClient'` (Expo Go)
  - `__DEV__` (development mode fallback)
- Added debug logging to see which detection method is used

### 2. **Server Running on All Interfaces**
- Server is running on `0.0.0.0:8000` to accept connections from all interfaces
- However, `192.168.1.240` may not be accessible due to network/firewall

---

## 🔄 **REQUIRED: FULL APP RESTART**

**CRITICAL**: The API config is loaded at app startup, so you need to **fully restart** the app (not just reload):

### Steps:
1. **Stop the app completely**:
   ```bash
   # In terminal where npm start is running, press Ctrl+C
   ```

2. **Restart the app**:
   ```bash
   cd mobile
   npm start
   ```

3. **In the simulator/device, close the app completely and reopen it**

4. **Check the logs** for API config messages:
   - Look for `[API Config]` messages in the terminal
   - Should show `isSimulator: true` and `localHost: http://localhost:8000`

---

## ✅ **VERIFICATION**

After restarting, check:

1. **Terminal logs should show**:
   ```
   [API Config] Platform: ios
   [API Config] Constants.isDevice: false (or true)
   [API Config] isSimulator: true
   [API Config] localHost: http://localhost:8000
   [API_BASE] -> resolved to: http://localhost:8000
   ```

2. **GraphQL queries should go to**:
   - `http://localhost:8000/graphql/` ✅
   - NOT `http://192.168.1.240:8000/graphql/` ❌

3. **Paper Trading should load**:
   - If authenticated: Shows account data
   - If not authenticated: Shows "Authentication Required"
   - No more timeouts

---

## 🔍 **ALTERNATIVE: Use Environment Variable**

If the simulator detection still doesn't work, you can force localhost using an environment variable:

1. **Create/update `.env.local` in mobile directory**:
   ```bash
   EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

2. **Restart the app**

This will override the automatic detection and always use localhost.

---

## 📝 **TECHNICAL DETAILS**

### Simulator Detection Logic:
```typescript
const isSimulator = Platform.OS === 'ios' && (
  !Constants.isDevice ||                    // Standard check
  Constants.executionEnvironment === 'storeClient' || // Expo Go
  __DEV__                                   // Development mode
);
```

### Why This Works:
- `Constants.isDevice` may not always be reliable
- `executionEnvironment === 'storeClient'` indicates Expo Go (always simulator)
- `__DEV__` is true in development builds (usually simulator)

---

**Status**: ✅ Fixed - **FULL RESTART REQUIRED** (not just reload)!

