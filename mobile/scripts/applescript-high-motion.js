const { execSync } = require('child_process');

function runOSA(script) {
  execSync(`osascript -e '${script.replace(/'/g, "'\\''")}'`, { stdio: 'ignore' });
}

function tap(x, y, label) {
  console.log(`🎯 Tapping: ${label} at (${x}, ${y})`);
  runOSA(`
    tell application "Simulator" to activate
    tell application "System Events"
      tell process "Simulator"
        click at {${x}, ${y}}
      end tell
    end tell
  `);
}

function typeText(text) {
  console.log(`⌨️  Typing: ${text}`);
  runOSA(`
    tell application "Simulator" to activate
    tell application "System Events"
      keystroke "${text.replace(/"/g, '\\"')}"
    end tell
  `);
}

function pause(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

console.log('🚀 High-Motion AppleScript Demo Starting...');

// Assumes iPhone-sized coordinates in portrait. Adjust if needed.
// Tab bar sweeps
['Voice','MemeQuest','Coach','Learn','Community'].forEach((name, i) => {
  tap(100 + i*98, 800, `${name} Tab`);
  pause(700);
});

// Scroll content up/down a few times
for (let i = 0; i < 3; i++) {
  tap(196, 600, 'Scroll Down seed');
  pause(300);
  tap(196, 500, 'Scroll Down seed');
  pause(300);
  tap(196, 400, 'Scroll Up seed');
  pause(300);
}

// Open a modal-like area and close
tap(196, 500, 'Open Card/Modal');
pause(700);
tap(340, 160, 'Close (X)');
pause(500);

// Navigate through tabs again with actions
// Voice AI
tap(100, 800, 'Voice AI Tab');
pause(500);
tap(100, 400, 'Select Nova');
pause(400);
tap(196, 400, 'Voice Orb');
pause(600);
tap(196, 500, 'Execute');
pause(500);

// MemeQuest
tap(198, 800, 'MemeQuest Tab');
pause(400);
tap(150, 400, 'Frog Template');
pause(400);
tap(196, 500, 'Voice Launch');
pause(400);
tap(196, 600, 'Animate');
pause(400);

// Coach
tap(296, 800, 'Coach Tab');
pause(400);
tap(196, 500, 'Bullish Strategy');
pause(400);

// Learning
tap(394, 800, 'Learning Tab');
pause(400);
tap(196, 400, 'Start Quiz');
pause(400);
tap(196, 500, 'Answer 1');
pause(300);
tap(196, 600, 'Next');
pause(300);
tap(196, 500, 'Answer 2');
pause(300);

// Community
tap(492, 800, 'Community Tab');
pause(400);
tap(196, 400, 'League');
pause(400);
tap(196, 500, 'Join Discussion');
pause(400);
typeText('Great insights!');
pause(300);
tap(196, 600, 'Send Message');
pause(400);

console.log('🎉 High-Motion AppleScript Demo Complete!');
