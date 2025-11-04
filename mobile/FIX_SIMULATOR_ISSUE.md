# Why Your Simulator Stopped Working

## The Problem

**Xcode 26.0.1 (iOS 26.0 SDK) is incompatible with React Native 0.81.5**

The build fails with C++ header errors:
```
use of undeclared identifier '__enable_hash_helper'
no template named '__check_hash_requirements'
```

## What Happened?

Even though you said nothing changed, **Xcode likely auto-updated** to 26.0.1 (beta/newer version). This happens if:
- Automatic app updates are enabled
- You're enrolled in Xcode beta updates
- macOS System Updates pushed a newer Xcode

## Solutions

### ✅ Solution 1: Use EAS Build (Recommended - Already Configured)

Your `eas.json` is already set to use Xcode 15.4 which works:

```bash
cd /Users/marioncollins/RichesReach/mobile

# Build remotely (uses Xcode 15.4, avoids local issues)
eas build --profile development --platform ios

# Wait for build to complete (10-15 min)
# Then install the .app file on your simulator
./install_dev_build.sh
```

**Pros**: Works immediately, no local Xcode changes needed
**Cons**: Requires internet, takes 10-15 minutes

### Solution 2: Download Xcode 15.4

If you want to build locally:

1. Download Xcode 15.4 from [developer.apple.com](https://developer.apple.com/download/all/)
2. Install it alongside Xcode 26.0.1:
   ```bash
   # Move existing Xcode
   sudo mv /Applications/Xcode.app /Applications/Xcode-26.0.1.app
   
   # Install Xcode 15.4 to /Applications/Xcode.app
   # Or keep both: /Applications/Xcode-15.4.app
   ```
3. Switch command line tools:
   ```bash
   sudo xcode-select --switch /Applications/Xcode-15.4.app/Contents/Developer
   ```
4. Build:
   ```bash
   cd /Users/marioncollins/RichesReach/mobile
   npm run ios
   ```

### Solution 3: Upgrade React Native (Future Fix)

React Native 0.82+ should support iOS 26.0 SDK, but requires migration work.

## Quick Check

**Verify simulator works** (it should - the issue is the build, not simulator):
```bash
xcrun simctl boot "iPhone 15 Pro"
open -a Simulator
```

**Verify Xcode version:**
```bash
xcodebuild -version
```

## Recommended Action

**Use EAS Build** - it's already configured and will work immediately:
```bash
eas build --profile development --platform ios
```

