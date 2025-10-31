#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(pwd)}"
MOBILE="$ROOT/mobile"
IOS="$MOBILE/ios"
APPJSON="$MOBILE/app.json"
PODFILE="$IOS/Podfile"
ENVFILE="$MOBILE/.env"

echo "==> Repo root: $ROOT"
test -d "$MOBILE" || { echo "❌ Expected $MOBILE"; exit 1; }
test -f "$APPJSON" || { echo "❌ Missing $APPJSON"; exit 1; }

echo "==> Patching app.json (enable New Architecture + Info.plist)…"
cp -f "$APPJSON" "$APPJSON.bak.$(date +%s)"
APPJSON="$APPJSON" node -e '
const fs=require("fs");
const p=process.env.APPJSON;
if(!p){ console.error("APPJSON env not set"); process.exit(1); }
const j=JSON.parse(fs.readFileSync(p,"utf8"));
j.expo=j.expo||{}; j.expo.ios=j.expo.ios||{};
j.expo.ios.newArchEnabled=true;
j.expo.ios.infoPlist=Object.assign({}, j.expo.ios.infoPlist, {
  NSMicrophoneUsageDescription: "Voice wake-word and ASR",
  NSSpeechRecognitionUsageDescription: "Voice commands for coaching",
  NSCameraUsageDescription: "AR preview requires camera"
});
fs.writeFileSync(p, JSON.stringify(j,null,2)+"\n");
console.log("✔ app.json updated");'

echo "==> Patching Podfile (add CDN source + RCT_NEW_ARCH_ENABLED=1)…"
test -f "$PODFILE" || { echo "❌ Missing $PODFILE (run: npx expo prebuild -p ios)"; exit 1; }
cp -f "$PODFILE" "$PODFILE.bak.$(date +%s)"

if ! grep -q "https://cdn.cocoapods.org/" "$PODFILE"; then
  (echo "source 'https://cdn.cocoapods.org/'"; cat "$PODFILE") > "$PODFILE.tmp" && mv "$PODFILE.tmp" "$PODFILE"
  echo "✔ Added CocoaPods CDN source"
fi

if ! grep -q "ENV\['RCT_NEW_ARCH_ENABLED'\]\s*=\s*'1'" "$PODFILE"; then
  awk '
    /use_native_modules!\(/ && !i { print "  ENV['"'"RCT_NEW_ARCH_ENABLED'"'"] = '"'"1"'"'"; i=1 }
    { print }
  ' "$PODFILE" > "$PODFILE.tmp" && mv "$PODFILE.tmp" "$PODFILE"
  echo "✔ Forced RCT_NEW_ARCH_ENABLED=1"
fi

echo "==> Writing env block to $ENVFILE…"
mkdir -p "$MOBILE"; touch "$ENVFILE"
upsert_env(){ local k="$1" v="$2"; grep -vE "^${k}=" "$ENVFILE" > "$ENVFILE.tmp" || true; mv "$ENVFILE.tmp" "$ENVFILE"; printf "%s=%s\n" "$k" "$v" >> "$ENVFILE"; }
upsert_env EXPO_PUBLIC_API_BASE_URL            "http://192.168.1.236:8000"
upsert_env EXPO_PUBLIC_GRAPHQL_URL             "http://192.168.1.236:8000/graphql/"
upsert_env EXPO_PUBLIC_WS_URL                  "ws://192.168.1.236:8000/ws"
upsert_env EXPO_PUBLIC_SIGNAL_URL              "ws://192.168.1.236:8000"
upsert_env EXPO_PUBLIC_TURN_URLS               "stun:stun.l.google.com:19302"
upsert_env EXPO_PUBLIC_TURN_USERNAME           ""
upsert_env EXPO_PUBLIC_TURN_CREDENTIAL         ""
upsert_env EXPO_PUBLIC_AUTH_REFRESH_PATH       "/auth/refresh"
upsert_env EXPO_PUBLIC_AUTH_REFRESH_MODE       "cookie"
echo "✔ .env updated"

echo "==> Cleaning CocoaPods and installing…"
cd "$IOS"; rm -rf Pods Podfile.lock
env -i LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin" HOME="$HOME" \
  /opt/homebrew/bin/pod install --repo-update --verbose
echo "✔ pod install done"

echo "==> Prebuild & run iOS dev client…"
cd "$MOBILE"
CI=1 npx expo prebuild -p ios
npx expo run:ios --device || npx expo run:ios

echo "==> Starting Metro (clean)…"
npx expo start -c
echo "✅ All done."


