#!/bin/bash

# Verify Secrets Deployment
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

PROJECT="richesreach"
ENVIRONMENT="production"
AWS_REGION="us-east-1"

log_info "🔍 Verifying Secrets Deployment for RichesReach"

# Check if secrets exist
log_step "Checking secrets..."
SECRETS=(
    "finnhub_api_key"
    "polygon_api_key"
    "alpha_vantage_key"
    "openai_api_key"
    "alchemy_key"
    "walletconnect_id"
    "newsapi_key"
)

for secret in "${SECRETS[@]}"; do
    if aws secretsmanager describe-secret --secret-id "$PROJECT/$ENVIRONMENT/$secret" --region "$AWS_REGION" > /dev/null 2>&1; then
        log_info "✅ Secret exists: $secret"
    else
        log_error "❌ Secret missing: $secret"
    fi
done

# Check KMS key
log_step "Checking KMS key..."
if aws kms describe-key --key-id "alias/$PROJECT-$ENVIRONMENT-secrets" --region "$AWS_REGION" > /dev/null 2>&1; then
    log_info "✅ KMS key exists: alias/$PROJECT-$ENVIRONMENT-secrets"
else
    log_warn "⚠️ KMS key not found: alias/$PROJECT-$ENVIRONMENT-secrets"
fi

# Check IAM policies
log_step "Checking IAM policies..."
if aws iam get-policy --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$PROJECT-$ENVIRONMENT-app-read-secrets" > /dev/null 2>&1; then
    log_info "✅ App read secrets policy exists"
else
    log_warn "⚠️ App read secrets policy not found"
fi

# Test secret access
log_step "Testing secret access..."
TEST_SECRET=$(aws secretsmanager get-secret-value \
    --secret-id "$PROJECT/$ENVIRONMENT/finnhub_api_key" \
    --region "$AWS_REGION" \
    --query 'SecretString' \
    --output text 2>/dev/null)

if [ $? -eq 0 ] && [ "$TEST_SECRET" != "null" ]; then
    log_info "✅ Secret access test passed"
else
    log_error "❌ Secret access test failed"
fi

log_info "🎉 Verification completed!"
