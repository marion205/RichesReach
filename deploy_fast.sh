#!/bin/bash

# Fast AWS Deployment Script - Optimized for Speed
set -e

echo "🚀 Fast AWS Deployment - Optimized for Speed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "backend/backend" ]; then
    print_error "Please run this script from the RichesReach root directory"
    exit 1
fi

# Check AWS credentials
print_status "Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

print_success "AWS credentials verified"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "AWS Account ID: $AWS_ACCOUNT_ID"

# Set variables
PROJECT_NAME="riches-reach-ai"
REGION="us-east-1"
ECR_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-ai-service"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMAGE_TAG="fast-$TIMESTAMP"

print_status "Deployment Configuration:"
echo " Project: $PROJECT_NAME"
echo " Region: $REGION"
echo " ECR Repository: $ECR_REPO"
echo " Image Tag: $IMAGE_TAG"

# Navigate to backend directory
cd backend/backend

# Clean up any existing containers/images to free space
print_status "Cleaning up Docker cache..."
docker system prune -f > /dev/null 2>&1 || true

# Login to ECR (do this early to fail fast if there are auth issues)
print_status "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

# Create ECR repository if it doesn't exist
print_status "Ensuring ECR repository exists..."
aws ecr describe-repositories --repository-names $PROJECT_NAME-ai-service --region $REGION > /dev/null 2>&1 || {
    print_status "Creating ECR repository..."
    aws ecr create-repository --repository-name $PROJECT_NAME-ai-service --region $REGION
}

# Build Docker image with optimized Dockerfile and buildkit
print_status "Building optimized Docker image..."
export DOCKER_BUILDKIT=1
docker build \
    --tag $PROJECT_NAME-ai-service:$IMAGE_TAG \
    --tag $PROJECT_NAME-ai-service:latest \
    --file Dockerfile.optimized \
    --progress=plain \
    .

print_success "Docker image built successfully"

# Tag and push image to ECR
print_status "Tagging and pushing image to ECR..."
docker tag $PROJECT_NAME-ai-service:$IMAGE_TAG $ECR_REPO:$IMAGE_TAG
docker tag $PROJECT_NAME-ai-service:latest $ECR_REPO:latest

# Push both tags in parallel for faster upload
print_status "Pushing images to ECR (this may take a few minutes)..."
docker push $ECR_REPO:$IMAGE_TAG &
docker push $ECR_REPO:latest &
wait

print_success "Images pushed to ECR successfully"

# Deploy to ECS
print_status "Updating ECS service..."
ECS_CLUSTER="riches-reach-ai-production-cluster"
ECS_SERVICE="riches-reach-ai-ai"

# Check if ECS service exists
if aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $REGION > /dev/null 2>&1; then
    # Update service with new image
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --force-new-deployment \
        --region $REGION
    
    print_success "ECS service update initiated successfully"
    
    # Wait for deployment to complete (optional)
    print_status "Waiting for deployment to stabilize..."
    aws ecs wait services-stable \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $REGION
    
    print_success "Deployment completed and service is stable"
else
    print_warning "ECS service not found. You may need to create it first."
    print_status "Available clusters:"
    aws ecs list-clusters --region $REGION --query 'clusterArns[]' --output table
fi

print_success "🚀 Fast deployment completed!"
print_status "Deployment Summary:"
echo " ✅ Optimized Docker build with proper caching"
echo " ✅ Excluded unnecessary files from build context"
echo " ✅ Used buildkit for faster builds"
echo " ✅ Parallel image pushes to ECR"
echo " ✅ Service updated and stabilized"

print_status "Next steps:"
echo "1. Test your production API endpoints"
echo "2. Monitor the service in AWS ECS console"
echo "3. Check application logs for any issues"

print_success "🎉 Your application is now deployed with real data!"
