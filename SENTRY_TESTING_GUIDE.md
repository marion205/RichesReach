# Sentry Testing Guide

## Quick Test Methods

### Method 1: Using Sentry Test Button (Recommended)

1. **Open the app**
2. **Navigate to Sentry Test Screen**:
   - In development: Look for "Sentry Test" option in navigation
   - Or add a test button to your debug menu
3. **Test Error & Message**:
   - Tap "Test Error & Message"
   - This sends a test error and message to Sentry
4. **Test Performance**:
   - Tap "Test Performance"
   - This sends a performance transaction
5. **Test Crash** (⚠️ Use with caution):
   - Tap "Test Crash"
   - This will crash the app to test native crash reporting
   - **Warning**: Only use in development!

### Method 2: Programmatic Test

Add this code anywhere in your app:

```typescript
import Sentry from './config/sentry';

// Test error
Sentry.captureException(new Error('Test error from RichesReach'));

// Test message
Sentry.captureMessage('Test message from RichesReach', 'info');

// Test with context
Sentry.setContext('test', {
  testType: 'manual',
  timestamp: new Date().toISOString(),
});
```

### Method 3: Test in Code

Add a test button to any screen:

```typescript
import Sentry from '../config/sentry';

<TouchableOpacity
  onPress={() => {
    Sentry.captureException(new Error('Test error'));
    Alert.alert('Test Sent', 'Error sent to Sentry');
  }}
>
  <Text>Test Sentry</Text>
</TouchableOpacity>
```

---

## Verifying in Sentry Dashboard

### Steps:

1. **Go to Sentry Dashboard**:
   - https://sentry.io
   - Navigate to: **elite-algorithmics** → **react-native**

2. **Check Issues**:
   - Go to **Issues** tab
   - Look for your test error
   - Should appear within 1-2 minutes

3. **Check Performance**:
   - Go to **Performance** tab
   - Look for "Test Transaction"
   - Should show transaction details

4. **Check Releases**:
   - Go to **Releases** tab
   - Verify your release is tracked

---

## Expected Results

### Error Test
- ✅ Error appears in Issues
- ✅ Stack trace is available
- ✅ Context is included
- ✅ Environment is set correctly

### Performance Test
- ✅ Transaction appears in Performance
- ✅ Duration is recorded
- ✅ Transaction details are available

### Crash Test
- ✅ Crash appears in Issues
- ✅ Native crash report is available
- ✅ Device information is included

---

## Troubleshooting

### Error Not Appearing?

1. **Check DSN**:
   - Verify DSN in `app.json` is correct
   - Check `sentry.ts` is reading DSN correctly

2. **Check Network**:
   - Ensure device has internet connection
   - Check Sentry service is accessible

3. **Check Logs**:
   - Look for "✅ Sentry initialized" in console
   - Check for any Sentry errors

4. **Check Sentry Dashboard**:
   - Verify project is active
   - Check quota/limits

### Performance Not Tracking?

1. **Check Sampling Rate**:
   - Default is 10% (0.1)
   - May need to trigger multiple times

2. **Check Transaction**:
   - Ensure transaction is finished
   - Check transaction name

---

## Test Checklist

- [ ] Test error appears in Sentry
- [ ] Test message appears in Sentry
- [ ] Performance transaction appears
- [ ] Context is included correctly
- [ ] Environment is set correctly
- [ ] Release is tracked
- [ ] Native crash reporting works (if tested)

---

**Status**: Ready to test Sentry integration

