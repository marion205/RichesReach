# Quick Fix for Physical Device Connection 🚀

## Problem
Your app is running on a physical device and trying to connect to `localhost:8000`, which doesn't work.

## Solution

### Your Mac's IP: `192.168.1.240`

### Step 1: Update Environment Variable

**Before restarting Expo**, set this environment variable:

```bash
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
```

### Step 2: Restart Expo/Metro Bundler

**IMPORTANT**: You must restart Expo for the environment variable to take effect!

1. Stop the current Expo server (Ctrl+C)
2. Start it again:
   ```bash
   cd mobile
   npx expo start
   ```

### Step 3: Reload the App

Shake your device and tap "Reload" or press `r` in the Expo terminal.

### Step 4: Verify

Check the console logs in Expo. You should see:
```
[API_BASE at runtime] http://192.168.1.240:8000
```

Instead of:
```
[API_BASE at runtime] http://localhost:8000
```

## Alternative: Update .env.local

I've added the IP to `mobile/.env.local`. If Expo doesn't pick it up automatically, you may need to:

1. Install `dotenv` or use Expo's built-in env support
2. Restart Metro bundler
3. Clear cache: `npx expo start -c`

## Test Connection

From your Mac, test that the server is accessible:
```bash
curl http://192.168.1.240:8000/health
```

Should return: `{"status":"ok",...}`

## If Still Not Working

1. **Check firewall**: macOS System Settings > Network > Firewall
2. **Verify IP hasn't changed**: `ifconfig | grep "inet " | grep -v 127.0.0.1`
3. **Test from device browser**: Open Safari on iPhone, go to `http://192.168.1.240:8000/health`

## Server Status

✅ Server is running on port 8000
✅ Server is listening on all interfaces (accessible from network)
✅ Family Sharing API is registered

The issue is just the app configuration pointing to `localhost` instead of your Mac's IP.

