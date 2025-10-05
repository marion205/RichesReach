#!/bin/bash

# Deploy Secure Secrets Management Infrastructure
# This script sets up enterprise-grade secret management for RichesReach

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Configuration
PROJECT="richesreach"
ENVIRONMENT="${1:-production}"
AWS_REGION="us-east-1"

log_info "🔐 Deploying Secure Secrets Management for RichesReach"
log_info "Environment: $ENVIRONMENT"
log_info "Region: $AWS_REGION"

# Check prerequisites
log_step "Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    log_error "Terraform is not installed. Please install Terraform first."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed. Please install AWS CLI first."
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

log_info "✅ Prerequisites check passed"

# Create build directory
log_step "Creating build directory..."
mkdir -p infrastructure/secrets/.build
log_info "✅ Build directory created"

# Deploy Terraform infrastructure
log_step "Deploying Terraform infrastructure..."

cd infrastructure/secrets

# Initialize Terraform
log_info "Initializing Terraform..."
terraform init

# Plan deployment
log_info "Planning deployment..."
terraform plan \
    -var "project=$PROJECT" \
    -var "env=$ENVIRONMENT" \
    -out=tfplan

# Apply deployment
log_info "Applying Terraform configuration..."
terraform apply tfplan

log_info "✅ Terraform infrastructure deployed"

# Get outputs
log_step "Retrieving deployment outputs..."
KMS_KEY_ARN=$(terraform output -raw kms_key_arn)
ROTATION_LAMBDA_ARN=$(terraform output -raw rotation_lambda_arn)
APP_POLICY_ARN=$(terraform output -raw app_read_secrets_policy_arn)
CI_POLICY_ARN=$(terraform output -raw ci_rotate_secrets_policy_arn)

log_info "KMS Key ARN: $KMS_KEY_ARN"
log_info "Rotation Lambda ARN: $ROTATION_LAMBDA_ARN"
log_info "App Policy ARN: $APP_POLICY_ARN"
log_info "CI Policy ARN: $CI_POLICY_ARN"

# Deploy Lambda functions
log_step "Deploying Lambda functions..."

# Create Lambda deployment package
cd ../../infrastructure/lambdas/rotate_generic
zip -r handler.zip handler.py

# Update Lambda function code
log_info "Updating rotation Lambda function..."
aws lambda update-function-code \
    --function-name "$PROJECT-$ENVIRONMENT-rotate-generic" \
    --zip-file fileb://handler.zip \
    --region "$AWS_REGION"

log_info "✅ Lambda functions deployed"

# Create ECS task definition template
log_step "Creating ECS task definition template..."

cd ../../..

cat > ecs-task-definition-with-secrets.json << EOF
{
  "family": "richesreach-backend",
  "taskRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/richesreach-ecs-task-role",
  "executionRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/richesreach-ecs-execution-role",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/richesreach-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:$PROJECT/$ENVIRONMENT/openai_api_key"
        },
        {
          "name": "POLYGON_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:$PROJECT/$ENVIRONMENT/polygon_api_key"
        },
        {
          "name": "FINNHUB_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:$PROJECT/$ENVIRONMENT/finnhub_api_key"
        },
        {
          "name": "ALPHA_VANTAGE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:$PROJECT/$ENVIRONMENT/alpha_vantage_key"
        },
        {
          "name": "ALCHEMY_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:$PROJECT/$ENVIRONMENT/alchemy_key"
        },
        {
          "name": "WALLETCONNECT_PROJECT_ID",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:$PROJECT/$ENVIRONMENT/walletconnect_id"
        },
        {
          "name": "NEWS_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:$PROJECT/$ENVIRONMENT/newsapi_key"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "$ENVIRONMENT"
        },
        {
          "name": "AWS_REGION",
          "value": "$AWS_REGION"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/richesreach-backend",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "essential": true
    }
  ]
}
EOF

log_info "✅ ECS task definition template created: ecs-task-definition-with-secrets.json"

# Create rotation script
log_step "Creating rotation script..."

cat > rotate_secret.sh << 'EOF'
#!/bin/bash

# Rotate a specific secret
# Usage: ./rotate_secret.sh <secret_name> <new_value> [environment]

set -e

SECRET_NAME="$1"
NEW_VALUE="$2"
ENVIRONMENT="${3:-production}"
PROJECT="richesreach"
AWS_REGION="us-east-1"

if [ -z "$SECRET_NAME" ] || [ -z "$NEW_VALUE" ]; then
    echo "Usage: $0 <secret_name> <new_value> [environment]"
    echo "Example: $0 polygon_api_key 'new_key_here' production"
    exit 1
fi

echo "🔄 Rotating secret: $SECRET_NAME"
echo "Environment: $ENVIRONMENT"

# Get secret ARN
SECRET_ARN=$(aws secretsmanager list-secrets \
    --filters Key=name,Values="$PROJECT/$ENVIRONMENT/$SECRET_NAME" \
    --query 'SecretList[0].ARN' --output text)

if [ "$SECRET_ARN" = "None" ] || [ -z "$SECRET_ARN" ]; then
    echo "❌ Secret not found: $PROJECT/$ENVIRONMENT/$SECRET_NAME"
    exit 1
fi

echo "Secret ARN: $SECRET_ARN"

# Invoke rotation Lambda
echo "🔄 Invoking rotation Lambda..."
aws lambda invoke \
    --function-name "$PROJECT-$ENVIRONMENT-rotate-generic" \
    --payload "{
        \"SecretId\": \"$SECRET_ARN\",
        \"CandidateValue\": \"$NEW_VALUE\",
        \"Action\": \"rotate\"
    }" \
    /tmp/rotation_result.json

# Check result
if jq -e '.statusCode == 200' /tmp/rotation_result.json > /dev/null; then
    echo "✅ Secret rotation successful"
    cat /tmp/rotation_result.json
else
    echo "❌ Secret rotation failed"
    cat /tmp/rotation_result.json
    exit 1
fi

# Clean up
rm -f /tmp/rotation_result.json

echo "🎉 Secret rotation completed successfully!"
EOF

chmod +x rotate_secret.sh

log_info "✅ Rotation script created: rotate_secret.sh"

# Create verification script
log_step "Creating verification script..."

cat > verify_secrets.sh << 'EOF'
#!/bin/bash

# Verify secrets infrastructure
# Usage: ./verify_secrets.sh [environment]

set -e

ENVIRONMENT="${1:-production}"
PROJECT="richesreach"
AWS_REGION="us-east-1"

echo "🔍 Verifying secrets infrastructure for $ENVIRONMENT"

# Check if secrets exist
echo "📋 Checking secrets..."
aws secretsmanager list-secrets \
    --filters Key=name,Values="$PROJECT/$ENVIRONMENT/" \
    --query 'SecretList[].Name' --output table

# Check Lambda function
echo "🔧 Checking rotation Lambda..."
aws lambda get-function \
    --function-name "$PROJECT-$ENVIRONMENT-rotate-generic" \
    --query 'Configuration.{FunctionName:FunctionName,Runtime:Runtime,State:State}' \
    --output table

# Check KMS key
echo "🔐 Checking KMS key..."
aws kms describe-key \
    --key-id "alias/$PROJECT-$ENVIRONMENT-secrets" \
    --query 'KeyMetadata.{KeyId:KeyId,Description:Description,KeyState:KeyState}' \
    --output table

echo "✅ Verification completed"
EOF

chmod +x verify_secrets.sh

log_info "✅ Verification script created: verify_secrets.sh"

# Final instructions
log_step "🎉 Deployment completed successfully!"

echo ""
log_info "📋 NEXT STEPS:"
echo ""
echo "1. 🔑 Rotate your API keys:"
echo "   ./rotate_secret.sh polygon_api_key 'YOUR_NEW_POLYGON_KEY' $ENVIRONMENT"
echo "   ./rotate_secret.sh finnhub_api_key 'YOUR_NEW_FINNHUB_KEY' $ENVIRONMENT"
echo "   ./rotate_secret.sh openai_api_key 'YOUR_NEW_OPENAI_KEY' $ENVIRONMENT"
echo ""
echo "2. 🐳 Update your ECS task definition:"
echo "   Use the generated 'ecs-task-definition-with-secrets.json'"
echo ""
echo "3. 🔍 Verify deployment:"
echo "   ./verify_secrets.sh $ENVIRONMENT"
echo ""
echo "4. 🚀 Deploy your application with the new task definition"
echo ""
echo "📚 Documentation:"
echo "   - SECURE_SECRETS_ROTATION_TEMPLATE.md"
echo "   - .github/workflows/rotate-secrets.yml (for CI/CD rotation)"
echo ""

log_info "🔐 Your RichesReach platform now has enterprise-grade secret management!"
