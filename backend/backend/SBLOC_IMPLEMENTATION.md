# SBLOC Aggregator Integration

This document describes the complete SBLOC (Securities-Based Line of Credit) aggregator integration implementation.

## Overview

The SBLOC system provides a referral-based approach to SBLOC lending through third-party aggregators. Users can:

1. **Pre-qualify** for SBLOC based on their portfolio
2. **Select a bank** from available partners
3. **Complete application** through the bank's hosted portal
4. **Track status** through webhooks and status updates

## Architecture

### Backend Components

#### 1. Database Models (`core/models.py`)
- **SBLOCBank**: Partner banks offering SBLOC
- **SBLOCReferral**: User referrals and application tracking
- **SBLOCSession**: Short-lived sessions for hosted applications

#### 2. Service Layer (`core/sbloc_service.py`)
- **SBLOCAggregatorService**: API client for aggregator integration
- **SBLOCDataProcessor**: Business logic for referrals and sessions

#### 3. GraphQL API (`core/sbloc_graphql.py`)
- Queries: `sblocBanks`, `sblocReferral`, `sblocReferrals`
- Mutations: `createSblocSession`, `createSblocReferral`, `syncSblocBanks`

#### 4. Webhook Handlers (`core/sbloc_views.py`)
- **POST /api/sbloc/webhook**: Status updates from aggregator
- **GET /api/sbloc/callback**: Application completion callback
- **GET /api/sbloc/health**: Health check endpoint

#### 5. Background Tasks (`core/sbloc_tasks.py`)
- **reconcile_sbloc_statuses**: Periodic status reconciliation
- **sync_sbloc_banks**: Daily bank catalog sync
- **cleanup_expired_sbloc_sessions**: Session cleanup
- **send_sbloc_notifications**: Status change notifications

### Frontend Components

#### 1. React Native Screens
- **SBLOCBankSelectionScreen**: Bank selection and session creation
- **SBLOCApplicationScreen**: Hosted application flow management

#### 2. GraphQL Integration
- **sblocQueries.ts**: GraphQL queries and mutations
- **sbloc.ts**: TypeScript type definitions

#### 3. UI Components
- **SblocFundingCard**: Updated to use new SBLOC flow
- **SblocCalculatorModal**: Pre-qualification calculator

## Configuration

### Environment Variables

```bash
# SBLOC Aggregator Configuration
USE_SBLOC_AGGREGATOR=true
SBLOC_AGGREGATOR_BASE_URL=https://api.sbloc-aggregator.com
SBLOC_AGGREGATOR_API_KEY=your_api_key_here
SBLOC_WEBHOOK_SECRET=your_webhook_secret_here
SBLOC_REDIRECT_URI=https://app.richesreach.net/sbloc/callback
```

### Django Settings

The SBLOC configuration is automatically loaded in `settings.py` with validation and logging.

## Usage Flow

### 1. User Initiates SBLOC Request

```typescript
// User clicks "Borrow against portfolio" in BankAccountScreen
navigation.navigate('SBLOCBankSelection', {
  requestedAmount: 25000,
  consentData: {
    consent: true,
    dataScope: {
      identity: true,
      contact: true,
      portfolioSummary: true,
      positions: true,
      recentTransfers: false,
      income: false,
    },
  },
});
```

### 2. Bank Selection

```graphql
query GetSBLOCBanks {
  sblocBanks {
    id
    name
    minLtv
    maxLtv
    typicalAprMin
    typicalAprMax
    minLineUsd
    maxLineUsd
  }
}
```

### 3. Session Creation

```graphql
mutation CreateSBLOCSession(
  $bankId: ID!
  $requestedAmountUsd: Float!
  $consentData: JSONString!
) {
  createSblocSession(
    bankId: $bankId
    requestedAmountUsd: $requestedAmountUsd
    consentData: $consentData
  ) {
    success
    message
    sessionPayload {
      sessionUrl
      expiresAt
      referral {
        id
        status
        bank {
          name
        }
      }
    }
  }
}
```

### 4. Hosted Application

The user is redirected to the aggregator's hosted application portal where they:
- Complete KYC/AML requirements
- Provide additional documentation
- Review and accept loan terms
- Submit the application

### 5. Status Tracking

Status updates are received via webhooks and displayed in the app:

```typescript
// Status progression
DRAFT → SUBMITTED → IN_REVIEW → CONDITIONAL_APPROVAL → APPROVED → FUNDED
```

## Security & Compliance

### Data Protection
- PII encryption at rest and in transit
- Short-lived pre-signed URLs for data packages
- HMAC signature verification for webhooks
- Consent logging and audit trails

### Compliance Features
- Clear disclosures about referral nature
- No credit decisions made by RichesReach
- Transparent data sharing with user consent
- Regulatory compliance for loan broker activities

### Webhook Security

```python
def _verify_webhook_signature(request):
    signature = request.headers.get("X-Webhook-Signature", "")
    expected = hmac.new(
        settings.SBLOC_WEBHOOK_SECRET.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## Development & Testing

### Mock Mode

When `USE_SBLOC_AGGREGATOR=false`, the system operates in mock mode:
- Mock banks are created automatically
- Mock sessions return test URLs
- No real aggregator API calls

### Management Commands

```bash
# Sync banks from aggregator
python manage.py sync_sbloc_banks

# Dry run sync
python manage.py sync_sbloc_banks --dry-run
```

### Testing Endpoints

```bash
# Health check
curl https://app.richesreach.net/api/sbloc/health

# Test webhook (with proper signature)
curl -X POST https://app.richesreach.net/api/sbloc/webhook \
  -H "X-Webhook-Signature: <signature>" \
  -H "Content-Type: application/json" \
  -d '{"applicationId": "test-123", "status": "approved"}'
```

## Production Deployment

### 1. Environment Setup

```bash
# Set production environment variables
export USE_SBLOC_AGGREGATOR=true
export SBLOC_AGGREGATOR_BASE_URL=https://api.sbloc-aggregator.com
export SBLOC_AGGREGATOR_API_KEY=<production_key>
export SBLOC_WEBHOOK_SECRET=<production_secret>
export SBLOC_REDIRECT_URI=https://app.richesreach.net/sbloc/callback
```

### 2. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Initial Bank Sync

```bash
python manage.py sync_sbloc_banks
```

### 4. Celery Tasks

Set up periodic tasks for:
- Status reconciliation (every 6 hours)
- Bank sync (daily)
- Session cleanup (hourly)
- Notifications (every 5 minutes)

### 5. Webhook Configuration

Configure the aggregator to send webhooks to:
```
https://app.richesreach.net/api/sbloc/webhook
```

## Monitoring & Analytics

### Key Metrics
- Referral creation rate
- Application completion rate
- Approval rate by bank
- Time to decision
- User satisfaction scores

### Logging

All SBLOC operations are logged with appropriate levels:
- INFO: Normal operations
- WARNING: Configuration issues
- ERROR: API failures, webhook errors
- DEBUG: Detailed request/response data

### Health Checks

The system includes comprehensive health checks:
- Aggregator API connectivity
- Webhook endpoint availability
- Database connectivity
- Celery task status

## Troubleshooting

### Common Issues

1. **Webhook Signature Verification Failed**
   - Check `SBLOC_WEBHOOK_SECRET` configuration
   - Verify aggregator is sending correct signature

2. **Session Creation Failed**
   - Check aggregator API credentials
   - Verify user portfolio data is available
   - Check network connectivity

3. **Status Not Updating**
   - Check webhook endpoint is accessible
   - Verify Celery tasks are running
   - Check aggregator webhook configuration

### Debug Mode

Enable debug logging:

```python
LOGGING = {
    'loggers': {
        'core.sbloc_service': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Future Enhancements

### Planned Features
1. **Real-time Notifications**: Push notifications for status changes
2. **Document Management**: Secure document upload and storage
3. **Multi-bank Applications**: Apply to multiple banks simultaneously
4. **Rate Shopping**: Compare rates across banks
5. **Portfolio Analytics**: Advanced portfolio analysis for SBLOC

### Integration Opportunities
1. **Yodlee Integration**: Automatic portfolio data sync
2. **Credit Bureau**: Soft credit pulls for pre-qualification
3. **Document Verification**: Automated document processing
4. **Risk Assessment**: ML-based risk scoring

## Support

For technical support or questions about the SBLOC implementation:

1. Check the logs for error messages
2. Verify environment configuration
3. Test webhook endpoints
4. Review aggregator API documentation
5. Contact the development team

## License

This SBLOC implementation is part of the RichesReach platform and is subject to the same licensing terms.
