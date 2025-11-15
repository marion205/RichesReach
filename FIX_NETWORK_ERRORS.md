# 🔧 Fix Network Request Failed Errors

## Problem
Your app is showing "Network request failed" errors because:
1. **Backend server is not running** on port 8000
2. **API URL is set to localhost** which doesn't work on physical devices

## Solution

### Step 1: Start the Backend Server

```bash
cd /Users/marioncollins/RichesReach
python3 main_server.py
```

**Keep this terminal open!** The server must stay running.

### Step 2: Configure Mobile App for Your Network

Your Mac's IP is: **192.168.1.240**

Create or update `mobile/.env.local`:

```bash
cd mobile
cat > .env.local << 'EOF'
# Local Development - Use Mac's LAN IP for physical devices
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
EXPO_PUBLIC_GRAPHQL_URL=http://192.168.1.240:8000/graphql/
EXPO_PUBLIC_RUST_API_URL=http://192.168.1.240:3001
EXPO_PUBLIC_WS_URL=ws://192.168.1.240:8000/ws
EXPO_PUBLIC_SFU_SERVER_URL=http://192.168.1.240:8000
EXPO_PUBLIC_SIGNAL_URL=ws://192.168.1.240:8000/fireside
EOF
```

### Step 3: Restart Expo with Clear Cache

```bash
cd mobile
npx expo start --clear
```

### Step 4: Verify Connection

In the app console, you should see:
```
[API_BASE at runtime] http://192.168.1.240:8000
[API_BASE] http://192.168.1.240:8000 -> resolved to: http://192.168.1.240:8000
```

## Quick Test

Test the backend from your Mac:
```bash
curl http://192.168.1.240:8000/health
```

Expected: `{"status":"ok",...}`

## Troubleshooting

### Backend Won't Start
- Check if port 8000 is already in use: `lsof -i :8000`
- Check Python dependencies: `pip3 install fastapi uvicorn`

### Still Getting Network Errors
1. **Verify backend is running**: `curl http://localhost:8000/health`
2. **Check firewall**: Make sure port 8000 is not blocked
3. **Verify IP address**: `ifconfig | grep "inet " | grep -v 127.0.0.1`
4. **Check device and Mac are on same WiFi network**

### Using iOS Simulator
If using iOS Simulator (not physical device), you can use `localhost`:
```bash
export EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Alternative: Use Production API

If you don't want to run a local backend, point to production:

```bash
cd mobile
cat > .env.local << 'EOF'
EXPO_PUBLIC_API_BASE_URL=https://api.richesreach.com
EXPO_PUBLIC_GRAPHQL_URL=https://api.richesreach.com/graphql/
EOF
```

Then restart Expo: `npx expo start --clear`

