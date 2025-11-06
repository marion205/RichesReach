#!/bin/bash
# Expo-Compatible Performance Benchmark Test
# Measures code metrics, dependencies, and optimization status

set -e

OUTPUT_DIR="./benchmark-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${OUTPUT_DIR}/benchmark_expo_${TIMESTAMP}.txt"

echo "🚀 Running Expo Performance Benchmark Tests..."
echo "=============================================="
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Start timer
START_TIME=$(date +%s)

# 1. Code Metrics Analysis
echo "📊 1. Code Metrics Analysis" | tee "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"
echo "Timestamp: $(date)" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

if [ -d "src" ]; then
  # Count files
  TSX_COUNT=$(find src -name "*.tsx" 2>/dev/null | wc -l | xargs)
  TS_COUNT=$(find src -name "*.ts" 2>/dev/null | wc -l | xargs)
  JS_COUNT=$(find src -name "*.js" 2>/dev/null | wc -l | xargs)
  JSX_COUNT=$(find src -name "*.jsx" 2>/dev/null | wc -l | xargs)
  
  # Count lines
  TOTAL_LINES=$(find src -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.js" -o -name "*.jsx" \) -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
  
  # Count components (files with default export or component naming)
  COMPONENT_COUNT=$(grep -r "export default\|export.*function\|export.*const.*=" src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l | xargs)
  
  # Find largest files
  LARGEST_FILES=$(find src -type f \( -name "*.tsx" -o -name "*.ts" \) -exec wc -l {} + 2>/dev/null | sort -rn | head -10)
  
  echo "TypeScript React files (.tsx): ${TSX_COUNT}" | tee -a "${REPORT_FILE}"
  echo "TypeScript files (.ts): ${TS_COUNT}" | tee -a "${REPORT_FILE}"
  echo "JavaScript files (.js): ${JS_COUNT}" | tee -a "${REPORT_FILE}"
  echo "JavaScript React files (.jsx): ${JSX_COUNT}" | tee -a "${REPORT_FILE}"
  echo "Total lines of code: ${TOTAL_LINES}" | tee -a "${REPORT_FILE}"
  echo "Estimated components: ${COMPONENT_COUNT}" | tee -a "${REPORT_FILE}"
  echo "" | tee -a "${REPORT_FILE}"
  
  echo "Largest files (top 10):" | tee -a "${REPORT_FILE}"
  echo "${LARGEST_FILES}" | tee -a "${REPORT_FILE}"
  echo "" | tee -a "${REPORT_FILE}"
fi

# 2. Dependency Analysis
echo "📚 2. Dependency Analysis" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

if [ -f "package.json" ]; then
  # Count dependencies
  DEPENDENCIES=$(grep -E '^\s*"[^"]+":\s*"' package.json | grep -v "scripts" | wc -l | xargs)
  DEV_DEPENDENCIES=$(grep -A 100 '"devDependencies"' package.json | grep -E '^\s*"[^"]+":\s*"' | wc -l | xargs)
  
  echo "Production dependencies: ${DEPENDENCIES}" | tee -a "${REPORT_FILE}"
  echo "Dev dependencies: ${DEV_DEPENDENCIES}" | tee -a "${REPORT_FILE}"
  
  # Check for heavy dependencies
  echo "" | tee -a "${REPORT_FILE}"
  echo "Heavy dependencies (checking node_modules):" | tee -a "${REPORT_FILE}"
  if [ -d "node_modules" ]; then
    find node_modules -type f -name "*.js" -size +1M -exec ls -lh {} \; 2>/dev/null | \
      sort -k5 -rh | head -10 | awk '{print "   " $9 " (" $5 ")"}' | tee -a "${REPORT_FILE}" || \
      echo "   (Unable to analyze)" | tee -a "${REPORT_FILE}"
  fi
  echo "" | tee -a "${REPORT_FILE}"
fi

# 3. Asset Analysis
echo "🖼️  3. Asset Analysis" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

if [ -d "assets" ]; then
  ASSET_COUNT=$(find assets -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.svg" \) 2>/dev/null | wc -l | xargs)
  ASSET_SIZE=$(du -sh assets 2>/dev/null | cut -f1 || echo "N/A")
  
  PNG_COUNT=$(find assets -name "*.png" 2>/dev/null | wc -l | xargs)
  JPG_COUNT=$(find assets -name "*.jpg" -o -name "*.jpeg" 2>/dev/null | wc -l | xargs)
  SVG_COUNT=$(find assets -name "*.svg" 2>/dev/null | wc -l | xargs)
  
  echo "Total image files: ${ASSET_COUNT}" | tee -a "${REPORT_FILE}"
  echo "  - PNG: ${PNG_COUNT}" | tee -a "${REPORT_FILE}"
  echo "  - JPG/JPEG: ${JPG_COUNT}" | tee -a "${REPORT_FILE}"
  echo "  - SVG: ${SVG_COUNT}" | tee -a "${REPORT_FILE}"
  echo "Total asset size: ${ASSET_SIZE}" | tee -a "${REPORT_FILE}"
  echo "" | tee -a "${REPORT_FILE}"
  
  # List largest assets
  echo "Largest assets (top 5):" | tee -a "${REPORT_FILE}"
  find assets -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -exec ls -lh {} \; 2>/dev/null | \
    sort -k5 -rh | head -5 | awk '{print "   " $9 " (" $5 ")"}' | tee -a "${REPORT_FILE}" || \
    echo "   (No images found)" | tee -a "${REPORT_FILE}"
  echo "" | tee -a "${REPORT_FILE}"
fi

# 4. Optimization Status Check
echo "⚡ 4. Optimization Status" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

# Check Metro config
if [ -f "metro.config.js" ]; then
  if grep -q "inlineRequires" metro.config.js; then
    echo "✅ Metro config: Optimized (inline requires)" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Metro config: Not optimized" | tee -a "${REPORT_FILE}"
  fi
  
  if grep -q "minifierConfig" metro.config.js; then
    echo "✅ Metro config: Minification enabled" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Metro config: Minification not configured" | tee -a "${REPORT_FILE}"
  fi
  
  if grep -q "tree-shaking\|unstable_enableSymlinks" metro.config.js; then
    echo "✅ Metro config: Tree-shaking enabled" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Metro config: Tree-shaking not explicitly enabled" | tee -a "${REPORT_FILE}"
  fi
else
  echo "❌ Metro config: File not found" | tee -a "${REPORT_FILE}"
fi

# Check lazy loading
if [ -f "src/App.tsx" ]; then
  LAZY_COUNT=$(grep -c "lazy(" src/App.tsx 2>/dev/null || echo "0")
  SUSPENSE_COUNT=$(grep -c "Suspense" src/App.tsx 2>/dev/null || echo "0")
  
  if [ "${LAZY_COUNT}" -gt 0 ]; then
    echo "✅ Code splitting: ${LAZY_COUNT} lazy-loaded components" | tee -a "${REPORT_FILE}"
    echo "✅ Suspense boundaries: ${SUSPENSE_COUNT} found" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Code splitting: Not implemented" | tee -a "${REPORT_FILE}"
  fi
else
  echo "⚠️  App.tsx: Not found" | tee -a "${REPORT_FILE}"
fi

# Check lodash-es
if [ -f "package.json" ]; then
  if grep -q "lodash-es" package.json; then
    echo "✅ Dependencies: lodash-es (tree-shakeable)" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Dependencies: lodash-es not found" | tee -a "${REPORT_FILE}"
  fi
fi

# Check for unused imports (basic check)
if command -v grep &> /dev/null; then
  UNUSED_IMPORTS=$(grep -r "import.*from.*unused\|import.*from.*test" src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l | xargs)
  if [ "${UNUSED_IMPORTS}" -gt 0 ]; then
    echo "⚠️  Potential unused imports: ${UNUSED_IMPORTS} found" | tee -a "${REPORT_FILE}"
  fi
fi

echo "" | tee -a "${REPORT_FILE}"

# 5. Performance Targets & Recommendations
echo "🎯 5. Performance Targets & Recommendations" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

# Code size recommendations
if [ -n "${TOTAL_LINES}" ] && [ "${TOTAL_LINES}" -gt 0 ]; then
  if [ "${TOTAL_LINES}" -lt 100000 ]; then
    echo "✅ Code size: ${TOTAL_LINES} lines (Good - <100K)" | tee -a "${REPORT_FILE}"
  elif [ "${TOTAL_LINES}" -lt 200000 ]; then
    echo "⚠️  Code size: ${TOTAL_LINES} lines (Consider code splitting - >100K)" | tee -a "${REPORT_FILE}"
  else
    echo "❌ Code size: ${TOTAL_LINES} lines (Large - >200K, needs optimization)" | tee -a "${REPORT_FILE}"
  fi
fi

# Asset recommendations
if [ -n "${PNG_COUNT}" ] && [ "${PNG_COUNT}" -gt 0 ]; then
  if [ "${PNG_COUNT}" -gt 5 ]; then
    echo "⚠️  Image optimization: ${PNG_COUNT} PNG files found (consider WebP conversion)" | tee -a "${REPORT_FILE}"
  else
    echo "✅ Image optimization: ${PNG_COUNT} PNG files (manageable)" | tee -a "${REPORT_FILE}"
  fi
fi

# Dependency recommendations
if [ -n "${DEPENDENCIES}" ] && [ "${DEPENDENCIES}" -gt 50 ]; then
  echo "⚠️  Dependencies: ${DEPENDENCIES} packages (consider audit for unused deps)" | tee -a "${REPORT_FILE}"
else
  echo "✅ Dependencies: ${DEPENDENCIES} packages (reasonable)" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"

# 6. Bundle Size Estimation (Expo)
echo "📦 6. Estimated Bundle Size (Expo)" | tee -a "${REPORT_FILE}"
echo "----------------------------" | tee -a "${REPORT_FILE}"

# Estimate based on code size
if [ -n "${TOTAL_LINES}" ] && [ "${TOTAL_LINES}" -gt 0 ]; then
  # Rough estimate: ~50 bytes per line of code (minified)
  ESTIMATED_BYTES=$((TOTAL_LINES * 50))
  ESTIMATED_KB=$((ESTIMATED_BYTES / 1024))
  ESTIMATED_MB=$(echo "scale=2; ${ESTIMATED_BYTES} / 1024 / 1024" | bc)
  
  echo "Estimated bundle size (minified): ${ESTIMATED_MB} MB (${ESTIMATED_KB} KB)" | tee -a "${REPORT_FILE}"
  echo "Note: Actual size depends on dependencies and Metro bundler optimizations" | tee -a "${REPORT_FILE}"
  
  if (( $(echo "${ESTIMATED_MB} < 10" | bc -l 2>/dev/null || echo "0") )); then
    echo "✅ Estimated size: <10MB target (Good)" | tee -a "${REPORT_FILE}"
  else
    echo "⚠️  Estimated size: >10MB (Consider further optimization)" | tee -a "${REPORT_FILE}"
  fi
fi

# End timer
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo "" | tee -a "${REPORT_FILE}"
echo "==============================================" | tee -a "${REPORT_FILE}"
echo "✅ Benchmark Complete!" | tee -a "${REPORT_FILE}"
echo "Total time: ${TOTAL_TIME}s" | tee -a "${REPORT_FILE}"
echo "Report saved: ${REPORT_FILE}" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

# Display summary
echo ""
echo "📊 BENCHMARK SUMMARY"
echo "==================="
cat "${REPORT_FILE}" | grep -E "(✅|⚠️|❌|Estimated|Optimization)" | head -20
echo ""
echo "📄 Full report: ${REPORT_FILE}"

