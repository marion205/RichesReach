# Microstructure Awareness Roadmap

## Goal
Add order-book intelligence to make signals "microstructure-aware" without needing HFT infrastructure.

## What We're Building

### Phase 1: L2 Data Integration (Weeks 1-3)

#### 1.1 Microstructure Service
**File**: `deployment_package/backend/core/microstructure_service.py`

```python
class MicrostructureService:
    """
    Provides order-book intelligence for day trading signals.
    Not HFT-level, but good enough for 1-5 minute intraday decisions.
    """
    
    def get_order_book_features(self, symbol: str) -> Dict:
        """
        Fetch L2 data and compute features:
        - Best bid/ask + sizes
        - Depth on top 5 levels
        - Order imbalance
        - Spread metrics
        """
        pass
    
    def calculate_imbalance(self, bids: List, asks: List) -> float:
        """
        Order imbalance: (sum(bid_sizes) - sum(ask_sizes)) / total
        Returns: -1 (bearish) to +1 (bullish)
        """
        pass
    
    def is_tradeable(self, symbol: str, mode: str) -> Dict:
        """
        Check if symbol passes microstructure filters.
        Returns: {'tradeable': bool, 'reason': str}
        """
        # SAFE: spread < 0.5%, depth > $100k
        # AGGRESSIVE: spread < 1.0%, depth > $50k
        pass
```

#### 1.2 Data Sources
- **Primary**: Polygon L2 snapshot API
- **Fallback**: Alpaca market data API
- **Tertiary**: IEX Cloud (if available)

#### 1.3 Integration Points
1. Add to `_get_real_intraday_day_trading_picks()` - filter out thin books
2. Add imbalance as feature in ML scoring
3. Mark signals as "microstructure risky" if depth is thin

### Phase 2: Execution Quality Filters (Week 4)

#### 2.1 Spread Filter
```python
def _apply_spread_filter(pick, mode):
    """Don't show as SAFE if spread > 0.5%"""
    if mode == "SAFE" and pick['spread_bps'] > 50:
        return None
    if mode == "AGGRESSIVE" and pick['spread_bps'] > 100:
        return None
    return pick
```

#### 2.2 Depth Filter
```python
def _apply_depth_filter(pick, mode):
    """Avoid symbols with thin order books"""
    if mode == "SAFE" and pick['depth_dollars'] < 100_000:
        return None
    if mode == "AGGRESSIVE" and pick['depth_dollars'] < 50_000:
        return None
    return pick
```

#### 2.3 Gap & Halt Filters
```python
def _apply_gap_filter(pick):
    """Skip symbols with > 5% gap in last 5 minutes"""
    if pick['gap_pct'] > 0.05:
        return None
    return pick

def _apply_halt_filter(pick):
    """Skip symbols with recent halts"""
    if pick['has_recent_halt']:
        return None
    return pick
```

### Phase 3: ML Features (Week 5)

#### 3.1 New Features
Add to feature set:
- `order_imbalance`: -1 to 1 (bullish/bearish)
- `bid_depth`: Total bid size in top 5 levels
- `ask_depth`: Total ask size in top 5 levels
- `spread_bps`: Bid-ask spread in basis points
- `depth_imbalance`: (bid_depth - ask_depth) / total

#### 3.2 Feature Integration
```python
# In _process_intraday_data()
microstructure = microstructure_service.get_order_book_features(symbol)
features.update({
    'order_imbalance': microstructure['imbalance'],
    'bid_depth': microstructure['bid_depth'],
    'ask_depth': microstructure['ask_depth'],
    'spread_bps': microstructure['spread_bps'],
    'depth_imbalance': microstructure['depth_imbalance'],
})
```

## Success Metrics

- ✅ 50-150 symbols have L2 data available
- ✅ Spread/depth filters reduce bad fills by 30%+
- ✅ Order imbalance improves entry timing
- ✅ Signals marked as "microstructure risky" when appropriate

## Implementation Timeline

- **Week 1**: Design service architecture, set up Polygon L2 API
- **Week 2**: Implement L2 data fetching and feature extraction
- **Week 3**: Integrate into day trading picks pipeline
- **Week 4**: Add execution quality filters
- **Week 5**: Add microstructure features to ML scoring

## Data Requirements

- **Polygon L2 Snapshot**: ~$200-500/month
- **Alpaca Market Data**: Free (with account)
- **Caching**: 5-10 second cache (L2 data changes frequently)

## Expected Impact

- **Fill Quality**: 30-50% improvement in slippage
- **Signal Quality**: Better entry timing with order imbalance
- **User Experience**: Fewer "can't fill" situations

