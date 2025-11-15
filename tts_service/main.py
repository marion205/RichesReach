# tts_service/main.py
"""
Wealth Oracle TTS Microservice
FastAPI service for generating custom voice narration
"""
import os
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from gtts import gTTS  # Simple TTS; you can swap to ElevenLabs, Azure, etc.

MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)


# Max text length to prevent abuse
MAX_TEXT_LENGTH = 1500


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


@app.post("/tts")
async def synthesize(req: TTSRequest, request: Request):
    """
    Synthesize speech for the given text and return a URL to the audio file.
    
    Guards:
    - Text length capped at MAX_TEXT_LENGTH
    - Basic error handling
    """
    from fastapi import HTTPException
    
    # Guard: Truncate text if too long
    text = req.text[:MAX_TEXT_LENGTH] if len(req.text) > MAX_TEXT_LENGTH else req.text
    
    if len(req.text) > MAX_TEXT_LENGTH:
        # Log warning but proceed with truncated text
        print(f"[TTS] Text truncated from {len(req.text)} to {MAX_TEXT_LENGTH} chars")
    
    try:
        filename = f"{req.symbol}_{req.moment_id}_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(MEDIA_DIR, filename)

        # Simple persona tweak: slightly slower, clear pronunciation
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(filepath)

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

