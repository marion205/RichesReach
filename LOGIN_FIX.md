# Fix "No Usable Data Found" - Login Required

## 🔍 Root Cause Identified

**GraphQL is working!** ✅
- Server responds correctly
- User data exists
- Queries return data when authenticated

**The Problem**: ⚠️
- App is **not authenticated** (no JWT token)
- GraphQL queries require authentication
- Without token → empty data → "no usable data found"

---

## ✅ Solution: Login First

### Step 1: Open Login Screen

1. **In the mobile app**, navigate to the **Login screen**
2. If you don't see it, the app might be showing a blank/home screen

### Step 2: Login with Test Credentials

**Credentials**:
- **Email**: `test@example.com`
- **Password**: `testpass123`

### Step 3: Verify Authentication

**After login, check Expo console for**:
```
🔐 Apollo Client: Adding Bearer token to request
🔐 Apollo Client: Token length: ...
```

**If you see**:
```
🔐 Apollo Client: No token found in AsyncStorage
```
→ Login didn't work, check login endpoint

---

## 🧪 Test Login Endpoint

**From terminal**:
```bash
curl -X POST http://192.168.1.240:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

**Expected Response**:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "1",
    "email": "test@example.com",
    "name": "Test User"
  }
}
```

**If this works** → Login endpoint is fine, app just needs to use it  
**If this fails** → Login endpoint issue, need to fix backend

---

## 🔧 Alternative: Check App State

### If Login Screen Doesn't Appear

The app might be:
1. **Stuck on home screen** (showing "no usable data")
2. **Auto-logged out** (token expired)
3. **Never logged in** (first time use)

**Force login**:
- Look for a "Login" or "Sign In" button
- Or navigate to login screen manually
- Or clear app data and restart

### Check Expo Console

**Look for**:
```
🔐 Apollo Client: No token found in AsyncStorage
```

**This confirms** → User is not logged in

---

## 📱 Quick Test

1. **Open app**
2. **Find login screen** (might be hidden behind "no data" message)
3. **Login with**: `test@example.com` / `testpass123`
4. **Check console** for token confirmation
5. **Data should load** after authentication

---

## 🎯 Expected Flow

1. **App loads** → Shows login screen OR home (if already logged in)
2. **User logs in** → Gets JWT token
3. **Token stored** → In AsyncStorage
4. **Queries made** → With Bearer token in header
5. **Data loads** → GraphQL returns user data

**If step 2 is skipped** → "No usable data found"

---

## ✅ Summary

**Status**: 
- ✅ Server working
- ✅ GraphQL working  
- ✅ User exists
- ⚠️ **App not authenticated**

**Fix**: **Login first!**

Use credentials:
- Email: `test@example.com`
- Password: `testpass123`

After login, data should load automatically! 🚀

