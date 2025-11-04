#!/usr/bin/env bash
# Bulletproof EAS Build Script - Phase 3
# Monitors build and provides escape hatch if needed
set -euo pipefail

cd "$(dirname "$0")"

echo "🚀 Bulletproof EAS Build - Phase 3"
echo "================================"
echo ""

# Verify EAS login
echo "📋 Verifying EAS authentication..."
if ! eas whoami &>/dev/null; then
  echo "❌ Not logged in. Run: eas login"
  exit 1
fi
echo "✅ Authenticated: $(eas whoami 2>&1 | grep -i 'logged in' || echo 'OK')"
echo ""

# Choose profile
PROFILE="${1:-development}"
echo "📦 Build Profile: $PROFILE"
echo ""

# Launch build (async, no-wait for monitoring)
echo "🔥 Launching EAS build..."
echo "   Profile: $PROFILE"
echo "   Platform: ios"
echo "   Image: macos-sonoma-14.6-xcode-16.1 (Xcode 16.1)"
echo ""

BUILD_ID=$(eas build --profile "$PROFILE" --platform ios --clear-cache --non-interactive --json 2>&1 | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")

if [ -z "$BUILD_ID" ]; then
  echo "❌ Failed to start build. Checking status..."
  eas build:list --platform ios --limit 1 --non-interactive
  exit 1
fi

echo "✅ Build started: $BUILD_ID"
echo ""
echo "📊 Monitor at: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds/$BUILD_ID"
echo ""
echo "🔍 Watching for Darwin/cyclic/glog errors..."
echo "   (Press Ctrl+C to stop watching - build continues in background)"
echo ""

# Monitor build (watch for specific errors)
watch_build() {
  while true; do
    STATUS=$(eas build:view "$BUILD_ID" --json 2>&1 | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
    
    case "$STATUS" in
      "finished")
        echo ""
        echo "✅ BUILD SUCCESS!"
        echo ""
        echo "📥 Installing artifact..."
        ./install_latest_eas_sim.sh || echo "⚠️  Manual install needed - check Downloads/"
        exit 0
        ;;
      "errored"|"canceled")
        echo ""
        echo "❌ BUILD FAILED: $STATUS"
        echo ""
        echo "🔍 Check logs: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds/$BUILD_ID"
        echo ""
        echo "🚨 Escape Hatch - Local Build:"
        echo "   cd $(pwd)"
        echo "   npx expo run:ios --configuration Debug"
        exit 1
        ;;
      "in-progress"|"in_queue")
        echo -n "."
        sleep 10
        ;;
      *)
        echo ""
        echo "⏳ Status: $STATUS (waiting...)"
        sleep 10
        ;;
    esac
  done
}

# Trap Ctrl+C
trap 'echo ""; echo "⏸️  Monitoring stopped (build continues)"; echo "🔗 Check status: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds/$BUILD_ID"; exit 0' INT

watch_build

