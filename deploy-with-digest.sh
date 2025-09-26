#!/bin/bash

# Deploy using image digest for immutable deployments
# Usage: ./deploy-with-digest.sh [IMAGE_TAG]
# If no tag provided, uses 'latest-prod'

IMAGE_TAG=${1:-latest-prod}
REPO="498606688292.dkr.ecr.us-east-1.amazonaws.com/riches-reach-ai-ai-service"

echo "🔍 Looking for image: $REPO:$IMAGE_TAG"

# Get image digest for immutable deployment
DIGEST=$(aws ecr describe-images \
  --repository-name riches-reach-ai-ai-service \
  --image-ids imageTag=$IMAGE_TAG \
  --region us-east-1 \
  --query 'imageDetails[0].imageDigest' --output text 2>/dev/null)

if [ "$DIGEST" = "None" ] || [ -z "$DIGEST" ]; then
  echo "❌ Image $REPO:$IMAGE_TAG not found in ECR"
  echo "Available images:"
  aws ecr describe-images --repository-name riches-reach-ai-ai-service --region us-east-1 --query 'imageDetails[].imageTags' --output table
  exit 1
fi

NEW_IMAGE="$REPO@$DIGEST"
echo "✅ Found image: $NEW_IMAGE"

# Export current task def to a file
echo "📋 Exporting current task definition..."
aws ecs describe-task-definition \
  --task-definition riches-reach-ai-task \
  --region us-east-1 \
  --query 'taskDefinition' > td.json

# Strip read-only fields and update just the image
echo "🔧 Updating task definition with new image..."
jq 'del(.taskDefinitionArn,.revision,.status,.compatibilities,.requiresAttributes,.registeredAt,.registeredBy)
    | .containerDefinitions[0].image="'"$NEW_IMAGE"'"' td.json > td-patched.json

# Register new revision
echo "📝 Registering new task definition..."
REVISION=$(aws ecs register-task-definition \
  --cli-input-json file://td-patched.json \
  --region us-east-1 \
  --query 'taskDefinition.revision' --output text)

echo "✅ New task definition: riches-reach-ai-task:$REVISION"

# Update the service
echo "🚀 Updating ECS service..."
aws ecs update-service \
  --cluster riches-reach-ai-production-cluster \
  --service riches-reach-ai-ai \
  --task-definition riches-reach-ai-task:$REVISION \
  --region us-east-1

echo "✅ ECS service update initiated!"
echo "📊 Monitor deployment with:"
echo "aws ecs describe-services --cluster riches-reach-ai-production-cluster --services riches-reach-ai-ai --region us-east-1"

# Clean up temporary files
rm -f td.json td-patched.json github-trust-policy-fixed.json

echo ""
echo "🎯 Next steps:"
echo "1. Wait for deployment to complete (~2-3 minutes)"
echo "2. Run: ./verify-deployment.sh"
echo "3. If migrations are needed: ./run-migration-fix.sh $REVISION"
