# Pre-Market Scanner - Complete Implementation

## 🎯 **What It Does**

The pre-market scanner identifies quality trading setups **before market open** (4AM-9:30AM ET). It:
- Scans pre-market movers from Polygon
- Applies looser filters (pre-market moves are often bigger)
- Flags quality setups with room to run
- Alerts before market open (9:30 AM ET)

---

## 🚀 **How to Use**

### **1. Via Django Management Command**

```bash
# Run pre-market scan (AGGRESSIVE mode, top 20 setups)
python manage.py pre_market_scan --mode AGGRESSIVE --limit 20

# Run with alert message
python manage.py pre_market_scan --mode AGGRESSIVE --limit 20 --alert

# SAFE mode (stricter filters)
python manage.py pre_market_scan --mode SAFE --limit 10
```

### **2. Via GraphQL Query**

```graphql
query GetPreMarketPicks {
  preMarketPicks(mode: "AGGRESSIVE", limit: 20) {
    asOf
    mode
    picks {
      symbol
      side
      score
      preMarketPrice
      preMarketChangePct
      volume
      marketCap
      prevClose
      notes
      scannedAt
    }
    totalScanned
    minutesUntilOpen
  }
}
```

### **3. Via Python Script**

```python
from core.pre_market_scanner import PreMarketScanner

scanner = PreMarketScanner()
setups = scanner.scan_pre_market_sync(mode="AGGRESSIVE", limit=20)

for setup in setups:
    print(f"{setup['symbol']} - {setup['side']}: {setup['pre_market_change_pct']:.2%}")
```

### **4. Via Test Script**

```bash
python test_pre_market_scanner.py
```

---

## ⚙️ **Pre-Market Filters (Looser Than Regular Trading)**

### **AGGRESSIVE Mode:**
- **Min Price:** $2.00
- **Min Volume:** 500K shares (vs 1M regular)
- **Min Market Cap:** $500M (vs $1B regular)
- **Max Change %:** 50% (vs 30% regular)

### **SAFE Mode:**
- **Min Price:** $5.00
- **Min Volume:** 2M shares (vs 5M regular)
- **Min Market Cap:** $10B (vs $50B regular)
- **Max Change %:** 25% (vs 15% regular)

**Why Looser?**
- Pre-market volume is lower (so we accept lower volume)
- Pre-market moves are often bigger (so we allow bigger % changes)
- We want to catch early momentum before it's fully priced in

---

## 📊 **Output Format**

Each setup includes:
- **symbol:** Stock ticker
- **side:** "LONG" or "SHORT"
- **score:** Quality score (0-10)
- **preMarketPrice:** Current pre-market price
- **preMarketChangePct:** Pre-market move percentage
- **volume:** Pre-market volume
- **marketCap:** Market capitalization
- **prevClose:** Previous day's close
- **notes:** Human-readable notes
- **scannedAt:** ISO timestamp

---

## 🔔 **Alert System**

The scanner can generate alert messages:

```bash
python manage.py pre_market_scan --alert
```

**Alert includes:**
- Number of quality setups found
- Minutes until market open
- Top 10 setups with key metrics
- Risk management reminder

**Example Alert:**
```
🔔 PRE-MARKET ALERT - 5 Quality Setups Found
================================================================================

Scanned at: 2025-11-25 08:45:00 UTC
Market opens in: ~45 minutes

TOP SETUPS:
--------------------------------------------------------------------------------
1. AAPL - LONG
   Pre-market: +2.5% | Price: $185.50 | Score: 7.5
   Pre-market LONG: 2.5% move, 1,200,000 shares

2. TSLA - SHORT
   Pre-market: -3.2% | Price: $245.30 | Score: 8.2
   Pre-market SHORT: -3.2% move, 2,100,000 shares
...
```

---

## ⏰ **Pre-Market Hours**

The scanner only runs during pre-market hours:
- **Start:** 4:00 AM ET
- **End:** 9:30 AM ET (market open)

**Outside these hours:**
- Returns empty results
- Logs warning message
- GraphQL query returns empty picks array

---

## 🔧 **Integration with Regular Day Trading**

The pre-market scanner is **separate** from the regular day trading algorithm:
- **Pre-market:** Scans pre-market movers, looser filters
- **Regular:** Scans intraday movers, stricter filters

**You can use both:**
1. Run pre-market scan at 8:00 AM ET
2. Get quality setups to watch at open
3. Run regular day trading scan after 9:30 AM ET
4. Compare picks from both scans

---

## 📈 **Quality Score Calculation**

The quality score is a simplified metric:
- **Base:** `abs(change_pct) * 10` (scales change % to 0-10)
- **Volume bonus:** +2 if volume > 1M shares
- **Capped at:** 10.0

**In production, you'd use full feature extraction:**
- Momentum
- Volatility
- Volume profile
- Breakout patterns
- Catalyst score

---

## 🎯 **Best Practices**

1. **Run at 8:00 AM ET** - Gives you 90 minutes before open
2. **Review top 10 setups** - Don't try to trade all of them
3. **Use proper risk management** - Pre-market moves can reverse
4. **Watch for news** - Pre-market moves often driven by news
5. **Confirm at open** - Wait for market open confirmation before entering

---

## ⚠️ **Risk Warnings**

- **Pre-market moves can reverse** - Don't chase
- **Lower liquidity** - Wider spreads, slippage risk
- **News-driven** - Moves may be overreactions
- **Gap risk** - Price can gap at open

**Always use:**
- Stop losses
- Position sizing
- Risk management
- Confirmation at open

---

## 🔍 **Troubleshooting**

### **No picks found:**
- Check if in pre-market hours (4AM-9:30AM ET)
- Verify Polygon API key is set
- Check if market is open (scanner only works pre-market)
- Review filter criteria (may be too strict)

### **API errors:**
- Verify `POLYGON_API_KEY` environment variable
- Check Polygon API rate limits
- Ensure network connectivity

### **GraphQL errors:**
- Verify `preMarketPicks` query is in schema
- Check resolver is properly registered
- Review server logs for errors

---

## 📝 **Files Created**

1. **`core/pre_market_scanner.py`** - Main scanner service
2. **`core/management/commands/pre_market_scan.py`** - Django command
3. **`test_pre_market_scanner.py`** - Test script
4. **GraphQL types** - Added to `types.py`
5. **GraphQL resolver** - Added to `queries.py`

---

## 🚀 **Next Steps**

1. **Schedule daily runs** - Use cron/scheduler to run at 8:00 AM ET
2. **Add email alerts** - Send alerts to your email
3. **Integrate with mobile app** - Push notifications
4. **Track performance** - See if pre-market picks outperform
5. **Refine filters** - Adjust based on backtesting

---

## 💡 **Future Enhancements**

- **News integration** - Flag setups with news catalysts
- **Options flow** - Include options activity in scoring
- **Social sentiment** - Add Reddit/Twitter sentiment
- **Historical performance** - Track which pre-market setups work best
- **Auto-alerts** - Email/SMS when quality setups found

---

**Ready to catch early momentum! 🎯**

