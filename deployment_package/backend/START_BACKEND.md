# Starting the Backend Server

## ❌ Problem: Backend Not Running

The curl test shows the backend is **not running** at `192.168.1.240:8000`. This is why voice processing is "taking forever" - the app can't connect to the server.

## ✅ Solution: Start the Backend

### Option 1: Quick Start (Development)
```bash
cd deployment_package/backend

# Activate virtual environment (if you have one)
source venv/bin/activate  # or: python3 -m venv venv && source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Using Python Directly
```bash
cd deployment_package/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Check if Already Running
```bash
# Check what's on port 8000
lsof -i :8000

# Kill existing process if needed
kill -9 $(lsof -t -i:8000)
```

## 🔍 Verify It's Running

After starting, test:
```bash
# From your Mac
curl http://localhost:8000/health

# From your iPhone (same network)
curl http://192.168.1.240:8000/health
```

Both should return `{"status":"ok"}` or similar.

## 🌐 Network Configuration

**Important:** The server must bind to `0.0.0.0` (not `127.0.0.1`) to be accessible from your iPhone:

```bash
# ✅ CORRECT - accessible from network
uvicorn main:app --host 0.0.0.0 --port 8000

# ❌ WRONG - only accessible from localhost
uvicorn main:app --host 127.0.0.1 --port 8000
```

## 📱 Mobile App Configuration

The mobile app is configured to use:
- `192.168.1.240:8000` for physical devices
- `localhost:8000` for iOS Simulator

If your Mac's IP changed, update `mobile/src/config/api.ts`:
```typescript
const LAN_IP = "192.168.1.240"; // Update this to your current IP
```

## 🔧 Troubleshooting

### Can't Connect from iPhone
1. **Check firewall**: macOS may block port 8000
   ```bash
   # Allow incoming connections on port 8000
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python3
   ```

2. **Verify IP address**: Your Mac's IP might have changed
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

3. **Test connectivity**: From iPhone, ping your Mac
   - Settings → Wi-Fi → (i) next to network → Router IP

### Server Starts But No Response
- Check backend logs for errors
- Verify `OPENAI_API_KEY` is set (for Whisper/LLM)
- Check if port 8000 is already in use

## ✅ Once Running

After starting the backend:
1. ✅ Voice processing will work (no more "taking forever")
2. ✅ Streaming will be fast (~350-450ms first token)
3. ✅ All endpoints will respond

