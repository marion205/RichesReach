# Quick Fix: Development Client Setup

## ✅ Step 1: Clear Watchman Warning (Done)

```bash
watchman watch-del '/Users/marioncollins/RichesReach'
watchman watch-project '/Users/marioncollins/RichesReach'
```

---

## ✅ Step 2: Install Dev Client Dependency

```bash
cd mobile
npx expo install expo-dev-client
```

**Status**: Already installed ✅

---

## 🚀 Step 3: Build & Install Dev Client

### Option A: iOS Simulator (Fastest - Recommended)

**Builds and installs automatically**:
```bash
cd mobile
npx expo run:ios
```

**What this does**:
- Compiles native code
- Builds development client
- Installs on iOS Simulator
- Launches automatically

**Time**: 5-15 minutes (first time), faster after

---

### Option B: Physical iPhone/iPad

**Build via EAS**:
```bash
cd mobile
eas build --profile development --platform ios
```

**After build completes**:
```bash
eas install -p ios
```

**Or manually**:
1. Download `.ipa` from Expo dashboard
2. Install via Xcode (Window > Devices and Simulators)
3. Trust developer profile on device

---

## 🎯 Step 4: Start Expo with Dev Client

**After dev client is installed**:

```bash
cd mobile
npx expo start --dev-client
```

**This will**:
- Start Metro bundler
- Show QR code
- Auto-open in dev client (if installed)
- Or scan QR to connect

---

## ⚠️ Important Notes

### Don't Start Before Installing!

**Wrong** (will error):
```bash
npx expo start --dev-client  # ❌ No dev client installed yet
```

**Correct** (after installing):
```bash
npx expo run:ios  # ✅ Builds and installs first
# Then:
npx expo start --dev-client  # ✅ Now it works
```

### Bundle ID Check

**Verify in `app.json`**:
```json
{
  "ios": {
    "bundleIdentifier": "com.richesreach.app"
  }
}
```

**Status**: ✅ Already configured correctly

---

## 🎯 Recommended: Use Simulator Build

**Fastest path to get running**:

```bash
cd mobile
npx expo run:ios
```

**This single command**:
- ✅ Builds dev client
- ✅ Installs on simulator
- ✅ Launches app
- ✅ Connects to Metro

**Then**:
```bash
npx expo start --dev-client
```

**App will reload automatically!**

---

## 📋 Quick Reference

**Simulator** (Recommended):
```bash
cd mobile
npx expo run:ios
npx expo start --dev-client
```

**Physical Device**:
```bash
cd mobile
eas build --profile development --platform ios
eas install -p ios
npx expo start --dev-client
```

---

## ✅ Success Indicators

You'll know it's working when:
- ✅ Dev client builds successfully
- ✅ App installs on simulator/device
- ✅ App opens automatically
- ✅ `expo start --dev-client` connects
- ✅ App reloads when you make code changes

---

**Ready to build!** Choose simulator (fastest) or physical device! 🚀

