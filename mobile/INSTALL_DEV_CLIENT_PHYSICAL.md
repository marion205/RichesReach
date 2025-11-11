# Install Development Client on Physical Device

## ✅ Configuration Updated

**Updated `eas.json`**:
- `simulator: false` for development profile
- `distribution: "internal"` added

---

## 🚀 Step 1: Build for Physical Device

```bash
cd mobile
eas build --profile development --platform ios
```

**What happens**:
1. EAS uploads your code
2. Builds in cloud (10-20 minutes)
3. Provides download link for `.ipa` file

**Monitor progress**:
- Terminal will show build URL
- Or check: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds

---

## 📥 Step 2: Download .ipa File

**After build completes**:

1. **Get download link** from:
   - Terminal output
   - Expo dashboard: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds

2. **Download the `.ipa` file**:
   - Click download link in browser
   - Save to your Mac (e.g., `~/Downloads/RichesReach.ipa`)

---

## 📱 Step 3: Install on iPhone/iPad

### Option A: Using Xcode (Recommended)

**Prerequisites**:
- Xcode installed
- iPhone/iPad connected via USB
- Device unlocked and trusted

**Steps**:

1. **Open Xcode**:
   ```bash
   open -a Xcode
   ```

2. **Open Devices window**:
   - Menu: `Window` > `Devices and Simulators`
   - Or press: `Shift + Cmd + 2`

3. **Select your device**:
   - In left sidebar, select your iPhone/iPad
   - Make sure it shows "Connected"

4. **Install the app**:
   - Drag the `.ipa` file into the "Installed Apps" section
   - Or click "+" button and select the `.ipa` file

5. **Wait for installation**:
   - Progress bar will show installation
   - App icon will appear on device when done

---

### Option B: Using Apple Configurator 2

**Prerequisites**:
- Apple Configurator 2 installed (free from Mac App Store)
- iPhone/iPad connected via USB

**Steps**:

1. **Open Apple Configurator 2**

2. **Connect device**:
   - Device should appear in sidebar
   - Click on device name

3. **Install app**:
   - Click "Add" button (or drag `.ipa`)
   - Select the `.ipa` file
   - Wait for installation

4. **Enable wireless sync** (optional):
   - After first USB install, can enable wireless
   - Device > Configure > Enable wireless sync

---

## 🔐 Step 4: Trust the Developer Profile

**On your iPhone/iPad**:

1. **Go to Settings** > **General** > **VPN & Device Management**

2. **Find your developer profile**:
   - Look for "Apple Development: ..." or your Apple ID
   - Or "Developer App" profile

3. **Tap on it** and select **"Trust"**

4. **Confirm** by tapping "Trust" again

**Note**: You may need to do this each time you install a new build.

---

## ✅ Step 5: Launch the Dev Client

**After installation**:

1. **On your device**, find the **RichesReach** app icon
2. **Tap to open** (may show "Untrusted Developer" first - trust it as above)
3. **App should open** (may be blank initially - that's normal)

---

## 🚀 Step 6: Connect to Expo

**On your Mac**:

1. **Start Expo**:
   ```bash
   cd mobile
   npx expo start --clear
   ```

2. **Scan QR code**:
   - Use the dev client app's built-in scanner
   - Or use iPhone Camera app (will open in dev client)
   - Or manually enter URL shown in Expo terminal

3. **App should reload** with your code

---

## 🧪 Step 7: Test Data Loading

**After app loads**:

1. **Check Expo terminal** for:
   - `[API_BASE at runtime] http://192.168.1.240:8000`
   - `[GQL]` queries
   - `🔐` authentication logs

2. **Login** with:
   - Email: `test@example.com`
   - Password: `testpass123`

3. **Watch for data loading**

---

## 🔧 Troubleshooting

### "Untrusted Developer" Error

**Fix**: Trust the developer profile (Step 4 above)

### App Won't Install

**Check**:
- Device is unlocked
- USB connection is stable
- Xcode recognizes device
- You have enough storage on device

**Try**:
- Disconnect and reconnect USB
- Restart device
- Try Apple Configurator instead of Xcode

### App Crashes on Launch

**Check**:
- Device iOS version is compatible
- Build completed successfully
- Try reinstalling

### Can't Connect to Expo

**Check**:
- Device and Mac on same WiFi network
- Firewall not blocking
- Expo server is running
- Try tunnel mode: `npx expo start --tunnel`

---

## 📋 Quick Reference

**Build Command**:
```bash
cd mobile
eas build --profile development --platform ios
```

**Install via Xcode**:
1. Open Xcode > Window > Devices and Simulators
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

## ✅ Success Indicators

You'll know it's working when:
- ✅ App installs without errors
- ✅ App opens on device
- ✅ Can scan QR code in dev client
- ✅ App reloads with your code
- ✅ Expo logs show API connections
- ✅ Data loads after login

---

**Ready to build!** Run the build command and follow the steps above! 🚀

