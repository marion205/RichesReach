#!/bin/bash
# Start ASGI server for RichesReach async AI endpoints
# Usage: ./START_ASGI_SERVER.sh [--reload] [--port PORT] [--workers N]

cd "$(dirname "$0")"

# Defaults
RELOAD=""
PORT=8000
WORKERS=4

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --reload)
            RELOAD="--reload"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--reload] [--port PORT] [--workers N]"
            exit 1
            ;;
    esac
done

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found. Install with: pip install uvicorn[standard]"
    exit 1
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. AI features will use fallback."
fi

echo "🚀 Starting ASGI server..."
echo "   Port: $PORT"
if [ -n "$RELOAD" ]; then
    echo "   Mode: Development (auto-reload)"
else
    echo "   Workers: $WORKERS"
    echo "   Mode: Production"
fi
echo ""
echo "📡 Endpoints:"
echo "   GET  http://localhost:$PORT/api/ai/health/"
echo "   POST http://localhost:$PORT/api/ai/chat/"
echo "   POST http://localhost:$PORT/api/ai/chat/stream/"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start server
if [ -n "$RELOAD" ]; then
    uvicorn richesreach.asgi:application --host 0.0.0.0 --port "$PORT" $RELOAD
else
    uvicorn richesreach.asgi:application --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
fi

