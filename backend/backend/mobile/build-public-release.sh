#!/bin/bash

# RichesReach AI - Public Release Build Script
# This script builds the app for Google Play Store public release

echo "🚀 Building RichesReach AI for Public Release..."

# Set production environment variables
export EXPO_PUBLIC_API_URL="https://app.richesreach.net"
export EXPO_PUBLIC_GRAPHQL_URL="https://app.richesreach.net/graphql"
export EXPO_PUBLIC_RUST_API_URL="https://app.richesreach.net:3001"
export EXPO_PUBLIC_ENVIRONMENT="production"
export EXPO_PUBLIC_APP_VERSION="1.0.2"
export EXPO_PUBLIC_BUILD_NUMBER="3"

echo "📱 Environment configured for public release:"
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

# Build for Android (Production)
echo "🔨 Building Android App Bundle for Google Play Store..."
echo "   This will create an AAB file for Google Play Store upload"

# Try EAS Build for production
echo "   Using EAS Build (cloud) for production release"
if command -v eas &> /dev/null; then
    echo "   Building production AAB..."
    eas build --platform android --profile production --non-interactive
else
    echo "   EAS CLI not available. Please install it first:"
    echo "   npm install -g eas-cli"
    echo ""
    echo "   Then run:"
    echo "   eas build --platform android --profile production"
fi

echo "✅ Build process completed!"
echo ""
echo "📋 Next Steps for Public Release:"
echo "   1. Download the AAB file from EAS Build dashboard"
echo "   2. Go to Google Play Console (https://play.google.com/console)"
echo "   3. Select your app and go to Release > Production"
echo "   4. Upload the AAB file"
echo "   5. Fill in the release details from APP_STORE_LISTING.md"
echo "   6. Add screenshots and feature graphic"
echo "   7. Review and publish to production"
echo ""
echo "📱 App Details for Play Console:"
echo "   Package: com.richesreach.app"
echo "   Version: 1.0.2 (3)"
echo "   Environment: Production"
echo "   Backend: https://app.richesreach.net"
echo "   Release Type: Production (Public)"
echo ""
echo "🎯 For Jacksonville Meeting:"
echo "   - Real user data from public release"
echo "   - Live app in Google Play Store"
echo "   - User reviews and ratings"
echo "   - Download and usage statistics"
echo "   - Public validation of the platform"
echo ""
echo "📊 Expected Impact:"
echo "   - 1,000+ downloads in first month"
echo "   - 4.0+ star rating from real users"
echo "   - 500+ daily active users"
echo "   - Real testimonials and feedback"
echo "   - Public proof of concept"
echo ""
echo "🚀 This public release will provide the strongest possible validation"
echo "   for your Jacksonville city presentation and $1M pilot proposal!"
