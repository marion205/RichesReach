#!/bin/bash
# Start Expo with the correct environment variables for physical device

cd "$(dirname "$0")"

# Get Mac's IP address
MAC_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

if [ -z "$MAC_IP" ]; then
    MAC_IP="192.168.1.240"
    echo "⚠️  Could not detect IP, using default: $MAC_IP"
else
    echo "✅ Detected Mac IP: $MAC_IP"
fi

# Set environment variables
export EXPO_PUBLIC_API_BASE_URL="http://${MAC_IP}:8000"
export EXPO_PUBLIC_GRAPHQL_URL="http://${MAC_IP}:8000/graphql/"
export EXPO_PUBLIC_WS_URL="ws://${MAC_IP}:8000/ws"

echo ""
echo "🔧 Environment variables set:"
echo "   EXPO_PUBLIC_API_BASE_URL=$EXPO_PUBLIC_API_BASE_URL"
echo "   EXPO_PUBLIC_GRAPHQL_URL=$EXPO_PUBLIC_GRAPHQL_URL"
echo "   EXPO_PUBLIC_WS_URL=$EXPO_PUBLIC_WS_URL"
echo ""
echo "🚀 Starting Expo with cleared cache..."
echo ""

# Start Expo with cleared cache
npx expo start --clear

