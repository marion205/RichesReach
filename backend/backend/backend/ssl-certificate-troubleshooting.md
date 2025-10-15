# SSL Certificate Troubleshooting Guide

## Current Issue
**Error**: `UnsupportedCertificate: The certificate must have a fully-qualified domain name, a supported signature, and a supported key size.`

## Possible Causes

### 1. Certificate Not Fully Issued
- **Status**: Certificate might still be "Pending validation"
- **Solution**: Check certificate status in AWS Console

### 2. Domain Name Mismatch
- **Issue**: Certificate domain doesn't match ALB DNS name exactly
- **Required**: `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
- **Solution**: Ensure exact domain match

### 3. Certificate Region Mismatch
- **Issue**: Certificate created in wrong region
- **Required**: `us-east-1` (N. Virginia)
- **Solution**: Create certificate in correct region

### 4. DNS Validation Not Complete
- **Issue**: DNS validation records not properly added
- **Solution**: Complete DNS validation process

## Troubleshooting Steps

### Step 1: Check Certificate Status
1. Go to AWS Certificate Manager (ACM)
2. Select region: **US East (N. Virginia) us-east-1**
3. Find certificate: `953cba04-ba00-45fe-af4a-908e4fb6fd73`
4. Check status:
   - ✅ **ISSUED**: Certificate is ready
   - ⏳ **PENDING_VALIDATION**: Still validating
   - ❌ **FAILED**: Validation failed

### Step 2: Verify Domain Name
- **Certificate Domain**: Must be exactly `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
- **No wildcards**: Must be exact match
- **No subdomains**: Must be the full ALB DNS name

### Step 3: Check Region
- **Certificate Region**: Must be `us-east-1`
- **ALB Region**: Must be `us-east-1`
- **Both must match**: Certificate and ALB in same region

### Step 4: Complete DNS Validation
If status is "PENDING_VALIDATION":
1. Click on the certificate in ACM console
2. In "Domains" section, add the CNAME record
3. Wait 5-10 minutes for DNS propagation
4. Check status again

## Alternative Solutions

### Option 1: Create New Certificate
If current certificate has issues:
1. Delete the problematic certificate
2. Create new certificate with exact domain name
3. Complete DNS validation
4. Use new certificate ARN

### Option 2: Use HTTP for Now
If HTTPS setup is urgent:
1. Keep HTTP listener (already working)
2. Update mobile app to use HTTP temporarily
3. Fix certificate issues later
4. Deploy HTTPS when ready

### Option 3: Custom Domain
For production:
1. Register a custom domain (e.g., `api.richesreach.com`)
2. Create certificate for custom domain
3. Point custom domain to ALB
4. Use custom domain for HTTPS

## Current Working Configuration

### HTTP Endpoints (Working Now)
- **API**: `http://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
- **Health**: `http://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/health/`
- **AI Status**: `http://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/api/ai-status`

### Mobile App Configuration
Currently configured for HTTPS, but can be updated to HTTP if needed:
```bash
# Temporary HTTP configuration
EXPO_PUBLIC_API_URL=http://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com
```

## Next Steps

### Immediate Action Required
1. **Check certificate status** in AWS Console
2. **Verify domain name** matches exactly
3. **Complete DNS validation** if pending
4. **Retry HTTPS listener creation** once certificate is issued

### If Certificate Issues Persist
1. **Create new certificate** with correct domain
2. **Use HTTP temporarily** for immediate deployment
3. **Plan custom domain** for production

## Commands to Retry

### Once Certificate is Fixed
```bash
./setup-https-listener.sh arn:aws:acm:us-east-1:498606688292:certificate/953cba04-ba00-45fe-af4a-908e4fb6fd73
```

### Test HTTPS (After Success)
```bash
curl https://richesreach-alb-2022321469.us-east-1.elb.amazonaws.com/health/
```

## Support Resources
- **AWS ACM Documentation**: [Certificate Manager User Guide](https://docs.aws.amazon.com/acm/)
- **ALB Documentation**: [Application Load Balancer User Guide](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- **AWS Support**: Available with support plan
