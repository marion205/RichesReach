#!/bin/bash

echo "🚀 Deploying Clean Signals API to AWS ECS Fargate..."

# Set variables
AWS_REGION="us-east-1"
ACCOUNT_ID="498606688292"
ECR_REPO="richesreach-api"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMG="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:signals-$TIMESTAMP"

echo "Building image: $IMG"

# Navigate to backend directory
cd backend/backend

# Create ECR repository if it doesn't exist
echo "Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name $ECR_REPO

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build Docker image
echo "Building Docker image..."
docker build -t $IMG .

# Push to ECR
echo "Pushing image to ECR..."
docker push $IMG

echo "✅ Image pushed successfully: $IMG"

# Create log group
echo "Creating log group..."
aws logs create-log-group --log-group-name /ecs/richesreach-signals 2>/dev/null || true

# Create task definition
echo "Creating task definition..."
cat > task-def.json << EOF
{
  "family": "richesreach-signals",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "$IMG",
      "portMappings": [{ "containerPort": 8001, "protocol": "tcp" }],
      "environment": [
        {"name": "DJANGO_SETTINGS_MODULE", "value": "richesreach.settings"},
        {"name": "DEBUG", "value": "False"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/richesreach-signals",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Register task definition
echo "Registering task definition..."
aws ecs register-task-definition --cli-input-json file://task-def.json

# Create cluster if it doesn't exist
echo "Creating ECS cluster..."
aws ecs create-cluster --cluster-name richesreach-cluster 2>/dev/null || true

# Update existing service or create new one
echo "Updating ECS service..."
aws ecs update-service \
  --cluster riches-reach-ai-production-cluster \
  --service riches-reach-ai-ai \
  --task-definition richesreach-signals \
  --force-new-deployment \
  --region $AWS_REGION

echo "✅ Deployment completed!"
echo "🎉 Your signals API is now deployed to AWS ECS Fargate!"
echo ""
echo "Next steps:"
echo "1. Monitor the deployment in AWS ECS console"
echo "2. Wait for the service to become healthy"
echo "3. Test the health endpoint: http://<public-ip>:8001/healthz"
echo "4. Test the signals API: http://<public-ip>:8001/graphql/"

# Clean up
rm -f task-def.json

echo ""
echo "Image URI: $IMG"
echo "Task Definition: richesreach-signals"
echo "Cluster: riches-reach-ai-production-cluster"
echo "Service: riches-reach-ai-ai"
