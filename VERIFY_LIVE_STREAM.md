# 🎥 How to Verify Your Live Stream is Working

## Quick Verification Steps

### 1. **Check Backend Server is Running**
```bash
curl http://localhost:8000/health
```
**Expected**: `{"status":"ok",...}`

### 2. **Check Socket.io Connection**
The live stream uses Socket.io on your backend server. Verify it's accessible:
```bash
curl http://localhost:8000/ws
```
**Expected**: Should connect (may show WebSocket upgrade response)

### 3. **Test in the App**

#### **As Host (Starting Stream):**
1. Open RichesReach app
2. Navigate to any Wealth Circle
3. Tap **"🎥 Go Live"** button
4. Grant camera/microphone permissions when prompted
5. **Verify these indicators:**
   - ✅ "LIVE" indicator appears (usually red dot)
   - ✅ Duration timer starts counting (00:00, 00:01, etc.)
   - ✅ Your video feed displays
   - ✅ Viewer count shows "0" or "1" (you as host)
   - ✅ Stream controls are visible (mute, camera flip, end stream)

#### **As Viewer (Joining Stream):**
1. On another device or app instance
2. Navigate to the same Wealth Circle
3. Tap **"📺 Join Live"** or **"Live Streams"** button
4. **Verify these indicators:**
   - ✅ Host's video feed displays
   - ✅ Viewer count increases
   - ✅ Chat interface is available
   - ✅ Reaction buttons work (❤️ 🔥 💰 👍)
   - ✅ Stream info shows correctly

### 4. **Test Real-Time Features**

#### **Chat Test:**
- Send a message from viewer
- **Expected**: Message appears instantly for both host and viewer
- **Expected**: Message shows username and timestamp

#### **Reactions Test:**
- Tap reaction buttons (❤️ 🔥 💰 👍) from viewer
- **Expected**: Animated emoji floats up the screen
- **Expected**: Reaction count increases
- **Expected**: Host sees reactions in real-time

#### **Viewer Count Test:**
- Have multiple viewers join
- **Expected**: Viewer count updates in real-time for all participants

### 5. **Check Console Logs**

#### **In Expo/Metro Terminal:**
Look for these log messages:
```
🎥 Starting RichesReach live stream for circle: [Circle Name]
📺 Live stream started in circle [id] by [user]
👀 Viewer [user] joined live stream in circle [id]
🔌 Client connected: [socket-id]
```

#### **In Backend Terminal:**
Look for Socket.io connection logs:
```
🔌 Client connected: [socket-id]
👥 User [socket-id] joined circle [circle-id]
📺 Live stream started in circle [circle-id] by [host]
```

### 6. **Common Issues & Solutions**

#### **Stream Won't Start:**
- ✅ Check camera/microphone permissions
- ✅ Verify backend server is running (`curl http://localhost:8000/health`)
- ✅ Check network connection
- ✅ Restart the app

#### **Viewers Can't See Stream:**
- ✅ Verify Socket.io connection (check backend logs)
- ✅ Check if host's stream is actually active
- ✅ Verify both devices are on same network (for local testing)
- ✅ Check WebRTC permissions

#### **Chat/Reactions Not Working:**
- ✅ Verify Socket.io connection is active
- ✅ Check backend server logs for Socket.io events
- ✅ Verify network connectivity

### 7. **Advanced Verification**

#### **Check Socket.io Events:**
Open browser console or check backend logs for:
- `join-live` - When someone joins
- `viewer-joined` - When viewer connects
- `viewer_count_update` - When count changes
- `chat-message` - When message sent
- `reaction` - When reaction sent

#### **Check WebRTC Connection:**
- Look for WebRTC connection state in logs
- Verify `RTCPeerConnection` is established
- Check for ICE candidate exchange

### 8. **Performance Checks**

#### **Stream Quality:**
- Video should be smooth (not choppy)
- Audio should be clear
- No significant delay (< 2 seconds)

#### **Real-Time Features:**
- Chat messages: < 1 second delay
- Reactions: < 500ms delay
- Viewer count: Updates within 1 second

## 🧪 Automated Test Script

Run the verification script:
```bash
./test_live_stream.sh
```

This will test:
- ✅ Backend server connectivity
- ✅ Streaming server (if separate)
- ✅ WebSocket endpoints
- ✅ API endpoints
- ✅ Configuration

## 📊 Success Indicators

Your live stream is working if:
- ✅ Stream starts without errors
- ✅ Video/audio displays correctly
- ✅ Multiple viewers can join
- ✅ Chat messages appear instantly
- ✅ Reactions work in real-time
- ✅ Viewer count updates correctly
- ✅ No crashes or freezes

## 🔍 Debug Mode

Enable debug logging in the app:
```typescript
// In AdvancedLiveStreaming.tsx
const DEBUG = true;

if (DEBUG) {
  console.log('Stream state:', isStreaming);
  console.log('Viewer count:', viewerCount);
  console.log('Socket connected:', socketRef.current?.connected);
}
```

## 📞 Still Having Issues?

1. **Check Backend Logs**: Look for Socket.io connection errors
2. **Check Mobile Logs**: Look for WebRTC or permission errors
3. **Verify Network**: Both devices on same network for local testing
4. **Check Permissions**: Camera, microphone, and network permissions granted

---

**Quick Test Checklist:**
- [ ] Backend server running (port 8000)
- [ ] App can connect to backend
- [ ] Camera/microphone permissions granted
- [ ] "Go Live" button works
- [ ] Stream starts successfully
- [ ] Video displays correctly
- [ ] Viewer can join
- [ ] Chat works
- [ ] Reactions work
- [ ] Viewer count updates

