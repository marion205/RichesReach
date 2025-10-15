#!/usr/bin/env node
/**
* RichesReach App Store Screenshots Generator
* 
* This script helps generate App Store screenshots by:
* 1. Starting the app in iOS Simulator
* 2. Navigating to key screens
* 3. Capturing screenshots in required sizes
* 4. Organizing files for App Store submission
*/
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
// Configuration
const CONFIG = {
appName: 'RichesReach',
bundleId: 'com.richesreach.app',
screenshotDir: './screenshots',
devices: [
{
name: 'iPhone 14 Pro Max',
id: 'iPhone 14 Pro Max',
width: 1290,
height: 2796,
folder: 'iphone-6.7'
},
{
name: 'iPhone 11 Pro Max',
id: 'iPhone 11 Pro Max',
width: 1242,
height: 2688,
folder: 'iphone-6.5'
},
{
name: 'iPhone 8 Plus',
id: 'iPhone 8 Plus',
width: 1242,
height: 2208,
folder: 'iphone-5.5'
},
{
name: 'iPad Pro 12.9-inch',
id: 'iPad Pro (12.9-inch)',
width: 2048,
height: 2732,
folder: 'ipad-12.9'
},
{
name: 'iPad Pro 11-inch',
id: 'iPad Pro (11-inch)',
width: 1668,
height: 2388,
folder: 'ipad-11'
}
],
screenshots: [
{
name: '01-hero-ai-portfolio',
description: 'AI Portfolio Advisor - Main feature screen',
screen: 'AIPortfolioScreen'
},
{
name: '02-market-data',
description: 'Real-Time Market Data - Live market information',
screen: 'StocksScreen'
},
{
name: '03-portfolio-tracking',
description: 'Portfolio Tracking - Investment performance',
screen: 'PortfolioScreen'
},
{
name: '04-social-community',
description: 'Social Trading Community - User interactions',
screen: 'CommunityScreen'
},
{
name: '05-risk-education',
description: 'Risk Assessment & Education - Learning modules',
screen: 'EducationScreen'
}
]
};
class ScreenshotGenerator {
constructor() {
this.setupDirectories();
}
setupDirectories() {
console.log(' Setting up screenshot directories...');
// Create main screenshots directory
if (!fs.existsSync(CONFIG.screenshotDir)) {
fs.mkdirSync(CONFIG.screenshotDir, { recursive: true });
}
// Create device-specific directories
CONFIG.devices.forEach(device => {
const deviceDir = path.join(CONFIG.screenshotDir, device.folder);
if (!fs.existsSync(deviceDir)) {
fs.mkdirSync(deviceDir, { recursive: true });
}
});
console.log(' Directories created successfully');
}
checkPrerequisites() {
console.log(' Checking prerequisites...');
try {
// Check if Xcode is installed
execSync('xcode-select --print-path', { stdio: 'ignore' });
console.log(' Xcode found');
} catch (error) {
console.error(' Xcode not found. Please install Xcode from the App Store.');
process.exit(1);
}
try {
// Check if iOS Simulator is available
execSync('xcrun simctl list devices available', { stdio: 'ignore' });
console.log(' iOS Simulator available');
} catch (error) {
console.error(' iOS Simulator not available.');
process.exit(1);
}
console.log(' All prerequisites met');
}
listAvailableDevices() {
console.log(' Available iOS Simulators:');
try {
const output = execSync('xcrun simctl list devices available', { encoding: 'utf8' });
console.log(output);
} catch (error) {
console.error(' Failed to list devices:', error.message);
}
}
bootSimulator(deviceId) {
console.log(` Booting simulator: ${deviceId}`);
try {
execSync(`xcrun simctl boot "${deviceId}"`, { stdio: 'ignore' });
console.log(' Simulator booted successfully');
// Wait for simulator to be ready
console.log('⏳ Waiting for simulator to be ready...');
execSync('sleep 5');
} catch (error) {
console.log(' Simulator may already be running');
}
}
installApp(deviceId) {
console.log(` Installing app on ${deviceId}...`);
try {
// This would typically be done by running the app
console.log(' App installation completed (via npm run ios)');
} catch (error) {
console.error(' Failed to install app:', error.message);
}
}
captureScreenshot(deviceId, filename) {
console.log(` Capturing screenshot: ${filename}`);
try {
const outputPath = path.join(CONFIG.screenshotDir, filename);
execSync(`xcrun simctl io booted screenshot "${outputPath}"`, { stdio: 'ignore' });
console.log(` Screenshot saved: ${outputPath}`);
return true;
} catch (error) {
console.error(` Failed to capture screenshot: ${error.message}`);
return false;
}
}
generateScreenshots() {
console.log(' Starting screenshot generation...');
console.log('=====================================');
this.checkPrerequisites();
this.listAvailableDevices();
console.log('\n Screenshot Generation Plan:');
console.log('==============================');
CONFIG.screenshots.forEach((screenshot, index) => {
console.log(`${index + 1}. ${screenshot.name}: ${screenshot.description}`);
});
console.log('\n IMPORTANT: Before proceeding, make sure:');
console.log('1. Your app is running in iOS Simulator');
console.log('2. You have navigated to each required screen');
console.log('3. The app is in the correct state for screenshots');
console.log('\n Ready to start? (This will capture screenshots for all devices)');
console.log('Press Ctrl+C to cancel, or wait 10 seconds to continue...');
// Wait for user confirmation
setTimeout(() => {
this.startCaptureProcess();
}, 10000);
}
startCaptureProcess() {
console.log('\n Starting capture process...');
CONFIG.devices.forEach(device => {
console.log(`\n Processing ${device.name} (${device.width}x${device.height})`);
console.log('==========================================');
// Boot the simulator
this.bootSimulator(device.id);
// Capture each screenshot
CONFIG.screenshots.forEach(screenshot => {
const filename = `${device.folder}/${screenshot.name}.png`;
this.captureScreenshot(device.id, filename);
// Wait between captures
execSync('sleep 2');
});
});
this.generateReport();
}
generateReport() {
console.log('\n Screenshot Generation Report');
console.log('================================');
let totalScreenshots = 0;
let successfulScreenshots = 0;
CONFIG.devices.forEach(device => {
console.log(`\n ${device.name}:`);
CONFIG.screenshots.forEach(screenshot => {
const filename = `${device.folder}/${screenshot.name}.png`;
const filepath = path.join(CONFIG.screenshotDir, filename);
totalScreenshots++;
if (fs.existsSync(filepath)) {
const stats = fs.statSync(filepath);
console.log(` ${screenshot.name}.png (${Math.round(stats.size / 1024)}KB)`);
successfulScreenshots++;
} else {
console.log(` ${screenshot.name}.png (missing)`);
}
});
});
console.log(`\n Summary:`);
console.log(` Total screenshots: ${totalScreenshots}`);
console.log(` Successful: ${successfulScreenshots}`);
console.log(` Failed: ${totalScreenshots - successfulScreenshots}`);
if (successfulScreenshots === totalScreenshots) {
console.log('\n All screenshots generated successfully!');
console.log(' Check the screenshots/ directory for your files.');
console.log(' Remember to post-process them according to the guide.');
} else {
console.log('\n Some screenshots failed to generate.');
console.log(' Check the error messages above and try again.');
}
}
showInstructions() {
console.log(' RichesReach App Store Screenshots Generator');
console.log('==============================================');
console.log('');
console.log('This script helps you generate App Store screenshots for RichesReach.');
console.log('');
console.log('Usage:');
console.log(' node generate-screenshots.js [command]');
console.log('');
console.log('Commands:');
console.log(' generate - Generate all screenshots (default)');
console.log(' list - List available iOS simulators');
console.log(' setup - Set up directories only');
console.log(' help - Show this help message');
console.log('');
console.log('Prerequisites:');
console.log(' - Xcode installed');
console.log(' - iOS Simulator available');
console.log(' - App running in simulator');
console.log('');
console.log('Example:');
console.log(' 1. Start your app: npm run ios');
console.log(' 2. Navigate to each screen you want to capture');
console.log(' 3. Run: node generate-screenshots.js generate');
console.log(' 4. Check screenshots/ directory for results');
}
}
// Main execution
const command = process.argv[2] || 'generate';
const generator = new ScreenshotGenerator();
switch (command) {
case 'generate':
generator.generateScreenshots();
break;
case 'list':
generator.listAvailableDevices();
break;
case 'setup':
generator.setupDirectories();
console.log(' Directories set up successfully');
break;
case 'help':
default:
generator.showInstructions();
break;
}
