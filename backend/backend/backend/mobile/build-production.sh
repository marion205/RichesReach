#!/bin/bash
# RichesReach Production Build Script
echo " Building RichesReach for Production..."
# Check if EAS CLI is installed
if ! command -v eas &> /dev/null; then
echo " EAS CLI not found. Installing..."
npm install -g @expo/cli eas-cli
fi
# Check if logged into Expo
if ! eas whoami &> /dev/null; then
echo " Please log in to Expo:"
eas login
fi
# Install dependencies
echo " Installing dependencies..."
npm install
# Create production build
echo " Creating production build..."
echo "Choose build type:"
echo "1) iOS only"
echo "2) Android only" 
echo "3) Both platforms"
read -p "Enter choice (1-3): " choice
case $choice in
1)
echo " Building for iOS..."
eas build --platform ios --profile production
;;
2)
echo " Building for Android..."
eas build --platform android --profile production
;;
3)
echo " Building for both platforms..."
eas build --platform all --profile production
;;
*)
echo " Invalid choice. Building for iOS by default..."
eas build --platform ios --profile production
;;
esac
echo " Build process initiated!"
echo " You'll receive an email when the build is complete."
echo " Check build status at: https://expo.dev/accounts/[your-username]/projects/richesreach-ai/builds"
