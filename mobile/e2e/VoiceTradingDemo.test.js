const { detox, device, element, by, waitFor, expect } = require('detox');

describe('RichesReach Voice AI Trading Demo', () => {
  beforeAll(async () => {
    await detox.init();
  });

  afterAll(async () => {
    await detox.cleanup();
  });

  it('Voice Trading Demo - Complete Flow', async () => {
    await device.reloadReactNative();

    // Step 1: Navigate to Voice AI Assistant
    await element(by.id('voice-ai-tab')).tap();
    await expect(element(by.text('Voice AI Assistant'))).toBeVisible();

    // Step 2: Select Voice (Nova)
    await element(by.text('Nova')).tap();
    await expect(element(by.id('voice-orb'))).toBeVisible();

    // Step 3: Voice Command Simulation
    await element(by.id('voice-orb')).tap();
    await waitFor(element(by.text('Listening...'))).toBeVisible().withTimeout(2000);
    
    // Simulate voice command: "Buy 100 AAPL at limit $150"
    await element(by.text('Buy 100 AAPL')).tap();
    await expect(element(by.text('Confidence: 95%'))).toBeVisible();

    // Step 4: Confirm Trade
    await element(by.text('Execute Trade')).tap();
    await expect(element(by.text('Trade Executed!'))).toBeVisible();

    // Step 5: Show Portfolio Update
    await element(by.text('View Portfolio')).tap();
    await expect(element(by.text('Portfolio Value'))).toBeVisible();
  });

  it('MemeQuest Social Trading Demo', async () => {
    await device.reloadReactNative();

    // Step 1: Navigate to MemeQuest
    await element(by.id('memequest-tab')).tap();
    await expect(element(by.text('MemeQuest Raid!'))).toBeVisible();

    // Step 2: Pick Template (Frog)
    await element(by.text('Frog')).tap();
    await expect(element(by.text('AR Preview'))).toBeVisible();

    // Step 3: Voice Launch Command
    await element(by.id('voice-orb')).tap();
    await waitFor(element(by.text('Listening...'))).toBeVisible().withTimeout(2000);
    await element(by.text('Launch Meme!')).tap();

    // Step 4: AR Preview & Confetti
    await expect(element(by.id('ar-camera'))).toBeVisible();
    await element(by.text('Animate!')).tap();
    await element(by.text('Send Tip!')).tap();
    await waitFor(element(by.id('confetti-cannon'))).toExist().withTimeout(3000);

    // Step 5: Success & Streak Update
    await expect(element(by.text('Meme Mooned!'))).toBeVisible();
    await expect(element(by.text('Streak: 8 Days'))).toBeVisible();
  });

  it('AI Trading Coach Demo', async () => {
    await device.reloadReactNative();

    // Step 1: Navigate to AI Coach
    await element(by.id('coach-tab')).tap();
    await expect(element(by.text('AI Trading Coach'))).toBeVisible();

    // Step 2: Risk Slider Interaction
    await element(by.id('risk-slider')).swipe('right', 'fast', 0.8);
    await expect(element(by.text('Risk Level: High'))).toBeVisible();

    // Step 3: Strategy Selection
    await element(by.text('Bullish Spread')).tap();
    await expect(element(by.text('Strategy Selected'))).toBeVisible();

    // Step 4: Haptic Feedback Test
    await element(by.id('execute-button')).tap();
    await expect(element(by.text('Trade Executed'))).toBeVisible();
  });

  it('Learning System Demo', async () => {
    await device.reloadReactNative();

    // Step 1: Navigate to Learning
    await element(by.id('learning-tab')).tap();
    await expect(element(by.text('Learning Dashboard'))).toBeVisible();

    // Step 2: Start Quiz
    await element(by.text('Options Quiz')).tap();
    await expect(element(by.text('Question 1 of 5'))).toBeVisible();

    // Step 3: Answer Questions
    await element(by.text('Call Option')).tap();
    await element(by.text('Next')).tap();
    
    await element(by.text('Put Option')).tap();
    await element(by.text('Next')).tap();

    // Step 4: Show Results & XP
    await expect(element(by.text('Quiz Complete!'))).toBeVisible();
    await expect(element(by.text('+50 XP'))).toBeVisible();
    await expect(element(by.text('Level Up!'))).toBeVisible();
  });
});
