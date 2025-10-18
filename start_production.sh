#!/bin/bash

# RichesReach Production Server
# This script starts the production server with all real services

echo "🚀 Starting RichesReach Production Server..."
echo "📊 Configuration: All Real Services (No Mocks)"
echo ""

# Kill any existing Django servers
echo "🔄 Stopping any existing servers..."
pkill -f "manage.py runserver" 2>/dev/null || true

# Wait a moment for processes to stop
sleep 2

# Start the server
echo "▶️  Starting server with settings_production_clean.py..."
cd /Users/marioncollins/RichesReach/backend/backend/backend/backend
export DJANGO_SETTINGS_MODULE=richesreach.settings_production_clean
python3 manage.py runserver 0.0.0.0:8000
