#!/bin/bash
# Navigate to project root
cd /Users/marioncollins/RichesReach
echo " Checking git status..."
git status
echo ""
echo " Adding all changes..."
git add .
echo ""
echo " Committing changes..."
git commit -m "Fix individual stock return percentages and add WebSocket live data
- Fixed individual stock holdings showing same percentage as portfolio total
- Updated backend PremiumAnalyticsService to provide different return percentages per stock
- Enhanced WebSocket consumer to use consistent data source with GraphQL
- Integrated WebSocket live data with HomeScreen for real-time individual holdings updates
- Added mock data with realistic individual stock return percentages
- Portfolio holdings now display unique return percentages that update in real-time
Fixes: Individual stocks now show their own return percentages instead of all showing 17.65%"
echo ""
echo " Pushing to GitHub..."
git push origin main
echo ""
echo " All changes committed and pushed to GitHub!"
