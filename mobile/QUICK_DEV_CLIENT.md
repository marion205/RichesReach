# Quick Dev Client Setup ⚡

## TL;DR

```bash
cd /Users/marioncollins/RichesReach/mobile

# 1. Build (5-10 min)
./build-dev-client.sh simulator

# 2. After build, install
./install-dev-client.sh /path/to/RichesReach.app

# 3. Start Expo
./start.sh
# Press 'i' to launch
```

## What You Need

✅ **Already have**:
- EAS CLI installed
- `eas.json` configured
- EAS project ID set

⚠️ **Check login**:
```bash
eas whoami
# If not logged in: eas login
```

## Build Options

### Cloud Build (Easiest)
```bash
npm run build:dev:ios
# or
eas build --profile simulator --platform ios
```
- ✅ No Xcode needed
- ✅ 5-10 minutes
- ✅ Monitor at expo.dev dashboard

### Local Build (Faster)
```bash
npm run build:dev:ios:local
# or
eas build --profile simulator --platform ios --local
```
- ✅ 2-5 minutes
- ⚠️ Requires Xcode 16+

## After Build

1. **Download** from Expo dashboard
2. **Extract**: `tar -xzf build.tar.gz`
3. **Install**: `./install-dev-client.sh ./RichesReach.app`

## That's It!

Once installed, just run `./start.sh` and press `i`. The dev client will launch automatically with all your native features working! 🚀

