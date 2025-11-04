#!/bin/bash
# CocoaPods installation wrapper script
# Uses system Ruby to avoid RVM conflicts

set -e

cd "$(dirname "$0")"

echo "🔧 Running pod install with system Ruby..."

# Use system Ruby with clean environment
env -i \
  HOME="$HOME" \
  PATH="/usr/bin:/bin:/usr/local/bin" \
  /usr/bin/ruby -S ~/.gem/ruby/2.6.0/bin/pod install "$@"

echo "✅ Pod install completed!"

