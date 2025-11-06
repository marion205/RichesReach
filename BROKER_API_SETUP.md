# Broker API Integration Setup Guide

This guide walks through setting up Alpaca Broker API integration for RichesReach.

## Overview

The Broker API integration enables:
- Customer account creation and KYC via Alpaca
- Real trading with guardrails (symbol whitelist, notional caps, PDT checks)
- Order placement, position tracking, and account management
- Webhook handling for real-time updates

## Prerequisites

1. Alpaca Broker API production access (after email approval)
2. Django backend running
3. PostgreSQL database
4. AWS Secrets Manager (optional, for production)

## Setup Steps

### 1. Database Migration

Create and run migrations for broker models:

```bash
cd deployment_package/backend
python manage.py makemigrations core
python manage.py migrate
```

### 2. Environment Variables

Copy `.env.broker.sample` to your `.env` file and fill in:

```bash
# Production keys from Alpaca
ALPACA_BROKER_API_KEY=your_key_here
ALPACA_BROKER_API_SECRET=your_secret_here
ALPACA_BROKER_BASE_URL=https://broker-api.alpaca.markets
ALPACA_WEBHOOK_SECRET=your_webhook_secret_here
```

### 3. URL Routing

Add broker URLs to your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns
    path('broker/', include('core.broker_urls')),
    path('', include('core.broker_urls.webhook_urlpatterns')),  # Webhooks at root
]
```

### 4. AWS Secrets Manager (Production)

If using AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name richesreach/alpaca-broker-api \
  --secret-string file://infrastructure/aws-secrets-manager-alpaca-template.json
```

Update your Django settings to load from Secrets Manager:

```python
import boto3
import json

def get_secrets():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='richesreach/alpaca-broker-api')
    return json.loads(response['SecretString'])

# Load secrets
secrets = get_secrets()
os.environ['ALPACA_BROKER_API_KEY'] = secrets['ALPACA_BROKER_API_KEY']
# ... etc
```

### 5. Webhook Configuration

In Alpaca dashboard, configure webhooks:
- **Trade Updates**: `https://your-domain.com/webhooks/alpaca/trade_updates`
- **Account Updates**: `https://your-domain.com/webhooks/alpaca/account_updates`
- Set webhook secret for HMAC verification

### 6. Frontend Integration

Import and use `BrokerConfirmOrderModal` in your trading screens:

```typescript
import BrokerConfirmOrderModal from '../components/BrokerConfirmOrderModal';

// In your component
const [showConfirmModal, setShowConfirmModal] = useState(false);
const [orderDetails, setOrderDetails] = useState(null);

const handlePlaceOrder = async () => {
  // Call your GraphQL mutation or REST API
  const result = await placeOrderMutation({
    variables: {
      symbol: orderDetails.symbol,
      side: orderDetails.side,
      orderType: orderDetails.orderType,
      quantity: orderDetails.quantity,
      // ... etc
    }
  });
};

<BrokerConfirmOrderModal
  visible={showConfirmModal}
  onClose={() => setShowConfirmModal(false)}
  onConfirm={handlePlaceOrder}
  orderDetails={orderDetails}
  accountInfo={accountInfo}
/>
```

## API Endpoints

### REST Endpoints

- `POST /broker/onboard` - Create/update broker account (KYC)
- `GET /broker/account` - Get account status, buying power, PDT flags
- `POST /broker/orders` - Place order (with guardrails)
- `GET /broker/orders` - List orders
- `GET /broker/positions` - Get positions
- `GET /broker/activities` - Get account activities

### GraphQL

**Queries:**
```graphql
query {
  brokerAccount {
    kycStatus
    alpacaAccountId
  }
  brokerAccountInfo {
    buyingPower
    cash
    dailyNotionalUsed
    dailyNotionalRemaining
  }
  brokerOrders(status: "FILLED", limit: 10) {
    id
    symbol
    side
    quantity
    status
  }
}
```

**Mutations:**
```graphql
mutation {
  createBrokerAccount(
    firstName: "John"
    lastName: "Doe"
    dateOfBirth: "1990-01-01"
    ssn: "123-45-6789"
    # ... other fields
  ) {
    success
    accountId
    kycStatus
  }
  
  placeOrder(
    symbol: "AAPL"
    side: "BUY"
    orderType: "MARKET"
    quantity: 10
    estimatedPrice: 150.0
  ) {
    success
    orderId
    status
  }
}
```

## Guardrails

Guardrails are enforced automatically:

1. **Symbol Whitelist**: Only U.S. equities & ETFs in whitelist
2. **Per-Order Cap**: Max $10k per order
3. **Daily Cap**: Max $50k per day per user
4. **Trading Hours**: Market orders only during 9:30 AM - 4:00 PM ET
5. **PDT Checks**: Pattern day trader restrictions
6. **KYC Status**: Must be APPROVED before trading
7. **Buying Power**: Must have sufficient funds

## Testing

### Test Plan

1. **Account Creation**
   - Create test user
   - Complete KYC onboarding
   - Verify account status changes to APPROVED

2. **Order Placement**
   - Place market order (during market hours)
   - Place limit order
   - Verify guardrail checks (symbol, notional, etc.)
   - Test rejected orders (invalid symbol, exceeds limits)

3. **Webhooks**
   - Place order and verify trade update webhook fires
   - Update account and verify account update webhook fires
   - Test HMAC signature verification

4. **Edge Cases**
   - After-hours order (should be blocked for market orders)
   - Exceeding daily limit
   - Pattern day trader restrictions
   - Insufficient buying power

## Compliance

Required disclosures in app:

1. **Brokerage Services**: "Brokerage services provided by Alpaca Securities LLC, member FINRA/SIPC."
2. **Not Investment Advice**: Clear disclaimers that recommendations are not investment advice
3. **Risk Warnings**: "Trading involves risk of loss. Past performance does not guarantee future results."
4. **PDT Warnings**: For pattern day traders
5. **Order Type Education**: Market vs limit order explanations

## Monitoring

Key metrics to monitor:

- Order rejection rate
- Guardrail block rate (by reason)
- Webhook delivery success rate
- Average order size
- Daily notional usage per user
- KYC approval rate

## Security

- API keys stored in AWS Secrets Manager (never in code)
- HMAC verification for all webhooks
- IP allow-listing (if required by Alpaca)
- PII encrypted at rest
- Audit logs for all guardrail decisions

## Next Steps

After initial setup:

1. Complete test trades with small amounts
2. Monitor webhook delivery and order execution
3. Review guardrail logs for any issues
4. Gradually increase user limits for beta
5. Add additional symbols to whitelist as needed

## Support

- Alpaca Broker API Docs: https://alpaca.markets/docs/broker-api/
- Alpaca Support: partnerships@alpaca.markets

