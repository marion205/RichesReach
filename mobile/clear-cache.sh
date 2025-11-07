#!/bin/bash
# Clear all Metro/Expo caches to fix bundling issues

echo "🧹 Clearing all caches..."

# Clear Metro cache
rm -rf node_modules/.cache 2>/dev/null
rm -rf .expo 2>/dev/null
rm -rf .metro* 2>/dev/null

# Clear watchman (if installed)
watchman watch-del-all 2>/dev/null || true

# Clear npm/yarn cache for this project
rm -rf node_modules/.bin/.cache 2>/dev/null

# Clear iOS build artifacts (if exists)
rm -rf ios/build 2>/dev/null
rm -rf ios/Pods 2>/dev/null

# Clear Android build artifacts (if exists)
rm -rf android/build 2>/dev/null
rm -rf android/.gradle 2>/dev/null

echo "✅ Cache cleared!"
echo ""
echo "Next steps:"
echo "1. Run: npm install (or yarn install)"
echo "2. Run: npx expo start --clear"
echo "3. If using dev client: cd ios && pod install && cd .."

