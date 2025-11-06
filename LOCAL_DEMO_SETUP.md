# Local Demo Setup - PostgreSQL with Production Schema

## ✅ Configuration for Local Demo

### Current Setup:
- ✅ **PostgreSQL Database:** `richesreach` on `localhost:5432`
- ✅ **Backend Server:** Configured to use local PostgreSQL
- ✅ **Mobile App:** Connects to `http://localhost:8000/graphql/`
- ✅ **Production Schema:** Will be used when Django is configured

## 🔧 Configuration Details

### Backend Server (`main_server.py`):
- Automatically detects Django settings
- Tries: `richesreach.settings_aws` → `richesreach.settings` → `richesreach.settings_local`
- Uses local PostgreSQL database: `richesreach` on `localhost:5432`

### Database Configuration:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'richesreach',        # Local database
        'USER': 'marioncollins',      # Your local user
        'PASSWORD': '',               # No password for local
        'HOST': 'localhost',          # Local PostgreSQL
        'PORT': '5432',               # Default PostgreSQL port
    }
}
```

### Mobile App Configuration:
**File:** `mobile/src/config/api.ts`
```typescript
// Default: http://localhost:8000 (for iOS Simulator)
// For physical devices: Use LAN IP
export const API_GRAPHQL = `${API_BASE}/graphql/`;
```

## 🚀 Running the Demo

### 1. Start Backend Server:
```bash
cd /Users/marioncollins/RichesReach
source .venv/bin/activate
export DB_NAME=richesreach DB_USER=$(whoami) DB_HOST=localhost DB_PORT=5432
python main_server.py
```

### 2. Start Mobile App:
```bash
cd mobile
npm start
```

### 3. For Physical Devices:
If using a physical device, set in `mobile/.env.local`:
```bash
EXPO_PUBLIC_API_BASE_URL=http://<YOUR_MAC_IP>:8000
```

## 📊 What Happens

1. **Backend Server:**
   - Connects to local PostgreSQL (`richesreach` database)
   - Uses production GraphQL schema (when Django configured)
   - Serves GraphQL at `http://localhost:8000/graphql/`

2. **Mobile App:**
   - Connects to `http://localhost:8000/graphql/`
   - Sends GraphQL queries
   - Receives data from local PostgreSQL database

3. **Data Flow:**
   ```
   Mobile App → http://localhost:8000/graphql/ → Backend → Local PostgreSQL (richesreach)
   ```

## ✅ Verification

### Check Database:
```bash
psql -d richesreach -c "SELECT current_database(), version();"
```

### Check Server Logs:
Look for:
```
📊 Using Django settings: richesreach.settings
✅ Django initialized with database: richesreach on localhost
✅ Using Django Graphene schema with PostgreSQL
```

### Test GraphQL:
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ portfolioMetrics { totalValue } }"}'
```

## 🎯 Summary

**Everything is configured for local demo:**
- ✅ Local PostgreSQL database: `richesreach`
- ✅ Backend uses local database
- ✅ Mobile app connects to localhost
- ✅ Production schema will be used
- ✅ All running locally - no external dependencies

**Ready for demo!** 🚀

