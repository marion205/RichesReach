# 🎯 Alpaca Connect (OAuth) Implementation Plan

**Status**: Pivot from Broker API to OAuth-based Connect  
**Timeline**: 1-2 weeks post-OAuth credentials  
**Priority**: MVP launch path

---

## 📊 Current State Assessment

### ✅ What You Have (Still Useful)
- Trading UI components
- Order placement logic
- Position tracking UI
- Guardrails framework
- Data API integration (`data.alpaca.markets`)

### ❌ What Needs to Change
- **API Client**: Broker API → Trading API with OAuth tokens
- **Auth Flow**: Account creation → OAuth connection (for existing accounts only)
- **Database Models**: BrokerAccount → AlpacaConnection
- **Frontend**: "Create Account" → "Connect Account" + Guided Signup for new users

### ⚠️ Critical Limitation
- **OAuth Connect does NOT support account creation**
- Users must already have Alpaca accounts
- For new users: Implement guided signup (link to Alpaca signup)
- See `ALPACA_CONNECT_ACCOUNT_CREATION_STRATEGY.md` for details

---

## 🏗️ Architecture Changes

### Current (Broker API)
```
User → RichesReach → Create Account → KYC → Alpaca Broker API → Account Created
```

### New (OAuth Connect)
```
User → RichesReach → "Connect with Alpaca" → OAuth → Access Token → Trading API → User's Existing Account
```

---

## 📝 Implementation Steps

### Phase 1: OAuth Setup (Days 1-3)

#### 1.1 Get OAuth Credentials from Alpaca
- [ ] Request OAuth client ID and secret
- [ ] Register redirect URI: `https://api.richesreach.com/auth/alpaca/callback`
- [ ] Request scopes: `trading:write`, `account:read`, `positions:read`
- [ ] Test OAuth flow in sandbox

#### 1.2 Create OAuth Service
**File**: `deployment_package/backend/core/alpaca_oauth_service.py`
```python
class AlpacaOAuthService:
    """Handle OAuth flow for Alpaca Connect"""
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            'client_id': ALPACA_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'trading:write account:read positions:read',
            'state': state,  # CSRF protection
        }
        return f"https://app.alpaca.markets/oauth/authorize?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str) -> dict:
        """Exchange authorization code for access/refresh tokens"""
        # Implementation
        pass
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh expired access token"""
        # Implementation
        pass
```

#### 1.3 Create OAuth Endpoints
**File**: `deployment_package/backend/core/alpaca_oauth_views.py`
```python
@csrf_exempt
def alpaca_oauth_initiate(request):
    """Initiate OAuth flow - redirect to Alpaca"""
    state = generate_csrf_token()
    request.session['alpaca_oauth_state'] = state
    auth_url = oauth_service.get_authorization_url(REDIRECT_URI, state)
    return redirect(auth_url)

@csrf_exempt
@login_required
def alpaca_oauth_callback(request):
    """Handle OAuth callback from Alpaca"""
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    # Verify state (CSRF protection)
    if state != request.session.get('alpaca_oauth_state'):
        return JsonResponse({'error': 'Invalid state'}, status=400)
    
    # Exchange code for tokens
    tokens = oauth_service.exchange_code_for_tokens(code)
    
    # Get user's Alpaca account
    trading_service = AlpacaTradingService(tokens['access_token'])
    account = trading_service.get_account()
    
    # Link to RichesReach user
    connection = AlpacaConnection.objects.create(
        user=request.user,
        alpaca_account_id=account['id'],
        access_token=encrypt(tokens['access_token']),
        refresh_token=encrypt(tokens['refresh_token']),
        token_expires_at=timezone.now() + timedelta(seconds=tokens['expires_in']),
    )
    
    return redirect('/trading?connected=true')
```

---

### Phase 2: Trading API Client (Days 3-5)

#### 2.1 Create Trading API Service
**File**: `deployment_package/backend/core/alpaca_trading_service.py`
```python
class AlpacaTradingService:
    """Trading API client using OAuth access tokens"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = 'https://api.alpaca.markets'  # Production
        # self.base_url = 'https://paper-api.alpaca.markets'  # Paper trading
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'APCA-API-KEY-ID': os.getenv('ALPACA_CLIENT_ID'),  # Your app's ID
            'APCA-API-SECRET-KEY': os.getenv('ALPACA_CLIENT_SECRET'),
        }
    
    def get_account(self):
        """Get user's Alpaca account"""
        return self._make_request('GET', '/v2/account')
    
    def place_order(self, symbol, qty, side, order_type='market', **kwargs):
        """Place order on user's account"""
        data = {
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'type': order_type,
            'time_in_force': kwargs.get('time_in_force', 'day'),
        }
        if order_type == 'limit':
            data['limit_price'] = kwargs.get('limit_price')
        return self._make_request('POST', '/v2/orders', data=data)
    
    def get_positions(self):
        """Get user's positions"""
        return self._make_request('GET', '/v2/positions')
    
    def get_orders(self, status=None, limit=50):
        """Get user's orders"""
        params = {'limit': limit}
        if status:
            params['status'] = status
        return self._make_request('GET', '/v2/orders', params=params)
```

#### 2.2 Update Database Models
**File**: `deployment_package/backend/core/alpaca_connection_models.py`
```python
from django.db import models
from django.contrib.auth import get_user_model
from django_cryptography.fields import encrypt

User = get_user_model()

class AlpacaConnection(models.Model):
    """OAuth connection to user's Alpaca account"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='alpaca_connection')
    alpaca_account_id = models.CharField(max_length=100, unique=True)
    
    # OAuth tokens (encrypted)
    access_token = encrypt(models.TextField())
    refresh_token = encrypt(models.TextField())
    token_expires_at = models.DateTimeField()
    
    # Account info (cached, synced periodically)
    account_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50, blank=True)  # ACTIVE, CLOSED, etc.
    buying_power = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    equity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Metadata
    connected_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(auto_now=True)
    
    def get_trading_service(self):
        """Get Trading API service with current access token"""
        # Refresh token if expired
        if timezone.now() >= self.token_expires_at:
            self.refresh_token()
        return AlpacaTradingService(self.access_token)
    
    def refresh_token(self):
        """Refresh expired access token"""
        oauth_service = AlpacaOAuthService()
        tokens = oauth_service.refresh_access_token(self.refresh_token)
        self.access_token = encrypt(tokens['access_token'])
        self.token_expires_at = timezone.now() + timedelta(seconds=tokens['expires_in'])
        self.save()
```

---

### Phase 3: Update Existing Endpoints (Days 5-7)

#### 3.1 Update Order Placement
**Replace**: `BrokerOrdersView` → `AlpacaTradingOrdersView`
```python
@method_decorator(login_required, name='dispatch')
class AlpacaTradingOrdersView(View):
    """Place orders using Trading API"""
    
    def post(self, request):
        user = request.user
        data = json.loads(request.body)
        
        # Get user's Alpaca connection
        try:
            connection = user.alpaca_connection
        except AlpacaConnection.DoesNotExist:
            return JsonResponse({
                'error': 'Not connected to Alpaca. Please connect your account first.'
            }, status=400)
        
        # Get trading service
        trading_service = connection.get_trading_service()
        
        # Apply guardrails (client-side limits)
        # ... guardrail checks ...
        
        # Place order
        result = trading_service.place_order(
            symbol=data['symbol'],
            qty=data['quantity'],
            side=data['side'],
            order_type=data.get('order_type', 'market'),
        )
        
        # Save order to database (for history)
        order = TradingOrder.objects.create(
            user=user,
            alpaca_order_id=result['id'],
            symbol=data['symbol'],
            quantity=data['quantity'],
            side=data['side'],
            status=result['status'],
        )
        
        return JsonResponse({'success': True, 'order': result})
```

#### 3.2 Update Account/Position Endpoints
- Replace Broker API calls with Trading API calls
- Use OAuth tokens from `AlpacaConnection`
- Keep same GraphQL/REST interface

---

### Phase 4: Frontend Updates (Days 7-10)

#### 4.1 Replace "Create Account" with "Connect Account"
**File**: `mobile/src/features/stocks/screens/TradingScreen.tsx`
```typescript
// Before
const handleCreateAccount = async () => {
  const result = await createAlpacaAccount();
  // ...
};

// After
const handleConnectAlpaca = () => {
  const authUrl = `https://app.alpaca.markets/oauth/authorize?` +
    `client_id=${ALPACA_CLIENT_ID}&` +
    `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
    `response_type=code&` +
    `scope=trading:write account:read positions:read`;
  
  Linking.openURL(authUrl);
};
```

#### 4.2 Update UI Components
- [ ] Replace "Create Trading Account" button with "Connect with Alpaca"
- [ ] Add pre-connect modal: "Do you have an Alpaca account?"
- [ ] Add "Create Account" link for users without accounts
- [ ] Add Alpaca logo/branding
- [ ] Show connection status
- [ ] Update messaging: "Connect your Alpaca account"
- [ ] Handle OAuth errors gracefully (no account, denied access, etc.)
- [ ] Remove KYC flow UI (Alpaca handles this for existing accounts)

---

### Phase 5: Testing & Launch (Days 10-14)

#### 5.1 Testing Checklist
- [ ] OAuth flow end-to-end
- [ ] Token refresh flow
- [ ] Order placement with real account
- [ ] Position fetching
- [ ] Account info syncing
- [ ] Error handling (expired tokens, disconnected accounts)
- [ ] Guardrails still work
- [ ] Load testing

#### 5.2 Launch Plan
- [ ] Beta test with 10-50 users
- [ ] Monitor token refresh rates
- [ ] Monitor API rate limits
- [ ] Set up alerts for failures
- [ ] Gradual rollout

---

## 🔄 Migration Strategy

### Step 1: Keep Broker API Code (For Now)
- Don't delete existing code yet
- Add new OAuth/Trading API code alongside
- Feature flag to switch between them

### Step 2: Test OAuth Flow
- Test with sandbox OAuth credentials
- Verify token exchange works
- Test Trading API calls

### Step 3: Switch Over
- Update frontend to use OAuth flow
- Update backend endpoints
- Remove Broker API code (or keep for Phase 2)

---

## 📧 Updated Email to Hunter

**Key Changes:**
- "We're building on Alpaca Connect (OAuth) for MVP"
- "Request OAuth client credentials (not Broker API keys)"
- "Users will connect existing Alpaca accounts"
- "Focus on Trading API integration"

---

## 🎯 Success Metrics

- [ ] OAuth flow completion rate > 80%
- [ ] Token refresh success rate > 99%
- [ ] Order placement success rate > 95%
- [ ] API error rate < 1%
- [ ] User connection time < 2 minutes

---

## 📚 Resources

- **Alpaca Connect Docs**: https://alpaca.markets/docs/connect/
- **OAuth Flow**: https://alpaca.markets/docs/connect/oauth/
- **Trading API**: https://alpaca.markets/docs/api-documentation/api-v2/
- **Scopes**: `trading:write`, `account:read`, `positions:read`

---

**Next Step**: Update email to Hunter requesting OAuth credentials! 🚀

