# RichesReach Whisper Server

Self-hosted speech-to-text transcription server using OpenAI's Whisper model optimized for mobile voice posts.

## Features

- 🎤 **Voice Transcription**: Convert audio to text using Whisper.cpp
- 🚀 **Optimized Models**: Quantized models for faster inference and smaller size
- 🔒 **Secure**: JWT authentication and rate limiting
- 📱 **Mobile Ready**: Optimized for React Native/Expo audio uploads
- ⚡ **Real-time**: Socket.io integration for live updates
- 🐳 **Docker Ready**: Easy deployment with Docker Compose
- 📊 **Monitoring**: Health checks and performance metrics

## Model Optimization

This server uses quantized Whisper models for optimal performance:

| Model | Size | Accuracy | Speed | Use Case |
|-------|------|----------|-------|----------|
| tiny.en-q5_0 | ~20MB | 80-85% | Fastest | Mobile apps, real-time |
| base.en-q5_0 | ~70MB | 85-90% | Fast | Balanced performance |
| small.en-q5_0 | ~240MB | 90-95% | Medium | High accuracy needs |

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and setup
git clone <your-repo>
cd whisper-server

# Start with Docker Compose
docker-compose up -d

# Check status
curl http://localhost:3001/health
```

### Option 2: Manual Setup

```bash
# Install dependencies
npm install

# Setup Whisper model (downloads and quantizes)
npm run setup-whisper

# Start server
npm start
```

## API Endpoints

### POST /api/transcribe-audio/
Transcribe audio files to text.

**Request:**
```bash
curl -X POST http://localhost:3001/api/transcribe-audio/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@voice.m4a"
```

**Response:**
```json
{
  "transcription": "Hello, this is a test transcription",
  "audioUrl": "/uploads/audio-1234567890.m4a",
  "processingTime": 1250,
  "model": "ggml-tiny.en-q5_0.bin"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "whisperModel": "ggml-tiny.en-q5_0.bin",
  "modelExists": true
}
```

## Mobile Integration

Update your React Native app to use the new transcription endpoint:

```typescript
// In your CircleDetailScreen component
const transcribeAudio = async (audioUri: string) => {
  const formData = new FormData();
  formData.append('audio', { 
    uri: audioUri, 
    type: 'audio/m4a', 
    name: 'voice.m4a' 
  } as any);

  const response = await fetch('http://your-server:3001/api/transcribe-audio/', {
    method: 'POST',
    body: formData,
    headers: { 
      'Authorization': `Bearer ${token}`,
    },
  });

  const { transcription, audioUrl } = await response.json();
  return { transcription, audioUrl };
};
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Server Configuration
PORT=3001
NODE_ENV=production

# Whisper Configuration
WHISPER_MODEL=ggml-tiny.en-q5_0.bin
WHISPER_PATH=./whisper.cpp

# Database
MONGODB_URI=mongodb://localhost:27017/richesreach_whisper

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,exp://192.168.1.236:8081

# Optional: GPU acceleration
CUDA=1
```

### Model Selection

To use a different model, update the `WHISPER_MODEL` environment variable:

```bash
# For better accuracy (larger model)
WHISPER_MODEL=ggml-base.en-q5_0.bin

# For fastest processing (smallest model)
WHISPER_MODEL=ggml-tiny.en-q5_0.bin
```

## Performance Optimization

### Model Quantization

The setup script automatically quantizes models to Q5_0 format, reducing size by ~50% with minimal accuracy loss:

```bash
# Manual quantization
cd whisper.cpp
./quantize models/ggml-tiny.en.bin models/ggml-tiny.en-q5_0.bin q5_0
```

### GPU Acceleration

For servers with NVIDIA GPUs, enable CUDA acceleration:

```bash
# Rebuild with CUDA support
cd whisper.cpp
make CUDA=1

# Set environment variable
CUDA=1
```

### Rate Limiting

The server includes built-in rate limiting:

- General API: 10 requests/second
- Transcription: 2 requests/second
- Burst allowance for temporary spikes

## Deployment

### Production Deployment

1. **VPS Setup** (DigitalOcean, AWS, etc.):
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone and deploy
git clone <your-repo>
cd whisper-server
docker-compose up -d
```

2. **SSL/HTTPS**:
```bash
# Add SSL certificates to ./ssl/
# Update nginx.conf for HTTPS
```

3. **Monitoring**:
```bash
# Check logs
docker-compose logs -f whisper-server

# Health check
curl https://your-domain.com/health
```

### Scaling

For high-traffic deployments:

1. **Load Balancing**: Use multiple server instances
2. **Redis**: Add Redis for Socket.io scaling
3. **CDN**: Use CloudFlare for static file delivery
4. **Database**: Use MongoDB Atlas for managed database

## Troubleshooting

### Common Issues

1. **Model not found**:
```bash
npm run setup-whisper
```

2. **Permission denied**:
```bash
chmod +x whisper.cpp/main
chmod +x whisper.cpp/quantize
```

3. **Audio format issues**:
- Ensure audio is in supported format (M4A, WAV, MP3)
- Check FFmpeg installation
- Verify audio file size (<25MB)

4. **Memory issues**:
- Use smaller model (tiny.en instead of base.en)
- Increase server RAM
- Enable swap file

### Performance Tuning

1. **Faster transcription**:
   - Use tiny.en model
   - Enable GPU acceleration
   - Optimize audio format (16kHz, mono)

2. **Better accuracy**:
   - Use base.en or small.en model
   - Ensure good audio quality
   - Use English-specific models (.en)

## Security

- JWT authentication for all endpoints
- Rate limiting to prevent abuse
- File type validation
- Input sanitization
- CORS configuration
- Security headers via Helmet

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs
3. Test with the health endpoint
4. Create an issue in the repository
