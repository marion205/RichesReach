# 🎬 Production Demo Guide - RichesReach AI

## ✅ What's Ready

All testIDs have been added to key components:
- ✅ Voice AI orb button
- ✅ MemeQuest templates (including Frog template)
- ✅ MemeQuest launch/animate buttons
- ✅ Learning quiz buttons
- ✅ Community message inputs
- ✅ AI Trading Coach strategy button
- ✅ Tab navigation
- ✅ Home screen root view

## 🚀 Run the Demo

```bash
cd mobile
./demo-detox.sh
```

This will:
1. Build the app (if needed)
2. Start iOS Simulator
3. Record screen automatically
4. Run full automated demo (60 seconds)
5. Save video to Desktop

## 📋 Demo Flow

The automated demo showcases:

1. **Voice AI Trading** (Home tab)
   - Taps voice orb
   - Selects Nova voice
   - Executes trade command

2. **MemeQuest Social Trading** (Invest tab)
   - Selects Frog template
   - Launches meme with voice
   - Animates meme

3. **AI Trading Coach** (Coach tab)
   - Activates AI Genius
   - Shows Bullish Spread strategy

4. **Learning System** (Learn tab)
   - Starts Options Quiz
   - Answers questions (Call/Put options)
   - Shows results

5. **Social Features** (Community tab)
   - Joins BIPOC Wealth Builders League
   - Types message
   - Sends message

## 🎯 Demo Highlights

- **Real interactions** - Detox actually taps buttons and types text
- **Smooth navigation** - Tests all major tabs
- **Fallback handling** - Uses text-based selectors if IDs missing
- **Production ready** - No mock data, all real features

## 🔧 Troubleshooting

### If Demo Hangs

Run with verbose logging:
```bash
DEBUG=detox* ./demo-detox.sh
```

Look for messages like:
- `by.id("voice-orb") not found` → Missing testID
- `Timeout waiting for element` → Element not visible yet

### If Simulator Doesn't Start

```bash
# Manually start simulator
open -a Simulator
xcrun simctl boot "iPhone 16 Pro"
```

### If Build Fails

```bash
cd mobile
npm install
npx expo prebuild --platform ios
cd ios
pod install
cd ..
npm run build:e2e:ios
```

## 📊 Test IDs Added

All testIDs are centralized in `src/testIDs.ts`:

- `voice-orb` - Voice recording button
- `frog-template` - MemeQuest Frog template
- `animate-button` - MemeQuest launch button
- `voice-launch` - MemeQuest voice launch
- `start-options-quiz-button` - Quiz start button
- `call-option-answer` - Quiz answer buttons
- `message-input` - Chat/message inputs
- `send-message-button` - Send buttons
- `bullish-spread-button` - AI Coach strategy button

## 🎥 Output

Demo video will be saved to:
- `~/Desktop/RichesReach_Demo_Detox_[timestamp].mov`
- `~/Desktop/RichesReach_Demo_Optimized.mp4` (if ffmpeg available)

## ✨ Production Features

- ✅ All real data (no mocks)
- ✅ Real API endpoints
- ✅ Production-grade error handling
- ✅ Smooth animations
- ✅ Professional UI

## 🎉 Ready to Show!

Your demo is production-ready. Run `./demo-detox.sh` and get a professional demo video showcasing all RichesReach AI features!

