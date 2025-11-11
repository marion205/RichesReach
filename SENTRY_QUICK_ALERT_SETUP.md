# Sentry Alert Setup - Quick Guide

**You're in**: Sentry Dashboard → elite-algorithmics → react-native  
**Current Page**: Feed (Issues)

---

## Quick Alert Setup (5 minutes)

### Step 1: Navigate to Alerts

**From the left sidebar**:
1. Click **"Configure"** (in the sidebar)
2. Click **"Alerts"**

**Or direct URL**:
- https://elite-algorithmics.sentry.io/alerts/rules/

---

### Step 2: Create Critical Error Alert

1. **Click "Create Alert Rule"** (top right)

2. **Alert Name**: `Critical Errors - Immediate Action`

3. **Conditions**:
   - **When**: Select "An event is seen"
   - **Filter**: Add filter → `level` → `is` → `error` OR `fatal`
   - **Time Window**: `Last 5 minutes`
   - **Threshold**: `1` event

4. **Actions**:
   - Click "Add Action"
   - Select "Send a notification via Email"
   - Enter your email address
   - Click "Save Action"

5. **Click "Save Rule"**

---

### Step 3: Create High Volume Alert

1. **Click "Create Alert Rule"** again

2. **Alert Name**: `High Volume Errors`

3. **Conditions**:
   - **When**: "An event is seen"
   - **Filter**: `level` → `is` → `error` OR `fatal`
   - **Time Window**: `Last 10 minutes`
   - **Threshold**: `10` events

4. **Actions**: Email notification (same as above)

5. **Click "Save Rule"**

---

### Step 4: Create New Error Type Alert

1. **Click "Create Alert Rule"**

2. **Alert Name**: `New Error Types`

3. **Conditions**:
   - **When**: "An issue is created" (different from "event is seen")
   - **Filter**: `level` → `is` → `error` OR `fatal`
   - **Threshold**: `1` (any new issue)

4. **Actions**: Email notification

5. **Click "Save Rule"**

---

## Test Your Alerts

### Option 1: Use Mobile App
1. Open your mobile app
2. Navigate to `sentry-test` screen
3. Tap "Test Error & Message"
4. Check Sentry dashboard in 1-2 minutes
5. Verify alert email is received

### Option 2: Test from Backend
```bash
cd deployment_package/backend
python manage.py shell
```

```python
import sentry_sdk
sentry_sdk.capture_exception(Exception("Test error for alerts"))
```

---

## Verify Alerts Are Working

1. **Check Sentry Dashboard**:
   - Go to **Issues** → **Feed**
   - You should see your test error appear

2. **Check Email**:
   - You should receive an alert email within 1-2 minutes

3. **Check Alert Rules**:
   - Go to **Configure** → **Alerts**
   - Verify your 3 alerts are listed and active

---

## What You're Seeing in Sentry

**Current Status**: "Waiting to receive first event to continue"

**This is normal** - Sentry is waiting for the first error to be captured. Once you:
1. Send a test error (from app or backend)
2. Or a real error occurs in production

The dashboard will populate with issues and you'll see:
- Error details
- Stack traces
- User impact
- Performance data

---

## Next Steps After Alerts

1. ✅ **Alerts Created** - You'll be notified of errors
2. **Monitor Dashboard** - Check Issues feed regularly
3. **Create Dashboard** - Add widgets for key metrics
4. **Review Errors** - Fix issues as they appear

---

## Quick Reference

**Sentry Dashboard**: https://elite-algorithmics.sentry.io  
**Alerts Page**: https://elite-algorithmics.sentry.io/alerts/rules/  
**Issues Feed**: https://elite-algorithmics.sentry.io/issues/ (current page)

---

**Status**: Ready to create alerts! Follow steps above.

