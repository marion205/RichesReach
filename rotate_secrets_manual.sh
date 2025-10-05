#!/bin/bash

# Manual Secret Rotation Script
# This script rotates secrets directly in AWS Secrets Manager

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
ENVIRONMENT="production"
AWS_REGION="us-east-1"

log_info "🔐 Manual Secret Rotation for RichesReach"
log_info "Environment: $ENVIRONMENT"
log_info "Region: $AWS_REGION"

# Function to rotate a secret
rotate_secret() {
    local secret_name="$1"
    local new_value="$2"
    
    if [ -z "$secret_name" ] || [ -z "$new_value" ]; then
        log_error "Usage: rotate_secret <secret_name> <new_value>"
        return 1
    fi
    
    local secret_id="$PROJECT/$ENVIRONMENT/$secret_name"
    
    log_step "Rotating secret: $secret_name"
    
    # Create the secret value with metadata
    local secret_data=$(cat << EOF
{
    "value": "$new_value",
    "metadata": {
        "source": "manual_rotation",
        "rotated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "rotated_by": "$(whoami)"
    }
}
EOF
)
    
    # Update the secret
    aws secretsmanager put-secret-value \
        --secret-id "$secret_id" \
        --secret-string "$secret_data" \
        --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        log_info "✅ Successfully rotated secret: $secret_name"
    else
        log_error "❌ Failed to rotate secret: $secret_name"
        return 1
    fi
}

# Function to verify a secret
verify_secret() {
    local secret_name="$1"
    local secret_id="$PROJECT/$ENVIRONMENT/$secret_name"
    
    log_step "Verifying secret: $secret_name"
    
    local secret_value=$(aws secretsmanager get-secret-value \
        --secret-id "$secret_id" \
        --region "$AWS_REGION" \
        --query 'SecretString' \
        --output text 2>/dev/null)
    
    if [ $? -eq 0 ] && [ "$secret_value" != "null" ]; then
        log_info "✅ Secret verified: $secret_name"
        return 0
    else
        log_error "❌ Secret verification failed: $secret_name"
        return 1
    fi
}

# Main rotation logic
if [ $# -eq 0 ]; then
    echo "Usage: $0 <secret_name> <new_value>"
    echo ""
    echo "Available secrets:"
    aws secretsmanager list-secrets \
        --filters Key=name,Values="$PROJECT/$ENVIRONMENT/" \
        --query 'SecretList[].Name' \
        --output table
    exit 1
fi

SECRET_NAME="$1"
NEW_VALUE="$2"

if [ -z "$NEW_VALUE" ]; then
    log_error "Please provide a new value for the secret"
    exit 1
fi

# Rotate the secret
rotate_secret "$SECRET_NAME" "$NEW_VALUE"

# Verify the rotation
verify_secret "$SECRET_NAME"

log_info "🎉 Secret rotation completed successfully!"
