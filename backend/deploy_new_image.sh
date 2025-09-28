#!/bin/bash
set -euo pipefail

# ====== CONFIG ======
AWS_REGION=us-east-1
ACCOUNT_ID=498606688292
ECR_REPO=riches-reach-ai
CLUSTER=riches-reach-ai-production-cluster
SERVICE=riches-reach-ai-ai
TASK_FAMILY=riches-reach-ai-task
CONTAINER_NAME=riches-reach-ai
SUBNET_ID=subnet-037cb59936a709c87
SG_ID=sg-007dff041138724c3

# Generate unique tag
IMAGE_TAG="prod-$(date +%Y%m%d%H%M%S)"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO"

echo "🚀 DEPLOYMENT SCRIPT STARTING"
echo "Image: $ECR_URI:$IMAGE_TAG"
echo "=================================="

# ====== 0) SANITY CHECKS ======
echo "📋 Step 0: Sanity Checks"
aws sts get-caller-identity --query 'Account' --output text
echo "✅ AWS Identity verified"

aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$AWS_REGION" --query 'repositories[0].repositoryName' --output text >/dev/null
echo "✅ ECR Repository exists"

# ====== 1) ECR LOGIN ======
echo ""
echo "🔐 Step 1: ECR Login"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
echo "✅ ECR Login successful"

# ====== 2) BUILDX SETUP ======
echo ""
echo "🔧 Step 2: BuildX Setup"
if ! docker buildx ls | grep -q "docker-container.*running"; then
    echo "Creating new buildx builder..."
    docker buildx create --name rr-builder --use --bootstrap
else
    echo "✅ BuildX builder ready"
fi

# ====== 3) BUILD & PUSH ======
echo ""
echo "🏗️  Step 3: Building Multi-Arch Image"
echo "This may take 5-10 minutes..."
echo "Platforms: linux/amd64,linux/arm64"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "$ECR_URI:$IMAGE_TAG" \
  --push \
  --provenance=false \
  --sbom=false \
  --progress=plain \
  .

echo "✅ Image built and pushed"

# ====== 4) VERIFY IMAGE ======
echo ""
echo "🔍 Step 4: Verifying Image in ECR"
aws ecr describe-images \
  --repository-name "$ECR_REPO" \
  --image-ids imageTag="$IMAGE_TAG" \
  --region "$AWS_REGION" \
  --query 'imageDetails[0].imageDigest' --output text
echo "✅ Image verified in ECR"

# ====== 5) TEST TASK ======
echo ""
echo "🧪 Step 5: Testing New Image (One-off Task)"
echo "Creating test task definition..."

# Export current good task def and modify image
aws ecs describe-task-definition \
  --task-definition riches-reach-ai-task:100 \
  --region "$AWS_REGION" \
  --query 'taskDefinition' > /tmp/td-test.json

# Update image in task definition
python3 -c "
import json
with open('/tmp/td-test.json', 'r') as f:
    td = json.load(f)
for k in ['taskDefinitionArn','revision','status','requiresAttributes','compatibilities','registeredAt','registeredBy']:
    td.pop(k, None)
for c in td['containerDefinitions']:
    if c['name'] == '$CONTAINER_NAME':
        c['image'] = '$ECR_URI:$IMAGE_TAG'
        break
with open('/tmp/td-test.json', 'w') as f:
    json.dump(td, f)
"

# Register test task definition
TEST_TD_ARN=$(aws ecs register-task-definition --cli-input-json file:///tmp/td-test.json --region "$AWS_REGION" --query 'taskDefinition.taskDefinitionArn' --output text)
echo "Test TD: $TEST_TD_ARN"

# Run test task
echo "Starting test task..."
TEST_TASK_ARN=$(aws ecs run-task \
  --cluster "$CLUSTER" \
  --launch-type FARGATE \
  --count 1 \
  --task-definition "$TEST_TD_ARN" \
  --network-configuration "awsvpcConfiguration={subnets=[\"$SUBNET_ID\"],securityGroups=[\"$SG_ID\"],assignPublicIp=ENABLED}" \
  --region "$AWS_REGION" \
  --query 'tasks[0].taskArn' --output text)

echo "Test task started: $TEST_TASK_ARN"
echo "⏳ Waiting for test task to start..."

# Wait for task to start
aws ecs wait tasks-running --cluster "$CLUSTER" --tasks "$TEST_TASK_ARN" --region "$AWS_REGION"
echo "✅ Test task is running"

# ====== 6) CHECK TEST LOGS ======
echo ""
echo "📊 Step 6: Checking Test Task Logs"
TASK_ID=$(basename "$TEST_TASK_ARN")
LOG_STREAM="ecs/riches-reach-ai/$TASK_ID"

echo "Log stream: $LOG_STREAM"
echo "Recent logs:"
aws logs get-log-events \
  --log-group-name /ecs/riches-reach-ai \
  --log-stream-name "$LOG_STREAM" \
  --region "$AWS_REGION" \
  --start-time $(($(date +%s) - 300))000 \
  --query 'events[-10:].[timestamp,message]' \
  --output table

echo ""
echo "🎉 DEPLOYMENT SCRIPT COMPLETED"
echo "=================================="
echo "✅ New image: $ECR_URI:$IMAGE_TAG"
echo "✅ Test task: $TEST_TASK_ARN"
echo ""
echo "Next steps:"
echo "1. Check the logs above for any errors"
echo "2. If test looks good, update the service:"
echo "   aws ecs update-service --cluster $CLUSTER --service $SERVICE --task-definition $TEST_TD_ARN --force-new-deployment --region $AWS_REGION"
echo ""
echo "To rollback if needed:"
echo "   aws ecs update-service --cluster $CLUSTER --service $SERVICE --task-definition riches-reach-ai-task:100 --force-new-deployment --region $AWS_REGION"
