#!/bin/bash

# Force the mobile app to use the correct IP address
echo "🚀 Starting Expo with FORCED IP configuration..."

# Kill any existing Expo processes
pkill -f "expo start" || true

# Set environment variables explicitly
export EXPO_PUBLIC_API_BASE_URL="http://192.168.1.236:8000"
export EXPO_PUBLIC_GRAPHQL_URL="http://192.168.1.236:8000/graphql/"
export EXPO_PUBLIC_RUST_API_URL="http://192.168.1.236:3001"
export EXPO_PUBLIC_WS_URL="ws://192.168.1.236:8000/ws"

# Verify the environment variables are set
echo "📡 Environment variables set:"
echo "EXPO_PUBLIC_API_BASE_URL=$EXPO_PUBLIC_API_BASE_URL"
echo "EXPO_PUBLIC_GRAPHQL_URL=$EXPO_PUBLIC_GRAPHQL_URL"

# Navigate to mobile directory
cd /Users/marioncollins/RichesReach/mobile

# Start Expo with explicit environment variables and clear cache
npx expo start --clear --reset-cache --tunnel
