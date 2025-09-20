#!/bin/bash

# AWS Deployment Script for RichesReach
set -e

echo "🚀 Starting RichesReach AWS Deployment..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install it first."
    exit 1
fi

# Configuration
REGION="us-east-1"
CLUSTER_NAME="richesreach-cluster"
SERVICE_NAME="richesreach-service"
TASK_DEFINITION="richesreach-task"
REPOSITORY_NAME="richesreach"

echo "📋 Configuration:"
echo "  Region: $REGION"
echo "  Cluster: $CLUSTER_NAME"
echo "  Service: $SERVICE_NAME"

# Create ECR repository
echo "📦 Creating ECR repository..."
aws ecr create-repository --repository-name $REPOSITORY_NAME --region $REGION || echo "Repository already exists"

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com

# Build and push Docker image
echo "🏗️ Building Docker image..."
docker build -t $REPOSITORY_NAME:latest .

# Tag and push image
ECR_URI=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest
docker tag $REPOSITORY_NAME:latest $ECR_URI
docker push $ECR_URI

echo "✅ Image pushed to ECR: $ECR_URI"

# Create ECS cluster
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION || echo "Cluster already exists"

# Create task definition
echo "📝 Creating task definition..."
cat > task-definition.json << EOF
{
  "family": "$TASK_DEFINITION",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "richesreach-backend",
      "image": "$ECR_URI",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DJANGO_SETTINGS_MODULE",
          "value": "richesreach.settings_production"
        },
        {
          "name": "DB_HOST",
          "value": "your-rds-endpoint.amazonaws.com"
        },
        {
          "name": "DB_NAME",
          "value": "richesreach_prod"
        },
        {
          "name": "DB_USER",
          "value": "postgres"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://your-elasticache-endpoint.cache.amazonaws.com:6379/0"
        }
      ],
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:$REGION:$(aws sts get-caller-identity --query Account --output text):secret:richesreach/db-password"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:$REGION:$(aws sts get-caller-identity --query Account --output text):secret:richesreach/secret-key"
        },
        {
          "name": "FINNHUB_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$REGION:$(aws sts get-caller-identity --query Account --output text):secret:richesreach/finnhub-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/richesreach",
          "awslogs-region": "$REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION

# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/richesreach --region $REGION || echo "Log group already exists"

# Create service
echo "🚀 Creating ECS service..."
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition $TASK_DEFINITION \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --region $REGION || echo "Service already exists"

echo "✅ Deployment completed!"
echo "🌐 Your application should be available at: http://your-alb-endpoint.amazonaws.com"

# Cleanup
rm task-definition.json

echo "🎉 RichesReach is now deployed on AWS!"

