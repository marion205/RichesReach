# Quick Start - RichesReach Mobile

## 🚀 Start Expo (Always Works)

```bash
cd /Users/marioncollins/RichesReach/mobile
./start.sh
```

That's it! The script handles everything.

## 📍 Project Root

**Always start from**: `/Users/marioncollins/RichesReach/mobile`

This directory contains:
- ✅ `package.json` - Expo project config
- ✅ `app.json` - App configuration
- ✅ `start.sh` - Quick start script
- ✅ `.env.local` - Environment variables (IP: 192.168.1.240:8000)

## 🔧 For Physical Device Testing

The `.env.local` file is already configured with your Mac's IP:
```
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000
```

If your Mac's IP changes, update `.env.local`:
```bash
echo "EXPO_PUBLIC_API_BASE_URL=http://YOUR_NEW_IP:8000" > .env.local
```

## ✅ Verification

After starting Expo, check the console logs. You should see:
```
[API_BASE at runtime] http://192.168.1.240:8000
```

If you see `localhost:8000`, the environment variable isn't loading. Restart Expo.

## 🐛 Troubleshooting

### "ConfigError: package.json not found"
- You're in the wrong directory
- Run: `cd /Users/marioncollins/RichesReach/mobile`

### Timeout errors on physical device
- Check `.env.local` has the correct IP
- Restart Expo after changing `.env.local`
- Verify backend server is running: `curl http://192.168.1.240:8000/health`

### Environment not loading
- Delete `.expo` folder: `rm -rf .expo`
- Restart with cache clear: `./start.sh` (already includes `--clear`)

## 📱 Next Steps

1. Start Expo: `./start.sh`
2. Scan QR code or press `i` for iOS Simulator
3. Test family sharing feature - should work now!

