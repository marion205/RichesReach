#!/bin/bash
cd "$(dirname "$0")/backend" || exit 1
export PYTHONPATH="$(pwd)/backend:${PYTHONPATH}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-for-dev}"
../.venv/bin/python -m uvicorn backend.final_complete_server:app --host 0.0.0.0 --port 8000 --reload
