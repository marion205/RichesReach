# 🧪 Alpaca Connect Testing Guide

**Purpose**: Test both "has account" and "needs account" scenarios for OAuth Connect flow

---

## 📋 Test Scenarios

### Scenario 1: User Has Alpaca Account (Happy Path)

**Steps:**
1. Open TradingScreen
2. Try to place an order without connected account
3. Modal appears: "Do you already have an Alpaca account?"
4. Select **"Yes, I have an account"**
5. OAuth flow should start
6. User approves on Alpaca's site
7. Callback returns to app
8. Account linked successfully
9. Order placement can proceed

**Expected Results:**
- ✅ Modal shows correctly
- ✅ OAuth URL opens in browser/WebView
- ✅ Callback handled correctly
- ✅ Account linked
- ✅ Analytics tracks: `connect_initiated`, `connect_has_account_yes`, `connect_oauth_started`, `connect_oauth_success`, `connect_account_linked`

**Analytics to Verify:**
```javascript
{
  totalAttempts: 1,
  hasAccountCount: 1,
  oauthStarted: 1,
  oauthSuccess: 1,
  accountLinked: 1,
  successRate: 1.0
}
```

---

### Scenario 2: User Needs to Create Account (Guided Signup)

**Steps:**
1. Open TradingScreen
2. Try to place an order without connected account
3. Modal appears: "Do you already have an Alpaca account?"
4. Select **"No, I need to create one"**
5. Signup instructions screen appears
6. Tap **"Create Account at Alpaca"**
7. Browser opens to `https://alpaca.markets/signup`
8. User creates account on Alpaca
9. User returns to RichesReach app
10. User taps "Connect with Alpaca" again
11. OAuth flow starts (now they have account)
12. Account linked successfully

**Expected Results:**
- ✅ Modal shows signup screen
- ✅ Alpaca signup page opens
- ✅ User can return and connect
- ✅ Analytics tracks: `connect_initiated`, `connect_has_account_no`, `connect_signup_redirected`

**Analytics to Verify:**
```javascript
{
  totalAttempts: 1,
  noAccountCount: 1,
  signupRedirects: 1
}
```

---

### Scenario 3: OAuth Error - User Denies Access

**Steps:**
1. Start OAuth flow
2. On Alpaca's authorization page, user clicks **"Deny"**
3. Callback returns with `error=access_denied`
4. Error handling shows appropriate message

**Expected Results:**
- ✅ Error message shown: "Access denied. Please approve to connect your account."
- ✅ User can retry
- ✅ Analytics tracks: `connect_oauth_error` with `error: 'access_denied'`

---

### Scenario 4: OAuth Error - No Callback (Signup Mid-Flow)

**Steps:**
1. User without account starts OAuth flow
2. On Alpaca's site, user signs up (creates account)
3. Callback doesn't fire properly (known issue)
4. User returns to app manually
5. Error handling shows message

**Expected Results:**
- ✅ Error message: "Having trouble connecting? Make sure you completed account creation, then try again."
- ✅ User can retry connection
- ✅ Analytics tracks: `connect_oauth_error` with `error: 'no_callback'`

---

### Scenario 5: Analytics Verification

**Steps:**
1. Complete full flow (either scenario 1 or 2)
2. Check analytics summary
3. Verify all events tracked correctly

**Expected Analytics Events:**
```javascript
[
  { event: 'connect_initiated', timestamp: ..., metadata: { source: 'order_placement' } },
  { event: 'connect_modal_shown', timestamp: ... },
  { event: 'connect_has_account_yes', timestamp: ... }, // or 'connect_has_account_no'
  { event: 'connect_oauth_started', timestamp: ... },
  { event: 'connect_oauth_success', timestamp: ... },
  { event: 'connect_account_linked', timestamp: ..., metadata: { accountId: '...' } }
]
```

**Summary to Verify:**
```javascript
{
  totalAttempts: 1,
  hasAccountCount: 1, // or noAccountCount: 1
  oauthStarted: 1,
  oauthSuccess: 1,
  accountLinked: 1,
  successRate: 1.0,
  sessionId: 'alpaca_...'
}
```

---

## 🛠️ Testing Tools

### 1. React Native Debugger
- View console logs
- Check analytics events
- Inspect component state

### 2. ngrok (for local testing)
```bash
# Start your backend
npm run start:backend

# Expose with ngrok
ngrok http 8000

# Use ngrok URL as redirect_uri in OAuth config
```

### 3. Analytics Dashboard
- Check `alpacaAnalytics.getSummary()` in console
- View events: `alpacaAnalytics.getEvents()`
- Monitor success rate: `alpacaAnalytics.getSuccessRate()`

---

## 📊 Success Metrics

### Target Metrics (Post-Launch)
- **Connect Success Rate**: > 80%
- **Has Account Rate**: ~70% of users
- **Signup Completion Rate**: > 50% of users who need account
- **OAuth Error Rate**: < 5%

### Monitoring
- Track daily: `totalAttempts`, `successRate`
- Alert if: `successRate < 0.5` (consider hybrid approach)
- Alert if: `oauthErrors > 10%` (investigate OAuth issues)

---

## 🐛 Common Issues & Solutions

### Issue: OAuth callback doesn't fire
**Solution**: 
- Check redirect URI matches exactly
- Verify OAuth client ID/secret
- Test with ngrok for local development
- Check browser/WebView settings

### Issue: "No account" users can't complete flow
**Solution**:
- Verify signup link works
- Check if user completed Alpaca signup
- Provide clear instructions
- Consider hybrid approach if <50% success

### Issue: Analytics not tracking
**Solution**:
- Check `ANALYTICS_ENABLED` flag
- Verify telemetry service initialized
- Check console for errors
- Ensure events are being called

---

## ✅ Pre-Launch Checklist

- [ ] Test Scenario 1 (has account) - 5+ times
- [ ] Test Scenario 2 (needs account) - 3+ times
- [ ] Test Scenario 3 (OAuth denied) - 2+ times
- [ ] Test Scenario 4 (no callback) - 1+ time
- [ ] Verify analytics tracking for all scenarios
- [ ] Check success rate calculation
- [ ] Test error handling
- [ ] Verify signup link works
- [ ] Test on iOS and Android
- [ ] Test with real Alpaca accounts (sandbox)
- [ ] Load test (100+ concurrent connections)

---

## 📝 Test Results Template

```
Date: __________
Tester: __________
Environment: [Dev/Staging/Production]

Scenario 1 (Has Account):
- [ ] Pass / [ ] Fail
- Notes: __________

Scenario 2 (Needs Account):
- [ ] Pass / [ ] Fail
- Notes: __________

Scenario 3 (OAuth Denied):
- [ ] Pass / [ ] Fail
- Notes: __________

Analytics Verification:
- Success Rate: _____%
- Total Attempts: _____
- Errors: _____

Issues Found:
1. __________
2. __________
```

---

**Status**: Ready for testing! 🚀

