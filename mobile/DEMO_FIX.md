# 🎬 Demo Recording Fix

## Problem
The AppleScript-based automation uses coordinate-based tapping which doesn't actually interact with the app. The script reports success but nothing happens in the video.

## Solutions

### Option 1: Use Detox (Recommended - Actually Works!)
Detox uses element-based interactions (finding buttons by text/ID) which actually works.

**Setup:**
```bash
cd mobile
npm install --save-dev detox
npm run build:e2e:ios
```

**Run:**
```bash
./demo-detox.sh
```

**Pros:**
- ✅ Actually interacts with the app
- ✅ Uses element selectors (not coordinates)
- ✅ Reliable and repeatable
- ✅ Can record videos automatically

**Cons:**
- ⚠️ Requires app to be built first
- ⚠️ Needs test IDs in your app components

### Option 2: Manual Recording (Simplest - Always Works!)
Record manually while following a script.

**Run:**
```bash
./demo-manual.sh
```

This will:
1. Start the simulator
2. Start your app
3. Start screen recording
4. Show you a checklist to follow
5. Save video when you press Ctrl+C

**Pros:**
- ✅ Always works
- ✅ No setup needed
- ✅ You control the flow
- ✅ Can react to app state

**Cons:**
- ⚠️ Requires manual interaction
- ⚠️ Takes 2-3 minutes

### Option 3: Fix AppleScript (More Complex)
The current AppleScript uses `click at {x, y}` which doesn't work reliably. We'd need to:
1. Use accessibility identifiers
2. Find elements by accessibility tree
3. Use proper UI automation

**Better approach:** Use Detox instead (Option 1)

## Quick Fix: Use Manual Recording

The fastest solution right now:

```bash
cd mobile
./demo-manual.sh
```

Then follow the on-screen checklist. The video will be saved to your Desktop when you're done.

## Why AppleScript Failed

The AppleScript automation uses:
```applescript
click at {196, 800}  // Hardcoded coordinates
```

This doesn't work because:
1. Coordinates are absolute screen positions
2. Simulator window size can vary
3. App layout can change
4. Doesn't actually interact with React Native elements

Detox uses:
```javascript
await element(by.text('Voice AI')).tap();  // Finds element by text
```

This works because:
1. Finds actual UI elements
2. Works regardless of position
3. Waits for elements to appear
4. Actually interacts with React Native

## Next Steps

1. **For immediate use:** Run `./demo-manual.sh` and record manually
2. **For automation:** Set up Detox properly (see Option 1)
3. **For production:** Consider commercial tools like Loom or Camtasia

## Adding Test IDs for Detox

To make Detox work better, add `testID` props to your components:

```tsx
<TouchableOpacity testID="voice-ai-tab">
  <Text>Voice AI</Text>
</TouchableOpacity>

<Button testID="voice-orb" onPress={...}>
  ...
</Button>
```

Then Detox can find them reliably:
```javascript
await element(by.id('voice-ai-tab')).tap();
```

