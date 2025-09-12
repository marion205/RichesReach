#!/bin/bash

# RichesReach App Store Publishing Script
echo "🚀 Publishing RichesReach to App Stores..."

# Check if EAS CLI is installed
if ! command -v eas &> /dev/null; then
    echo "❌ EAS CLI not found. Installing..."
    npm install -g eas-cli
fi

# Login to EAS
echo "🔐 Logging into EAS..."
eas login

# Initialize project if needed
if [ ! -f "eas.json" ]; then
    echo "⚙️ Initializing EAS project..."
    eas init
fi

# Configure build settings
echo "🔧 Configuring build settings..."
eas build:configure

echo "📱 Choose your publishing option:"
echo "1. Build for Android (APK for testing)"
echo "2. Build for Android (AAB for Google Play Store)"
echo "3. Build for iOS (Simulator for testing)"
echo "4. Build for iOS (App Store)"
echo "5. Submit to Google Play Store"
echo "6. Submit to Apple App Store"
echo "7. Build for both platforms (Production)"

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        echo "🤖 Building Android APK..."
        eas build --platform android --profile preview
        ;;
    2)
        echo "🤖 Building Android AAB for Google Play..."
        eas build --platform android --profile production
        ;;
    3)
        echo "🍎 Building iOS for Simulator..."
        eas build --platform ios --profile preview
        ;;
    4)
        echo "🍎 Building iOS for App Store..."
        eas build --platform ios --profile production
        ;;
    5)
        echo "📤 Submitting to Google Play Store..."
        eas submit --platform android
        ;;
    6)
        echo "📤 Submitting to Apple App Store..."
        eas submit --platform ios
        ;;
    7)
        echo "🚀 Building for both platforms..."
        eas build --platform all --profile production
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo "✅ Publishing process completed!"
echo "📱 Check your Expo dashboard for build status: https://expo.dev"
