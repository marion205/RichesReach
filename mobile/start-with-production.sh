#!/bin/bash

# RichesReach Mobile App - Start with Production API
# This script sets up and starts the mobile app connected to production servers

echo "🚀 Starting RichesReach Mobile App with Production API"
echo "======================================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the mobile directory"
    exit 1
fi

# Check Node version
echo "🔍 Checking Node version..."
NODE_VERSION=$(node --version)
echo "   Current Node version: $NODE_VERSION"

# Switch to Node 22 if needed
if [[ $NODE_VERSION != v22* ]]; then
    echo "🔄 Switching to Node 22..."
    nvm use 22
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to switch to Node 22"
        echo "   Please install Node 22: nvm install 22"
        exit 1
    fi
fi

# Test production API connection
echo "🧪 Testing production API connection..."
node test-production-connection.js
if [ $? -ne 0 ]; then
    echo "❌ Error: Production API connection failed"
    echo "   Please check if the production server is running"
    exit 1
fi

echo ""
echo "✅ Production API connection successful!"
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
fi

# Start Expo development server
echo "🎯 Starting Expo development server..."
echo ""
echo "📱 Next steps:"
echo "1. Install 'Expo Go' app on your phone"
echo "2. Scan the QR code that appears"
echo "3. Test the app with production API"
echo ""
echo "🔗 Production API: http://54.160.139.56:8000"
echo ""

# Start Expo
npx expo start
