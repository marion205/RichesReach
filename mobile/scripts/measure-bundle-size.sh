#!/bin/bash
# Measure React Native Bundle Size
# Usage: ./scripts/measure-bundle-size.sh [android|ios]

set -e

PLATFORM=${1:-android}
OUTPUT_DIR="./bundle-analysis"
BUNDLE_FILE="${OUTPUT_DIR}/bundle.js"
BUNDLE_INFO="${OUTPUT_DIR}/bundle-info.txt"

echo "📦 Measuring Bundle Size for ${PLATFORM}..."
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Build bundle
echo "Building bundle..."
npx react-native bundle \
  --platform "${PLATFORM}" \
  --dev false \
  --entry-file index.js \
  --bundle-output "${BUNDLE_FILE}" \
  --assets-dest "${OUTPUT_DIR}/assets" \
  2>&1 | tee "${OUTPUT_DIR}/build.log"

# Measure size
if [ -f "${BUNDLE_FILE}" ]; then
  SIZE_BYTES=$(wc -c < "${BUNDLE_FILE}")
  SIZE_KB=$((SIZE_BYTES / 1024))
  SIZE_MB=$(echo "scale=2; ${SIZE_BYTES} / 1024 / 1024" | bc)
  LINE_COUNT=$(wc -l < "${BUNDLE_FILE}")
  
  echo "" > "${BUNDLE_INFO}"
  echo "📊 Bundle Size Analysis" >> "${BUNDLE_INFO}"
  echo "========================" >> "${BUNDLE_INFO}"
  echo "Platform: ${PLATFORM}" >> "${BUNDLE_INFO}"
  echo "Size: ${SIZE_MB} MB (${SIZE_KB} KB)" >> "${BUNDLE_INFO}"
  echo "Lines: ${LINE_COUNT}" >> "${BUNDLE_INFO}"
  echo "Date: $(date)" >> "${BUNDLE_INFO}"
  
  echo ""
  echo "✅ Bundle created successfully!"
  echo "📊 Size: ${SIZE_MB} MB (${SIZE_KB} KB)"
  echo "📄 Lines: ${LINE_COUNT}"
  echo "📁 Output: ${OUTPUT_DIR}/"
  echo ""
  echo "Target: <10MB ✅ or ⚠️"
  
  if (( $(echo "${SIZE_MB} < 10" | bc -l) )); then
    echo "✅ Bundle size is within target (<10MB)"
  else
    echo "⚠️ Bundle size exceeds target (${SIZE_MB}MB > 10MB)"
    echo "   Consider: Code splitting, tree-shaking, removing unused deps"
  fi
else
  echo "❌ Bundle file not created. Check build.log for errors."
  exit 1
fi

