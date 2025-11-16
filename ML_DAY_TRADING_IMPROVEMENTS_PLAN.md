# ML Day Trading Improvements - Implementation Plan

## Current State Analysis

### What We Have ✅

1. **Frontend (DayTradingScreen.tsx)**:
   - Expects `dayTradingPicks` query with features:
     - `momentum15m`, `rvol10m`, `vwapDist`, `breakoutPct`, `spreadBps`, `catalystScore`
   - Risk management: `atr5m`, `sizeShares`, `stop`, `targets`, `timeStopMin`
   - Two modes: `SAFE` and `AGGRESSIVE`
   - Currently using mock data when backend unavailable

2. **Backend ML Services**:
   - `ml_service.py` - Basic ML scoring (R² = 0.023)
   - `improved_ml_service.py` - Enhanced features (MACD, Bollinger, Volume)
   - `integrated_ml_system.py` - Market + alternative data integration
   - Current features: SMA, EMA, MACD, RSI, Bollinger Bands, Volume, Volatility

3. **Missing**: 
   - **No `dayTradingPicks` resolver** - Need to implement
   - Limited day-trading specific features
   - No candlestick pattern detection
   - No regime detection
   - No sentiment integration for day trading

---

## Integration Plan: Book Concepts → ML Features

### Phase 1: Feature Engineering Service (Week 1)

Create `day_trading_feature_service.py` that extracts all book-based features:

#### A. From "Day Trading 101" (Joe Duarte)

**1. Candlestick Pattern Features**
```python
def extract_candlestick_features(ohlcv_data: pd.DataFrame) -> Dict:
    """Extract candlestick patterns as binary features"""
    features = {}
    
    # Body/wick ratios
    features['body_pct'] = (close - open) / open
    features['upper_wick_pct'] = (high - max(open, close)) / open
    features['lower_wick_pct'] = (min(open, close) - low) / open
    features['range_pct'] = (high - low) / open
    
    # Gap features
    features['gap_up_pct'] = (open_t - close_{t-1}) / close_{t-1}
    features['gap_down_pct'] = (open_t - close_{t-1}) / close_{t-1}
    
    # Pattern flags (binary)
    features['is_hammer'] = detect_hammer(ohlcv_data)
    features['is_shooting_star'] = detect_shooting_star(ohlcv_data)
    features['is_doji'] = detect_doji(ohlcv_data)
    features['is_engulfing_bull'] = detect_bullish_engulfing(ohlcv_data)
    features['is_engulfing_bear'] = detect_bearish_engulfing(ohlcv_data)
    features['is_marubozu'] = detect_marubozu(ohlcv_data)
    
    return features
```

**2. Classic Indicators (Already have, but enhance)**
- ✅ SMA_5, SMA_20, SMA_50
- ✅ EMA_12, EMA_26
- ✅ MACD, MACD_Signal, MACD_Hist
- ✅ RSI_14
- ✅ Bollinger Bands (BB_Upper, BB_Middle, BB_Lower)
- ➕ Add: Stochastic (K, D), ATR_14

**3. Risk Management Features**
```python
def calculate_risk_features(price: float, atr: float, risk_per_trade: float) -> Dict:
    """Calculate position sizing and risk metrics"""
    return {
        'vol_norm_size': risk_per_trade / (atr * price),  # Position size
        'atr_pct': atr / price,  # ATR as % of price
        'risk_reward_ratio': 2.0,  # Default 2:1
        'max_risk_pct': 0.005 if mode == 'SAFE' else 0.012  # 0.5% or 1.2%
    }
```

#### B. From "The Ultimate Day Trader" (Jacob Bernstein)

**1. Volatility & Breakout Features**
```python
def extract_volatility_features(ohlcv_data: pd.DataFrame) -> Dict:
    """Bernstein's volatility expansion/contraction"""
    features = {}
    
    # Realized volatility
    features['realized_vol_20'] = returns[-20:].std()
    features['atr_14_pct'] = atr_14 / close
    features['true_range_pct'] = (high - low) / close
    
    # Breakout strength
    prior_range_20 = high[-20:].max() - low[-20:].min()
    features['breakout_pct'] = (close - high[-20:].max()) / prior_range_20
    features['breakdown_pct'] = (close - low[-20:].min()) / prior_range_20
    
    # Volatility expansion flags
    features['is_vol_expansion'] = atr_14_pct > percentile_80(atr_history)
    features['is_breakout'] = breakout_pct > threshold
    features['is_breakdown'] = breakdown_pct < -threshold
    
    return features
```

**2. Regime Detection**
```python
def detect_market_regime(ohlcv_data: pd.DataFrame) -> Dict:
    """Bernstein's regime classification"""
    sma_20 = ohlcv_data['close'].rolling(20).mean()
    sma_50 = ohlcv_data['close'].rolling(50).mean()
    atr_pct = atr_14 / close
    
    trend_strength = abs(sma_20 - sma_50) / close
    range_compression = prior_range_20 / prior_range_60
    
    regime = {
        'is_trend_regime': (trend_strength > 0.02) and (range_compression < 0.8),
        'is_range_regime': (trend_strength < 0.01) and (atr_pct < 0.015),
        'is_high_vol_chop': (atr_pct > 0.02) and (trend_strength < 0.01),
        'trend_strength': trend_strength,
        'regime_confidence': calculate_regime_confidence(...)
    }
    return regime
```

**3. Time-of-Day Features**
```python
def extract_time_features(timestamp: datetime) -> Dict:
    """Bernstein's seasonal patterns"""
    return {
        'dow': day_of_week,  # 0=Mon, 6=Sun
        'dom': day_of_month / 31.0,  # Normalized
        'hour_of_day': hour / 24.0,
        'is_opening_hour': 9.5 <= hour < 10.5,
        'is_closing_hour': 15.5 <= hour < 16.0,
        'is_month_end': day_of_month >= 28,
        'is_month_start': day_of_month <= 3,
        # Sin/cos encoding for cyclical patterns
        'dow_sin': sin(2 * pi * dow / 7),
        'dow_cos': cos(2 * pi * dow / 7),
        'hour_sin': sin(2 * pi * hour / 24),
        'hour_cos': cos(2 * pi * hour / 24)
    }
```

**4. Sentiment Features (Integrate with existing sentiment)**
```python
def extract_sentiment_features(symbol: str, sentiment_data: Dict) -> Dict:
    """Bernstein's sentiment index concept"""
    return {
        'sentiment_score': sentiment_data.get('score', 0),  # -1 to 1
        'sentiment_volume': sentiment_data.get('message_count', 0),
        'bull_ratio': sentiment_data.get('bull_count', 0) / total_messages,
        'extreme_sentiment_flag': bull_ratio > 0.85 or bull_ratio < 0.15,
        'sentiment_divergence': calculate_divergence(price_trend, sentiment_trend)
    }
```

---

### Phase 2: Day Trading Picks Resolver (Week 1-2)

Create `resolve_day_trading_picks` in `queries.py`:

```python
def resolve_day_trading_picks(self, info, mode: str = "SAFE"):
    """Generate day trading picks using ML + book strategies"""
    from .day_trading_feature_service import DayTradingFeatureService
    from .day_trading_ml_scorer import DayTradingMLScorer
    
    # 1. Get candidate symbols (liquid, high volume)
    universe = get_day_trading_universe(mode)  # 500-1000 symbols
    
    # 2. Extract features for each symbol
    feature_service = DayTradingFeatureService()
    ml_scorer = DayTradingMLScorer()
    
    picks = []
    for symbol in universe:
        # Get OHLCV data (1min, 5min bars)
        ohlcv_1m = get_intraday_data(symbol, interval='1min', limit=390)
        ohlcv_5m = get_intraday_data(symbol, interval='5min', limit=78)
        
        # Extract all features
        features = feature_service.extract_all_features(
            ohlcv_1m, ohlcv_5m, symbol
        )
        
        # ML scoring
        ml_score = ml_scorer.score(features)
        
        # Risk calculation
        risk_metrics = feature_service.calculate_risk(features, mode)
        
        # Filter by quality threshold
        if ml_score >= quality_threshold:
            picks.append({
                'symbol': symbol,
                'side': 'LONG' if features['momentum_15m'] > 0 else 'SHORT',
                'score': ml_score,
                'features': {
                    'momentum15m': features['momentum_15m'],
                    'rvol10m': features['realized_vol_10m'],
                    'vwapDist': features['vwap_distance'],
                    'breakoutPct': features['breakout_pct'],
                    'spreadBps': features['spread_bps'],
                    'catalystScore': features['catalyst_score']
                },
                'risk': risk_metrics
            })
    
    # Sort by score and return top picks
    picks.sort(key=lambda x: x['score'], reverse=True)
    return picks[:20]  # Top 20
```

---

### Phase 3: ML Model Training (Week 2-3)

**Target Variables** (from book concepts):

1. **Direction Prediction**:
   ```python
   y_dir = sign(price_{t+H} / price_t - 1)  # H = 15min, 30min, 1hr
   ```

2. **Hit Target Before Stop**:
   ```python
   y_hit = 1 if price hits +R% before -S%, else 0
   # R = reward (2%), S = stop (1%) for 2:1 R:R
   ```

3. **Regime Classification**:
   ```python
   y_regime ∈ {'trend_up', 'trend_down', 'range', 'high_vol_chop'}
   ```

**Feature Matrix** (100+ features):
- Candlestick patterns (20 features)
- Technical indicators (30 features)
- Volatility/breakout (15 features)
- Regime detection (10 features)
- Time features (10 features)
- Sentiment (10 features)
- Risk metrics (5 features)

**Model Architecture**:
- **Tabular**: XGBoost/LightGBM for initial implementation
- **Sequence**: LSTM/Transformer for pattern sequences (future)

---

### Phase 4: Integration Points

**1. Update `improved_ml_service.py`**:
- Add day-trading specific feature extraction
- Add regime detection model
- Add pattern recognition

**2. Create `day_trading_ml_scorer.py`**:
- Specialized scoring for intraday timeframes
- Real-time feature computation
- Caching for performance

**3. Update GraphQL Schema**:
- Add `dayTradingPicks` resolver
- Add `DayTradingPickType` with all features
- Add `DayTradingFeaturesType`

---

## Implementation Priority

### High Priority (Week 1)
1. ✅ Create `day_trading_feature_service.py` with all book features
2. ✅ Implement `resolve_day_trading_picks` resolver
3. ✅ Add candlestick pattern detection
4. ✅ Add volatility/breakout features

### Medium Priority (Week 2)
5. ✅ Regime detection model
6. ✅ Time-of-day features
7. ✅ Sentiment integration
8. ✅ Risk management features

### Low Priority (Week 3)
9. ✅ LSTM/Transformer for sequences
10. ✅ Pattern embeddings
11. ✅ Advanced setup detection

---

## Expected Improvements

### Current State
- Basic ML scoring (R² = 0.023)
- Limited features (SMA, EMA, MACD, RSI)
- No day-trading specific logic
- Mock data fallback

### After Integration
- **100+ features** from both books
- **Regime-aware** predictions (avoid bad markets)
- **Pattern recognition** (candlestick + chart patterns)
- **Time-aware** (opening/closing hour effects)
- **Sentiment-enhanced** (crowd psychology)
- **Risk-optimized** (position sizing, stops, targets)

### Performance Targets
- **Accuracy**: 55-60% win rate (realistic for day trading)
- **Sharpe Ratio**: > 1.5
- **Max Drawdown**: < 10%
- **Response Time**: < 100ms per symbol

---

## Next Steps

1. **Create feature service** (`day_trading_feature_service.py`)
2. **Implement resolver** (`resolve_day_trading_picks`)
3. **Train initial model** with book-based features
4. **Backtest** against historical data
5. **Deploy** and monitor performance

Would you like me to start implementing the feature service and resolver now?

