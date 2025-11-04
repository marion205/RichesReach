# Local iOS Build Setup (Alternative to EAS)

Since you've hit your EAS build limit, here's how to set up local builds with Xcode 16.1.

## The Problem

Your current Xcode 26.0.1 has iOS 26.0 SDK with breaking changes incompatible with React Native 0.81.5.

## Solution: Install Xcode 16.1 Alongside Current Xcode

### Step 1: Download Xcode 16.1

1. Go to [Apple Developer Downloads](https://developer.apple.com/download/all/)
2. Sign in with your Apple ID
3. Search for "Xcode 16.1"
4. Download the `.xip` file (~12GB)
5. Wait for download (can take 30-60 minutes)

### Step 2: Install Xcode 16.1

```bash
# Extract the .xip file (double-click in Finder, or use command line)
cd ~/Downloads
xattr -d com.apple.quarantine Xcode_16.1.xip  # Remove quarantine
open Xcode_16.1.xip  # Extract

# Wait for extraction (10-15 minutes), then:
sudo mv ~/Downloads/Xcode.app /Applications/Xcode-16.1.app
```

### Step 3: Switch to Xcode 16.1

```bash
# Switch command line tools
sudo xcode-select --switch /Applications/Xcode-16.1.app/Contents/Developer

# Verify
xcodebuild -version  # Should show 16.1
```

### Step 4: Build Locally

```bash
cd /Users/marioncollins/RichesReach/mobile

# Clean and rebuild
rm -rf ios/Pods ios/Podfile.lock
cd ios && pod install && cd ..

# Build and run
npm run ios
```

### Step 5: Switch Back to Xcode 26.0.1 (When Needed)

```bash
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
```

## Alternative: Upgrade EAS Plan

If you need more builds immediately:
1. Go to https://expo.dev/accounts/marion205/settings/billing
2. Upgrade to On-demand plan ($0.05/build or subscription)
3. Then run: `eas build --profile development --platform ios`

## Quick Test (Verify Simulator Works)

The simulator itself should work fine - test it:

```bash
xcrun simctl boot "iPhone 15 Pro"
open -a Simulator
```

If simulator launches, the issue is only the build toolchain (Xcode version).

## Notes

- You can keep both Xcode versions installed
- Switch between them using `xcode-select` as needed
- EAS builds will reset on Dec 1, 2025 (28 days)
- Local builds don't count against EAS limits

