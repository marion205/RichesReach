# 🔄 Reset Simulator & Reload App

## Quick Fix Steps:

### Option 1: Reset Simulator (Fastest)
1. In Xcode Simulator menu: **Device → Erase All Content and Settings**
2. Or from terminal:
   ```bash
   xcrun simctl erase all
   ```

### Option 2: Force Quit & Reload
1. Press **⌘⌥Esc** to open Force Quit
2. Quit **Simulator** app completely
3. Reopen Simulator
4. In simulator, press **⌘K** to clear console
5. Press **⌘R** to reload app

### Option 3: Uninstall & Reinstall App
1. Long press the app icon in simulator
2. Tap the X to delete
3. Rebuild with: `npx expo run:ios`

### Option 4: Hard Reset Simulator
1. In Simulator menu: **Device → Restart**
2. Or press **⌘⌃Z** (this forces a reboot)

## If App is Completely Frozen:

1. **Kill all processes:**
   ```bash
   pkill -9 -f "Simulator\|Metro\|expo"
   ```

2. **Restart Simulator:**
   ```bash
   xcrun simctl shutdown all
   open -a Simulator
   ```

3. **Start Metro fresh:**
   ```bash
   cd mobile
   npx expo start --clear
   ```

4. **Rebuild app:**
   ```bash
   npx expo run:ios
   ```

## Debugging Tips:

- Check Metro bundler is running: http://localhost:8081/status
- Check console for errors (⌘⌥C in Simulator)
- Try a different simulator device
- Check memory usage (Activity Monitor)

