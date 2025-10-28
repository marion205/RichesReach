const { detox, device, element, by, waitFor, expect } = require('detox');

describe('RichesReach Social Features Demo', () => {
  beforeAll(async () => {
    await detox.init();
  });

  afterAll(async () => {
    await detox.cleanup();
  });

  it('Wealth Circles Community Demo', async () => {
    await device.reloadReactNative();

    // Step 1: Navigate to Wealth Circles
    await element(by.id('community-tab')).tap();
    await expect(element(by.text('Wealth Circles'))).toBeVisible();

    // Step 2: Join BIPOC Wealth Builders League
    await element(by.text('BIPOC Wealth Builders')).tap();
    await expect(element(by.text('League Details'))).toBeVisible();

    // Step 3: Participate in Discussion
    await element(by.text('Join Discussion')).tap();
    await element(by.id('message-input')).typeText('Great insights on options strategies!');
    await element(by.text('Send')).tap();

    // Step 4: Show Community Engagement
    await expect(element(by.text('Message Sent'))).toBeVisible();
    await expect(element(by.text('Community Points: +10'))).toBeVisible();
  });

  it('Social Trading Copy Demo', async () => {
    await device.reloadReactNative();

    // Step 1: Navigate to Social Trading
    await element(by.id('social-trading-tab')).tap();
    await expect(element(by.text('Social Trading'))).toBeVisible();

    // Step 2: Browse Top Traders
    await element(by.text('Top Traders')).tap();
    await expect(element(by.text('Trader Leaderboard'))).toBeVisible();

    // Step 3: Copy Trade
    await element(by.text('Copy Trade')).tap();
    await expect(element(by.text('Trade Copied'))).toBeVisible();

    // Step 4: Show Performance
    await element(by.text('View Performance')).tap();
    await expect(element(by.text('P&L: +$250'))).toBeVisible();
  });

  it('News Feed & Market Commentary Demo', async () => {
    await device.reloadReactNative();

    // Step 1: Navigate to News Feed
    await element(by.id('news-tab')).tap();
    await expect(element(by.text('Market News'))).toBeVisible();

    // Step 2: Filter by Category
    await element(by.text('Crypto')).tap();
    await expect(element(by.text('Crypto News'))).toBeVisible();

    // Step 3: Read Article
    await element(by.text('Bitcoin Surges')).tap();
    await expect(element(by.text('Article Content'))).toBeVisible();

    // Step 4: Share & React
    await element(by.text('Share')).tap();
    await element(by.text('Like')).tap();
    await expect(element(by.text('Shared Successfully'))).toBeVisible();
  });
});
