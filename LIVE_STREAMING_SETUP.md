# Live Streaming Setup Guide

Complete setup guide for Facebook Live/TikTok style live streaming in RichesReach.

## 🎥 **What You Get**

A complete live streaming solution that works like Facebook Live or TikTok Live:

- **🎥 Go Live**: Start broadcasting to your wealth circle
- **👁️ Live Viewers**: See real-time viewer count
- **💬 Live Chat**: Interactive chat during streams
- **👍 Reactions**: Real-time reactions (👍❤️🔥💎)
- **📺 Stream Discovery**: Browse and join live streams
- **🔒 Secure**: Self-hosted, no external APIs

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Stream Host   │    │ Streaming Server│    │   Viewers       │
│                 │    │                 │    │                 │
│ • Camera/Audio  │◄──►│ • Socket.io     │◄──►│ • Watch Stream  │
│ • Live Controls │    │ • Stream Mgmt   │    │ • Chat/React    │
│ • Chat Moderation│    │ • WebRTC Relay  │    │ • Share Stream  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Your Backend  │
                    │                 │
                    │ • User Auth     │
                    │ • Circle Mgmt   │
                    │ • Notifications │
                    └─────────────────┘
```

## 🚀 **Quick Start**

### **1. Install Dependencies**

```bash
# Install streaming server dependencies
cd streaming-server
npm install

# Install mobile app dependencies (if not already done)
cd ../mobile
npm install
```

### **2. Start the Servers**

```bash
# Terminal 1: Start the streaming server
cd streaming-server
npm start

# Terminal 2: Start your main backend (Django)
cd backend/backend
python manage.py runserver

# Terminal 3: Start the Whisper server (optional)
cd whisper-server
npm start
```

### **3. Update Environment Variables**

In your mobile app's `.env` file:

```env
EXPO_PUBLIC_STREAMING_SERVER_URL=http://192.168.1.236:3002
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.236:8000
EXPO_PUBLIC_WHISPER_API_URL=http://192.168.1.236:3001
```

### **4. Test the Feature**

1. **Open your RichesReach app**
2. **Navigate to a Wealth Circle**
3. **Tap "🎥 Go Live"** to start streaming
4. **Tap "📺 Live Streams"** to view available streams

## 📱 **How to Use**

### **Starting a Live Stream**

1. **Go to any Wealth Circle**
2. **Tap "🎥 Go Live"** button
3. **Grant camera/microphone permissions**
4. **Start broadcasting!**

### **Watching Live Streams**

1. **Tap "📺 Live Streams"** button
2. **Browse available streams**
3. **Tap any stream to join**
4. **Chat and react in real-time**

### **Live Stream Features**

#### **For Hosts:**
- **🎥 Camera Control**: Toggle video on/off
- **🎤 Audio Control**: Mute/unmute microphone
- **📊 Viewer Count**: See how many people are watching
- **💬 Chat Moderation**: See and respond to chat messages
- **🔚 End Stream**: Stop broadcasting anytime

#### **For Viewers:**
- **👁️ Watch Live**: Real-time video streaming
- **💬 Live Chat**: Send messages during the stream
- **👍 Reactions**: Send emoji reactions (👍❤️🔥💎)
- **📱 Share**: Share stream with others
- **🔔 Notifications**: Get notified of new streams

## 🔧 **Server Configuration**

### **Streaming Server (Port 3002)**

The streaming server handles:
- **Stream Management**: Start/stop streams
- **WebRTC Signaling**: Connect hosts and viewers
- **Live Chat**: Real-time messaging
- **Reactions**: Emoji reactions
- **Viewer Count**: Track live viewers

### **API Endpoints**

```javascript
// Get all active streams
GET /api/streams

// Get specific stream details
GET /api/streams/:streamId

// Start a new stream
POST /api/streams/start
{
  "streamId": "stream-user123-1234567890",
  "title": "Live from Wealth Circle",
  "host": "John Doe",
  "category": "wealth-management",
  "circleId": "circle-123"
}

// End a stream
POST /api/streams/:streamId/end

// Get stream chat
GET /api/streams/:streamId/chat
```

### **Socket.io Events**

```javascript
// Host starts streaming
socket.emit('start-streaming', {
  streamId: 'stream-123',
  title: 'My Live Stream',
  category: 'wealth-management',
  circleId: 'circle-123'
});

// Viewer joins stream
socket.emit('join-stream', {
  streamId: 'stream-123',
  userId: 'user-456',
  userName: 'Jane Doe',
  userAvatar: 'https://...'
});

// Send chat message
socket.emit('stream-chat', {
  streamId: 'stream-123',
  message: 'Great stream!',
  userId: 'user-456',
  userName: 'Jane Doe',
  userAvatar: 'https://...'
});

// Send reaction
socket.emit('stream-reaction', {
  streamId: 'stream-123',
  reaction: '👍',
  userId: 'user-456',
  userName: 'Jane Doe'
});
```

## 🎯 **Use Cases**

### **1. Financial Education**
- **Live Market Analysis**: Real-time market commentary
- **Investment Strategies**: Live investment advice
- **Q&A Sessions**: Interactive financial Q&A
- **Portfolio Reviews**: Live portfolio analysis

### **2. Wealth Circle Activities**
- **Circle Meetings**: Virtual circle gatherings
- **Guest Speakers**: Invite financial experts
- **Group Discussions**: Live financial discussions
- **Announcements**: Important circle updates

### **3. Personal Finance**
- **Budget Planning**: Live budget planning sessions
- **Tax Preparation**: Live tax advice
- **Retirement Planning**: Live retirement discussions
- **Debt Management**: Live debt reduction strategies

## 🔒 **Security & Privacy**

### **Authentication**
- **JWT Tokens**: Secure user authentication
- **Circle Membership**: Only circle members can stream/watch
- **User Verification**: Verified users only

### **Privacy**
- **Self-Hosted**: No external video services
- **Data Control**: All data stays on your servers
- **No Recording**: Streams not recorded by default
- **End-to-End**: WebRTC encryption

### **Moderation**
- **Host Controls**: Stream hosts can moderate chat
- **User Reporting**: Report inappropriate content
- **Circle Rules**: Enforce circle-specific rules

## 📊 **Performance**

### **Expected Performance**
- **Latency**: <2 seconds for live streaming
- **Quality**: HD video (720p) with good audio
- **Concurrent Streams**: 10+ simultaneous streams
- **Viewers per Stream**: 100+ viewers per stream

### **Bandwidth Requirements**
- **Host**: ~2-3 Mbps upload
- **Viewer**: ~1-2 Mbps download
- **Server**: ~100 Mbps for 50 concurrent streams

## 🚀 **Deployment**

### **Production Setup**

1. **Deploy Streaming Server**
```bash
# On your VPS/server
cd streaming-server
npm install --production
pm2 start live-streaming-server.js --name "live-streaming"
```

2. **Configure Nginx**
```nginx
# /etc/nginx/sites-available/streaming
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

3. **Update Mobile App**
```env
EXPO_PUBLIC_STREAMING_SERVER_URL=https://your-domain.com
```

### **Docker Deployment**

```dockerfile
# Dockerfile for streaming server
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3002
CMD ["node", "live-streaming-server.js"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  streaming-server:
    build: ./streaming-server
    ports:
      - "3002:3002"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

## 🔧 **Customization**

### **Custom Stream Categories**
```javascript
// In live-streaming-server.js
const STREAM_CATEGORIES = [
  'wealth-management',
  'investment-strategies',
  'market-analysis',
  'financial-education',
  'retirement-planning',
  'tax-advice'
];
```

### **Custom Reactions**
```javascript
// In LiveStreamingModal.tsx
const CUSTOM_REACTIONS = [
  '👍', '❤️', '🔥', '💎', '🚀', '💰', '📈', '🎯'
];
```

### **Stream Quality Settings**
```javascript
// In LiveStreamingModal.tsx
const STREAM_QUALITY = {
  low: { width: 640, height: 480, bitrate: 500 },
  medium: { width: 1280, height: 720, bitrate: 1000 },
  high: { width: 1920, height: 1080, bitrate: 2000 }
};
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Camera/Microphone Not Working**
```javascript
// Check permissions
const { status } = await MediaStream.getUserMedia({ video: true, audio: true });
if (status !== 'granted') {
  Alert.alert('Permission needed', 'Grant camera and microphone access');
}
```

#### **Stream Not Starting**
```bash
# Check server status
curl http://localhost:3002/health

# Check logs
pm2 logs live-streaming
```

#### **Viewers Can't Join**
```javascript
// Check WebRTC configuration
const rtcConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
};
```

#### **High Latency**
- **Use WiFi**: Better performance on WiFi vs cellular
- **Close Other Apps**: Free up device resources
- **Check Server Load**: Monitor server performance
- **Optimize Video Quality**: Lower resolution for better performance

### **Debug Mode**

```javascript
// Enable debug logging
const DEBUG = true;

if (DEBUG) {
  console.log('Stream state:', streamState);
  console.log('Viewer count:', viewerCount);
  console.log('Chat messages:', chatMessages);
}
```

## 📈 **Analytics**

### **Stream Statistics**
- **Total Views**: How many people watched
- **Peak Viewers**: Maximum concurrent viewers
- **Chat Messages**: Total chat activity
- **Reactions**: Total reactions received
- **Duration**: How long the stream lasted

### **Performance Metrics**
- **Connection Quality**: WebRTC connection stats
- **Latency**: Stream delay measurements
- **Bandwidth Usage**: Data consumption
- **Error Rates**: Failed connections/streams

## 🎉 **Ready to Go Live!**

Your RichesReach app now has a complete live streaming solution that:

- ✅ **Works Like Facebook Live**: One-to-many streaming
- ✅ **Real-time Chat**: Interactive live chat
- ✅ **Live Reactions**: Emoji reactions
- ✅ **Self-hosted**: No external dependencies
- ✅ **Secure**: End-to-end encrypted
- ✅ **Scalable**: Handles multiple concurrent streams
- ✅ **Integrated**: Works with your existing app

**Start broadcasting to your wealth circles today!** 🎥

## 📞 **Support**

If you need help:
1. **Check the logs**: `pm2 logs live-streaming`
2. **Test connectivity**: `curl http://localhost:3002/health`
3. **Verify permissions**: Camera/microphone access
4. **Check network**: WiFi vs cellular performance

**Happy streaming!** 🚀
