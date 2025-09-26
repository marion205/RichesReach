#!/bin/bash

# Quick deployment with 403 error fix
set -e

echo "🚀 Deploying fixed version to AWS..."

# Set variables
REGION="us-east-1"
ACCOUNT_ID="498606688292"
ECR_REPO="riches-reach-ai-ai-service"
IMG="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}:fixed-$(date +%Y%m%d%H%M%S)"
CLUSTER="riches-reach-ai-production-cluster"
SERVICE="riches-reach-ai-ai"

echo "Building image: $IMG"

# Build with the production Dockerfile
docker build -f backend/backend/Dockerfile.production backend/backend -t rr-fixed:latest

echo "✅ Build complete"

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Tag and push
docker tag rr-fixed:latest $IMG
docker push $IMG

echo "✅ Image pushed: $IMG"

# Update ECS service
aws ecs update-service --cluster $CLUSTER --service $SERVICE --force-new-deployment --region $REGION

echo "✅ Service update initiated"

# Watch the deployment
echo "Watching deployment..."
aws ecs describe-services --cluster $CLUSTER --services $SERVICE --region $REGION --query 'services[0].events[0:5]'

echo "🎉 Deployment completed!"
echo "The 403 error should be fixed now."
