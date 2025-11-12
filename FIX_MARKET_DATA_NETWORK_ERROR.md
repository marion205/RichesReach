# Fix: Market Data Network Error - Using Mock Data Fallback

## 🔍 Problem

Your app is showing network errors when fetching market quotes:
- `⚠️ Network error for quotes, using mock data fallback`
- `Network request failed` errors in console
- Requests to `/api/market/quotes` are pending/failing

**Root Cause**: The backend server is not running, so the app can't fetch real market data.

---

## ✅ Solution: Start the Backend Server

### Step 1: Open a New Terminal

Keep your Expo terminal running, and open a **new terminal window**.

### Step 2: Navigate to Project Directory

```bash
cd /Users/marioncollins/RichesReach
```

### Step 3: Start the Backend Server

```bash
python3 main_server.py
```

### Step 4: Verify Server Started

You should see output like:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 Test the Server

### Test Health Endpoint

In another terminal:
```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{"status": "ok", "schemaVersion": "1.0.0", "timestamp": "..."}
```

### Test Quotes Endpoint

```bash
curl 'http://localhost:8000/api/market/quotes?symbols=AAPL,MSFT,TSLA'
```

**Expected Response**:
```json
{
  "quotes": [
    {
      "symbol": "AAPL",
      "price": 150.25,
      "change": 1.25,
      "changePercent": 0.84,
      ...
    },
    ...
  ]
}
```

---

## 📱 After Starting Server

Once the server is running:

1. **The app will automatically reconnect** (no need to restart Expo)
2. **Network errors will stop** - requests will succeed
3. **Real market data will load** - no more mock data fallback
4. **Console logs will show**:
   - `✅ Successfully fetched X quotes`
   - `📦 Raw response: {...}`

---

## 🔧 Troubleshooting

### Server Won't Start

**Check Python version**:
```bash
python3 --version
# Should be Python 3.8+
```

**Check if port 8000 is in use**:
```bash
lsof -i :8000
# If something is using it, kill it: kill -9 <PID>
```

**Install missing dependencies**:
```bash
pip3 install fastapi uvicorn python-dotenv
```

### Server Starts But App Still Can't Connect

**For iOS Simulator**:
- Should work automatically with `localhost:8000`
- Check that `API_BASE` in console shows `http://localhost:8000`

**For Physical Device**:
- Need to use your Mac's LAN IP address
- Set environment variable: `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000`
- Replace `192.168.1.240` with your Mac's actual IP address

**Find your Mac's IP**:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### Check API Base URL in App

Look in Expo console for:
```
[API_BASE at runtime] http://localhost:8000
```

If it shows a different URL, that's the issue.

---

## 📊 What Data Will Be Real vs Mock

### ✅ Real Data (Once Server is Running):
- **Market Quotes** (`/api/market/quotes`) - Real stock prices
- **GraphQL Benchmark Data** (`benchmarkSeries`) - Real market data
- **Portfolio Data** (if you have portfolios in database)
- **Stock Research** (via GraphQL queries)

### ⚠️ Still Mock Data:
- **Portfolio History** (if no database entries)
- **User Portfolios** (if not created in database)
- **Some UI elements** (until real data loads)

---

## 🚀 Quick Start Command

Run this in a new terminal:
```bash
cd /Users/marioncollins/RichesReach && python3 main_server.py
```

Then check your Expo console - the network errors should disappear and real data should load!

---

**Last Updated**: $(date)

