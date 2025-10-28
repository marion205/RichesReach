const { execSync } = require('child_process');

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function runAppleScriptCommand(command) {
    try {
        execSync(`osascript -e '${command}'`);
        return true;
    } catch (error) {
        console.warn(`⚠️  AppleScript command failed: ${command}\nError: ${error.message}`);
        return false;
    }
}

async function tap(x, y, description = `Tap at (${x}, ${y})`) {
    console.log(`🎯 Tapping: ${description} at (${x}, ${y})`);
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
        console.log(`✅ Tap successful: ${description}`);
    }
    await delay(2000); // Longer delay for app to respond
}

async function swipe(startX, startY, endX, endY, description = 'Swipe') {
    console.log(`👆 Swiping: ${description}`);
    const success = await runAppleScriptCommand(`
        tell application "Simulator"
            activate
        end tell
        tell application "System Events"
            tell process "Simulator"
                set startPoint to {${startX}, ${startY}}
                set endPoint to {${endX}, ${endY}}
                drag from startPoint to endPoint
            end tell
        end tell
    `);
    if (success) {
        console.log(`✅ Swipe successful: ${description}`);
    }
    await delay(2000);
}

async function runAggressiveNavigationDemo() {
    console.log('🚀 Aggressive Navigation Demo Starting...');

    // Phase 1: Multiple attempts to bypass onboarding
    console.log('📱 Phase 1: Aggressive onboarding bypass...');
    
    // Try all possible skip/get started locations
    const skipLocations = [
        {x: 200, y: 700, desc: 'Bottom Center Skip'},
        {x: 350, y: 100, desc: 'Top Right Skip'},
        {x: 50, y: 100, desc: 'Top Left Skip'},
        {x: 200, y: 650, desc: 'Lower Center Skip'},
        {x: 300, y: 700, desc: 'Bottom Right Skip'},
        {x: 100, y: 700, desc: 'Bottom Left Skip'},
    ];
    
    for (const loc of skipLocations) {
        await tap(loc.x, loc.y, loc.desc);
        await delay(1000);
    }

    // Phase 2: Force navigation through bottom tabs
    console.log('📱 Phase 2: Force navigation through tabs...');
    
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
    
    // Navigate through each tab multiple times
    for (let round = 0; round < 3; round++) {
        console.log(`📱 Tab navigation round ${round + 1}...`);
        for (const tab of tabLocations) {
            await tap(tab.x, tab.y, tab.desc);
            await delay(1500);
        }
    }

    // Phase 3: Aggressive content interaction
    console.log('📱 Phase 3: Aggressive content interaction...');
    
    const contentAreas = [
        {x: 200, y: 200, desc: 'Top Center'},
        {x: 100, y: 300, desc: 'Top Left'},
        {x: 300, y: 300, desc: 'Top Right'},
        {x: 200, y: 400, desc: 'Center'},
        {x: 100, y: 500, desc: 'Middle Left'},
        {x: 300, y: 500, desc: 'Middle Right'},
        {x: 200, y: 600, desc: 'Lower Center'},
    ];
    
    for (const area of contentAreas) {
        await tap(area.x, area.y, area.desc);
        await delay(1000);
    }

    // Phase 4: Multiple scrolling patterns
    console.log('📱 Phase 4: Multiple scrolling patterns...');
    
    const scrollPatterns = [
        {start: {x: 200, y: 600}, end: {x: 200, y: 200}, desc: 'Vertical Down'},
        {start: {x: 200, y: 200}, end: {x: 200, y: 600}, desc: 'Vertical Up'},
        {start: {x: 100, y: 400}, end: {x: 300, y: 400}, desc: 'Horizontal Right'},
        {start: {x: 300, y: 400}, end: {x: 100, y: 400}, desc: 'Horizontal Left'},
        {start: {x: 150, y: 500}, end: {x: 250, y: 300}, desc: 'Diagonal Down-Right'},
        {start: {x: 250, y: 300}, end: {x: 150, y: 500}, desc: 'Diagonal Up-Left'},
    ];
    
    for (const pattern of scrollPatterns) {
        await swipe(pattern.start.x, pattern.start.y, pattern.end.x, pattern.end.y, pattern.desc);
        await delay(1500);
    }

    // Phase 5: Try to trigger any modals or menus
    console.log('📱 Phase 5: Triggering modals and menus...');
    
    const modalTriggers = [
        {x: 200, y: 100, desc: 'Top Center Menu'},
        {x: 50, y: 100, desc: 'Top Left Menu'},
        {x: 350, y: 100, desc: 'Top Right Menu'},
        {x: 200, y: 150, desc: 'Upper Center'},
        {x: 200, y: 750, desc: 'Bottom Center'},
        {x: 50, y: 750, desc: 'Bottom Left'},
        {x: 350, y: 750, desc: 'Bottom Right'},
    ];
    
    for (const trigger of modalTriggers) {
        await tap(trigger.x, trigger.y, trigger.desc);
        await delay(1000);
    }

    // Phase 6: Final tab cycling
    console.log('📱 Phase 6: Final tab cycling...');
    
    for (let i = 0; i < 5; i++) {
        await tap(200, 800, 'Center Tab');
        await delay(1000);
        await tap(300, 800, 'Right Tab');
        await delay(1000);
        await tap(100, 800, 'Left Tab');
        await delay(1000);
    }

    console.log('🎉 Aggressive Navigation Demo Complete!');
}

if (require.main === module) {
    runAggressiveNavigationDemo();
} else {
    module.exports = runAggressiveNavigationDemo;
}
