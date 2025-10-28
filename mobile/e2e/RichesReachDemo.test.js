const { detox, device, element, by, waitFor, expect } = require('detox');

describe('RichesReach AI Full Demo', () => {
  beforeAll(async () => {
    await detox.init();
    await device.launchApp(); // Auto-run Expo app
  });

  afterAll(async () => {
    await detox.cleanup();
  });

  it('Voice Trade + MemeQuest Raid (60s)', async () => {
    // Step 1: Voice Trade Demo (Voice AI Tab)
    console.log('🎤 Starting Voice AI Trading Demo...');
    await element(by.text('Voice AI')).tap(); // Navigate to Voice AI tab
    await waitFor(element(by.id('voice-orb'))).toBeVisible().withTimeout(5000);
    await element(by.id('voice-orb')).tap(); // Voice prompt
    await waitFor(element(by.text('Nova'))).toBeVisible().withTimeout(2000);
    await element(by.text('Nova')).tap(); // Select Nova voice
    await element(by.text('Execute Trade')).tap(); // Sim success
    await waitFor(element(by.text('Trade Executed'))).toBeVisible().withTimeout(3000);

    // Step 2: MemeQuest Raid (MemeQuest Tab)
    console.log('🎭 Starting MemeQuest Social Demo...');
    await element(by.text('MemeQuest')).tap();
    await waitFor(element(by.text('Frog Template'))).toBeVisible().withTimeout(3000);
    await element(by.text('Frog Template')).tap();
    await element(by.id('voice-launch')).tap(); // Voice launch
    await element(by.text('Animate')).tap(); // AR hop
    await waitFor(element(by.text('Meme Mooned!'))).toBeVisible().withTimeout(3000);

    // Step 3: AI Trading Coach
    console.log('🤖 Starting AI Trading Coach Demo...');
    await element(by.text('Coach')).tap();
    await waitFor(element(by.text('Bullish Spread Strategy'))).toBeVisible().withTimeout(3000);
    await element(by.text('Bullish Spread Strategy')).tap();
    await element(by.text('Execute Trade')).tap();
    await waitFor(element(by.text('Trade Executed'))).toBeVisible().withTimeout(3000);

    // Step 4: Learning System
    console.log('📚 Starting Learning System Demo...');
    await element(by.text('Learning')).tap();
    await waitFor(element(by.text('Start Options Quiz'))).toBeVisible().withTimeout(3000);
    await element(by.text('Start Options Quiz')).tap();
    await element(by.text('Call Option')).tap(); // Answer question
    await element(by.text('Next')).tap();
    await element(by.text('Put Option')).tap(); // Answer question
    await element(by.text('Show Results')).tap();
    await waitFor(element(by.text('Quiz Complete'))).toBeVisible().withTimeout(3000);

    // Step 5: Social Features
    console.log('👥 Starting Social Features Demo...');
    await element(by.text('Community')).tap();
    await waitFor(element(by.text('BIPOC Wealth Builders League'))).toBeVisible().withTimeout(3000);
    await element(by.text('BIPOC Wealth Builders League')).tap();
    await element(by.text('Join Discussion')).tap();
    await element(by.id('message-input')).typeText('Great insights!');
    await element(by.text('Send Message')).tap();
    await waitFor(element(by.text('Message Sent'))).toBeVisible().withTimeout(3000);

    console.log('🎉 Demo completed successfully!');
  });
});
