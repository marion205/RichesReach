# SSL Certificate Request Guide - AWS Console

## Step-by-Step Instructions

### 1. Access AWS Certificate Manager
1. **Login to AWS Console**: Go to [https://aws.amazon.com/console/](https://aws.amazon.com/console/)
2. **Navigate to Certificate Manager**: 
   - Search for "Certificate Manager" in the services search bar
   - Or go directly to: [https://console.aws.amazon.com/acm/home](https://console.aws.amazon.com/acm/home)
3. **Select Region**: Make sure you're in **US East (N. Virginia) us-east-1** region

### 2. Request Public Certificate
1. **Click "Request a certificate"** button
2. **Select "Request a public certificate"**
3. **Click "Next"**

### 3. Add Domain Name
1. **Domain name**: Enter exactly: `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
2. **Subject Alternative Names (SANs)**: Leave empty (not needed for single domain)
3. **Click "Next"**

### 4. Select Validation Method
1. **Choose "DNS validation"** (recommended)
2. **Click "Next"**

### 5. Add Tags (Optional)
1. **Key**: `Project`
2. **Value**: `RichesReach`
3. **Click "Next"**

### 6. Review and Request
1. **Review the configuration**:
   - Domain: `richesreach-alb-2022321469.us-east-1.elb.amazonaws.com`
   - Validation: DNS validation
   - Region: US East (N. Virginia)
2. **Click "Request"**

### 7. DNS Validation
1. **Certificate Status**: Will show "Pending validation"
2. **Click on the certificate** to view details
3. **In the "Domains" section**, you'll see a CNAME record to add
4. **Copy the CNAME record** (Name and Value)

### 8. Add DNS Record (If Required)
Since this is an ALB domain, AWS typically handles the DNS validation automatically. However, if manual validation is required:

1. **Go to Route 53** (if using Route 53) or your DNS provider
2. **Add the CNAME record** provided by ACM
3. **Wait for DNS propagation** (usually 5-10 minutes)

### 9. Wait for Certificate Issuance
1. **Refresh the ACM console** every few minutes
2. **Certificate status** will change from "Pending validation" to "Issued"
3. **This typically takes 5-15 minutes**

### 10. Copy Certificate ARN
Once issued:
1. **Click on the certificate**
2. **Copy the ARN** (starts with `arn:aws:acm:us-east-1:498606688292:certificate/`)
3. **Save this ARN** - you'll need it for the next step

## Expected Certificate ARN Format
```
arn:aws:acm:us-east-1:498606688292:certificate/12345678-1234-1234-1234-123456789012
```

## Next Steps After Certificate Issuance
Once you have the certificate ARN, run this command:

```bash
./setup-https-listener.sh arn:aws:acm:us-east-1:498606688292:certificate/YOUR-CERT-ID
```

## Troubleshooting

### Certificate Not Issuing
- **Check DNS validation**: Ensure CNAME record is properly added
- **Wait longer**: DNS propagation can take up to 24 hours
- **Check domain ownership**: Ensure you have access to the domain

### Validation Issues
- **CNAME record format**: Must match exactly as provided by ACM
- **DNS propagation**: Wait 5-10 minutes after adding the record
- **Multiple attempts**: You can re-request validation if it fails

### Common Issues
- **Wrong region**: Certificate must be in us-east-1 for ALB
- **Domain mismatch**: Must match ALB DNS name exactly
- **Validation timeout**: ACM will retry validation automatically

## Security Notes
- **Certificate is free** for AWS services
- **Auto-renewal**: AWS handles certificate renewal automatically
- **HTTPS only**: Certificate is only valid for HTTPS connections
- **ALB integration**: Certificate will be automatically attached to ALB

## Support
If you encounter issues:
1. **Check AWS documentation**: [ACM User Guide](https://docs.aws.amazon.com/acm/)
2. **AWS Support**: Available if you have a support plan
3. **Community forums**: AWS re:Post for community help
