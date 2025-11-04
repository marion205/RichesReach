# 📊 Chart Testing Guide

## 🎯 How to Access Chart Test Screen

### Method 1: Navigation Command (Recommended)
In your app, add a button or use the console:

```javascript
// In HomeScreen or any screen, add a test button:
<TouchableOpacity onPress={() => navigateTo('chart-test')}>
  <Text>Test Chart</Text>
</TouchableOpacity>
```

### Method 2: Direct Navigation
If you have access to the navigation function:
- Navigate to: `'chart-test'`
- The screen will load in isolation

### Method 3: Temporary Test Link
Add this to HomeScreen temporarily:
```tsx
<TouchableOpacity 
  style={{ padding: 16, backgroundColor: '#0F62FE', borderRadius: 8, margin: 16 }}
  onPress={() => navigateTo('chart-test')}
>
  <Text style={{ color: '#FFFFFF', fontWeight: '600' }}>🧪 Test Chart Features</Text>
</TouchableOpacity>
```

---

## ✨ Features to Test

### 1. **Visual Elements**
- ✅ **Regime Bands**: Colored backgrounds (green=trend, yellow=chop, red=shock)
- ✅ **Confidence Glass**: Semi-transparent blue prediction bands (80% and 50%)
- ✅ **Event Markers**: Colored dots showing earnings/Fed decisions
- ✅ **Driver Lines**: Vertical colored lines (news, macro, flow, etc.)

### 2. **Interactive Gestures**
- ✅ **Pinch to Zoom**: Pinch in/out on chart
- ✅ **Pan/Scroll**: Swipe left/right when zoomed
- ✅ **Tap Events**: Tap blue/red dots for details
- ✅ **Tap Drivers**: Tap colored vertical lines for explanations

### 3. **Controls**
- ✅ **Data Range**: Test with 7/30/90 day datasets
- ✅ **Regenerate**: Generate new sample data

---

## 🛡️ Safety Features

1. **Delayed Loading**: Chart loads 1 second after screen mount to prevent freeze
2. **Isolated Environment**: Doesn't affect main app if it crashes
3. **Easy Exit**: Close button to return to home
4. **Error Handling**: Shows loading state and warnings

---

## ⚠️ Testing Notes

### If Chart Freezes:
1. **Force Quit Simulator**: ⌘Q, then restart
2. **Check Console**: Look for Skia/Canvas errors
3. **Reduce Data**: Try 7-day dataset first
4. **Restart Metro**: `npx expo start -c`

### If Chart Doesn't Load:
- Check Metro logs for module errors
- Verify `InnovativeChartSkia.tsx` has default export
- Ensure backend is running (not needed for test screen)

### Performance Tips:
- Start with small datasets (7 days)
- Wait for "Loading chart..." to disappear
- Test gestures after chart fully renders
- Monitor console for warnings

---

## 🔧 Debugging

### Console Commands:
```javascript
// In React Native Debugger or console:
// Check if chart is mounted
console.log('Chart mounted:', document.querySelector('[data-testid="chart"]'));

// Force reload
// Press ⌘R in simulator
```

### Common Issues:
1. **"Module has no export"**: Check `InnovativeChartSkia.tsx` default export
2. **"Network request failed"**: Test screen doesn't need backend, ignore
3. **White screen**: Chart may be loading, wait 1-2 seconds
4. **Freeze on mount**: Skia issue - chart needs optimization

---

## 📝 Next Steps

Once testing confirms chart works:
1. Re-enable chart in HomeScreen with proper lazy loading
2. Add error boundaries around chart component
3. Monitor production performance metrics
4. Consider SVG alternative if Skia remains problematic

---

## 🚀 Quick Start

1. **Navigate to test screen**: `navigateTo('chart-test')`
2. **Wait for chart to load**: See "Loading chart..." disappear
3. **Test gestures**: Pinch, pan, tap
4. **Try different datasets**: 7/30/90 days
5. **Check console**: Monitor for errors

**Enjoy testing! 🎉**

