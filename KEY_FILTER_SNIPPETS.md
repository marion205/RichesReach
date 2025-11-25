# Key Filter Snippets - Day Trading Algorithm

## 🎯 **Core Filter Logic**

### **1. Dynamic Universe Filter (from `_get_dynamic_universe_from_polygon`)**

```python
# Mode-specific filters
if mode == "SAFE":
    min_price = 5.0  # Avoid penny stocks
    max_price = 500.0  # Avoid ultra-high priced stocks
    min_volume = 5_000_000  # 5M shares minimum
    min_market_cap = 50_000_000_000  # $50B minimum
    max_change_pct = 0.15  # Reject anything with >15% intraday move
else:  # AGGRESSIVE
    min_price = 2.0
    max_price = 500.0
    min_volume = 1_000_000  # 1M shares minimum
    min_market_cap = 1_000_000_000  # $1B minimum
    max_change_pct = 0.30  # Allow up to 30% moves

# Apply filters to each ticker
for ticker_obj in tickers[:100]:
    ticker_str = ticker_obj.get('ticker', '')
    
    # Basic symbol filters
    if not ticker_str or len(ticker_str) > 5:
        continue
    if ticker_str.endswith('X') or '.' in ticker_str:
        continue  # Skip ETFs and warrants
    
    # Extract data
    price = float(last_trade.get('p', 0))
    volume = int(ticker_obj.get('day', {}).get('v', 0))
    market_cap = float(ticker_obj.get('market_cap', 0) or 0)
    change_pct = abs(float(ticker_obj.get('todaysChangePct', 0) or 0)) / 100
    
    # Apply filters
    if price < min_price or price > max_price:
        continue
    if volume < min_volume:
        continue
    if change_pct > max_change_pct:  # KEY FILTER
        continue
    if market_cap > 0 and market_cap < min_market_cap:
        continue
    
    valid_symbols.append(ticker_str)
```

### **2. Volatility Filter (from `_process_intraday_data`)**

```python
# Calculate volatility from intraday bars
if len(bars) > 1:
    prices = [bar['c'] for bar in bars]
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    volatility = np.std(returns) if returns else 0
else:
    volatility = 0

# Mode-specific volatility limits
mode_max_volatility = 0.03 if mode == "SAFE" else 0.08

# Filter out high volatility
if volatility > mode_max_volatility:
    logger.debug(f"⚠️ {symbol} filtered: volatility {volatility:.4f} > max {mode_max_volatility}")
    return None
```

### **3. Momentum Filter**

```python
# Calculate 15-minute momentum
momentum15m = (current_price - price_15m_ago) / price_15m_ago if price_15m_ago > 0 else 0

# Mode-specific momentum requirements
if mode == "SAFE":
    if momentum15m < 0.001:  # Require small positive momentum
        return None
else:  # AGGRESSIVE
    if abs(momentum15m) < 0.0001:  # Very minimal movement required (0.01%)
        return None
```

### **4. Quality Score Threshold**

```python
# Calculate composite score
score = momentum_score + volume_score + volatility_score

# Apply quality threshold
quality_threshold = 2.5 if mode == "SAFE" else 2.0

if score < quality_threshold:
    continue  # Skip low-quality picks
```

---

## 🔧 **How to Adapt for Your Setup**

### **Quick Filter Template**

```python
def should_filter_stock(symbol, price, volume, market_cap, change_pct, volatility, mode="AGGRESSIVE"):
    """Universal filter function - adapt these thresholds"""
    
    # Basic filters
    if len(symbol) > 5 or '.' in symbol or symbol.endswith('X'):
        return True, "Symbol format"
    
    # Mode-specific thresholds
    filters = {
        "SAFE": {
            "min_price": 5.0,
            "max_price": 500.0,
            "min_volume": 5_000_000,
            "min_market_cap": 50_000_000_000,
            "max_change_pct": 0.15,
            "max_volatility": 0.03,
        },
        "AGGRESSIVE": {
            "min_price": 2.0,
            "max_price": 500.0,
            "min_volume": 1_000_000,
            "min_market_cap": 1_000_000_000,
            "max_change_pct": 0.30,
            "max_volatility": 0.08,
        }
    }
    
    f = filters[mode]
    
    # Apply filters
    if price < f["min_price"] or price > f["max_price"]:
        return True, f"Price out of range: ${price:.2f}"
    if volume < f["min_volume"]:
        return True, f"Volume too low: {volume:,}"
    if market_cap > 0 and market_cap < f["min_market_cap"]:
        return True, f"Market cap too low: ${market_cap:,.0f}"
    if change_pct > f["max_change_pct"]:
        return True, f"Change too high: {change_pct:.1%}"
    if volatility > f["max_volatility"]:
        return True, f"Volatility too high: {volatility:.1%}"
    
    return False, "Passed"
```

---

## ⚡ **Dynamic Time-Based Filter (Your Suggestion)**

```python
import datetime

def get_dynamic_max_change_pct(mode="AGGRESSIVE"):
    """Dynamic % change threshold based on time of day"""
    now = datetime.datetime.now(datetime.timezone.utc)
    hour = now.hour  # UTC hour
    
    # Convert to ET (UTC-5, or UTC-4 during DST)
    et_hour = (hour - 5) % 24  # Simplified (doesn't account for DST)
    
    base_max = 0.30 if mode == "AGGRESSIVE" else 0.15
    
    if et_hour < 10:  # Pre-10AM ET
        return base_max * 1.67  # 50% for AGGRESSIVE, 25% for SAFE
    elif et_hour < 14:  # 10AM-2PM ET
        return base_max  # 30% for AGGRESSIVE, 15% for SAFE
    else:  # Post-2PM ET
        return base_max * 0.33  # 10% for AGGRESSIVE, 5% for SAFE

# Usage in filter
max_change_pct = get_dynamic_max_change_pct(mode)
if change_pct > max_change_pct:
    continue  # Filter out
```

---

## 📊 **Filter Priority Order**

1. **Symbol format** (fastest, filter first)
2. **Price range** (quick check)
3. **Volume** (liquidity check)
4. **Change %** (momentum check - YOUR DYNAMIC FILTER GOES HERE)
5. **Market cap** (quality check)
6. **Volatility** (risk check - requires data fetch)
7. **Quality score** (final filter - requires full analysis)

---

## 🎯 **Pro Tips**

1. **Filter early, filter often** - Reject bad symbols before expensive API calls
2. **Cache universe** - Don't re-scan every request (60s cache works well)
3. **Log filter reasons** - Helps debug and tune thresholds
4. **Mode-specific is key** - SAFE vs AGGRESSIVE should be clearly separated
5. **Dynamic thresholds** - Time-based, market condition-based, etc.

---

## 🔍 **Debugging Filter Issues**

```python
# Add this to your filter function
filter_log = {
    "symbol": symbol,
    "filtered": False,
    "reasons": []
}

# For each filter check:
if price < min_price:
    filter_log["filtered"] = True
    filter_log["reasons"].append(f"Price ${price:.2f} < ${min_price:.2f}")

# Log at end
if filter_log["filtered"]:
    logger.debug(f"Filtered {symbol}: {', '.join(filter_log['reasons'])}")
```

