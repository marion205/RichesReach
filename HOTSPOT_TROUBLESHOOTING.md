# 📱 Hotspot Connection Troubleshooting

## 🎯 Quick Fix (60 seconds)

### 1. Test from Phone Browser First
Open your phone's browser and go to:
```
http://172.20.10.8:8000/health/
```

**Expected result**: `{"ok": true, "mode": "simple"}`

**If this fails**: The issue is networking, not the app. Skip to "Plan B" below.

### 2. Hard-Pin Mobile App to Hotspot IP
The mobile app is now configured to use `172.20.10.8:8000` directly.

### 3. Restart Everything
```bash
# Kill existing processes
pkill -f "manage.py runserver"
pkill -f "expo start"

# Restart Django (in backend/backend/)
python3 manage.py runserver 0.0.0.0:8000

# Restart React Native (in mobile/)
npx expo start --clear
```

## 🔧 If Hotspot Still Doesn't Work

### Plan B: Use ngrok (Public Tunnel)
```bash
# Install ngrok if you haven't
brew install ngrok

# Tunnel your Django server
ngrok http 8000

# Copy the https://xxxxxxxx.ngrok.io URL
# Update mobile/config/api.ts:
export const API_HTTP = 'https://xxxxxxxx.ngrok.io';
```

### Plan C: Same Wi-Fi (Best Option)
1. Connect both phone and laptop to the same Wi-Fi network
2. Find your Wi-Fi IP: `ipconfig getifaddr en0`
3. Update mobile app to use that IP instead of hotspot IP

## 🚨 Common Issues

### "Network request failed" in Mobile App
**Cause**: Mobile app can't reach Django server
**Fix**: 
1. Test phone browser first: `http://172.20.10.8:8000/health/`
2. If that fails, use ngrok or switch to same Wi-Fi

### Django Server Not Accessible
**Cause**: Firewall or binding issues
**Fix**:
1. Ensure Django runs on `0.0.0.0:8000` (not `127.0.0.1:8000`)
2. Check macOS firewall: System Settings → Privacy & Security → Firewall
3. Allow Python/Terminal incoming connections

### IP Address Changed
**Cause**: Hotspot IP changed when reconnecting
**Fix**: Run the fix script:
```bash
cd mobile
./scripts/fix-hotspot-connection.sh
```

## 📋 Demo Checklist

Before any demo with hotspot:

1. ✅ **Test phone browser**: `http://172.20.10.8:8000/health/`
2. ✅ **Django server**: Running on `0.0.0.0:8000`
3. ✅ **Mobile app**: Hard-pinned to `172.20.10.8:8000`
4. ✅ **Firewall**: Python allowed incoming connections
5. ✅ **Backup plan**: ngrok ready if hotspot fails

## 🆘 Emergency Fallback

If everything breaks during demo:

1. **Quick fix**: Use ngrok
   ```bash
   ngrok http 8000
   # Update mobile app to use ngrok URL
   ```

2. **Alternative**: Switch to same Wi-Fi
   - Connect laptop and phone to same Wi-Fi
   - Update IP in mobile app
   - Restart both servers

3. **Last resort**: Use iOS Simulator
   - Works with localhost
   - No network issues
   - Perfect for demos

---

**Remember**: Always test the phone browser first - it tells you instantly if it's a networking or app configuration issue! 🎯
