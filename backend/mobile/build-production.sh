#!/bin/bash

# RichesReach AI - Production Build Script
# This script builds the app for Google Play Store internal testing

echo "🚀 Building RichesReach AI for Production..."

# Set production environment variables
export EXPO_PUBLIC_API_URL="https://app.richesreach.net"
export EXPO_PUBLIC_GRAPHQL_URL="https://app.richesreach.net/graphql"
export EXPO_PUBLIC_RUST_API_URL="https://app.richesreach.net:3001"
export EXPO_PUBLIC_ENVIRONMENT="production"
export EXPO_PUBLIC_APP_VERSION="1.0.2"
export EXPO_PUBLIC_BUILD_NUMBER="3"

echo "📱 Environment configured for production:"
echo "   API URL: $EXPO_PUBLIC_API_URL"
echo "   GraphQL URL: $EXPO_PUBLIC_GRAPHQL_URL"
echo "   Rust API URL: $EXPO_PUBLIC_RUST_API_URL"
echo "   Environment: $EXPO_PUBLIC_ENVIRONMENT"
echo "   Version: $EXPO_PUBLIC_APP_VERSION"
echo "   Build Number: $EXPO_PUBLIC_BUILD_NUMBER"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the mobile directory."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Clear cache
echo "🧹 Clearing cache..."
npx expo start --clear

# Build for Android
echo "🔨 Building Android APK..."
echo "   This will create an APK file for Google Play Store upload"

# Try different build methods
echo "   Method 1: Using EAS Build (cloud)"
if command -v eas &> /dev/null; then
    eas build --platform android --profile internal --non-interactive
else
    echo "   EAS CLI not available, trying alternative method..."
    
    # Method 2: Using Expo CLI
    echo "   Method 2: Using Expo CLI"
    npx expo export --platform android
    
    # Method 3: Manual build instructions
    echo "   Method 3: Manual build required"
    echo "   Please follow these steps:"
    echo "   1. Open Android Studio"
    echo "   2. Import the project from ./android directory"
    echo "   3. Build > Generate Signed Bundle/APK"
    echo "   4. Choose APK and follow the wizard"
fi

echo "✅ Build process completed!"
echo ""
echo "📋 Next Steps:"
echo "   1. Upload the APK to Google Play Console"
echo "   2. Set up internal testing track"
echo "   3. Add testers (Jacksonville officials)"
echo "   4. Share testing instructions"
echo ""
echo "📱 App Details:"
echo "   Package: com.richesreach.app"
echo "   Version: 1.0.2 (3)"
echo "   Environment: Production"
echo "   Backend: https://app.richesreach.net"
echo ""
echo "🎯 For Jacksonville Meeting:"
echo "   - Real user data from internal testing"
echo "   - Live app demonstration"
echo "   - User feedback and testimonials"
echo "   - Usage analytics and metrics"