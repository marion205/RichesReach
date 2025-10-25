#!/bin/bash

# Voice AI Setup Script for RichesReach
# Installs Coqui TTS and dependencies for natural voice synthesis

set -e

echo "🎤 Setting up Voice AI for RichesReach..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "Please run this script from the Django backend directory"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

print_success "Python version check passed: $python_version"

# Install system dependencies
print_status "Installing system dependencies..."

# Update package list
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y \
        espeak-ng \
        espeak-ng-data \
        libespeak-ng1 \
        festival \
        festvox-kallpc16k \
        ffmpeg \
        sox \
        libsox-fmt-all
elif command -v brew &> /dev/null; then
    brew install espeak festival ffmpeg sox
else
    print_warning "System package manager not found. Please install espeak, festival, ffmpeg, and sox manually."
fi

# Install Python dependencies
print_status "Installing Python dependencies..."

# Install PyTorch (CPU version for compatibility)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install TTS and related packages
pip install TTS[all]
pip install librosa
pip install soundfile
pip install scipy
pip install numpy
pip install aiofiles

print_success "Python dependencies installed"

# Create necessary directories
print_status "Creating directories..."

mkdir -p media/tts_audio
mkdir -p models
mkdir -p voices

print_success "Directories created"

# Download TTS models
print_status "Downloading TTS models..."

# Download XTTS-v2 model (this may take a while)
python3 -c "
from TTS.utils.manage import ModelManager
import os

# Set model directory
model_dir = 'models'
os.makedirs(model_dir, exist_ok=True)

# Download XTTS-v2 model
print('Downloading XTTS-v2 model...')
manager = ModelManager(model_dir)
manager.download_model('tts_models/multilingual/multi-dataset/xtts_v2')
print('XTTS-v2 model downloaded successfully')
"

print_success "TTS models downloaded"

# Create sample voice files (placeholder)
print_status "Creating sample voice files..."

# Create a simple script to generate sample voices
cat > generate_sample_voices.py << 'EOF'
import os
import numpy as np
import soundfile as sf

# Create sample voice files (synthetic for now)
voices_dir = 'voices'
os.makedirs(voices_dir, exist_ok=True)

# Generate a simple sine wave as placeholder
sample_rate = 22050
duration = 1.0  # 1 second
frequency = 440  # A4 note

t = np.linspace(0, duration, int(sample_rate * duration), False)
wave = np.sin(frequency * 2 * np.pi * t) * 0.1  # Low amplitude

# Create sample voice files
voice_files = [
    'default_finance_voice.wav',
    'finance_expert_voice.wav',
    'friendly_advisor_voice.wav',
    'confident_analyst_voice.wav'
]

for voice_file in voice_files:
    file_path = os.path.join(voices_dir, voice_file)
    sf.write(file_path, wave, sample_rate)
    print(f'Created sample voice: {voice_file}')

print('Sample voice files created')
EOF

python3 generate_sample_voices.py
rm generate_sample_voices.py

print_success "Sample voice files created"

# Update Django settings
print_status "Updating Django settings..."

# Add TTS settings to settings_local.py
cat >> richesreach/settings_local.py << 'EOF'

# Voice AI Settings
TTS_MODEL_PATH = os.path.join(BASE_DIR, 'models')
TTS_AUDIO_OUTPUT_DIR = os.path.join(BASE_DIR, 'media', 'tts_audio')
TTS_ENABLED = True
TTS_DEFAULT_VOICE = 'default'
TTS_DEFAULT_SPEED = 1.0
TTS_DEFAULT_EMOTION = 'neutral'
EOF

print_success "Django settings updated"

# Create management command for testing TTS
print_status "Creating TTS test command..."

mkdir -p core/management/commands

cat > core/management/commands/test_tts.py << 'EOF'
from django.core.management.base import BaseCommand
import asyncio
from core.voice_ai_service import voice_ai_service

class Command(BaseCommand):
    help = 'Test the TTS service'

    def add_arguments(self, parser):
        parser.add_argument('--text', type=str, default='Hello, this is a test of the voice AI system.', help='Text to synthesize')
        parser.add_argument('--voice', type=str, default='default', help='Voice to use')
        parser.add_argument('--speed', type=float, default=1.0, help='Speech speed')
        parser.add_argument('--emotion', type=str, default='neutral', help='Emotion tone')

    def handle(self, *args, **options):
        text = options['text']
        voice = options['voice']
        speed = options['speed']
        emotion = options['emotion']

        self.stdout.write(f'Testing TTS with text: "{text}"')
        self.stdout.write(f'Voice: {voice}, Speed: {speed}, Emotion: {emotion}')

        async def test_tts():
            # Load model
            await voice_ai_service.load_model()
            
            if not voice_ai_service.model_loaded:
                self.stdout.write(self.style.ERROR('Failed to load TTS model'))
                return

            # Synthesize speech
            audio_path = await voice_ai_service.synthesize_speech(
                text=text,
                voice=voice,
                speed=speed,
                emotion=emotion
            )

            if audio_path:
                self.stdout.write(self.style.SUCCESS(f'Success! Audio generated: {audio_path}'))
            else:
                self.stdout.write(self.style.ERROR('Failed to generate audio'))

        asyncio.run(test_tts())
EOF

print_success "TTS test command created"

# Add voice AI URLs to main URLs
print_status "Adding voice AI URLs..."

# Check if voice AI URLs are already added
if ! grep -q "voice-ai" richesreach/urls.py; then
    # Add import
    sed -i '/from core.urls_live_streaming import urlpatterns as live_streaming_urls/a from core.urls_voice_ai import urlpatterns as voice_ai_urls' richesreach/urls.py
    
    # Add URL pattern
    sed -i '/path("api/live-streaming/", include(live_streaming_urls)),/a\    path("api/voice-ai/", include(voice_ai_urls)),' richesreach/urls.py
fi

print_success "Voice AI URLs added"

# Run migrations
print_status "Running migrations..."
python3 manage.py makemigrations
python3 manage.py migrate

print_success "Migrations completed"

# Test the installation
print_status "Testing TTS installation..."

python3 manage.py test_tts --text "Welcome to RichesReach Voice AI. Your portfolio is performing well today."

print_success "TTS test completed"

# Final instructions
print_success "Voice AI setup completed successfully!"
echo ""
echo "🎤 Voice AI is now ready to use!"
echo ""
echo "Available commands:"
echo "  python manage.py test_tts --text 'Your text here'"
echo "  python manage.py test_tts --voice finance_expert --emotion confident"
echo ""
echo "API endpoints:"
echo "  POST /api/voice-ai/synthesize/ - Generate speech"
echo "  GET  /api/voice-ai/voices/ - Get available voices"
echo "  GET  /api/voice-ai/health/ - Health check"
echo ""
echo "Next steps:"
echo "  1. Start your Django server: python manage.py runserver"
echo "  2. Test the API endpoints"
echo "  3. Integrate with your mobile app"
echo ""
echo "For custom voices, replace the sample files in the 'voices/' directory"
echo "with your own voice recordings (5-30 minutes of clean audio)."
