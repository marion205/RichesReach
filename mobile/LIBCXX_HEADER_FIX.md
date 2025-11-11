# Fix libc++ Header Search Path Issues (Xcode 16 / iOS 18.5)

## ⚠️ Problem

**Error**: libc++ header search path issues
- `<cmath> tried including <math.h> but didn't find libc++'s <math.h> header`
- `no member named 'memcpy' in namespace 'std'`
- Missing `__bit_reference`, `__enable_hash_helper`, `std::isnan`, `std::ceil`, etc.

**Cause**: C headers are being found before libc++ headers, causing the compiler to use C headers instead of libc++'s C++ wrappers.

---

## ✅ Solution: Prioritize libc++ Headers

### Step 1: Enhanced Podfile post_install Hook

**Key changes**:
1. **Add libc++ header path FIRST** in `HEADER_SEARCH_PATHS`
2. **Add `-stdlib=libc++`** to `OTHER_CPLUSPLUSFLAGS`
3. **Remove bad header paths** (already done)
4. **Use `CURRENT_ARCH=arm64`** for pod install

**Podfile post_install** (already applied):
```ruby
post_install do |installer|
  installer.pods_project.targets.each do |t|
    t.build_configurations.each do |config|
      config.build_settings['ALWAYS_SEARCH_USER_PATHS'] = 'NO'
      config.build_settings['USE_HEADERMAP'] = 'YES'
      config.build_settings['CLANG_CXX_LIBRARY'] = 'libc++'
      
      # Remove bad header paths
      paths = Array(config.build_settings['HEADER_SEARCH_PATHS'] || '$(inherited)')
      paths = [paths].flatten.reject { |p|
        p.to_s == '/usr/include' ||
        p.to_s.include?('$(SDKROOT)/usr/include') ||
        p.to_s == '/usr/include/**' ||
        p.to_s.include?('/usr/local/include') ||
        p.to_s.include?('/opt/homebrew/include')
      }
      
      # CRITICAL: Prioritize libc++ headers FIRST
      cpp_header_path = '$(SDKROOT)/usr/include/c++/v1'
      paths = paths.reject { |p| p.to_s == cpp_header_path }
      paths = [cpp_header_path] + paths
      paths << '$(inherited)' unless paths.include?('$(inherited)')
      config.build_settings['HEADER_SEARCH_PATHS'] = paths
      
      # Add -stdlib=libc++ to C++ flags
      cppflags = Array(config.build_settings['OTHER_CPLUSPLUSFLAGS'] || '$(inherited)')
      cppflags = [cppflags].flatten
      cppflags << '-stdlib=libc++' unless cppflags.any? { |f| f.to_s.include?('stdlib=libc++') }
      config.build_settings['OTHER_CPLUSPLUSFLAGS'] = cppflags
      
      # C++ standard
      config.build_settings['CLANG_CXX_LANGUAGE_STANDARD'] = 'gnu++17'
      
      # glog-specific fixes
      if t.name == 'glog'
        config.build_settings['GCC_PREPROCESSOR_DEFINITIONS'] ||= ['$(inherited)']
        config.build_settings['GCC_PREPROCESSOR_DEFINITIONS'] << 'GLOG_NO_ABBREVIATED_SEVERITIES=1'
      end
    end
  end
end
```

### Step 2: Clean and Reinstall Pods with Architecture Fix

```bash
cd ios
rm -rf Pods Podfile.lock
CURRENT_ARCH=arm64 pod install --repo-update
cd ..
```

**Why `CURRENT_ARCH=arm64`**: Ensures glog and other C++ pods compile for the correct architecture on Apple Silicon.

### Step 3: Clean DerivedData

```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/*
```

### Step 4: Build with Clean Environment

```bash
cd /Users/marioncollins/RichesReach/mobile
env -u CPATH -u C_INCLUDE_PATH -u CPLUS_INCLUDE_PATH -u LIBRARY_PATH -u SDKROOT CURRENT_ARCH=arm64 npx expo run:ios
```

---

## 🔧 Why This Works

1. **libc++ header path first**: Ensures `<cmath>` finds libc++'s `<math.h>` wrapper before C's `<math.h>`
2. **`-stdlib=libc++`**: Explicitly tells the compiler to use libc++ standard library
3. **`CURRENT_ARCH=arm64`**: Fixes glog compilation on Apple Silicon
4. **Removing bad paths**: Prevents C headers from shadowing libc++ headers

---

## 📋 Complete Command Sequence

```bash
# 1) Clean and reinstall pods with architecture fix
cd ~/RichesReach/mobile/ios
rm -rf Pods Podfile.lock
unset CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH LIBRARY_PATH SDKROOT CFLAGS CXXFLAGS LDFLAGS CC CXX
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
export PATH="/opt/homebrew/bin:$PATH"
export LANG=en_US.UTF-8
CURRENT_ARCH=arm64 arch -arm64 pod install --repo-update

# 2) Clean DerivedData
cd ..
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# 3) Build with clean environment
env -u CPATH -u C_INCLUDE_PATH -u CPLUS_INCLUDE_PATH -u LIBRARY_PATH -u SDKROOT CURRENT_ARCH=arm64 npx expo run:ios
```

---

## 🐛 If It Still Fails

### 1. Check Expo SDK Version

```bash
npx expo --version
npx expo-doctor
```

**If SDK < 52**: Consider upgrading:
```bash
npx expo install --fix
npx expo upgrade
```

### 2. Verify Header Search Paths

```bash
cd ios
xcodebuild -workspace RichesReach.xcworkspace \
  -scheme RichesReach -sdk iphonesimulator \
  -showBuildSettings | grep HEADER_SEARCH_PATHS
```

**Expected**: `$(SDKROOT)/usr/include/c++/v1` should be FIRST in the list.

### 3. Check glog Target Specifically

```bash
cd ios
xcodebuild -workspace RichesReach.xcworkspace \
  -target glog -sdk iphonesimulator \
  -showBuildSettings | grep -E 'HEADER_SEARCH_PATHS|CLANG_CXX'
```

### 4. Try Building in Xcode

```bash
open ios/RichesReach.xcworkspace
```

**In Xcode**:
- Select `glog` target
- Build Settings → Search for "Header Search Paths"
- Verify `$(SDKROOT)/usr/include/c++/v1` is first
- Build → Clean Build Folder
- Build → Build

---

## 🎯 Expected Result

After applying these fixes:
- ✅ `<cmath>` finds libc++'s `<math.h>` wrapper
- ✅ `std::memcpy`, `std::isnan`, `std::ceil` resolve correctly
- ✅ `__bit_reference`, `__enable_hash_helper` found
- ✅ glog compiles successfully
- ✅ Build completes without libc++ errors

---

**This should resolve the libc++ header search path issues!** 🎉

