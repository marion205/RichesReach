# Backend Bootstrap - Quick Reference

## 🚀 First Time Setup

```bash
# From repo root
./bootstrap_backend.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Run migrations
- ✅ Optionally start server

## 📡 Daily Use

```bash
# From repo root
./start_django_backend.sh
```

Auto-bootstraps if needed, then starts the server.

## 📋 What Was Created

1. **`bootstrap_backend.sh`** - Full bootstrap script
   - Creates venv if missing
   - Installs deps only if Django is missing
   - Checks for ML dependencies
   - Runs migrations
   - Optionally starts server

2. **`start_django_backend.sh`** - Quick start script
   - Auto-bootstraps if needed
   - Checks migrations
   - Starts server

3. **`setup_day_trading.sh`** - Day trading setup
4. **`verify_day_trading.sh`** - Day trading verification

## 🎯 After Bootstrap

1. **Generate signals** (GraphQL Playground: http://localhost:8000/graphql):
   ```graphql
   query {
     dayTradingPicks(mode: "SAFE") {
       picks { symbol side score }
     }
   }
   ```

2. **Verify signals**:
   ```bash
   ./verify_day_trading.sh
   ```

3. **Query stats**:
   ```graphql
   query {
     dayTradingStats(period: "ALL_TIME") {
       mode
       winRate
       sharpeRatio
       maxDrawdown
     }
   }
   ```

## 📚 Full Documentation

See `docs/features/day-trading/BOOTSTRAP_GUIDE.md` for complete details.

