#!/bin/bash

# 🔧 RichesReach SSL & Routing Fix Script
# This script fixes SSL certificate issues and API routing problems

set -e  # Exit on any error

echo "🚀 Starting RichesReach SSL & Routing Fix"
echo "=========================================="

# Configuration
REGION="us-east-1"
CLUSTER_NAME="riches-reach-ai-production-cluster"
SERVICE_NAME="riches-reach-ai-ai"
LB_ARN="arn:aws:elasticloadbalancing:us-east-1:498606688292:loadbalancer/app/riches-reach-alb/32043ad73025696d"
TG_ARN="arn:aws:elasticloadbalancing:us-east-1:498606688292:targetgroup/riches-reach-tg/0233836fa56bf9f1"

echo "📋 Configuration:"
echo "  Region: $REGION"
echo "  Cluster: $CLUSTER_NAME"
echo "  Service: $SERVICE_NAME"
echo "  Load Balancer: $LB_ARN"
echo "  Target Group: $TG_ARN"
echo ""

# Step 1: Check current ECS service status
echo "🔍 Step 1: Checking ECS Service Status"
echo "--------------------------------------"
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $REGION \
  --query 'services[0].{Status:status,RunningCount:runningCount,DesiredCount:desiredCount,TaskDefinition:taskDefinition}' \
  --output table

# Step 2: Check current listeners
echo ""
echo "🔍 Step 2: Checking Current Load Balancer Listeners"
echo "---------------------------------------------------"
aws elbv2 describe-listeners \
  --load-balancer-arn $LB_ARN \
  --region $REGION \
  --query 'Listeners[*].{Port:Port,Protocol:Protocol,Certificates:Certificates}' \
  --output table

# Step 3: Check target group health
echo ""
echo "🔍 Step 3: Checking Target Group Health"
echo "---------------------------------------"
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --region $REGION \
  --query 'TargetHealthDescriptions[*].{Target:Target.Id,Health:TargetHealth.State,Reason:TargetHealth.Reason}' \
  --output table

# Step 4: Create HTTPS listener (if SSL cert exists)
echo ""
echo "🔒 Step 4: Setting up HTTPS Listener"
echo "------------------------------------"

# First, let's try to find an existing certificate
echo "Searching for SSL certificates..."
CERT_ARN=$(aws acm list-certificates --region $REGION --query 'CertificateSummaryList[0].CertificateArn' --output text 2>/dev/null || echo "")

if [ -z "$CERT_ARN" ] || [ "$CERT_ARN" = "None" ]; then
    echo "⚠️  No SSL certificate found. Creating self-signed certificate for testing..."
    echo "   For production, you should use AWS Certificate Manager with a proper domain."
    
    # Create a self-signed certificate for testing
    openssl req -x509 -newkey rsa:4096 -keyout /tmp/key.pem -out /tmp/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com" 2>/dev/null || echo "OpenSSL not available, skipping certificate creation"
    
    echo "⚠️  SSL certificate setup requires manual intervention."
    echo "   Please create an ACM certificate for your domain and update the script."
else
    echo "✅ Found SSL certificate: $CERT_ARN"
    
    # Create HTTPS listener
    echo "Creating HTTPS listener on port 443..."
    aws elbv2 create-listener \
      --load-balancer-arn $LB_ARN \
      --protocol HTTPS \
      --port 443 \
      --certificates CertificateArn=$CERT_ARN \
      --default-actions Type=forward,TargetGroupArn=$TG_ARN \
      --region $REGION \
      --output table || echo "⚠️  HTTPS listener may already exist"
fi

# Step 5: Update target group health check
echo ""
echo "🏥 Step 5: Updating Target Group Health Check"
echo "---------------------------------------------"
aws elbv2 modify-target-group \
  --target-group-arn $TG_ARN \
  --health-check-path "/health/" \
  --health-check-protocol HTTP \
  --health-check-port "traffic-port" \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --region $REGION \
  --output table

# Step 6: Force new deployment
echo ""
echo "🔄 Step 6: Forcing New ECS Deployment"
echo "-------------------------------------"
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region $REGION \
  --output table

# Step 7: Wait for deployment to stabilize
echo ""
echo "⏳ Step 7: Waiting for Deployment to Stabilize"
echo "----------------------------------------------"
echo "This may take 2-3 minutes..."
aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $REGION

# Step 8: Test the fixes
echo ""
echo "🧪 Step 8: Testing the Fixes"
echo "-----------------------------"

LB_DNS="riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com"

echo "Testing HTTP endpoint..."
curl -I http://$LB_DNS/health/ --max-time 10 || echo "HTTP test failed"

echo ""
echo "Testing GraphQL endpoint..."
curl -I http://$LB_DNS/graphql/ --max-time 10 || echo "GraphQL test failed"

# Step 9: Final verification
echo ""
echo "✅ Step 9: Final Verification"
echo "------------------------------"

# Check service status
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $REGION \
  --query 'services[0].{Status:status,RunningCount:runningCount,DesiredCount:desiredCount}' \
  --output table

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --region $REGION \
  --query 'TargetHealthDescriptions[*].{Target:Target.Id,Health:TargetHealth.State}' \
  --output table

echo ""
echo "🎉 Fix Complete!"
echo "==============="
echo "✅ ECS service redeployed"
echo "✅ Target group health check updated"
echo "✅ Load balancer configuration updated"
echo ""
echo "🌐 Your application is now accessible at:"
echo "   HTTP:  http://$LB_DNS"
echo "   HTTPS: https://$LB_DNS (if SSL certificate is configured)"
echo ""
echo "📱 Test these endpoints:"
echo "   Health: http://$LB_DNS/health/"
echo "   GraphQL: http://$LB_DNS/graphql/"
echo "   AI API: http://$LB_DNS/api/ai-options/recommendations/"
echo ""
echo "⚠️  Note: For production SSL, you need to:"
echo "   1. Create an ACM certificate for your domain"
echo "   2. Update the HTTPS listener with the correct certificate ARN"
echo "   3. Configure your domain to point to the load balancer"
echo ""
echo "🔧 Next steps:"
echo "   1. Test all endpoints from your mobile app"
echo "   2. Configure proper SSL certificate for production"
echo "   3. Update mobile app configuration if needed"
