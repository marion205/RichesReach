# App Store Screenshots - Quick Start Guide
## Quick Start (5 Minutes)
### Step 1: Start Your App
```bash
# In the mobile directory
npm run ios
```
### Step 2: Navigate to Key Screens
Navigate to these 5 screens in your app:
1. **AI Portfolio Advisor** (Hero screen)
2. **Real-Time Market Data** (Stocks screen)
3. **Portfolio Tracking** (Portfolio screen)
4. **Social Trading Community** (Community screen)
5. **Risk Assessment & Education** (Education screen)
### Step 3: Capture Screenshots
```bash
# Option A: Automated capture
./capture-screenshots.sh
# Option B: Manual capture
# Press Cmd+S in iOS Simulator for each screen
```
### Step 4: Organize Files
Screenshots will be saved to:
```
screenshots/
├── iphone-6.7/ # iPhone 14 Pro Max
├── iphone-6.5/ # iPhone 11 Pro Max
├── iphone-5.5/ # iPhone 8 Plus
├── ipad-12.9/ # iPad Pro 12.9"
└── ipad-11/ # iPad Pro 11"
```
## Required Sizes
| Device | Resolution | File Size |
|--------|------------|-----------|
| iPhone 6.7" | 1290 x 2796 | < 5MB |
| iPhone 6.5" | 1242 x 2688 | < 5MB |
| iPhone 5.5" | 1242 x 2208 | < 5MB |
| iPad 12.9" | 2048 x 2732 | < 5MB |
| iPad 11" | 1668 x 2388 | < 5MB |
## Post-Processing Checklist
- [ ] Remove status bar from screenshots
- [ ] Ensure file size < 5MB
- [ ] Use PNG or JPEG format
- [ ] Check image quality (crisp text)
- [ ] Verify no personal information
- [ ] Consistent branding and colors
## Tools Available
### Automated Scripts
- `./capture-screenshots.sh` - Interactive screenshot capture
- `./generate-screenshots.js` - Automated generation with reporting
### Manual Methods
- **iOS Simulator**: Cmd+S to capture
- **Physical Device**: Power + Volume Up
- **QuickTime**: Screen recording from device
## Screenshot Content Guide
### 1. Hero Screen - AI Portfolio Advisor
- Show AI-powered recommendations
- Display personalized risk assessment
- Include clean, professional interface
- Highlight main value proposition
### 2. Real-Time Market Data
- Live stock prices and charts
- Market indicators and trends
- Professional financial data
- Real-time updates
### 3. Portfolio Tracking
- Portfolio performance dashboard
- Investment tracking
- Performance analytics
- Clean data visualization
### 4. Social Trading Community
- Social feed with insights
- User interactions
- Community engagement
- Knowledge sharing
### 5. Risk Assessment & Education
- Risk assessment interface
- Educational content
- Learning progress
- Financial tips
## Common Issues & Solutions
### Issue: Screenshots too large
**Solution**: Compress images or reduce resolution
### Issue: Status bar visible
**Solution**: Use image editing software to remove
### Issue: Poor image quality
**Solution**: Ensure simulator is at 100% scale
### Issue: Wrong device size
**Solution**: Use correct simulator device
### Issue: App not running
**Solution**: Start app with `npm run ios` first
## Need Help?
1. **Check the detailed guide**: `app-store-screenshots-guide.md`
2. **Use templates**: `screenshot-templates.md`
3. **Run automated script**: `./capture-screenshots.sh`
4. **Check prerequisites**: Ensure Xcode and iOS Simulator are installed
## Final Checklist
Before submitting to App Store:
- [ ] All 5 required screenshots captured
- [ ] Correct resolutions for each device
- [ ] File sizes under 5MB
- [ ] No personal information visible
- [ ] Professional appearance
- [ ] Consistent branding
- [ ] High image quality
- [ ] Proper file naming
## You're Ready!
Your screenshots are now ready for App Store submission. Upload them to App Store Connect along with your app build.
