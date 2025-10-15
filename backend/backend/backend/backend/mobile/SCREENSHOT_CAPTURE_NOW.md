# Screenshot Capture - Ready to Start!
## Quick Start (Right Now!)
### Step 1: Your App is Running 
- iPhone 16 Pro simulator is booted and ready
- Screenshot capture is working
- All tools are set up
### Step 2: Navigate to Each Screen
** You need to capture these 5 screens:**
1. **AI Portfolio Advisor** (Hero Screen)
- Navigate to: AI Portfolio Advisor tab/screen
- Show: Personalized recommendations, risk assessment
2. **Real-Time Market Data** (Stocks Screen)
- Navigate to: Stocks/Market Data screen
- Show: Live stock prices, charts, market indicators
3. **Portfolio Tracking** (Portfolio Screen)
- Navigate to: Portfolio/My Investments screen
- Show: Performance dashboard, investment tracking
4. **Social Trading Community** (Community Screen)
- Navigate to: Community/Social screen
- Show: User interactions, social feed
5. **Risk Assessment & Education** (Education Screen)
- Navigate to: Education/Learning screen
- Show: Risk assessment, educational content
### Step 3: Capture Screenshots
**Option A: Manual Capture (Recommended)**
```bash
./manual-screenshot-capture.sh
```
**Option B: Quick Capture Commands**
```bash
# For each screen, run:
xcrun simctl io booted screenshot screenshots/01-hero-ai-portfolio.png
xcrun simctl io booted screenshot screenshots/02-market-data.png
xcrun simctl io booted screenshot screenshots/03-portfolio-tracking.png
xcrun simctl io booted screenshot screenshots/04-social-community.png
xcrun simctl io booted screenshot screenshots/05-risk-education.png
```
### Step 4: Check Results
```bash
ls -la screenshots/*.png
```
## App Store Requirements
- **File Format**: PNG or JPEG
- **Max File Size**: 5MB per screenshot
- **Quality**: High resolution, crisp text
- **Content**: No personal information, professional appearance
## Post-Processing
1. **Remove Status Bar** (if visible)
2. **Check File Size** (should be under 5MB)
3. **Verify Quality** (text should be crisp)
4. **Remove Personal Info** (if any)
## Ready to Start?
Your app is running and ready for screenshots. Just navigate to each screen and capture!
**Run this command to start:**
```bash
./manual-screenshot-capture.sh
```
## What You'll Get
After capture, you'll have:
- 5 high-quality screenshots
- Ready for App Store submission
- Professional appearance
- All requirements met
## Success!
Once captured, your screenshots will be ready for App Store submission!
