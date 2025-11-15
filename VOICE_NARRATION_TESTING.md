# Voice Narration Testing Guide

## ✅ What's Fixed

1. **Automatic Fallback**: TTS service now automatically falls back to `expo-speech` if:
   - TTS service is not running
   - TTS service returns an error
   - Network request fails
   - Audio URL is missing

2. **Proper Voice Stopping**: Voice now stops correctly when:
   - Story player is closed
   - Play/Pause button is pressed
   - Next/Previous buttons are pressed
   - Component unmounts

3. **Better Logging**: Console logs help track TTS behavior

## 🧪 Testing Checklist

### Test 1: Voice Plays During Story (TTS Service Running)
**Setup**: Start the TTS service:
```bash
cd tts_service
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Steps**:
1. Open Story Mode (tap "▶ Play Story" button)
2. Listen for voice narration
3. Check console for: `[WealthOracleTTS] Playing audio from TTS service`

**Expected**:
- ✅ Voice plays clearly
- ✅ Voice matches the moment text
- ✅ Console shows TTS service is being used

---

### Test 2: Fallback to expo-speech (TTS Service Not Running)
**Setup**: Make sure TTS service is NOT running

**Steps**:
1. Open Story Mode
2. Listen for voice narration
3. Check console for: `[WealthOracleTTS] Using expo-speech fallback`

**Expected**:
- ✅ Voice still plays (using device TTS)
- ✅ Console shows fallback is being used
- ✅ Voice quality is acceptable (may be different from TTS service)

---

### Test 3: Voice Stops When Paused
**Steps**:
1. Open Story Mode
2. Wait for voice to start playing
3. Tap "Pause" button
4. Check console for: `[WealthOracleTTS] Stopped audio playback` or `[WealthOracleTTS] Stopped expo-speech`

**Expected**:
- ✅ Voice stops immediately when paused
- ✅ No audio continues in background
- ✅ Console confirms voice was stopped

---

### Test 4: Voice Stops When Closed
**Steps**:
1. Open Story Mode
2. Wait for voice to start playing
3. Tap "Close" button
4. Check console for stop messages

**Expected**:
- ✅ Voice stops immediately when closed
- ✅ No audio continues after modal closes
- ✅ Console confirms voice was stopped

---

### Test 5: Voice Stops When Navigating
**Steps**:
1. Open Story Mode
2. Wait for voice to start playing
3. Tap "Next" (▶) button
4. Check console for stop messages

**Expected**:
- ✅ Current voice stops
- ✅ New voice starts for next moment
- ✅ No overlapping audio

---

### Test 6: Voice Continues After Resume
**Steps**:
1. Open Story Mode
2. Wait for voice to start
3. Tap "Pause"
4. Tap "Play" again

**Expected**:
- ✅ Voice resumes from the same moment
- ✅ No audio glitches
- ✅ Smooth transition

---

## 🔍 Console Logs to Watch For

### Successful TTS Service Call:
```
[WealthOracleTTS] Attempting to call TTS service: http://192.168.1.240:8001/tts
[WealthOracleTTS] Playing audio from TTS service
```

### Fallback to expo-speech:
```
[WealthOracleTTS] TTS request failed (404), falling back to expo-speech
[WealthOracleTTS] Using expo-speech fallback
```

### Voice Stopped:
```
[WealthOracleTTS] Stopped audio playback
[WealthOracleTTS] Stopped expo-speech
```

### Errors (should not happen, but good to know):
```
[WealthOracleTTS] Error calling TTS service, falling back to expo-speech: [error details]
[WealthOracleTTS] Failed to use expo-speech fallback: [error details]
```

---

## 🐛 Common Issues

### Issue: Voice doesn't play at all
**Possible Causes**:
- TTS service not running AND expo-speech not working
- Device volume is muted
- Audio permissions not granted

**Fix**:
- Check device volume
- Check console for errors
- Verify expo-speech permissions

### Issue: Voice continues after closing
**Possible Causes**:
- `stopWealthOracle()` not being called
- Audio cleanup not working

**Fix**:
- Check console for stop messages
- Verify `handleClose` calls `stopSpeech()`

### Issue: Overlapping audio
**Possible Causes**:
- Previous audio not stopped before new one starts
- Multiple TTS calls happening simultaneously

**Fix**:
- Check that `stopWealthOracle()` is called before `playWealthOracle()`
- Verify cleanup in `useEffect` return function

---

## ✅ Success Criteria

Voice narration is working correctly when:
- ✅ Voice plays during story (either TTS service or expo-speech)
- ✅ Voice stops when paused
- ✅ Voice stops when closed
- ✅ Voice stops when navigating
- ✅ Fallback works when TTS service unavailable
- ✅ No overlapping audio
- ✅ Console logs are helpful for debugging

---

## 📝 Test Results Template

```
Date: __________
Device: __________
TTS Service Running: [ ] Yes [ ] No

Test 1 (Voice Plays): [ ] Pass [ ] Fail
Test 2 (Fallback): [ ] Pass [ ] Fail
Test 3 (Pause): [ ] Pass [ ] Fail
Test 4 (Close): [ ] Pass [ ] Fail
Test 5 (Navigate): [ ] Pass [ ] Fail
Test 6 (Resume): [ ] Pass [ ] Fail

Issues Found:
- 
- 
```

