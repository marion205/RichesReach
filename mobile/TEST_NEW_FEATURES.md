# 🎓 Testing New Educational Features

## Quick Reload Instructions

### Option 1: Reload in Simulator/Device
- **iOS Simulator**: Press `Cmd + R` or shake device → "Reload"
- **Android**: Press `R` twice or shake device → "Reload"
- **Expo Go**: Shake device → "Reload"

### Option 2: Restart Metro Bundler
```bash
cd mobile
# Kill existing Metro
pkill -f "expo start"

# Start fresh (picks up new files)
npx expo start --clear
```

## 🧪 Feature Testing Checklist

### 1. ResearchScreen (`Research` tab in StockScreen)
- [ ] Navigate to Research tab
- [ ] Tap on **RSI (14)** - Should show tooltip explaining overbought/oversold
- [ ] Tap on **MACD** - Should show tooltip explaining momentum signals
- [ ] Tap on **MA 50** - Should show tooltip explaining medium-term trend
- [ ] Tap on **MA 200** - Should show tooltip explaining long-term trend
- [ ] Tap on **Support** - Should show tooltip explaining support levels
- [ ] Tap on **Resistance** - Should show tooltip explaining resistance levels

### 2. StockScreen (Technical Indicators Section)
- [ ] Navigate to any stock detail
- [ ] Scroll to "Technical Indicators" section
- [ ] Tap on **RSI (14)** - Should show tooltip
- [ ] Tap on **MACD** - Should show tooltip
- [ ] Tap on **SMA 20** - Should show tooltip
- [ ] Tap on **SMA 50** - Should show tooltip
- [ ] Tap on **Bollinger Upper/Lower** - Should show tooltip

### 3. StockDetailScreen (Chart Tab)
- [ ] Navigate to any stock → **Chart** tab
- [ ] Look for **chart annotations** on the right side:
  - [ ] Red "Stop Loss" line with tooltip
  - [ ] Blue "Current" line with tooltip
  - [ ] Green "Take Profit" line with tooltip
- [ ] Tap on each annotation to see educational tooltip

### 4. DayTradingScreen
- [ ] Navigate to **Day Trading** screen
- [ ] For each pick card:
  - [ ] Tap **"Why This Trade?"** button - Should open modal with explanation
  - [ ] Check **Risk Management** section - Tooltips on Stop, Target, Time Stop, ATR
  - [ ] Check **Risk/Reward Diagram** below risk metrics
- [ ] Tap **"Learn"** button in header - Should open learning library modal

### 5. SwingDayTradingScreen
- [ ] Navigate to **Swing Trading** → Daily Top-3 Picks
- [ ] In Risk section:
  - [ ] Tap **"Stop"** - Should show tooltip explaining ATR-based stops
  - [ ] Tap **"Target"** - Should show tooltip explaining risk:reward
  - [ ] Tap **"Time Stop"** - Should show tooltip explaining time discipline

### 6. OrderForm (When placing trades)
- [ ] Navigate to any stock → **Trade** tab
- [ ] Tap **Buy/Sell** button
- [ ] In order form:
  - [ ] Tap **"Stop Price"** label - Should show tooltip
  - [ ] Check **"Risk Preview"** card showing risk per share and total risk
  - [ ] Check **Risk/Reward Diagram** showing entry, stop, target visually
- [ ] Before submitting:
  - [ ] Should see **Pre-Execution Risk Check Modal** (if stop loss set)
  - [ ] Tap **"Learn About Trading"** button - Should open learning modal

### 7. TradingScreen
- [ ] Navigate to main **Trading** screen
- [ ] Look for **"Help"** button (book icon) in header
- [ ] Tap it - Should open **Learn While Trading Modal**

## 🐛 Troubleshooting

### If tooltips don't appear:
1. **Reload the app** (Cmd+R or shake device)
2. **Clear Metro cache**: `npx expo start --clear`
3. **Check console** for any errors

### If chart annotations don't show:
1. Make sure you're on the **Chart** tab (not Overview)
2. Stock must have `currentPrice` data
3. Check console for any errors

### If modals don't open:
1. Check console for JavaScript errors
2. Verify the component is imported correctly
3. Try reloading the app

## ✅ Expected Behavior

All tooltips should:
- ✅ Appear when you tap/click the indicator
- ✅ Show educational explanation
- ✅ Be dismissible by tapping outside
- ✅ Position correctly (top/bottom/left/right)

All modals should:
- ✅ Open smoothly with animation
- ✅ Show relevant educational content
- ✅ Have close button
- ✅ Be dismissible by tapping outside

All chart annotations should:
- ✅ Show on the right side of chart
- ✅ Position at correct price levels
- ✅ Have tooltips when tapped
- ✅ Use correct colors (red=stop, blue=entry, green=target)
