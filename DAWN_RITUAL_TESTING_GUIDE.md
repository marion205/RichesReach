# Dawn Ritual Testing Guide 🌅

## Overview

The Dawn Ritual is a daily 30-second sunrise animation that syncs Yodlee transactions and displays motivational haikus. This guide shows you how to test it in multiple ways.

## Quick Test Methods

### Method 1: Manual Trigger via Code (Fastest for Development)

**Option A: Add a test button to PortfolioScreen**

1. Open `mobile/src/features/portfolio/screens/PortfolioScreen.tsx`
2. Find the "Portfolio Management" section (around line 620)
3. Add this button:

```typescript
<TouchableOpacity 
  style={styles.actionButton}
  onPress={() => setShowDawnRitual(true)}
>
  <View style={styles.actionContent}>
    <Icon name="sunrise" size={24} color="#FF9500" />
    <View style={styles.actionText}>
      <Text style={styles.actionTitle}>🌅 Test Dawn Ritual</Text>
      <Text style={styles.actionDescription}>
        Trigger the daily dawn ritual animation
      </Text>
    </View>
    <Icon name="chevron-right" size={20} color="#8E8E93" />
  </View>
</TouchableOpacity>
```

**Option B: Use React Native Debugger Console**

1. Open React Native Debugger or Metro console
2. Navigate to PortfolioScreen
3. In the console, type:
```javascript
// This will trigger the ritual
// (You'll need to expose setShowDawnRitual via a ref or global)
```

### Method 2: Test via Notification (Realistic)

1. **Set notification time to current time + 1 minute:**
   ```typescript
   // In your test code or console:
   const { dawnRitualScheduler } = require('./features/rituals/services/DawnRitualScheduler');
   
   const now = new Date();
   const testTime = new Date(now.getTime() + 60000); // 1 minute from now
   const timeString = `${testTime.getHours()}:${testTime.getMinutes().toString().padStart(2, '0')}`;
   
   await dawnRitualScheduler.scheduleDailyRitual({
     enabled: true,
     time: timeString,
   });
   ```

2. **Wait for notification** (should appear in 1 minute)
3. **Tap the notification** to open the ritual
4. **Watch the animation:**
   - 0-15s: Sunrise animation
   - 15-25s: Transaction sync (progress bar)
   - 25-30s: Haiku display
   - 30s+: Auto-close

### Method 3: Test API Directly (Backend Testing)

**Using curl:**
```bash
# Get your auth token first (from AsyncStorage or login response)
TOKEN="your-auth-token-here"

# Test the API endpoint
curl -X POST http://localhost:8000/api/rituals/dawn/perform \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response:**
```json
{
  "transactionsSynced": 5,
  "haiku": "From grocery shadows to investment light\nYour wealth awakens, bold and bright.",
  "timestamp": "2024-01-15T07:00:00Z"
}
```

**Using Postman/Insomnia:**
- Method: `POST`
- URL: `http://localhost:8000/api/rituals/dawn/perform`
- Headers:
  - `Authorization: Bearer <your-token>`
  - `Content-Type: application/json`
- Body: `{}` (empty JSON object)

### Method 4: Test Scheduler Preferences

**Check current preferences:**
```typescript
const { dawnRitualScheduler } = require('./features/rituals/services/DawnRitualScheduler');
const prefs = await dawnRitualScheduler.getPreferences();
console.log('Current preferences:', prefs);
// Output: { enabled: true, time: "07:00", lastPerformed: "..." }
```

**Reset last performed date (to test again today):**
```typescript
const prefs = await dawnRitualScheduler.getPreferences();
delete prefs.lastPerformed;
await AsyncStorage.setItem('dawn_ritual_preferences', JSON.stringify(prefs));
```

**Check if should perform today:**
```typescript
const shouldPerform = await dawnRitualScheduler.shouldPerformToday();
console.log('Should perform today?', shouldPerform);
```

## What to Test

### ✅ Animation Flow
- [ ] Sunrise animation plays smoothly (15 seconds)
- [ ] Sun rises from horizon to top
- [ ] Sky gradient transitions from dark to light
- [ ] Progress bar animates during sync (10 seconds)
- [ ] Haiku fades in smoothly (5 seconds)
- [ ] Modal auto-closes after completion

### ✅ Haptic Feedback
- [ ] Light haptic on sunrise start
- [ ] Medium haptic on sync start
- [ ] Success haptic on haiku display

### ✅ API Integration
- [ ] Backend API is called correctly
- [ ] Transaction sync count is displayed
- [ ] Haiku is shown (from API or fallback)
- [ ] Error handling works (shows fallback haiku if API fails)

### ✅ State Management
- [ ] Ritual is marked as performed after completion
- [ ] `lastPerformed` date is saved correctly
- [ ] Won't trigger again on same day
- [ ] Can be triggered again after resetting `lastPerformed`

### ✅ User Controls
- [ ] Skip button works (closes modal immediately)
- [ ] Modal can be closed via back button (Android)
- [ ] Modal handles completion callback correctly

### ✅ Notification System
- [ ] Notification is scheduled at correct time
- [ ] Notification appears at scheduled time
- [ ] Tapping notification opens the ritual
- [ ] Notification data contains correct type (`dawn_ritual`)

## Troubleshooting

### Issue: Ritual doesn't trigger
**Solution:**
1. Check if `enabled` is `true` in preferences
2. Check if `lastPerformed` is today (reset it if needed)
3. Verify notification permissions are granted

### Issue: API returns error
**Solution:**
1. Check backend is running (`http://localhost:8000`)
2. Verify auth token is valid
3. Check Yodlee integration (if applicable)
4. Fallback haiku should still display

### Issue: Animation is choppy
**Solution:**
1. Check device performance
2. Verify `useNativeDriver: true` for animations
3. Check for memory leaks in animation cleanup

### Issue: Notification doesn't appear
**Solution:**
1. Check notification permissions
2. Verify time is set correctly (use future time for testing)
3. Check Expo Notifications is properly configured
4. On iOS simulator, notifications may not work - test on real device

## Quick Test Script

Add this to your test file or run in console:

```typescript
// Quick test function
async function testDawnRitual() {
  const { dawnRitualScheduler } = require('./features/rituals/services/DawnRitualScheduler');
  
  // 1. Check preferences
  const prefs = await dawnRitualScheduler.getPreferences();
  console.log('📋 Current preferences:', prefs);
  
  // 2. Reset last performed (to allow testing today)
  prefs.lastPerformed = undefined;
  await AsyncStorage.setItem('dawn_ritual_preferences', JSON.stringify(prefs));
  console.log('✅ Reset last performed date');
  
  // 3. Check if should perform
  const shouldPerform = await dawnRitualScheduler.shouldPerformToday();
  console.log('🎯 Should perform today?', shouldPerform);
  
  // 4. Schedule for 1 minute from now
  const now = new Date();
  const testTime = new Date(now.getTime() + 60000);
  const timeString = `${testTime.getHours()}:${testTime.getMinutes().toString().padStart(2, '0')}`;
  
  await dawnRitualScheduler.scheduleDailyRitual({
    enabled: true,
    time: timeString,
  });
  console.log(`⏰ Scheduled for ${timeString}`);
  
  return 'Test setup complete! Wait 1 minute for notification.';
}

// Run it
testDawnRitual().then(console.log);
```

## Production Checklist

Before shipping:
- [ ] Remove any test buttons from PortfolioScreen
- [ ] Verify default time is 7:00 AM
- [ ] Test on both iOS and Android
- [ ] Test notification permissions flow
- [ ] Verify haiku fallback works when API is down
- [ ] Test skip functionality
- [ ] Verify ritual only triggers once per day
- [ ] Check animation performance on low-end devices

## Summary

The Dawn Ritual can be tested in multiple ways:
1. **Manual trigger** (fastest for development) - Add a test button
2. **Notification** (most realistic) - Schedule for 1 minute from now
3. **API directly** (backend testing) - Use curl/Postman
4. **Scheduler** (preferences testing) - Check/modify preferences

The ritual takes ~30 seconds total:
- 15s sunrise animation
- 10s transaction sync
- 5s haiku display
- Auto-closes after completion

Happy testing! 🌅✨

