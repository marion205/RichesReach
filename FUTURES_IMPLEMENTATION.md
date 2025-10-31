# Tomorrow - Futures Trading (Simple Jobs-Style)

## What We Built

**Name**: "Tomorrow" - Trade tomorrow's markets today  
**Style**: One sentence, one visual, one action (just like "Why Now")

## Files Created

### Mobile (React Native)
- `mobile/src/features/futures/screens/TomorrowScreen.tsx` - Main screen
- `mobile/src/features/futures/services/FuturesService.ts` - API client
- `mobile/src/features/futures/types/FuturesTypes.ts` - Type definitions

### Backend (FastAPI)
- `backend/backend/core/futures_api.py` - Simple REST API

### Navigation
- Added to `AppNavigator.tsx`
- Added to `InvestAdvancedSheet.tsx` (Advanced menu)

## Design Principles

1. **Simple Names**: "Tomorrow" not "Futures Trading Platform"
2. **One Sentence**: "Calm market. Hedge portfolio with micro contract—max loss $50."
3. **Clear Actions**: Buy or Sell (no complex UI)
4. **Leverages Existing**: Uses same patterns as Options screens

## Features

### Level 0 (Default - What We Built)
- Simple recommendation cards
- One sentence "Why Now" explanation
- Max loss, max gain, probability shown
- One-tap trade (starts with micro contracts)
- Paper trading ready

### Future Levels (To Build)
- **Level 1**: Live micro futures (MES, MNQ, MYM)
- **Level 2**: Advanced strategies (spreads, hedges)
- **Level 3**: Expert tools (full chain, Greeks, IV surface)

## API Endpoints

```
GET  /api/futures/recommendations  - Get simple recommendations
POST /api/futures/order            - Place order (symbol, side, quantity)
GET  /api/futures/positions        - Get current positions
```

## Next Steps

1. **Wire to IBKR** (Phase 2):
   - Create `ibkr_adapter.py`
   - Connect to TWS API
   - Replace mock data

2. **Add Policy Engine**:
   - Suitability gates
   - Max loss caps
   - Leverage limits

3. **Enhance Options** (Level 0-2):
   - Build on existing OptionsCopilot
   - Add progressive disclosure
   - Keep it simple

## Usage

Access via:
- **Invest tab** → **Advanced** → **Tomorrow**
- Direct navigation: `navigation.navigate('Tomorrow')`

## Jobs-Style Philosophy

- **Tomorrow**: One word, clear meaning
- **Why Now**: One sentence explanation
- **Simple**: Max loss, max gain, probability
- **One Action**: Buy or Sell

No clutter. No confusion. Just what matters.

