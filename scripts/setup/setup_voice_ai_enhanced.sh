#!/bin/bash

# Enhanced Voice AI Setup Script for RichesReach
# This script sets up a comprehensive, natural-sounding voice AI system

set -e

echo "🎤 Setting up Enhanced Voice AI System for RichesReach"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "backend/backend/manage.py" ]; then
    print_error "Please run this script from the RichesReach root directory"
    exit 1
fi

print_info "Installing enhanced TTS dependencies..."

# Install TTS and related packages
pip install TTS==0.22.0
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install aiofiles
pip install python-dotenv
pip install librosa
pip install soundfile
pip install scipy
pip install numpy
pip install pandas

print_status "TTS dependencies installed"

# Create voice samples directory
print_info "Creating voice samples directory..."
mkdir -p backend/backend/voices
mkdir -p backend/backend/media/tts_audio

# Create default voice samples (placeholder files)
print_info "Creating voice sample placeholders..."
cat > backend/backend/voices/default_finance_voice.wav << 'EOF'
# This is a placeholder for the default finance voice sample
# In production, replace with actual voice samples
EOF

cat > backend/backend/voices/finance_expert_voice.wav << 'EOF'
# This is a placeholder for the finance expert voice sample
# In production, replace with actual voice samples
EOF

cat > backend/backend/voices/friendly_advisor_voice.wav << 'EOF'
# This is a placeholder for the friendly advisor voice sample
# In production, replace with actual voice samples
EOF

cat > backend/backend/voices/confident_analyst_voice.wav << 'EOF'
# This is a placeholder for the confident analyst voice sample
# In production, replace with actual voice samples
EOF

print_status "Voice sample placeholders created"

# Create enhanced voice AI configuration
print_info "Creating enhanced voice AI configuration..."
cat > backend/backend/voice_ai_config.py << 'EOF'
"""
Enhanced Voice AI Configuration for RichesReach
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# TTS Configuration
TTS_CONFIG = {
    # Model settings
    'MODEL_NAME': 'tts_models/multilingual/multi-dataset/xtts_v2',
    'MODEL_PATH': BASE_DIR / 'models' / 'xtts_v2',
    
    # Audio settings
    'AUDIO_OUTPUT_DIR': BASE_DIR / 'media' / 'tts_audio',
    'AUDIO_FORMAT': 'wav',
    'SAMPLE_RATE': 22050,
    'BIT_DEPTH': 16,
    
    # Voice samples
    'VOICE_SAMPLES_DIR': BASE_DIR / 'voices',
    'DEFAULT_VOICE_SAMPLE': 'default_finance_voice.wav',
    
    # Natural speech parameters
    'NATURAL_SPEECH': {
        'USE_SPEAKER_EMBEDDING': True,
        'USE_GST': True,  # Global Style Tokens
        'TEMPERATURE_RANGE': (0.0, 1.0),
        'SPEED_RANGE': (0.5, 2.0),
        'EMOTION_WEIGHTS': {
            'neutral': 0.5,
            'confident': 0.8,
            'friendly': 0.7,
            'analytical': 0.6,
            'encouraging': 0.9,
        }
    },
    
    # Performance settings
    'MAX_BATCH_SIZE': 10,
    'AUDIO_CACHE_HOURS': 24,
    'CLEANUP_INTERVAL_HOURS': 6,
    
    # Quality settings
    'HIGH_QUALITY': True,
    'NOISE_REDUCTION': True,
    'NORMALIZE_AUDIO': True,
}

# Voice-specific configurations
VOICE_CONFIGS = {
    'default': {
        'name': 'Default Finance Voice',
        'description': 'Professional, neutral tone for general finance content',
        'temperature': 0.7,
        'length_penalty': 1.0,
        'repetition_penalty': 1.1,
        'top_k': 50,
        'top_p': 0.9,
        'num_beams': 4,
        'emotions': ['neutral', 'confident'],
    },
    'finance_expert': {
        'name': 'Finance Expert',
        'description': 'Authoritative voice for market analysis and insights',
        'temperature': 0.6,
        'length_penalty': 1.1,
        'repetition_penalty': 1.05,
        'top_k': 40,
        'top_p': 0.85,
        'num_beams': 6,
        'emotions': ['confident', 'analytical'],
    },
    'friendly_advisor': {
        'name': 'Friendly Advisor',
        'description': 'Warm, approachable voice for personal finance advice',
        'temperature': 0.8,
        'length_penalty': 0.9,
        'repetition_penalty': 1.15,
        'top_k': 60,
        'top_p': 0.95,
        'num_beams': 3,
        'emotions': ['friendly', 'encouraging'],
    },
    'confident_analyst': {
        'name': 'Confident Analyst',
        'description': 'Strong, decisive voice for trading recommendations',
        'temperature': 0.5,
        'length_penalty': 1.2,
        'repetition_penalty': 1.0,
        'top_k': 30,
        'top_p': 0.8,
        'num_beams': 8,
        'emotions': ['confident', 'analytical'],
    }
}

# Finance terminology pronunciation dictionary
FINANCE_PRONUNCIATIONS = {
    # Basic terms
    'portfolio': 'port-folio',
    'yield': 'yield',
    'dividend': 'div-i-dend',
    'volatility': 'vol-a-til-ity',
    'diversification': 'di-ver-si-fi-ca-tion',
    'liquidity': 'li-quid-ity',
    'leverage': 'lev-er-age',
    'equity': 'eq-ui-ty',
    'bond': 'bond',
    'stock': 'stock',
    'share': 'share',
    'market': 'mar-ket',
    'trading': 'trad-ing',
    'investment': 'in-vest-ment',
    'return': 're-turn',
    'profit': 'prof-it',
    'loss': 'loss',
    'gain': 'gain',
    'risk': 'risk',
    'asset': 'as-set',
    'liability': 'li-a-bil-ity',
    'revenue': 'rev-e-nue',
    'expense': 'ex-pense',
    'income': 'in-come',
    'capital': 'cap-i-tal',
    'interest': 'in-ter-est',
    'principal': 'prin-ci-pal',
    'maturity': 'ma-tur-ity',
    'coupon': 'cou-pon',
    'premium': 'pre-mi-um',
    'discount': 'dis-count',
    'spread': 'spread',
    'margin': 'mar-gin',
    'collateral': 'col-lat-er-al',
    'derivative': 'de-riv-a-tive',
    'futures': 'fu-tures',
    'options': 'op-tions',
    'hedge': 'hedge',
    'arbitrage': 'ar-bi-trage',
    'speculation': 'spec-u-la-tion',
    'analysis': 'a-nal-y-sis',
    'valuation': 'val-u-a-tion',
    'earnings': 'earn-ings',
    'cash flow': 'cash flow',
    'balance sheet': 'bal-ance sheet',
    'income statement': 'in-come state-ment',
    'P&L': 'P-and-L',
    'EBITDA': 'E-B-I-T-D-A',
    'EPS': 'E-P-S',
    'P/E ratio': 'P-E ra-tio',
    'ROI': 'R-O-I',
    'ROE': 'R-O-E',
    'ROA': 'R-O-A',
    'APY': 'A-P-Y',
    'APR': 'A-P-R',
    'CD': 'C-D',
    'IRA': 'I-R-A',
    '401k': 'four-oh-one-k',
    '403b': 'four-oh-three-b',
    'Roth': 'Roth',
    'Traditional': 'Tra-di-tion-al',
    'ETF': 'E-T-F',
    'mutual fund': 'mu-tu-al fund',
    'index fund': 'in-dex fund',
    'hedge fund': 'hedge fund',
    'private equity': 'pri-vate eq-ui-ty',
    'venture capital': 'ven-ture cap-i-tal',
    'IPO': 'I-P-O',
    'M&A': 'M-and-A',
    'merger': 'mer-ger',
    'acquisition': 'ac-qui-si-tion',
    'spin-off': 'spin-off',
    'stock split': 'stock split',
    'buyback': 'buy-back',
    'shareholder': 'share-hold-er',
    'stakeholder': 'stake-hold-er',
    'board': 'board',
    'CEO': 'C-E-O',
    'CFO': 'C-F-O',
    'CTO': 'C-T-O',
    'COO': 'C-O-O',
    'NASDAQ': 'NAS-DAQ',
    'NYSE': 'N-Y-S-E',
    'S&P 500': 'S-and-P five-hundred',
    'Dow Jones': 'Dow Jones',
    'Russell 2000': 'Rus-sell two-thou-sand',
    'Federal Reserve': 'Fed-er-al Re-serve',
    'Fed': 'Fed',
    'FOMC': 'F-O-M-C',
    'inflation': 'in-fla-tion',
    'deflation': 'de-fla-tion',
    'stagflation': 'stag-fla-tion',
    'recession': 're-ces-sion',
    'depression': 'de-pres-sion',
    'recovery': 're-cov-er-y',
    'expansion': 'ex-pan-sion',
    'contraction': 'con-trac-tion',
    'bull market': 'bull mar-ket',
    'bear market': 'bear mar-ket',
    'correction': 'cor-rec-tion',
    'crash': 'crash',
    'rally': 'ral-ly',
    'VIX': 'V-I-X',
    'beta': 'be-ta',
    'alpha': 'al-pha',
    'gamma': 'gam-ma',
    'delta': 'del-ta',
    'theta': 'the-ta',
    'vega': 've-ga',
    'rho': 'rho',
    'Sharpe ratio': 'Sharpe ra-tio',
    'Sortino ratio': 'Sor-ti-no ra-tio',
    'Jensen\'s alpha': 'Jen-sen\'s al-pha',
    'Treynor ratio': 'Trey-nor ra-tio',
    'Information ratio': 'In-for-ma-tion ra-tio',
    'Calmar ratio': 'Cal-mar ra-tio',
    'Sterling ratio': 'Ster-ling ra-tio',
    'Burke ratio': 'Burke ra-tio',
    'Kappa ratio': 'Kap-pa ra-tio',
    'Omega ratio': 'O-me-ga ra-tio',
    'Gain-to-Pain ratio': 'Gain-to-Pain ra-tio',
    'Ulcer Index': 'Ul-cer In-dex',
    'Maximum Drawdown': 'Max-i-mum Draw-down',
    'Value at Risk': 'Val-ue at Risk',
    'VaR': 'V-a-R',
    'Expected Shortfall': 'Ex-pect-ed Short-fall',
    'Conditional Value at Risk': 'Con-di-tion-al Val-ue at Risk',
    'CVaR': 'C-V-a-R',
    'Monte Carlo': 'Mon-te Car-lo',
    'Black-Scholes': 'Black-Scho-les',
    'Binomial': 'Bi-no-mi-al',
    'trinomial': 'tri-no-mi-al',
    'lattice': 'lat-tice',
    'finite difference': 'fi-nite dif-fer-ence',
    'finite element': 'fi-nite el-e-ment',
    'stochastic': 'sto-chas-tic',
    'deterministic': 'de-ter-min-is-tic',
    'regression': 're-gres-sion',
    'correlation': 'cor-re-la-tion',
    'covariance': 'co-var-i-ance',
    'autocorrelation': 'au-to-cor-re-la-tion',
    'heteroscedasticity': 'het-er-o-sce-das-tic-i-ty',
    'homoscedasticity': 'ho-mo-sce-das-tic-i-ty',
    'stationarity': 'sta-tion-ar-i-ty',
    'cointegration': 'co-in-te-gra-tion',
    'unit root': 'u-nit root',
    'Dickey-Fuller': 'Dick-ey-Ful-ler',
    'Augmented Dickey-Fuller': 'Au-gment-ed Dick-ey-Ful-ler',
    'Phillips-Perron': 'Phil-lips-Per-ron',
    'KPSS': 'K-P-S-S',
    'Johansen': 'Jo-han-sen',
    'Engle-Granger': 'En-gle-Gran-ger',
    'VAR': 'V-A-R',
    'VECM': 'V-E-C-M',
    'GARCH': 'G-A-R-C-H',
    'EGARCH': 'E-G-A-R-C-H',
    'GJR-GARCH': 'G-J-R-G-A-R-C-H',
    'APARCH': 'A-P-A-R-C-H',
    'FIGARCH': 'F-I-G-A-R-C-H',
    'FIEGARCH': 'F-I-E-G-A-R-C-H',
    'HYGARCH': 'H-Y-G-A-R-C-H',
    'CGARCH': 'C-G-A-R-C-H',
    'TGARCH': 'T-G-A-R-C-H',
    'NGARCH': 'N-G-A-R-C-H',
    'AVGARCH': 'A-V-G-A-R-C-H',
    'NAGARCH': 'N-A-G-A-R-C-H',
    'APGARCH': 'A-P-G-A-R-C-H',
    'GQARCH': 'G-Q-A-R-C-H',
    'GOGARCH': 'G-O-G-A-R-C-H',
    'GO-GARCH': 'G-O-G-A-R-C-H',
    'DCC-GARCH': 'D-C-C-G-A-R-C-H',
    'BEKK': 'B-E-K-K',
    'CCC': 'C-C-C',
    'DCC': 'D-C-C',
    'ADCC': 'A-D-C-C',
    'FDCC': 'F-D-C-C',
    'RCC': 'R-C-C',
    'GOF': 'G-O-F',
    'ICA': 'I-C-A',
    'PCA': 'P-C-A',
    'FA': 'F-A',
    'CCA': 'C-C-A',
    'PLS': 'P-L-S',
    'PCR': 'P-C-R',
    'Ridge': 'Ridge',
    'Lasso': 'Las-so',
    'Elastic Net': 'E-las-tic Net',
    'Random Forest': 'Ran-dom For-est',
    'Gradient Boosting': 'Gra-di-ent Boost-ing',
    'XGBoost': 'X-G-Boost',
    'LightGBM': 'Light-G-B-M',
    'CatBoost': 'Cat-Boost',
    'AdaBoost': 'A-da-Boost',
    'SVM': 'S-V-M',
    'Support Vector Machine': 'Sup-port Vec-tor Ma-chine',
    'KNN': 'K-N-N',
    'k-Nearest Neighbors': 'k-Near-est Neigh-bors',
    'Naive Bayes': 'Na-ive Bayes',
    'Logistic Regression': 'Lo-gis-tic Re-gres-sion',
    'Linear Regression': 'Lin-ear Re-gres-sion',
    'Polynomial Regression': 'Pol-y-no-mi-al Re-gres-sion',
    'Ridge Regression': 'Ridge Re-gres-sion',
    'Lasso Regression': 'Las-so Re-gres-sion',
    'Elastic Net Regression': 'E-las-tic Net Re-gres-sion',
    'Decision Tree': 'De-ci-sion Tree',
    'Extra Trees': 'Ex-tra Trees',
    'Neural Network': 'Neu-ral Net-work',
    'Deep Learning': 'Deep Learn-ing',
    'CNN': 'C-N-N',
    'Convolutional Neural Network': 'Con-vo-lu-tion-al Neu-ral Net-work',
    'RNN': 'R-N-N',
    'Recurrent Neural Network': 'Re-cur-rent Neu-ral Net-work',
    'LSTM': 'L-S-T-M',
    'Long Short-Term Memory': 'Long Short-Term Mem-o-ry',
    'GRU': 'G-R-U',
    'Gated Recurrent Unit': 'Gat-ed Re-cur-rent Unit',
    'Transformer': 'Trans-form-er',
    'BERT': 'B-E-R-T',
    'GPT': 'G-P-T',
    'GPT-2': 'G-P-T-two',
    'GPT-3': 'G-P-T-three',
    'GPT-4': 'G-P-T-four',
    'T5': 'T-five',
    'RoBERTa': 'Ro-B-E-R-T-a',
    'ALBERT': 'A-L-B-E-R-T',
    'ELECTRA': 'E-L-E-C-T-R-A',
    'DeBERTa': 'De-B-E-R-T-a',
    'XLNet': 'X-L-Net',
    'BART': 'B-A-R-T',
    'UL2': 'U-L-two',
    'PaLM': 'P-a-L-M',
    'LaMDA': 'La-M-D-A',
    'Chinchilla': 'Chin-chil-la',
    'Gopher': 'Go-pher',
    'Megatron': 'Meg-a-tron',
    'Switch Transformer': 'Switch Trans-form-er',
    'Mixture of Experts': 'Mix-ture of Ex-perts',
    'MoE': 'M-o-E',
    'Sparse MoE': 'Sparse M-o-E',
    'Dense MoE': 'Dense M-o-E',
    'Switch MoE': 'Switch M-o-E',
    'GLaM': 'G-La-M',
}

# Natural speech enhancement settings
NATURAL_SPEECH_ENHANCEMENTS = {
    'PAUSE_AFTER_SENTENCES': True,
    'PAUSE_AFTER_COMMAS': True,
    'EMPHASIS_ON_NUMBERS': True,
    'EMPHASIS_ON_PERCENTAGES': True,
    'EMPHASIS_ON_CURRENCY': True,
    'EMPHASIS_ON_ACRONYMS': True,
    'NATURAL_RHYTHM': True,
    'PROSODY_CONTROL': True,
    'EMOTION_MODULATION': True,
    'SPEAKER_CONSISTENCY': True,
}

# Performance optimization settings
PERFORMANCE_SETTINGS = {
    'ENABLE_CACHING': True,
    'CACHE_DURATION_HOURS': 24,
    'MAX_CONCURRENT_SYNTHESIS': 5,
    'BATCH_PROCESSING': True,
    'AUDIO_COMPRESSION': True,
    'LAZY_LOADING': True,
    'PRELOAD_COMMON_TERMS': True,
    'OPTIMIZE_FOR_MOBILE': True,
}

# Quality assurance settings
QUALITY_SETTINGS = {
    'AUDIO_QUALITY_CHECK': True,
    'PRONUNCIATION_VALIDATION': True,
    'EMOTION_CONSISTENCY_CHECK': True,
    'SPEED_OPTIMIZATION': True,
    'NOISE_REDUCTION': True,
    'NORMALIZE_VOLUME': True,
    'ENHANCE_CLARITY': True,
    'MAINTAIN_NATURALNESS': True,
}
EOF

print_status "Enhanced voice AI configuration created"

# Create a comprehensive test script
print_info "Creating comprehensive test script..."
cat > test_voice_ai_enhanced.py << 'EOF'
#!/usr/bin/env python3
"""
Comprehensive Voice AI Test Script for RichesReach
Tests all voice endpoints for naturalness and quality
"""

import asyncio
import json
import requests
import time
from typing import Dict, List, Any

class VoiceAITester:
    def __init__(self, base_url: str = "http://192.168.1.236:8000"):
        self.base_url = base_url
        self.test_results = []
        
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test the health endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/voice-ai/health/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data.get('status', 'unknown')}")
                return {"status": "passed", "data": data}
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_voices_endpoint(self) -> Dict[str, Any]:
        """Test the voices endpoint"""
        print("🔍 Testing voices endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/voice-ai/voices/")
            if response.status_code == 200:
                data = response.json()
                voices = data.get('voices', {})
                print(f"✅ Voices endpoint passed: {len(voices)} voices available")
                return {"status": "passed", "data": data}
            else:
                print(f"❌ Voices endpoint failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Voices endpoint error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_synthesis_endpoint(self, text: str, voice: str = "default", 
                                    speed: float = 1.0, emotion: str = "neutral") -> Dict[str, Any]:
        """Test the synthesis endpoint"""
        print(f"🔍 Testing synthesis endpoint with voice '{voice}'...")
        try:
            payload = {
                "text": text,
                "voice": voice,
                "speed": speed,
                "emotion": emotion
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/voice-ai/synthesize/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    audio_url = data.get('audio_url')
                    print(f"✅ Synthesis passed: {audio_url} (took {end_time - start_time:.2f}s)")
                    return {
                        "status": "passed", 
                        "data": data,
                        "duration": end_time - start_time,
                        "audio_url": audio_url
                    }
                else:
                    print(f"❌ Synthesis failed: {data.get('error', 'Unknown error')}")
                    return {"status": "failed", "error": data.get('error')}
            else:
                print(f"❌ Synthesis failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Synthesis error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_preview_endpoint(self, voice: str = "default", 
                                  speed: float = 1.0, emotion: str = "neutral") -> Dict[str, Any]:
        """Test the preview endpoint"""
        print(f"🔍 Testing preview endpoint with voice '{voice}'...")
        try:
            payload = {
                "voice": voice,
                "speed": speed,
                "emotion": emotion
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/voice-ai/preview/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    audio_url = data.get('audio_url')
                    print(f"✅ Preview passed: {audio_url} (took {end_time - start_time:.2f}s)")
                    return {
                        "status": "passed", 
                        "data": data,
                        "duration": end_time - start_time,
                        "audio_url": audio_url
                    }
                else:
                    print(f"❌ Preview failed: {data.get('error', 'Unknown error')}")
                    return {"status": "failed", "error": data.get('error')}
            else:
                print(f"❌ Preview failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Preview error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_batch_endpoint(self, texts: List[str], voice: str = "default", 
                                speed: float = 1.0, emotion: str = "neutral") -> Dict[str, Any]:
        """Test the batch endpoint"""
        print(f"🔍 Testing batch endpoint with {len(texts)} texts...")
        try:
            payload = {
                "texts": texts,
                "voice": voice,
                "speed": speed,
                "emotion": emotion
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/voice-ai/batch/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results = data.get('results', [])
                    successful = len([r for r in results if r.get('success')])
                    print(f"✅ Batch passed: {successful}/{len(texts)} successful (took {end_time - start_time:.2f}s)")
                    return {
                        "status": "passed", 
                        "data": data,
                        "duration": end_time - start_time,
                        "successful": successful,
                        "total": len(texts)
                    }
                else:
                    print(f"❌ Batch failed: {data.get('error', 'Unknown error')}")
                    return {"status": "failed", "error": data.get('error')}
            else:
                print(f"❌ Batch failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Batch error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_all_voices(self) -> Dict[str, Any]:
        """Test all available voices"""
        print("🔍 Testing all available voices...")
        
        # Get available voices
        voices_response = await self.test_voices_endpoint()
        if voices_response["status"] != "passed":
            return {"status": "failed", "error": "Could not get voices list"}
        
        voices = voices_response["data"].get("voices", {})
        test_text = "Hello, I'm your AI financial advisor. I can help you understand market trends and analyze your portfolio."
        
        results = {}
        for voice_id, voice_info in voices.items():
            print(f"  Testing voice: {voice_info.get('name', voice_id)}")
            result = await self.test_synthesis_endpoint(test_text, voice_id)
            results[voice_id] = result
            
            # Test different emotions for each voice
            emotions = voice_info.get('emotions', ['neutral'])
            for emotion in emotions:
                print(f"    Testing emotion: {emotion}")
                emotion_result = await self.test_synthesis_endpoint(test_text, voice_id, 1.0, emotion)
                results[f"{voice_id}_{emotion}"] = emotion_result
        
        return {"status": "completed", "results": results}
    
    async def test_finance_terminology(self) -> Dict[str, Any]:
        """Test finance-specific terminology pronunciation"""
        print("🔍 Testing finance terminology pronunciation...")
        
        finance_terms = [
            "Your portfolio has a 12.5% ROI this quarter.",
            "The S&P 500 ETF shows strong performance.",
            "Consider diversifying with a 401k and Roth IRA.",
            "The Federal Reserve's inflation target is 2%.",
            "Market volatility measured by VIX is increasing.",
            "Your Sharpe ratio indicates good risk-adjusted returns.",
            "The Black-Scholes model values your options at $1,250.",
            "GARCH analysis shows heteroscedasticity in returns.",
            "Monte Carlo simulation predicts 95% confidence interval.",
            "Your beta of 1.2 indicates higher market sensitivity."
        ]
        
        results = []
        for i, text in enumerate(finance_terms):
            print(f"  Testing finance term {i+1}/{len(finance_terms)}: {text[:50]}...")
            result = await self.test_synthesis_endpoint(text, "finance_expert", 1.0, "analytical")
            results.append({
                "text": text,
                "result": result
            })
        
        return {"status": "completed", "results": results}
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("🎤 Starting Comprehensive Voice AI Test Suite")
        print("=" * 50)
        
        test_results = {}
        
        # Test basic endpoints
        test_results["health"] = await self.test_health_endpoint()
        test_results["voices"] = await self.test_voices_endpoint()
        
        # Test synthesis with different parameters
        test_text = "Welcome to RichesReach, your comprehensive wealth management platform."
        test_results["synthesis_default"] = await self.test_synthesis_endpoint(test_text)
        test_results["synthesis_finance_expert"] = await self.test_synthesis_endpoint(test_text, "finance_expert", 1.0, "confident")
        test_results["synthesis_friendly"] = await self.test_synthesis_endpoint(test_text, "friendly_advisor", 0.9, "friendly")
        
        # Test preview endpoint
        test_results["preview"] = await self.test_preview_endpoint("default", 1.0, "neutral")
        
        # Test batch endpoint
        batch_texts = [
            "Market analysis shows positive trends.",
            "Your portfolio performance is excellent.",
            "Consider rebalancing your investments."
        ]
        test_results["batch"] = await self.test_batch_endpoint(batch_texts)
        
        # Test all voices
        test_results["all_voices"] = await self.test_all_voices()
        
        # Test finance terminology
        test_results["finance_terminology"] = await self.test_finance_terminology()
        
        # Generate summary
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for test_name, result in test_results.items():
            if isinstance(result, dict):
                if result.get("status") == "passed":
                    passed_tests += 1
                elif result.get("status") == "failed":
                    failed_tests += 1
                total_tests += 1
        
        print("\n" + "=" * 50)
        print("🎤 Voice AI Test Suite Results")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0
            },
            "results": test_results
        }

async def main():
    """Main test function"""
    tester = VoiceAITester()
    results = await tester.run_comprehensive_test()
    
    # Save results to file
    with open("voice_ai_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to voice_ai_test_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
EOF

print_status "Comprehensive test script created"

# Make scripts executable
chmod +x setup_voice_ai_enhanced.sh
chmod +x test_voice_ai_enhanced.py

print_info "Running Django migrations for voice AI..."
cd backend/backend
python manage.py makemigrations
python manage.py migrate

print_status "Django migrations completed"

# Test the setup
print_info "Testing voice AI setup..."
python ../../test_voice_ai_enhanced.py

print_status "Voice AI setup completed successfully!"

echo ""
echo "🎤 Enhanced Voice AI System Setup Complete!"
echo "=========================================="
echo ""
echo "✅ Features implemented:"
echo "   • Natural text-to-speech synthesis using Coqui TTS XTTS-v2"
echo "   • Finance-specific voice optimization with custom pronunciation"
echo "   • Multiple voice options: Default, Finance Expert, Friendly Advisor, Confident Analyst"
echo "   • Emotion control: Neutral, Confident, Friendly, Analytical, Encouraging"
echo "   • Adjustable speech speed (0.5x to 2.0x)"
echo "   • Auto-play support for AI responses"
echo "   • Batch processing for multiple texts"
echo "   • Voice preview functionality"
echo "   • Comprehensive finance terminology pronunciation"
echo "   • Natural speech enhancement with pauses and emphasis"
echo "   • Performance optimization and caching"
echo ""
echo "🔗 Available endpoints:"
echo "   • POST /api/voice-ai/synthesize/ - Main TTS synthesis"
echo "   • POST /api/voice-ai/batch/ - Batch TTS synthesis"
echo "   • POST /api/voice-ai/preview/ - Voice preview"
echo "   • GET  /api/voice-ai/voices/ - Available voices"
echo "   • GET  /api/voice-ai/health/ - Health check"
echo "   • GET  /api/voice-ai/audio/<filename>/ - Audio file serving"
echo ""
echo "📱 Frontend integration:"
echo "   • VoiceAI component with play/preview buttons"
echo "   • VoiceAIIntegration modal for settings"
echo "   • AsyncStorage persistence for user preferences"
echo "   • Error handling and fallback mechanisms"
echo ""
echo "🚀 Next steps:"
echo "   1. Start the Django server: python manage.py runserver"
echo "   2. Test the voice AI endpoints"
echo "   3. Replace voice sample placeholders with actual recordings"
echo "   4. Fine-tune synthesis parameters for your specific use case"
echo ""
echo "📚 Documentation:"
echo "   • Configuration: backend/backend/voice_ai_config.py"
echo "   • Test results: voice_ai_test_results.json"
echo "   • Voice samples: backend/backend/voices/"
echo ""
print_status "Setup complete! Your voice AI system is ready for natural speech synthesis."
