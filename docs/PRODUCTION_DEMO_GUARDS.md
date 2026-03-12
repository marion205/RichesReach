# Production vs Demo: What’s Fixed and What Depends on Config

This doc clarifies which demo/mock behaviors are **blocked in production** by recent fixes, what **still depends on environment config**, and what is **intentionally demo-only** and out of scope.

---

## Fixed (confirmed)

- **Trading quotes** — Now fetch real data instead of hardcoded prices.
- **`DEMO_TOKEN` auth bypass** — Blocked in production (no bypass when running as production).
- **Demo user auto-creation** — Blocked in production (demo user is not auto-created when running as production).

---

## Still reliant on correct environment config

Mock/data guards only fire when the app and backend think they are in **production**. If config is wrong, those guards will not run.

### Backend: `ENVIRONMENT=production`

- **`authentication.py`** and **`auth_views.py`** use `os.getenv("ENVIRONMENT", "")` to detect production.
- If the production server does **not** set `ENVIRONMENT=production` (or your code path uses `NODE_ENV=production` and you rely on that), these guards will **not** fire.
- **Action:** Verify your production deploy sets `ENVIRONMENT=production` (or the variable your code actually checks) on the backend.

### Mobile: `EXPO_PUBLIC_DEMO_MODE` must be false in production

- The mobile app’s **`EXPO_PUBLIC_DEMO_MODE`** is a **build-time** flag.
- If a production build’s `.env` (or env used at build time) has `EXPO_PUBLIC_DEMO_MODE=true`, the global fetch interceptor in **`demoFetch.ts`** will intercept **all** API calls and return fake data for every screen.
- **Action:** Ensure `EXPO_PUBLIC_DEMO_MODE` is `false` or unset for production builds.

**Recommendation:** Double-check both in your deployment config:

1. Backend: `ENVIRONMENT=production` (or equivalent) set on the production server.
2. Mobile: `EXPO_PUBLIC_DEMO_MODE` is **not** `true` in the env used for production builds.

---

## Out of scope of these fixes (intentionally demo-only)

- **`main_server.py` mock chart data** — Already hard-blocked in production via **`USE_MOCK_STOCK_DATA`** (production should not set this).
- **`autopilot_service.py` demo repair flow** — Only runs for users who have a **`demo:`** cache entry, which is set explicitly (e.g. when entering demo mode). No change needed for production as long as that entry is not set for real users.

---

## Summary

| Guard | Condition for “production” behavior |
|-------|-------------------------------------|
| Trading quotes real data | Backend in production (and no demo overrides). |
| No `DEMO_TOKEN` bypass | Backend: `ENVIRONMENT=production` (or equivalent). |
| No demo user auto-creation | Backend: `ENVIRONMENT=production` (or equivalent). |
| No global fake API responses | Mobile: `EXPO_PUBLIC_DEMO_MODE` not `true` in **production build** env. |
| No mock chart data | Backend: `USE_MOCK_STOCK_DATA` not set in production. |
| No autopilot demo repair | `demo:` cache entry only set when explicitly in demo mode. |

**Bottom line:** Mock data is blocked in production **as long as**:

1. **Backend** has `ENVIRONMENT=production` set.
2. **Mobile** production builds are built with `EXPO_PUBLIC_DEMO_MODE` false or unset.

Verify both in your deployment config.
