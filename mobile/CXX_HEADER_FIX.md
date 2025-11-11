# Fix C++/libc++ Header Errors

## ⚠️ Problem

**Error**: C++/libc++ header errors while compiling Pods/glog for Simulator
- `<cmath>` didn't find libc++'s `<math.h>`
- `__enable_hash_helper` missing
- Wrong toolchain/headers being picked up

**Cause**: Environment variables or non-Apple compiler in PATH shadowing Xcode's libc++ headers

---

## ✅ Solution: Reset Toolchain + Environment

### Step 0: Ensure Xcode Toolchain is Selected

```bash
sudo xcode-select -s /Applications/Xcode.app
sudo xcodebuild -runFirstLaunch || true
```

### Step 1: Fresh Shell Environment

```bash
cd ~/RichesReach/mobile

# Clear conflicting environment variables
unset CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH SDKROOT CFLAGS CXXFLAGS LDFLAGS CC CXX

# Force Apple toolchain
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
export PATH="/opt/homebrew/bin:$PATH"
```

### Step 2: Clean Caches and Pods

```bash
rm -rf ios/Pods ios/Podfile.lock ~/Library/Developer/Xcode/DerivedData/*
```

### Step 3: Reinstall Pods with Apple clang

```bash
cd ios
arch -arm64 pod repo update
arch -arm64 pod install --repo-update
```

### Step 4: Build Dev Client

```bash
cd ..
npx expo run:ios
```

---

## 🔍 Verification

**Check Apple toolchain**:
```bash
xcrun --sdk iphonesimulator clang --version
xcrun --show-sdk-path --sdk iphonesimulator
```

**Expected**:
- Apple clang version
- SDK path under `/Applications/Xcode.app/.../iPhoneSimulator.sdk`

---

## 🔧 Why This Works

1. **`unset CPATH CPLUS_INCLUDE_PATH ... CC CXX`**: Prevents Homebrew GCC/LLVM or custom include paths from shadowing Xcode's libc++ headers
2. **`DEVELOPER_DIR` + `xcode-select`**: Forces the Apple toolchain
3. **Reinstalling pods after cleaning**: Ensures Pods pick up the corrected search paths

---

## 🐛 If It Still Errors

### 1. Check Shell Init Overrides

```bash
grep -E 'CPATH|CPLUS_INCLUDE_PATH|SDKROOT|CFLAGS|CXXFLAGS|CC=|CXX=' ~/.zshrc ~/.bashrc ~/.bash_profile ~/.profile 2>/dev/null
```

**Fix**: Comment out any matches and open a new terminal

### 2. Check Project Scripts

Make sure `CC`/`CXX` aren't set in custom build scripts

### 3. Build in Xcode (Last Resort)

```bash
open ios/RichesReach.xcworkspace
```

**In Xcode**:
- Select `RichesReach` scheme
- Select any iOS Simulator device
- Product → Clean Build Folder
- Product → Build

If it works in Xcode, `npx expo run:ios` will usually follow suit.

---

## 🚀 After It Compiles

**Start Metro and connect dev client**:
```bash
npx expo start --dev-client
```

**If Simulator app doesn't auto-connect**:
```bash
xcrun simctl openurl booted exp+devclient://localhost:8081
```

---

## 📋 Complete Command Block

```bash
# 0) Ensure Xcode toolchain is selected
sudo xcode-select -s /Applications/Xcode.app
sudo xcodebuild -runFirstLaunch || true

# 1) Fresh shell env for this build
cd ~/RichesReach/mobile
unset CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH SDKROOT CFLAGS CXXFLAGS LDFLAGS CC CXX
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
export PATH="/opt/homebrew/bin:$PATH"

# 2) Clean caches/DerivedData + Pods
rm -rf ios/Pods ios/Podfile.lock ~/Library/Developer/Xcode/DerivedData/*

# 3) Reinstall pods with the Apple clang for Apple Silicon
cd ios
arch -arm64 pod repo update
arch -arm64 pod install --repo-update

# 4) Build the Simulator dev client
cd ..
npx expo run:ios
```

---

**All fixed and ready to build!** 🎉

