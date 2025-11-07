# Expo Start Directory Fix ✅

## Problem Solved
The Expo start error was due to running the command from the wrong directory. The project root is:
```
/Users/marioncollins/RichesReach/mobile
```

## Quick Start (Always Works)

### Option 1: Use the Start Script (Recommended)
```bash
cd /Users/marioncollins/RichesReach/mobile
./start.sh
```

This script:
- ✅ Verifies you're in the correct directory
- ✅ Checks for package.json and app.json
- ✅ Warns if EXPO_PUBLIC_API_BASE_URL is not set
- ✅ Starts Expo with `--clear` flag

### Option 2: Manual Start
```bash
cd /Users/marioncollins/RichesReach/mobile
npx expo start --clear
```

## For Physical Device Testing

Before starting Expo, set your Mac's IP:
```bash
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
```

Or it will be loaded from `.env.local` if present.

## Verify You're in the Right Place

Run this check:
```bash
cd /Users/marioncollins/RichesReach/mobile
pwd  # Should show: /Users/marioncollins/RichesReach/mobile
ls package.json app.json  # Both should exist
```

## Project Structure

```
/Users/marioncollins/RichesReach/mobile/
├── package.json          ✅ Expo project config
├── app.json              ✅ App configuration  
├── start.sh              ✅ Quick start script
├── .env.local            ✅ Local environment (IP: 192.168.1.240:8000)
├── src/                  ✅ Source code
│   ├── features/         ✅ Feature modules
│   ├── components/       ✅ Shared components
│   └── config/           ✅ Configuration (api.ts)
└── node_modules/         ✅ Dependencies
```

## Common Mistakes to Avoid

### ❌ Wrong: Running from nested directory
```bash
cd /Users/marioncollins/RichesReach/mobile/mobile  # WRONG!
npx expo start
```

### ✅ Correct: Running from project root
```bash
cd /Users/marioncollins/RichesReach/mobile  # CORRECT!
npx expo start --clear
```

## Environment Variables

The app will use:
1. `EXPO_PUBLIC_API_BASE_URL` environment variable (if set)
2. `.env.local` file (if exists)
3. Default: `http://localhost:8000` (simulator only)

For physical devices, ensure `.env.local` contains:
```
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
```

## Next Steps

1. **Navigate to project root**:
   ```bash
   cd /Users/marioncollins/RichesReach/mobile
   ```

2. **Start Expo**:
   ```bash
   ./start.sh
   # or
   npx expo start --clear
   ```

3. **Reload app on device** - The timeout errors should be gone!

## Troubleshooting

### Still getting directory errors?
```bash
# Use absolute path
cd /Users/marioncollins/RichesReach/mobile
pwd  # Verify
./start.sh
```

### Environment not loading?
```bash
# Check .env.local
cat /Users/marioncollins/RichesReach/mobile/.env.local

# Or set manually before starting
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
cd /Users/marioncollins/RichesReach/mobile
npx expo start --clear
```

### Cache issues?
```bash
cd /Users/marioncollins/RichesReach/mobile
npx expo start --clear
# The --clear flag handles this automatically
```

## Success Indicators

When Expo starts correctly, you should see:
- ✅ Metro bundler starting
- ✅ QR code displayed
- ✅ "Press ? to show a list of all available commands"
- ✅ No ConfigError about package.json

In your app console, you should see:
- ✅ `[API_BASE at runtime] http://192.168.1.240:8000` (for physical device)
- ✅ No timeout errors when creating family groups

