#!/usr/bin/env bash
set -euo pipefail

BUNDLE_ID=com.richesreach.app
ART=$(find ~/Downloads -maxdepth 1 -type f \( -name "RichesReach*.tar.gz" -o -name "RichesReach*.zip" -o -name "RichesReach*.app" \) -print | sort -r | head -n1)

if [ -z "$ART" ]; then
  echo "❌ No artifact found in ~/Downloads"
  exit 1
fi

mkdir -p ~/Downloads/RichesReach_extracted

case "$ART" in
  *.tar.gz) tar -xzf "$ART" -C ~/Downloads/RichesReach_extracted ;;
  *.zip) unzip -o "$ART" -d ~/Downloads/RichesReach_extracted >/dev/null ;;
  *.app) rsync -a "$ART" ~/Downloads/RichesReach_extracted/ ;;
esac

APP=$(find ~/Downloads/RichesReach_extracted -type d -name "*.app" -print -quit)

if [ -z "$APP" ]; then
  echo "❌ No .app bundle found in artifact"
  exit 1
fi

echo "✅ Found app bundle: $APP"
open -a Simulator
xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || true
xcrun simctl install booted "$APP"
xcrun simctl launch booted "$BUNDLE_ID"

echo "✅ App installed and launched"

