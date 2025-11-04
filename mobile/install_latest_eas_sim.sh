#!/bin/bash
set -euo pipefail

APP_NAME="RichesReach"
BUNDLE_ID="com.richesreach.app"
DL="$HOME/Downloads"
OUT="$DL/${APP_NAME}_extracted"

mkdir -p "$OUT"

poll_url() {
  while :; do
    URL=$(eas build:list --platform ios --limit 5 --json --non-interactive 2>/dev/null | node -e '
      let s="";process.stdin.on("data",d=>s+=d);
      process.stdin.on("end",()=>{try{
        const arr=JSON.parse(s);
        for (const b of arr){
          const u=(b?.artifacts?.applicationArchiveUrl)||(b?.artifacts?.buildUrl)||"";
          if(u){console.log(u);process.exit(0)}
        }
      }catch(e){};process.exit(1);});
    ' 2>/dev/null || true)
    if [ -n "${URL:-}" ]; then echo "$URL"; return 0; fi
    echo "Waiting for EAS build to complete..."
    sleep 4
  done
}

echo "Polling for EAS build artifact..."
URL=$(poll_url)
echo "Found artifact URL: $URL"

NAME="${APP_NAME}-devclient-$(date +%s)"
EXT="${URL##*.}"
FILE="$DL/$NAME.$EXT"

echo "Downloading to: $FILE"
curl -L "$URL" -o "$FILE"

echo "Extracting..."
case "$FILE" in
  *.tar.gz) tar -xzf "$FILE" -C "$OUT" ;;
  *.zip) unzip -o "$FILE" -d "$OUT" >/dev/null ;;
  *.app) rsync -a "$FILE" "$OUT"/ ;;
esac

APP=$(find "$OUT" -type d -name "*.app" -print -quit)
if [ -z "$APP" ]; then
  echo "❌ Could not find .app bundle in extracted files"
  exit 1
fi

echo "Installing app: $APP"
open -a Simulator
xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || true
xcrun simctl install booted "$APP"
xcrun simctl launch booted "$BUNDLE_ID"
echo "✅ App installed and launched!"
