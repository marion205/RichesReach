#!/bin/bash

# Set API Keys
export ALPHA_VANTAGE_API_KEY="OHYSFF1AE446O7CR"
export FINNHUB_API_KEY="d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"
export NEWS_API_KEY="94a335c7316145f79840edd62f77e11e"

# Activate virtual environment
source venv/bin/activate

# Start the server
echo "🚀 Starting RichesReach Crypto Server with your API keys..."
python final_complete_server.py
