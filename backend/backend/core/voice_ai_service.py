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
            import torch
            
            # Fix PyTorch weights_only issue for TTS models
            torch.serialization.add_safe_globals([
                'TTS.tts.configs.xtts_config.XttsConfig',
                'TTS.tts.models.xtts.Xtts',
                'TTS.tts.utils.manage.ModelManager',
            ])
            
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
            
            # Enhanced synthesis parameters for natural speech
            synthesis_params = self._get_natural_synthesis_params(voice, speed, emotion)
            
            # Use XTTS for natural speech generation with enhanced parameters
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
        """Prepare text for natural finance speech with enhanced pronunciation"""
        # Enhanced finance term pronunciations for natural speech
        finance_replacements = {
            # Basic terms
            "portfolio": "port-folio",
            "yield": "yield",
            "dividend": "div-i-dend",
            "volatility": "vol-a-til-ity",
            "diversification": "di-ver-si-fi-ca-tion",
            "liquidity": "li-quid-ity",
            "leverage": "lev-er-age",
            "equity": "eq-ui-ty",
            "bond": "bond",
            "stock": "stock",
            "share": "share",
            "market": "mar-ket",
            "trading": "trad-ing",
            "investment": "in-vest-ment",
            "return": "re-turn",
            "profit": "prof-it",
            "loss": "loss",
            "gain": "gain",
            "risk": "risk",
            "asset": "as-set",
            "liability": "li-a-bil-ity",
            "revenue": "rev-e-nue",
            "expense": "ex-pense",
            "income": "in-come",
            "capital": "cap-i-tal",
            "interest": "in-ter-est",
            "principal": "prin-ci-pal",
            "maturity": "ma-tur-ity",
            "coupon": "cou-pon",
            "premium": "pre-mi-um",
            "discount": "dis-count",
            "spread": "spread",
            "margin": "mar-gin",
            "collateral": "col-lat-er-al",
            "derivative": "de-riv-a-tive",
            "futures": "fu-tures",
            "options": "op-tions",
            "hedge": "hedge",
            "arbitrage": "ar-bi-trage",
            "speculation": "spec-u-la-tion",
            "analysis": "a-nal-y-sis",
            "valuation": "val-u-a-tion",
            "earnings": "earn-ings",
            "revenue": "rev-e-nue",
            "cash flow": "cash flow",
            "balance sheet": "bal-ance sheet",
            "income statement": "in-come state-ment",
            "P&L": "P-and-L",
            "EBITDA": "E-B-I-T-D-A",
            "EPS": "E-P-S",
            "P/E ratio": "P-E ra-tio",
            "ROI": "R-O-I",
            "ROE": "R-O-E",
            "ROA": "R-O-A",
            "APY": "A-P-Y",
            "APR": "A-P-R",
            "CD": "C-D",
            "IRA": "I-R-A",
            "401k": "four-oh-one-k",
            "403b": "four-oh-three-b",
            "Roth": "Roth",
            "Traditional": "Tra-di-tion-al",
            "ETF": "E-T-F",
            "mutual fund": "mu-tu-al fund",
            "index fund": "in-dex fund",
            "hedge fund": "hedge fund",
            "private equity": "pri-vate eq-ui-ty",
            "venture capital": "ven-ture cap-i-tal",
            "IPO": "I-P-O",
            "M&A": "M-and-A",
            "merger": "mer-ger",
            "acquisition": "ac-qui-si-tion",
            "spin-off": "spin-off",
            "dividend": "div-i-dend",
            "stock split": "stock split",
            "buyback": "buy-back",
            "shareholder": "share-hold-er",
            "stakeholder": "stake-hold-er",
            "board": "board",
            "CEO": "C-E-O",
            "CFO": "C-F-O",
            "CTO": "C-T-O",
            "COO": "C-O-O",
            "NASDAQ": "NAS-DAQ",
            "NYSE": "N-Y-S-E",
            "S&P 500": "S-and-P five-hundred",
            "Dow Jones": "Dow Jones",
            "Russell 2000": "Rus-sell two-thou-sand",
            "Federal Reserve": "Fed-er-al Re-serve",
            "Fed": "Fed",
            "FOMC": "F-O-M-C",
            "inflation": "in-fla-tion",
            "deflation": "de-fla-tion",
            "stagflation": "stag-fla-tion",
            "recession": "re-ces-sion",
            "depression": "de-pres-sion",
            "recovery": "re-cov-er-y",
            "expansion": "ex-pan-sion",
            "contraction": "con-trac-tion",
            "bull market": "bull mar-ket",
            "bear market": "bear mar-ket",
            "correction": "cor-rec-tion",
            "crash": "crash",
            "rally": "ral-ly",
            "volatility": "vol-a-til-ity",
            "VIX": "V-I-X",
            "beta": "be-ta",
            "alpha": "al-pha",
            "gamma": "gam-ma",
            "delta": "del-ta",
            "theta": "the-ta",
            "vega": "ve-ga",
            "rho": "rho",
            "Sharpe ratio": "Sharpe ra-tio",
            "Sortino ratio": "Sor-ti-no ra-tio",
            "Jensen's alpha": "Jen-sen's al-pha",
            "Treynor ratio": "Trey-nor ra-tio",
            "Information ratio": "In-for-ma-tion ra-tio",
            "Calmar ratio": "Cal-mar ra-tio",
            "Sterling ratio": "Ster-ling ra-tio",
            "Burke ratio": "Burke ra-tio",
            "Kappa ratio": "Kap-pa ra-tio",
            "Omega ratio": "O-me-ga ra-tio",
            "Gain-to-Pain ratio": "Gain-to-Pain ra-tio",
            "Ulcer Index": "Ul-cer In-dex",
            "Maximum Drawdown": "Max-i-mum Draw-down",
            "Value at Risk": "Val-ue at Risk",
            "VaR": "V-a-R",
            "Expected Shortfall": "Ex-pect-ed Short-fall",
            "Conditional Value at Risk": "Con-di-tion-al Val-ue at Risk",
            "CVaR": "C-V-a-R",
            "Monte Carlo": "Mon-te Car-lo",
            "Black-Scholes": "Black-Scho-les",
            "Binomial": "Bi-no-mi-al",
            "trinomial": "tri-no-mi-al",
            "lattice": "lat-tice",
            "finite difference": "fi-nite dif-fer-ence",
            "finite element": "fi-nite el-e-ment",
            "stochastic": "sto-chas-tic",
            "deterministic": "de-ter-min-is-tic",
            "regression": "re-gres-sion",
            "correlation": "cor-re-la-tion",
            "covariance": "co-var-i-ance",
            "autocorrelation": "au-to-cor-re-la-tion",
            "heteroscedasticity": "het-er-o-sce-das-tic-i-ty",
            "homoscedasticity": "ho-mo-sce-das-tic-i-ty",
            "stationarity": "sta-tion-ar-i-ty",
            "cointegration": "co-in-te-gra-tion",
            "unit root": "u-nit root",
            "Dickey-Fuller": "Dick-ey-Ful-ler",
            "Augmented Dickey-Fuller": "Au-gment-ed Dick-ey-Ful-ler",
            "Phillips-Perron": "Phil-lips-Per-ron",
            "KPSS": "K-P-S-S",
            "Johansen": "Jo-han-sen",
            "Engle-Granger": "En-gle-Gran-ger",
            "VAR": "V-A-R",
            "VECM": "V-E-C-M",
            "GARCH": "G-A-R-C-H",
            "EGARCH": "E-G-A-R-C-H",
            "GJR-GARCH": "G-J-R-G-A-R-C-H",
            "APARCH": "A-P-A-R-C-H",
            "FIGARCH": "F-I-G-A-R-C-H",
            "FIEGARCH": "F-I-E-G-A-R-C-H",
            "HYGARCH": "H-Y-G-A-R-C-H",
            "CGARCH": "C-G-A-R-C-H",
            "TGARCH": "T-G-A-R-C-H",
            "NGARCH": "N-G-A-R-C-H",
            "AVGARCH": "A-V-G-A-R-C-H",
            "NAGARCH": "N-A-G-A-R-C-H",
            "APGARCH": "A-P-G-A-R-C-H",
            "GQARCH": "G-Q-A-R-C-H",
            "GOGARCH": "G-O-G-A-R-C-H",
            "GO-GARCH": "G-O-G-A-R-C-H",
            "DCC-GARCH": "D-C-C-G-A-R-C-H",
            "BEKK": "B-E-K-K",
            "CCC": "C-C-C",
            "DCC": "D-C-C",
            "ADCC": "A-D-C-C",
            "FDCC": "F-D-C-C",
            "RCC": "R-C-C",
            "GOF": "G-O-F",
            "GO-GARCH": "G-O-G-A-R-C-H",
            "ICA": "I-C-A",
            "PCA": "P-C-A",
            "FA": "F-A",
            "CCA": "C-C-A",
            "PLS": "P-L-S",
            "PCR": "P-C-R",
            "Ridge": "Ridge",
            "Lasso": "Las-so",
            "Elastic Net": "E-las-tic Net",
            "Random Forest": "Ran-dom For-est",
            "Gradient Boosting": "Gra-di-ent Boost-ing",
            "XGBoost": "X-G-Boost",
            "LightGBM": "Light-G-B-M",
            "CatBoost": "Cat-Boost",
            "AdaBoost": "A-da-Boost",
            "SVM": "S-V-M",
            "Support Vector Machine": "Sup-port Vec-tor Ma-chine",
            "KNN": "K-N-N",
            "k-Nearest Neighbors": "k-Near-est Neigh-bors",
            "Naive Bayes": "Na-ive Bayes",
            "Logistic Regression": "Lo-gis-tic Re-gres-sion",
            "Linear Regression": "Lin-ear Re-gres-sion",
            "Polynomial Regression": "Pol-y-no-mi-al Re-gres-sion",
            "Ridge Regression": "Ridge Re-gres-sion",
            "Lasso Regression": "Las-so Re-gres-sion",
            "Elastic Net Regression": "E-las-tic Net Re-gres-sion",
            "Decision Tree": "De-ci-sion Tree",
            "Random Forest": "Ran-dom For-est",
            "Extra Trees": "Ex-tra Trees",
            "Gradient Boosting": "Gra-di-ent Boost-ing",
            "XGBoost": "X-G-Boost",
            "LightGBM": "Light-G-B-M",
            "CatBoost": "Cat-Boost",
            "AdaBoost": "A-da-Boost",
            "Neural Network": "Neu-ral Net-work",
            "Deep Learning": "Deep Learn-ing",
            "CNN": "C-N-N",
            "Convolutional Neural Network": "Con-vo-lu-tion-al Neu-ral Net-work",
            "RNN": "R-N-N",
            "Recurrent Neural Network": "Re-cur-rent Neu-ral Net-work",
            "LSTM": "L-S-T-M",
            "Long Short-Term Memory": "Long Short-Term Mem-o-ry",
            "GRU": "G-R-U",
            "Gated Recurrent Unit": "Gat-ed Re-cur-rent Unit",
            "Transformer": "Trans-form-er",
            "BERT": "B-E-R-T",
            "GPT": "G-P-T",
            "GPT-2": "G-P-T-two",
            "GPT-3": "G-P-T-three",
            "GPT-4": "G-P-T-four",
            "T5": "T-five",
            "RoBERTa": "Ro-B-E-R-T-a",
            "ALBERT": "A-L-B-E-R-T",
            "ELECTRA": "E-L-E-C-T-R-A",
            "DeBERTa": "De-B-E-R-T-a",
            "XLNet": "X-L-Net",
            "BART": "B-A-R-T",
            "T5": "T-five",
            "UL2": "U-L-two",
            "PaLM": "P-a-L-M",
            "LaMDA": "La-M-D-A",
            "Chinchilla": "Chin-chil-la",
            "Gopher": "Go-pher",
            "Megatron": "Meg-a-tron",
            "Switch Transformer": "Switch Trans-form-er",
            "Mixture of Experts": "Mix-ture of Ex-perts",
            "MoE": "M-o-E",
            "Sparse MoE": "Sparse M-o-E",
            "Dense MoE": "Dense M-o-E",
            "Switch MoE": "Switch M-o-E",
            "GLaM": "G-La-M",
            "PaLM": "P-a-L-M",
            "LaMDA": "La-M-D-A",
            "Chinchilla": "Chin-chil-la",
            "Gopher": "Go-pher",
            "Megatron": "Meg-a-tron",
            "Switch Transformer": "Switch Trans-form-er",
            "Mixture of Experts": "Mix-ture of Ex-perts",
            "MoE": "M-o-E",
            "Sparse MoE": "Sparse M-o-E",
            "Dense MoE": "Dense M-o-E",
            "Switch MoE": "Switch M-o-E",
            "GLaM": "G-La-M",
        }
        
        # Apply replacements with case-insensitive matching
        import re
        for term, pronunciation in finance_replacements.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(term) + r'\b'
            text = re.sub(pattern, pronunciation, text, flags=re.IGNORECASE)
        
        # Add natural pauses and emphasis
        text = self._add_natural_pauses(text)
        text = self._add_emphasis_markers(text)
        
        return text.strip()
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pauses to improve speech flow"""
        # Add pauses after sentences
        text = re.sub(r'\.(?!\s)', '. ', text)
        text = re.sub(r'!(?!\s)', '! ', text)
        text = re.sub(r'\?(?!\s)', '? ', text)
        
        # Add slight pauses after commas
        text = re.sub(r',(?!\s)', ', ', text)
        
        # Add pauses after colons and semicolons
        text = re.sub(r':(?!\s)', ': ', text)
        text = re.sub(r';(?!\s)', '; ', text)
        
        # Add emphasis pauses before important financial terms
        emphasis_terms = [
            'portfolio', 'yield', 'dividend', 'volatility', 'diversification',
            'ROI', 'APY', 'ETF', 'IRA', '401k', 'NASDAQ', 'S&P 500',
            'Federal Reserve', 'inflation', 'recession', 'bull market', 'bear market'
        ]
        
        for term in emphasis_terms:
            pattern = r'\b' + re.escape(term) + r'\b'
            text = re.sub(pattern, f' {term} ', text, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _add_emphasis_markers(self, text: str) -> str:
        """Add emphasis markers for important financial concepts"""
        # Add emphasis to key financial metrics
        emphasis_patterns = [
            (r'\b(\d+\.?\d*%)\b', r'<emphasis level="strong">\1</emphasis>'),
            (r'\b(\$\d+(?:,\d{3})*(?:\.\d{2})?)\b', r'<emphasis level="moderate">\1</emphasis>'),
            (r'\b(ROI|APY|EPS|P/E|ROE|ROA)\b', r'<emphasis level="strong">\1</emphasis>'),
            (r'\b(NASDAQ|NYSE|S&P 500|Dow Jones)\b', r'<emphasis level="moderate">\1</emphasis>'),
        ]
        
        for pattern, replacement in emphasis_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _get_natural_synthesis_params(self, voice: str, speed: float, emotion: str) -> Dict[str, Any]:
        """Get optimized synthesis parameters for natural speech"""
        # Base parameters for natural speech
        base_params = {
            "speed": speed,
            "language": "en",
            "use_speaker_embedding": True,
            "use_gst": True,  # Global Style Tokens for emotion
        }
        
        # Voice-specific parameters for naturalness
        voice_params = {
            "default": {
                "temperature": 0.7,
                "length_penalty": 1.0,
                "repetition_penalty": 1.1,
                "top_k": 50,
                "top_p": 0.9,
                "num_beams": 4,
                "early_stopping": True,
            },
            "finance_expert": {
                "temperature": 0.6,
                "length_penalty": 1.1,
                "repetition_penalty": 1.05,
                "top_k": 40,
                "top_p": 0.85,
                "num_beams": 6,
                "early_stopping": True,
            },
            "friendly_advisor": {
                "temperature": 0.8,
                "length_penalty": 0.9,
                "repetition_penalty": 1.15,
                "top_k": 60,
                "top_p": 0.95,
                "num_beams": 3,
                "early_stopping": True,
            },
            "confident_analyst": {
                "temperature": 0.5,
                "length_penalty": 1.2,
                "repetition_penalty": 1.0,
                "top_k": 30,
                "top_p": 0.8,
                "num_beams": 8,
                "early_stopping": True,
            }
        }
        
        # Emotion-specific adjustments
        emotion_adjustments = {
            "neutral": {
                "temperature": 0.0,
                "emotion_weight": 0.5,
            },
            "confident": {
                "temperature": -0.1,
                "emotion_weight": 0.8,
                "pitch_shift": 0.1,
            },
            "friendly": {
                "temperature": 0.1,
                "emotion_weight": 0.7,
                "pitch_shift": -0.05,
            },
            "analytical": {
                "temperature": -0.2,
                "emotion_weight": 0.6,
                "pitch_shift": 0.05,
            },
            "encouraging": {
                "temperature": 0.2,
                "emotion_weight": 0.9,
                "pitch_shift": -0.1,
            }
        }
        
        # Combine parameters
        params = base_params.copy()
        params.update(voice_params.get(voice, voice_params["default"]))
        
        # Apply emotion adjustments
        emotion_params = emotion_adjustments.get(emotion, emotion_adjustments["neutral"])
        for key, value in emotion_params.items():
            if key in params:
                params[key] += value
            else:
                params[key] = value
        
        # Speed-based adjustments for naturalness
        if speed < 0.8:
            params["temperature"] += 0.1
            params["length_penalty"] += 0.1
        elif speed > 1.3:
            params["temperature"] -= 0.1
            params["length_penalty"] -= 0.1
        
        # Ensure parameters are within valid ranges
        params["temperature"] = max(0.0, min(1.0, params["temperature"]))
        params["length_penalty"] = max(0.5, min(2.0, params["length_penalty"]))
        params["repetition_penalty"] = max(1.0, min(1.5, params["repetition_penalty"]))
        params["top_k"] = max(10, min(100, params["top_k"]))
        params["top_p"] = max(0.5, min(1.0, params["top_p"]))
        params["num_beams"] = max(1, min(10, params["num_beams"]))
        
        return params
    
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
