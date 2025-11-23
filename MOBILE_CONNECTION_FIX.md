# Mobile App Connection Fix

**Issue**: Paper Trading screen shows "Loading..." and GraphQL queries timeout

**Root Cause**: Mobile app was trying to connect to `192.168.1.240:8000` but server was only accessible on `localhost:8000`

---

## ✅ **FIX APPLIED**

Updated `mobile/src/config/api.ts` to:
- Use `localhost:8000` for **iOS Simulator** (which you're using)
- Use `192.168.1.240:8000` for **physical devices**

---

## 🔄 **RELOAD REQUIRED**

After this change, you need to **reload the mobile app**:

### Option 1: Quick Reload
- In the terminal where `npm start` is running, press **`r`** to reload
- Or shake the device/simulator and select **"Reload"**

### Option 2: Full Restart
```bash
# Stop the app (Ctrl+C in terminal)
cd mobile
npm start
```

---

## ✅ **VERIFICATION**

After reloading, the Paper Trading screen should:
1. ✅ Connect to `localhost:8000` (for simulator)
2. ✅ Load account data successfully
3. ✅ Show account balance and positions
4. ✅ No more timeout errors

---

## 🔍 **If Still Timing Out**

If you still see timeouts after reload:

1. **Check server is running**:
   ```bash
   curl http://localhost:8000/graphql/ -X POST -H "Content-Type: application/json" -d '{"query": "{ __typename }"}'
   ```

2. **Check server logs** for errors

3. **Verify authentication** - Paper Trading queries require user to be logged in

---

**Status**: ✅ Fixed - Reload app to see changes!

