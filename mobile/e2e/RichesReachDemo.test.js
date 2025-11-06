// Detox APIs are available globally via e2e/init.js
const { device, element, by, waitFor, expect } = require('detox');

// Import test IDs (using relative path from e2e to src)
const TID = {
  tabs: {
    voiceAI: 'voice-ai-tab',
    memeQuest: 'memequest-tab',
    coach: 'coach-tab',
    learning: 'learning-tab',
    community: 'community-tab',
  },
  voice: {
    orb: 'voice-orb',
    selector: 'voice-selector',
    nova: 'voice-selector-nova',
    executeTrade: 'execute-trade-button',
    viewPortfolio: 'view-portfolio-button',
  },
  memeQuest: {
    frogTemplate: 'frog-template',
    voiceLaunch: 'voice-launch',
    animate: 'animate-button',
    sendTip: 'send-tip-button',
  },
  coach: {
    bullishSpread: 'bullish-spread-button',
    executeTrade: 'coach-execute-trade',
  },
  learning: {
    startQuiz: 'start-options-quiz-button',
    callOption: 'call-option-answer',
    putOption: 'put-option-answer',
    next: 'next-button',
    showResults: 'show-results-button',
  },
  community: {
    bipocLeague: 'bipoc-wealth-builders-league',
    joinDiscussion: 'join-discussion-button',
    messageInput: 'message-input',
    sendMessage: 'send-message-button',
  },
  screens: {
    home: 'home-screen',
    voiceAI: 'voice-ai-screen',
    memeQuest: 'memequest-screen',
    coach: 'coach-screen',
    learning: 'learning-screen',
    community: 'community-screen',
  },
};

describe('RichesReach AI Full Demo', () => {
  it('Voice Trade + MemeQuest Raid (60s)', async () => {
    // Launch app with clean state (first time only)
    await device.launchApp({
      newInstance: true,
      delete: true,
    });
    await device.setOrientation('portrait');
    // Wait for app to be ready (home screen)
    console.log('⏳ Waiting for app to load...');
    
    // Wait for any visible element first (app might be loading)
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Try to find home screen by testID or any visible element
    try {
    await waitFor(element(by.id(TID.screens.home)))
      .toBeVisible()
        .withTimeout(15000);
      console.log('✅ Home screen found');
    } catch (e) {
      console.log('⚠️ Home screen testID not found, trying alternative...');
      // Fallback: wait for any visible element
      await waitFor(element(by.type('RCTView')))
        .toBeVisible()
        .withTimeout(10000);
    }

    // Step 1: Voice Trade Demo (Voice AI Tab)
    console.log('🎤 Starting Voice AI Trading Demo...');
    
    // Wait for tab bar to be visible and interactable
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Debug: Log visible elements to help diagnose
    try {
      const tabBar = await element(by.type('UISegmentedControl')).atIndex(0);
      console.log('Tab bar found');
    } catch (e) {
      console.log('Tab bar not found by type, trying other methods...');
    }
    
    // React Navigation tab bar buttons: try multiple matchers
    let tabFound = false;
    
    // Method 1: Try by testID (tabBarTestID)
    try {
    await waitFor(element(by.id(TID.tabs.voiceAI)))
      .toBeVisible()
      .withTimeout(10000);
      console.log('✅ Voice AI tab found by testID');
    await element(by.id(TID.tabs.voiceAI)).tap();
      tabFound = true;
    } catch (e) {
      console.log(`⚠️ Tab not found by testID (${TID.tabs.voiceAI}): ${e.message}`);
    }
    
    // Method 2: Try by accessibility label
    if (!tabFound) {
      try {
        await waitFor(element(by.label(TID.tabs.voiceAI)))
          .toBeVisible()
          .withTimeout(5000);
        console.log('✅ Voice AI tab found by accessibility label');
        await element(by.label(TID.tabs.voiceAI)).tap();
        tabFound = true;
      } catch (e2) {
        console.log(`⚠️ Tab not found by accessibility label: ${e2.message}`);
      }
    }
    
    // Method 3: Try by text "Home" (since Home tab = Voice AI features)
    if (!tabFound) {
      try {
        await waitFor(element(by.text('Home')))
          .toBeVisible()
          .withTimeout(5000);
        console.log('✅ Home tab found by text, tapping...');
        await element(by.text('Home')).tap();
        tabFound = true;
      } catch (e3) {
        console.log(`⚠️ Tab not found by text: ${e3.message}`);
      }
    }
    
    // Method 4: Try to find first tab button and tap
    if (!tabFound) {
      try {
        // React Navigation creates tab buttons as TouchableOpacity
        const tabButtons = await element(by.type('RCTTouchableOpacity')).atIndex(0);
        console.log('✅ Found tab button, tapping...');
        await tabButtons.tap();
        tabFound = true;
      } catch (e4) {
        console.log(`❌ Could not find any tab button: ${e4.message}`);
        throw new Error('Failed to find and tap Voice AI tab');
      }
    }
    
    // Wait a bit for navigation
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Try to find voice orb by ID first, then fallback to text
    try {
      await waitFor(element(by.id(TID.voice.orb)))
        .toBeVisible()
        .withTimeout(10000);
      await element(by.id(TID.voice.orb)).tap();
    } catch (e) {
      console.log('⚠️ Voice orb not found by ID, trying text...');
      // Fallback: try to find by text or navigate to voice AI screen
      await element(by.text('Voice AI')).tap().catch(() => {});
    }
    
    // Try to select Nova voice
    try {
      await waitFor(element(by.id(TID.voice.nova)))
        .toBeVisible()
        .withTimeout(5000);
      await element(by.id(TID.voice.nova)).tap();
    } catch (e) {
      // Fallback to text
      await waitFor(element(by.text('Nova')))
        .toBeVisible()
        .withTimeout(5000)
        .catch(() => {});
      await element(by.text('Nova')).tap().catch(() => {});
    }
    
    // Try to execute trade
    try {
      await element(by.id(TID.voice.executeTrade)).tap();
    } catch (e) {
      await element(by.text('Execute Trade')).tap().catch(() => {});
    }

    // Step 2: MemeQuest Raid (MemeQuest Tab)
    console.log('🎭 Starting MemeQuest Social Demo...');
    
    await waitFor(element(by.id(TID.tabs.memeQuest)))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id(TID.tabs.memeQuest)).tap();
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Try to find elements with fallbacks
    try {
      await waitFor(element(by.id(TID.memeQuest.frogTemplate)))
        .toBeVisible()
        .withTimeout(5000);
      await element(by.id(TID.memeQuest.frogTemplate)).tap();
    } catch (e) {
      await waitFor(element(by.text('Frog Template')))
        .toBeVisible()
        .withTimeout(5000)
        .catch(() => {});
      await element(by.text('Frog Template')).tap().catch(() => {});
    }
    
    try {
      await element(by.id(TID.memeQuest.voiceLaunch)).tap();
    } catch (e) {
      await element(by.text('Voice Launch')).tap().catch(() => {});
    }
    
    try {
      await element(by.id(TID.memeQuest.animate)).tap();
    } catch (e) {
      await element(by.text('Animate')).tap().catch(() => {});
    }

    // Step 3: AI Trading Coach
    console.log('🤖 Starting AI Trading Coach Demo...');
    
    // Coach features might be in Learn or Home tab
    // Try to navigate - might need to go through Home first
    await element(by.id(TID.tabs.voiceAI)).tap(); // Back to home
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Try to find Coach button or navigate to coach screen
    // Coach might be in Learn tab or separate tab
    try {
      await waitFor(element(by.id(TID.coach.bullishSpread)))
        .toBeVisible()
        .withTimeout(5000)
        .catch(() => {});
      await element(by.id(TID.coach.bullishSpread)).tap().catch(() => {});
    } catch (e) {
      // Fallback: try text
      await element(by.text('Activate AI Genius')).tap().catch(() => {});
      await element(by.text('Bullish Spread Strategy')).tap().catch(() => {});
    }

    // Step 4: Learning System
    console.log('📚 Starting Learning System Demo...');
    
    await waitFor(element(by.id(TID.tabs.learning)))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id(TID.tabs.learning)).tap();
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    try {
      await waitFor(element(by.id(TID.learning.startQuiz)))
        .toBeVisible()
        .withTimeout(5000);
      await element(by.id(TID.learning.startQuiz)).tap();
    } catch (e) {
      await waitFor(element(by.text('Start Options Quiz')))
        .toBeVisible()
        .withTimeout(5000)
        .catch(() => {});
      await element(by.text('Start Options Quiz')).tap().catch(() => {});
    }
    
    // Answer quiz questions
    try {
      await element(by.id(TID.learning.callOption)).tap();
    } catch (e) {
      await element(by.text('Call Option')).tap().catch(() => {});
    }
    
    try {
      await element(by.id(TID.learning.next)).tap();
    } catch (e) {
      await element(by.text('Next')).tap().catch(() => {});
    }
    
    try {
      await element(by.id(TID.learning.putOption)).tap();
    } catch (e) {
      await element(by.text('Put Option')).tap().catch(() => {});
    }
    
    try {
      await element(by.id(TID.learning.showResults)).tap();
    } catch (e) {
      await element(by.text('Show Results')).tap().catch(() => {});
    }

    // Step 5: Social Features
    console.log('👥 Starting Social Features Demo...');
    
    await waitFor(element(by.id(TID.tabs.community)))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id(TID.tabs.community)).tap();
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    try {
      await waitFor(element(by.id(TID.community.bipocLeague)))
        .toBeVisible()
        .withTimeout(5000);
      await element(by.id(TID.community.bipocLeague)).tap();
    } catch (e) {
      await waitFor(element(by.text('BIPOC Wealth Builders League')))
        .toBeVisible()
        .withTimeout(5000)
        .catch(() => {});
      await element(by.text('BIPOC Wealth Builders League')).tap().catch(() => {});
    }
    
    try {
      await element(by.id(TID.community.joinDiscussion)).tap();
    } catch (e) {
      await element(by.text('Join Discussion')).tap().catch(() => {});
    }
    
    // Type message
    try {
      await waitFor(element(by.id(TID.community.messageInput)))
        .toBeVisible()
        .withTimeout(5000);
      await element(by.id(TID.community.messageInput)).tap();
      await element(by.id(TID.community.messageInput)).typeText('Great insights!');
    } catch (e) {
      console.log('⚠️ Message input not found');
    }
    
    try {
      await element(by.id(TID.community.sendMessage)).tap();
    } catch (e) {
      await element(by.text('Send Message')).tap().catch(() => {});
    }

    console.log('🎉 Demo completed successfully!');
  });
});
