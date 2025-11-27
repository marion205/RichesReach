#!/bin/bash
# Run voice endpoint tests and benchmarks

set -e

echo "🧪 Running Voice Endpoint Tests"
echo "================================"
echo ""

# Check if server is running
echo "🔍 Checking if server is running on ${BASE_URL:-http://localhost:8000}..."
if ! curl -s -f "${BASE_URL:-http://localhost:8000}/health" > /dev/null 2>&1; then
    echo "⚠️  Warning: Server may not be running. Tests may fail."
    echo ""
fi

# Run unit tests
echo "📋 Running unit tests..."
python3 -m pytest test_voice_endpoints.py -v -s || {
    echo "❌ Unit tests failed"
    exit 1
}

echo ""
echo "✅ Unit tests passed!"
echo ""

# Run benchmark
echo "📊 Running benchmark tests..."
python3 test_voice_benchmark.py || {
    echo "❌ Benchmark tests failed"
    exit 1
}

echo ""
echo "✅ All tests completed!"

