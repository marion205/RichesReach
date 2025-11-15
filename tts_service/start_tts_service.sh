#!/bin/bash
# Script to start the Wealth Oracle TTS service

cd "$(dirname "$0")" || exit 1

echo "🎤 Starting Wealth Oracle TTS Service..."

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    echo "Activating parent virtual environment..."
    source ../.venv/bin/activate
else
    echo "No virtual environment found. Installing dependencies globally..."
    pip install -r requirements.txt || {
        echo "❌ Failed to install dependencies. Please install manually:"
        echo "   pip install -r requirements.txt"
        exit 1
    }
fi

# Check if dependencies are installed
python3 -c "import fastapi, uvicorn, gtts; print('Dependencies OK')" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Missing dependencies. Installing..."
    pip install -r requirements.txt || {
        echo "❌ Failed to install dependencies."
        exit 1
    }
fi

# Create media directory if it doesn't exist
mkdir -p media

echo "Starting TTS service on port 8001..."
echo "API endpoint: http://localhost:8001/tts"
echo "Health check: http://localhost:8001/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the service
python3 main.py

