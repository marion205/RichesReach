# Sentry Monitoring Setup - Quick Start

**Organization**: elite-algorithmics  
**Project**: react-native  
**DSN**: Configured in `.env`

---

## Immediate Actions

### 1. Verify Sentry is Working

**Test from App**:
1. Open mobile app
2. Navigate to `sentry-test` screen
3. Tap "Test Error & Message"
4. Check Sentry dashboard within 1-2 minutes

**Test from Backend**:
```python
# In Django shell or test
import sentry_sdk
sentry_sdk.capture_exception(Exception("Test error from backend"))
```

---

### 2. Set Up Critical Alerts

Go to: https://sentry.io → elite-algorithmics → react-native → Alerts

#### Alert 1: Critical Errors (Immediate)
- **Name**: "Critical Errors - Immediate Action"
- **Condition**: Error level = error OR fatal
- **Threshold**: 1 event in 5 minutes
- **Action**: Email + Slack

#### Alert 2: High Volume Errors
- **Name**: "High Volume Errors"
- **Condition**: Error level = error OR fatal
- **Threshold**: 10 events in 10 minutes
- **Action**: Email + Slack

#### Alert 3: New Error Types
- **Name**: "New Error Types"
- **Condition**: New issue created
- **Threshold**: Any
- **Action**: Email

---

### 3. Create Monitoring Dashboard

1. Go to **Dashboards** → **Create Dashboard**
2. Add widgets:
   - Error Rate Over Time
   - Transaction Duration (p95)
   - Top Errors
   - Affected Users
   - Release Health

---

## Monitoring Best Practices

### Daily Checks
- [ ] Review error rate (should be < 1%)
- [ ] Check for new error types
- [ ] Review performance metrics

### Weekly Reviews
- [ ] Analyze error trends
- [ ] Review user impact
- [ ] Update alert thresholds if needed

### Monthly Reviews
- [ ] Review alert effectiveness
- [ ] Update monitoring dashboard
- [ ] Document common issues

---

## Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Error Rate | < 1% | > 5% |
| Transaction p95 | < 2s | > 5s |
| Affected Users | < 10 | > 50 |
| New Issues | < 5/day | > 20/day |

---

## Quick Links

- **Sentry Dashboard**: https://sentry.io
- **Alerts Setup Guide**: `SENTRY_ALERTS_SETUP.md`
- **Testing Guide**: `SENTRY_TESTING_GUIDE.md`

---

**Status**: Ready to monitor  
**Next Step**: Set up alerts in Sentry dashboard

