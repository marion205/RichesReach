# 📊 InnovativeChart Features Guide

## 🎯 How to Access the Chart

### Location
1. **Home Screen** → Scroll down below the Portfolio Performance Card
2. Look for section titled **"What moved this"** with a trending-up icon
3. The chart appears below that header

---

## ✨ Chart Features

### 1. **Interactive Gestures** 👆
- **Pinch to Zoom**: Pinch in/out to zoom the timeline
- **Pan**: Swipe left/right to scroll through time periods
- **Tap Events**: Tap on colored dots to see event details (Earnings, Fed Decisions, etc.)
- **Tap Drivers**: Tap on vertical colored lines to see "why" explanations

### 2. **Regime Bands** 📈
The chart shows colored background bands indicating market regimes:
- **🟢 Green (Trend)**: Strong directional movement
- **🟡 Yellow (Chop)**: Sideways/choppy movement  
- **🔴 Red (Shock)**: High volatility/sudden moves

### 3. **Confidence Glass** 🔮
Semi-transparent blue bands showing:
- **Darker blue (80% confidence)**: Wider prediction band
- **Lighter blue (50% confidence)**: Tighter prediction band

These show where your portfolio value might be in the future based on statistical analysis.

### 4. **Event Markers** 📍
- **Blue dots**: Earnings announcements
- **Red dots**: Fed decisions
- Tap any dot to see details:
  - Title (e.g., "Earnings")
  - Summary (e.g., "Q3 results exceeded expectations")

### 5. **Driver Lines** 🎯
Vertical colored lines showing what moved your portfolio:
- **Blue**: News-driven moves
- **Red**: Macro events (Fed, inflation data)
- **Green**: Flow/institutional buying
- **Orange**: Options activity
- **Purple**: Earnings impact

Tap a line to see:
- Driver type
- Cause description
- Relevancy percentage

### 6. **Bottom Controls** 🎛️
In the bottom-right corner:
- **Money/Price Toggle**: Switch between price view and money view (shows profit/loss areas)
- **Benchmark Toggle**: Show/hide benchmark comparison (when benchmark data available)
- **AR Walk Button**: Opens AR preview (experimental feature)

---

## 🔧 Chart Optimizations (Performance)

The chart now includes these performance improvements:

1. **InteractionManager Gate**: Chart loads after first frame (brief "Loading chart..." message)
2. **Deferred Benchmark Computation**: Heavy math operations deferred until needed
3. **Optimized Worklets**: All animations run on UI thread without blocking
4. **Lazy Event Computation**: Events and drivers computed efficiently

---

## 🎮 How to Use

### Basic Navigation
1. **Zoom**: Pinch in/out on the chart
2. **Scroll**: Swipe left/right while zoomed in
3. **Explore Events**: Tap colored dots for details
4. **Understand Drivers**: Tap vertical lines to see what caused moves

### Understanding the Chart
- **Main Line**: Your portfolio value over time
- **Colored Backgrounds**: Market regime (trend/chop/shock)
- **Blue Bands**: Future confidence intervals
- **Dots**: Important events that affected your portfolio
- **Lines**: Key drivers of portfolio movement

---

## 🐛 Troubleshooting

### Chart doesn't appear?
- Check if you have portfolio history data
- Chart only shows if `chartData.series.length > 0`
- You should see "Loading chart..." briefly before it appears

### Chart is slow?
- First load may take 1-2 seconds (InteractionManager delay)
- After initial load, all interactions should be smooth
- If still slow, check Performance Monitor (⌘D → Performance Monitor)

### Gestures not working?
- Make sure GestureHandlerRootView is enabled (it is now)
- Try tapping instead of swiping first
- Restart app if gestures feel unresponsive

---

## 📝 Code Location

- **Component**: `mobile/src/components/charts/InnovativeChart.tsx`
- **Usage**: `mobile/src/navigation/HomeScreen.tsx` (line ~1079)
- **Data Source**: Portfolio history from `usePortfolioHistory()` hook

---

## 🎉 Ready to Explore!

Reload the app (⌘R) and scroll to the "What moved this" section to see all the chart features!

