#!/usr/bin/env bash
set -euo pipefail

du -sh ~/Library/Developer/Xcode/Archives 2>/dev/null || true
du -sh ~/Library/Developer/Xcode/DerivedData 2>/dev/null || true
du -sh ~/Library/Developer/Xcode/iOS\ DeviceSupport 2>/dev/null || true
du -sh ~/Library/Developer/CoreSimulator 2>/dev/null || true
du -sh ~/Library/Caches/CocoaPods 2>/dev/null || true
du -sh ~/.npm ~/.cache/yarn ~/.pnpm-store 2>/dev/null || true
du -sh ~/.expo 2>/dev/null || true

rm -rf ~/Library/Developer/Xcode/Archives/*
rm -rf ~/Library/Developer/Xcode/DerivedData/*
rm -rf ~/Library/Developer/Xcode/iOS\ DeviceSupport/*
rm -rf ~/Library/Developer/CoreSimulator/Caches/*
rm -rf ~/Library/Caches/CocoaPods/*
rm -rf ~/.npm/_cacache/*
rm -rf ~/.cache/yarn/*
rm -rf ~/.pnpm-store/*
rm -rf ~/.expo/*

brew cleanup -s || true
pod cache clean --all || true
watchman watch-del-all || true

echo ""
echo "✅ Space cleanup complete"
df -h / | tail -1

