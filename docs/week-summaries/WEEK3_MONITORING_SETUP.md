# Week 3: Monitoring Setup Guide

## Sentry Configuration

### Backend (Django/FastAPI)

**Status**: ✅ Setup code created

**Files Created**:
- `core/monitoring_setup.py` - Sentry initialization
- `requirements.txt` - Added sentry-sdk dependency
- `settings.py` - Integrated monitoring setup

**Installation**:
```bash
cd deployment_package/backend
source venv/bin/activate
pip install sentry-sdk[fastapi,django]
```

**Configuration**:
Add to `.env`:
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
RELEASE_VERSION=1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

**Features**:
- ✅ Error tracking
- ✅ Performance monitoring
- ✅ Django integration
- ✅ FastAPI integration
- ✅ Celery integration
- ✅ Redis integration
- ✅ Sensitive data filtering

---

### Mobile (React Native)

**Status**: ⏳ Pending installation

**Installation**:
```bash
cd mobile
npm install @sentry/react-native
```

**Configuration**:
Add to `mobile/src/config/sentry.ts`:
```typescript
import * as Sentry from '@sentry/react-native';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.ENVIRONMENT || 'production',
  tracesSampleRate: 0.1,
  enableAutoSessionTracking: true,
});
```

**Add to `App.tsx`**:
```typescript
import * as Sentry from '@sentry/react-native';

// Wrap app with Sentry
export default Sentry.wrap(App);
```

---

## APM (Application Performance Monitoring)

### Options

1. **Sentry Performance** (Recommended - Already integrated)
   - ✅ Included with Sentry
   - ✅ No additional setup needed
   - ✅ Automatic instrumentation

2. **New Relic** (Alternative)
   - Install: `pip install newrelic`
   - Configure: Add to `settings.py`

3. **Datadog** (Alternative)
   - Install: `pip install ddtrace`
   - Configure: Add to `settings.py`

**Recommendation**: Use Sentry Performance (already integrated)

---

## Logging Configuration

**Status**: ✅ Configured

**Features**:
- ✅ Structured logging (JSON format option)
- ✅ Log levels configurable via environment
- ✅ Separate loggers for Django and core
- ✅ Console output

**Configuration**:
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json  # or 'text'
DJANGO_LOG_LEVEL=INFO
CORE_LOG_LEVEL=INFO
```

---

## Alerting Setup

### Sentry Alerts

1. **Create Sentry Project**:
   - Go to sentry.io
   - Create new project
   - Get DSN

2. **Configure Alerts**:
   - Error rate alerts
   - Performance degradation alerts
   - New issue alerts

3. **Notification Channels**:
   - Email
   - Slack
   - PagerDuty
   - Webhooks

---

## Health Checks

**Status**: ✅ Implemented

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "ok",
  "schemaVersion": "1.0.0",
  "timestamp": "2024-11-10T..."
}
```

**Enhancement**: Add database, Redis, and external service health checks

---

## Metrics Collection

**Status**: ⏳ Pending

**Options**:
1. **Sentry Metrics** (Recommended)
   - Custom metrics via Sentry SDK
   - Automatic performance metrics

2. **Prometheus** (Advanced)
   - Install: `pip install prometheus-client`
   - Expose metrics endpoint

3. **CloudWatch** (AWS)
   - Use AWS CloudWatch for infrastructure metrics

---

## Next Steps

1. **Get Sentry DSN**:
   - Sign up at sentry.io
   - Create project
   - Get DSN

2. **Configure Environment Variables**:
   - Add `SENTRY_DSN` to `.env`
   - Add other Sentry config

3. **Install Mobile Sentry**:
   - `npm install @sentry/react-native`
   - Configure in `App.tsx`

4. **Set Up Alerts**:
   - Configure error alerts
   - Configure performance alerts
   - Set up notification channels

5. **Test Monitoring**:
   - Trigger test error
   - Verify it appears in Sentry
   - Test performance tracking

---

## Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Backend Sentry | ✅ Setup Complete | Need DSN |
| Mobile Sentry | ⏳ Pending | Need installation |
| Logging | ✅ Configured | Ready |
| APM | ✅ Sentry Performance | Included |
| Alerting | ⏳ Pending | Need Sentry project |
| Health Checks | ✅ Implemented | Basic version |

---

**Status**: ✅ Monitoring infrastructure ready - Need Sentry DSN and mobile setup

