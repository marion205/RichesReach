#!/bin/bash
# Debug script for Detox E2E tests with verbose logging

set -e

cd "$(dirname "$0")/.."

echo "🔍 Detox Debug Mode - Starting with verbose logging..."
echo ""

# Clean simulator state
echo "🧹 Cleaning simulator..."
xcrun simctl erase all 2>/dev/null || echo "⚠️  Could not erase simulator (may not exist)"

# Build Detox app
echo "🔨 Building Detox app..."
npm run build:e2e:ios || {
  echo "⚠️  Build failed, but continuing with test (may use existing build)..."
}

# Run test with maximum debug output
echo ""
echo "🧪 Running Detox test with full debugging..."
echo "   - Record logs: all"
echo "   - Take screenshots: failure"
echo "   - Debug: detox*"
echo ""

DEBUG=detox* npm run test:e2e:ios -- \
  --record-logs all \
  --take-screenshots failing \
  --loglevel trace \
  --retries 1

echo ""
echo "📸 Check artifacts/ folder for screenshots and logs"
echo "✅ Debug complete"

