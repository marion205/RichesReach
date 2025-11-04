#!/bin/bash
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
export LANG=en_US.UTF-8

cd /Users/marioncollins/RichesReach/mobile

echo "Building iOS dev client for iPhone 16 Pro..."
npx expo run:ios --device "iPhone 16 Pro"

