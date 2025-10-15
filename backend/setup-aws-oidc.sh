#!/bin/bash
set -euo pipefail

echo "🔧 Setting up AWS OIDC for GitHub Actions"
echo "========================================"
echo ""

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="498606688292"
ROLE_NAME="github-actions-richesreach-deploy"
REPO_NAME="marion205/RichesReach"

echo "📋 Configuration:"
echo "  AWS Account ID: $AWS_ACCOUNT_ID"
echo "  AWS Region: $AWS_REGION"
echo "  Role Name: $ROLE_NAME"
echo "  Repository: $REPO_NAME"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ jq not found. Please install it first:"
    echo "   brew install jq  # macOS"
    echo "   apt-get install jq  # Ubuntu"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Step 1: Create OIDC provider if it doesn't exist
echo "🔍 Checking OIDC provider..."
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "arn:aws:iam::$AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com" &>/dev/null; then
    echo "✅ OIDC provider already exists"
else
    echo "📝 Creating OIDC provider..."
    aws iam create-open-id-connect-provider \
        --url "https://token.actions.githubusercontent.com" \
        --client-id-list "sts.amazonaws.com" \
        --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1" \
        --tags Key=Purpose,Value=GitHubActions Key=Repository,Value="$REPO_NAME"
    echo "✅ OIDC provider created"
fi
echo ""

# Step 2: Create IAM role
echo "🔍 Checking IAM role..."
if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    echo "✅ IAM role already exists"
    echo "🔄 Updating trust policy..."
    aws iam update-assume-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-document file://aws-iam-trust-policy.json
    echo "✅ Trust policy updated"
else
    echo "📝 Creating IAM role..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://aws-iam-trust-policy.json \
        --description "Role for GitHub Actions to deploy RichesReach AI" \
        --tags Key=Purpose,Value=GitHubActions Key=Repository,Value="$REPO_NAME"
    echo "✅ IAM role created"
fi
echo ""

# Step 3: Attach deployment policy
echo "📝 Attaching deployment policy..."
aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "RichesReachDeployPolicy" \
    --policy-document file://aws-iam-deploy-policy.json
echo "✅ Deployment policy attached"
echo ""

# Step 4: Ensure ECR repository exists
echo "🔍 Checking ECR repository..."
if aws ecr describe-repositories --repository-names "riches-reach-ai" --region "$AWS_REGION" &>/dev/null; then
    echo "✅ ECR repository already exists"
else
    echo "📝 Creating ECR repository..."
    aws ecr create-repository \
        --repository-name "riches-reach-ai" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --tags Key=Purpose,Value=RichesReach Key=Environment,Value=Production
    echo "✅ ECR repository created"
fi
echo ""

# Step 5: Get role ARN
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
echo "🎯 Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Add this secret to your GitHub repository:"
echo "   Repository: https://github.com/$REPO_NAME/settings/secrets/actions"
echo "   Secret Name: AWS_GH_ACTIONS_ROLE_ARN"
echo "   Secret Value: $ROLE_ARN"
echo ""
echo "2. Your GitHub Actions workflow will now use OIDC authentication"
echo "   No long-lived AWS keys needed!"
echo ""
echo "3. Test the deployment by pushing to main branch"
echo ""
echo "🔗 Role ARN: $ROLE_ARN"
