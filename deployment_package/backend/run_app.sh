#!/usr/bin/env bash
# Unified entrypoint: run the RichesReach app (FastAPI + Django GraphQL).
# Usage: ./run_app.sh   or   bash run_app.sh
set -e
cd "$(dirname "$0")"
PORT="${PORT:-8000}"
echo "Starting RichesReach app on port $PORT (main.py)"
exec python main.py
