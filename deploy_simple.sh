#!/bin/bash

echo "🚀 Deploying Signals API to AWS ECS..."

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured"
    exit 1
fi

echo "✅ AWS credentials verified"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Set variables
PROJECT_NAME="riches-reach-ai"
REGION="us-east-1"
ECR_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME-ai-service"

echo "Deployment Configuration:"
echo " Project: $PROJECT_NAME"
echo " Region: $REGION"
echo " ECR Repository: $ECR_REPO"

# Navigate to backend directory
cd backend/backend

# Create a minimal production Dockerfile
echo "Creating minimal production Dockerfile..."
cat > Dockerfile.signals << EOF
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=richesreach.settings

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py /app/
COPY richesreach/ /app/richesreach/
COPY core/ /app/core/

EXPOSE 8001

CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
EOF

# Build Docker image
echo "Building Docker image..."
docker build -t $PROJECT_NAME-ai-service:signals -f Dockerfile.signals .

echo "✅ Docker image built successfully"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

# Tag and push image
echo "Pushing image to ECR..."
docker tag $PROJECT_NAME-ai-service:signals $ECR_REPO:signals
docker push $ECR_REPO:signals

echo "✅ Image pushed to ECR successfully"

# Update ECS service
echo "Updating ECS service..."
ECS_CLUSTER="riches-reach-ai-production-cluster"
ECS_SERVICE="riches-reach-ai-ai"

# Force new deployment
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --region $REGION

echo "✅ ECS service update initiated"

echo "🎉 Signals API deployment completed!"
echo "Monitor the deployment in AWS ECS console"

# Clean up
rm -f Dockerfile.signals
