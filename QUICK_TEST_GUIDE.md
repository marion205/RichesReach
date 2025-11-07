# 🚀 Quick Test Guide - Constellation Dashboard

## Start Everything (2 Terminals)

### Terminal 1: Backend
```bash
cd /Users/marioncollins/RichesReach
python main_server.py
```
✅ Wait for: `Server running on http://localhost:8000`

### Terminal 2: Mobile App
```bash
cd /Users/marioncollins/RichesReach/mobile
npm start
```
✅ Press `i` for iOS Simulator or scan QR for device

---

## Navigate to Portfolio

1. Open app → Login
2. Tap **"Portfolio"** tab (bottom nav)
3. OR: **"Invest"** → **"Portfolio"**

---

## What You Should See

### ✅ With Bank Linked:
- **Constellation Orb** (pulsing circle)
- Net worth in center
- Satellites around orb

### ✅ Without Bank:
- Traditional portfolio view (normal)

---

## Test Gestures

### 1️⃣ **Tap** → Life Events Modal
- Tap the orb
- Should see: Emergency Fund, Home, Retirement goals

### 2️⃣ **Swipe Left** → Shield Modal  
- Swipe left on orb
- Should see: Protection strategies

### 3️⃣ **Swipe Right** → Growth Modal
- Swipe right on orb
- Should see: Growth projections

### 4️⃣ **Pinch** → What-If Modal
- Pinch orb (two fingers)
- Should see: Interactive calculator

---

## Quick Troubleshooting

**Orb not showing?**
- Check: Do you have bank accounts linked?
- Check: Backend running? (`http://localhost:8000/health`)

**Gestures not working?**
- Try on simulator first
- Check console for errors

**Modals not opening?**
- Check: State variables in PortfolioScreen
- Check: All components imported

---

## Test Backend Endpoint

```bash
# Test snapshot API (needs auth token)
curl http://localhost:8000/api/money/snapshot \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Should return JSON with `netWorth`, `cashflow`, `positions`, `shield`

---

## ✅ Success Checklist

- [ ] Portfolio screen loads
- [ ] Orb appears (if bank linked) OR traditional view (if not)
- [ ] Tap gesture opens Life Events
- [ ] Swipe left opens Shield
- [ ] Swipe right opens Growth
- [ ] Pinch opens What-If
- [ ] All modals close properly

---

**Full guide**: See `TESTING_CONSTELLATION_DASHBOARD.md`

