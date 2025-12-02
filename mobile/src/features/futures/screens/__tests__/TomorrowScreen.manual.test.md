# TomorrowScreen Manual Testing Checklist

## ✅ Phase 1: Core Features

### Loading & Error States
- [ ] **Skeleton Loaders**: On initial load, 3 skeleton cards appear
- [ ] **Error Banner**: When network fails, yellow banner shows "Connection Issue" with retry button
- [ ] **Cached Data Banner**: When using mock data, banner shows "Using cached data. Pull to refresh for latest"
- [ ] **Empty State**: When no recommendations, shows "No recommendations yet" with refresh button

### Real-time Data
- [ ] **Price Display**: Each card shows current price (e.g., "$22.95")
- [ ] **Price Change**: Shows change amount and percentage (e.g., "+0.45 (+2.00%)")
- [ ] **Color Coding**: Green for positive, red for negative
- [ ] **Arrows**: Up arrow (↑) for positive, down arrow (↓) for negative
- [ ] **Price Updates**: Prices update every 5 seconds (check network tab)

### Sparklines
- [ ] **Sparkline Visible**: Mini chart appears below price on each card
- [ ] **Color**: Green for up trend, red for down trend
- [ ] **Updates**: Sparkline updates with new price data

### Session Indicators
- [ ] **RTH Badge**: Green "RTH" badge during Regular Trading Hours (9:30 AM - 4:00 PM ET)
- [ ] **ETH Badge**: Orange "ETH" badge during Extended Hours
- [ ] **Session Label**: Shows "Regular Trading Hours" or "Extended Hours" text
- [ ] **Background Color**: Light green/orange tint on card border

## ✅ Phase 2: Advanced Features

### View Toggle
- [ ] **List View**: Default view shows cards in vertical list
- [ ] **Heatmap View**: Toggle to grid shows contracts grouped by category
- [ ] **Toggle Buttons**: Two buttons in header (list icon and grid icon)
- [ ] **Active State**: Active view button is highlighted in blue

### Heatmap View
- [ ] **Categories**: Contracts grouped by "Equity Index", "Currency", "Commodities"
- [ ] **Color Coding**: Cells colored based on price change (green/red gradient)
- [ ] **2-Column Grid**: Contracts displayed in 2 columns
- [ ] **Badges**: Top Movers and Unusual Volume badges visible on cells
- [ ] **Info Button**: Info button (ℹ️) works in heatmap view

### Badges
- [ ] **Top Movers**: Orange "Top" badge on top 3 contracts by price change
- [ ] **Unusual Volume**: Purple "Vol" badge when volume_ratio > 1.5
- [ ] **Both Badges**: Can show both badges on same contract
- [ ] **Layout**: Badges don't block "Regular Trading Hours" text

### Contract Info Modal
- [ ] **Info Button**: Tap info button (ℹ️) opens modal
- [ ] **Contract Specs**: Shows Tick Size, Tick Value, Contract Size, Margin
- [ ] **Educational Section**: "What This Means" explains each spec
- [ ] **Place Trade Button**: Button at bottom opens trade confirmation
- [ ] **Close Button**: X button closes modal

### Enhanced "Why Now"
- [ ] **Bullet Points**: Explanations formatted as bullet points (•)
- [ ] **Max 3 Bullets**: Shows maximum 3 bullet points
- [ ] **Detailed Context**: Includes momentum, volatility, volume insights

## ✅ Phase 3: Enhanced Features

### Chart Modal
- [ ] **Card Tap**: Tapping card (not Buy button) opens chart modal
- [ ] **Price Display**: Shows large price (e.g., "$22.95")
- [ ] **Price Change**: Shows change with colored badge
- [ ] **Large Sparkline**: Bigger chart (320x180) in modal
- [ ] **Quick Actions**: "Trade" and "Details" buttons at bottom
- [ ] **Secondary Actions**: "Watchlist", "Share", "Compare" buttons below

### Filters & Sorting
- [ ] **Filter Bar**: Visible below header in list view
- [ ] **Category Filters**: "All", "Equity Index", "Currency", "Commodities" chips
- [ ] **Active Filter**: Selected filter highlighted in blue
- [ ] **Sort Options**: "Default", "Price", "Prob" chips
- [ ] **Filtering Works**: Selecting category shows only that category
- [ ] **Sorting Works**: Selecting sort reorders recommendations

### Watchlist
- [ ] **Add to Watchlist**: Tap "Watchlist" in chart modal
- [ ] **Success Alert**: Shows "MESZ5 added to watchlist!" alert
- [ ] **Haptic Feedback**: Feels vibration on success
- [ ] **Already Added**: Shows "already in watchlist" message if duplicate

### Share
- [ ] **Share Button**: Tap "Share" in chart modal
- [ ] **Native Share Sheet**: Opens iOS/Android share sheet
- [ ] **Share Content**: Includes symbol, name, why now, metrics, price
- [ ] **Haptic Feedback**: Vibration on share action

### Comparison View
- [ ] **Compare Button**: Tap comparison icon (layers) on card
- [ ] **Comparison Modal**: Opens automatically when first contract added
- [ ] **Add Multiple**: Can add up to 3 contracts
- [ ] **Side-by-Side**: Contracts displayed in vertical list for comparison
- [ ] **Remove Button**: X button removes contract from comparison
- [ ] **Individual Trade**: Each contract has its own "Trade" button
- [ ] **Visual Indicator**: Comparison icon highlighted when contract selected

## ✅ Trade Actions

### Order Placement
- [ ] **Buy Button**: Tap "Buy" button on card
- [ ] **Confirmation Modal**: "Confirm Trade" modal appears
- [ ] **Trade Details**: Shows symbol, action, why now, max loss
- [ ] **Cancel Button**: Closes modal without placing order
- [ ] **Trade Button**: Places order and shows success alert
- [ ] **Haptic Feedback**: Success vibration on order placement

### Order Blocking
- [ ] **Blocked Order**: If order blocked, shows "Order Blocked" alert
- [ ] **Why Not**: Shows reason and fix suggestion
- [ ] **Duplicate Order**: Shows "Order already submitted" if duplicate

## ✅ Additional Features

### Pull-to-Refresh
- [ ] **Pull Down**: Pull down on list to refresh
- [ ] **Loading Indicator**: Shows spinner while refreshing
- [ ] **Data Updates**: Recommendations refresh after pull

### Dark Mode
- [ ] **Auto Detection**: Uses system dark mode setting
- [ ] **Dark Colors**: All text, backgrounds, borders use dark theme
- [ ] **Contrast**: Text remains readable in dark mode
- [ ] **Icons**: Icons visible in dark mode

### Haptic Feedback
- [ ] **Card Tap**: Light vibration when tapping card
- [ ] **Trade Success**: Success vibration on order placement
- [ ] **Trade Error**: Error vibration on failed order

### Performance
- [ ] **Smooth Scrolling**: List scrolls smoothly with many contracts
- [ ] **No Lag**: No lag when switching views
- [ ] **Fast Loading**: Recommendations load quickly
- [ ] **Efficient Updates**: Price updates don't cause re-renders

## Test Results

**Date**: _______________
**Tester**: _______________
**Environment**: iOS / Android / Both
**Version**: _______________

### Issues Found
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

### Notes
_________________________________________________
_________________________________________________

