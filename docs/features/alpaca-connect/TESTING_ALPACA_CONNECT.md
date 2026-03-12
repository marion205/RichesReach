# How to Check If Alpaca Connect Is Working

After your Alpaca Connect application is approved, use this guide to verify the integration end-to-end.

---

## Quick steps (link Alpaca → restart backend → see real data on Home)

1. **Link Alpaca in the app**
   - Open the app and go to the **Invest** tab (bottom nav).
   - Open **Trading** (e.g. tap “Trading” or the Stocks/Trade screen).
   - If no account is linked, you’ll see a card: **“Connect Alpaca Account”** with a **Connect** button.
   - Tap the card or **Connect** → the **Connect Your Alpaca Account** modal opens.
   - Choose **“Yes, I have an account”** → accept the authorization disclosure → the app opens your browser to Alpaca.
   - Sign in to Alpaca (if needed) and **approve** RichesReach. You’re redirected back to the app; the Trading screen should then show your account (e.g. buying power, positions) instead of the connect card.

2. **Restart the backend** (so it loads the latest code, including Alpaca-backed portfolio metrics)
   - From the **repo root** (e.g. `RichesReach/`):
     ```bash
     python3 main_server.py
     ```
   - Or, if you use the full script:
     ```bash
     ./start_all_backend_services.sh
     ```
   - Stop the existing process first (Ctrl+C), then run the command again.

3. **See real data on Home**
   - Go to the **Home** tab.
   - **Pull to refresh** (or close and reopen the app).
   - The **Portfolio Performance** card should show:
     - **If you have Alpaca positions:** real **Total Value** and **Total Return** from your Alpaca account (cached for 1 minute).
     - **If you have no positions:** **$0** for Total Value and Total Return.
   - If it still shows $0 after linking and refreshing: ensure you’re logged in as the same user that completed OAuth, and that the backend is the one you restarted (check `EXPO_PUBLIC_API_BASE_URL` / port 8000). Backend logs may show `Alpaca metrics failed for user X` if token/connection fails.

---

## 0. API base URL (mobile / clients)

Use the **base URL with port 8000** so the app and any in-app browser hit the real backend:

- **Root (e.g. "open in browser"):** `http://192.168.1.246:8000/` — **must include `:8000`**. If you open `http://192.168.1.246` (no port), the request goes to port 80 and you get `{"detail":"Not Found"}` from whatever is on port 80, not the RichesReach API.
- **GraphQL:** `http://192.168.1.246:8000/graphql/`
- **Health:** `http://192.168.1.246:8000/health`
- **Alpaca OAuth initiate:** `http://192.168.1.246:8000/api/auth/alpaca/initiate` — GET returns 302 to Alpaca’s authorize page (or 401 if backend auth is required; this path is public in zero-trust config).

In `mobile/.env.local`, set `EXPO_PUBLIC_API_BASE=http://192.168.1.246:8000` and `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.246:8000` (with `:8000`, no trailing path). The app builds `API_GRAPHQL = API_BASE + "/graphql/"` in `mobile/config/api.ts`.

---

## 1. Get Your Connect Credentials

- Go to **https://app.alpaca.markets/connect** (Alpaca Connect dashboard).
- Open your app (RichesReach) and note:
  - **Client ID**
  - **Client Secret**
- Under **Redirect URI**, ensure you have registered the **backend** callback URL (Alpaca redirects the user here after they approve). Use the **exact** path `/api/auth/alpaca/callback`:
  - Production: `https://api.richesreach.com/api/auth/alpaca/callback`
  - Local (device/simulator): `http://192.168.1.246:8000/api/auth/alpaca/callback` — **do not use** `127.0.0.1` or `localhost` when testing on a device; the device would open that on itself and show "Not Found".

---

## 2. Backend Environment Variables

**Production:** For production deploys, ensure `ENVIRONMENT=production` is set on the backend so demo guards (e.g. no `DEMO_TOKEN` bypass, no demo user auto-creation) apply. See [Production vs Demo guards](../../PRODUCTION_DEMO_GUARDS.md) for what’s fixed and what depends on env.

Set these on the server that runs the RichesReach API (Django):

```bash
# Required for OAuth flow
ALPACA_OAUTH_CLIENT_ID=<your-client-id-from-connect-dashboard>
ALPACA_OAUTH_CLIENT_SECRET=<your-client-secret>

# Where Alpaca redirects after user approves (must match Alpaca Connect dashboard).
# For device testing use your Mac's LAN IP so the phone can reach the backend:
ALPACA_OAUTH_REDIRECT_URI=http://192.168.1.246:8000/api/auth/alpaca/callback

# Encrypt OAuth tokens at rest (generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ALPACA_TOKEN_ENCRYPTION_KEY=<fernet-key>
```

Without `ALPACA_OAUTH_CLIENT_ID` and `ALPACA_OAUTH_CLIENT_SECRET`, the OAuth flow will fail (initiate or token exchange).

---

## 2b. Paper Trading: “no such table: paper_trading_accounts”

If the app shows “Order could not be placed” and the backend logs show `no such table: paper_trading_accounts`, migrations have not been applied to the **same database** the server uses.

- **Server started from repo root** (`python3 main_server.py`): the server sets `DB_NAME`, `DB_USER`, `DB_HOST` and uses **PostgreSQL**. Run migrations against that DB (PostgreSQL must be running and the database must exist):

  ```bash
  cd deployment_package/backend
  source .venv/bin/activate
  export DB_NAME=richesreach DB_USER=$USER DB_HOST=localhost DB_PORT=5432
  python manage.py migrate
  ```

- **Server and migrate both using SQLite**: run the server without PostgreSQL env so it uses SQLite, then migrate from the backend (same SQLite file):

  ```bash
  cd deployment_package/backend
  source .venv/bin/activate
  unset DB_NAME DB_USER DB_HOST DB_PORT DATABASE_URL
  python manage.py migrate
  ```

  Then start the server from the **repo root** with the same env unset (e.g. `unset DB_NAME DB_USER DB_HOST; python3 main_server.py`) so it uses `backend/db.sqlite3`.

---

## 3. Quick Backend Checks (No App)

### 3.1 Initiate redirects to Alpaca

From a browser or curl:

**Local (your machine on port 8000):**
```bash
curl -I "http://192.168.1.246:8000/api/auth/alpaca/initiate"
```

**Production:**
```bash
curl -I "https://api.richesreach.com/api/auth/alpaca/initiate"
```

Or open in a browser: `http://192.168.1.246:8000/api/auth/alpaca/initiate`

- **Expected:** `302` redirect to `https://app.alpaca.markets/oauth/authorize?...` (with `client_id`, `redirect_uri`, `state`, etc.).  
- If you get 401, the initiate path may not be in the backend’s public paths.  
- If you get 500 or no redirect, check backend logs and env (client ID/secret).

### 3.2 Run the existing script (if you use it)

```bash
./scripts/test-all-endpoints.sh
```

- The Alpaca OAuth initiate endpoint should be tested there (expect 302).

---

## 4. Test From the App (Full Flow)

1. **Log in** to the RichesReach app as a real user (backend must know the user; session or auth token).
2. **Open the Trading screen** (Stocks / Trade tab).
3. If no Alpaca account is linked, you should see an option to **Connect** (e.g. “Connect with Alpaca” or a connect modal).
4. **Tap Connect**  
   - The app opens: `{API_BASE}/api/auth/alpaca/initiate` (in browser or in-app browser).  
   - Backend redirects you to Alpaca’s authorization page.
5. **Sign in to Alpaca** (if needed) and **approve** RichesReach.
6. Alpaca redirects to your **backend** callback URL (`ALPACA_OAUTH_REDIRECT_URI`).  
   - Backend exchanges the code for tokens, stores the connection, then redirects the **browser** to the URL stored in session (e.g. `/trading?connected=true&account_id=...`).
7. **Return to the app** (or open the app if it was in the background).
8. **Confirm connection:**
   - On the Trading screen you should see the linked account (e.g. buying power, positions) instead of “Connect”.
   - If the app uses GraphQL `GetAlpacaAccount` / `alpacaAccount`, that query should now return the account after the backend has synced the OAuth connection to the broker account (see below).
9. **Portfolio Performance (real data):** Once Alpaca is linked, the **Home** screen’s **Portfolio Performance** card and the **GetPortfolioMetrics** GraphQL query use **real positions** from your Alpaca account. Total Value, Total Return, and holdings are fetched from Alpaca and cached for 1 minute. If you have no positions, values show as zero.

**Note:** If the post-approval redirect goes to a **web** URL (e.g. `https://api.richesreach.com/trading?connected=true`), the app may not receive the “connected” signal unless you:
- Use a **deep link** as the post-OAuth redirect (e.g. `richesreach://auth/alpaca/callback?connected=true&account_id=...`) and pass that as `redirect_uri` when opening the initiate URL, or  
- Have a web page at that URL that deep-links back into the app.

### If after accepting you see Not Found or a blank page at 127.0.0.1

Alpaca is redirecting to your callback URL. On a phone or simulator, 127.0.0.1 is the **device**, not your Mac, so the callback never hits your backend.

1. **Backend .env:** Set `ALPACA_OAUTH_REDIRECT_URI=http://192.168.1.246:8000/api/auth/alpaca/callback` (use your Mac's LAN IP and port 8000).
2. **Alpaca Connect dashboard:** Under your app's Redirect URIs, add that exact URL.
3. **Restart the backend** and run the Connect flow again.

---

## 5. Verify “Everything Connects” (API Call)

To confirm the stored connection works and the backend can call Alpaca on behalf of the user:

1. **After completing the Connect flow once**, call your backend’s **account/portfolio** API for the logged-in user (e.g. GraphQL `alpacaAccount(userId: ...)` or your REST broker account endpoint).
2. **Expected:**  
   - Account id, buying power, cash, or positions returned from Alpaca (not “not linked” or 404).
3. **Optional:** In Django admin (or DB), check:
   - `core_alpaca_connection`: one row per user with `alpaca_account_id` and tokens (stored encrypted if `ALPACA_TOKEN_ENCRYPTION_KEY` is set).
   - Broker account record for that user with the same `alpaca_account_id` so the app’s `GetAlpacaAccount` (or equivalent) resolves.

If the app still shows “not connected” after a successful OAuth:
- Ensure the backend syncs **AlpacaConnection** → **BrokerAccount** (e.g. in the OAuth callback). The Trading screen reads from the broker account (GraphQL `alpacaAccount`), not only from `AlpacaConnection`.

---

## 6. Summary Checklist

| Step | What to do | Success |
|------|------------|--------|
| 1 | Get Client ID/Secret and set Redirect URI at app.alpaca.markets/connect | Redirect URI matches backend |
| 2 | Set `ALPACA_OAUTH_*` and `ALPACA_TOKEN_ENCRYPTION_KEY` on backend | No “credentials not configured” in logs |
| 3 | GET `/api/auth/alpaca/initiate` | 302 to Alpaca authorize URL |
| 4 | In app: Tap Connect → approve on Alpaca → return to app | No error; session/DB has connection |
| 5 | Call account/positions API or open Trading screen | Account/positions from Alpaca shown |

If any step fails, check backend logs (OAuth initiate, callback, token exchange, and Alpaca API errors) and the env vars above.

---

## 7. Testing Stock and Options Purchases

To confirm users can **buy stocks or options** after connecting:

### Prerequisites
- User has completed **Alpaca Connect** (OAuth) and the app shows the linked account on the Trading screen.
- Backend has **ALPACA_OAUTH_*** and **ALPACA_TOKEN_ENCRYPTION_KEY** set (and, for non-Connect broker accounts, **ALPACA_BROKER_*** if you use broker onboarding too).

### Stocks
1. Open the **Trading** (or **Stocks**) tab and ensure the account is connected (buying power visible).
2. Enter a **symbol**, **side** (Buy/Sell), **quantity**, and **order type** (e.g. Market).
3. Tap **Place Order** (or equivalent).
4. **Success:** Order confirmation and order appears in open/order history.  
   **Failure:** Check backend logs for Alpaca API errors (e.g. 403, insufficient buying power, symbol not tradeable).

### Options
1. Navigate to the **Options** flow (e.g. from a stock detail or Options tab).
2. Select a **contract** (underlying, expiration, strike, call/put), **quantity**, and **order type**.
3. Tap **Place Order** / **Place Trade**.
4. **Success:** Order confirmation and order/position updates.  
   **Failure:** Check backend logs; ensure the contract symbol (OCC format) and account have options permission on Alpaca.

### Backend behavior
- **Connect (OAuth) users:** Orders are sent with the user’s OAuth token to Alpaca’s **Trading API** (`api.alpaca.markets`). No broker API keys are required for that user’s orders.
- **Broker-onboarded users:** Orders use your **Broker API** keys and `ALPACA_BROKER_*` env vars.
- Connect users are treated as **approved** for trading (KYC set from Connect); broker-onboarded accounts still require `kyc_status == 'APPROVED'`.

---

## Should we use Alpaca for options, forex, crypto, and historical data?

**Summary**

| Use case | Use Alpaca? | Notes |
|----------|-------------|--------|
| **Equities (stocks) trading** | ✅ Yes | Primary use: OAuth Connect, positions, orders, portfolio metrics. Already wired. |
| **Options trading** | ✅ Yes | Alpaca supports US equity/ETF options (single- and multi-leg). We already use `create_options_order` (Broker API) and Trading API for options; keep using Alpaca for execution. |
| **Options / equities historical data** | ✅ Optional | Alpaca’s Data API provides historical bars and quotes. You can use it as one source for charts and backtests if you want a single provider; otherwise keep using your current data sources (e.g. Polygon, Alpha Vantage). |
| **Forex trading** | ❌ No | Alpaca is not a forex broker. Our **forex** features (e.g. `rust_forex_analysis`) use the Rust analytics engine for signals/analysis, not Alpaca. Keep forex analytics as-is; don’t route forex orders through Alpaca. |
| **Forex historical data** | ❌ No | Use your existing FX data provider; Alpaca is not the right source for forex history. |
| **Crypto trading** | ✅ Yes | Alpaca supports crypto trading. We have GraphQL types and mutations for Alpaca crypto (e.g. `alpacaCryptoAccount`, crypto orders). Use Alpaca for crypto **execution** when the user has a linked Alpaca account and you want unified brokerage. |
| **Crypto historical data** | ✅ Optional | Alpaca’s data API includes crypto. You can use it for crypto history/charts if you want; otherwise keep using other crypto data sources. |

**Recommendation**

- **Trading (execution):** Use Alpaca for **equities** and **options** (already in place) and for **crypto** if you want the same broker for stocks + crypto. Do **not** use Alpaca for forex execution.
- **Historical / analytics:** Use Alpaca’s Data API where it fits (e.g. stocks, options, or crypto) and you want one less vendor. For forex history and analytics, keep using your current providers and the Rust forex engine.
