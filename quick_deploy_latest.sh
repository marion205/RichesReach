#!/bin/bash

# Quick Deploy Latest Changes to AWS
# This script deploys the latest AI Options changes to your AWS production environment

set -e

echo "🚀 Deploying Latest AI Options Changes to AWS..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
if [ ! -f "backend/main.py" ]; then
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

print_status "Deployment Configuration:"
echo "   Project: $PROJECT_NAME"
echo "   Region: $REGION"
echo "   ECR Repository: $ECR_REPO"

# Build Docker image with latest changes
print_status "Building Docker image with latest AI Options changes..."
docker build -t $PROJECT_NAME-ai-service:latest -f backend/Dockerfile.production backend/

print_success "Docker image built successfully"

# Login to ECR
print_status "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

# Create ECR repository if it doesn't exist
print_status "Ensuring ECR repository exists..."
aws ecr describe-repositories --repository-names $PROJECT_NAME-ai-service --region $REGION > /dev/null 2>&1 || {
    print_status "Creating ECR repository..."
    aws ecr create-repository --repository-name $PROJECT_NAME-ai-service --region $REGION
}

# Tag and push image
print_status "Tagging and pushing image to ECR..."
docker tag $PROJECT_NAME-ai-service:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

print_success "Image pushed to ECR successfully"

# Deploy to ECS
print_status "Updating ECS service with latest changes..."
ECS_CLUSTER="riches-reach-ai-production-cluster"
ECS_SERVICE="riches-reach-ai-ai"

aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --region $REGION

print_success "ECS service update initiated successfully"
print_status "The service is now deploying your latest AI Options changes..."
print_status "You can monitor the deployment in the AWS ECS console"

print_success "🎉 Deployment completed!"
print_status "Your latest AI Options changes are now deployed to AWS"
print_status "Key updates deployed:"
echo "   ✅ AI Options strategy optimization fixes"
echo "   ✅ Mobile app auto-reload improvements"
echo "   ✅ Search button only behavior"
echo "   ✅ All new AI Options system files"

print_status "Next steps:"
echo "1. Test your mobile app to verify the changes"
echo "2. Check the AI Options screen functionality"
echo "3. Verify strategy optimization is working"
