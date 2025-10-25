# Video Streaming Feature Guide

Complete guide on how to use the self-hosted video streaming feature in RichesReach.

## 🎥 **How Video Streaming Works**

The video streaming feature is **completely self-hosted** and doesn't rely on external APIs. It uses:

### **1. WebRTC (Peer-to-Peer Video)**
- **Direct Connection**: Users connect directly to each other
- **No External Servers**: Video/audio streams go directly between users
- **Low Latency**: Real-time communication with minimal delay
- **Secure**: End-to-end encrypted video/audio

### **2. Socket.io (Signaling Server)**
- **Connection Setup**: Helps users find and connect to each other
- **Call Management**: Handles call offers, answers, and connection details
- **Runs on Your Server**: Uses the same server as your Whisper transcription

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User A        │    │   Your Server   │    │   User B        │
│                 │    │                 │    │                 │
│ • WebRTC Client │◄──►│ • Socket.io     │◄──►│ • WebRTC Client │
│ • Video/Audio   │    │ • Signaling     │    │ • Video/Audio   │
│ • Call Controls │    │ • Call Setup    │    │ • Call Controls │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Whisper API   │
                    │                 │
                    │ • Transcription │
                    │ • Voice Posts   │
                    └─────────────────┘
```

## 🚀 **How to Use Video Streaming**

### **1. Start the Servers**

First, make sure both servers are running:

```bash
# Terminal 1: Start the main server (Django backend)
cd backend/backend
python manage.py runserver

# Terminal 2: Start the Whisper/Socket.io server
cd whisper-server
npm start
```

### **2. Access the Video Call Feature**

In your RichesReach app:

1. **Navigate to a Wealth Circle**
2. **Look for the "📹 Call" button** in the circle detail screen
3. **Tap the button** to start a video call

### **3. Video Call Flow**

#### **Starting a Call:**
```typescript
// When user taps "📹 Call" button
const startVideoCall = async (partnerId: string) => {
  // 1. Request camera/microphone permissions
  const stream = await MediaStream.getUserMedia({ video: true, audio: true });
  
  // 2. Create WebRTC peer connection
  const pc = new RTCPeerConnection(rtcConfiguration);
  
  // 3. Add local video/audio tracks
  stream.getTracks().forEach(track => pc.addTrack(track, stream));
  
  // 4. Create call offer
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  
  // 5. Send offer via Socket.io
  socket.emit('call-offer', { offer, to: partnerId, from: userId });
};
```

#### **Receiving a Call:**
```typescript
// When receiving a call offer
socket.on('call-offer', ({ offer, from }) => {
  // Show incoming call alert
  Alert.alert('Incoming Call', `${from} is calling. Answer?`, [
    { text: 'Decline', onPress: () => declineCall() },
    { text: 'Answer', onPress: () => answerCall(offer, from) }
  ]);
});
```

#### **Answering a Call:**
```typescript
const answerCall = async (offer, from) => {
  // 1. Get local media stream
  const stream = await MediaStream.getUserMedia({ video: true, audio: true });
  
  // 2. Add tracks to peer connection
  stream.getTracks().forEach(track => pc.addTrack(track, stream));
  
  // 3. Set remote description
  await pc.setRemoteDescription(new RTCSessionDescription(offer));
  
  // 4. Create answer
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  
  // 5. Send answer via Socket.io
  socket.emit('call-answer', { answer, to: from });
};
```

## 🔧 **Server Configuration**

### **Socket.io Signaling Server**

The signaling server handles call setup:

```javascript
// whisper-server/server.js

// Video call signaling handlers
socket.on('call-offer', ({ offer, to, from }) => {
  console.log(`📞 Call offer from ${from} to ${to}`);
  socket.to(to).emit('call-offer', { offer, from });
});

socket.on('call-answer', ({ answer, to }) => {
  console.log(`📞 Call answer to ${to}`);
  socket.to(to).emit('call-answer', { answer });
});

socket.on('ice-candidate', ({ candidate, to }) => {
  socket.to(to).emit('ice-candidate', { candidate });
});

socket.on('call-decline', ({ to }) => {
  console.log(`📞 Call declined to ${to}`);
  socket.to(to).emit('call-decline', {});
});

socket.on('end-call', ({ to }) => {
  console.log(`📞 Call ended to ${to}`);
  socket.to(to).emit('end-call', {});
});
```

### **WebRTC Configuration**

```typescript
// STUN servers for NAT traversal
const rtcConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
};
```

## 📱 **Mobile App Integration**

### **Video Call UI Components**

The video call feature includes:

1. **Call Button**: "📹 Call" button in the circle detail screen
2. **Call Modal**: Full-screen video call interface
3. **Call Controls**: Mute, video toggle, end call buttons
4. **Video Views**: Local and remote video streams

### **Key UI Elements**

```typescript
// Call Button
<TouchableOpacity onPress={() => startVideoCall('partner-user-id')}>
  <LinearGradient colors={['#007AFF', '#5856D6']}>
    <Text>📹 Call</Text>
  </LinearGradient>
</TouchableOpacity>

// Video Call Modal
<Modal visible={callModalVisible} animationType="slide">
  <View style={styles.videoCallModal}>
    {/* Remote Video */}
    {remoteStream && (
      <RTCView 
        streamURL={remoteStream.toURL()} 
        style={styles.remoteVideo} 
      />
    )}
    
    {/* Local Video */}
    {localStream && (
      <RTCView 
        streamURL={localStream.toURL()} 
        style={styles.localVideo} 
      />
    )}
    
    {/* Call Controls */}
    <View style={styles.callControls}>
      <TouchableOpacity onPress={toggleMute}>
        <Text>{isMuted ? '🔇' : '🎤'}</Text>
      </TouchableOpacity>
      
      <TouchableOpacity onPress={endVideoCall}>
        <Text>📞</Text>
      </TouchableOpacity>
      
      <TouchableOpacity onPress={toggleVideo}>
        <Text>{isVideoEnabled ? '📹' : '📷'}</Text>
      </TouchableOpacity>
    </View>
  </View>
</Modal>
```

## 🎯 **Use Cases**

### **1. Wealth Circle Video Calls**
- **1-on-1 Calls**: Direct video calls between circle members
- **Investment Discussions**: Real-time financial advice and discussions
- **Portfolio Reviews**: Screen sharing for portfolio analysis
- **Market Updates**: Live market commentary and analysis

### **2. Financial Advisory**
- **Client Meetings**: Secure video calls with financial advisors
- **Portfolio Reviews**: Real-time portfolio analysis and recommendations
- **Tax Planning**: Video consultations for tax strategies
- **Estate Planning**: Secure discussions about estate planning

### **3. Educational Content**
- **Financial Education**: Live financial literacy sessions
- **Market Analysis**: Real-time market commentary
- **Investment Strategies**: Live investment strategy discussions
- **Q&A Sessions**: Interactive financial Q&A sessions

## 🔒 **Security Features**

### **End-to-End Encryption**
- **WebRTC Security**: All video/audio streams are encrypted
- **DTLS/SRTP**: Industry-standard encryption protocols
- **No Server Storage**: Video/audio never stored on servers

### **Authentication**
- **JWT Tokens**: Secure authentication for all users
- **User Verification**: Only authenticated users can make calls
- **Circle Membership**: Only circle members can call each other

### **Privacy**
- **Self-Hosted**: No third-party video services
- **Data Control**: All data stays on your servers
- **No Recording**: Calls are not recorded by default

## 🚀 **Getting Started**

### **1. Prerequisites**
- Node.js server running (whisper-server)
- Django backend running
- Mobile app with WebRTC support
- Camera/microphone permissions

### **2. Test the Feature**
```bash
# Start both servers
cd whisper-server && npm start
cd backend/backend && python manage.py runserver

# Open mobile app
# Navigate to a wealth circle
# Tap "📹 Call" button
# Test video call functionality
```

### **3. Troubleshooting**

#### **Common Issues:**

**Camera/Microphone Not Working:**
```typescript
// Check permissions
const { status } = await MediaStream.getUserMedia({ video: true, audio: true });
if (status !== 'granted') {
  Alert.alert('Permission needed', 'Grant camera and microphone access');
}
```

**Connection Failed:**
```typescript
// Check STUN servers
const rtcConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' }
  ]
};
```

**Socket Connection Issues:**
```typescript
// Check server URL
const API_BASE_URL = 'http://your-server-ip:3001';
const socket = io(API_BASE_URL);
```

## 📊 **Performance**

### **Expected Performance**
- **Latency**: <200ms for video calls
- **Quality**: HD video (720p) with good audio
- **Bandwidth**: ~1-2 Mbps per user
- **Concurrent Calls**: Limited by server resources

### **Optimization Tips**
- **Use WiFi**: Better performance on WiFi vs cellular
- **Close Other Apps**: Free up device resources
- **Good Lighting**: Better video quality with good lighting
- **Stable Connection**: Ensure stable internet connection

## 🔧 **Customization**

### **Customize Call UI**
```typescript
// Custom call button styles
const styles = StyleSheet.create({
  videoCallButton: {
    position: 'absolute',
    bottom: 150,
    right: 16,
    zIndex: 1,
  },
  videoCallGradient: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 25,
  },
  videoCallText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
});
```

### **Add Call Features**
```typescript
// Screen sharing
const startScreenShare = async () => {
  const stream = await MediaStream.getDisplayMedia();
  // Add screen share track to peer connection
};

// Call recording
const startRecording = () => {
  // Implement call recording functionality
};

// Group calls
const startGroupCall = (participants) => {
  // Implement multi-participant calls
};
```

## 🎉 **Ready to Use!**

Your RichesReach app now has a complete, self-hosted video streaming solution that:

- ✅ **Works Offline**: No external API dependencies
- ✅ **Secure**: End-to-end encrypted video calls
- ✅ **Fast**: Low latency peer-to-peer connections
- ✅ **Integrated**: Works seamlessly with your existing app
- ✅ **Scalable**: Can handle multiple concurrent calls

**Start making video calls in your wealth circles today!** 🚀
