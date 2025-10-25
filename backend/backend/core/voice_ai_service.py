"""
Voice AI Service for RichesReach
Handles natural text-to-speech synthesis using Coqui TTS
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio
import aiofiles
from django.conf import settings

logger = logging.getLogger(__name__)

class VoiceAIService:
    """Service for natural voice synthesis using Coqui TTS"""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.model_path = getattr(settings, 'TTS_MODEL_PATH', 'models/xtts_v2')
        self.audio_output_dir = getattr(settings, 'TTS_AUDIO_OUTPUT_DIR', 'media/tts_audio')
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure audio output directory exists"""
        Path(self.audio_output_dir).mkdir(parents=True, exist_ok=True)
    
    async def load_model(self):
        """Load the TTS model asynchronously"""
        try:
            # Import TTS here to avoid import errors if not installed
            from TTS.api import TTS
            
            # Load XTTS-v2 model for natural speech
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            self.model_loaded = True
            logger.info("✅ TTS model loaded successfully")
            
        except ImportError:
            logger.warning("⚠️ TTS library not installed. Install with: pip install TTS")
            self.model_loaded = False
        except Exception as e:
            logger.error(f"❌ Failed to load TTS model: {e}")
            self.model_loaded = False
    
    async def synthesize_speech(
        self, 
        text: str, 
        voice: str = "default",
        speed: float = 1.0,
        emotion: str = "neutral"
    ) -> Optional[str]:
        """
        Synthesize natural speech from text
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (default, finance_expert, etc.)
            speed: Speech speed (0.5-2.0)
            emotion: Emotion tone (neutral, confident, friendly)
        
        Returns:
            Path to generated audio file or None if failed
        """
        if not self.model_loaded:
            await self.load_model()
        
        if not self.model_loaded:
            logger.error("❌ TTS model not loaded, cannot synthesize speech")
            return None
        
        try:
            # Clean and prepare text for finance domain
            cleaned_text = self._prepare_finance_text(text)
            
            # Generate unique filename
            import uuid
            audio_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
            audio_path = os.path.join(self.audio_output_dir, audio_filename)
            
            # Synthesize speech with natural parameters
            synthesis_params = {
                "speed": speed,
                "emotion": emotion,
                "language": "en"
            }
            
            # Use XTTS for natural speech generation
            self.model.tts_to_file(
                text=cleaned_text,
                speaker_wav=self._get_voice_sample(voice),
                language="en",
                file_path=audio_path,
                **synthesis_params
            )
            
            logger.info(f"✅ Generated TTS audio: {audio_filename}")
            return audio_path
            
        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            return None
    
    def _prepare_finance_text(self, text: str) -> str:
        """Prepare text for natural finance speech"""
        # Add natural pauses and emphasis for finance terms
        finance_replacements = {
            "portfolio": "port-folio",
            "yield": "yield",
            "dividend": "div-i-dend",
            "volatility": "vol-a-til-ity",
            "diversification": "di-ver-si-fi-ca-tion",
            "ROI": "R-O-I",
            "APY": "A-P-Y",
            "ETF": "E-T-F",
            "IRA": "I-R-A",
            "401k": "four-oh-one-k",
            "NASDAQ": "NAS-DAQ",
            "S&P 500": "S-and-P five-hundred",
            "Dow Jones": "Dow Jones",
            "Federal Reserve": "Federal Reserve",
            "inflation": "in-fla-tion",
            "recession": "re-ces-sion",
            "bull market": "bull market",
            "bear market": "bear market",
        }
        
        # Apply replacements
        for term, pronunciation in finance_replacements.items():
            text = text.replace(term, pronunciation)
        
        # Add natural pauses after sentences
        text = text.replace(".", ". ")
        text = text.replace("!", "! ")
        text = text.replace("?", "? ")
        
        return text.strip()
    
    def _get_voice_sample(self, voice: str) -> str:
        """Get voice sample path for the specified voice"""
        voice_samples = {
            "default": "voices/default_finance_voice.wav",
            "finance_expert": "voices/finance_expert_voice.wav",
            "friendly_advisor": "voices/friendly_advisor_voice.wav",
            "confident_analyst": "voices/confident_analyst_voice.wav",
        }
        
        voice_path = voice_samples.get(voice, voice_samples["default"])
        full_path = os.path.join(settings.BASE_DIR, voice_path)
        
        # Return default if voice file doesn't exist
        if not os.path.exists(full_path):
            logger.warning(f"⚠️ Voice sample not found: {voice_path}, using default")
            return voice_samples["default"]
        
        return full_path
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices"""
        return {
            "default": {
                "name": "Default Finance Voice",
                "description": "Professional, neutral tone for general finance content",
                "emotions": ["neutral", "confident"]
            },
            "finance_expert": {
                "name": "Finance Expert",
                "description": "Authoritative voice for market analysis and insights",
                "emotions": ["confident", "analytical"]
            },
            "friendly_advisor": {
                "name": "Friendly Advisor",
                "description": "Warm, approachable voice for personal finance advice",
                "emotions": ["friendly", "encouraging"]
            },
            "confident_analyst": {
                "name": "Confident Analyst",
                "description": "Strong, decisive voice for trading recommendations",
                "emotions": ["confident", "decisive"]
            }
        }
    
    async def cleanup_old_audio(self, max_age_hours: int = 24):
        """Clean up old audio files to save disk space"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.audio_output_dir):
                if filename.startswith('tts_'):
                    file_path = os.path.join(self.audio_output_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"🗑️ Cleaned up old TTS file: {filename}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old audio files: {e}")

# Global instance
voice_ai_service = VoiceAIService()
