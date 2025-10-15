#!/bin/bash

# Certificate Status Check Script
# Use this to monitor your SSL certificate request status

set -e

echo "🔍 Checking SSL Certificate Status for RichesReach ALB..."

# Configuration
REGION="us-east-1"
DOMAIN="richesreach-alb-2022321469.us-east-1.elb.amazonaws.com"

echo "📍 Domain: $DOMAIN"
echo "🌍 Region: $REGION"
echo ""

# List all certificates for the domain
echo "📋 Searching for certificates for domain: $DOMAIN"
CERT_ARNS=$(aws acm list-certificates \
    --region "$REGION" \
    --query "CertificateSummaryList[?DomainName=='$DOMAIN'].CertificateArn" \
    --output text)

if [ -z "$CERT_ARNS" ]; then
    echo "❌ No certificates found for domain: $DOMAIN"
    echo ""
    echo "🔧 Next Steps:"
    echo "1. Go to AWS Certificate Manager (ACM) in the AWS Console"
    echo "2. Request a public certificate for: $DOMAIN"
    echo "3. Use DNS validation"
    echo "4. Wait for certificate to be issued"
    echo "5. Re-run this script to check status"
    exit 1
fi

echo "✅ Found certificate(s) for domain: $DOMAIN"
echo ""

# Check each certificate
for CERT_ARN in $CERT_ARNS; do
    echo "🔍 Checking certificate: $CERT_ARN"
    
    # Get certificate details
    CERT_STATUS=$(aws acm describe-certificate \
        --certificate-arn "$CERT_ARN" \
        --region "$REGION" \
        --query 'Certificate.Status' \
        --output text)
    
    CERT_DOMAIN=$(aws acm describe-certificate \
        --certificate-arn "$CERT_ARN" \
        --region "$REGION" \
        --query 'Certificate.DomainName' \
        --output text)
    
    CERT_TYPE=$(aws acm describe-certificate \
        --certificate-arn "$CERT_ARN" \
        --region "$REGION" \
        --query 'Certificate.Type' \
        --output text)
    
    echo "   Domain: $CERT_DOMAIN"
    echo "   Type: $CERT_TYPE"
    echo "   Status: $CERT_STATUS"
    
    case $CERT_STATUS in
        "ISSUED")
            echo "   ✅ Certificate is ISSUED and ready to use!"
            echo ""
            echo "🚀 Ready to deploy HTTPS listener:"
            echo "   ./setup-https-listener.sh $CERT_ARN"
            ;;
        "PENDING_VALIDATION")
            echo "   ⏳ Certificate is PENDING VALIDATION"
            echo ""
            echo "🔧 Validation Steps:"
            echo "1. Go to AWS Certificate Manager (ACM) in the AWS Console"
            echo "2. Click on the certificate: $CERT_ARN"
            echo "3. In the 'Domains' section, add the CNAME record to your DNS"
            echo "4. Wait for DNS propagation (5-10 minutes)"
            echo "5. Re-run this script to check status"
            ;;
        "VALIDATION_TIMED_OUT")
            echo "   ❌ Certificate validation TIMED OUT"
            echo ""
            echo "🔧 Next Steps:"
            echo "1. Go to AWS Certificate Manager (ACM) in the AWS Console"
            echo "2. Click on the certificate: $CERT_ARN"
            echo "3. Click 'Request validation' to retry"
            echo "4. Ensure DNS records are correct"
            ;;
        "FAILED")
            echo "   ❌ Certificate validation FAILED"
            echo ""
            echo "🔧 Next Steps:"
            echo "1. Go to AWS Certificate Manager (ACM) in the AWS Console"
            echo "2. Check the validation error details"
            echo "3. Fix DNS records and retry validation"
            ;;
        *)
            echo "   ⚠️ Unknown status: $CERT_STATUS"
            ;;
    esac
    
    echo ""
done

echo "📋 Certificate Summary:"
echo "   Domain: $DOMAIN"
echo "   Region: $REGION"
echo "   Certificates found: $(echo $CERT_ARNS | wc -w)"
echo ""

if echo "$CERT_ARNS" | grep -q "ISSUED"; then
    echo "🎉 Ready to deploy HTTPS!"
else
    echo "⏳ Certificate still pending - check AWS Console for details"
fi
