#!/bin/bash
# Quick Backend Deployment to AWS ECS
# Triggers a new deployment without waiting

set -e

AWS_REGION="us-east-1"
CLUSTER_NAME="richesreach-cluster"
SERVICE_NAME="richesreach-service"

echo "🚀 Deploying RichesReach Backend to AWS ECS"
echo "============================================"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
  echo "❌ AWS credentials not configured"
  exit 1
fi

echo "✅ AWS credentials verified"
echo ""

# Check service status
echo "📊 Current service status:"
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $AWS_REGION \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,TaskDef:taskDefinition}' \
  --output table

echo ""

# Trigger new deployment
echo "🔄 Triggering new deployment..."
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region $AWS_REGION \
  --output json > /dev/null

echo "✅ Deployment triggered successfully!"
echo ""
echo "📊 Monitor deployment at:"
echo "   https://${AWS_REGION}.console.aws.amazon.com/ecs/v2/clusters/${CLUSTER_NAME}/services/${SERVICE_NAME}"
echo ""
echo "💡 To check deployment status:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query 'services[0].deployments'"
echo ""





