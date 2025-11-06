# 🚀 Quick Start: Detox Demo

## ✅ What's Already Done

1. ✅ Test IDs created (`src/testIDs.ts`)
2. ✅ Tab navigation testIDs added (`AppNavigator.tsx`)
3. ✅ HomeScreen root testID added
4. ✅ Test file updated with fallbacks and better error handling

## 🎬 Run the Demo

```bash
cd mobile
./demo-detox.sh
```

This will:
- Build the app (if needed)
- Start simulator
- Record screen
- Run automated demo
- Save video to Desktop

## 🔍 If It Still Hangs

### 1. Check What's Missing

Run with verbose logging:

```bash
DEBUG=detox* ./demo-detox.sh
```

Look for error messages like:
- `by.id("voice-orb") not found`
- `Timeout waiting for element`

### 2. Add Missing testIDs

The test has **text-based fallbacks**, so it will try to find elements by text if IDs aren't found. But adding testIDs makes it more reliable.

**Common missing testIDs:**
- `voice-orb` - Voice recording button
- `message-input` - Chat text input
- `execute-trade-button` - Trade execution button

### 3. Quick Test Individual Features

Test just the tabs first:

```bash
cd mobile
npm run test:e2e:ios -- e2e/RichesReachDemo.test.js --testNamePattern="Voice Trade"
```

## 📋 Current Status

**Working:**
- ✅ Tab navigation (testIDs added)
- ✅ Home screen detection
- ✅ Test with fallbacks

**May Need:**
- ⏳ Component-level testIDs (voice orb, buttons, inputs)
- ⏳ Screen-specific testIDs

## 💡 Pro Tips

1. **Tabs work first** - The tab testIDs are already added, so navigation should work
2. **Fallbacks help** - Test will try text selectors if IDs aren't found
3. **Incremental** - Add testIDs as you find missing ones
4. **Check logs** - Detox logs are very helpful

## 🎯 Next: Add Component testIDs

As you find missing elements, add testIDs like:

```tsx
<TouchableOpacity testID={TID.voice.orb} onPress={...}>
  <Icon name="mic" />
</TouchableOpacity>
```

The test file already references these IDs, so once you add them, it will work!

---

**Ready? Run `./demo-detox.sh` and let's see what happens!** 🎬

