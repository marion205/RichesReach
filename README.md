# RichesReach

AI-powered investment platform: portfolio management, trading, options, and contextual financial education.

## Overview

RichesReach is a full-stack investment app with a **React Native (Expo)** mobile client and a **Python** backend (FastAPI + Django, GraphQL). It combines real-time portfolio and market data with AI-driven insights, options trading tools, learning flows, “Teach me what I own”–style education tied to your positions, and **Private Markets** deal intelligence (score, confidence, compare, diligence workflow, Learn & Save).

## Repo structure

| Path | Description |
|------|-------------|
| `main_server.py` | Main backend entry (FastAPI + Django WSGI), run from repo root |
| `deployment_package/backend` | Django app (ASGI, GraphQL, Celery, migrations) |
| `mobile/` | React Native (Expo) app – iOS/Android |
| `docker-compose.yml` | PostgreSQL 16, Redis, PgBouncer, optional Pyroscope/Grafana |
| `tts_service/` | TTS API (FastAPI, port 8002) |
| `whisper-server/` | Whisper-based transcription (port 3003) |
| `rust_crypto_engine/` | Optional Rust service (port 3001) |
| `contracts/` | Smart contracts (e.g. DeFi) |
| `docs/` | Guides, deployment, and technical docs |

## Features

- **Portfolio** – Holdings, allocation, AI insights, and **“Teach me what I own”**: when a position is under pressure, inline repair suggestion, “Why this repair,” and “Learn more” → Learn tab.
- **Trading & options** – Order entry, options chain, Greeks, options learning.
- **Private Markets** – Evidence-based deal intelligence: **Deal Room** (browse opportunities), **Deal Detail** (AI Deal Score, confidence with factors, “What feeds this score,” “What would change this score,” risk framing, portfolio fit, decision guidance), **Compare** (2–4 deals with summary and best/worst callouts), **diligence workflow** (Not started → Requested → Received → Reviewed per item; “Request from issuer/GP” placeholder), **Learn** (deal-context education: how to read the score, confidence, key terms, what to do next), **Save** (watchlist with Saved tab). Execution via licensed partner.
- **Learn** – Daily Brief, tutor modules, lesson library, quizzes, voice digest.
- **AI** – Trading coach, portfolio insights, holding-level repair/education (demo + API).
- **DeFi** – Vaults, autopilot, positions (where enabled).
- **Social / community** – Wealth circles, challenges, peer progress.
- **Demo mode** – Set `EXPO_PUBLIC_DEMO_MODE=true` in `mobile/.env.local` for sample data and no live brokerage.

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for PostgreSQL and Redis)

### 1. Databases (Docker)

From repo root:

```bash
docker-compose up -d
```

Uses PostgreSQL on 5432 and Redis on 6379 (and optional PgBouncer on 6432).

### 2. Backend

From repo root:

```bash
# Optional: venv and env
python3 -m venv .venv && source .venv/bin/activate  # or venv/
# Optional: .env.openai with OPENAI_API_KEY for AI features

# Start all backend services (main server, ASGI, optional Rust/TTS/Whisper)
./start_all_backend_services.sh
```

Or start only the main API:

```bash
python3 main_server.py
```

- Main API: **http://127.0.0.1:8000** (health: `/health`, GraphQL: `/graphql`)
- Django ASGI (async AI): **http://127.0.0.1:8001** (e.g. `/api/ai/health/`)

Migrations (when using Django/Postgres):

```bash
cd deployment_package/backend
python manage.py migrate
```

### 3. Mobile app

```bash
cd mobile
npm install
npx expo start
```

- Use Expo Go or a dev client; press `i` for iOS simulator, `a` for Android.
- For **demo mode**, set in `mobile/.env.local`: `EXPO_PUBLIC_DEMO_MODE=true`.
- Point the app at your backend via `EXPO_PUBLIC_API_BASE_URL` and `EXPO_PUBLIC_GRAPHQL_URL` (defaults often assume `http://localhost:8000`).

### Alternative: start “all features”

Script that starts DBs, backend, optional Rust, and mobile (from `scripts/start/`):

```bash
cd scripts/start
./start_all_features.sh
```

See `scripts/README.md` for other start/setup/deploy scripts.

## Environment

- **Backend:** `.env.openai` for `OPENAI_API_KEY`; see `deployment_package/backend/env.production.example` for full options.
- **Mobile:** `mobile/.env.local` – e.g. `EXPO_PUBLIC_DEMO_MODE`, `EXPO_PUBLIC_API_BASE_URL`, `EXPO_PUBLIC_GRAPHQL_URL`.

## Docs and scripts

- **Scripts:** `scripts/README.md` – start, setup, deploy, utils.
- **Backend entry:** `deployment_package/backend/ENTRYPOINT.md` – how to run Django/ASGI from this repo.
- **Project docs:** `docs/` – guides, deployment, API, and feature docs.

## Testing

```bash
# Backend (from deployment_package/backend)
cd deployment_package/backend && python manage.py test

# Mobile
cd mobile && npm test
```

## License

MIT – see [LICENSE](LICENSE).

---

RichesReach – portfolio, trading, and learning in one place.
