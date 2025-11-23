# Mobile App Testing Checklist

**Quick Reference for Manual Testing**

---

## 🚀 Start Testing

1. **Start Mobile App**:
   ```bash
   cd mobile
   npm start
   ```

2. **Login**: Use test user credentials

3. **Navigate to features** using paths below

---

## 📋 Quick Test Paths

### Paper Trading
**Path**: `Invest` tab → Look for "Paper Trading" or navigate directly

**Test**:
- [ ] Screen loads
- [ ] Shows $100k balance
- [ ] Can place order
- [ ] Order appears in list
- [ ] Position updates

### Signal Updates (from Stock Detail)
**Path**: 
1. Go to any stock (e.g., "AAPL")
2. Tap **activity icon** (📊) in top right

**Test**:
- [ ] Screen loads
- [ ] Shows fusion score
- [ ] Shows recommendation
- [ ] Shows signal breakdown
- [ ] Shows alerts (if any)

### Research Report (from Stock Detail)
**Path**:
1. Go to any stock (e.g., "AAPL")
2. Tap **file-text icon** (📄) in top right

**Test**:
- [ ] Screen loads
- [ ] Shows executive summary
- [ ] Shows all sections
- [ ] Data is populated

---

## ✅ Success Indicators

- ✅ Screens load without crashes
- ✅ Data displays correctly
- ✅ Navigation works (back button)
- ✅ No console errors
- ✅ GraphQL queries execute

---

## 🐛 If Something Fails

1. Check React Native debugger for errors
2. Check network tab for GraphQL requests
3. Verify backend server is running
4. Check authentication token

---

**Time Estimate**: 10-15 minutes for all three screens

