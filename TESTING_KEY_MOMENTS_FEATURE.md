# Testing the "Smart Storylines" / "Key Moments" Feature

## 🎯 Overview

The new feature adds interactive stock moments to charts with:
- **Interactive Chart**: Drag to explore key moments on the price chart
- **Story Mode**: Cinematic narration of stock events
- **Long-Press Gesture**: Long-press a moment dot to jump into Story Mode
- **Wealth Oracle Voice**: Custom TTS narration
- **Haptic Feedback**: Tactile feedback when interacting with moments

## 📍 Where to Find It

1. **Navigate to Stocks**:
   - Open the app
   - Tap on "Stocks" or navigate to the stock screen
   - You'll see a list of stocks (AAPL, MSFT, TSLA, etc.)

2. **Open a Stock Detail**:
   - Tap on any stock card (e.g., AAPL, TSLA, MSFT)
   - This opens the `StockDetailScreen`

3. **Go to Chart Tab**:
   - In the stock detail screen, tap the "Chart" tab
   - Scroll down to see the chart with moments

4. **Look for the Feature**:
   - The `StockMomentsIntegration` component is rendered below the main chart
   - You should see:
     - A chart with dots representing key moments
     - A "▶ Play Story" button

## 🧪 Testing Steps

### 1. Basic Chart Interaction
- **Drag on the chart**: Move your finger across the chart
- **Expected**: Chart highlights moments as you drag
- **Haptic feedback**: You should feel subtle vibrations when passing over moments

### 2. Play Story Mode (Button)
- **Tap "▶ Play Story" button**
- **Expected**:
  - Modal opens with cinematic story player
  - Intro slide appears (if enabled)
  - Story auto-plays through moments
  - Voice narration (if TTS service is running)
  - Progress indicator shows "X/Y moments listened"

### 3. Long-Press Gesture (Quick Start)
- **Long-press on a moment dot** on the chart
- **Expected**:
  - Story Mode opens immediately
  - **No intro slide** (skips intro)
  - Starts from that specific moment
  - Voice narration begins

### 4. Story Player Controls
- **Play/Pause**: Tap play/pause button
- **Next/Previous**: Use arrow buttons to navigate
- **Close**: Tap X or swipe down to close
- **Expected**: Smooth transitions, voice stops when paused

### 5. Analytics Tracking
- **Check console logs**: Look for analytics events
- **Expected**: Logs like:
  ```
  [MomentAnalytics] { type: 'moment_listened', ... }
  [MomentAnalytics] { type: 'story_close', listenedCount: 3, totalMoments: 5 }
  ```

## 🔧 Prerequisites

### Backend Requirements
1. **Backend running**: `http://localhost:8000`
2. **GraphQL endpoint**: `/graphql/`
3. **Stock moments data**: The backend needs `StockMoment` records in the database

### TTS Service (Optional)
- **Wealth Oracle TTS**: For voice narration
- **Default**: Falls back to `expo-speech` if TTS service unavailable
- **To enable**: Start TTS service at `http://localhost:8001` (or configure `TTS_API_BASE_URL`)

### Database Setup
The feature requires `StockMoment` records. To test with data:

1. **Create test moments** (via Django admin or API):
   ```python
   from core.models import StockMoment, MomentCategory
   from django.utils import timezone
   from datetime import timedelta
   
   StockMoment.objects.create(
       symbol='AAPL',
       timestamp=timezone.now() - timedelta(days=5),
       category=MomentCategory.NEWS,
       title='Product Launch',
       quick_summary='New iPhone released',
       deep_summary='Apple launched new iPhone with advanced features...',
       importance_score=0.8
   )
   ```

2. **Or use the worker** to generate moments:
   ```bash
   cd deployment_package/backend
   python core/stock_moment_worker.py
   ```

## 🐛 Troubleshooting

### Feature Not Showing
- **Check**: Is the chart tab selected?
- **Check**: Are there moments in the database for this symbol?
- **Check**: GraphQL query in `StockMomentsIntegration.tsx` - verify it's working
- **Check console**: Look for GraphQL errors

### No Voice Narration
- **Check**: Is TTS service running? (`http://localhost:8001`)
- **Check**: `TTS_API_BASE_URL` in environment variables
- **Fallback**: Should use `expo-speech` if TTS unavailable

### Chart Not Interactive
- **Check**: Is `ChartWithMoments` component rendering?
- **Check**: Are there moments in the data?
- **Check console**: Look for errors in chart rendering

### Long-Press Not Working
- **Check**: Press and hold for ~500ms on a moment dot
- **Check**: Are there moments visible on the chart?
- **Check console**: Look for `onMomentLongPress` events

## 📊 Expected UI Elements

1. **Chart with Moments**:
   - Line chart showing price over time
   - Dots/circles on the chart representing moments
   - Active moment highlighted when dragging

2. **Play Story Button**:
   - Button with "▶ Play Story" text
   - Appears below the chart when moments exist

3. **Story Player Modal**:
   - Full-screen or modal overlay
   - Current moment card with title and summary
   - Play/pause controls
   - Progress indicator
   - Navigation arrows
   - Close button

4. **Intro Slide** (if enabled):
   - Appears before first moment
   - Text: "Here's the story behind [SYMBOL]'s recent moves..."

## 🎨 Visual Indicators

- **Moment Dots**: Small circles on the chart at key timestamps
- **Active Moment**: Highlighted or larger when selected
- **Story Progress**: Shows "X/Y moments" or progress bar
- **Listening Indicator**: Shows which moments have been listened to

## 📝 Testing Checklist

- [ ] Chart displays with moments
- [ ] Can drag on chart to explore moments
- [ ] Haptic feedback works when passing over moments
- [ ] "Play Story" button appears and works
- [ ] Story Mode opens with intro (when using button)
- [ ] Long-press on dot opens Story Mode without intro
- [ ] Voice narration plays (if TTS available)
- [ ] Play/pause controls work
- [ ] Next/previous navigation works
- [ ] Progress tracking works
- [ ] Analytics events are logged
- [ ] Story closes properly
- [ ] Chart updates when story plays (active moment highlights)

## 🚀 Quick Test Commands

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check GraphQL endpoint
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query":"{ stockMoments(symbol: \"AAPL\", range: ONE_MONTH) { id title } }"}'

# Check TTS service (if running)
curl http://localhost:8001/health
```

## 📱 Testing on Physical Device

1. **Update environment**: Use LAN IP instead of localhost
2. **Start backend**: Ensure it's accessible from device
3. **Start Expo**: Use `start_with_env.sh` to auto-detect IP
4. **Connect device**: Scan QR code or enter URL manually

---

**Note**: The feature requires stock moments data in the database. If you don't see moments, create some test data first using the Django admin or the worker script.

