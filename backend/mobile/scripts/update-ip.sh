#!/bin/bash

# Quick IP Update Script for RichesReach Mobile App
# Usage: ./scripts/update-ip.sh [IP_ADDRESS]

set -e

# Get current IP if not provided
if [ -z "$1" ]; then
    echo "🔍 Getting current IP address..."
    CURRENT_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
    echo "Found IP: $CURRENT_IP"
else
    CURRENT_IP="$1"
    echo "Using provided IP: $CURRENT_IP"
fi

# Update environment files
echo "🔧 Updating environment files..."

# Update .env
sed -i '' "s/EXPO_PUBLIC_API_HOST=.*/EXPO_PUBLIC_API_HOST=$CURRENT_IP/" .env 2>/dev/null || echo "EXPO_PUBLIC_API_HOST=$CURRENT_IP" >> .env

# Update .env.local
sed -i '' "s/EXPO_PUBLIC_API_HOST=.*/EXPO_PUBLIC_API_HOST=$CURRENT_IP/" .env.local 2>/dev/null || echo "EXPO_PUBLIC_API_HOST=$CURRENT_IP" >> .env.local

echo "✅ Environment files updated with IP: $CURRENT_IP"

# Show current configuration
echo ""
echo "📋 Current Configuration:"
echo "IP Address: $CURRENT_IP"
echo "API URL: http://$CURRENT_IP:8000"
echo "GraphQL: http://$CURRENT_IP:8000/graphql/"
echo ""

# Test server connectivity
echo "🧪 Testing server connectivity..."
if curl -s --max-time 5 "http://$CURRENT_IP:8000/health/" > /dev/null; then
    echo "✅ Server is accessible at http://$CURRENT_IP:8000"
else
    echo "❌ Server is not accessible at http://$CURRENT_IP:8000"
    echo "💡 Make sure Django server is running with: python manage.py runserver 0.0.0.0:8000"
fi

echo ""
echo "🚀 Next steps:"
echo "1. Restart React Native app: npx expo start --clear"
echo "2. Test connectivity in the app's debug menu"
echo "3. For real device testing, scan the QR code"
