# RichesReach Server Configuration

## Consolidated Setup

We now have **2 clean server configurations** instead of the previous 8+ scattered settings files:

### 🏠 **Local Development** (`settings_local.py`)
**Use this for daily development and testing**

**Features:**
- ✅ Production database schema (local PostgreSQL)
- ✅ Real market data providers (Alpha Vantage, Polygon, Finnhub)
- ✅ Real JWT authentication
- ✅ Real AI/ML services
- ✅ Mock fallbacks for portfolio/broker data (ensures functionality)
- ✅ GraphiQL enabled for testing
- ✅ Debug mode enabled
- ✅ CORS enabled for mobile app

**Start Command:**
```bash
./start_local.sh
```

**Or manually:**
```bash
export DJANGO_SETTINGS_MODULE=richesreach.settings_local
python3 manage.py runserver 0.0.0.0:8000
```

### 🚀 **Production** (`settings_production_clean.py`)
**Use this for production deployment**

**Features:**
- ✅ All real services (no mocks)
- ✅ Production security settings
- ✅ SSL/HTTPS enabled
- ✅ Production database
- ✅ All external services enabled
- ✅ GraphiQL disabled
- ✅ Debug mode disabled

**Start Command:**
```bash
./start_production.sh
```

**Or manually:**
```bash
export DJANGO_SETTINGS_MODULE=richesreach.settings_production_clean
python3 manage.py runserver 0.0.0.0:8000
```

## 🗑️ **Removed/Consolidated Files**

The following settings files have been consolidated and are no longer needed:
- `settings_dev.py` → Merged into `settings_local.py`
- `settings_dev_real.py` → Merged into `settings_local.py`
- `settings_local_db.py` → Merged into `settings_local.py`
- `settings_local_prod.py` → Merged into `settings_local.py`
- `settings_aws.py` → Merged into `settings_production_clean.py`
- `settings_secure_production.py` → Merged into `settings_production_clean.py`

## 📊 **Current Status**

**Local Development Server:** ✅ Running with `settings_local.py`
- Database: Local PostgreSQL with production schema
- Market Data: Real providers (Alpha Vantage, Polygon, Finnhub)
- Authentication: Real JWT
- AI Services: Real with fallbacks
- Portfolio Data: Mock fallbacks for reliability

## 🔧 **Environment Variables**

Make sure you have these in your `.env` file:
```bash
# Market Data APIs
ALPHA_VANTAGE_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# AI Services
OPENAI_API_KEY=your_key_here

# Database (for production)
DJANGO_DB_NAME=appdb
DJANGO_DB_USER=postgres
DJANGO_DB_PASSWORD=your_password
DJANGO_DB_HOST=your_host
DJANGO_DB_PORT=5432
```

## 🎯 **Benefits of This Setup**

1. **Simplified**: Only 2 configurations instead of 8+
2. **Clear Purpose**: Local vs Production, no confusion
3. **Real Data**: Local development uses real market data
4. **Reliable**: Mock fallbacks ensure portfolio features work
5. **Production-Ready**: Easy to deploy with production settings
6. **Maintainable**: Single source of truth for each environment
