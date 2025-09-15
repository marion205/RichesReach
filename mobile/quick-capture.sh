#!/bin/bash
# Quick Screenshot Capture for RichesReach App Store
echo " Quick Screenshot Capture - RichesReach"
echo "========================================="
# Create directories
mkdir -p screenshots/iphone-6.7
mkdir -p screenshots/iphone-6.5
mkdir -p screenshots/iphone-5.5
mkdir -p screenshots/ipad-12.9
mkdir -p screenshots/ipad-11
echo " Ready to capture 5 required screenshots!"
echo ""
echo " Instructions:"
echo "1. Navigate to each screen in your app"
echo "2. Press Enter when ready to capture"
echo "3. Repeat for all 5 screens"
echo ""
# Function to capture screenshot
capture_screen() {
local screen_name=$1
local description=$2
echo " Ready to capture: $description"
echo "Navigate to this screen in your app, then press Enter..."
read -p "Press Enter when ready..."
# Capture screenshot
xcrun simctl io booted screenshot "screenshots/${screen_name}.png"
if [ $? -eq 0 ]; then
echo " Screenshot captured: ${screen_name}.png"
echo " File size: $(ls -lh "screenshots/${screen_name}.png" | awk '{print $5}')"
else
echo " Failed to capture screenshot"
fi
echo ""
}
# Capture all 5 required screenshots
capture_screen "01-hero-ai-portfolio" "AI Portfolio Advisor (Hero Screen)"
capture_screen "02-market-data" "Real-Time Market Data (Stocks Screen)"
capture_screen "03-portfolio-tracking" "Portfolio Tracking (Portfolio Screen)"
capture_screen "04-social-community" "Social Trading Community (Community Screen)"
capture_screen "05-risk-education" "Risk Assessment & Education (Education Screen)"
echo " All screenshots captured!"
echo "=========================="
echo ""
echo " Screenshots saved to:"
ls -la screenshots/*.png
echo ""
echo " Next steps:"
echo "1. Review each screenshot for quality"
echo "2. Remove status bar if needed"
echo "3. Ensure file sizes are under 5MB"
echo "4. Ready for App Store submission!"
