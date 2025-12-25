# tts_service/main.py
"""
Wealth Oracle TTS Microservice
FastAPI service for generating custom voice narration
Uses OpenAI TTS for natural-sounding voices
"""
import os
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Try OpenAI TTS first (natural voices), fallback to gTTS if unavailable
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    from gtts import gTTS

MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)

# Max text length to prevent abuse
# Increased to allow full paragraphs to be read
MAX_TEXT_LENGTH = 5000  # ~800 words, enough for most story moments

# OpenAI TTS voice options (natural-sounding voices)
# Options: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
# "nova" and "shimmer" are recommended for Wealth Oracle (warm, professional)
WEALTH_ORACLE_VOICE = os.getenv("WEALTH_ORACLE_VOICE", "nova")  # Default to "nova" - warm, professional

class TTSRequest(BaseModel):
    text: str
    voice: str = "wealth_oracle_v1"
    symbol: str
    moment_id: str


app = FastAPI(title="Wealth Oracle TTS")

# CORS configuration - tighten in production
ALLOWED_ORIGINS = os.getenv("TTS_ALLOWED_ORIGINS", "*").split(",")
if ALLOWED_ORIGINS == ["*"]:
    # Development: allow all
    allow_origins = ["*"]
else:
    # Production: specific domains
    allow_origins = ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Serve generated audio files
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# Initialize OpenAI client if available
# Note: We'll initialize this lazily in the endpoint to ensure env vars are loaded
openai_client = None

def get_openai_client():
    """Lazy initialization of OpenAI client to ensure env vars are loaded"""
    global openai_client
    if openai_client is not None:
        return openai_client
    
    if not OPENAI_AVAILABLE:
        print("[TTS] ⚠️  OpenAI library not installed - using gTTS (install: pip install openai)")
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            openai_client = OpenAI(api_key=api_key)
            print("[TTS] ✅ OpenAI TTS enabled - using natural voices (HD model)")
            return openai_client
        except Exception as e:
            print(f"[TTS] ⚠️  Failed to initialize OpenAI client: {e}")
            return None
    else:
        print("[TTS] ⚠️  OpenAI API key not found - falling back to gTTS")
        return None

# Try to initialize at startup
get_openai_client()


@app.post("/tts")
async def synthesize(req: TTSRequest, request: Request):
    """
    Synthesize speech for the given text and return a URL to the audio file.
    
    Uses OpenAI TTS for natural-sounding voices, falls back to gTTS if unavailable.
    
    Guards:
    - Text length capped at MAX_TEXT_LENGTH
    - Basic error handling
    """
    from fastapi import HTTPException
    
    # Guard: Truncate text if too long
    original_length = len(req.text)
    text = req.text[:MAX_TEXT_LENGTH] if len(req.text) > MAX_TEXT_LENGTH else req.text
    
    if len(req.text) > MAX_TEXT_LENGTH:
        # Log warning but proceed with truncated text
        print(f"[TTS] Text truncated from {original_length} to {MAX_TEXT_LENGTH} chars")
    else:
        print(f"[TTS] Processing text of length {original_length} chars (no truncation needed)")
    
    try:
        filename = f"{req.symbol}_{req.moment_id}_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(MEDIA_DIR, filename)

        # Try OpenAI TTS first (natural voices)
        client = get_openai_client()
        if client:
            try:
                # Map voice request to OpenAI voice options
                # Valid OpenAI voices: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
                # "nova" and "shimmer" are best for Wealth Oracle (warm, professional, natural)
                valid_voices = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
                voice_mapping = {
                    "wealth_oracle_v1": "shimmer",  # Warm, professional female voice (most natural)
                }
                
                # Use requested voice, map legacy names, or fall back to env/default
                requested_voice = req.voice.lower()
                if requested_voice in voice_mapping:
                    final_voice = voice_mapping[requested_voice]
                elif requested_voice in valid_voices:
                    final_voice = requested_voice
                else:
                    # Fall back to env variable or default to shimmer (best quality)
                    final_voice = WEALTH_ORACLE_VOICE if WEALTH_ORACLE_VOICE in valid_voices else "shimmer"
                
                print(f"[TTS] Using OpenAI TTS HD model with voice: {final_voice}, speed: 0.9")
                response = client.audio.speech.create(
                    model="tts-1-hd",  # High-definition model for much more natural sound
                    voice=final_voice,
                    input=text,
                    speed=0.9,  # Slower speed for more natural, conversational delivery (0.9 = 10% slower)
                )
                
                # Save audio file
                response.stream_to_file(filepath)
                print(f"[TTS] ✅ OpenAI TTS audio generated: {filename}")
                
            except Exception as e:
                print(f"[TTS] ⚠️  OpenAI TTS failed: {e}, falling back to gTTS")
                # Fall through to gTTS fallback
                if not OPENAI_AVAILABLE:
                    raise
                # Use gTTS as fallback
                tts = gTTS(text=text, lang="en", slow=False)
                tts.save(filepath)
                print(f"[TTS] ✅ gTTS fallback audio generated: {filename}")
        else:
            # Use gTTS (fallback)
            print(f"[TTS] Using gTTS (OpenAI not available)")
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(filepath)
            print(f"[TTS] ✅ gTTS audio generated: {filename}")

        base_url = str(request.base_url).rstrip("/")
        audio_url = f"{base_url}/media/{filename}"

        return {"audio_url": audio_url}
    except Exception as e:
        print(f"[TTS] Error generating speech: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "wealth-oracle-tts"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

