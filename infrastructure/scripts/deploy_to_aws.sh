#!/bin/bash
# AWS Production Deployment Script for RichesReach AI

set -e

echo "Starting AWS Production Deployment..."

# Check AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "ERROR: AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Set variables
PROJECT_NAME="riches-reach-ai"
REGION="us-east-1"
STACK_NAME="${PROJECT_NAME}-production"

echo "Deployment Configuration:"
echo "   Project: $PROJECT_NAME"
echo "   Region: $REGION"
echo "   Stack: $STACK_NAME"

# Build and push Docker image
echo "🐳 Building Docker image..."
docker build -t $PROJECT_NAME-ai-service .

echo "📤 Pushing to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names $PROJECT_NAME-ai-service --region $REGION || aws ecr create-repository --repository-name $PROJECT_NAME-ai-service --region $REGION

# Tag and push image
docker tag $PROJECT_NAME-ai-service:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-ai-service:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-ai-service:latest

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy     --template-file cloudformation-template.yaml     --stack-name $STACK_NAME     --parameter-overrides Environment=production     --capabilities CAPABILITY_NAMED_IAM     --region $REGION

echo "SUCCESS: Deployment completed successfully!"
echo "Check CloudFormation console for stack status"
echo "🌐 Load Balancer DNS: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' --output text)"
