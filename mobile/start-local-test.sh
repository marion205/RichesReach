#!/bin/bash
set -euo pipefail

echo "🚀 Starting React Native app with LOCAL Django server..."

# Ensure nvm is sourced
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# Switch to Node 22
echo "Switching to Node.js v22..."
nvm use 22

# Navigate to the mobile directory
cd "$(dirname "$0")"

# Set environment variables for LOCAL API
export EXPO_PUBLIC_API_BASE_URL="http://localhost:8000"
export EXPO_PUBLIC_GRAPHQL_URL="http://localhost:8000/graphql/"
export EXPO_PUBLIC_ENVIRONMENT="local"

echo "Environment variables set:"
echo "  EXPO_PUBLIC_API_BASE_URL=$EXPO_PUBLIC_API_BASE_URL"
echo "  EXPO_PUBLIC_GRAPHQL_URL=$EXPO_PUBLIC_GRAPHQL_URL"
echo "  EXPO_PUBLIC_ENVIRONMENT=$EXPO_PUBLIC_ENVIRONMENT"

echo ""
echo "✅ Make sure your local Django server is running on port 8000!"
echo "   You can start it with: cd backend/backend/backend/backend && python3 manage.py runserver 0.0.0.0:8000"
echo ""

# Start the Expo development server
echo "Starting Expo development server..."
npx expo start --clear

echo "✅ Expo server started. Scan the QR code with Expo Go."
echo "Press Ctrl+C to stop the server."
