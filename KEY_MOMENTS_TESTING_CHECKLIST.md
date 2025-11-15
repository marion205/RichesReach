# Key Moments Feature - Complete Testing Checklist

## ✅ What's Working
- Story Mode is visible and playing
- Mock data is displaying (3 moments)

## 🧪 Testing Checklist

### 1. Chart Interaction & Visual Feedback
- [ ] **Drag on Chart**: Move finger across the chart
  - [ ] Chart highlights moments as you drag over them
  - [ ] Active moment dot becomes larger/highlighted
  - [ ] Moment info appears (title, summary) when dragging near a dot
  
- [ ] **Haptic Feedback**: 
  - [ ] Feel subtle vibration when passing over moment dots
  - [ ] Haptic feedback feels responsive (not too strong/weak)

### 2. Story Mode - Button Trigger (Full Experience)
- [ ] **Tap "▶ Play Story" Button**:
  - [ ] Story player modal opens
  - [ ] Intro slide appears first (if enabled)
  - [ ] Intro text: "Here's the story behind [SYMBOL]'s recent moves..."
  - [ ] Story auto-plays through moments
  - [ ] Voice narration plays (if TTS available)
  - [ ] Chart updates to show active moment as story progresses

### 3. Story Mode - Long-Press Gesture (Quick Start)
- [ ] **Long-Press on Moment Dot** (hold for ~500ms):
  - [ ] Story Mode opens immediately
  - [ ] **No intro slide** (skips intro)
  - [ ] Starts from that specific moment
  - [ ] Voice narration begins from that moment
  - [ ] Chart highlights the selected moment

### 4. Story Player Controls
- [ ] **Play/Pause Button**:
  - [ ] Pauses narration when pressed
  - [ ] Resumes from same position when pressed again
  - [ ] Button icon changes (play ↔ pause)
  
- [ ] **Next Button** (→):
  - [ ] Advances to next moment
  - [ ] Voice narration continues
  - [ ] Chart updates to show new moment
  - [ ] Progress indicator updates
  
- [ ] **Previous Button** (←):
  - [ ] Goes back to previous moment
  - [ ] Voice narration continues
  - [ ] Chart updates to show previous moment
  - [ ] Progress indicator updates

- [ ] **Close Button** (X):
  - [ ] Closes story player
  - [ ] Stops voice narration
  - [ ] Returns to chart view
  - [ ] Analytics event fires (check console)

### 5. Progress & Analytics
- [ ] **Progress Indicator**:
  - [ ] Shows "X/Y moments" or progress bar
  - [ ] Updates as moments are listened to
  - [ ] Shows which moments have been listened to
  
- [ ] **Analytics Tracking** (Check Console):
  - [ ] `[MomentAnalytics]` logs appear
  - [ ] `moment_listened` events fire when moments play
  - [ ] `story_close` event fires with:
    - `listenedCount`: Number of moments listened to
    - `totalMoments`: Total moments available
    - `symbol`: Stock symbol
  - [ ] Example log: "User listened to 3/5 moments for AAPL"

### 6. Voice Narration (TTS)
- [ ] **Wealth Oracle Voice**:
  - [ ] Voice plays when story starts
  - [ ] Voice stops when paused
  - [ ] Voice continues when resuming
  - [ ] Voice stops when closing story
  - [ ] If TTS service unavailable, falls back to `expo-speech`
  
- [ ] **Voice Quality**:
  - [ ] Clear pronunciation
  - [ ] Appropriate speed (not too fast/slow)
  - [ ] No audio glitches or interruptions

### 7. Visual Elements
- [ ] **Moment Dots on Chart**:
  - [ ] Dots appear at correct timestamps
  - [ ] Dots are visible and not too small/large
  - [ ] Active dot is highlighted differently
  - [ ] Dots are positioned correctly on price line

- [ ] **Story Player UI**:
  - [ ] Modal/overlay appears correctly
  - [ ] Current moment card displays:
    - Title
    - Quick summary
    - Category badge/icon
  - [ ] Controls are accessible and visible
  - [ ] Progress indicator is clear

### 8. Edge Cases & Error Handling
- [ ] **No Chart Data**:
  - [ ] Component doesn't crash
  - [ ] Shows appropriate message or hides gracefully
  
- [ ] **No Moments**:
  - [ ] Component doesn't render (returns null)
  - [ ] No errors in console
  
- [ ] **GraphQL Error**:
  - [ ] Falls back to mock data
  - [ ] Error logged but doesn't break UI
  - [ ] Mock moments still appear

- [ ] **Network Issues**:
  - [ ] Timeout after 3 seconds shows mock data
  - [ ] No infinite loading state

### 9. Performance
- [ ] **Smooth Animations**:
  - [ ] Chart interactions are smooth (no lag)
  - [ ] Story player transitions are smooth
  - [ ] No janky scrolling or rendering
  
- [ ] **Memory**:
  - [ ] No memory leaks (check with React DevTools)
  - [ ] Audio stops properly when component unmounts

### 10. Integration Points
- [ ] **Chart Tab**:
  - [ ] Feature appears in Chart tab
  - [ ] Scrolls correctly with chart
  - [ ] Doesn't interfere with chart interactions
  
- [ ] **Multiple Stocks**:
  - [ ] Test with different stocks (AAPL, TSLA, MSFT)
  - [ ] Moments are stock-specific
  - [ ] Story text includes correct symbol

## 🎯 Priority Testing Order

1. **High Priority** (Core Functionality):
   - Story Mode opens from button ✅ (You've seen this)
   - Long-press gesture works
   - Play/pause controls work
   - Voice narration plays

2. **Medium Priority** (User Experience):
   - Chart interaction (drag to explore)
   - Haptic feedback
   - Progress tracking
   - Next/previous navigation

3. **Low Priority** (Polish):
   - Analytics events
   - Visual polish
   - Edge cases

## 📝 Test Results Template

```
Stock Symbol: __________
Date: __________

Chart Interaction: [ ] Pass [ ] Fail
Story Mode (Button): [ ] Pass [ ] Fail
Long-Press Gesture: [ ] Pass [ ] Fail
Play/Pause: [ ] Pass [ ] Fail
Next/Previous: [ ] Pass [ ] Fail
Voice Narration: [ ] Pass [ ] Fail
Haptic Feedback: [ ] Pass [ ] Fail
Progress Tracking: [ ] Pass [ ] Fail
Analytics: [ ] Pass [ ] Fail

Issues Found:
- 
- 
```

## 🐛 Common Issues to Watch For

1. **Long-press not working**: May need to hold longer (~500ms)
2. **Voice not playing**: Check if TTS service is running or using fallback
3. **Chart not updating**: Check if `priceSeriesForMoments` has data
4. **Moments not appearing**: Check console for `[StockMomentsIntegration]` logs
5. **Story player not closing**: Check if close button is working

## 🎉 Success Criteria

The feature is fully working when:
- ✅ Story Mode opens from button with intro
- ✅ Long-press on dot opens Story Mode without intro
- ✅ Voice narration plays
- ✅ All controls work (play/pause/next/previous/close)
- ✅ Chart updates as story progresses
- ✅ Analytics events fire
- ✅ Haptic feedback works

---

**Next Steps**: Go through the checklist above and test each feature. Report any issues you find!

