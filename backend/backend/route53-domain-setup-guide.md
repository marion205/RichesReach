# Route 53 Domain Registration & HTTPS Setup Guide

## 🎯 Complete Setup Process

### Step 1: Register Domain on Route 53
1. **Go to Route 53**: [https://console.aws.amazon.com/route53/home](https://console.aws.amazon.com/route53/home)
2. **Click "Register domain"**
3. **Search for domain**: `richesreach.com` (or your preferred name)
4. **Select domain**: Choose from available options
5. **Add to cart**: Click "Add to cart"
6. **Review and purchase**: ~$12/year for .com domains

### Step 2: Configure DNS Records
Once domain is registered (takes 5-10 minutes):

1. **Go to Hosted Zones**: Route 53 → Hosted zones
2. **Click on your domain**: `richesreach.com`
3. **Create CNAME record**:
   - **Record name**: `app`
   - **Record type**: `CNAME`
   - **Value**: `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
   - **TTL**: `300` (5 minutes)

### Step 3: Request SSL Certificate
1. **Go to Certificate Manager**: [https://console.aws.amazon.com/acm/home](https://console.aws.amazon.com/acm/home)
2. **Select Region**: **US East (N. Virginia) us-east-1**
3. **Click "Request a certificate"**
4. **Select "Request a public certificate"**
5. **Domain name**: `app.richesreach.com`
6. **Validation method**: **DNS validation**
7. **Click "Request"**

### Step 4: Complete DNS Validation
1. **Certificate Status**: Will show "Pending validation"
2. **Click on certificate** to view details
3. **In "Domains" section**: Copy the CNAME record
4. **Add CNAME to Route 53**:
   - **Record name**: `_abc123.app` (from ACM)
   - **Record type**: `CNAME`
   - **Value**: `_def456.acm-validations.aws` (from ACM)
   - **TTL**: `300`

### Step 5: Wait for Certificate Issuance
- **Status**: "Pending validation" → "Issued"
- **Time**: 5-15 minutes
- **Copy Certificate ARN** when issued

### Step 6: Deploy HTTPS Listener
```bash
./setup-https-listener.sh arn:aws:acm:us-east-1:498606688292:certificate/NEW-CERT-ID
```

### Step 7: Update Mobile App
Update mobile app configuration to use custom domain:
- **API**: `https://app.richesreach.com`
- **GraphQL**: `https://app.richesreach.com/graphql/`
- **WebSocket**: `wss://app.richesreach.com/ws/`

## 🎯 Expected Timeline
- **Domain Registration**: 5-10 minutes
- **DNS Propagation**: 5-10 minutes
- **Certificate Request**: 2-3 minutes
- **Certificate Validation**: 5-15 minutes
- **HTTPS Deployment**: 2-3 minutes
- **Total**: 20-40 minutes

## 💰 Cost Breakdown
- **Domain Registration**: ~$12/year
- **Route 53 Hosted Zone**: $0.50/month
- **DNS Queries**: $0.40 per million queries
- **SSL Certificate**: FREE
- **Total**: ~$18/year

## 🔧 Alternative Domain Names
If `richesreach.com` is taken, try:
- `richesreachapp.com`
- `richesreach.io`
- `richesreach.co`
- `getrichesreach.com`
- `richesreach.trade`

## 📋 DNS Record Summary
```
# Main app subdomain
app.richesreach.com → richesreach-alb-2022321469.us-east-1.elb.amazonaws.com

# SSL validation (from ACM)
_abc123.app.richesreach.com → _def456.acm-validations.aws
```

## 🚀 Final Production URLs
- **API**: `https://app.richesreach.com`
- **Health**: `https://app.richesreach.com/health/`
- **AI Status**: `https://app.richesreach.com/api/ai-status`
- **AI Options**: `https://app.richesreach.com/api/ai-options/recommendations`
- **GraphQL**: `https://app.richesreach.com/graphql/`
- **WebSocket**: `wss://app.richesreach.com/ws/`
