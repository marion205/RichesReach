#!/bin/bash
# Start Django server with production environment variables

export ALPHA_VANTAGE_KEY="OHYSFF1AE446O7CR"
export FINNHUB_KEY="d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"

echo "🚀 Starting RichesReach Production Server..."
echo "   Alpha Vantage Key: ${ALPHA_VANTAGE_KEY:0:10}..."
echo "   Finnhub Key: ${FINNHUB_KEY:0:10}..."
echo "   Redis Host: $REDIS_HOST:$REDIS_PORT/$REDIS_DB"
echo "   Server URL: http://localhost:8000"
echo ""

# Start the server
python3 manage.py runserver 8000
