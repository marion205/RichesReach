#!/usr/bin/env bash
# Force-kill any process on port 8000 and start main_server.py (ensures latest code is loaded).
set -e
cd "$(dirname "$0")/.."
echo "Stopping any process on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2
echo "Starting main_server.py..."
python3 main_server.py > /tmp/main_server.log 2>&1 &
sleep 3
if curl -sf http://127.0.0.1:8000/health >/dev/null; then
  echo "OK: Main server is running at http://127.0.0.1:8000"
  echo "Logs: tail -f /tmp/main_server.log"
else
  echo "WARN: Health check failed. Check /tmp/main_server.log"
  tail -30 /tmp/main_server.log
fi
