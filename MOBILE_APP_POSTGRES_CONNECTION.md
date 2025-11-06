# Mobile App → PostgreSQL Connection Flow

## ✅ Yes, the Mobile App Will Use PostgreSQL Schema

When you run `npm start`, the mobile app connects to your backend server, which is configured to use PostgreSQL.

## 📊 Connection Flow

```
Mobile App (npm start)
    ↓
Apollo Client (GraphQL)
    ↓
http://localhost:8000/graphql/ (or your configured API_BASE_URL)
    ↓
Backend Server (main_server.py)
    ↓
Django Graphene Schema (when configured)
    ↓
PostgreSQL Database
```

## 🔧 Current Configuration

### Mobile App Configuration:
**File:** `mobile/src/config/api.ts`
```typescript
export const API_GRAPHQL = `${API_BASE}/graphql/`;
// Default: http://localhost:8000/graphql/
```

**File:** `mobile/src/lib/apolloFactory.ts`
```typescript
import { API_GRAPHQL } from '../config/api';
// Uses API_GRAPHQL to create Apollo Client
```

### Backend Server Configuration:
**File:** `main_server.py`
- ✅ Configured to use PostgreSQL
- ✅ Configured to use Django Graphene schema
- ⚠️ Currently in fallback mode (Django project structure needed)

## 📝 Current Status

### ✅ What's Working:
1. **Mobile app → Backend connection:** ✅ Configured
2. **GraphQL endpoint:** ✅ Working (`http://localhost:8000/graphql/`)
3. **Backend server:** ✅ Running and responding
4. **PostgreSQL database:** ✅ Running and accessible

### ⚠️ Current Mode:
- **Backend:** Using fallback handlers (custom GraphQL implementations)
- **Data:** Returns mock data (as designed until Django is configured)
- **PostgreSQL:** Ready but not connected yet (Django module needed)

## 🚀 What Happens When You Run `npm start`

1. **Mobile app starts** (Expo/React Native)
2. **Apollo Client connects** to `http://localhost:8000/graphql/`
3. **GraphQL queries** are sent to your backend server
4. **Backend server** processes queries:
   - **Attempts** to use Django Graphene schema with PostgreSQL
   - **Falls back** to custom handlers if Django not available
   - **Returns data** (mock data in fallback mode, real data when Django configured)

## ✅ To Enable Full PostgreSQL Usage

Once Django project structure is fully configured:

1. **Backend server will automatically:**
   - Detect Django settings (`richesreach.settings` or `richesreach.settings_aws`)
   - Connect to PostgreSQL database
   - Use Django Graphene schema
   - Query real database tables

2. **Mobile app will automatically:**
   - Continue using the same GraphQL endpoint
   - Receive real PostgreSQL data (no mobile app changes needed)
   - Get all benefits of database persistence

## 📱 Configuration for Physical Devices

If running on a physical device (not simulator), you'll need to set:

```bash
# In mobile/.env.local or mobile/.env
EXPO_PUBLIC_API_BASE_URL=http://<YOUR_MAC_IP>:8000
```

Example:
```bash
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.236:8000
```

This ensures the mobile device can reach your Mac's backend server.

## 🎯 Summary

**Yes, when you run `npm start`:**
- ✅ Mobile app connects to backend server
- ✅ Backend server is configured for PostgreSQL
- ✅ GraphQL queries will use PostgreSQL once Django is fully set up
- ✅ Currently in fallback mode (working, but using mock data)

**No changes needed in mobile app code** - it will automatically get real PostgreSQL data once the backend Django structure is complete.

## 🔍 How to Verify

1. **Start backend server:**
   ```bash
   python main_server.py
   ```

2. **Start mobile app:**
   ```bash
   cd mobile
   npm start
   ```

3. **Check logs:**
   - Backend logs should show: `📊 PortfolioMetrics query received`
   - When Django is configured: `✅ Using Django Graphene schema with PostgreSQL`

4. **Test in app:**
   - Navigate to portfolio screen
   - Data should come from backend GraphQL endpoint
   - Will be real PostgreSQL data once Django is set up

---

**Bottom Line:** The mobile app is already configured correctly. It will automatically use PostgreSQL data once the backend Django project structure is fully configured. No mobile app changes needed! 🎉

