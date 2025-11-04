# Quick Build Instructions

## Current Issue: RVM Ruby conflict with CocoaPods

## Solution 1: Build in Xcode (Recommended - No Pod Issues)
1. Xcode should be opening now
2. In Xcode:
   - Select **iPhone 15 Pro** simulator (top toolbar)
   - Press **⌘R** (Product → Run)
   - Xcode will automatically handle pods
   - Wait ~1-2 minutes for first build

## Solution 2: Fix RVM temporarily
Run these commands:

```bash
cd /Users/marioncollins/RichesReach/mobile/ios

# Temporarily disable RVM
unset GEM_HOME GEM_PATH
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

# Use Homebrew CocoaPods if available
brew link cocoapods 2>/dev/null || /opt/homebrew/bin/pod install || sudo /usr/bin/gem install cocoapods

pod install

cd ..
npx expo run:ios
```

## Solution 3: Use Bundler (Clean Ruby Environment)
```bash
cd mobile/ios
gem install bundler
bundle init
echo 'gem "cocoapods"' >> Gemfile
bundle install
bundle exec pod install
cd ..
npx expo run:ios
```

## Current Status
- ✅ Simulator booted
- ✅ Metro running
- ✅ Code optimized (benchmark computation removed)
- ⚠️ Need pods installed to build
