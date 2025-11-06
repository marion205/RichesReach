# 🚀 Start Server Guide

## Quick Start

### 1. Activate Virtual Environment
```bash
cd /Users/marioncollins/RichesReach
source .venv/bin/activate
```

### 2. Set Environment Variables (Optional - auto-detected)
```bash
export DB_NAME=richesreach
export DB_USER=$(whoami)
export DB_HOST=localhost
export DB_PORT=5432
export DJANGO_SETTINGS_MODULE=richesreach.settings
```

### 3. Start Server
```bash
python main_server.py
```

## ✅ Current Status

### Server Status: ✅ **RUNNING**
- Server is accessible on `http://localhost:8000`
- Health endpoint: ✅ Working
- GraphQL endpoint: ✅ Working

### PostgreSQL Status: ✅ **READY**
- PostgreSQL 14 running on `localhost:5432`
- Database `richesreach` exists
- Connection test: ✅ Successful

### GraphQL Status: ⚠️ **FALLBACK MODE**
- GraphQL endpoint responds to queries
- Currently using fallback handlers (custom implementations)
- Returns mock data (as designed when Django not fully connected)
- Will switch to PostgreSQL + Django schema once Django project is fully configured

## 📊 Test the Server

### Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"ok","schemaVersion":"1.0.0","timestamp":"..."}
```

### GraphQL Query
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ portfolioMetrics { totalValue totalReturn totalReturnPercent } }"}'
```

**Expected Response:**
```json
{
  "data": {
    "portfolioMetrics": {
      "totalValue": 14303.52,
      "totalReturn": 2303.52,
      "totalReturnPercent": 19.2,
      ...
    }
  }
}
```

## 📝 Server Logs

When the server starts, you should see:

```
🚀 Starting RichesReach Main Server...
📡 Available endpoints:
   • GET /health - Health check
   • POST /graphql/ - GraphQL endpoint
🌐 Server running on http://localhost:8000
📊 GraphQL Playground: http://localhost:8000/graphql
```

**Current Status:**
- ⚠️ Django setup: Attempting initialization (may need Django project structure)
- ✅ GraphQL endpoint: Working (fallback mode)
- ✅ Health endpoint: Working
- ✅ Server: Running and accessible

## 🔄 To Enable Full PostgreSQL + GraphQL

Once Django project structure is in place:
1. The server will automatically detect `richesreach.settings`
2. Connect to PostgreSQL database
3. Use Django Graphene schema
4. Logs will show:
   ```
   📊 Using production settings: richesreach.settings
   ✅ Django initialized with database: richesreach on localhost
   ✅ Using Django Graphene schema with PostgreSQL
   ```

## 🎯 Summary

✅ **Server is running and ready**
✅ **PostgreSQL is configured and accessible**
✅ **GraphQL endpoint is working**
⚠️ **Django connection pending** (needs Django project structure)

The server is operational and will automatically upgrade to full PostgreSQL + GraphQL mode once Django is fully configured!

