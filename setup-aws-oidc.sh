#!/bin/bash
# One-time AWS setup for GitHub OIDC CI/CD
# This script is idempotent - safe to run multiple times

set -e

echo "🚀 Setting up AWS resources for GitHub OIDC CI/CD..."

# Set region
export AWS_REGION=us-east-1
echo "📍 Using AWS region: $AWS_REGION"

# 1) Create OIDC provider (skip if exists)
echo "🔐 Creating GitHub OIDC provider..."
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 || echo "✅ OIDC provider already exists"

# 2) Create IAM role (create or ensure trust policy)
echo "👤 Creating IAM role for GitHub Actions..."
if aws iam get-role --role-name riches-reach-github-actions >/dev/null 2>&1; then
  echo "✅ Role exists, updating trust policy..."
  aws iam update-assume-role-policy \
    --role-name riches-reach-github-actions \
    --policy-document file://trust-policy.json
else
  echo "✅ Creating new role..."
  aws iam create-role \
    --role-name riches-reach-github-actions \
    --assume-role-policy-document file://trust-policy.json
fi

# 3) Attach inline policy
echo "📋 Attaching permissions policy..."
aws iam put-role-policy \
  --role-name riches-reach-github-actions \
  --policy-name RichesReachGitHubActionsPolicy \
  --policy-document file://permissions-policy.json

# 4) Create ECR repository
echo "🐳 Creating ECR repository..."
aws ecr describe-repositories --repository-names riches-reach-ai >/dev/null 2>&1 \
  || aws ecs create-repository --repository-name riches-reach-ai || echo "✅ ECR repository already exists"

# 5) Create ECS clusters
echo "🏗️ Creating ECS clusters..."
aws ecs create-cluster --cluster-name riches-reach-staging >/dev/null 2>&1 || echo "✅ Staging cluster already exists"
aws ecs create-cluster --cluster-name riches-reach-prod >/dev/null 2>&1 || echo "✅ Production cluster already exists"

echo ""
echo "🎉 AWS setup complete!"
echo ""
echo "📋 Summary:"
echo "  ✅ GitHub OIDC provider configured"
echo "  ✅ IAM role: riches-reach-github-actions"
echo "  ✅ ECR repository: riches-reach-ai"
echo "  ✅ ECS clusters: riches-reach-staging, riches-reach-prod"
echo ""
echo "🧪 Next steps:"
echo "  1. Push changes: git push origin main"
echo "  2. Test workflow: GitHub Actions → RichesReach CI/CD (OIDC) → Run workflow"
echo "  3. Select 'develop' branch for staging test"
echo ""
echo "🔍 To verify setup:"
echo "  aws iam get-role --role-name riches-reach-github-actions"
echo "  aws ecr describe-repositories --repository-names riches-reach-ai"
echo "  aws ecs describe-clusters --clusters riches-reach-staging riches-reach-prod"
