#!/bin/bash
# Hot-swap ECS service to use the newest ECR image
# Run this after OIDC pipeline produces images

set -e

echo "🚀 Hot-swapping ECS service to newest image..."

# Vars
ACCOUNT_ID=498606688292
REGION=us-east-1
CLUSTER=riches-reach-staging
SERVICE=riches-reach-staging-svc
CONTAINER=riches-reach-ai

echo "Step 1: Getting the newest image tag..."
LATEST_TAG=$(aws ecr describe-images --repository-name riches-reach-ai \
  --query 'reverse(sort_by(imageDetails,& imagePushedAt))[0].imageTags[0]' --output text)
IMAGE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/riches-reach-ai:${LATEST_TAG}"

echo "✅ Newest image: $IMAGE"

echo ""
echo "Step 2: Getting current task definition..."
TD_ARN=$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].taskDefinition' --output text)
aws ecs describe-task-definition --task-definition "$TD_ARN" --query 'taskDefinition' >/tmp/td.json

echo "✅ Current task definition: $TD_ARN"

echo ""
echo "Step 3: Creating new task definition with updated image..."
jq --arg IMG "$IMAGE" '
  .containerDefinitions |= map(if .name == "'$CONTAINER'" then .image=$IMG else . end)
  | del(.taskDefinitionArn,.revision,.status,.requiresAttributes,.compatibilities,.registeredAt,.registeredBy)
' /tmp/td.json >/tmp/td-new.json

echo "✅ New task definition created with image: $IMAGE"

echo ""
echo "Step 4: Registering new task definition..."
NEW_TD=$(aws ecs register-task-definition --cli-input-json file:///tmp/td-new.json \
  --query 'taskDefinition.taskDefinitionArn' --output text)

echo "✅ New task definition registered: $NEW_TD"

echo ""
echo "Step 5: Updating service with new task definition..."
aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" \
  --task-definition "$NEW_TD" --force-new-deployment

echo "✅ Service updated! Deployment in progress..."

echo ""
echo "Step 6: Verifying the rollout..."
echo "New task definition image:"
TD=$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].taskDefinition' --output text)
aws ecs describe-task-definition --task-definition "$TD" \
  --query 'taskDefinition.containerDefinitions[?name==`'$CONTAINER'`].image' --output text

echo ""
echo "Service events (latest 5):"
aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].events[0:5].[createdAt,message]' --output table

echo ""
echo "Running tasks:"
aws ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" \
  --desired-status RUNNING --output table

echo ""
echo "🎉 Hot-swap complete! Monitor the service events above for deployment progress."
echo ""
echo "💡 If tasks fail, check stopped tasks:"
echo "aws ecs list-tasks --cluster $CLUSTER --service-name $SERVICE --desired-status STOPPED --query 'taskArns' --output text | xargs -I{} aws ecs describe-tasks --cluster $CLUSTER --tasks {} --query 'tasks[].{stoppedReason:stoppedReason,exit:containers[0].exitCode,reason:containers[0].reason}' --output table"
