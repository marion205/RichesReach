#!/bin/bash
# Quick status check for OIDC run

echo "🔍 Quick OIDC Status Check"
echo "=========================="

# Check ECR images
echo "📦 ECR Images:"
aws ecr describe-images --repository-name riches-reach-ai \
  --query 'reverse(sort_by(imageDetails,& imagePushedAt))[0].imageTags' --output json 2>/dev/null || echo "No images yet - build in progress"

# Check ECS service
echo ""
echo "🚀 ECS Service:"
aws ecs describe-services --cluster riches-reach-staging --services riches-reach-staging-svc \
  --query 'services[0].events[0:3].[createdAt,message]' --output table 2>/dev/null || echo "Service not found yet - deploy in progress"

# Check running tasks
echo ""
echo "🎯 Running Tasks:"
aws ecs list-tasks --cluster riches-reach-staging --service-name riches-reach-staging-svc \
  --desired-status RUNNING --query 'taskArns' --output table 2>/dev/null || echo "No running tasks yet"

echo ""
echo "💡 Run './monitor-oidc-run.sh' for full details"
