const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const OUTPUT_VIDEO = `RichesReach_Demo_${new Date().toISOString().split('T')[0]}_${Date.now()}.mov`;
const TRIMMED_VIDEO = 'RichesReach_Demo_60s.mov';
const SIMULATOR_ID = 'iPhone 16 Pro'; // Update to your simulator

console.log('🚀 Auto-Demo Recorder Starting...');

let recordProcess = null;

(async () => {
try {
  // Step 1: Boot Simulator (if not running)
  console.log('📱 Booting iOS Simulator...');
  try {
    execSync(`xcrun simctl boot "${SIMULATOR_ID}"`, { stdio: 'inherit' });
  } catch (e) {
    console.log('⚠️ Simulator already booted or boot failed, continuing...');
  }

  // Step 2: Start Silent Recording
  console.log('🎥 Starting auto-recording...');
  const recordCmd = `xcrun simctl io booted recordVideo "${OUTPUT_VIDEO}"`;
  recordProcess = spawn('xcrun', ['simctl', 'io', 'booted', 'recordVideo', OUTPUT_VIDEO], {
    stdio: 'pipe',
    detached: true
  });

  // Wait for recording to start
  await new Promise(resolve => setTimeout(resolve, 3000));

  // Step 3: Run Detox Demo
  console.log('🤖 Running Detox demo...');
  try {
    execSync('npx detox test -c ios.sim.debug', { 
      stdio: 'inherit',
      cwd: path.join(__dirname, '..')
    });
  } catch (e) {
    console.log('⚠️ Detox test failed, running fallback demo...');
    // Fallback: Run our AppleScript demo
    execSync('node scripts/applescript-demo-recorder.js', { 
      stdio: 'inherit',
      cwd: path.join(__dirname, '..')
    });
  }

  // Step 4: Stop Recording
  console.log('⏹️ Stopping recording...');
  if (recordProcess) {
    recordProcess.kill('SIGINT');
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // Step 5: Trim to 60s (ffmpeg)
  if (fs.existsSync(OUTPUT_VIDEO)) {
    console.log('✂️ Trimming to 60s...');
    try {
      execSync(`ffmpeg -y -i "${OUTPUT_VIDEO}" -ss 0 -t 60 -c copy "${TRIMMED_VIDEO}"`, { stdio: 'inherit' });
      
      // Move to Desktop
      const desktopPath = path.join(process.env.HOME, 'Desktop');
      fs.renameSync(OUTPUT_VIDEO, path.join(desktopPath, OUTPUT_VIDEO));
      fs.renameSync(TRIMMED_VIDEO, path.join(desktopPath, TRIMMED_VIDEO));
      
      console.log(`✅ Demo saved! 🎉\n- Full: ~/Desktop/${OUTPUT_VIDEO}\n- Trimmed: ~/Desktop/${TRIMMED_VIDEO}`);
    } catch (e) {
      console.log('⚠️ ffmpeg not available, keeping original file');
      const desktopPath = path.join(process.env.HOME, 'Desktop');
      fs.renameSync(OUTPUT_VIDEO, path.join(desktopPath, OUTPUT_VIDEO));
      console.log(`✅ Demo saved! 🎉\n- Full: ~/Desktop/${OUTPUT_VIDEO}`);
    }
  } else {
    console.log('❌ Recording failed—check simulator.');
  }

} catch (error) {
  console.error('Demo failed:', error.message);
  if (recordProcess) {
    recordProcess.kill();
  }
  process.exit(1);
}
})();
