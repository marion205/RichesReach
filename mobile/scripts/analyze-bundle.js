#!/usr/bin/env node

/**
 * Bundle Size Analysis Script
 * 
 * Analyzes React Native bundle size and generates reports
 * Uses react-native-bundle-visualizer and source-map-explorer
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const PLATFORM = process.argv[2] || 'ios';
const OUTPUT_DIR = path.join(__dirname, '../bundle-analysis');

console.log(`📦 Analyzing bundle size for ${PLATFORM}...\n`);

// Create output directory
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

try {
  // Step 1: Generate bundle
  console.log('1️⃣ Generating bundle...');
  const bundlePath = path.join(OUTPUT_DIR, `${PLATFORM}-bundle.js`);
  const sourceMapPath = path.join(OUTPUT_DIR, `${PLATFORM}-bundle.js.map`);

  execSync(
    `npx react-native bundle \
      --platform ${PLATFORM} \
      --dev false \
      --entry-file index.js \
      --bundle-output ${bundlePath} \
      --sourcemap-output ${sourceMapPath} \
      --minify`,
    { stdio: 'inherit' }
  );

  // Step 2: Analyze with source-map-explorer
  console.log('\n2️⃣ Analyzing bundle composition...');
  const reportPath = path.join(OUTPUT_DIR, `${PLATFORM}-report.html`);
  
  execSync(
    `npx source-map-explorer ${bundlePath} --html ${reportPath}`,
    { stdio: 'inherit' }
  );

  // Step 3: Get bundle size
  const stats = fs.statSync(bundlePath);
  const sizeInMB = (stats.size / (1024 * 1024)).toFixed(2);
  const sizeInKB = (stats.size / 1024).toFixed(2);

  console.log('\n✅ Bundle analysis complete!');
  console.log(`\n📊 Bundle Size: ${sizeInMB} MB (${sizeInKB} KB)`);
  console.log(`📄 Report: ${reportPath}`);
  console.log(`\n💡 Tips to reduce bundle size:`);
  console.log(`   - Use dynamic imports for heavy screens`);
  console.log(`   - Remove unused dependencies`);
  console.log(`   - Optimize images and assets`);
  console.log(`   - Enable Hermes for better compression`);

  // Generate summary JSON
  const summary = {
    platform: PLATFORM,
    size: {
      bytes: stats.size,
      kb: parseFloat(sizeInKB),
      mb: parseFloat(sizeInMB),
    },
    bundlePath,
    sourceMapPath,
    reportPath,
    timestamp: new Date().toISOString(),
  };

  fs.writeFileSync(
    path.join(OUTPUT_DIR, `${PLATFORM}-summary.json`),
    JSON.stringify(summary, null, 2)
  );

} catch (error) {
  console.error('❌ Bundle analysis failed:', error.message);
  process.exit(1);
}

