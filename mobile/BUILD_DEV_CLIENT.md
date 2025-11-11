# Build Development Client - Quick Guide

## ✅ Current Setup

**Status**:
- ✅ EAS CLI installed and logged in (`marion205`)
- ✅ `expo-dev-client` installed
- ✅ `eas.json` configured
- ✅ Bundle ID: `com.richesreach.app`
- ✅ `expo-dev-client` added to plugins

---

## 🚀 Build Options

### Option 1: Simulator Build (Fastest - Recommended for Testing)

**For iOS Simulator**:
```bash
cd mobile
eas build --profile simulator --platform ios
```

**Pros**:
- ✅ Fastest (5-10 minutes)
- ✅ No Apple Developer account needed
- ✅ Perfect for testing
- ✅ Can test on Mac simulator

**After build completes**:
1. Download `.tar.gz` from Expo dashboard
2. Extract: `tar -xzf RichesReach-*.tar.gz`
3. Install on simulator:
   ```bash
   xcrun simctl install booted ./RichesReach.app
   ```

---

### Option 2: Physical Device Build

**For iPhone/iPad**:
```bash
cd mobile
eas build --profile development --platform ios
```

**Note**: Your `eas.json` has `simulator: true` for development profile. For physical device, you may need to update it:

**Update `eas.json`** (if building for physical device):
```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "simulator": false  // Change to false for physical device
      }
    }
  }
}
```

**After build completes**:
1. Download `.ipa` from Expo dashboard
2. Connect iPhone via USB
3. Install via Xcode or Apple Configurator

---

## 📋 Build Process

### Step 1: Start the Build

```bash
cd mobile
eas build --profile simulator --platform ios
```

**What happens**:
1. EAS uploads your code
2. Builds in the cloud (5-15 minutes)
3. Provides download link

### Step 2: Monitor Build

**Watch progress**:
- Expo dashboard: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds
- Or check terminal for build URL

### Step 3: Download & Install

**For Simulator**:
```bash
# Download the .tar.gz file
# Extract it
tar -xzf RichesReach-*.tar.gz

# Install on simulator (make sure simulator is running)
xcrun simctl install booted ./RichesReach.app
```

**For Physical Device**:
- Download `.ipa` file
- Connect device via USB
- Install via Xcode (Window > Devices and Simulators)
- Or use Apple Configurator

### Step 4: Trust the App (Physical Device Only)

**On iPhone**:
1. Settings > General > VPN & Device Management
2. Trust "Apple Development" or your developer profile

---

## 🎯 Quick Start (Recommended)

**For fastest testing, use simulator build**:

```bash
cd mobile
eas build --profile simulator --platform ios
```

**Wait for build** (5-15 minutes), then:
1. Download `.tar.gz`
2. Extract
3. Install on simulator
4. Start Expo: `npx expo start --clear`
5. Scan QR or press `i` in Expo terminal

---

## 🔧 Troubleshooting

### Build Fails?

**Check**:
- `eas.json` syntax is correct
- All dependencies are in `package.json`
- EAS account has build credits

**Fix**:
```bash
eas build:configure  # Reconfigure if needed
```

### "Profile Not Found"?

**Check** `eas.json` has the profile you're using:
- `simulator` profile exists
- `development` profile exists

### Already Have a Build?

**Check existing builds**:
```bash
eas build:list
```

**Use existing build** if it's recent (within 7 days)

---

## ✅ After Installation

**Once dev client is installed**:

1. **Start Expo**:
   ```bash
   cd mobile
   npx expo start --clear
   ```

2. **Open dev client** on simulator/device

3. **Scan QR** or press `i` (simulator)

4. **Watch logs** for:
   - `[API_BASE at runtime]`
   - `[GQL]` queries
   - `🔐` authentication

5. **Login** with: `test@example.com` / `testpass123`

6. **Data should load!** 🎉

---

## 📝 Summary

**Quickest Path**:
1. `eas build --profile simulator --platform ios`
2. Wait 5-15 minutes
3. Download & install on simulator
4. `npx expo start --clear`
5. Press `i` to launch
6. Login and test!

**Full Guide**: See this file for detailed steps

