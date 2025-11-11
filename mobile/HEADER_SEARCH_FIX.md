# Fix Xcode 16 / iOS 18 SDK Header Search-Order Problems

## ⚠️ Problem

**Error**: C++/libc++ header errors
- `<cmath>` tried including `<math.h>` but didn't find libc++'s `<math.h>` header
- libc++ internals like `__enable_hash_helper` "missing"

**Cause**: Bad header search paths (SDKROOT/usr/include, /usr/local/include, /opt/homebrew/include, etc.) are being searched **before** Apple's libc++ headers.

---

## ✅ Solution: Enforce Safe Build Settings

### Step 1: Patch Podfile with Safe Build Settings

**Added to `post_install` hook**:
```ruby
# ✅ CRITICAL: Fix Xcode 16 / iOS 18 SDK header search-order problems
# Force ALWAYS_SEARCH_USER_PATHS = NO and remove bad header paths
installer.pods_project.targets.each do |t|
  t.build_configurations.each do |config|
    config.build_settings['ALWAYS_SEARCH_USER_PATHS'] = 'NO'
    
    # Clean header search paths that break libc++ on Xcode 16
    hsp = config.build_settings['HEADER_SEARCH_PATHS']
    if hsp
      hsp = [hsp].flatten.reject { |p|
        p.to_s.include?('$(SDKROOT)/usr/include') ||
        p.to_s == '/usr/include/**' ||
        p.to_s.include?('/usr/local/include') ||
        p.to_s.include?('/opt/homebrew/include')
      }
      config.build_settings['HEADER_SEARCH_PATHS'] = hsp
    end
    
    # Also clean SYSTEM_HEADER_SEARCH_PATHS
    shsp = config.build_settings['SYSTEM_HEADER_SEARCH_PATHS']
    if shsp
      shsp = [shsp].flatten.reject { |p|
        p.to_s.include?('$(SDKROOT)/usr/include') ||
        p.to_s == '/usr/include/**' ||
        p.to_s.include?('/usr/local/include') ||
        p.to_s.include?('/opt/homebrew/include')
      }
      config.build_settings['SYSTEM_HEADER_SEARCH_PATHS'] = shsp
    end
    
    # Pin sane C++ standard
    config.build_settings['CLANG_CXX_LANGUAGE_STANDARD'] = 'gnu++17'
    config.build_settings['CLANG_CXX_LIBRARY'] = 'libc++'
  end
end
```

### Step 2: Clean and Reinstall Pods

```bash
cd ios
rm -rf Pods Podfile.lock
pod repo update
pod install
cd ..
```

### Step 3: Clean Caches

```bash
rm -rf ~/Library/Developer/Xcode/DerivedData
watchman watch-del-all 2>/dev/null || true
rm -rf node_modules
npm i  # or yarn / pnpm
```

### Step 4: Verify Build Settings

```bash
cd ios
xcodebuild -workspace RichesReach.xcworkspace \
  -scheme RichesReach -sdk iphonesimulator \
  -configuration Debug -showBuildSettings | egrep -i 'ALWAYS_SEARCH_USER_PATHS|HEADER_SEARCH_PATHS'
cd ..
```

**Expected**:
- `ALWAYS_SEARCH_USER_PATHS = NO`
- No `$(SDKROOT)/usr/include`, `/usr/include/**`, `/usr/local/include`, or `/opt/homebrew/include` in `HEADER_SEARCH_PATHS`

### Step 5: Build with Clean Environment

```bash
cd /Users/marioncollins/RichesReach/mobile
env -u CPATH -u CPLUS_INCLUDE_PATH -u LIBRARY_PATH -u SDKROOT -u CFLAGS -u CXXFLAGS -u CC -u CXX npx expo run:ios
```

**Why `env -u`**: Ensures the child `xcodebuild` process also runs clean, even if your shell startup files export those vars.

---

## 🔧 If It Still Fails

### 1. Check Shell Startup Files

```bash
grep -E 'CPATH|CPLUS_INCLUDE_PATH|SDKROOT|CFLAGS|CXXFLAGS|CC=|CXX=' ~/.zshrc ~/.bashrc ~/.bash_profile ~/.profile 2>/dev/null
```

**Fix**: Comment out any matches and open a new terminal

### 2. Check Xcode Project Directly

```bash
open ios/Pods.xcodeproj
```

**In Xcode**:
- Search Build Settings for any target (often `glog`, `RCT-Folly`, `fmt`)
- Look for bad include paths in `HEADER_SEARCH_PATHS`
- Remove them manually

### 3. Ensure Xcode is Selected Toolchain

```bash
sudo xcode-select -s /Applications/Xcode.app
```

**In Xcode**:
- Settings → Locations
- Set "Command Line Tools" to your current Xcode

### 4. Update CocoaPods

```bash
sudo gem install cocoapods
pod --version
```

---

## 📋 Complete Command Sequence

```bash
# 1) Clean environment and rebuild pods
cd ~/RichesReach/mobile/ios
rm -rf Pods Podfile.lock
unset CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH SDKROOT CFLAGS CXXFLAGS LDFLAGS CC CXX
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
export PATH="/opt/homebrew/bin:$PATH"
export LANG=en_US.UTF-8
arch -arm64 pod repo update
arch -arm64 pod install --repo-update

# 2) Clean caches
cd ..
rm -rf ~/Library/Developer/Xcode/DerivedData
watchman watch-del-all 2>/dev/null || true

# 3) Verify build settings
cd ios
xcodebuild -workspace RichesReach.xcworkspace \
  -scheme RichesReach -sdk iphonesimulator \
  -configuration Debug -showBuildSettings | egrep -i 'ALWAYS_SEARCH_USER_PATHS|HEADER_SEARCH_PATHS'

# 4) Build with clean environment
cd ..
env -u CPATH -u CPLUS_INCLUDE_PATH -u LIBRARY_PATH -u SDKROOT -u CFLAGS -u CXXFLAGS -u CC -u CXX npx expo run:ios
```

---

## 🎯 Why This Works

1. **`ALWAYS_SEARCH_USER_PATHS = NO`**: Prevents Xcode from searching user paths before system paths
2. **Removing bad header paths**: Ensures only Apple's libc++ headers are found
3. **Clean environment**: Prevents shell startup files from polluting the build
4. **Pinned C++ standard**: Ensures consistent C++17 compilation

---

**This sequence fixes the `<cmath>`/`<math.h>` + libc++ cascade 99% of the time on Xcode 16 with React Native/Expo Pods.** 🎉

