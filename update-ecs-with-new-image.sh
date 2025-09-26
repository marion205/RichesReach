#!/bin/bash

# Update ECS service with the new production image
# Usage: ./update-ecs-with-new-image.sh [IMAGE_TAG]
# If no tag provided, uses 'latest-prod'

IMAGE_TAG=${1:-latest-prod}
NEW_IMAGE="498606688292.dkr.ecr.us-east-1.amazonaws.com/riches-reach-ai-ai-service:$IMAGE_TAG"

echo "Updating ECS service with image: $NEW_IMAGE"

# Create a temporary task definition with the new image
cat > temp-task-definition.json << 'EOF'
{
  "family": "riches-reach-ai-task",
  "taskRoleArn": "arn:aws:iam::498606688292:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::498606688292:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [{
    "name": "riches-reach-ai",
    "image": "REPLACE_IMAGE_URI",
    "essential": true,
    "portMappings": [{"containerPort": 8000, "hostPort": 8000, "protocol": "tcp"}],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/riches-reach-ai",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "environment": [
      {"name": "DJANGO_SETTINGS_MODULE", "value": "richesreach.settings"},
      {"name": "SECRET_KEY", "value": "django-insecure-production-key-change-in-production"},
      {"name": "DEBUG", "value": "False"},
      {"name": "ALLOWED_HOSTS", "value": "app.richesreach.com,localhost,127.0.0.1,98.81.210.223"},
      {"name": "CSRF_TRUSTED_ORIGINS", "value": "https://app.richesreach.com,http://98.81.210.223:8000"}
    ],
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8000/health/ || exit 1"],
      "interval": 30, "timeout": 5, "retries": 3, "startPeriod": 60
    },
    "command": ["/bin/sh","-c","echo 'Migrating...' && python manage.py migrate --noinput && echo 'Collecting static...' && python manage.py collectstatic --noinput || true && echo 'Starting Gunicorn...' && gunicorn richesreach.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers 3 --timeout 60"]
  }]
}
EOF

# Replace the image URI
sed "s|REPLACE_IMAGE_URI|$NEW_IMAGE|g" temp-task-definition.json > prod-task-definition-updated.json

# Register the new task definition
echo "Registering new task definition..."
TASK_DEF_ARN=$(aws ecs register-task-definition \
  --cli-input-json file://prod-task-definition-updated.json \
  --region us-east-1 \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "New task definition: $TASK_DEF_ARN"

# Extract the revision number
REVISION=$(echo $TASK_DEF_ARN | cut -d: -f7)
echo "Revision: $REVISION"

# Update the service
echo "Updating ECS service..."
aws ecs update-service \
  --cluster riches-reach-ai-production-cluster \
  --service riches-reach-ai-ai \
  --task-definition riches-reach-ai-task:$REVISION \
  --region us-east-1

echo "✅ ECS service update initiated!"
echo "Monitor the deployment in the AWS console or with:"
echo "aws ecs describe-services --cluster riches-reach-ai-production-cluster --services riches-reach-ai-ai --region us-east-1"

# Clean up temporary files
rm -f temp-task-definition.json prod-task-definition-updated.json
