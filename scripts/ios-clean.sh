#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)/mobile"

pkill -9 -x xcodebuild || true
pkill -9 -x XCBBuildService || true
watchman watch-del "$(pwd)" || true
watchman watch-project "$(pwd)" || true
rm -rf ios/Pods ios/Podfile.lock
rm -rf ~/Library/Developer/Xcode/DerivedData
rm -rf ~/Library/Developer/Xcode/Archives
rm -rf ~/Library/Caches/CocoaPods
pod repo update
cd ios && pod install --repo-update && cd ..

