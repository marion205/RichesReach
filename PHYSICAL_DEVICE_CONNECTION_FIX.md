# Physical Device Connection Fix ✅

## Issue
The app is running on a physical device (192.168.1.240) and trying to connect to `localhost:8000`, which doesn't work because `localhost` on the device refers to the device itself, not your Mac.

## Solution

### Your Mac's IP Address
**192.168.1.240** (detected from network interface)

### Quick Fix

**Option 1: Set Environment Variable (Recommended)**

Before starting Expo/Metro bundler:
```bash
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
```

Then restart your Expo development server.

**Option 2: Create .env File**

I've created `mobile/.env.local` with the correct IP. If Expo doesn't pick it up automatically, you may need to:

1. Install `expo-constants` if not already installed
2. Restart Metro bundler
3. Reload the app

**Option 3: Update app.json/app.config.js**

Add to your Expo config:
```json
{
  "extra": {
    "API_BASE": "http://192.168.1.240:8000"
  }
}
```

## Verify Connection

Test from your Mac to ensure the server is accessible:
```bash
curl http://192.168.1.240:8000/health
```

Should return:
```json
{"status":"ok","schemaVersion":"1.0.0","timestamp":"..."}
```

## Current Configuration

The app is configured to:
- Check `EXPO_PUBLIC_API_BASE_URL` environment variable first
- Fall back to `localhost:8000` (only works in simulator)
- Log the resolved URL at runtime

## Next Steps

1. **Set the environment variable**:
   ```bash
   export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
   ```

2. **Restart Expo/Metro bundler** (important!)

3. **Reload the app** on your device

4. **Check the console logs** - you should see:
   ```
   [API_BASE at runtime] http://192.168.1.240:8000
   ```

5. **Try creating a family group again** - it should work now!

## Troubleshooting

### If still timing out:

1. **Check firewall**: Make sure port 8000 is not blocked
   ```bash
   # macOS: System Settings > Network > Firewall
   ```

2. **Verify server is listening on all interfaces**:
   ```bash
   netstat -an | grep 8000
   ```
   Should show: `*.8000` or `0.0.0.0:8000`

3. **Test from device's network**:
   - Open Safari on your iPhone
   - Go to: `http://192.168.1.240:8000/health`
   - Should see JSON response

4. **Check IP address hasn't changed**:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

## Server Configuration

The server is configured to listen on all interfaces (`0.0.0.0:8000`), so it should be accessible from your local network.

If you need to restart the server:
```bash
cd /Users/marioncollins/RichesReach
python3 main_server.py > /tmp/main_server.log 2>&1 &
```

