# RichesReach - Development Build Workflows

## 🏠 Local iOS Dev Build (No EAS)

Complete local build setup - runs on your machine:

```bash
cd /Users/marioncollins/RichesReach/mobile

# 1. Ensure expo-dev-client is installed
npx expo install expo-dev-client

# 2. Generate native iOS project
npx expo prebuild --platform ios

# 3. Install CocoaPods dependencies
cd ios
pod install --repo-update
cd ..

# 4. Build and install to simulator (takes 5-10 min first time)
npx expo run:ios

# 5. Start Metro with dev client
npx expo start --dev-client
```

**Note:** First build takes 5-10 minutes. Subsequent builds are faster (1-2 min).

---

## ☁️ Install EAS Simulator Artifact

When EAS build completes and you have the artifact in Downloads:

```bash
cd /Users/marioncollins/RichesReach/mobile

# 1. Open simulator
open -a Simulator

# 2. Install (auto-detects from ~/Downloads)
./install_dev_build.sh

# 3. Start Metro with dev client
npx expo start --dev-client
```

---

## 📁 Install EAS Artifact by Explicit Path

If you want to specify the exact path to the artifact:

```bash
cd /Users/marioncollins/RichesReach/mobile

# 1. Open simulator
open -a Simulator

# 2. Install from specific path
./install_dev_build.sh ~/Downloads/RichesReach.app
# Or: ./install_dev_build.sh ~/Downloads/RichesReach.tar.gz
# Or: ./install_dev_build.sh ~/Downloads/RichesReach.zip

# 3. Start Metro with dev client
npx expo start --dev-client
```

---

## 🔄 If Metro is Already Running

To restart Metro with dev client mode:

```bash
# Kill existing Metro
pkill -f "expo start" || true

# Start fresh with dev client
npx expo start --dev-client
```

---

## ✅ Verify Dev Client Installation

Check if the dev client is installed on simulator:

```bash
xcrun simctl get_app_container booted com.richesreach.app || echo "Not installed"
```

If installed, this will show the app path. If not, you'll see "Not installed".

---

## 🎯 Quick Comparison

| Method | Speed | Requirements | Best For |
|--------|-------|--------------|----------|
| **Local Build** | 5-10 min (first) | Xcode, CocoaPods | Offline, faster iterations after first build |
| **EAS Build** | 5-10 min (always) | EAS account | Clean builds, CI/CD, no local setup |

---

## 🛠️ Troubleshooting

### Local Build Issues

**CocoaPods errors:**
```bash
cd ios
rm -rf Pods Podfile.lock ~/Library/Caches/CocoaPods
pod install --repo-update
cd ..
```

**Xcode build fails:**
```bash
# Clean build folder
cd ios
xcodebuild clean -workspace RichesReach.xcworkspace -scheme RichesReach
cd ..
npx expo run:ios
```

### EAS Build Issues

**Wrong simulator architecture:**
- Verify `eas.json` has `"ios": { "simulator": true }` in development profile
- Rebuild: `eas build --profile development --platform ios`

**Installation fails:**
```bash
# Clean simulator
xcrun simctl terminate booted com.richesreach.app || true
xcrun simctl uninstall booted com.richesreach.app || true
./install_dev_build.sh
```

---

## 📝 Quick Reference

**Local build:**
```bash
cd mobile && npx expo run:ios && npx expo start --dev-client
```

**EAS build:**
```bash
eas build --profile development --platform ios
# Then: ./install_dev_build.sh && npx expo start --dev-client
```

**Verify installation:**
```bash
xcrun simctl get_app_container booted com.richesreach.app
```

---

**Current Build Status:** Check `/tmp/eas_build.log` for EAS build progress.

