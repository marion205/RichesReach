# How to Access RichesReach App

**Date**: November 10, 2024

---

## 🚀 Production API (Backend)

### Health Endpoint
```bash
curl https://api.richesreach.com/health/
# or
curl http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/health/
```

**Expected Response**: `{"ok": true, "mode": "full", "production": true}`

### GraphQL Endpoint
```bash
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

**Expected Response**: `{"data":{"__typename":"Query"}}`

### Direct URLs
- **API Base**: `https://api.richesreach.com`
- **Health**: `https://api.richesreach.com/health/`
- **GraphQL**: `https://api.richesreach.com/graphql/`
- **ALB Direct**: `http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com`

---

## 📱 Mobile App Access

### Option 1: Expo Go (Development)

**If using Expo Go**:
```bash
cd mobile
npm start
# or
expo start
```

Then:
1. Scan QR code with Expo Go app (iOS/Android)
2. App will load in Expo Go

### Option 2: Development Build

**If you have a development build**:
```bash
cd mobile
npm run start:dev
```

### Option 3: Production Build

**If app is built and deployed**:
- **iOS**: Check App Store or TestFlight
- **Android**: Check Play Store or APK distribution

### Option 4: Local Development

**Run locally**:
```bash
cd mobile
npm start
# Choose: iOS simulator, Android emulator, or Expo Go
```

---

## 🖥️ Local Backend Server

### Start Local Server

**If you want to run backend locally**:
```bash
cd /Users/marioncollins/RichesReach
python3 main_server.py
```

**Server will run on**: `http://localhost:8000`

**Endpoints**:
- Health: `http://localhost:8000/health/`
- GraphQL: `http://localhost:8000/graphql/`

**Note**: Local server uses local database/SQLite, not production RDS.

---

## 🌐 Web Access (If Available)

**Check if web version exists**:
- Frontend URL: `https://app.richesreach.com` (if deployed)
- Or check for React web app in codebase

---

## 📊 Quick Access Summary

| Access Type | URL/Command | Status |
|-------------|------------|--------|
| **Production API** | `https://api.richesreach.com` | ✅ Live |
| **Health Check** | `https://api.richesreach.com/health/` | ✅ Working |
| **GraphQL** | `https://api.richesreach.com/graphql/` | ✅ Working |
| **Local Server** | `python3 main_server.py` | ⚠️ Run if needed |
| **Mobile App** | `cd mobile && npm start` | ⚠️ Run if needed |

---

## 🔍 Check What's Running

### Check Production API
```bash
curl https://api.richesreach.com/health/
```

### Check Local Server
```bash
ps aux | grep main_server.py
# or
lsof -i :8000
```

### Check Mobile App
```bash
cd mobile
npm start
# Check Expo/React Native status
```

---

## 🎯 Recommended Access Method

### For Testing/Development:
1. **Backend**: Use production API (`https://api.richesreach.com`)
2. **Mobile**: Run locally with `cd mobile && npm start`

### For Production Use:
1. **Backend**: Already deployed and accessible
2. **Mobile**: Use production build (if deployed to app stores)

---

## Quick Start Commands

### Test Production API
```bash
# Health check
curl https://api.richesreach.com/health/

# GraphQL test
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

### Start Mobile App Locally
```bash
cd mobile
npm start
# Then choose: iOS, Android, or Expo Go
```

### Start Backend Locally
```bash
python3 main_server.py
# Access at http://localhost:8000
```

---

**Status**: Production API is live and accessible! 🚀

