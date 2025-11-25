# API Endpoints Documentation

## Architecture
- **FastAPI** routes are checked first (defined in `main.py`)
- **Django** routes are mounted at root via `WSGIMiddleware` (handles remaining paths)
- FastAPI routes take precedence when there's overlap

## FastAPI Endpoints (main.py)

### Tax Optimization
- `GET /api/tax/optimization-summary` - Get tax optimization summary
- `POST /api/tax/report/pdf` - Generate tax report PDF
- `POST /api/tax/smart-harvest/recommendations` - Get smart harvest recommendations
- `POST /api/tax/smart-harvest/execute` - Execute smart harvest
- `GET /api/tax/projection` - Get tax projection

### Market Data
- `GET /api/market/quotes` - Get market quotes (FastAPI version)
- `POST /api/market/regime` - Predict market regime

### Yodlee Banking
- `GET /api/yodlee/accounts` - Get Yodlee accounts (FastAPI version)

### Portfolio
- `POST /api/portfolio/analyze` - Analyze portfolio

### Authentication
- `POST /api/auth/login/` - Login (FastAPI version)

### GraphQL
- `POST /graphql/` - GraphQL endpoint (FastAPI version)
- `GET /graphql/` - GraphQL endpoint (GET, FastAPI version)

### System
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/status` - Service status
- `GET /api/test/sbloc-banks` - Test SBLOC banks endpoint

## Django Endpoints (urls.py + included URLs)

### Admin
- `GET/POST /admin/` - Django admin interface

### GraphQL
- `POST /graphql/` - GraphQL endpoint (Django version, overridden by FastAPI)
- `GET /graphql-daytrading-test/` - Day trading test GraphQL endpoint

### Yodlee Banking (banking_urls.py)
- `GET /api/yodlee/fastlink/start` - Start FastLink session
- `POST /api/yodlee/fastlink/callback` - FastLink callback
- `GET /api/yodlee/accounts` - Get Yodlee accounts (Django version, overridden by FastAPI)
- `GET /api/yodlee/transactions` - Get Yodlee transactions
- `POST /api/yodlee/refresh` - Refresh Yodlee account
- `DELETE /api/yodlee/bank-link/<id>` - Delete bank link
- `POST /api/yodlee/webhook` - Yodlee webhook handler

### Authentication (auth_views.py)
- `POST /api/auth/login/` - Login (Django version, overridden by FastAPI)

### Alpaca OAuth (alpaca_oauth_urls.py)
- `GET /api/auth/alpaca/initiate` - Initiate Alpaca OAuth
- `GET /api/auth/alpaca/callback` - Alpaca OAuth callback
- `POST /api/auth/alpaca/disconnect` - Disconnect Alpaca account

### Market Data (market_views.py)
- `GET /api/market/quotes/` - Get market quotes (Django version, overridden by FastAPI)

### Wealth Circles (wealth_circles_views.py)
- `GET /api/wealth-circles/<id>/posts/` - Get wealth circle posts
- `POST /api/wealth-circles/<id>/posts/` - Create wealth circle post

### Voices (voices_views.py)
- `GET /api/voices/` - Get voices list

### AI Options (ai_options_views.py)
- `GET /api/ai-options/recommendations/` - Get AI options recommendations

## Endpoint Overlaps (FastAPI takes precedence)

1. `/api/auth/login/` - FastAPI version used
2. `/graphql/` - FastAPI version used
3. `/api/market/quotes` - FastAPI version used (note: Django has trailing slash)
4. `/api/yodlee/accounts` - FastAPI version used

## Notes

- All Django endpoints are accessible through FastAPI via WSGIMiddleware
- FastAPI routes are matched first, then Django routes handle remaining paths
- Some endpoints have both FastAPI and Django versions (FastAPI takes precedence)
- Django endpoints with trailing slashes may behave differently than FastAPI versions

