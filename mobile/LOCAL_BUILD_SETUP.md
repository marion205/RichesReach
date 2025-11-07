# Local Build Setup - Fastlane Installation

## Issue
Local builds require **Fastlane** to be installed, but it's not currently in your PATH.

## Quick Fix: Use Cloud Build (Recommended)

The easiest solution is to use cloud build instead:

```bash
cd /Users/marioncollins/RichesReach/mobile
./build-dev-client.sh simulator
# Choose option 1 (Cloud build)
```

Cloud builds:
- ✅ No Fastlane needed
- ✅ No Xcode setup required
- ✅ 5-10 minutes
- ✅ Free tier: 30 builds/month

## Install Fastlane (For Local Builds)

If you want to use local builds (faster, 2-5 min), install Fastlane:

### Option 1: System-wide (Requires sudo)
```bash
sudo gem install fastlane
```

### Option 2: User Installation (No sudo)
```bash
gem install fastlane --user-install
echo 'export PATH="$HOME/.gem/ruby/$(ruby -e "puts RUBY_VERSION.split(\".\")[0..1].join(\".\")")/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Option 3: Using Homebrew (Recommended)
```bash
brew install fastlane
```

### Verify Installation
```bash
fastlane --version
# Should show: fastlane 2.x.x
```

## After Installing Fastlane

1. **Retry local build**:
   ```bash
   ./build-dev-client.sh simulator
   # Choose option 2 (Local build)
   ```

2. **Or use npm script**:
   ```bash
   npm run build:dev:ios:local
   ```

## Recommendation

For your first dev client build, **use cloud build** (option 1):
- ✅ No setup required
- ✅ Works immediately
- ✅ Same result, just a bit slower

You can always install Fastlane later if you want faster local builds.

## Next Steps

1. **Run the build script again**:
   ```bash
   ./build-dev-client.sh simulator
   ```

2. **Choose option 1** (Cloud build)

3. **Wait 5-10 minutes** for the build to complete

4. **Download and install** when done
