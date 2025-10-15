#!/usr/bin/env node

/**
 * UI Test Runner
 * Provides instructions for testing the swing trading UI components
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Swing Trading UI Test Runner\n');

// Check if we're in the right directory
if (!fs.existsSync('package.json')) {
  console.log('❌ Please run this script from the mobile directory');
  process.exit(1);
}

// Check if node_modules exists
if (!fs.existsSync('node_modules')) {
  console.log('📦 Installing dependencies...');
  try {
    execSync('npm install', { stdio: 'inherit' });
    console.log('✅ Dependencies installed successfully\n');
  } catch (error) {
    console.log('❌ Failed to install dependencies');
    process.exit(1);
  }
}

console.log('🧪 UI Testing Options:\n');

console.log('1. 📱 Test with Expo Go (Recommended for quick testing)');
console.log('   - Run: npm start');
console.log('   - Scan QR code with Expo Go app on your phone');
console.log('   - Navigate to the test screen\n');

console.log('2. 🖥️  Test with iOS Simulator');
console.log('   - Run: npm run ios');
console.log('   - Requires Xcode and iOS Simulator\n');

console.log('3. 🤖 Test with Android Emulator');
console.log('   - Run: npm run android');
console.log('   - Requires Android Studio and emulator\n');

console.log('4. 🌐 Test with Web Browser');
console.log('   - Run: npm run web');
console.log('   - Opens in browser (limited React Native features)\n');

console.log('📋 Test Checklist:');
console.log('   ✅ Signals screen displays mock trading signals');
console.log('   ✅ Backtest screen shows strategy results');
console.log('   ✅ Day Trading screen shows picks with risk metrics');
console.log('   ✅ Risk screen calculates position sizing');
console.log('   ✅ All tabs switch correctly');
console.log('   ✅ Data displays properly formatted');
console.log('   ✅ UI is responsive and looks good\n');

console.log('🔧 To add the test screen to your app:');
console.log('   1. Import SwingTradingTestScreen in your main App.tsx');
console.log('   2. Add it to your navigation stack');
console.log('   3. Or temporarily replace your main screen with it\n');

console.log('📊 Mock Data Includes:');
console.log('   - 3 realistic trading signals with ML scores');
console.log('   - 2 backtest strategies with performance metrics');
console.log('   - 2 day trading picks with risk calculations');
console.log('   - Risk management calculator with position sizing\n');

console.log('🎯 Ready to test! Choose an option above and start the development server.');

// Check if we should start the server automatically
const args = process.argv.slice(2);
if (args.includes('--start')) {
  console.log('\n🚀 Starting development server...\n');
  try {
    execSync('npm start', { stdio: 'inherit' });
  } catch (error) {
    console.log('❌ Failed to start development server');
  }
}
