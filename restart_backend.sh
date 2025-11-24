#!/bin/bash
# Restart backend server to pick up new endpoints

echo "🔄 Restarting backend server..."

# Find and kill existing process
PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$PID" ]; then
  echo "Stopping existing server (PID: $PID)..."
  kill $PID
  sleep 2
  # Force kill if still running
  if ps -p $PID > /dev/null 2>&1; then
    kill -9 $PID
  fi
fi

# Start new server
cd deployment_package/backend
source ../../venv/bin/activate

echo "Starting server with new endpoints..."
echo "📡 Server will be available at http://0.0.0.0:8000"
echo "📡 PDF endpoint: POST /api/tax/report/pdf"
echo ""
echo "Press Ctrl+C to stop"

# Use uvicorn with auto-reload for development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
