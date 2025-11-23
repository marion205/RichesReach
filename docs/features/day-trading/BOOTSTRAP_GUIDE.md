# Backend Bootstrap Guide

## Quick Start

### First Time Setup

```bash
# From repo root
./bootstrap_backend.sh
```

This script will:
1. ✅ Create virtual environment if missing
2. ✅ Activate it
3. ✅ Install dependencies (only if Django is missing)
4. ✅ Check for ML dependencies (optional)
5. ✅ Run migrations
6. ✅ Optionally start the server

### Daily Use

After the first bootstrap, just use:

```bash
# From repo root
./start_django_backend.sh
```

This will:
- Auto-bootstrap if needed
- Check for pending migrations
- Start the Django server

## Manual Steps (if you prefer)

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Go to backend
cd deployment_package/backend

# 3. Install deps (if needed)
pip install -r requirements.txt

# 4. Run migrations
python manage.py makemigrations core
python manage.py migrate

# 5. Start server
python manage.py runserver
```

## What Gets Installed

### Core Dependencies (Required)
- Django
- graphene-django (GraphQL)
- psycopg2-binary (PostgreSQL)
- django-redis (Caching)
- celery (Background tasks)

### ML Dependencies (Optional)
- scikit-learn
- statsmodels
- pandas
- numpy

The bootstrap script will prompt you to install ML deps if they're missing.

## Troubleshooting

### "Virtual environment not found"
The bootstrap script will create it automatically.

### "Django not installed"
The bootstrap script will install requirements.txt automatically.

### "Migrations pending"
Run:
```bash
cd deployment_package/backend
source ../../venv/bin/activate
python manage.py makemigrations core
python manage.py migrate
```

### "Port 8000 already in use"
Either:
- Stop the other server
- Or use a different port: `python manage.py runserver 8001`

## Scripts Available

- `bootstrap_backend.sh` - Full bootstrap (first time setup)
- `start_django_backend.sh` - Quick start (auto-bootstraps if needed)
- `setup_day_trading.sh` - Day trading specific setup
- `verify_day_trading.sh` - Verify day trading system

## After Bootstrap

Once bootstrapped, you can:

1. **Generate signals** via GraphQL:
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

3. **Evaluate performance**:
   ```bash
   cd deployment_package/backend
   source ../../venv/bin/activate
   python manage.py evaluate_signal_performance --all
   python manage.py calculate_strategy_performance --period ALL_TIME
   ```

4. **Query stats**:
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

