# RichesReach Self-Hosted Setup Guide

Complete guide for setting up the self-hosted RichesReach solution with WebRTC streaming, Socket.io chat, and Whisper transcription.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile App    │    │  Django Backend │    │ Whisper Server  │
│                 │    │                 │    │                 │
│ • WebRTC Client │◄──►│ • API Endpoints │    │ • Transcription │
│ • Socket.io     │    │ • Authentication│    │ • Audio Processing│
│ • Voice Recording│   │ • Data Storage  │    │ • Model Serving │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Streaming Server│
                    │                 │
                    │ • Mediasoup SFU │
                    │ • Socket.io     │
                    │ • WebRTC Signaling│
                    └─────────────────┘
```

## 📋 Prerequisites

- Node.js 18+ 
- Python 3.8+
- MongoDB
- FFmpeg
- Git
- Docker (optional)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo>
cd RichesReach

# Setup Django backend
cd backend/backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# Setup Whisper server (new terminal)
cd ../../whisper-server
./setup.sh
npm start

# Setup Streaming server (new terminal)
cd ../streaming-server
npm install
npm start
```

### 2. Mobile App Configuration

Update your mobile app environment:

```bash
# Copy development environment
cp mobile/env.local.dev mobile/.env.local

# The file should contain:
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.236:8000
EXPO_PUBLIC_WHISPER_API_URL=http://192.168.1.236:3001
EXPO_PUBLIC_STREAMING_SERVER_URL=http://192.168.1.236:3001
```

### 3. Test the Setup

```bash
# Test Django backend
curl http://192.168.1.236:8000/health

# Test Whisper server
curl http://192.168.1.236:3001/health

# Test streaming server
curl http://192.168.1.236:3001/health
```

## 🔧 Detailed Setup

### Django Backend (Port 8000)

The Django backend handles:
- User authentication
- Wealth circles data
- Posts and comments
- Push notifications
- API endpoints

**Setup:**
```bash
cd backend/backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

**Key Features:**
- JWT authentication
- Real-time updates via Socket.io
- Push notification support
- Media upload handling

### Whisper Server (Port 3001)

The Whisper server handles:
- Voice transcription
- Audio processing
- Model serving
- Real-time chat

**Setup:**
```bash
cd whisper-server
./setup.sh  # Downloads and quantizes Whisper model
npm start
```

**Model Optimization:**
- Uses quantized `tiny.en` model (~20MB)
- 80-85% accuracy for English
- <2 second processing time
- Supports M4A, WAV, MP3, WebM

### Streaming Server (Port 3001)

The streaming server handles:
- WebRTC signaling
- Mediasoup SFU
- Live streaming
- Viewer count tracking

**Setup:**
```bash
cd streaming-server
npm install
npm start
```

**Features:**
- Low-latency streaming (<500ms)
- Multi-viewer support
- Real-time viewer count
- Cross-platform compatibility

## 📱 Mobile App Integration

### Voice Transcription

The mobile app now includes voice recording with automatic transcription:

```typescript
// Voice recording with transcription
const startRecording = async () => {
  const recording = new Audio.Recording();
  await recording.prepareToRecordAsync({
    android: {
      extension: '.m4a',
      sampleRate: 16000,
      numberOfChannels: 1,
    },
    ios: {
      extension: '.m4a',
      sampleRate: 16000,
      numberOfChannels: 1,
    },
  });
  await recording.startAsync();
};

const stopRecordingAndTranscribe = async () => {
  await recording.stopAndUnloadAsync();
  const uri = recording.getURI();
  
  // Upload to Whisper server
  const formData = new FormData();
  formData.append('audio', { uri, type: 'audio/m4a' } as any);
  
  const response = await fetch(`${WHISPER_API_URL}/api/transcribe-audio/`, {
    method: 'POST',
    body: formData,
    headers: { 'Authorization': `Bearer ${token}` },
  });
  
  const { transcription } = await response.json();
  setNewPostText(transcription);
};
```

### WebRTC Streaming

```typescript
// WebRTC streaming integration
const startLiveStream = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: true,
    audio: true
  });
  
  const peerConnection = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
  });
  
  stream.getTracks().forEach(track => {
    peerConnection.addTrack(track, stream);
  });
  
  // Connect to streaming server
  socket.emit('start_live_stream', { circleId: circle.id });
};
```

### Socket.io Chat

```typescript
// Real-time chat integration
const chatService = new SocketChatService('http://192.168.1.236:3001');

useEffect(() => {
  chatService.connect();
  chatService.onMessage((message) => {
    setMessages(prev => GiftedChat.append(prev, [message]));
  });
}, []);

const sendMessage = (text: string) => {
  chatService.sendMessage(text);
};
```

## 🐳 Docker Deployment

### Option 1: Individual Services

```bash
# Whisper server
cd whisper-server
docker-compose up -d

# Streaming server
cd ../streaming-server
docker-compose up -d
```

### Option 2: Full Stack

```bash
# Create docker-compose.yml in root
version: '3.8'
services:
  django:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/richesreach
    depends_on: [db]
  
  whisper:
    build: ./whisper-server
    ports: ["3001:3001"]
    volumes:
      - ./whisper-server/models:/app/models
      - ./whisper-server/uploads:/app/uploads
  
  streaming:
    build: ./streaming-server
    ports: ["3002:3002"]
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=richesreach
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🔒 Security Configuration

### JWT Authentication

```bash
# Generate secure JWT secret
openssl rand -base64 32

# Add to environment files
JWT_SECRET=your-generated-secret-here
```

### Rate Limiting

The servers include built-in rate limiting:

- **API endpoints**: 10 requests/second
- **Transcription**: 2 requests/second
- **File uploads**: 25MB max size

### CORS Configuration

```javascript
// Update allowed origins
ALLOWED_ORIGINS=http://localhost:3000,http://192.168.1.236:8081,exp://192.168.1.236:8081
```

## 📊 Performance Optimization

### Whisper Model Selection

| Model | Size | Accuracy | Speed | Use Case |
|-------|------|----------|-------|----------|
| tiny.en-q5_0 | ~20MB | 80-85% | Fastest | Mobile apps |
| base.en-q5_0 | ~70MB | 85-90% | Fast | Balanced |
| small.en-q5_0 | ~240MB | 90-95% | Medium | High accuracy |

### GPU Acceleration

For servers with NVIDIA GPUs:

```bash
# Rebuild Whisper with CUDA
cd whisper.cpp
make CUDA=1

# Set environment variable
CUDA=1
```

### Scaling

For high-traffic deployments:

1. **Load Balancing**: Use nginx or HAProxy
2. **Database**: Use MongoDB Atlas or PostgreSQL
3. **Caching**: Add Redis for session storage
4. **CDN**: Use CloudFlare for static assets

## 🧪 Testing

### Health Checks

```bash
# Django backend
curl http://192.168.1.236:8000/health

# Whisper server
curl http://192.168.1.236:3001/health

# Streaming server
curl http://192.168.1.236:3001/health
```

### Voice Transcription Test

```bash
# Test with sample audio
curl -X POST http://192.168.1.236:3001/api/transcribe-audio/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@sample.m4a"
```

### WebRTC Test

```bash
# Test WebRTC connection
# Use browser developer tools to check WebRTC stats
```

## 🚨 Troubleshooting

### Common Issues

1. **Whisper model not found**:
   ```bash
   cd whisper-server
   npm run setup-whisper
   ```

2. **Audio format issues**:
   - Ensure audio is 16kHz, mono
   - Use M4A format for best compatibility
   - Check file size (<25MB)

3. **WebRTC connection failed**:
   - Check STUN/TURN server configuration
   - Verify firewall settings
   - Test with different network

4. **Socket.io connection issues**:
   - Check CORS configuration
   - Verify server URLs
   - Check network connectivity

### Performance Issues

1. **Slow transcription**:
   - Use smaller model (tiny.en)
   - Enable GPU acceleration
   - Optimize audio format

2. **High memory usage**:
   - Use quantized models
   - Implement request queuing
   - Add memory monitoring

3. **Network latency**:
   - Use CDN for static assets
   - Implement connection pooling
   - Add compression

## 📈 Monitoring

### Logs

```bash
# Django logs
tail -f backend/logs/django.log

# Whisper server logs
tail -f whisper-server/logs/server.log

# Streaming server logs
tail -f streaming-server/logs/server.log
```

### Metrics

- **Transcription accuracy**: Monitor WER (Word Error Rate)
- **Processing time**: Track average transcription time
- **Memory usage**: Monitor model memory consumption
- **Network latency**: Track WebRTC connection times

## 🔄 Updates and Maintenance

### Model Updates

```bash
# Update Whisper model
cd whisper-server
npm run setup-whisper

# Test new model
npm test
```

### Security Updates

```bash
# Update dependencies
npm audit fix
pip install --upgrade -r requirements.txt

# Update Docker images
docker-compose pull
docker-compose up -d
```

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review server logs
3. Test individual components
4. Create an issue in the repository

## 🎉 Success!

You now have a complete self-hosted RichesReach solution with:

- ✅ Voice transcription with Whisper
- ✅ WebRTC live streaming
- ✅ Real-time chat with Socket.io
- ✅ Mobile app integration
- ✅ Docker deployment ready
- ✅ Production optimizations

The system is ready for development and testing. For production deployment, follow the security and scaling guidelines above.
