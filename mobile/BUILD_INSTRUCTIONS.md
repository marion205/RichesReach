# Build Development Client - Step by Step

## ⚠️ Important: Run This in Your Terminal

The build command requires interactive input (Apple account credentials), so you need to run it in your own terminal.

---

## 🚀 Step 1: Start the Build

**In your terminal**, run:

```bash
cd /Users/marioncollins/RichesReach/mobile
eas build --profile development --platform ios
```

**What to expect**:

1. **EAS will ask about Apple account**:
   ```
   Do you want to log in to your Apple account?
   ```
   - **Answer**: `y` (yes) - This allows EAS to manage certificates automatically
   - Or `n` (no) - You'll need to provide credentials manually

2. **If you choose yes**:
   - Enter your Apple ID email
   - Enter your Apple ID password
   - May require 2FA code

3. **Build will start**:
   - Code uploads to EAS
   - Build starts in cloud
   - You'll get a build URL

---

## ⏱️ Step 2: Wait for Build (10-20 minutes)

**Monitor progress**:

- **Terminal**: Will show build status
- **Dashboard**: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds
- **Email**: You'll get notified when build completes

**Build stages**:
1. Uploading code
2. Installing dependencies
3. Building native code
4. Packaging app
5. ✅ Complete

---

## 📥 Step 3: Download .ipa File

**When build completes**:

1. **Get download link**:
   - Terminal will show: `Download: https://expo.dev/...`
   - Or check dashboard: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds

2. **Download the `.ipa` file**:
   - Click the download link
   - Or use: `eas build:download` command
   - Save to: `~/Downloads/RichesReach.ipa`

---

## 📱 Step 4: Install via Xcode

### Prerequisites:
- ✅ Xcode installed
- ✅ iPhone/iPad connected via USB
- ✅ Device unlocked
- ✅ Device trusted on Mac

### Installation Steps:

1. **Open Xcode**:
   ```bash
   open -a Xcode
   ```

2. **Open Devices Window**:
   - Menu: `Window` > `Devices and Simulators`
   - Or keyboard shortcut: `Shift + Cmd + 2`

3. **Select Your Device**:
   - In left sidebar, click on your iPhone/iPad
   - Make sure it shows "Connected" (not "Disconnected")

4. **Install the App**:
   - **Option A**: Drag the `.ipa` file into the "Installed Apps" section
   - **Option B**: Click the "+" button, then select the `.ipa` file

5. **Wait for Installation**:
   - Progress bar will show
   - App icon appears on device when done

---

## 🔐 Step 5: Trust Developer Profile

**On your iPhone/iPad**:

1. **Go to Settings** > **General** > **VPN & Device Management**

2. **Find Developer Profile**:
   - Look for "Apple Development: [your email]" 
   - Or "Developer App" profile

3. **Tap on it** and select **"Trust [Developer Name]"**

4. **Confirm** by tapping "Trust" again

**Note**: You may see "Untrusted Developer" when opening the app - this is normal. Trust the profile as above.

---

## ✅ Step 6: Launch Dev Client

**After installation**:

1. **On your device**, find the **RichesReach** app icon
2. **Tap to open**
3. **If prompted**, trust the developer profile (see Step 5)

---

## 🚀 Step 7: Connect to Expo

**On your Mac**:

1. **Start Expo**:
   ```bash
   cd mobile
   npx expo start --clear
   ```

2. **Scan QR Code**:
   - **Option A**: Use dev client's built-in scanner
     - Open RichesReach app
     - Tap "Scan QR Code" (if available)
   - **Option B**: Use iPhone Camera
     - Open Camera app
     - Scan QR code from Expo terminal
     - Tap notification to open in dev client
   - **Option C**: Manual URL entry
     - Copy URL from Expo terminal
     - Paste in dev client

3. **App should reload** with your code

---

## 🧪 Step 8: Test Data Loading

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

### Build Fails?

**Common issues**:
- **Apple account credentials wrong** → Re-enter credentials
- **2FA required** → Enter code when prompted
- **Build quota exceeded** → Check EAS plan limits
- **Code signing error** → EAS will try to fix automatically

**Fix**:
```bash
# Check build status
eas build:list

# Retry build
eas build --profile development --platform ios
```

### "Untrusted Developer" Error

**Fix**: Trust the developer profile (Step 5)

### App Won't Install

**Check**:
- Device is unlocked
- USB connection stable
- Xcode recognizes device
- Enough storage on device

**Try**:
- Disconnect and reconnect USB
- Restart device
- Try Apple Configurator instead

### Can't Connect to Expo

**Check**:
- Device and Mac on same WiFi
- Firewall not blocking
- Expo server running
- Try tunnel mode: `npx expo start --tunnel`

---

## 📋 Quick Reference

**Build Command**:
```bash
cd mobile
eas build --profile development --platform ios
```

**Download Build** (if needed):
```bash
eas build:download
```

**Install via Xcode**:
1. Xcode > Window > Devices and Simulators
2. Select device
3. Drag `.ipa` to "Installed Apps"

**Trust Profile**:
Settings > General > VPN & Device Management > Trust

**Start Expo**:
```bash
cd mobile
npx expo start --clear
```

---

## ✅ Success Checklist

- [ ] Build completed successfully
- [ ] `.ipa` file downloaded
- [ ] App installed on device
- [ ] Developer profile trusted
- [ ] App opens on device
- [ ] Can connect to Expo
- [ ] App reloads with code
- [ ] Data loads after login

---

**Ready to build!** Run the command in your terminal and follow the prompts! 🚀

