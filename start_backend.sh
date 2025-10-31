#!/bin/bash
# Quick script to start the backend server

cd "$(dirname "$0")/backend" || exit 1

echo "🚀 Starting RichesReach Backend Server..."
echo "📡 Will be available at http://localhost:8000"
echo "📡 And at http://192.168.1.236:8000 (for mobile devices)"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

# Start the server
python -m uvicorn backend.final_complete_server:app --host 0.0.0.0 --port 8000 --reload

