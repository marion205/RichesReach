#!/usr/bin/env bash
set -euo pipefail

DEVICE="${DEVICE:-iPhone 16 Pro}"
TS="$(date +%Y%m%d_%H%M%S)"
WORKDIR="/Users/marioncollins/RichesReach/mobile"
RAW_MOV="$WORKDIR/Demo_Raw_${TS}.mov"
QT_MP4="$WORKDIR/RichesReach_Demo_QuickTime_${TS}.mp4"

cd "$WORKDIR"

echo "📱 Ensuring simulator is booted: $DEVICE"
xcrun simctl bootstatus "$DEVICE" -b >/dev/null 2>&1 || true

# Step 1: Start Expo server if not running
echo "🚀 Starting Expo server..."
if ! pgrep -f "expo start" >/dev/null; then
  echo "Starting Expo development server..."
  npx expo start --ios --no-dev --minify &
  EXPO_PID=$!
  sleep 10
else
  echo "Expo server already running"
fi

# Step 2: Wait for app to load and be ready
echo "⏳ Waiting for RichesReach app to load..."
sleep 5

# Step 3: Force focus on simulator and app
echo "🎯 Focusing simulator and ensuring app is active..."
osascript -e 'tell application "Simulator" to activate' 2>/dev/null || true
sleep 2

# Step 4: Tap to ensure app is in foreground
echo "👆 Ensuring app is in foreground..."
osascript -e '
tell application "Simulator"
    activate
end tell
tell application "System Events"
    tell process "Simulator"
        click at {200, 400}
        delay 1
        click at {200, 500}
    end tell
end tell
' 2>/dev/null || true

sleep 3

# Step 5: Start recording
echo "📹 Starting Simulator recording (MOV) -> $RAW_MOV"
xcrun simctl io "$DEVICE" recordVideo --codec=h264 "$RAW_MOV" 2>record.err &
REC_PID=$!

# Wait for recording to start
sleep 3

# Add extra time for navigation
echo "⏱️ Allowing extra time for navigation..."
sleep 5

# Step 6: Run Expo Go specific demo
echo "🤖 Running Expo Go specific demo sequence..."
node scripts/expo-go-demo.js || true

# Step 7: Stop recording
echo "⏹️ Stopping recording (SIGINT)..."
kill -INT $REC_PID 2>/dev/null || true
wait $REC_PID 2>/dev/null || true
sleep 2

if [ ! -s "$RAW_MOV" ]; then
  echo "❌ Recording failed or empty file: $RAW_MOV"
  [ -f record.err ] && echo "stderr:" && tail -n +1 record.err || true
  exit 1
fi

# Step 8: Convert to QuickTime-safe MP4
echo "🎬 Converting to QuickTime-safe MP4..."
if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -y -i "$RAW_MOV" \
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    -c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p -r 30 -fps_mode cfr \
    -c:a aac -b:a 128k -movflags +faststart "$QT_MP4" 2>/dev/null
else
  echo "⚠️ ffmpeg not found. Installing via Homebrew..."
  brew install ffmpeg
  ffmpeg -y -i "$RAW_MOV" \
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    -c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p -r 30 -fps_mode cfr \
    -c:a aac -b:a 128k -movflags +faststart "$QT_MP4" 2>/dev/null
fi

# Fallback to baseline if needed
if [ ! -s "$QT_MP4" ]; then
  echo "🔁 Retrying with Baseline profile for maximum compatibility..."
  ffmpeg -y -i "$RAW_MOV" -c:v libx264 -profile:v baseline -level 3.1 -pix_fmt yuv420p -r 30 -fps_mode cfr -c:a aac -b:a 128k -movflags +faststart "$QT_MP4" 2>/dev/null
fi

# Move outputs to Desktop
if [ -s "$QT_MP4" ]; then
  mv "$RAW_MOV" ~/Desktop/ 2>/dev/null || true
  mv "$QT_MP4" ~/Desktop/ 2>/dev/null || true
  echo "✅ Done -> ~/Desktop/$(basename "$QT_MP4")"
else
  echo "❌ Conversion failed. Raw file kept at: $RAW_MOV"
  exit 1
fi

# Clean up Expo process
if [ ! -z "${EXPO_PID:-}" ]; then
  kill $EXPO_PID 2>/dev/null || true
fi

echo "🎉 Demo recording complete with proper app focus!"
