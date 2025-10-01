#!/bin/bash

# Application Load Balancer Setup Script for RichesReach
# This script creates an ALB for better reliability and HTTPS support

set -e

echo "🚀 Setting up Application Load Balancer for RichesReach..."

# Configuration
REGION="us-east-1"
VPC_ID="vpc-0298e0babc3977b39"  # Your VPC ID
SUBNET_IDS="subnet-04421d26dcf89b921,subnet-0e870d6ea49288b90"  # Your subnet IDs
SECURITY_GROUP_ID="sg-0f235e0e1f378f096"  # Your security group ID
CLUSTER_NAME="richesreach-cluster"
SERVICE_NAME="richesreach-service"

# Create ALB Security Group
echo "📋 Creating ALB Security Group..."
ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name richesreach-alb-sg \
    --description "Security group for RichesReach ALB" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' \
    --output text)

echo "✅ ALB Security Group created: $ALB_SG_ID"

# Add inbound rules for ALB
echo "🔒 Adding ALB security group rules..."
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $REGION

aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region $REGION

# Update ECS service security group to allow ALB traffic
echo "🔒 Updating ECS service security group..."
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8000 \
    --source-group $ALB_SG_ID \
    --region $REGION

# Create Application Load Balancer
echo "⚖️ Creating Application Load Balancer..."
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name richesreach-alb \
    --subnets subnet-04421d26dcf89b921 subnet-0e870d6ea49288b90 \
    --security-groups $ALB_SG_ID \
    --region $REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

echo "✅ ALB created: $ALB_ARN"

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --region $REGION \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "🌐 ALB DNS Name: $ALB_DNS"

# Create Target Group
echo "🎯 Creating Target Group..."
TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
    --name richesreach-targets \
    --protocol HTTP \
    --port 8000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-path /health/ \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --region $REGION \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

echo "✅ Target Group created: $TARGET_GROUP_ARN"

# Create HTTP Listener
echo "👂 Creating HTTP Listener..."
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
    --region $REGION

echo "✅ HTTP Listener created"

# Update ECS Service to use ALB
echo "🔄 Updating ECS Service to use ALB..."

# Get current service configuration
SERVICE_ARN=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].serviceArn' \
    --output text)

# Update service with load balancer configuration
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --load-balancers targetGroupArn=$TARGET_GROUP_ARN,containerName=richesreach-backend,containerPort=8000 \
    --region $REGION

echo "✅ ECS Service updated with ALB configuration"

# Wait for service to stabilize
echo "⏳ Waiting for service to stabilize..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION

echo "✅ Service is stable"

# Test ALB endpoint
echo "🧪 Testing ALB endpoint..."
sleep 10  # Give ALB time to register targets

if curl -s "http://$ALB_DNS/health/" | grep -q "ok"; then
    echo "✅ ALB is working correctly!"
    echo "🌐 Your API is now available at: http://$ALB_DNS"
else
    echo "⚠️ ALB test failed. Check target group health."
fi

echo ""
echo "🎉 Application Load Balancer setup complete!"
echo ""
echo "📋 Summary:"
echo "   ALB ARN: $ALB_ARN"
echo "   ALB DNS: $ALB_DNS"
echo "   Target Group: $TARGET_GROUP_ARN"
echo "   Security Group: $ALB_SG_ID"
echo ""
echo "🔗 API Endpoints:"
echo "   HTTP: http://$ALB_DNS"
echo "   Health: http://$ALB_DNS/health/"
echo "   AI Status: http://$ALB_DNS/api/ai-status"
echo "   AI Options: http://$ALB_DNS/api/ai-options/recommendations"
echo ""
echo "📱 Update your mobile app configuration:"
echo "   API_BASE_URL: http://$ALB_DNS"
echo "   GRAPHQL_URL: http://$ALB_DNS/graphql/"
echo "   WS_URL: ws://$ALB_DNS/ws/"
echo ""
echo "🔒 Next steps for HTTPS:"
echo "   1. Request SSL certificate in AWS Certificate Manager"
echo "   2. Create HTTPS listener on port 443"
echo "   3. Update mobile app to use https:// URLs"
