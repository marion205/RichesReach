# 🎬 Detox Setup Guide for Automated Demos

## Quick Start

```bash
cd mobile
./demo-detox.sh
```

That's it! The script will:
1. Install Detox if needed
2. Prebuild iOS app if needed
3. Build the app for testing
4. Start simulator
5. Record screen
6. Run automated demo
7. Save video to Desktop

## Prerequisites

1. **Xcode** installed and updated
2. **Node.js** (v14+)
3. **Expo CLI** (for prebuild)

## What Detox Does

Detox uses **element-based interactions** (not coordinates) which actually work:

```javascript
// ❌ AppleScript (doesn't work)
click at {196, 800}

// ✅ Detox (actually works)
await element(by.text('Voice AI')).tap();
await element(by.id('voice-orb')).tap();
```

## Adding Test IDs to Your Components

For Detox to find elements reliably, add `testID` props:

### Example: Tab Navigation

```tsx
// Before
<TouchableOpacity onPress={() => navigate('VoiceAI')}>
  <Text>Voice AI</Text>
</TouchableOpacity>

// After (with testID)
<TouchableOpacity 
  testID="voice-ai-tab"
  onPress={() => navigate('VoiceAI')}
>
  <Text>Voice AI</Text>
</TouchableOpacity>
```

### Example: Buttons

```tsx
<Button 
  testID="voice-orb"
  onPress={handleVoiceCommand}
>
  <Icon name="mic" />
</Button>
```

### Example: Text Inputs

```tsx
<TextInput
  testID="message-input"
  value={message}
  onChangeText={setMessage}
  placeholder="Type a message..."
/>
```

## Test Selectors

Detox can find elements by:

1. **Text** (easiest, but breaks if text changes):
   ```javascript
   await element(by.text('Voice AI')).tap();
   ```

2. **Test ID** (most reliable):
   ```javascript
   await element(by.id('voice-ai-tab')).tap();
   ```

3. **Label** (for accessibility):
   ```javascript
   await element(by.label('Voice AI Tab')).tap();
   ```

4. **Type** (for specific component types):
   ```javascript
   await element(by.type('RCTButton')).tap();
   ```

## Common Test IDs to Add

Based on your demo flow, add these testIDs:

### Voice AI Tab
- `voice-ai-tab`
- `voice-orb`
- `voice-selector-nova`
- `execute-trade-button`
- `view-portfolio-button`

### MemeQuest Tab
- `memequest-tab`
- `frog-template`
- `voice-launch-button`
- `animate-button`
- `send-tip-button`

### Coach Tab
- `coach-tab`
- `bullish-spread-strategy`
- `execute-trade-button`

### Learning Tab
- `learning-tab`
- `start-options-quiz-button`
- `call-option-answer`
- `put-option-answer`
- `next-button`
- `show-results-button`

### Community Tab
- `community-tab`
- `bipoc-wealth-builders-league`
- `join-discussion-button`
- `message-input`
- `send-message-button`

## Troubleshooting

### Build Fails

```bash
# Clean and rebuild
cd ios
rm -rf build
cd ..
npx expo prebuild --clean
npm run build:e2e:ios
```

### Simulator Not Found

```bash
# List available simulators
xcrun simctl list devices

# Boot specific simulator
xcrun simctl boot "iPhone 16 Pro"
```

### Detox Can't Find Elements

1. Check if `testID` is set correctly
2. Use `element(by.id('test-id'))` instead of `by.text()`
3. Add delays: `await waitFor(element(...)).toBeVisible().withTimeout(5000)`
4. Check if element is actually visible (not hidden by other views)

### Test Times Out

Increase timeouts:
```javascript
await waitFor(element(by.id('voice-orb')))
  .toBeVisible()
  .withTimeout(10000); // 10 seconds
```

## Manual Test Recording

If Detox isn't working, use manual recording:

```bash
./demo-manual.sh
```

## Advanced: Custom Demo Flows

Edit `e2e/RichesReachDemo.test.js` to customize the demo:

```javascript
it('Custom Demo Flow', async () => {
  // Your custom flow here
  await element(by.id('custom-button')).tap();
  await waitFor(element(by.text('Success'))).toBeVisible();
});
```

## Video Output

The demo creates two videos:
1. **Full video**: `RichesReach_Demo_Detox_[timestamp].mov` (all interactions)
2. **Optimized**: `RichesReach_Demo_Optimized.mp4` (60s, 1080x1920)

Both are saved to your Desktop.

## Next Steps

1. Add `testID` props to your components
2. Run `./demo-detox.sh`
3. Review the video
4. Adjust test file if needed
5. Re-run until perfect!

---

**Need help?** Check the test file at `e2e/RichesReachDemo.test.js` for examples.

