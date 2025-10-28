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

# Check if Expo is running
echo "🔍 Checking if Expo server is running..."
if ! pgrep -f "expo start" >/dev/null; then
  echo "⚠️ Expo server not running. Starting Expo..."
  npx expo start --ios &
  sleep 10
fi

# Wait for app to be ready
echo "⏳ Waiting for RichesReach app to load..."
sleep 5

# Force focus on the simulator and app
echo "🎯 Focusing simulator and app..."
osascript -e 'tell application "Simulator" to activate' 2>/dev/null || true
sleep 2

# Tap to ensure app is active
echo "👆 Ensuring app is active..."
osascript -e '
tell application "Simulator"
    activate
end tell
tell application "System Events"
    tell process "Simulator"
        click at {200, 400}
    end tell
end tell
' 2>/dev/null || true

sleep 2

# Optional: make the status bar pretty
xcrun simctl status_bar "$DEVICE" override --time "9:41" --dataNetwork wifi --wifiBars 3 --batteryState charged --batteryLevel 100 || true

# Start recording to MOV
echo "📹 Starting Simulator recording (MOV) -> $RAW_MOV"
xcrun simctl io "$DEVICE" recordVideo --codec=h264 "$RAW_MOV" 2>record.err &
REC_PID=$!

# Wait for recording to start
sleep 3

# Run the automated demo
echo "🤖 Running automated demo sequence..."
node scripts/applescript-demo-recorder.js || true

# Stop recording with SIGINT
echo "⏹️ Stopping recording (SIGINT)..."
kill -INT $REC_PID 2>/dev/null || true
wait $REC_PID 2>/dev/null || true
sleep 2

if [ ! -s "$RAW_MOV" ]; then
  echo "❌ Recording failed or empty file: $RAW_MOV"
  [ -f record.err ] && echo "stderr:" && tail -n +1 record.err || true
  exit 1
fi

# Convert to QuickTime-safe MP4
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

# Clear status bar overrides
xcrun simctl status_bar "$DEVICE" clear || true

echo "🎉 Demo recording complete with proper app focus!"
