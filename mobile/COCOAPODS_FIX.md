# Fix CocoaPods Installation

## ⚠️ Problem

**Error**: `CocoaPods CLI not found in PATH`

**Cause**: CocoaPods is either not installed or not properly linked in PATH.

---

## ✅ Solution: Install CocoaPods

### Option 1: Install via Homebrew (Recommended)

```bash
brew install cocoapods
```

**If already installed but not linked**:
```bash
brew unlink cocoapods
brew link cocoapods
```

**Verify**:
```bash
pod --version
```

### Option 2: Install via Gem (Alternative)

```bash
sudo gem install cocoapods
```

**Note**: May require system Ruby or rbenv/rvm setup.

### Option 3: Use Bundler (If Using Ruby Version Manager)

```bash
cd mobile/ios
bundle install
bundle exec pod install
```

---

## 🔧 Troubleshooting

### "Permission Denied" Error

**Fix**: Use `sudo`:
```bash
sudo gem install cocoapods
```

### "Ruby Version" Error

**Fix**: Use system Ruby or install via Homebrew:
```bash
brew install cocoapods
```

### "Command Not Found" After Install

**Fix**: Add to PATH or relink:
```bash
# For Homebrew
brew unlink cocoapods && brew link cocoapods

# For Gem
export PATH="$HOME/.gem/ruby/X.X.0/bin:$PATH"
# Or add to ~/.zshrc or ~/.bash_profile
```

---

## ✅ After CocoaPods is Installed

**Verify installation**:
```bash
pod --version
# Should show version number (e.g., 1.15.2)
```

**Then retry build**:
```bash
cd mobile
npx expo run:ios
```

---

## 📋 Quick Fix Commands

**Try these in order**:

1. **Check if installed**:
   ```bash
   pod --version
   ```

2. **If not found, install via Homebrew**:
   ```bash
   brew install cocoapods
   ```

3. **If Homebrew fails, try gem**:
   ```bash
   sudo gem install cocoapods
   ```

4. **Verify**:
   ```bash
   pod --version
   ```

5. **Retry build**:
   ```bash
   cd mobile
   npx expo run:ios
   ```

---

## 🎯 Expected Result

After CocoaPods is installed:
- ✅ `pod --version` shows version number
- ✅ `npx expo run:ios` can proceed
- ✅ Native dependencies will install
- ✅ Build will continue

---

**Install CocoaPods and retry the build!** 🚀

