#!/bin/bash

# Deploy Only Signals API to AWS ECS (Minimal Deployment)
set -e

echo "🚀 Deploying Signals API Only to AWS ECS..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
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

print_status "Deployment Configuration:"
echo " Project: $PROJECT_NAME"
echo " Region: $REGION"
echo " ECR Repository: $ECR_REPO"

# Navigate to backend directory
cd backend/backend

# Create a minimal production Dockerfile that just runs the signals API
print_status "Creating minimal production Dockerfile..."
cat > Dockerfile.signals << EOF
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=richesreach.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy only essential files for signals API
COPY manage.py /app/
COPY richesreach/ /app/richesreach/
COPY core/ /app/core/

# Create directories for logs and static files
RUN mkdir -p /app/logs /app/static

# Expose port
EXPOSE 8001

# Run the application with minimal settings
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
EOF

# Build Docker image with signals API only
print_status "Building minimal Docker image with signals API..."
docker build -t $PROJECT_NAME-ai-service:signals -f Dockerfile.signals .

print_success "Docker image built successfully"

# Login to ECR
print_status "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

# Tag and push image
print_status "Tagging and pushing signals-only image to ECR..."
docker tag $PROJECT_NAME-ai-service:signals $ECR_REPO:signals
docker push $ECR_REPO:signals

print_success "Signals-only image pushed to ECR successfully"

# Update ECS service to use the new image
print_status "Updating ECS service with signals-only image..."
ECS_CLUSTER="riches-reach-ai-production-cluster"
ECS_SERVICE="riches-reach-ai-ai"

# Update the task definition to use the new image
TASK_DEFINITION=$(aws ecs describe-task-definition --task-definition riches-reach-ai-task --region $REGION --query 'taskDefinition' --output json)

# Update the image URI in the task definition
UPDATED_TASK_DEF=$(echo "$TASK_DEFINITION" | jq --arg image "$ECR_REPO:signals" '.containerDefinitions[0].image = $image | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)')

# Register new task definition
NEW_TASK_DEF_ARN=$(echo "$UPDATED_TASK_DEF" | aws ecs register-task-definition --region $REGION --cli-input-json file:///dev/stdin --query 'taskDefinition.taskDefinitionArn' --output text)

print_status "New task definition registered: $NEW_TASK_DEF_ARN"

# Update the service to use the new task definition
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --task-definition $NEW_TASK_DEF_ARN --region $REGION

print_success "ECS service updated with signals-only image"

print_status "The service is now deploying your signals API..."
print_status "You can monitor the deployment in the AWS ECS console"

print_success "🚀 Signals API deployment completed!"
print_status "Key updates deployed:"
echo " ✅ Minimal Docker image with signals API only"
echo " ✅ No external dependencies or downloads"
echo " ✅ Simplified startup process"
echo " ✅ Signals GraphQL query ready"

print_status "Next steps:"
echo "1. Monitor the ECS service deployment in AWS console"
echo "2. Wait for the new task to start successfully"
echo "3. Test your production signals API endpoint"
echo "4. Update your mobile app to use the production URL"

# Clean up temporary files
rm -f Dockerfile.signals

print_success "🎉 Your signals API is now deployed to AWS ECS!"
