# HTTPS Setup Guide for RichesReach

## Current Status
- ✅ Application Load Balancer deployed: `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
- ✅ HTTP listener working on port 80
- ⚠️ HTTPS setup requires manual SSL certificate configuration

## Manual HTTPS Setup Steps

### 1. Request SSL Certificate (Manual)
Since the IAM user has reached the policy limit, you'll need to request the SSL certificate manually:

**Option A: AWS Console**
1. Go to AWS Certificate Manager (ACM) in the AWS Console
2. Click "Request a certificate"
3. Choose "Request a public certificate"
4. Add domain name: `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
5. Choose DNS validation
6. Complete the validation process

**Option B: Root Account**
If you have root account access, run:
```bash
aws acm request-certificate \
    --domain-name richesreach-alb-2022321469.us-east-1.elb.amazonaws.com \
    --validation-method DNS \
    --region us-east-1
```

### 2. Create HTTPS Listener
Once you have the certificate ARN, run this command:

```bash
# Replace CERT_ARN with your actual certificate ARN
CERT_ARN="arn:aws:acm:us-east-1:498606688292:certificate/YOUR-CERT-ID"
ALB_ARN="arn:aws:elasticloadbalancing:us-east-1:498606688292:loadbalancer/app/richesreach-alb/70143b6be8b29e2e"
TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:us-east-1:498606688292:targetgroup/richesreach-targets/b20d823071647df7"

aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=$CERT_ARN \
    --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
    --region us-east-1
```

### 3. Update Mobile App Configuration
The mobile app has already been updated to use HTTPS URLs. Once the certificate is active, the app will automatically use HTTPS.

### 4. Test HTTPS Endpoints
After setup, test these endpoints:
- `https://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/`
- `https://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/health/`
- `https://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/api/ai-status`

## Current Working Endpoints (HTTP)
- `http://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/`
- `http://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/health/`
- `http://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/api/ai-status`
- `http://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/api/ai-options/recommendations`

## Mobile App Configuration
The mobile app is already configured to use HTTPS URLs:
- **API Base URL**: `https://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
- **GraphQL URL**: `https://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/graphql/`
- **WebSocket URL**: `wss://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/ws/`

## Security Benefits
Once HTTPS is enabled:
- ✅ Encrypted data transmission
- ✅ SSL/TLS security
- ✅ App store compliance
- ✅ User trust and security
- ✅ Modern web standards compliance

## Troubleshooting
- If HTTPS doesn't work immediately, wait 5-10 minutes for certificate propagation
- Check certificate status in ACM console
- Verify ALB listener configuration
- Test with `curl -k` to bypass certificate verification during testing
