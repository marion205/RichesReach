#!/bin/bash

# HTTPS Listener Setup Script for RichesReach ALB
# Run this script after obtaining the SSL certificate ARN

set -e

echo "🔒 Setting up HTTPS Listener for RichesReach ALB..."

# Configuration
REGION="us-east-1"
ALB_ARN="arn:aws:elasticloadbalancing:us-east-1:498606688292:loadbalancer/app/richesreach-alb/70143b6be8b29e2e"
TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:us-east-1:498606688292:targetgroup/richesreach-targets/b20d823071647df7"

# Check if certificate ARN is provided
if [ -z "$1" ]; then
    echo "❌ Error: SSL Certificate ARN is required"
    echo "Usage: $0 <CERTIFICATE_ARN>"
    echo ""
    echo "To get the certificate ARN:"
    echo "1. Go to AWS Certificate Manager (ACM) in the AWS Console"
    echo "2. Find your certificate for richesreach-alb-2022321469.us-east-1.elb.amazonaws.com"
    echo "3. Copy the ARN (starts with arn:aws:acm:us-east-1:...)"
    echo ""
    echo "Example:"
    echo "$0 arn:aws:acm:us-east-1:498606688292:certificate/12345678-1234-1234-1234-123456789012"
    exit 1
fi

CERT_ARN="$1"

echo "📋 Configuration:"
echo "   ALB ARN: $ALB_ARN"
echo "   Target Group: $TARGET_GROUP_ARN"
echo "   Certificate ARN: $CERT_ARN"
echo "   Region: $REGION"
echo ""

# Verify certificate exists and is issued
echo "🔍 Verifying certificate status..."
CERT_STATUS=$(aws acm describe-certificate \
    --certificate-arn "$CERT_ARN" \
    --region "$REGION" \
    --query 'Certificate.Status' \
    --output text)

if [ "$CERT_STATUS" != "ISSUED" ]; then
    echo "❌ Error: Certificate is not issued. Current status: $CERT_STATUS"
    echo "Please wait for the certificate to be issued before running this script."
    exit 1
fi

echo "✅ Certificate is issued and ready to use"

# Create HTTPS listener
echo "👂 Creating HTTPS Listener..."
LISTENER_ARN=$(aws elbv2 create-listener \
    --load-balancer-arn "$ALB_ARN" \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn="$CERT_ARN" \
    --default-actions Type=forward,TargetGroupArn="$TARGET_GROUP_ARN" \
    --region "$REGION" \
    --query 'Listeners[0].ListenerArn' \
    --output text)

echo "✅ HTTPS Listener created: $LISTENER_ARN"

# Test HTTPS endpoint
echo "🧪 Testing HTTPS endpoint..."
sleep 10  # Give ALB time to update

ALB_DNS="richesreach-alb-2022321469.us-east-1.elb.amazonaws.com"

if curl -s "https://$ALB_DNS/health/" | grep -q "ok"; then
    echo "✅ HTTPS is working correctly!"
    echo "🌐 Your API is now available at: https://$ALB_DNS"
else
    echo "⚠️ HTTPS test failed. This might be due to:"
    echo "   - Certificate propagation delay (wait 5-10 minutes)"
    echo "   - DNS propagation delay"
    echo "   - ALB configuration update delay"
    echo ""
    echo "You can test manually with:"
    echo "curl -k https://$ALB_DNS/health/"
fi

echo ""
echo "🎉 HTTPS Listener setup complete!"
echo ""
echo "📋 Summary:"
echo "   HTTPS Listener ARN: $LISTENER_ARN"
echo "   Certificate ARN: $CERT_ARN"
echo "   HTTPS URL: https://$ALB_DNS"
echo ""
echo "🔗 HTTPS Endpoints:"
echo "   API: https://$ALB_DNS"
echo "   Health: https://$ALB_DNS/health/"
echo "   AI Status: https://$ALB_DNS/api/ai-status"
echo "   AI Options: https://$ALB_DNS/api/ai-options/recommendations"
echo ""
echo "📱 Mobile App Configuration:"
echo "   The mobile app is already configured to use HTTPS URLs"
echo "   No additional changes needed - it will automatically use HTTPS"
echo ""
echo "🔒 Security Benefits:"
echo "   ✅ Encrypted data transmission"
echo "   ✅ SSL/TLS security"
echo "   ✅ App store compliance"
echo "   ✅ User trust and security"
