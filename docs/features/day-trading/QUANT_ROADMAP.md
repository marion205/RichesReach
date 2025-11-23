# RichesReach Quant Roadmap: "Citadel Discipline for Real People"

## Vision

Transform RichesReach from a single day-trading engine into a **mini quant shop** with:
- Microstructure-aware signals (not HFT, but smart)
- Dozens of tracked strategies (breadth of alphas)
- Retail execution intelligence (smart order suggestions)
- Automated R&D pipeline (1-2 people punching above weight)

**Timeline**: 6-12 months to "mini-Citadel" status

---

## Phase 1: Microstructure Awareness (Months 1-2)

### Goal
Add order-book intelligence to make signals "microstructure-aware" without needing HFT infrastructure.

### What to Build

#### 1.1 Level 2 Data Integration
**Priority**: High  
**Effort**: 2-3 weeks

```python
# New service: core/microstructure_service.py
class MicrostructureService:
    def get_order_book_features(self, symbol: str) -> Dict:
        """
        Fetch L2 data and compute:
        - Best bid/ask + sizes
        - Depth on top 5 levels
        - Order imbalance
        - Spread metrics
        """
        # Use Polygon L2 snapshot or Alpaca market data
        pass
    
    def calculate_imbalance(self, bids: List, asks: List) -> float:
        """Order imbalance: (sum(bid_sizes) - sum(ask_sizes)) / total"""
        pass
    
    def is_tradeable(self, symbol: str, mode: str) -> bool:
        """Check if symbol passes microstructure filters"""
        # SAFE: spread < 0.5%, depth > $100k
        # AGGRESSIVE: spread < 1.0%, depth > $50k
        pass
```

**Integration Points**:
- Add to `_get_real_intraday_day_trading_picks()` - filter out thin books
- Add imbalance as feature in ML scoring
- Mark signals as "microstructure risky" if depth is thin

**Data Sources**:
- Polygon L2 snapshot API
- Alpaca market data API
- IEX Cloud (if available)

#### 1.2 Execution Quality Filters
**Priority**: High  
**Effort**: 1 week

Add filters to day trading picks:
- Spread filter: "Don't show as SAFE if spread > 0.5%"
- Depth filter: "Avoid symbols with < $100k depth"
- Gap filter: "Skip symbols with > 5% gap in last 5 minutes"
- Halt filter: "Skip symbols with recent halts"

**Implementation**:
```python
def _apply_microstructure_filters(pick, mode):
    """Apply execution-quality guardrails"""
    if mode == "SAFE":
        if pick['spread_bps'] > 50:  # 0.5%
            return None
        if pick['depth_dollars'] < 100_000:
            return None
    # ... more filters
```

#### 1.3 Order Book Features in ML
**Priority**: Medium  
**Effort**: 1 week

Add to feature set:
- `order_imbalance`: -1 to 1 (bullish/bearish)
- `bid_depth`: Total bid size in top 5 levels
- `ask_depth`: Total ask size in top 5 levels
- `spread_bps`: Bid-ask spread in basis points
- `depth_imbalance`: (bid_depth - ask_depth) / total

**Impact**: Better signal quality, especially for entry timing

### Success Metrics
- ✅ 50-150 symbols have L2 data available
- ✅ Spread/depth filters reduce bad fills by 30%+
- ✅ Order imbalance improves entry timing

---

## Phase 2: Breadth of Alphas (Months 3-6)

### Goal
Grow from 1-2 strategies to 20-50 tracked strategies across timeframes and universes.

### Strategy Expansion Plan

#### 2.1 Timeframe Expansion

**Very-Short Intraday** (Current - Day Trading)
- ✅ SAFE mode (5-45 min holds)
- ✅ AGGRESSIVE mode (5-25 min holds)

**End-of-Day Swing** (New)
- **Swing Momentum**: Hold 2-5 days, catch multi-day moves
- **Swing Breakout**: Enter on EOD breakouts, hold 3-7 days
- **Swing Mean Reversion**: Fade extremes, hold 2-4 days

**Weekly/Sector Rotation** (New)
- **Sector Momentum**: Rotate into strongest sectors weekly
- **Factor Rotation**: Value/Growth/Momentum factor shifts
- **Index Arbitrage**: SPY/QQQ/IWM relative strength

#### 2.2 Universe Expansion

**Current**: Large-cap US stocks

**Add**:
- **ETF Universe**: SPY, QQQ, IWM, sector ETFs, factor ETFs
- **High-Dividend**: Dividend aristocrats, REITs
- **Low-Vol**: Minimum volatility ETFs, defensive stocks
- **Growth**: High-growth tech, biotech
- **Value**: Deep value, contrarian plays

#### 2.3 Regime-Based Strategies

**Current**: Regime detection exists, but not used for strategy selection

**Add**:
- **Bull Regime**: Momentum strategies only
- **Bear Regime**: Short-only or defensive strategies
- **Chop Regime**: Mean reversion, range-bound strategies
- **Volatility Regime**: High-vol vs low-vol strategies

#### 2.4 Use-Case Strategies

**Overnight Gap Edge**
- Scan for pre-market gaps
- Filter by volume, news, technical setup
- Enter on gap fill or continuation

**Low-Vol Growth**
- Find high-quality growth stocks in low-vol periods
- Enter on breakouts with tight stops
- Hold 3-7 days

**Dividend + Buyback**
- Screen for companies with both
- Enter on technical setups
- Hold for dividend capture + capital gains

### Implementation Plan

#### Month 3: Swing Trading Engine
```python
# New: core/swing_trading_engine.py
class SwingTradingEngine:
    def generate_swing_signals(self, mode: str) -> List[Dict]:
        """Generate 2-5 day swing signals"""
        # Similar structure to day trading, but:
        # - 15-min bars instead of 5-min
        # - Hold 2-5 days instead of minutes
        # - Different risk parameters
        pass
```

#### Month 4: ETF Universe
```python
# Extend universe builders
def _get_etf_universe(mode: str) -> List[str]:
    """Get ETF symbols for strategy"""
    # Sector ETFs, factor ETFs, index ETFs
    pass
```

#### Month 5: Regime-Based Strategy Selection
```python
# New: core/regime_strategy_router.py
class RegimeStrategyRouter:
    def get_active_strategies(self, current_regime: str) -> List[str]:
        """Return strategies active in current regime"""
        # Bull: momentum strategies
        # Bear: short/defensive strategies
        # Chop: mean reversion strategies
        pass
```

#### Month 6: Use-Case Strategies
- Implement 3-5 specialized strategies
- Each gets its own StrategyPerformance row
- Track separately

### Strategy Tracking

**Each strategy gets**:
- Unique ID and name
- StrategyPerformance row
- Investment Committee health checks
- A/B testing capability

**Example StrategyPerformance rows**:
```
- day_trading_safe_v1
- day_trading_aggressive_v1
- swing_momentum_v1
- swing_breakout_v1
- etf_sector_rotation_v1
- overnight_gap_edge_v1
- low_vol_growth_v1
- ... (20-50 total)
```

### Success Metrics
- ✅ 20+ distinct strategies live
- ✅ Each tracked in StrategyPerformance
- ✅ Investment Committee evaluates all
- ✅ Users can select strategies by persona

---

## Phase 3: Execution Intelligence (Months 4-7)

### Goal
Build retail execution IQ that's miles ahead of "market buy at open".

### What to Build

#### 3.1 Smart Order Suggestions
**Priority**: High  
**Effort**: 2-3 weeks

For each signal, generate:
- **Suggested order type**: Limit, bracket, stop-limit
- **Suggested price band**: "Place limit between $X.10 – $X.20"
- **Suggested time-in-force**: DAY vs IOC
- **Entry strategy**: "Wait for pullback to VWAP" vs "Enter now"

```python
# New: core/execution_advisor.py
class ExecutionAdvisor:
    def suggest_order(self, signal: Dict) -> Dict:
        """
        Returns:
        {
            'order_type': 'LIMIT',
            'price_band': [150.10, 150.20],
            'time_in_force': 'DAY',
            'entry_strategy': 'Wait for VWAP pullback',
            'bracket_legs': {
                'stop': 147.50,
                'target1': 153.00,
                'target2': 156.00
            }
        }
        """
        pass
```

#### 3.2 Broker Integration
**Priority**: High  
**Effort**: 3-4 weeks

**Alpaca Integration** (First)
```python
# New: core/broker_integration/alpaca_adapter.py
class AlpacaOrderAdapter:
    def create_order_from_signal(self, signal: Dict, user: User) -> Dict:
        """Generate Alpaca order JSON from signal"""
        # Pre-fill: symbol, qty, side, limit price, bracket legs
        # User just swipes to confirm
        pass
    
    def submit_order(self, order: Dict) -> Dict:
        """Submit to Alpaca API"""
        pass
```

**Frontend**: "Swipe to Trade" button that:
1. Shows suggested order details
2. User swipes to confirm
3. Order pre-filled, user just clicks "Submit" in broker UI

#### 3.3 Execution Quality Tracking
**Priority**: Medium  
**Effort**: 2-3 weeks

For users who link accounts:
- Compare actual fill vs:
  - Mid-price at signal time
  - VWAP over next N minutes
- Compute:
  - Average slippage
  - % of trades where user chased price
  - Fill quality score

```python
# New: core/execution_quality_tracker.py
class ExecutionQualityTracker:
    def analyze_fill(self, signal: DayTradingSignal, actual_fill: Dict) -> Dict:
        """Compare actual fill to signal"""
        slippage = actual_fill['price'] - signal.entry_price
        vwap_slippage = actual_fill['price'] - vwap_at_fill_time
        
        return {
            'slippage': slippage,
            'vwap_slippage': vwap_slippage,
            'chased_price': abs(slippage) > 0.5%,  # User chased
            'quality_score': self._calculate_quality(slippage, vwap_slippage)
        }
    
    def generate_coaching_tips(self, user: User) -> List[str]:
        """Surface execution improvement tips"""
        # "Your average slippage is 0.35%. Using limits in this band would cut it to 0.15%."
        pass
```

### Success Metrics
- ✅ Order suggestions reduce slippage by 50%+
- ✅ Broker integration reduces user errors by 80%+
- ✅ Execution quality tracking shows measurable improvement

---

## Phase 4: R&D Automation (Months 5-12)

### Goal
Build automated research pipeline so 1-2 people can test hundreds of strategy variants.

### What to Build

#### 4.1 Daily Research Jobs
**Priority**: High  
**Effort**: 2-3 weeks

**Nightly Pipeline**:
```python
# New: core/management/commands/daily_research_pipeline.py
class Command(BaseCommand):
    def handle(self):
        # 1. Pull DayTradingSignal + market data
        signals = DayTradingSignal.objects.filter(...)
        
        # 2. Retrain or re-score models
        ml_scorer.retrain_if_needed(signals)
        
        # 3. Evaluate candidate tweaks
        candidates = self._generate_candidates()
        for candidate in candidates:
            performance = self._evaluate_candidate(candidate)
            StrategyPerformance.objects.create(
                strategy_id=f"{candidate.name}_v{candidate.version}",
                ...
            )
        
        # 4. Promote winners, retire losers
        self._promote_winners()
        self._retire_losers()
```

**Cron Schedule**:
```bash
# Nightly research pipeline
0 2 * * * python manage.py daily_research_pipeline

# Weekly strategy evaluation
0 3 * * 1 python manage.py strategy_health_check --all

# Monthly performance report
0 4 1 * * python manage.py generate_performance_report
```

#### 4.2 Automated A/B Testing
**Priority**: High  
**Effort**: 3-4 weeks

**Split Testing Framework**:
```python
# New: core/strategy_ab_testing.py
class StrategyABTester:
    def create_test(self, control_strategy: str, candidate_strategy: str):
        """Create A/B test between two strategy versions"""
        pass
    
    def split_signals(self, signals: List) -> Dict:
        """Split signals 50/50 between control and candidate"""
        pass
    
    def evaluate_test(self, test_id: str) -> Dict:
        """After X days, compare performance"""
        # Compare: Sharpe, win rate, DD
        # Promote winner, retire loser
        pass
```

**Example Tests**:
- Current scoring vs new feature weights
- CORE universe vs DYNAMIC_MOVERS universe
- Different volatility filters
- Different momentum windows

#### 4.3 Research Harness
**Priority**: Medium  
**Effort**: 2-3 weeks

**Jupyter Notebook Integration**:
- Notebooks for exploratory analysis
- Scripts to backtest strategy variants
- Automated evaluation against StrategyPerformance

**Cloud Compute**:
- Use AWS/GCP for heavy backtests
- Parallelize strategy evaluation
- Store results in database

### Success Metrics
- ✅ 10+ strategy variants tested per month
- ✅ Automated promotion/retirement of strategies
- ✅ Research pipeline runs without manual intervention

---

## Phase 5: Product & Marketing (Months 7-12)

### Goal
Package all of this as "Citadel discipline for real people".

### Product Positioning

#### 5.1 Persona-Based Strategy Selection
**Frontend**: Let users choose persona:
- **"Day Trader"**: Day trading strategies (SAFE/AGGRESSIVE)
- **"Swing Trader"**: Swing momentum, breakout strategies
- **"Long-Term Builder"**: ETF rotation, dividend strategies

Each persona shows 3-5 curated strategies.

#### 5.2 Performance Dashboard
**Show users**:
- Their strategy performance (if they linked account)
- Overall strategy stats (transparency)
- "How we compare to benchmarks"

#### 5.3 Marketing Messages

**"Citadel Discipline for Real People"**
- "We test hundreds of strategy variants, just like Citadel"
- "Every signal is tracked and evaluated"
- "Strategies that don't meet our standards get retired"
- "Real performance data, not marketing fluff"

**"Institutional-Grade, Retail-Friendly"**
- "The same tracking Citadel uses, but you can understand it"
- "Professional risk management, simplified"
- "Quality over quantity - we show 3 picks, not 100s"

### Success Metrics
- ✅ 3+ personas with curated strategies
- ✅ Performance dashboard live
- ✅ Marketing materials with real data

---

## Implementation Priority

### Must-Have (Months 1-3)
1. ✅ Microstructure filters (spread, depth)
2. ✅ Smart order suggestions
3. ✅ Swing trading engine (1-2 strategies)
4. ✅ Daily research pipeline

### Should-Have (Months 4-6)
5. ✅ Broker integration (Alpaca)
6. ✅ Execution quality tracking
7. ✅ 10+ strategies across timeframes
8. ✅ A/B testing framework

### Nice-to-Have (Months 7-12)
9. ✅ L2 order book features in ML
10. ✅ 20-50 total strategies
11. ✅ Regime-based strategy routing
12. ✅ Persona-based product

---

## Resource Requirements

### Technical
- **Backend**: 1-2 developers
- **Data**: Polygon L2 API, Alpaca market data
- **Infrastructure**: Cloud compute for backtests (AWS/GCP)
- **Time**: 6-12 months for full roadmap

### Data Costs
- Polygon L2: ~$200-500/month
- Alpaca market data: Free (with account)
- Cloud compute: ~$50-200/month

### Total Investment
- **Development**: 6-12 months
- **Data/Infra**: ~$300-700/month
- **Result**: Mini-Citadel capabilities for retail

---

## Success Criteria

### 6 Months
- ✅ Microstructure-aware signals
- ✅ 10+ tracked strategies
- ✅ Smart order suggestions
- ✅ Automated research pipeline

### 12 Months
- ✅ 20-50 tracked strategies
- ✅ Broker integration live
- ✅ Execution quality tracking
- ✅ "Citadel discipline" positioning in market

---

## Next Steps

1. **Week 1**: Design microstructure service architecture
2. **Week 2-3**: Implement L2 data integration
3. **Week 4**: Add execution quality filters
4. **Month 2**: Build swing trading engine
5. **Month 3**: Start daily research pipeline

See individual phase documents for detailed implementation plans.

