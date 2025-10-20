#!/bin/bash

# Load environment variables from env.secrets
echo "🔧 Loading Alpaca API credentials from env.secrets..."

# Export all variables from env.secrets
export $(grep -v '^#' env.secrets | xargs)

echo "🚀 Starting Django server with Alpaca credentials..."
echo "📊 ALPACA_API_KEY: ${ALPACA_API_KEY:0:10}..."
echo "📊 ALPACA_SECRET_KEY: ${ALPACA_SECRET_KEY:0:10}..."
echo "📊 USE_ALPACA: $USE_ALPACA"
echo "📊 USE_ALPACA_BROKER: $USE_ALPACA_BROKER"
echo "📊 USE_ALPACA_CRYPTO: $USE_ALPACA_CRYPTO"

# Start the Django server
python3 manage.py runserver 0.0.0.0:8000
