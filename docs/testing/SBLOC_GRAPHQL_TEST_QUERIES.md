# SBLOC GraphQL Test Queries

## GraphQL Playground

**URL**: `http://localhost:8000/graphql/`

**Note**: The GraphQL endpoint is at `/graphql/` (POST endpoint). For testing, you can use:
- GraphQL Playground (if configured)
- curl commands
- Postman
- Apollo Client DevTools

---

## 1. Test `sblocBanks` Query

### Query:
```graphql
query GetSBLOCBanks {
  sblocBanks {
    id
    name
    logoUrl
    minApr
    maxApr
    minLtv
    maxLtv
    notes
    regions
    minLoanUsd
  }
}
```

### Using curl:
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "query { sblocBanks { id name logoUrl minApr maxApr minLtv maxLtv notes regions minLoanUsd } }"
  }'
```

### Expected Response:
```json
{
  "data": {
    "sblocBanks": [
      {
        "id": "1",
        "name": "Test Bank 1",
        "logoUrl": null,
        "minApr": 0.05,
        "maxApr": 0.08,
        "minLtv": 0.5,
        "maxLtv": 0.7,
        "notes": null,
        "regions": ["US"],
        "minLoanUsd": 10000
      }
    ]
  }
}
```

---

## 2. Test `createSblocSession` Mutation

### Mutation:
```graphql
mutation CreateSBLOCSession($bankId: ID!, $amountUsd: Int!) {
  createSblocSession(bankId: $bankId, amountUsd: $amountUsd) {
    success
    sessionId
    applicationUrl
    error
  }
}
```

### Variables:
```json
{
  "bankId": "1",
  "amountUsd": 50000
}
```

### Using curl:
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "mutation CreateSBLOCSession($bankId: ID!, $amountUsd: Int!) { createSblocSession(bankId: $bankId, amountUsd: $amountUsd) { success sessionId applicationUrl error } }",
    "variables": {
      "bankId": "1",
      "amountUsd": 50000
    }
  }'
```

### Expected Response:
```json
{
  "data": {
    "createSblocSession": {
      "success": true,
      "sessionId": "uuid-here",
      "applicationUrl": "https://example.com/sbloc/apply?session=uuid-here",
      "error": null
    }
  }
}
```

---

## 3. Test `syncSblocBanks` Mutation (Admin Only)

### Mutation:
```graphql
mutation SyncSBLOCBanks {
  syncSblocBanks {
    success
    banksSynced
    error
  }
}
```

### Using curl:
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -d '{
    "query": "mutation { syncSblocBanks { success banksSynced error } }"
  }'
```

---

## 4. Test with Authentication

### Get JWT Token First:
```bash
# Login mutation
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { tokenAuth(username: \"test@richesreach.com\", password: \"testpass123\") { token } }"
  }'
```

### Use Token in Subsequent Requests:
```bash
TOKEN="your-jwt-token-here"

curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { sblocBanks { id name } }"
  }'
```

---

## 5. Testing in GraphQL Playground

If you have GraphQL Playground configured:

1. Open `http://localhost:8000/graphql` (if configured)
2. Or use a tool like [GraphiQL](https://github.com/graphql/graphiql) or [Altair](https://altairgraphql.dev/)

### Example Query:
```graphql
query {
  sblocBanks {
    id
    name
    minApr
    maxApr
  }
}
```

### Example Mutation:
```graphql
mutation {
  createSblocSession(bankId: "1", amountUsd: 50000) {
    success
    sessionId
    applicationUrl
  }
}
```

---

## 6. Testing with Mobile App

The mobile app uses these queries automatically:

**File**: `mobile/src/features/sbloc/screens/SBLOCBankSelectionScreen.tsx`

```typescript
const SBLOC_BANKS = gql`
  query SblocBanks {
    sblocBanks {
      id
      name
      logoUrl
      minApr
      maxApr
      minLtv
      maxLtv
      notes
      regions
      minLoanUsd
    }
  }
`;

const CREATE_SBLOC_SESSION = gql`
  mutation CreateSblocSession($bankId: ID!, $amountUsd: Int!) {
    createSblocSession(bankId: $bankId, amountUsd: $amountUsd) {
      success
      applicationUrl
      sessionId
      error
    }
  }
`;
```

---

## Troubleshooting

### Error: "Authentication required"
- Make sure you're sending a valid JWT token in the `Authorization` header
- Token format: `Bearer YOUR_JWT_TOKEN`

### Error: "No active banks found"
- Create test banks in the database first
- Or use `syncSblocBanks` mutation (admin only) to sync from aggregator

### Error: "SBLOC bank not found"
- Verify the bank ID exists
- Check that the bank is active (`is_active=True`)

### Error: "Minimum loan amount is $1,000"
- Ensure `amountUsd` is at least 1000

### Error: "Maximum loan amount is $10,000,000"
- Ensure `amountUsd` is not more than 10,000,000

---

## Next Steps

1. **Run Migration** (when database is accessible):
   ```bash
   cd deployment_package/backend
   python manage.py migrate
   ```

2. **Create Test Banks** (via Django shell or admin):
   ```python
   from core.sbloc_models import SBLOCBank
   SBLOCBank.objects.create(
       name='Test Bank',
       min_apr=0.05,
       max_apr=0.08,
       min_ltv=0.5,
       max_ltv=0.7,
       min_loan_usd=10000,
       is_active=True
   )
   ```

3. **Test Queries** using the examples above

