# Manual Metro Start Instructions

## ⚠️ Important: Run These Commands in YOUR Terminal (Not Agent Terminal)

The agent terminals are read-only. You need to run Metro in your own terminal window.

## Step 1: Open a New Terminal Window

Open Terminal.app (or iTerm) - a fresh terminal window you can type in.

## Step 2: Navigate to Mobile Directory

```bash
cd /Users/marioncollins/RichesReach/mobile
```

## Step 3: Start Metro

```bash
npx expo start --clear
```

## Step 4: Wait for Metro to Start

You should see:
- QR code
- Options like "Press i to open iOS simulator"
- "Metro waiting on http://localhost:8081"

## Step 5: Open iOS Simulator

In the Metro terminal, press:
- **`i`** - Opens iOS simulator
- OR scan QR code with Expo Go app on your phone

## Step 6: Test Portfolio Screen

Once app loads:
1. Login (or use dev mode)
2. Navigate to **Portfolio** tab
3. You should see:
   - Constellation Orb (if bank linked)
   - OR traditional portfolio view (if no bank)

## Troubleshooting

**If Metro won't start:**
```bash
# Kill everything
pkill -9 -f "expo"
pkill -9 -f "metro"

# Clear everything
cd /Users/marioncollins/RichesReach/mobile
rm -rf .expo .metro node_modules/.cache

# Start fresh
npx expo start --clear
```

**If you see "port 8081 in use":**
```bash
lsof -ti:8081 | xargs kill -9
```

**If you see module errors:**
The metro.config.js has been fixed. Try:
```bash
npx expo start --clear --reset-cache
```

---

## Backend Status

The backend server should be running on `http://localhost:8000`

To verify:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok",...}`

---

**Remember:** Run Metro in YOUR terminal, not the agent terminal!

