#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "🚀 Starting EAS Build & Auto-Install Script"
echo "============================================"
echo ""

# Fix watchman warning
watchman watch-del '/Users/marioncollins/RichesReach' 2>/dev/null || true
watchman watch-project '/Users/marioncollins/RichesReach' 2>/dev/null || true

# Start the build
echo "📦 Starting EAS build with 'development' profile..."
echo "   (This uses Xcode 16.1 - may take 10-15 minutes)"
echo ""

BUILD_ID=$(eas build --profile development --platform ios --clear-cache --non-interactive 2>&1 | grep -E "builds/[a-f0-9-]+" | head -1 | sed 's/.*builds\///' | sed 's/[^a-f0-9-].*//' || echo "")

if [ -z "$BUILD_ID" ]; then
  echo "⚠️  Could not extract build ID from output"
  echo "   The build may have started - check: eas build:list"
  exit 1
fi

echo "✅ Build started: $BUILD_ID"
echo "   View progress: https://expo.dev/accounts/marion205/projects/richesreach-ai/builds/$BUILD_ID"
echo ""
echo "⏳ Waiting for build to complete..."
echo "   (You can press Ctrl+C and check status later with: eas build:list)"
echo ""

# Poll for build completion
while true; do
  sleep 30
  
  STATUS=$(eas build:list --platform ios --limit 1 --non-interactive --json 2>/dev/null | \
    node -e "let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>{try{const b=JSON.parse(s)[0];console.log(b?.status);}catch(e){console.log('CHECKING');}});" 2>/dev/null || echo "CHECKING")
  
  if [ "$STATUS" = "finished" ]; then
    echo ""
    echo "✅ Build finished! Installing..."
    ./install_latest_eas_sim.sh
    echo ""
    echo "🎉 App installed! Starting Metro..."
    pkill -f "expo start" || true
    sleep 2
    npx expo start --dev-client
    exit 0
  elif [ "$STATUS" = "errored" ] || [ "$STATUS" = "ERRORED" ]; then
    echo ""
    echo "❌ Build failed. Check logs:"
    echo "   https://expo.dev/accounts/marion205/projects/richesreach-ai/builds"
    exit 1
  else
    echo "   Still building... (status: $STATUS)"
  fi
done

