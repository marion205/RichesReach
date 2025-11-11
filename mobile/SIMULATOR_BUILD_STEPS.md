# Build Dev Client for Simulator - Step by Step

## ✅ Pre-Flight Checks Complete

**Status**:
- ✅ Watchman warning cleared
- ✅ expo-dev-client installed
- ✅ In correct directory: `mobile/`

---

## 🚀 Step 1: Build Dev Client for Simulator

**Run this command**:
```bash
cd /Users/marioncollins/RichesReach/mobile
npx expo run:ios
```

**What happens**:
1. Compiles native code locally
2. Builds development client
3. Installs on iOS Simulator
4. Launches automatically

**Time**: 5-15 minutes (first time), faster after

**Note**: 
- If Xcode asks to trust toolchains → Accept
- If signing warnings appear → Ignore (not needed for Simulator)
- If simulator not found → Xcode will open, select a simulator

---

## ✅ Step 2: Start Expo with Dev Client

**After build completes and app launches**:

```bash
npx expo start --dev-client
```

**This will**:
- Start Metro bundler
- Connect to dev client on simulator
- App will reload automatically
- Show QR code (for reference)

---

## 🧪 Step 3: Test Data Loading

**After app loads**:

1. **Check Expo terminal** for logs:
   ```
   [API_BASE at runtime] http://192.168.1.240:8000
   [ApolloFactory] Creating client with GraphQL URL: ...
   [GQL] GetMe (query) -> ...
   🔐 Apollo Client: ...
   ```

2. **Login** with:
   - Email: `test@example.com`
   - Password: `testpass123`

3. **Watch for data loading**

---

## 🔧 Troubleshooting

### Xcode Asks to Trust Toolchains

**Fix**: Click "Trust" or "Allow" - this is normal

### Signing Warnings

**Fix**: Ignore them - Simulator doesn't require code signing

### Simulator Not Found

**Fix**: 
- Xcode will open automatically
- Select a simulator from the device list
- Or run: `open -a Simulator` first

### Build Fails with Pod Install Error

**Fix**:
```bash
cd ios
pod install
cd ..
npx expo run:ios
```

### "No such file or directory: mobile"

**Fix**: You're already in mobile directory - just run `npx expo run:ios` (no `cd mobile` needed)

---

## 📋 Quick Reference

**Complete sequence**:
```bash
cd /Users/marioncollins/RichesReach/mobile
watchman watch-del '/Users/marioncollins/RichesReach' ; watchman watch-project '/Users/marioncollins/RichesReach'
npx expo install expo-dev-client
npx expo run:ios
# After build completes:
npx expo start --dev-client
```

---

## ✅ Success Indicators

You'll know it's working when:
- ✅ Build completes without errors
- ✅ App installs on simulator
- ✅ App launches automatically
- ✅ `expo start --dev-client` connects
- ✅ App reloads when you make changes
- ✅ Data loads after login

---

## 🎯 Why This Works

**Simulator builds**:
- ✅ Build locally (no EAS/cloud)
- ✅ No Apple Developer account needed
- ✅ No code signing required
- ✅ Fast iteration

**Physical device builds**:
- ❌ Require paid Apple Developer account ($99/year)
- ❌ Need code signing
- ❌ Slower (cloud build)

**For now**: Simulator is perfect for development and testing!

---

**Ready to build!** Run `npx expo run:ios` and let it build! 🚀

