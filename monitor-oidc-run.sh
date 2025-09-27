#!/bin/bash
# Live OIDC Run Monitoring & Recovery Kit
# Use this to watch, verify, and recover from the GitHub Actions OIDC pipeline

set -e

echo "🔍 OIDC Pipeline Live Monitor & Recovery Kit"
echo "=============================================="
echo ""

# Quick status snapshot (anytime)
echo "1. 📊 QUICK STATUS SNAPSHOT"
echo "---------------------------"
echo "Who am I? (confirms OIDC role):"
aws sts get-caller-identity --query 'Arn' --output text
echo ""

echo "Latest Actions run URL:"
gh run list --limit 1 --json databaseId,headBranch,conclusion,htmlUrl | jq -r '.[0].htmlUrl' || echo "GitHub CLI not available"
echo ""

# Build & Push verification
echo "2. 🐳 BUILD & PUSH VERIFICATION"
echo "-------------------------------"
echo "Latest image tags (expect: SHA, develop, latest):"
aws ecr describe-images --repository-name riches-reach-ai \
  --query 'reverse(sort_by(imageDetails,& imagePushedAt))[0].imageTags' --output json 2>/dev/null || echo "No images yet - build in progress"
echo ""

echo "5 most recent images:"
aws ecr describe-images --repository-name riches-reach-ai \
  --query 'reverse(sort_by(imageDetails,& imagePushedAt))[0:5].[imageTags, imagePushedAt]' --output table 2>/dev/null || echo "No images yet - build in progress"
echo ""

# Deploy to Staging verification
echo "3. 🚀 DEPLOY TO STAGING VERIFICATION"
echo "------------------------------------"
echo "Service events (top 12 newest first):"
aws ecs describe-services --cluster riches-reach-staging --services riches-reach-staging-svc \
  --query 'services[0].events[0:12].[createdAt,message]' --output table 2>/dev/null || echo "Service not found yet - deploy in progress"
echo ""

echo "Active deployments & counts:"
aws ecs describe-services --cluster riches-reach-staging --services riches-reach-staging-svc \
  --query 'services[0].deployments[*].[status,taskDefinition,desiredCount,runningCount,updatedAt]' --output table 2>/dev/null || echo "Service not found yet - deploy in progress"
echo ""

echo "Current task definition image:"
TD=$(aws ecs describe-services --cluster riches-reach-staging --services riches-reach-staging-svc \
  --query 'services[0].taskDefinition' --output text 2>/dev/null || echo "")
if [ -n "$TD" ]; then
  aws ecs describe-task-definition --task-definition "$TD" \
    --query 'taskDefinition.containerDefinitions[?name==`riches-reach-ai`].image' --output text
else
  echo "Service not found yet - deploy in progress"
fi
echo ""

# Target health & tasks
echo "4. 🎯 TARGET HEALTH & TASKS"
echo "---------------------------"
echo "Currently running tasks:"
aws ecs list-tasks --cluster riches-reach-staging --service-name riches-reach-staging-svc \
  --desired-status RUNNING --query 'taskArns' --output table 2>/dev/null || echo "No running tasks yet"
echo ""

echo "Stopped tasks (if any):"
STOPPED_TASKS=$(aws ecs list-tasks --cluster riches-reach-staging --service-name riches-reach-staging-svc \
  --desired-status STOPPED --query 'taskArns' --output text 2>/dev/null || echo "")
if [ -n "$STOPPED_TASKS" ]; then
  echo "$STOPPED_TASKS" | xargs -I{} \
    aws ecs describe-tasks --cluster riches-reach-staging --tasks {} \
    --query 'tasks[].{stoppedReason:stoppedReason,exit:containers[0].exitCode,reason:containers[0].reason}' --output table
else
  echo "No stopped tasks"
fi
echo ""

# Logs
echo "5. 📝 LOGS (CloudWatch)"
echo "-----------------------"
echo "Available log groups:"
aws logs describe-log-groups --log-group-name-prefix "/ecs/riches-reach" --query 'logGroups[].logGroupName' --output table 2>/dev/null || echo "No log groups found yet"
echo ""

echo "To tail logs (run manually):"
echo "aws logs tail '/ecs/riches-reach-ai' --follow --since 15m"
echo ""

# Fast fixes
echo "6. 🔧 FAST FIXES"
echo "----------------"
echo "Re-deploy current task definition:"
echo "aws ecs update-service --cluster riches-reach-staging --service riches-reach-staging-svc --force-new-deployment"
echo ""
echo "Roll back to previous task definition:"
echo "aws ecs update-service --cluster riches-reach-staging --service riches-reach-staging-svc --task-definition <PREVIOUS_TASK_DEF_ARN> --force-new-deployment"
echo ""

# Production monitoring
echo "7. 🏭 PRODUCTION MONITORING (after merge to main)"
echo "------------------------------------------------"
echo "Production deployment status:"
aws ecs describe-services --cluster riches-reach-prod --services riches-reach-prod-svc \
  --query 'services[0].deployments[*].[status,taskDefinition,desiredCount,runningCount,updatedAt]' --output table 2>/dev/null || echo "Production service not found yet"
echo ""

echo "🎯 MONITORING COMPLETE!"
echo ""
echo "💡 TIPS:"
echo "- Run this script multiple times to watch progress"
echo "- If anything turns red, paste the error line for instant help"
echo "- Green on develop? Merge to main for production deploy!"
echo ""
echo "🚀 Ready for boring-green ✅"
