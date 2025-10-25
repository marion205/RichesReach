#!/bin/bash

# RichesReach Whisper Server Setup Script
echo "🚀 Setting up RichesReach Whisper Server..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg is not installed. Installing..."
    
    # Detect OS and install FFmpeg
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo "❌ Homebrew not found. Please install FFmpeg manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y ffmpeg
        elif command -v yum &> /dev/null; then
            sudo yum install -y ffmpeg
        else
            echo "❌ Package manager not found. Please install FFmpeg manually."
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install FFmpeg manually."
        exit 1
    fi
fi

echo "✅ FFmpeg installed"

# Setup Whisper model
echo "🎤 Setting up Whisper model..."
npm run setup-whisper

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Whisper Server Configuration
PORT=3001
WHISPER_MODEL=ggml-tiny.en-q5_0.bin
WHISPER_PATH=./whisper.cpp
MONGODB_URI=mongodb://localhost:27017/richesreach_whisper
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,exp://192.168.1.236:8081

# Optional: GPU acceleration (if NVIDIA GPU available)
# CUDA=1
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
mkdir -p uploads models

# Test the setup
echo "🧪 Testing setup..."
if [ -f "whisper.cpp/main" ]; then
    echo "✅ Whisper.cpp compiled successfully"
else
    echo "❌ Whisper.cpp compilation failed"
    exit 1
fi

if [ -f "models/ggml-tiny.en-q5_0.bin" ]; then
    echo "✅ Whisper model ready"
else
    echo "❌ Whisper model not found"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Start the server: npm start"
echo "2. Test transcription: curl -X POST http://localhost:3001/api/transcribe-audio/"
echo "3. Update your mobile app environment variables"
echo ""
echo "🔧 Configuration:"
echo "- Server will run on port 3001"
echo "- Model: ggml-tiny.en-q5_0.bin (~20MB)"
echo "- Audio formats: M4A, WAV, MP3, WebM"
echo "- Max file size: 25MB"
echo ""
echo "📱 Mobile app integration:"
echo "Add to your mobile app's env.local.dev:"
echo "EXPO_PUBLIC_WHISPER_API_URL=http://192.168.1.236:3001"
echo ""
echo "🚀 To start the server: npm start"
