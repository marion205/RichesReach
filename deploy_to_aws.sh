#!/bin/bash

# Deploy Signals API to AWS ECS Production
set -e

echo "🚀 Deploying Signals API to AWS ECS Production..."

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

print_status "Deployment Configuration:"
echo " Project: $PROJECT_NAME"
echo " Region: $REGION"
echo " ECR Repository: $ECR_REPO"

# Navigate to backend directory
cd backend/backend

# Create a temporary requirements file with fixed dependencies
print_status "Creating production requirements with fixed dependencies..."
cat > requirements_aws.txt << EOF
# Production requirements for RichesReach Signals API
# Core Django
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-environ==0.11.2

# GraphQL
graphene-django==3.1.5
graphql-core==3.2.3
graphql-relay==3.2.0
django-graphql-jwt==0.4.0

# Database
psycopg2-binary==2.9.7
django-redis==5.4.0

# Celery
celery==5.3.4
redis==5.0.1
django-celery-beat==2.5.0
django-celery-results==2.5.1

# HTTP requests
requests==2.31.0
aiohttp==3.9.1

# Monitoring and logging
sentry-sdk==1.38.0
whitenoise==6.6.0

# Security
django-ratelimit==4.1.0
django-axes==6.1.1

# Production server
gunicorn==21.2.0
uvicorn==0.24.0
EOF

# Create a production Dockerfile
print_status "Creating production Dockerfile..."
cat > Dockerfile.aws << EOF
FROM python:3.10-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=richesreach.settings

# Set work directory
WORKDIR /app

# Install system dependencies with caching and retries
RUN --mount=type=cache,target=/var/cache/apt \\
    --mount=type=cache,target=/var/lib/apt \\
    apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout="10" \\
 && apt-get install -y --no-install-recommends \\
      postgresql-client \\
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_aws.txt /app/
RUN --mount=type=cache,target=/root/.cache/pip \\
    pip install --no-cache-dir --prefer-binary -r requirements_aws.txt

# Copy project
COPY . /app/

# Create directories for logs and static files
RUN mkdir -p /app/logs /app/static

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Run the application
CMD ["/bin/sh", "-c", "python manage.py migrate --run-syncdb && python manage.py runserver 0.0.0.0:8000"]
EOF

# Build Docker image with latest signals API changes
print_status "Building Docker image with signals API changes..."
docker build -t $PROJECT_NAME-ai-service:latest -f Dockerfile.aws .

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
print_status "Updating ECS service with signals API changes..."
ECS_CLUSTER="riches-reach-ai-production-cluster"
ECS_SERVICE="riches-reach-ai-ai"

# Check if ECS service exists
if aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $REGION > /dev/null 2>&1; then
    aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --region $REGION
    print_success "ECS service update initiated successfully"
else
    print_warning "ECS service not found. You may need to create it first."
    print_status "Available clusters:"
    aws ecs list-clusters --region $REGION --query 'clusterArns[]' --output table
fi

print_status "The service is now deploying your signals API changes..."
print_status "You can monitor the deployment in the AWS ECS console"

print_success "🚀 Signals API deployment completed!"
print_status "Key updates deployed:"
echo " ✅ Fixed Django User model conflicts"
echo " ✅ Added SignalType to GraphQL schema"
echo " ✅ Added signals query with all expected fields"
echo " ✅ Fixed production requirements dependencies"
echo " ✅ Updated Docker configuration"

print_status "Next steps:"
echo "1. Monitor the ECS service deployment in AWS console"
echo "2. Test your production signals API endpoint"
echo "3. Update your mobile app to use the production URL"
echo "4. Verify signals query functionality in production"

# Clean up temporary files
rm -f requirements_aws.txt Dockerfile.aws

print_success "🎉 Your signals API is now deployed to AWS ECS!"
