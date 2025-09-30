#!/bin/bash

# Setup AWS IAM Roles for ECS
set -e

echo "🔧 Setting up AWS IAM Roles for ECS"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

AWS_ACCOUNT_ID="498606688292"
AWS_REGION="us-east-1"

# Create ECS Task Execution Role
log_info "Creating ECS Task Execution Role..."
cat > ecs-task-execution-role-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role if it doesn't exist
if ! aws iam get-role --role-name ecsTaskExecutionRole > /dev/null 2>&1; then
    aws iam create-role \
        --role-name ecsTaskExecutionRole \
        --assume-role-policy-document file://ecs-task-execution-role-trust-policy.json
    
    aws iam attach-role-policy \
        --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    
    log_info "✅ ECS Task Execution Role created"
else
    log_info "✅ ECS Task Execution Role already exists"
fi

# Create ECS Task Role
log_info "Creating ECS Task Role..."
cat > ecs-task-role-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

if ! aws iam get-role --role-name ecsTaskRole > /dev/null 2>&1; then
    aws iam create-role \
        --role-name ecsTaskRole \
        --assume-role-policy-document file://ecs-task-role-trust-policy.json
    
    # Create a basic policy for the task role
    cat > ecs-task-role-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
EOF
    
    aws iam put-role-policy \
        --role-name ecsTaskRole \
        --policy-name ECSBasicPolicy \
        --policy-document file://ecs-task-role-policy.json
    
    log_info "✅ ECS Task Role created"
else
    log_info "✅ ECS Task Role already exists"
fi

# Cleanup
rm -f ecs-task-execution-role-trust-policy.json
rm -f ecs-task-role-trust-policy.json
rm -f ecs-task-role-policy.json

log_info "🎉 AWS IAM Roles setup complete!"
