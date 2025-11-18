# 🚀 Alpaca Connect (OAuth) Implementation Guide

**Critical Clarification**: Alpaca Connect is **NOT** the Broker API. It's an OAuth-based app marketplace where users connect their existing Alpaca accounts.

---

## 📋 Understanding Alpaca Connect vs Broker API

### **Alpaca Connect (OAuth) - What You're Building**
- ✅ **OAuth-based app marketplace**
- ✅ Users already have Alpaca brokerage accounts
- ✅ Users tap "Connect with Alpaca" → OAuth flow
- ✅ You get access tokens to use their account
- ✅ Use **Trading API** (not Broker API)
- ✅ Alpaca owns the brokerage relationship
- ✅ **Less compliance overhead** - perfect for MVP
- ✅ Focus on UX, AI, education, insights

### **Broker API (What You've Been Building)**
- ❌ White-label broker model
- ❌ Users open accounts under RichesReach
- ❌ You handle KYC/AML, disclosures, supervision
- ❌ More regulatory overhead
- ❌ Better for Phase 2/3 when you want to "own the account"

---

## 🎯 Recommendation: Use Alpaca Connect for MVP

**Why Connect is Perfect for RichesReach:**
1. ✅ Faster approval path (less compliance)
2. ✅ Users already trust Alpaca
3. ✅ You focus on AI copilot experience
4. ✅ Can still demo "live trading"
5. ✅ Can upgrade to Broker API later if needed

---

## 🔄 What Needs to Change in Your Codebase

### **Keep (Still Useful)**
- ✅ Trading API client (you'll use this instead of Broker API)
- ✅ Order placement logic
- ✅ Position tracking
- ✅ Account info fetching
- ✅ Frontend trading UI
- ✅ Guardrails (can still enforce limits client-side)

### **Remove/Replace**
- ❌ Broker API service (`alpaca_broker_service.py` - replace with Trading API)
- ❌ KYC onboarding flows (Alpaca handles this)
- ❌ Account creation endpoints (users create accounts with Alpaca)
- ❌ Broker webhook handlers (different webhook structure for Trading API)
- ❌ Broker models (simplify - just track OAuth tokens)

### **Add (New)**
- ✅ OAuth flow implementation
- ✅ Access token storage/refresh
- ✅ "Connect with Alpaca" button/flow
- ✅ Trading API client (different from Broker API)
- ✅ User account linking (map RichesReach user → Alpaca account)

---

## 🔐 OAuth Flow Implementation

### Step 1: Register Your App with Alpaca
1. Get OAuth client ID and secret from Alpaca
2. Set redirect URI: `https://your-domain.com/auth/alpaca/callback`
3. Request scopes: `trading:write`, `account:read`, `positions:read`

### Step 2: "Connect with Alpaca" Button
```typescript
// Frontend: Connect button
const handleConnectAlpaca = () => {
  const authUrl = `https://app.alpaca.markets/oauth/authorize?` +
    `client_id=${ALPACA_CLIENT_ID}&` +
    `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
    `response_type=code&` +
    `scope=trading:write account:read positions:read`;
  
  // Open in browser or WebView
  Linking.openURL(authUrl);
};
```

### Step 3: OAuth Callback Handler
```python
# Backend: /auth/alpaca/callback
@csrf_exempt
def alpaca_oauth_callback(request):
    code = request.GET.get('code')
    
    # Exchange code for tokens
    token_response = requests.post('https://api.alpaca.markets/oauth/token', {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': ALPACA_CLIENT_ID,
        'client_secret': ALPACA_CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
    })
    
    tokens = token_response.json()
    # Store: access_token, refresh_token, expires_in
    
    # Get user's Alpaca account info
    account = get_alpaca_account(tokens['access_token'])
    
    # Link to RichesReach user
    link_user_alpaca_account(request.user, account['id'], tokens)
    
    return redirect('/trading?connected=true')
```

### Step 4: Trading API Client
```python
# New service: alpaca_trading_service.py
class AlpacaTradingService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = 'https://api.alpaca.markets'
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'APCA-API-KEY-ID': self.api_key,  # Your app's key
            'APCA-API-SECRET-KEY': self.api_secret,
        }
    
    def get_account(self):
        """Get user's Alpaca account"""
        return self._make_request('GET', '/v2/account')
    
    def place_order(self, symbol, qty, side, order_type='market'):
        """Place order on user's account"""
        return self._make_request('POST', '/v2/orders', {
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'type': order_type,
            'time_in_force': 'day',
        })
    
    def get_positions(self):
        """Get user's positions"""
        return self._make_request('GET', '/v2/positions')
```

---

## 📊 Database Schema Changes

### Simplified Model (Replace BrokerAccount)
```python
class AlpacaConnection(models.Model):
    """OAuth connection to user's Alpaca account"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    alpaca_account_id = models.CharField(max_length=100)
    
    # OAuth tokens (encrypted)
    access_token = models.TextField()  # Encrypted
    refresh_token = models.TextField()  # Encrypted
    token_expires_at = models.DateTimeField()
    
    # Account info (cached)
    account_number = models.CharField(max_length=50)
    status = models.CharField(max_length=50)  # ACTIVE, etc.
    
    connected_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(auto_now=True)
```

---

## 🎨 Frontend Changes

### Replace "Create Account" with "Connect Account"
```typescript
// Before: Create Alpaca account
<Button onPress={createAccount}>Create Trading Account</Button>

// After: Connect existing account
<Button onPress={connectAlpaca}>
  <AlpacaLogo />
  Connect with Alpaca
</Button>
```

### Update Product Messaging
**Old**: "Open a brokerage account with RichesReach"
**New**: "Connect your Alpaca account and trade with AI copilot"

---

## ✅ Implementation Checklist

### Phase 1: OAuth Setup (Week 1)
- [ ] Get OAuth client ID/secret from Alpaca
- [ ] Register redirect URI
- [ ] Implement OAuth authorization flow
- [ ] Implement token exchange endpoint
- [ ] Store tokens securely (encrypted)
- [ ] Test OAuth flow end-to-end

### Phase 2: Trading API Integration (Week 1-2)
- [ ] Replace Broker API service with Trading API client
- [ ] Implement account fetching
- [ ] Implement order placement
- [ ] Implement position fetching
- [ ] Update GraphQL/REST endpoints
- [ ] Test with connected account

### Phase 3: Frontend Updates (Week 2)
- [ ] Replace "Create Account" with "Connect Account"
- [ ] Add OAuth flow screens
- [ ] Update trading UI to use connected account
- [ ] Add account status indicator
- [ ] Update product messaging

### Phase 4: Testing & Launch (Week 2-3)
- [ ] End-to-end testing with real Alpaca accounts
- [ ] Test token refresh flow
- [ ] Test order placement
- [ ] Test position updates
- [ ] Load testing
- [ ] Beta launch with 10-50 users

---

## 🔄 Migration Path from Broker API

### What to Keep
1. **Guardrails** - Still enforce limits client-side
2. **Trading UI** - Same experience, different backend
3. **Order logic** - Similar, just different API
4. **Position tracking** - Same concept

### What to Replace
1. **API Client** - Broker API → Trading API
2. **Auth Flow** - Account creation → OAuth
3. **Models** - BrokerAccount → AlpacaConnection
4. **Webhooks** - Different structure

### What to Remove
1. **KYC flows** - Alpaca handles this
2. **Account creation** - Users create with Alpaca
3. **Document upload** - Not needed
4. **Compliance disclosures** - Simplified (just app permissions)

---

## 📝 Updated Email to Hunter

**Key Points to Add:**
- "We're building on Alpaca Connect (OAuth) for MVP"
- "Users will connect their existing Alpaca accounts"
- "Request OAuth client credentials"
- "Focus on Trading API integration"

---

## 🚀 Next Steps

1. **Confirm with Hunter**: "We want Alpaca Connect (OAuth), not Broker API"
2. **Get OAuth Credentials**: Client ID, secret, redirect URI setup
3. **Start Implementation**: OAuth flow first, then Trading API
4. **Update Messaging**: "Connect your Alpaca account" not "Open account"

---

## 📚 Resources

- **Alpaca Connect Docs**: https://alpaca.markets/docs/connect/
- **OAuth Flow**: https://alpaca.markets/docs/connect/oauth/
- **Trading API**: https://alpaca.markets/docs/api-documentation/api-v2/
- **Scopes**: `trading:write`, `account:read`, `positions:read`

---

**Status**: Ready to pivot to OAuth-based Connect model! 🎯

