#!/bin/bash

# Hotspot Connection Fix Script
# Use this when your hotspot IP changes

set -e

echo "🔧 Hotspot Connection Fix Script"
echo "================================"

# Get current hotspot IP
echo "🔍 Getting current hotspot IP..."
CURRENT_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo "Found IP: $CURRENT_IP"

# Update mobile app configuration
echo "📱 Updating mobile app configuration..."
sed -i '' "s/const DEV_HOST = '.*';/const DEV_HOST = '$CURRENT_IP';/" config/api.ts

# Update environment files
echo "📱 Updating environment files..."
sed -i '' "s|EXPO_PUBLIC_API_URL=http://.*:8000|EXPO_PUBLIC_API_URL=http://$CURRENT_IP:8000|" env.local
sed -i '' "s|EXPO_PUBLIC_GRAPHQL_URL=http://.*:8000|EXPO_PUBLIC_GRAPHQL_URL=http://$CURRENT_IP:8000|" env.local

# Update main config file
echo "📱 Updating main config file..."
sed -i '' "s|http://localhost:8000|http://$CURRENT_IP:8000|" src/config.ts

# Update Django settings
echo "🐍 Updating Django settings..."
cd ../backend/backend
sed -i '' "s/ALLOWED_HOSTS = \[.*\]/ALLOWED_HOSTS = [\"*\", \"localhost\", \"127.0.0.1\", \"$CURRENT_IP\"]/" richesreach/settings.py

# Update CSRF trusted origins
sed -i '' "s/CSRF_TRUSTED_ORIGINS = \[/CSRF_TRUSTED_ORIGINS = [\n        \"http:\/\/$CURRENT_IP:8000\",/" richesreach/settings.py

echo "✅ Configuration updated with IP: $CURRENT_IP"

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
echo "1. Restart Django server: python manage.py runserver 0.0.0.0:8000"
echo "2. Restart React Native: npx expo start --clear"
echo "3. Test on phone browser: http://$CURRENT_IP:8000/health/"
echo "4. Scan QR code to test mobile app"
