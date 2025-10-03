# 🌐 Network Setup & Troubleshooting Guide

This guide ensures your RichesReach app works reliably across different development environments.

## 🎯 Quick Setup (Do This Once)

### 1. Django Server Configuration
The Django server is now configured to:
- ✅ Bind to all interfaces (`0.0.0.0:8000`)
- ✅ Allow multiple hosts in `ALLOWED_HOSTS`
- ✅ Include CSRF trusted origins for all common IPs

### 2. Mobile App Configuration
The mobile app now automatically detects the right API endpoint:
- ✅ **iOS Simulator**: Uses `localhost:8000`
- ✅ **Android Emulator**: Uses `10.0.2.2:8000`
- ✅ **Real Device**: Uses `EXPO_PUBLIC_API_HOST` or falls back to `localhost`

## 🚀 Starting the App

### Backend (Django)
```bash
cd backend/backend
export POLYGON_API_KEY="uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2"
export FINNHUB_API_KEY="d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"
export DISABLE_ALPHA_VANTAGE="true"
export USE_OPENAI=true
export OPENAI_API_KEY=your_key_here
python3 manage.py runserver 0.0.0.0:8000
```

### Frontend (React Native)
```bash
cd mobile
npx expo start --clear
```

## 🔧 For Real Device Testing

When using a real phone/tablet, you need to set your computer's IP address:

### Option 1: Automatic IP Detection
```bash
cd mobile
./scripts/update-ip.sh
```

### Option 2: Manual Setup
1. Find your IP: `ifconfig | grep "inet " | grep -v 127.0.0.1`
2. Add to `.env`: `EXPO_PUBLIC_API_HOST=YOUR_IP_HERE`
3. Restart: `npx expo start --clear`

## 🧪 Testing Connectivity

### Built-in Debug Tools
The app includes a connectivity test screen that checks:
- ✅ Health endpoint (`/health/`)
- ✅ GraphQL endpoint (`/graphql/`)
- ✅ Auth endpoint (`/api/auth/login/`)
- ✅ WebSocket endpoint (`/ws/`)

### Manual Testing
```bash
# Test health endpoint
curl http://YOUR_IP:8000/health/

# Test GraphQL
curl -X POST http://YOUR_IP:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ stocks { symbol companyName currentPrice } }"}'
```

## 🚨 Troubleshooting

### "Network request failed" Errors

**Problem**: Mobile app can't reach Django server

**Solutions**:
1. **Check Django server**: `curl http://localhost:8000/health/`
2. **Check IP binding**: Server should show `Starting development server at http://0.0.0.0:8000/`
3. **Update IP for real device**: Use `./scripts/update-ip.sh`
4. **Check firewall**: Ensure port 8000 is open

### "Connection refused" Errors

**Problem**: Django server not accessible

**Solutions**:
1. **Restart Django**: `python3 manage.py runserver 0.0.0.0:8000`
2. **Check port**: Make sure nothing else is using port 8000
3. **Check environment**: Ensure all API keys are set

### "Invalid JWT format" Errors

**Problem**: Authentication issues

**Solutions**:
1. **Clear app cache**: Restart React Native app
2. **Check auth endpoint**: Test `/api/auth/login/` manually
3. **Verify JWT secret**: Check Django settings

### IP Address Changes

**Problem**: WiFi network changed, IP address different

**Solutions**:
1. **Quick fix**: `./scripts/update-ip.sh`
2. **Manual**: Update `EXPO_PUBLIC_API_HOST` in `.env`
3. **Restart**: `npx expo start --clear`

## 📱 Platform-Specific Notes

### iOS Simulator
- ✅ Uses `localhost` by default
- ✅ No additional configuration needed
- ✅ Works with `127.0.0.1` and `localhost`

### Android Emulator
- ✅ Uses `10.0.2.2` by default
- ✅ Maps to host machine's `127.0.0.1`
- ✅ No additional configuration needed

### Real iOS Device
- ❌ Cannot use `localhost` (refers to device itself)
- ✅ Must use computer's actual IP address
- ✅ Set `EXPO_PUBLIC_API_HOST=YOUR_IP`

### Real Android Device
- ❌ Cannot use `localhost` (refers to device itself)
- ✅ Must use computer's actual IP address
- ✅ Set `EXPO_PUBLIC_API_HOST=YOUR_IP`

## 🔒 Security Notes

### Development Mode
- ✅ `ALLOWED_HOSTS = ["*"]` (dev only)
- ✅ `CORS_ALLOW_ALL_ORIGINS = True` (dev only)
- ✅ CSRF trusted origins include common IPs

### Production Mode
- ✅ Restricted `ALLOWED_HOSTS`
- ✅ Specific CORS origins
- ✅ HTTPS enforcement
- ✅ Security headers enabled

## 🎯 Demo Checklist

Before any demo, run this checklist:

1. **✅ Django Server**: `curl http://localhost:8000/health/`
2. **✅ GraphQL**: Test with stocks query
3. **✅ Mobile App**: Use built-in connectivity test
4. **✅ Real Device**: Test on actual phone/tablet
5. **✅ Network**: Ensure stable WiFi connection
6. **✅ Backup**: Have localhost fallback ready

## 🆘 Emergency Fallback

If everything breaks:

1. **Kill all processes**: `pkill -f "manage.py runserver" && pkill -f "expo start"`
2. **Restart Django**: `python3 manage.py runserver 0.0.0.0:8000`
3. **Restart Mobile**: `npx expo start --clear`
4. **Test locally**: Use iOS Simulator with localhost
5. **Check logs**: Look for error messages in console

## 📞 Support

If you're still having issues:
1. Check the console logs for specific error messages
2. Use the built-in connectivity test in the app
3. Verify all environment variables are set
4. Ensure Django server is running on `0.0.0.0:8000`

---

**Remember**: The key to reliable networking is using `0.0.0.0:8000` for Django and the appropriate IP for your mobile platform! 🎯
