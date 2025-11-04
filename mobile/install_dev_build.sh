#!/usr/bin/env bash

set -euo pipefail

# Usage:
#   ./install_dev_build.sh                      # auto-picks newest artifact from ~/Downloads
#   ./install_dev_build.sh /path/to/RichesReach.app
#   ./install_dev_build.sh ~/Downloads/RichesReach.tar.gz
#   ./install_dev_build.sh ~/Downloads/RichesReach.zip

APP_INPUT="${1:-}"
DOWNLOADS="$HOME/Downloads"
APP_PATH=""
WORKDIR=""

pick_latest() {
  ls -t "$DOWNLOADS"/RichesReach*.{app,tar.gz,zip} 2>/dev/null | head -n1 || true
}

extract_if_needed() {
  local artifact="$1"
  case "$artifact" in
    *.tar.gz|*.tgz)
      WORKDIR="$(mktemp -d)"
      tar -xzf "$artifact" -C "$WORKDIR"
      ;;
    *.zip)
      WORKDIR="$(mktemp -d)"
      unzip -q "$artifact" -d "$WORKDIR"
      ;;
  esac
}

# 1) Locate artifact
if [[ -z "$APP_INPUT" ]]; then
  ARTIFACT="$(pick_latest)"
else
  ARTIFACT="$APP_INPUT"
fi

if [[ -z "${ARTIFACT:-}" ]]; then
  echo "❌ No artifact found. Pass a path to .app/.zip/.tar.gz or place it in ~/Downloads (prefixed with RichesReach)."
  exit 1
fi

# 2) If archive, extract; else use .app directly
case "$ARTIFACT" in
  *.tar.gz|*.tgz|*.zip)
    echo "📦 Extracting $ARTIFACT ..."
    extract_if_needed "$ARTIFACT"
    APP_PATH="$(find "$WORKDIR" -maxdepth 3 -name "*.app" -print -quit)"
    ;;
  *.app)
    APP_PATH="$ARTIFACT"
    ;;
  *)
    echo "❌ Unsupported artifact: $ARTIFACT"
    exit 1
    ;;
esac

if [[ -z "${APP_PATH:-}" || ! -d "$APP_PATH" ]]; then
  echo "❌ Could not locate .app inside archive."
  exit 1
fi

echo "📱 Using app: $APP_PATH"

# 3) Boot Simulator (if not already)
open -a Simulator || true
for i in {1..30}; do
  if xcrun simctl list | grep -q "Booted"; then break; fi
  sleep 1
done

# 4) Find bundle id
PLIST_A="$APP_PATH/Info.plist"
PLIST_B="$APP_PATH/Contents/Info.plist"
if [[ -f "$PLIST_A" ]]; then
  BUNDLE_ID=$(/usr/libexec/PlistBuddy -c 'Print CFBundleIdentifier' "$PLIST_A")
elif [[ -f "$PLIST_B" ]]; then
  BUNDLE_ID=$(/usr/libexec/PlistBuddy -c 'Print CFBundleIdentifier' "$PLIST_B")
else
  echo "❌ Info.plist not found in app bundle."
  exit 1
fi

echo "🆔 Bundle ID: $BUNDLE_ID"

# 5) Uninstall old, install new, launch
xcrun simctl uninstall booted "$BUNDLE_ID" || true
xcrun simctl install   booted "$APP_PATH"
xcrun simctl launch    booted "$BUNDLE_ID" || true

echo "✅ Installed & launched."
echo "👉 Start Metro now: npx expo start --dev-client"
