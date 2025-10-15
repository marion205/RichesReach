# Create New SSL Certificate - Step by Step

## Why the Current Certificate Failed
- **Status**: FAILED
- **Reason**: DNS validation likely failed
- **Action**: Create a new certificate

## Steps to Create New Certificate

### 1. Delete Failed Certificate (Optional)
1. Go to AWS Certificate Manager (ACM)
2. Find certificate: `953cba04-ba00-45fe-af4a-908e4fb6fd73`
3. Click "Delete" (optional - can leave it)

### 2. Request New Certificate
1. **Go to ACM**: [https://console.aws.amazon.com/acm/home](https://console.aws.amazon.com/acm/home)
2. **Select Region**: **US East (N. Virginia) us-east-1**
3. **Click "Request a certificate"**
4. **Select "Request a public certificate"**
5. **Domain name**: `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
6. **Validation method**: **DNS validation**
7. **Click "Request"**

### 3. Complete DNS Validation
1. **Certificate Status**: Will show "Pending validation"
2. **Click on the certificate** to view details
3. **In "Domains" section**: Add the CNAME record if required
4. **Wait 5-15 minutes** for validation

### 4. Get New Certificate ARN
Once status changes to "Issued":
1. **Copy the new Certificate ARN**
2. **Format**: `arn:aws:acm:us-east-1:498606688292:certificate/NEW-CERT-ID`

### 5. Deploy HTTPS Listener
```bash
./setup-https-listener.sh arn:aws:acm:us-east-1:498606688292:certificate/NEW-CERT-ID
```

## Expected Timeline
- **Certificate Request**: 2-3 minutes
- **DNS Validation**: 5-15 minutes
- **HTTPS Deployment**: 2-3 minutes
- **Total**: 10-20 minutes

## Troubleshooting Tips
- **Exact Domain**: Must match ALB DNS name exactly
- **Region**: Must be us-east-1
- **DNS Records**: Add CNAME record if manual validation required
- **Wait Time**: Allow 5-10 minutes for DNS propagation
