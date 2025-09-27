#!/bin/bash
# Verify AWS setup for GitHub OIDC CI/CD

echo "🔍 Verifying AWS setup for GitHub OIDC CI/CD..."
echo ""

# Check IAM role
echo "1. Checking IAM role..."
if aws iam get-role --role-name riches-reach-github-actions >/dev/null 2>&1; then
  echo "✅ riches-reach-github-actions role exists"
  aws iam get-role --role-name riches-reach-github-actions --query 'Role.Arn' --output text
else
  echo "❌ riches-reach-github-actions role missing"
fi

# Check OIDC provider
echo ""
echo "2. Checking OIDC provider..."
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "arn:aws:iam::498606688292:oidc-provider/token.actions.githubusercontent.com" >/dev/null 2>&1; then
  echo "✅ GitHub OIDC provider exists"
else
  echo "❌ GitHub OIDC provider missing"
fi

# Check ECR repository
echo ""
echo "3. Checking ECR repository..."
if aws ecr describe-repositories --repository-names riches-reach-ai >/dev/null 2>&1; then
  echo "✅ riches-reach-ai ECR repository exists"
  aws ecr describe-repositories --repository-names riches-reach-ai --query 'repositories[0].repositoryUri' --output text
else
  echo "❌ riches-reach-ai ECR repository missing"
fi

# Check ECS clusters
echo ""
echo "4. Checking ECS clusters..."
STAGING_STATUS=$(aws ecs describe-clusters --clusters riches-reach-staging --query 'clusters[0].status' --output text 2>/dev/null || echo "MISSING")
PROD_STATUS=$(aws ecs describe-clusters --clusters riches-reach-prod --query 'clusters[0].status' --output text 2>/dev/null || echo "MISSING")

if [ "$STAGING_STATUS" = "ACTIVE" ]; then
  echo "✅ riches-reach-staging cluster exists (ACTIVE)"
else
  echo "❌ riches-reach-staging cluster missing or inactive"
fi

if [ "$PROD_STATUS" = "ACTIVE" ]; then
  echo "✅ riches-reach-prod cluster exists (ACTIVE)"
else
  echo "❌ riches-reach-prod cluster missing or inactive"
fi

# Check ECS services (optional - may not exist yet)
echo ""
echo "5. Checking ECS services (optional)..."
STAGING_SERVICE=$(aws ecs describe-services --cluster riches-reach-staging --services riches-reach-staging-svc --query 'services[0].status' --output text 2>/dev/null || echo "MISSING")
PROD_SERVICE=$(aws ecs describe-services --cluster riches-reach-prod --services riches-reach-prod-svc --query 'services[0].status' --output text 2>/dev/null || echo "MISSING")

if [ "$STAGING_SERVICE" = "ACTIVE" ]; then
  echo "✅ riches-reach-staging-svc service exists (ACTIVE)"
else
  echo "⚠️  riches-reach-staging-svc service missing (will be created on first deploy)"
fi

if [ "$PROD_SERVICE" = "ACTIVE" ]; then
  echo "✅ riches-reach-prod-svc service exists (ACTIVE)"
else
  echo "⚠️  riches-reach-prod-svc service missing (will be created on first deploy)"
fi

echo ""
echo "🎯 Ready to test workflow if all checks pass!"
