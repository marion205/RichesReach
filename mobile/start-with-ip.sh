#!/bin/bash

# Set environment variables explicitly
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.236:8000
export EXPO_PUBLIC_GRAPHQL_URL=http://192.168.1.236:8000/graphql/
export EXPO_PUBLIC_RUST_API_URL=http://192.168.1.236:3001
export EXPO_PUBLIC_WS_URL=ws://192.168.1.236:8000/ws

echo "🚀 Starting Expo with IP address: 192.168.1.236:8000"
echo "📡 API_BASE_URL: $EXPO_PUBLIC_API_BASE_URL"
echo "🔗 GRAPHQL_URL: $EXPO_PUBLIC_GRAPHQL_URL"

# Start Expo with clear cache
npx expo start --clear --reset-cache
