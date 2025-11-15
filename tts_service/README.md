# Wealth Oracle TTS Service

FastAPI microservice for generating custom voice narration for stock moments.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## API

### POST /tts

Generate speech from text.

**Request:**
```json
{
  "text": "Here's the story behind TSLA's recent moves...",
  "voice": "wealth_oracle_v1",
  "symbol": "TSLA",
  "moment_id": "abc123"
}
```

**Response:**
```json
{
  "audio_url": "http://localhost:8001/media/TSLA_abc123_xyz789.mp3"
}
```

## Integration

The mobile app will call this service when `speakFn` is provided to `MomentStoryPlayer`.

## Future Enhancements

- Swap gTTS for ElevenLabs, Azure TTS, or custom voice model
- Add caching for frequently used phrases
- Rate limiting per user
- Multiple voice personas
- Streaming audio support

