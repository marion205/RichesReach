# Starting Backend Server

## 🚀 Quick Start

### Step 1: Open New Terminal

**Keep your Expo terminal running**, and open a **new terminal window**.

### Step 2: Navigate to Project

```bash
cd /Users/marioncollins/RichesReach
```

### Step 3: Start Backend Server

```bash
python3 main_server.py
```

---

## ✅ Expected Output

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 Verify Server is Running

### Test Health Endpoint

In another terminal (or new tab):
```bash
curl http://192.168.1.240:8000/health/
```

**Expected Response**:
```json
{"ok": true, "mode": "simple"}
```

### Test GraphQL Endpoint

```bash
curl -X POST http://192.168.1.240:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

**Expected Response**:
```json
{"data":{"__typename":"Query"}}
```

---

## 📱 Mobile App Connection

Once the backend is running:

1. **Your mobile app** (running via Expo) will connect to:
   - `http://192.168.1.240:8000` (from your `.env.local`)

2. **Check Expo console** for:
   - `[API_BASE at runtime] http://192.168.1.240:8000`
   - Successful API calls
   - Data loading in the app

---

## 🔧 Troubleshooting

### Server Won't Start

**Check Python version**:
```bash
python3 --version
# Should be Python 3.8+
```

**Check dependencies**:
```bash
pip3 install -r requirements.txt
```

**Check port availability**:
```bash
lsof -i :8000
# If something is using port 8000, kill it or use a different port
```

### Server Starts But App Can't Connect

**Check IP address**:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Verify 192.168.1.240 is your Mac's IP
```

**Check firewall**:
- macOS Firewall might be blocking port 8000
- Allow Python through firewall in System Settings

**Test from mobile device**:
- Open browser on phone: `http://192.168.1.240:8000/health/`
- Should return JSON response

### Use Production API Instead

If local backend is problematic, use production:

```bash
cd mobile
echo "EXPO_PUBLIC_API_BASE_URL=https://api.richesreach.com" > .env.local
# Restart Expo (Ctrl+C, then npx expo start --clear)
```

---

## 🎯 Quick Reference

**Start Backend**:
```bash
cd /Users/marioncollins/RichesReach
python3 main_server.py
```

**Stop Backend**:
- Press `Ctrl+C` in the terminal running the server

**Check if Running**:
```bash
curl http://192.168.1.240:8000/health/
```

**View Logs**:
- Server logs appear in the terminal where you ran `python3 main_server.py`

---

## ✅ Success Indicators

You'll know it's working when:
- ✅ Server starts without errors
- ✅ Health endpoint returns `{"ok": true}`
- ✅ Mobile app can fetch data
- ✅ No "no usable data found" errors

---

**Status**: Ready to start backend server! 🚀

