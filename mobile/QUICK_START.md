# Quick Start Guide - RichesReach Mobile

## Common Issue: Directory Mismatch

If you see an error like:
```
ConfigError: The expected package.json path: /Users/.../mobile/mobile/package.json does not exist
```

You're in the wrong directory! The project root is `/Users/marioncollins/RichesReach/mobile/`

## Quick Fix

### Option 1: Use the Start Script (Recommended)
```bash
cd /Users/marioncollins/RichesReach/mobile
./start.sh
```

### Option 2: Manual Start
```bash
cd /Users/marioncollins/RichesReach/mobile
npx expo start --clear
```

## Verify You're in the Right Place

You should see these files in the current directory:
- ✅ `package.json`
- ✅ `app.json`
- ✅ `expo-env.d.ts`
- ✅ `src/` directory
- ✅ `.env.local` (for local config)

## For Physical Device Testing

Before starting Expo, set your Mac's IP:
```bash
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
```

Then start Expo:
```bash
cd /Users/marioncollins/RichesReach/mobile
./start.sh
```

## Project Structure

```
mobile/
├── package.json          # Expo project config
├── app.json              # App configuration
├── expo-env.d.ts         # Environment exports
├── start.sh              # Quick start script
├── src/                  # Source code
│   ├── features/         # Feature modules
│   ├── components/       # Shared components
│   └── config/           # Configuration (api.ts, etc.)
├── .env.local            # Local environment variables
└── node_modules/         # Dependencies
```

## Troubleshooting

### Still getting directory errors?
```bash
# Check where you are
pwd

# Should show: /Users/marioncollins/RichesReach/mobile

# If not, navigate there
cd /Users/marioncollins/RichesReach/mobile
```

### Environment variables not loading?
```bash
# Check if .env.local exists
ls -la mobile/.env.local

# Verify contents
cat mobile/.env.local
```

### Cache issues?
```bash
cd /Users/marioncollins/RichesReach/mobile
npx expo start --clear
```

## Next Steps

Once Expo is running:
1. Scan QR code with Expo Go app (physical device)
2. Press `i` for iOS Simulator
3. Press `a` for Android Emulator
4. Press `r` to reload
5. Press `?` for all commands

