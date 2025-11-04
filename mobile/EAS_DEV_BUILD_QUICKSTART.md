# RichesReach - EAS Dev Build Quick Start

## ✅ Setup Complete!

All prerequisites and configuration are verified:
- ✅ EAS CLI installed
- ✅ expo-dev-client plugin configured
- ✅ eas.json configured for simulator builds
- ✅ Bundle ID: com.richesreach.app
- ✅ Installation script ready

## 📦 When EAS Build Completes

### Step 1: Download the Build
When the EAS build finishes, you'll get a download URL. Download the artifact (.app, .zip, or .tar.gz) to `~/Downloads/`

### Step 2: Install on Simulator
```bash
cd /Users/marioncollins/RichesReach/mobile

# Auto-detect and install (picks newest RichesReach artifact from ~/Downloads)
./install_dev_build.sh

# Or specify a path
./install_dev_build.sh ~/Downloads/RichesReach.app
./install_dev_build.sh ~/Downloads/RichesReach.tar.gz
```

### Step 3: Start Metro with Dev Client
```bash
npx expo start -c --dev-client
```

Then press `i` to open in iOS simulator, or click "Open in iOS" in the Metro bundler.

## 🔍 Monitor Build Progress

```bash
# Watch the build log
tail -f /tmp/eas_build.log

# Check EAS dashboard
open https://expo.dev/accounts/marion205/projects/richesreach-ai/builds
```

## 🛠️ Common Fixes

### "No development build installed"
- Make sure you're using: `npx expo start --dev-client` (not just `expo start`)
- Verify bundle ID matches: `com.richesreach.app`

### Simulator Issues
```bash
# Clean and reset
xcrun simctl terminate booted com.richesreach.app || true
xcrun simctl uninstall booted com.richesreach.app || true
xcrun simctl erase all  # WARNING: wipes all sims
```

### Wrong Architecture Error
- Make sure `eas.json` has `"ios": { "simulator": true }` in development profile
- Rebuild with: `eas build --profile development --platform ios`

## 📝 Quick Reference

**Build a new dev client:**
```bash
eas build --profile development --platform ios
```

**Install script usage:**
```bash
./install_dev_build.sh                    # Auto-detect
./install_dev_build.sh /path/to/app.app   # Specific path
```

**Start development:**
```bash
npx expo start -c --dev-client
```

## 🎯 What This Enables

- ✅ Native modules (WebRTC, ARKit) work properly
- ✅ Hot reload and Fast Refresh
- ✅ Custom native code support
- ✅ No "No development build" errors
- ✅ Full development experience

---

**Build Status:** Check `/tmp/eas_build.log` or the EAS dashboard for progress.

