# Development Client Setup Guide 🚀

## Why Development Client?

Your RichesReach app uses custom native modules that require a development build:
- ✅ 3D Constellation Orb (Reanimated, Gesture Handler)
- ✅ Haptic Feedback (expo-haptics)
- ✅ AI/ML integrations
- ✅ Real-time WebSocket connections

**Expo Go** can't run these features, so you need a **development client**.

## Quick Start

### Option 1: Build & Install (Recommended)

```bash
cd /Users/marioncollins/RichesReach/mobile

# Build development client for simulator
./build-dev-client.sh simulator

# After build completes, install it
./install-dev-client.sh /path/to/RichesReach.app
```

### Option 2: Manual Steps

1. **Build the client**:
   ```bash
   eas build --profile simulator --platform ios
   ```

2. **Download from Expo Dashboard**:
   - Go to: https://expo.dev/accounts/[your-account]/projects/richesreach-ai/builds
   - Download the `.tar.gz` file

3. **Extract**:
   ```bash
   tar -xzf path/to/your-build.tar.gz
   ```

4. **Install on Simulator**:
   ```bash
   # Make sure simulator is running
   open -a Simulator
   
   # Install the app
   xcrun simctl install booted ./RichesReach.app
   ```

5. **Start Expo**:
   ```bash
   ./start.sh
   # Press 'i' to launch on simulator
   ```

## Prerequisites

### ✅ Already Set Up
- EAS CLI installed (`/opt/homebrew/bin/eas`)
- `eas.json` configured with development profiles
- EAS project ID in `app.json`

### ⚠️ Check Login
```bash
eas whoami
```

If not logged in:
```bash
eas login
```

## Build Profiles

Your `eas.json` has two development profiles:

### 1. `simulator` (Recommended for Development)
- ✅ Fastest builds
- ✅ Simulator-only (no device provisioning needed)
- ✅ Perfect for testing Constellation Orb gestures

### 2. `development` (For Physical Devices)
- ✅ Can install on real devices
- ✅ Requires Apple Developer account
- ✅ Use for testing haptics on real device

## Build Options

### Cloud Build (Recommended)
```bash
eas build --profile simulator --platform ios
```
- ✅ No Xcode required
- ✅ 5-10 minutes
- ✅ Free tier: 30 builds/month

### Local Build (Faster, but requires Xcode)
```bash
eas build --profile simulator --platform ios --local
```
- ✅ 2-5 minutes
- ✅ Requires Xcode 16+ installed
- ✅ Requires Command Line Tools

## Installation on Simulator

### Automatic (Using Script)
```bash
./install-dev-client.sh /path/to/RichesReach.app
```

### Manual
```bash
# 1. Open Simulator
open -a Simulator

# 2. Install app
xcrun simctl install booted /path/to/RichesReach.app

# 3. Verify installation
xcrun simctl listapps booted | grep RichesReach
```

## Running the App

1. **Start Expo**:
   ```bash
   ./start.sh
   ```

2. **Launch on Simulator**:
   - Press `i` in the Expo terminal
   - Or: `npx expo start --ios`

3. **The dev client will**:
   - Open automatically
   - Connect to Metro bundler
   - Load your app with all native features

## Troubleshooting

### "No simulator booted"
```bash
# Boot a simulator
xcrun simctl boot "iPhone 16"

# Or open Simulator app
open -a Simulator
```

### "Build failed - native deps"
```bash
# Install iOS pods
cd ios
pod install
cd ..

# Rebuild
eas build --profile simulator --platform ios
```

### "Profile not found"
Your `eas.json` is already configured correctly. If you see this error:
```bash
eas build:configure
```

### "Port conflict"
```bash
# Kill old Metro processes
pkill -f "Metro Bundler"

# Restart
./start.sh
```

### "Environment variables not loading"
Environment variables (`EXPO_PUBLIC_*`) are runtime, not build-time. They load when Metro starts, not when the app builds.

Check `.env.local`:
```bash
cat .env.local
# Should show: EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
```

## Development Workflow

Once the dev client is installed:

1. **Start Expo**: `./start.sh`
2. **Press `i`**: Launches on simulator
3. **Make changes**: Hot reload works automatically
4. **Press `r`**: Reload manually if needed
5. **Press `?`**: See all commands

## Speed Tips

### Faster Iteration
- Use `simulator` profile (faster than `development`)
- Local builds are faster than cloud (if Xcode is set up)
- Once installed, you only rebuild when native code changes

### Hot Reload
- JS changes: Instant (hot reload)
- Native changes: Requires rebuild
- Config changes: Restart Metro (`./start.sh`)

## Next Steps

After the dev client is installed and running:

1. ✅ Test Constellation Orb gestures
2. ✅ Verify family sharing works
3. ✅ Test AI/ML features
4. ✅ Check WebSocket real-time sync

## Build Status

Check your builds at:
https://expo.dev/accounts/[your-account]/projects/richesreach-ai/builds

## Need Help?

- **Build logs**: Check Expo dashboard
- **Install issues**: Check simulator logs: `xcrun simctl spawn booted log stream`
- **Metro issues**: `./start.sh` with `--clear` flag (already included)

