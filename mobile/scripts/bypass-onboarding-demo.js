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
    await delay(1500); // Longer delay for app to respond
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
    await delay(1500);
}

async function typeText(text, description = 'Typing') {
    console.log(`⌨️  Typing: ${description} - '${text}'`);
    const success = await runAppleScriptCommand(`
        tell application "Simulator"
            activate
        end tell
        tell application "System Events"
            tell process "Simulator"
                keystroke "${text}"
            end tell
        end tell
    `);
    if (success) {
        console.log(`✅ Type successful: ${description}`);
    }
    await delay(1500);
}

async function runBypassOnboardingDemo() {
    console.log('🚀 Bypass Onboarding Demo Starting...');

    // Step 1: Skip/Get Started on onboarding
    console.log('📱 Step 1: Bypassing onboarding screen...');
    await tap(200, 700, 'Get Started / Skip Button'); // Bottom center area
    await delay(2000);
    
    // Try alternative skip locations
    await tap(350, 100, 'Skip Button (top right)');
    await delay(2000);
    
    // Step 2: Navigate to main app features
    console.log('📱 Step 2: Navigating to main app features...');
    
    // Tap on different bottom tabs to show navigation
    await tap(50, 800, 'Home Tab');
    await delay(2000);
    
    await tap(100, 800, 'Stocks Tab');
    await delay(2000);
    
    await tap(150, 800, 'Crypto Tab');
    await delay(2000);
    
    await tap(200, 800, 'AI Portfolio Tab');
    await delay(2000);
    
    await tap(250, 800, 'Tutor Tab');
    await delay(2000);
    
    await tap(300, 800, 'Trading Tab');
    await delay(2000);
    
    await tap(350, 800, 'Portfolio Tab');
    await delay(2000);
    
    await tap(400, 800, 'Discuss Tab');
    await delay(2000);

    // Step 3: Try to interact with content areas
    console.log('📱 Step 3: Interacting with content areas...');
    
    // Tap in center areas to trigger interactions
    await tap(200, 400, 'Center Content Area');
    await delay(1500);
    
    await tap(200, 500, 'Main Content Area');
    await delay(1500);
    
    await tap(200, 600, 'Lower Content Area');
    await delay(1500);

    // Step 4: Try scrolling to show movement
    console.log('📱 Step 4: Scrolling to show movement...');
    
    // Scroll down
    await swipe(200, 600, 200, 300, 'Scroll Down');
    await delay(1500);
    
    // Scroll up
    await swipe(200, 300, 200, 600, 'Scroll Up');
    await delay(1500);
    
    // Scroll down again
    await swipe(200, 600, 200, 300, 'Scroll Down Again');
    await delay(1500);

    // Step 5: Try tapping on specific feature areas
    console.log('📱 Step 5: Tapping feature areas...');
    
    // Try different areas where features might be
    await tap(100, 300, 'Top Left Feature');
    await delay(1500);
    
    await tap(300, 300, 'Top Right Feature');
    await delay(1500);
    
    await tap(100, 500, 'Middle Left Feature');
    await delay(1500);
    
    await tap(300, 500, 'Middle Right Feature');
    await delay(1500);

    // Step 6: Try opening menus or modals
    console.log('📱 Step 6: Trying to open menus...');
    
    // Tap top areas for potential menus
    await tap(200, 100, 'Top Center (Menu)');
    await delay(1500);
    
    await tap(50, 100, 'Top Left (Menu)');
    await delay(1500);
    
    await tap(350, 100, 'Top Right (Menu)');
    await delay(1500);

    console.log('🎉 Bypass Onboarding Demo Complete!');
}

if (require.main === module) {
    runBypassOnboardingDemo();
} else {
    module.exports = runBypassOnboardingDemo;
}
