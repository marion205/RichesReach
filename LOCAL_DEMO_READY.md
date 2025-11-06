# ✅ Local Demo Ready - PostgreSQL with Production Schema

## 🎯 Configuration Summary

**Everything is configured for local demo with local PostgreSQL:**

### ✅ Database:
- **Name:** `richesreach`
- **Host:** `localhost`
- **Port:** `5432`
- **User:** Your local user (no password for local)
- **Status:** ✅ Running and accessible

### ✅ Backend Server:
- **Configured:** Uses local PostgreSQL
- **GraphQL Endpoint:** `http://localhost:8000/graphql/`
- **Schema:** Production schema (when Django configured)
- **Database:** Local `richesreach` database

### ✅ Mobile App:
- **Connects to:** `http://localhost:8000/graphql/`
- **For Simulator:** Uses `localhost` (works automatically)
- **For Physical Device:** Set `EXPO_PUBLIC_API_BASE_URL` to your Mac's LAN IP

## 🚀 Quick Start

### Option 1: Use the Start Script
```bash
./START_LOCAL_DEMO.sh
```

### Option 2: Manual Start
```bash
# Terminal 1: Start Backend
cd /Users/marioncollins/RichesReach
source .venv/bin/activate
export DB_NAME=richesreach DB_USER=$(whoami) DB_HOST=localhost DB_PORT=5432
python main_server.py

# Terminal 2: Start Mobile App
cd mobile
npm start
```

## 📊 What Happens

1. **Backend Server:**
   - Connects to local PostgreSQL (`richesreach` on `localhost:5432`)
   - Uses production GraphQL schema
   - Serves at `http://localhost:8000/graphql/`

2. **Mobile App:**
   - Connects to `http://localhost:8000/graphql/`
   - Queries go to local PostgreSQL database
   - Gets real data from local database

3. **Data Flow:**
   ```
   Mobile App → localhost:8000/graphql/ → Backend → Local PostgreSQL (richesreach)
   ```

## 🔍 Verification

### Check Database:
```bash
psql -d richesreach -c "SELECT current_database(), version();"
```

### Check Server Logs:
Look for:
```
📊 Using Django settings with local PostgreSQL: richesreach.settings
📊 Local PostgreSQL config: DB_NAME=richesreach, DB_HOST=localhost
✅ Django initialized with database: richesreach on localhost
✅ Using Django Graphene schema with PostgreSQL
```

### Test GraphQL:
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ portfolioMetrics { totalValue } }"}'
```

## 📱 For Physical Devices

If running on a physical device (not simulator), create `mobile/.env.local`:

```bash
EXPO_PUBLIC_API_BASE_URL=http://<YOUR_MAC_IP>:8000
```

To find your Mac's IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

## ✅ Summary

**Everything is configured for local demo:**
- ✅ Local PostgreSQL database: `richesreach`
- ✅ Backend uses local database
- ✅ Production schema will be used
- ✅ Mobile app connects to localhost
- ✅ All running locally - no external dependencies

**Ready for demo!** 🚀

The backend server will automatically:
1. Detect local PostgreSQL
2. Use production GraphQL schema
3. Connect to `richesreach` database on `localhost`
4. Serve GraphQL at `http://localhost:8000/graphql/`

No additional configuration needed!

