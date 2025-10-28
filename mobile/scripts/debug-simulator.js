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

async function tap(x, y, description = `Tap at (${x}, ${y})`) {
    console.log(`\n🎯 ${description}`);
    console.log(`📍 Coordinates: (${x}, ${y})`);
    
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
    
    await delay(3000); // Longer delay to see what happens
}

async function debugSimulator() {
    console.log('🔍 Debugging Simulator Interaction...');
    
    // First, let's make sure simulator is active
    console.log('\n📱 Step 1: Activating Simulator');
    await runAppleScriptCommand('tell application "Simulator" to activate');
    await delay(2000);
    
    // Test basic tap in center
    console.log('\n📱 Step 2: Testing center tap');
    await tap(200, 400, 'Center Screen Tap');
    
    // Test bottom tab area
    console.log('\n📱 Step 3: Testing bottom tab area');
    await tap(200, 800, 'Bottom Tab Area');
    
    // Test different coordinates
    console.log('\n📱 Step 4: Testing various coordinates');
    await tap(100, 100, 'Top Left');
    await tap(300, 100, 'Top Right');
    await tap(100, 600, 'Bottom Left');
    await tap(300, 600, 'Bottom Right');
    
    // Test onboarding skip areas
    console.log('\n📱 Step 5: Testing onboarding skip areas');
    await tap(200, 700, 'Bottom Center Skip');
    await tap(350, 100, 'Top Right Skip');
    await tap(200, 650, 'Lower Center Skip');
    
    console.log('\n🎉 Debug complete! Check simulator for any changes.');
}

if (require.main === module) {
    debugSimulator();
} else {
    module.exports = debugSimulator;
}
