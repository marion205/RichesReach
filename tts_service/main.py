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


class TTSRequest(BaseModel):
    text: str
    voice: str = "wealth_oracle_v1"
    symbol: str
    moment_id: str


app = FastAPI(title="Wealth Oracle TTS")

# Allow mobile dev / web to hit this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated audio files
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@app.post("/tts")
async def synthesize(req: TTSRequest, request: Request):
    """
    Synthesize speech for the given text and return a URL to the audio file.
    """
    # In real prod, you'd:
    # - Check length limits
    # - Rate-limit per user
    # - Use a more robust TTS engine
    
    filename = f"{req.symbol}_{req.moment_id}_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(MEDIA_DIR, filename)

    # Simple persona tweak: slightly slower, clear pronunciation
    tts = gTTS(text=req.text, lang="en")
    tts.save(filepath)

    base_url = str(request.base_url).rstrip("/")
    audio_url = f"{base_url}/media/{filename}"

    return {"audio_url": audio_url}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "wealth-oracle-tts"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

