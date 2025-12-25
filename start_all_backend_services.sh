#!/bin/bash
# Start ALL backend services for RichesReach

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🚀 Starting ALL RichesReach Backend Services               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check port function
check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max=30
    local count=0
    
    echo -e "${YELLOW}⏳ Waiting for $service...${NC}"
    while [ $count -lt $max ]; do
        if curl -s "http://$host:$port" >/dev/null 2>&1 || nc -z $host $port 2>/dev/null; then
            echo -e "${GREEN}✅ $service ready!${NC}"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    echo -e "${YELLOW}⚠️  $service may still be starting${NC}"
    return 1
}

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Load OpenAI API key if available
if [ -f ".env.openai" ]; then
    export OPENAI_API_KEY=$(cat .env.openai)
    echo -e "${GREEN}✓ OpenAI API key loaded${NC}"
elif [ -n "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}✓ OpenAI API key found in environment${NC}"
fi

# ============================================
# Service 1: Main Server (FastAPI + Django WSGI)
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📡 Service 1: Main Server (FastAPI + Django WSGI) - Port 8000${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 already in use (main server may already be running)${NC}"
    if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Main server already running at http://127.0.0.1:8000${NC}"
    fi
else
    if [ -f "main_server.py" ]; then
        echo "Starting main_server.py on port 8000..."
        python3 main_server.py > /tmp/main_server.log 2>&1 &
        MAIN_SERVER_PID=$!
        echo "Main server PID: $MAIN_SERVER_PID"
        sleep 3
        
        if wait_for_service localhost 8000 "Main Server"; then
            echo -e "${GREEN}✅ Main server running at http://127.0.0.1:8000${NC}"
        fi
    else
        echo -e "${RED}❌ main_server.py not found${NC}"
    fi
fi

# ============================================
# Service 2: Django ASGI Server
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📡 Service 2: Django ASGI Server (Async AI) - Port 8001${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if check_port 8001; then
    echo -e "${YELLOW}⚠️  Port 8001 already in use (ASGI server may already be running)${NC}"
    if curl -s http://127.0.0.1:8001/api/ai/health/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ ASGI server already running at http://127.0.0.1:8001${NC}"
    fi
else
    if [ -d "deployment_package/backend" ]; then
        cd deployment_package/backend
        echo "Starting Django ASGI server on port 8001..."
        uvicorn richesreach.asgi:application --host 0.0.0.0 --port 8001 --workers 1 > /tmp/django_asgi.log 2>&1 &
        ASGI_SERVER_PID=$!
        echo "ASGI server PID: $ASGI_SERVER_PID"
        cd "$SCRIPT_DIR"
        sleep 3
        
        if wait_for_service localhost 8001 "ASGI Server"; then
            echo -e "${GREEN}✅ ASGI server running at http://127.0.0.1:8001${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Django ASGI server directory not found, skipping${NC}"
    fi
fi

# ============================================
# Service 3: Rust Crypto Engine
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🦀 Service 3: Rust Crypto Engine - Port 3001${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if check_port 3001; then
    echo -e "${YELLOW}⚠️  Port 3001 already in use (Rust engine may already be running)${NC}"
else
    if [ -d "rust_crypto_engine" ] && [ -f "rust_crypto_engine/Cargo.toml" ]; then
        if command -v cargo &> /dev/null; then
            cd rust_crypto_engine
            echo "Building and starting Rust crypto engine..."
            cargo run --release -- --port 3001 > /tmp/rust_engine.log 2>&1 &
            RUST_PID=$!
            echo "Rust engine PID: $RUST_PID"
            cd "$SCRIPT_DIR"
            sleep 5
            
            if wait_for_service localhost 3001 "Rust Engine"; then
                echo -e "${GREEN}✅ Rust engine running at http://127.0.0.1:3001${NC}"
            else
                echo -e "${YELLOW}⚠️  Rust engine may still be building/starting${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Rust/Cargo not installed, skipping crypto engine${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Rust engine not found, skipping${NC}"
    fi
fi

# ============================================
# Service 4: TTS Service
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎤 Service 4: TTS Service - Port 8002${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if check_port 8002; then
    echo -e "${YELLOW}⚠️  Port 8002 already in use (TTS service may already be running)${NC}"
else
    if [ -d "tts_service" ] && [ -f "tts_service/main.py" ]; then
        cd tts_service
        
        # Check if dependencies are installed
        python3 -c "import fastapi, uvicorn, gtts" 2>/dev/null || {
            echo "Installing TTS dependencies..."
            pip install -q fastapi uvicorn gtts || {
                echo -e "${YELLOW}⚠️  Failed to install TTS dependencies${NC}"
                cd "$SCRIPT_DIR"
                continue
            }
        }
        
        # Create media directory
        mkdir -p media
        
        echo "Starting TTS service on port 8002..."
        # Modify main.py to use port 8002 if needed, or use uvicorn directly
        PORT=8002 uvicorn main:app --host 0.0.0.0 --port 8002 > /tmp/tts_service.log 2>&1 &
        TTS_PID=$!
        echo "TTS service PID: $TTS_PID"
        cd "$SCRIPT_DIR"
        sleep 3
        
        if wait_for_service localhost 8002 "TTS Service"; then
            echo -e "${GREEN}✅ TTS service running at http://127.0.0.1:8002${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  TTS service not found, skipping${NC}"
    fi
fi

# ============================================
# Service 5: Whisper Server (Optional)
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎙️  Service 5: Whisper Server - Port 3003${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if check_port 3003; then
    echo -e "${YELLOW}⚠️  Port 3003 already in use (Whisper server may already be running)${NC}"
else
    if [ -d "whisper-server" ] && [ -f "whisper-server/package.json" ]; then
        if command -v node &> /dev/null; then
            cd whisper-server
            
            # Check if node_modules exists
            if [ ! -d "node_modules" ]; then
                echo "Installing Whisper server dependencies..."
                npm install --silent || {
                    echo -e "${YELLOW}⚠️  Failed to install Whisper dependencies${NC}"
                    cd "$SCRIPT_DIR"
                    continue
                }
            fi
            
            echo "Starting Whisper server on port 3003..."
            PORT=3003 node server.js > /tmp/whisper_server.log 2>&1 &
            WHISPER_PID=$!
            echo "Whisper server PID: $WHISPER_PID"
            cd "$SCRIPT_DIR"
            sleep 3
            
            if wait_for_service localhost 3003 "Whisper Server"; then
                echo -e "${GREEN}✅ Whisper server running at http://127.0.0.1:3003${NC}"
            else
                echo -e "${YELLOW}⚠️  Whisper server may still be starting${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Node.js not installed, skipping Whisper server${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Whisper server not found, skipping${NC}"
    fi
fi

# ============================================
# SUMMARY
# ============================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ All Backend Services Started!                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📡 Running Services:${NC}"
echo "   • Main Server (FastAPI + Django):  http://127.0.0.1:8000"
echo "     - GraphQL: http://127.0.0.1:8000/graphql"
echo "     - Health: http://127.0.0.1:8000/health"
echo ""
echo "   • Django ASGI Server (Async AI):   http://127.0.0.1:8001"
echo "     - Health: http://127.0.0.1:8001/api/ai/health/"
echo "     - Chat: http://127.0.0.1:8001/api/ai/chat/"
echo ""
echo "   • Rust Crypto Engine:              http://127.0.0.1:3001"
echo "     - Health: http://127.0.0.1:3001/health/live"
echo ""
echo "   • TTS Service:                     http://127.0.0.1:8002"
echo "     - Health: http://127.0.0.1:8002/health"
echo ""
echo "   • Whisper Server:                  http://127.0.0.1:3003"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo "   • Main Server:  tail -f /tmp/main_server.log"
echo "   • ASGI Server:  tail -f /tmp/django_asgi.log"
echo "   • Rust Engine:  tail -f /tmp/rust_engine.log"
echo "   • TTS Service:  tail -f /tmp/tts_service.log"
echo "   • Whisper:      tail -f /tmp/whisper_server.log"
echo ""
echo -e "${YELLOW}🛑 To stop all services:${NC}"
echo "   pkill -f 'main_server.py|uvicorn|rust_crypto|tts|whisper'"
echo ""

