const { execSync } = require('child_process');

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function runAppleScriptCommand(command) {
    try {
        console.log(`🔧 Running: ${command}`);
        execSync(`osascript -e '${command}'`);
        console.log(`✅ Success`);
        return true;
    } catch (error) {
        console.warn(`❌ Failed: ${error.message}`);
        return false;
    }
}

async function checkAndLaunchApp() {
    console.log('🔍 Checking and Launching RichesReach App...');
    
    // Step 1: Check if simulator is running
    console.log('\n📱 Step 1: Checking simulator status');
    try {
        const result = execSync('xcrun simctl list devices | grep "iPhone 16 Pro"', { encoding: 'utf8' });
        console.log('✅ iPhone 16 Pro simulator found');
    } catch (error) {
        console.log('❌ iPhone 16 Pro simulator not found');
        return;
    }
    
    // Step 2: Boot simulator if needed
    console.log('\n📱 Step 2: Booting simulator');
    try {
        execSync('xcrun simctl boot "iPhone 16 Pro"', { stdio: 'inherit' });
        console.log('✅ Simulator booted');
    } catch (error) {
        console.log('ℹ️ Simulator already booted or boot failed');
    }
    
    await delay(3000);
    
    // Step 3: Launch RichesReach app
    console.log('\n📱 Step 3: Launching RichesReach app');
    try {
        // Try to launch the app by bundle ID
        execSync('xcrun simctl launch "iPhone 16 Pro" com.richesreach.mobile', { stdio: 'inherit' });
        console.log('✅ App launched via bundle ID');
    } catch (error) {
        console.log('⚠️ Bundle ID launch failed, trying Expo URL');
        try {
            // Try Expo URL
            execSync('xcrun simctl openurl "iPhone 16 Pro" "exp://127.0.0.1:8081"', { stdio: 'inherit' });
            console.log('✅ App launched via Expo URL');
        } catch (error2) {
            console.log('❌ Both launch methods failed');
        }
    }
    
    await delay(5000);
    
    // Step 4: Activate simulator and app
    console.log('\n📱 Step 4: Activating simulator');
    await runAppleScriptCommand('tell application "Simulator" to activate');
    await delay(2000);
    
    // Step 5: Test if app is responsive
    console.log('\n📱 Step 5: Testing app responsiveness');
    await runAppleScriptCommand(`
        tell application "Simulator"
            activate
        end tell
        tell application "System Events"
            tell process "Simulator"
                click at {200, 400}
            end tell
        end tell
    `);
    
    console.log('\n🎉 App launch complete! Check simulator to see if RichesReach is running.');
}

if (require.main === module) {
    checkAndLaunchApp();
} else {
    module.exports = checkAndLaunchApp;
}
