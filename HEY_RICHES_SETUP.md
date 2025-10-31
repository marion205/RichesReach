# "Hey Riches" Wake Word Setup Guide

The "Hey Riches" feature uses **Picovoice Porcupine** for wake word detection. This allows you to activate the voice assistant hands-free by saying "Hey Riches".

## ⚠️ Important: Requires Development Build

**This feature does NOT work in Expo Go**. You must use a development build.

## Setup Steps

### 1. Get a Picovoice Access Key

1. Sign up for a free account at [https://console.picovoice.ai/](https://console.picovoice.ai/)
2. Navigate to your dashboard
3. Copy your Access Key

### 2. Create Custom "Hey Riches" Keyword

1. Go to [Picovoice Console](https://console.picovoice.ai/)
2. Navigate to **Porcupine** → **Keywords**
3. Click **"Create Keyword"**
4. Enter `Hey Riches` as the keyword phrase
5. Download the keyword file (`.ppn` file)

### 3. Configure Access Key

Add your Picovoice Access Key to your environment:

**Option A: Environment Variable**
```bash
export PICOVOICE_ACCESS_KEY="your_access_key_here"
```

**Option B: In `mobile/src/services/PorcupineWakeWordService.ts`**
Replace `'YOUR_ACCESS_KEY_HERE'` with your actual key (only for development, use env vars in production)

### 4. Add Keyword File to App

1. Place your downloaded `.ppn` file in `mobile/assets/keywords/hey_riches.ppn`
2. Update `PorcupineWakeWordService.ts` to use the custom keyword:

```typescript
// Replace this line:
this.porcupineManager = await PorcupineManager.fromBuiltInKeywords(
  PICOVOICE_ACCESS_KEY,
  ['Hey Alexa'] // Fallback
);

// With this:
const keywordPath = require('../assets/keywords/hey_riches.ppn');
this.porcupineManager = await PorcupineManager.fromKeywordPaths(
  PICOVOICE_ACCESS_KEY,
  [keywordPath]
);
```

### 5. Initialize in Your App

The service is already set up. To use it:

```typescript
import { porcupineWakeWordService } from './services/PorcupineWakeWordService';

// Start listening for "Hey Riches"
await porcupineWakeWordService.start();

// Stop listening
await porcupineWakeWordService.stop();

// Check status
const status = porcupineWakeWordService.getStatus();
console.log('Wake word service:', status);
```

### 6. Build Development Client

Since this requires native modules, rebuild your development client:

```bash
cd mobile
npx expo run:ios
# or
npx expo run:android
```

## How It Works

1. The service listens continuously in the background
2. When you say "Hey Riches", Porcupine detects it
3. It triggers the `hotword` event via `VoiceHotword.ts`
4. Your app responds (e.g., opens voice assistant)

## Testing

1. Make sure you're using a development build (not Expo Go)
2. Grant microphone permissions when prompted
3. Say "Hey Riches" clearly
4. Check console logs for detection confirmation

## Troubleshooting

### "Wake word detection not working"
- ✅ Verify you're using a development build (not Expo Go)
- ✅ Check microphone permissions are granted
- ✅ Verify PICOVOICE_ACCESS_KEY is set correctly
- ✅ Check console logs for error messages

### "Access key invalid"
- ✅ Sign up at console.picovoice.ai and get a new key
- ✅ Make sure you're using the correct key format

### "Keyword not detected"
- ✅ Make sure you've created the "Hey Riches" keyword in Picovoice Console
- ✅ Verify the keyword file is in the correct location
- ✅ Speak clearly and wait 1-2 seconds after saying "Hey Riches"

## Alternative: Manual Testing

For testing without Porcupine, you can manually trigger the hotword:

```typescript
import { triggerHotword } from './services/VoiceHotword';

// Manually trigger (for testing)
triggerHotword();
```

This will simulate the wake word detection without requiring Porcupine.

## Resources

- [Picovoice Console](https://console.picovoice.ai/)
- [Porcupine React Native Docs](https://github.com/Picovoice/porcupine-react-native)
- [Custom Keyword Creation Guide](https://picovoice.ai/docs/porcupine/)

