#!/bin/bash

# RichesReach Local Development Server
# This script starts the local development server with production schema and real data

echo "🚀 Starting RichesReach Local Development Server..."
echo "📊 Configuration: Production Schema + Real Data + Mock Fallbacks"
echo ""

# Kill any existing Django servers
echo "🔄 Stopping any existing servers..."
pkill -f "manage.py runserver" 2>/dev/null || true

# Wait a moment for processes to stop
sleep 2

# Start the server
echo "▶️  Starting server with settings_local.py..."
cd /Users/marioncollins/RichesReach/backend/backend/backend/backend
export DJANGO_SETTINGS_MODULE=richesreach.settings_local
python3 manage.py runserver 0.0.0.0:8000
