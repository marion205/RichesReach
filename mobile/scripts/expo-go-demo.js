const { execSync } = require('child_process');

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function runAppleScriptCommand(command) {
    try {
        execSync(`osascript -e '${command}'`);
        return true;
    } catch (error) {
        console.warn(`⚠️ AppleScript failed: ${error.message}`);
        return false;
    }
}

async function tap(x, y, description = `Tap at (${x}, ${y})`) {
    console.log(`🎯 ${description}`);
    const success = await runAppleScriptCommand(`
        tell application "Simulator"
            activate
        end tell
        tell application "System Events"
            tell process "Simulator"
                click at {${x}, ${y}}
            end tell
        end tell
    `);
    if (success) {
        console.log(`✅ Tap successful`);
    } else {
        console.log(`❌ Tap failed`);
    }
    await delay(2000);
}

async function runExpoGoDemo() {
    console.log('🚀 Expo Go Demo Starting...');
    
    // First ensure app is launched
    console.log('\n📱 Step 1: Ensuring Expo Go app is running');
    try {
        execSync('xcrun simctl openurl "iPhone 16 Pro" "exp://127.0.0.1:8081"', { stdio: 'inherit' });
        console.log('✅ Expo Go app launched');
    } catch (error) {
        console.log('⚠️ Expo Go launch failed');
    }
    
    await delay(5000);
    
    // Activate simulator
    await runAppleScriptCommand('tell application "Simulator" to activate');
    await delay(2000);
    
    console.log('\n📱 Step 2: Testing onboarding bypass');
    // Try different skip locations for Expo Go
    const skipLocations = [
        {x: 200, y: 700, desc: 'Bottom Center'},
        {x: 350, y: 100, desc: 'Top Right'},
        {x: 200, y: 650, desc: 'Lower Center'},
        {x: 200, y: 750, desc: 'Bottom Edge'},
        {x: 200, y: 600, desc: 'Center Bottom'},
    ];
    
    for (const loc of skipLocations) {
        await tap(loc.x, loc.y, `Skip: ${loc.desc}`);
    }
    
    console.log('\n📱 Step 3: Testing tab navigation');
    // Test bottom tab navigation with Expo Go coordinates
    const tabLocations = [
        {x: 50, y: 800, desc: 'Home Tab'},
        {x: 100, y: 800, desc: 'Stocks Tab'},
        {x: 150, y: 800, desc: 'Crypto Tab'},
        {x: 200, y: 800, desc: 'AI Portfolio Tab'},
        {x: 250, y: 800, desc: 'Tutor Tab'},
        {x: 300, y: 800, desc: 'Trading Tab'},
        {x: 350, y: 800, desc: 'Portfolio Tab'},
        {x: 400, y: 800, desc: 'Discuss Tab'},
    ];
    
    // Navigate through tabs multiple times
    for (let round = 0; round < 2; round++) {
        console.log(`\n📱 Tab round ${round + 1}:`);
        for (const tab of tabLocations) {
            await tap(tab.x, tab.y, tab.desc);
        }
    }
    
    console.log('\n📱 Step 4: Testing content areas');
    // Test various content areas
    const contentAreas = [
        {x: 200, y: 200, desc: 'Top Center'},
        {x: 200, y: 300, desc: 'Upper Center'},
        {x: 200, y: 400, desc: 'Center'},
        {x: 200, y: 500, desc: 'Lower Center'},
        {x: 200, y: 600, desc: 'Bottom Center'},
    ];
    
    for (const area of contentAreas) {
        await tap(area.x, area.y, area.desc);
    }
    
    console.log('\n📱 Step 5: Testing edge cases');
    // Test edge coordinates
    const edgeLocations = [
        {x: 50, y: 100, desc: 'Top Left Corner'},
        {x: 350, y: 100, desc: 'Top Right Corner'},
        {x: 50, y: 700, desc: 'Bottom Left'},
        {x: 350, y: 700, desc: 'Bottom Right'},
    ];
    
    for (const edge of edgeLocations) {
        await tap(edge.x, edge.y, edge.desc);
    }
    
    console.log('\n🎉 Expo Go Demo Complete!');
    console.log('📱 Check the simulator to see if any navigation occurred.');
}

if (require.main === module) {
    runExpoGoDemo();
} else {
    module.exports = runExpoGoDemo;
}
