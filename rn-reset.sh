#!/bin/bash

# React Native/Expo/iOS Simulator Reset Script (Nov 2025 Edition)
# Usage: ./rn-reset.sh [--skip-erase] [--verbose]
# Resets caches, kills processes, and (optionally) wipes Simulator.

set -e  # Exit on any error (remove for || true leniency)

VERBOSE=false
SKIP_ERASE=false

# Parse flags
while [[ $# -gt 0 ]]; do
  case $1 in
    --verbose) VERBOSE=true; shift ;;
    --skip-erase) SKIP_ERASE=true; shift ;;
    *) echo "Unknown option $1"; exit 1 ;;
  esac
done

log() {
  if [[ $VERBOSE == true ]]; then
    echo "[RESET] $1"
  fi
}

log "Starting React Native/Expo/iOS reset..."

# 1. Kill Simulator.app processes
log "Killing Simulator.app..."
pkill -f "Simulator.app" || true

# 2. Kill expo start processes
log "Killing expo start..."
pkill -f "expo start" || true
pkill -f "npx expo start" || true  # Covers npx variants

# 3. Clear Watchman watches (file watcher for Metro)
log "Clearing Watchman watches..."
watchman watch-del-all || true

# 4. Nuke Metro/Expo caches
log "Removing Metro/Expo caches..."
rm -rf "$TMPDIR/metro-*" "$TMPDIR/haste-map-*" ~/.metro ~/.cache/expo
rm -rf ~/Library/Caches/com.facebook.react-native/  # RN-specific cache
rm -rf ~/Library/Developer/Xcode/DerivedData/*  # Xcode derived data (build artifacts)

# 5. Optional: Clear npm/yarn caches (uncomment if needed)
# npm start --cache-only || true  # Or yarn cache clean

# 6. Launch Simulator
log "Launching iOS Simulator..."
open -a Simulator || { echo "Simulator failed to launch—check Xcode install"; exit 1; }

# 7. Erase all simulators (destructive—skippable)
if [[ $SKIP_ERASE == false ]]; then
  log "Erasing all simulators (this may take 10-60s)..."
  xcrun simctl erase all || { echo "Erase failed—some sims may be in use"; }
else
  log "Skipping Simulator erase (--skip-erase flag)."
fi

# 8. Post-reset: List available simulators for sanity check
log "Available simulators:"
xcrun simctl list devices | grep -E "(iPhone|iPad)" | head -5 || true

log "Reset complete! Restart with 'expo start --clear' or 'npx react-native start --reset-cache'."

