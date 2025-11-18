# WebRTC Camera Debugging Guide

## Quick Diagnostic Questions

**Answer these 3 questions to identify the issue:**

### 1. Are you testing in Expo Go or a development build?

**Check:**
```bash
# If you see "Expo Go" in your app → WebRTC will NOT work
# You MUST use a development build
```

**Solution:**
```bash
# iOS
npx expo run:ios

# Android
npx expo run:android
```

### 2. Is react-native-webrtc properly installed and configured?

**Check package.json:**
```json
"react-native-webrtc": "^124.0.7"  // Should be present
```

**Verify installation:**
```bash
cd mobile
npm list react-native-webrtc
```

**If missing or wrong version:**
```bash
npm install react-native-webrtc@^124.0.7
npx expo prebuild --clean
npx expo run:ios  # or run:android
```

### 3. Test with the minimal CameraTestScreen component

**Add to your navigation:**
```typescript
import CameraTestScreen from './components/CameraTestScreen';

// In your Stack.Screen
<Stack.Screen name="CameraTest" component={CameraTestScreen} />
```

**What to look for:**
- ✅ **Green checkmarks** = Everything is configured correctly
- ❌ **Red X marks** = Issue identified (see error message)
- 🖥️ **Black screen** = Check console for errors

## Common Issues & Solutions

### Issue 1: "WebRTC not available in Expo Go"

**Symptom:** Error message says "WebRTC is not available in Expo Go"

**Solution:**
```bash
# Stop Expo Go
# Build development client
npx expo run:ios
# or
npx expo run:android
```

### Issue 2: "mediaDevices is not available"

**Symptom:** CameraTestScreen shows "❌ Not Available" for mediaDevices

**Solution:**
```bash
# Rebuild with clean prebuild
npx expo prebuild --clean
npx expo run:ios
```

### Issue 3: "Permissions denied" (Android)

**Symptom:** App asks for permissions but camera still doesn't work

**Solution:**
1. Go to Android Settings → Apps → RichesReach → Permissions
2. Enable Camera and Microphone
3. Restart the app

### Issue 4: Black screen but no errors

**Possible causes:**
1. **Stream acquired but not rendering:**
   - Check console for "✅ Stream acquired" message
   - Verify `RTCView` is rendering (check component tree)
   - Ensure `stream.toURL()` returns a valid URL

2. **Stream stopped too early:**
   - Check if cleanup is running before stream starts
   - Look for "🛑 Stopped track" messages in console

3. **Mirror issue:**
   - Try setting `mirror={false}` on RTCView
   - Some Android devices show black if mirror is incorrect

### Issue 5: "Cannot read property 'getUserMedia' of undefined"

**Symptom:** JavaScript error in console

**Solution:**
```bash
# Ensure you're NOT in Expo Go
# Rebuild development client
npx expo prebuild --clean
npx expo run:ios
```

## Step-by-Step Debugging

### Step 1: Verify Environment
```bash
# Check if you're in Expo Go
# Open app and look for "Expo Go" branding
# OR check console for "isExpoGo()" logs
```

### Step 2: Test Minimal Component
1. Navigate to CameraTestScreen
2. Check all status indicators
3. Press "Start Front Camera"
4. Check console logs

### Step 3: Check Console Output

**Expected logs when working:**
```
🔍 Camera Test Environment Check:
- Is Expo Go: false
- RTCView available: true
- mediaDevices available: true
🎥 Requesting camera stream with front camera...
✅ Stream acquired: { hasStream: true, streamURL: '...', tracks: 2 }
```

**If you see errors:**
- Copy the full error message
- Check which step failed (permissions, getUserMedia, rendering)

### Step 4: Verify Permissions

**iOS:**
- Check Info.plist has `NSCameraUsageDescription`
- First launch should show permission dialog
- Check Settings → RichesReach → Camera is enabled

**Android:**
- Check `app.json` has `android.permission.CAMERA`
- Runtime permission should be requested automatically
- Check Settings → Apps → RichesReach → Permissions

## Testing Checklist

- [ ] Not using Expo Go (using development build)
- [ ] `react-native-webrtc` is installed (`npm list react-native-webrtc`)
- [ ] App rebuilt after installing WebRTC (`npx expo prebuild --clean`)
- [ ] Camera permissions granted (check device settings)
- [ ] CameraTestScreen shows all green checkmarks
- [ ] Console shows "✅ Stream acquired" when starting camera
- [ ] No errors in console when pressing "Start Front Camera"
- [ ] Video feed appears (not black screen)

## Still Not Working?

If CameraTestScreen also shows black screen:

1. **Check device camera:**
   - Open native camera app
   - Verify front camera works
   - Close other apps using camera

2. **Check React Native logs:**
   ```bash
   npx react-native log-ios
   # or
   npx react-native log-android
   ```

3. **Try different camera:**
   - Change `facingMode: 'user'` to `facingMode: 'environment'` (back camera)
   - See if back camera works

4. **Check WebRTC version compatibility:**
   ```bash
   npm list react-native-webrtc
   # Should be compatible with React Native 0.81.5
   ```

5. **Full clean rebuild:**
   ```bash
   # iOS
   cd ios && pod deintegrate && pod install && cd ..
   npx expo prebuild --clean
   npx expo run:ios

   # Android
   cd android && ./gradlew clean && cd ..
   npx expo prebuild --clean
   npx expo run:android
   ```

## Quick Test Commands

```bash
# 1. Check WebRTC installation
npm list react-native-webrtc

# 2. Clean rebuild
npx expo prebuild --clean

# 3. Run on iOS
npx expo run:ios

# 4. Run on Android
npx expo run:android

# 5. Check logs
npx react-native log-ios
# or
npx react-native log-android
```

## Expected Behavior

When everything works correctly:

1. **CameraTestScreen shows:**
   - ✅ Environment: Development Build
   - ✅ RTCView: Available
   - ✅ mediaDevices: Available
   - ✅ Stream Status: Active (after pressing button)

2. **Console shows:**
   ```
   🎥 Requesting front camera stream...
   ✅ Stream acquired: { hasStream: true, ... }
   🎥 Front camera stream started
   ```

3. **Screen shows:**
   - Your front camera feed (not black)
   - Video is mirrored (you see yourself correctly)

If you see this → **Everything is working!** The issue is likely in the live streaming components, not the WebRTC setup.

