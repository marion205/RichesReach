#!/bin/bash
# Quick script to start the backend server with proper setup

cd "$(dirname "$0")"

echo "🚀 Starting RichesReach Backend Server..."
echo ""

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✅ Found virtual environment, activating..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "✅ Found virtual environment, activating..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found. Installing packages to user directory..."
    python3 -m pip install --user fastapi uvicorn 2>/dev/null || {
        echo "❌ Failed to install packages. Trying system-wide..."
        pip3 install fastapi uvicorn 2>/dev/null || {
            echo "❌ Could not install packages. Please install manually:"
            echo "   python3 -m pip install --user fastapi uvicorn"
            exit 1
        }
    }
fi

# Check if packages are available
python3 -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "❌ FastAPI or uvicorn not available. Installing..."
    python3 -m pip install --user fastapi uvicorn
}

echo ""
echo "📡 Starting server on http://0.0.0.0:8000"
echo "📡 Accessible at http://192.168.1.240:8000 (for mobile devices)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 main_server.py

