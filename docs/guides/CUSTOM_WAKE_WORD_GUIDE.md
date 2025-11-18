# Custom "Hey Riches" Wake Word - Build From Scratch

You can build your own wake word detection **without Picovoice API**! This guide shows you how.

## 🎯 Two Approaches

### Option 1: Whisper-Based (Current Implementation)
**Uses your existing Whisper server** - simplest to implement

**Pros:**
- ✅ Uses your existing infrastructure
- ✅ No external API keys needed
- ✅ Works with your Whisper server
- ✅ Easy to customize

**Cons:**
- ⚠️ Less efficient (checks every 3 seconds)
- ⚠️ Uses more battery (continuous recording)
- ⚠️ Higher latency (~3-5 seconds)

### Option 2: Lightweight ML Model (Recommended for Production)
**Build a lightweight TensorFlow Lite model** - more efficient

**Pros:**
- ✅ Very low latency (< 500ms)
- ✅ Battery efficient
- ✅ Works offline
- ✅ Continuous listening

**Cons:**
- ⚠️ Requires model training
- ⚠️ More complex setup

---

## 🚀 Option 1: Whisper-Based Implementation

Already implemented in `CustomWakeWordService.ts`!

### How It Works:
1. Continuously records audio in 3-second chunks
2. Sends each chunk to your Whisper server for transcription
3. Checks transcript for "Hey Riches"
4. Triggers voice assistant when detected

### Setup:

```typescript
import { customWakeWordService } from './services/CustomWakeWordService';

// Start listening
await customWakeWordService.start();

// Check status
const status = customWakeWordService.getStatus();
console.log('Wake word service:', status);

// Stop listening
await customWakeWordService.stop();
```

### Configuration:
- `CHECK_INTERVAL`: How often to check (default: 3000ms)
- `WAKE_WORD`: The phrase to detect (default: "hey riches")
- `WHISPER_API_URL`: Your Whisper server URL

---

## 🧠 Option 2: Lightweight ML Model (Advanced)

Build a custom wake word detector using TensorFlow Lite.

### Step 1: Collect Training Data

1. Record multiple variations of "Hey Riches":
   - Different voices
   - Different accents
   - Different speeds
   - With background noise

2. Collect negative samples:
   - Random speech
   - Other phrases
   - Silence/noise

### Step 2: Train Model

Use a library like `tensorflow.js` or train a Python model and convert to TensorFlow Lite:

```python
# train_wake_word_model.py
import tensorflow as tf
from tensorflow import keras
import numpy as np

# Load audio data (convert to MFCC features)
# ... your training code ...

# Convert to TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
with open('hey_riches_model.tflite', 'wb') as f:
    f.write(tflite_model)
```

### Step 3: Use in React Native

Install TensorFlow Lite:
```bash
npm install @tensorflow/tfjs-react-native
```

Implement detection:
```typescript
import * as tf from '@tensorflow/tfjs';
import '@tensorflow/tfjs-react-native';

// Load model
const model = await tf.loadLayersModel('/path/to/hey_riches_model.tflite');

// Process audio chunks
const features = extractMFCC(audioBuffer);
const prediction = model.predict(features);

if (prediction > THRESHOLD) {
  triggerHotword();
}
```

---

## 🔄 Hybrid Approach (Best of Both)

Combine both methods:

1. **Use lightweight model** for initial detection (fast, battery-efficient)
2. **Verify with Whisper** when model detects (accurate, handles variations)

```typescript
// Pseudo-code
if (lightweightModel.detect(audioChunk)) {
  const transcript = await whisper.transcribe(audioChunk);
  if (transcript.includes('hey riches')) {
    triggerHotword(); // Confirmed!
  }
}
```

---

## 📊 Comparison

| Feature | Picovoice | Whisper-Based | ML Model |
|---------|-----------|--------------|----------|
| Latency | < 500ms | 3-5 seconds | < 500ms |
| Battery | Excellent | Good | Excellent |
| Accuracy | High | High | Medium-High |
| Setup Complexity | Easy | Easy | Medium |
| Cost | Free tier | Free (your server) | Free |
| Offline | Yes | No | Yes |
| Customizable | Limited | Full | Full |

---

## 🎯 Recommendation

For **development/testing**: Use Whisper-based (already implemented)
For **production**: Build ML model or use hybrid approach

---

## 📝 Quick Start (Whisper-Based)

1. Make sure your Whisper server is running:
   ```bash
   # Check whisper-server is accessible
   curl http://localhost:3001/health
   ```

2. Use the custom service:
   ```typescript
   import { customWakeWordService } from './services/CustomWakeWordService';
   
   // In your app initialization
   await customWakeWordService.start();
   ```

3. Say "Hey Riches" and it should detect!

---

## 🛠️ Customization

### Change Wake Word:
Edit `WAKE_WORD` in `CustomWakeWordService.ts`

### Adjust Sensitivity:
- Increase `CHECK_INTERVAL` for less battery usage (slower detection)
- Decrease for faster detection (more battery)

### Add Variations:
Edit the `variations` array in `detectWakeWord()` method

---

## 💡 Tips

1. **For better accuracy**: Collect more training data with variations
2. **For better battery**: Use ML model approach
3. **For faster setup**: Stick with Whisper-based
4. **For production**: Consider hybrid approach

---

## 🚀 Next Steps

1. ✅ Try Whisper-based (already implemented)
2. 🔄 Collect voice samples for ML model
3. 📊 Train model with your data
4. 🎯 Deploy hybrid approach for best results

