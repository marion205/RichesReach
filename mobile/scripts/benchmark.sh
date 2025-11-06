#!/bin/bash
# Comprehensive Performance Benchmark Test
# Measures bundle size, build time, and provides performance metrics

set -e

OUTPUT_DIR="./benchmark-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${OUTPUT_DIR}/benchmark_${TIMESTAMP}.txt"
BUNDLE_DIR="./bundle-analysis"

echo "🚀 Running Performance Benchmark Tests..."
echo "=========================================="
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${BUNDLE_DIR}"

# Start timer
START_TIME=$(date +%s)

# 1. Bundle Size Measurement
echo "📦 1. Measuring Bundle Size..."
echo "----------------------------" | tee -a "${REPORT_FILE}"
echo "Timestamp: $(date)" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

# Android Bundle
echo "Building Android bundle..."
ANDROID_START=$(date +%s)
npx react-native bundle \
  --platform android \
  --dev false \
  --entry-file index.js \
  --bundle-output "${BUNDLE_DIR}/android-bundle.js" \
  --assets-dest "${BUNDLE_DIR}/android-assets" \
  2>&1 | tee "${BUNDLE_DIR}/android-build.log"

ANDROID_END=$(date +%s)
ANDROID_BUILD_TIME=$((ANDROID_END - ANDROID_START))

if [ -f "${BUNDLE_DIR}/android-bundle.js" ]; then
  ANDROID_SIZE_BYTES=$(wc -c < "${BUNDLE_DIR}/android-bundle.js")
  ANDROID_SIZE_KB=$((ANDROID_SIZE_BYTES / 1024))
  ANDROID_SIZE_MB=$(echo "scale=2; ${ANDROID_SIZE_BYTES} / 1024 / 1024" | bc)
  ANDROID_LINES=$(wc -l < "${BUNDLE_DIR}/android-bundle.js")
  
  echo "✅ Android Bundle:" | tee -a "${REPORT_FILE}"
  echo "   Size: ${ANDROID_SIZE_MB} MB (${ANDROID_SIZE_KB} KB)" | tee -a "${REPORT_FILE}"
  echo "   Lines: ${ANDROID_LINES}" | tee -a "${REPORT_FILE}"
  echo "   Build Time: ${ANDROID_BUILD_TIME}s" | tee -a "${REPORT_FILE}"
  echo "" | tee -a "${REPORT_FILE}"
else
  echo "❌ Android bundle failed to build" | tee -a "${REPORT_FILE}"
  ANDROID_SIZE_MB=0
fi

# iOS Bundle (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Building iOS bundle..."
  IOS_START=$(date +%s)
  npx react-native bundle \
    --platform ios \
    --dev false \
    --entry-file index.js \
    --bundle-output "${BUNDLE_DIR}/ios-bundle.js" \
    --assets-dest "${BUNDLE_DIR}/ios-assets" \
    2>&1 | tee "${BUNDLE_DIR}/ios-build.log"
  
  IOS_END=$(date +%s)
  IOS_BUILD_TIME=$((IOS_END - IOS_START))
  
  if [ -f "${BUNDLE_DIR}/ios-bundle.js" ]; then
    IOS_SIZE_BYTES=$(wc -c < "${BUNDLE_DIR}/ios-bundle.js")
    IOS_SIZE_KB=$((IOS_SIZE_BYTES / 1024))
    IOS_SIZE_MB=$(echo "scale=2; ${IOS_SIZE_BYTES} / 1024 / 1024" | bc)
    IOS_LINES=$(wc -l < "${BUNDLE_DIR}/ios-bundle.js")
    
    echo "✅ iOS Bundle:" | tee -a "${REPORT_FILE}"
    echo "   Size: ${IOS_SIZE_MB} MB (${IOS_SIZE_KB} KB)" | tee -a "${REPORT_FILE}"
    echo "   Lines: ${IOS_LINES}" | tee -a "${REPORT_FILE}"
    echo "   Build Time: ${IOS_BUILD_TIME}s" | tee -a "${REPORT_FILE}"
    echo "" | tee -a "${REPORT_FILE}"
  else
    echo "❌ iOS bundle failed to build" | tee -a "${REPORT_FILE}"
    IOS_SIZE_MB=0
  fi
fi

# 2. Dependency Analysis
echo "" | tee -a "${REPORT_FILE}"
echo "📚 2. Dependency Analysis" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

if command -v npm &> /dev/null; then
  TOTAL_DEPS=$(npm list --depth=0 2>/dev/null | wc -l | xargs)
  echo "Total dependencies: ${TOTAL_DEPS}" | tee -a "${REPORT_FILE}"
fi

# Check for heavy dependencies
echo "Heavy dependencies (>1MB):" | tee -a "${REPORT_FILE}"
if [ -d "node_modules" ]; then
  find node_modules -type f -name "*.js" -exec du -ch {} + 2>/dev/null | \
    sort -rh | head -10 | tee -a "${REPORT_FILE}" || echo "   (Unable to analyze)" | tee -a "${REPORT_FILE}"
fi

# 3. Asset Analysis
echo "" | tee -a "${REPORT_FILE}"
echo "🖼️  3. Asset Analysis" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

if [ -d "assets" ]; then
  ASSET_COUNT=$(find assets -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) | wc -l | xargs)
  ASSET_SIZE=$(du -sh assets 2>/dev/null | cut -f1)
  echo "Image files: ${ASSET_COUNT}" | tee -a "${REPORT_FILE}"
  echo "Total asset size: ${ASSET_SIZE}" | tee -a "${REPORT_FILE}"
  
  # List largest assets
  echo "" | tee -a "${REPORT_FILE}"
  echo "Largest assets:" | tee -a "${REPORT_FILE}"
  find assets -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -exec ls -lh {} \; | \
    sort -k5 -rh | head -5 | awk '{print "   " $9 " (" $5 ")"}' | tee -a "${REPORT_FILE}"
fi

# 4. Code Metrics
echo "" | tee -a "${REPORT_FILE}"
echo "📊 4. Code Metrics" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

if [ -d "src" ]; then
  TSX_COUNT=$(find src -name "*.tsx" 2>/dev/null | wc -l | xargs)
  TS_COUNT=$(find src -name "*.ts" 2>/dev/null | wc -l | xargs)
  JS_COUNT=$(find src -name "*.js" 2>/dev/null | wc -l | xargs)
  TOTAL_LINES=$(find src -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.js" \) -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
  
  echo "TypeScript files (.tsx): ${TSX_COUNT}" | tee -a "${REPORT_FILE}"
  echo "TypeScript files (.ts): ${TS_COUNT}" | tee -a "${REPORT_FILE}"
  echo "JavaScript files (.js): ${JS_COUNT}" | tee -a "${REPORT_FILE}"
  echo "Total lines of code: ${TOTAL_LINES}" | tee -a "${REPORT_FILE}"
fi

# 5. Performance Targets
echo "" | tee -a "${REPORT_FILE}"
echo "🎯 5. Performance Targets" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

# Bundle size target
if [ -n "${ANDROID_SIZE_MB}" ] && [ "${ANDROID_SIZE_MB}" != "0" ]; then
  if (( $(echo "${ANDROID_SIZE_MB} < 10" | bc -l) )); then
    echo "✅ Bundle Size: ${ANDROID_SIZE_MB}MB < 10MB target" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Bundle Size: ${ANDROID_SIZE_MB}MB > 10MB target" | tee -a "${REPORT_FILE}"
  fi
fi

# Build time target
if [ "${ANDROID_BUILD_TIME}" -lt 60 ]; then
  echo "✅ Build Time: ${ANDROID_BUILD_TIME}s < 60s target" | tee -a "${REPORT_FILE}"
else
  echo "⚠️  Build Time: ${ANDROID_BUILD_TIME}s > 60s target" | tee -a "${REPORT_FILE}"
fi

# 6. Optimization Status
echo "" | tee -a "${REPORT_FILE}"
echo "⚡ 6. Optimization Status" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

# Check Metro config
if [ -f "metro.config.js" ]; then
  if grep -q "inlineRequires" metro.config.js; then
    echo "✅ Metro config: Optimized (inline requires)" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Metro config: Not optimized" | tee -a "${REPORT_FILE}"
  fi
fi

# Check lazy loading
if [ -f "src/App.tsx" ]; then
  if grep -q "lazy(" src/App.tsx; then
    LAZY_COUNT=$(grep -c "lazy(" src/App.tsx || echo "0")
    echo "✅ Code splitting: ${LAZY_COUNT} lazy-loaded components" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Code splitting: Not implemented" | tee -a "${REPORT_FILE}"
  fi
fi

# Check lodash-es
if [ -f "package.json" ]; then
  if grep -q "lodash-es" package.json; then
    echo "✅ Dependencies: lodash-es (tree-shakeable)" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Dependencies: lodash (not tree-shakeable)" | tee -a "${REPORT_FILE}"
  fi
fi

# End timer
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo "" | tee -a "${REPORT_FILE}"
echo "==========================================" | tee -a "${REPORT_FILE}"
echo "✅ Benchmark Complete!" | tee -a "${REPORT_FILE}"
echo "Total time: ${TOTAL_TIME}s" | tee -a "${REPORT_FILE}"
echo "Report saved: ${REPORT_FILE}" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

# Display summary
echo ""
echo "📊 BENCHMARK SUMMARY"
echo "==================="
cat "${REPORT_FILE}" | grep -E "(Bundle Size|Build Time|Optimization Status|✅|⚠️)" | tail -10
echo ""
echo "📄 Full report: ${REPORT_FILE}"

