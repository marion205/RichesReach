# 🚀 RichesReach Development Setup Guide

## ✅ **Current Working Configuration (ALWAYS USE THIS)**

This guide ensures you always use the correct setup that's been tested and working.

### 🎯 **Quick Start (Production Backend)**

```bash
# 1. Start the Production Backend (RECOMMENDED)
cd backend
source .venv/bin/activate
PORT=8000 python3 final_complete_server.py

# 2. Start the Rust Engine (in separate terminal)
cd rust_crypto_engine
cargo run --release -- --port 3002

# 3. Start Mobile App (in separate terminal)
cd mobile
npm start
```

### 🔑 **Test Credentials**
- **Email**: `test@example.com`
- **Password**: `password123`

### 🌐 **Service URLs**
- **Backend**: `http://127.0.0.1:8000` (Full production server with all features)
- **Rust Engine**: `http://127.0.0.1:3002` (Crypto analysis engine)
- **GraphQL**: `http://127.0.0.1:8000/graphql`

---

## 📋 **Complete Setup Instructions**

### 1. **Backend Setup**

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip wheel
pip install -r requirements.txt

# Environment configuration (already created)
# .env.local contains all necessary environment variables

# Start production server
PORT=8000 python3 final_complete_server.py
```

### 2. **Rust Engine Setup**

```bash
cd rust_crypto_engine

# Start on port 3002 (to avoid conflicts)
cargo run --release -- --port 3002
```

### 3. **Mobile App Setup**

```bash
cd mobile

# Install dependencies
npm install

# Start development server
npm start
```

---

## 🔧 **Configuration Files**

### **Backend Configuration**
- **`.env.local`**: Environment variables for local development
- **`docker-compose.dev.yml`**: Local infrastructure (Postgres/Redis) - optional
- **`final_complete_server.py`**: Main production server with all GraphQL resolvers

### **Mobile App Configuration**
- **`mobile/src/config.ts`**: API base URL configuration
- **`mobile/src/ApolloProvider.tsx`**: GraphQL client configuration
- **`mobile/src/graphql/auth.ts`**: Authentication mutations

---

## 🚨 **Important Notes**

### ✅ **DO THIS:**
1. **Always use `final_complete_server.py`** - it has all the GraphQL resolvers
2. **Use port 8000** for the backend to match mobile app configuration
3. **Use port 3002** for Rust engine to avoid conflicts
4. **Test with `test@example.com` / `password123`** credentials
5. **Check `mobile/src/config.ts`** is set to `IOS_SIM` for local development

### ❌ **DON'T DO THIS:**
1. **Don't use `quick_test_server.py`** for production - it's missing most resolvers
2. **Don't change the test user password** without updating both backend and mobile app
3. **Don't use port 8000** for Rust engine (conflicts with backend)
4. **Don't forget to restart servers** after making configuration changes

---

## 🐛 **Troubleshooting**

### **Authentication Issues**
```bash
# Check if backend is running
curl http://127.0.0.1:8000/health

# Test authentication
curl -H 'content-type: application/json' \
  -d '{"query":"mutation TokenAuth($email: String!, $password: String!) { tokenAuth(email: $email, password: $password) { token } }", "variables": {"email": "test@example.com", "password": "password123"}}' \
  http://127.0.0.1:8000/graphql
```

### **Mobile App Issues**
1. **Check `mobile/src/config.ts`** - should be `export const API_BASE = IOS_SIM;`
2. **Reload mobile app** - press `r` in Expo terminal
3. **Check console logs** - look for authentication and GraphQL errors

### **Backend Issues**
1. **Check port conflicts** - `lsof -i :8000` to see what's using port 8000
2. **Restart backend** - `pkill -f final_complete_server && PORT=8000 python3 final_complete_server.py`
3. **Check environment** - ensure `.env.local` exists and is loaded

---

## 📊 **Available Features**

With this setup, your mobile app has access to:

### **✅ Authentication**
- Login/Signup with JWT tokens
- User profiles and premium access
- Secure token management

### **✅ Crypto Features**
- Supported currencies (BTC, ETH, SOL, etc.)
- Real-time crypto prices
- ML-powered crypto signals
- Crypto portfolio management

### **✅ Stock Features**
- AI-powered stock screening
- Portfolio metrics and analytics
- Trading account management
- Watchlist functionality

### **✅ Social Features**
- Stock discussions
- Social feed
- User interactions

### **✅ Advanced Features**
- Risk assessment
- Asset allocation recommendations
- Market outlook analysis
- Rebalancing suggestions

---

## 🔄 **Development Workflow**

### **Making Changes**
1. **Backend changes**: Edit `final_complete_server.py`, restart server
2. **Mobile changes**: Edit React Native files, reload app with `r`
3. **Rust changes**: Edit Rust files, restart with `cargo run --release -- --port 3002`

### **Testing**
1. **Test authentication** with provided credentials
2. **Test GraphQL queries** using curl or mobile app
3. **Check console logs** for any errors
4. **Verify all features** are working as expected

### **Deployment**
1. **Commit changes** to git
2. **Push to GitHub** with descriptive commit messages
3. **Update this guide** if configuration changes

---

## 📝 **Commit Message Template**

```bash
git commit -m "🚀 [Feature/Component]: Brief description

✅ What was added/changed:
- Specific changes made
- Files modified
- Features implemented

🎯 Result: What this achieves
Test: How to verify it works"
```

---

## 🎉 **Success Indicators**

You know everything is working when:
- ✅ Backend responds to `http://127.0.0.1:8000/health`
- ✅ Mobile app successfully logs in with test credentials
- ✅ All GraphQL queries return data (no 404s or missing fields)
- ✅ Console shows successful authentication and data loading
- ✅ Mobile app navigates to main screen after login

---

**Last Updated**: 2025-09-22
**Status**: ✅ Fully Working
**Tested By**: Development Team
