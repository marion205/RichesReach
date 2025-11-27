# Voice Endpoint Testing Guide

## ✅ What's Complete

### Backend Implementation
- ✅ `/api/voice/stream` endpoint (streaming token-by-token)
- ✅ `/api/voice/process/` endpoint (Whisper transcription)
- ✅ Price caching (12s TTL)
- ✅ Parallel fetching in `build_context()`
- ✅ Trimmed history (last 4 exchanges)
- ✅ Optimized max_tokens (140-160)

### Frontend Implementation
- ✅ `processAudioStreaming()` function
- ✅ `speakText()` with immediate/interrupt mode
- ✅ Integrated into `processAudio()` flow

### Test Files Created
- ✅ `test_voice_benchmark.py` - Benchmark latency tests
- ✅ `test_voice_endpoints.py` - Unit tests for 404s/errors
- ✅ `quick_test.py` - Quick verification script

## 📋 What's Left to Do

### 1. Start Backend Server
```bash
cd deployment_package/backend
# Activate your virtual environment
source venv/bin/activate  # or your venv path
# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Run Quick Test
```bash
cd deployment_package/backend
python3 quick_test.py
```

This will verify:
- ✅ Server is running
- ✅ `/api/voice/stream` exists (no 404)
- ✅ `/api/voice/process/` exists (no 404)
- ✅ Streaming works (tokens received)

### 3. Run Full Benchmark
```bash
cd deployment_package/backend
python3 test_voice_benchmark.py
```

This will test:
- First token latency (target: <450ms)
- Full response latency
- Multiple test transcripts

### 4. Run Unit Tests
```bash
cd deployment_package/backend
pytest test_voice_endpoints.py -v
```

This will test:
- Endpoint existence (no 404s)
- Valid requests
- Error handling
- Different intents

## 🎯 Expected Results

### Streaming Performance
- **First token**: ~350-450ms (vs 1.6-2.3s before)
- **Full response**: ~1.4-2.3s (but feels instant due to streaming)

### Test Results
- ✅ All endpoints return 200 (not 404)
- ✅ Streaming returns tokens
- ✅ No server errors
- ✅ Intent detection works

## 🔧 Troubleshooting

### Server Not Running
```bash
# Check if port 8000 is in use
lsof -i :8000

# Start server
cd deployment_package/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Missing Dependencies
```bash
pip install pytest pytest-asyncio aiohttp
```

### OPENAI_API_KEY Not Set
```bash
export OPENAI_API_KEY="your-key-here"
# Or add to .env file
```

## 📊 Next Steps After Tests Pass

1. ✅ Verify streaming works in mobile app
2. ✅ Test on real device (not simulator)
3. ✅ Measure actual latency in production
4. ✅ Monitor for errors in production logs

