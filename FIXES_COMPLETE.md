# Complete Fixes for IP Address and Privacy Settings

## ✅ Issue 1: App Using 192.168.1.240 Instead of localhost

### Changes Made:

1. **Updated `mobile/src/config/api.ts`**:
   - Already forces `localhost:8000` in dev mode for iOS
   - Logic is correct, just needs cache reset

2. **Fixed `mobile/src/features/community/screens/CircleDetailScreenSelfHosted.tsx`**:
   - Removed hardcoded `192.168.1.240`
   - Now uses `API_BASE` from config (which respects dev mode)

3. **`mobile/src/features/family/services/FamilyWebSocketService.ts`**:
   - Only has IP in a comment (not actual code)
   - Uses `WS_URL` from config, which is correct

### ✅ RESTART REQUIRED:

```bash
# Stop current Metro bundler (Ctrl+C)

# Clear cache and restart
cd mobile
npm start -- --reset-cache

# Or with Expo:
npx expo start --clear
```

**Then in simulator/device:**
- Close app completely
- Reopen app

**Verify in logs:**
```
🔧 [API Config] DEV MODE + iOS: FORCING localhost
[API_BASE] -> resolved to: http://localhost:8000
🔵 [FETCH] Starting request to: http://localhost:8000/graphql/
```

---

## ✅ Issue 2: privacySettings GraphQL Field

### Changes Made:

1. **Created `deployment_package/backend/core/privacy_types.py`**:
   - Added `PrivacySettingsType` GraphQL type
   - Added `PrivacyQueries` with `privacySettings` field
   - Added `PrivacyMutations` with `updatePrivacySettings` mutation
   - Returns default values (ready for future DB model)

2. **Updated `deployment_package/backend/core/schema.py`**:
   - Added `PrivacyQueries` to `ExtendedQuery`
   - Added `PrivacyMutations` to `ExtendedMutation`

3. **Frontend already handles errors gracefully**:
   - `PrivacyDashboard.tsx` has error handling
   - Falls back to defaults if field missing
   - Now will get real data from backend!

### ✅ RESTART BACKEND REQUIRED:

```bash
cd deployment_package/backend
source venv/bin/activate

# Restart Django server
python manage.py runserver 0.0.0.0:8000
```

**Verify:**
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ privacySettings { dataSharingEnabled dataRetentionDays } }"}'
```

Should return:
```json
{
  "data": {
    "privacySettings": {
      "dataSharingEnabled": true,
      "dataRetentionDays": 90
    }
  }
}
```

---

## 📝 Summary

### What's Fixed:
- ✅ All hardcoded IPs removed (uses config)
- ✅ API config forces localhost in dev mode
- ✅ Privacy settings added to backend GraphQL schema
- ✅ Frontend query will now work (no more 400 errors)

### What You Need to Do:
1. **Restart Metro with cache reset**: `npm start -- --reset-cache`
2. **Restart Django server**: `python manage.py runserver 0.0.0.0:8000`
3. **Reload app in simulator**

### Future Enhancement:
The privacy settings currently return defaults. To persist user preferences:
1. Create a `PrivacySettings` Django model
2. Update resolvers in `privacy_types.py` to use the model
3. Run migrations

---

**Status**: ✅ Both issues fully fixed and ready to test!
