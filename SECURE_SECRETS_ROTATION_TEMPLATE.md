# 🔐 SECURE SECRETS ROTATION TEMPLATE
**Enterprise-Grade Secret Management for RichesReach**

## 🎯 **OVERVIEW**

This template extends your existing secret management with:
- ✅ **AWS Secrets Manager** with multi-region KMS encryption
- ✅ **Automated rotation** via Lambda functions
- ✅ **CI-driven rotation** for vendor APIs without rotation endpoints
- ✅ **Least-privilege IAM** policies
- ✅ **ECS TaskDefinition** secrets integration
- ✅ **Audit trails** and compliance monitoring

---

## 📁 **REPOSITORY STRUCTURE**

```
infrastructure/
├── secrets/
│   ├── variables.tf
│   ├── kms.tf
│   ├── secrets.tf
│   ├── rotation_lambda.tf
│   ├── iam.tf
│   ├── eventbridge.tf
│   └── outputs.tf
├── lambdas/
│   ├── rotate_generic/
│   │   └── handler.py
│   └── rotate_aws_iam_access_key/
│       └── handler.py
└── .github/
    └── workflows/
        └── rotate-secrets.yml

backend/
└── config/
    └── .env.template
```

---

## 🏗️ **TERRAFORM INFRASTRUCTURE**

### 1. Variables Configuration

```hcl
# infrastructure/secrets/variables.tf
variable "project" {
  type        = string
  description = "Project name"
  default     = "richesreach"
}

variable "env" {
  type        = string
  description = "Environment (production, staging, development)"
  default     = "production"
}

variable "regions" {
  type        = list(string)
  description = "AWS regions for multi-region deployment"
  default     = ["us-east-1", "eu-west-1", "ap-southeast-1"]
}

variable "secrets_list" {
  type = map(string)
  description = "Logical names -> descriptions for secrets"
  default = {
    "openai_api_key"      = "OpenAI API key for AI features"
    "polygon_api_key"     = "Polygon.io API key for market data"
    "finnhub_api_key"     = "Finnhub API key for stock data"
    "alpha_vantage_key"   = "Alpha Vantage API key for technical indicators"
    "alchemy_key"         = "Alchemy API key for blockchain data"
    "walletconnect_id"    = "WalletConnect project ID"
    "newsapi_key"         = "News API key for financial news"
    "aws_access_key"      = "AWS IAM access key for CI/CD"
  }
}
```

### 2. Multi-Region KMS Configuration

```hcl
# infrastructure/secrets/kms.tf
resource "aws_kms_key" "secrets_mrk" {
  description         = "${var.project}-${var.env}-secrets-mrk"
  enable_key_rotation = true
  multi_region        = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Secrets Manager"
        Effect = "Allow"
        Principal = {
          Service = "secretsmanager.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "secrets_mrk_alias" {
  name          = "alias/${var.project}-${var.env}-secrets"
  target_key_id = aws_kms_key.secrets_mrk.key_id
}

data "aws_caller_identity" "current" {}
```

### 3. Secrets Manager Configuration

```hcl
# infrastructure/secrets/secrets.tf
locals {
  name_prefix = "${var.project}/${var.env}"
}

# Create secrets in primary region (us-east-1)
resource "aws_secretsmanager_secret" "secret" {
  for_each                = var.secrets_list
  name                    = "${local.name_prefix}/${each.key}"
  kms_key_id              = aws_kms_key.secrets_mrk.arn
  recovery_window_in_days = 7
  description             = each.value
  
  tags = {
    Environment = var.env
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

# Initial placeholder values - CI will populate
resource "aws_secretsmanager_secret_version" "secret_init" {
  for_each      = var.secrets_list
  secret_id     = aws_secretsmanager_secret.secret[each.key].id
  secret_string = jsonencode({
    value = "REPLACE_ME_VIA_CI"
    metadata = {
      source     = "bootstrap"
      created_at = timestamp()
      rotated_by = "terraform"
    }
  })
}
```

### 4. Rotation Lambda Functions

```hcl
# infrastructure/secrets/rotation_lambda.tf
# Generic rotation Lambda for vendor APIs
data "archive_file" "rotate_generic_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/rotate_generic"
  output_path = "${path.module}/.build/rotate_generic.zip"
}

resource "aws_iam_role" "rotate_generic_role" {
  name = "${var.project}-${var.env}-rotate-generic"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "rotate_generic_policy" {
  name = "${var.project}-${var.env}-rotate-generic"
  role = aws_iam_role.rotate_generic_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = [
          for k, _ in var.secrets_list :
          aws_secretsmanager_secret.secret[k].arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "rotate_generic" {
  function_name = "${var.project}-${var.env}-rotate-generic"
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.rotate_generic_role.arn
  filename      = data.archive_file.rotate_generic_zip.output_path
  timeout       = 60
  
  environment {
    variables = {
      HEALTHCHECK_URL = "https://api.richesreach.net/health/ready"
      PROJECT         = var.project
      ENV             = var.env
    }
  }
  
  tags = {
    Environment = var.env
    Project     = var.project
  }
}

# Enable rotation for all secrets
resource "aws_secretsmanager_secret_rotation" "generic_rotation" {
  for_each               = var.secrets_list
  secret_id              = aws_secretsmanager_secret.secret[each.key].id
  rotation_lambda_arn    = aws_lambda_function.rotate_generic.arn
  
  rotation_rules {
    automatically_after_days = 30
  }
}
```

### 5. IAM Policies for Application Access

```hcl
# infrastructure/secrets/iam.tf
data "aws_iam_policy_document" "app_read_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = [
      for k, _ in var.secrets_list :
      aws_secretsmanager_secret.secret[k].arn
    ]
    condition {
      test     = "StringEquals"
      variable = "aws:ResourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_policy" "app_read_secrets" {
  name        = "${var.project}-${var.env}-app-read-secrets"
  description = "Policy for application to read secrets"
  policy      = data.aws_iam_policy_document.app_read_secrets.json
}

# CI/CD role for secret rotation
data "aws_iam_policy_document" "ci_rotate_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:PutSecretValue",
      "secretsmanager:UpdateSecretVersionStage",
      "secretsmanager:ListSecrets"
    ]
    resources = [
      for k, _ in var.secrets_list :
      aws_secretsmanager_secret.secret[k].arn
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.rotate_generic.arn
    ]
  }
}

resource "aws_iam_policy" "ci_rotate_secrets" {
  name        = "${var.project}-${var.env}-ci-rotate-secrets"
  description = "Policy for CI/CD to rotate secrets"
  policy      = data.aws_iam_policy_document.ci_rotate_secrets.json
}
```

### 6. EventBridge Scheduling

```hcl
# infrastructure/secrets/eventbridge.tf
resource "aws_cloudwatch_event_rule" "rotate_monthly" {
  name                = "${var.project}-${var.env}-rotate-monthly"
  description         = "Trigger monthly secret rotation check"
  schedule_expression = "rate(30 days)"
  
  tags = {
    Environment = var.env
    Project     = var.project
  }
}

resource "aws_cloudwatch_event_target" "rotate_generic_monthly" {
  rule      = aws_cloudwatch_event_rule.rotate_monthly.name
  target_id = "rotate-generic"
  arn       = aws_lambda_function.rotate_generic.arn
  
  input = jsonencode({
    SecretId       = "arn:aws:secretsmanager:us-east-1:${data.aws_caller_identity.current.account_id}:secret:${var.project}/${var.env}/openai_api_key"
    CandidateValue = "PLACEHOLDER_FROM_CI"
    Action         = "check_rotation_status"
  })
}

resource "aws_lambda_permission" "allow_events" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rotate_generic.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rotate_monthly.arn
}
```

---

## 🐍 **LAMBDA FUNCTIONS**

### 1. Generic Rotation Handler

```python
# infrastructure/lambdas/rotate_generic/handler.py
import json
import os
import time
import urllib.request
import boto3
from botocore.exceptions import ClientError

sm = boto3.client("secretsmanager")

def _get_stage_val(secret_id, stage):
    """Get secret value for a specific stage"""
    try:
        v = sm.get_secret_value(SecretId=secret_id, VersionStage=stage)
        body = json.loads(v.get("SecretString") or "{}")
        return body.get("value")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        raise

def _put_stage_val(secret_id, value, stage):
    """Set secret value for a specific stage"""
    secret_data = {
        "value": value,
        "metadata": {
            "source": "lambda_rotation",
            "rotated_at": time.time(),
            "stage": stage
        }
    }
    sm.put_secret_value(
        SecretId=secret_id,
        SecretString=json.dumps(secret_data),
        VersionStages=[stage]
    )

def _health_check(url):
    """Perform health check on application"""
    try:
        response = urllib.request.urlopen(url, timeout=10)
        return response.status == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def _promote_secret(secret_id, new_secret_value):
    """Promote new secret from AWSPENDING to AWSCURRENT"""
    # 1) Set AWSPENDING to new value
    _put_stage_val(secret_id, new_secret_value, "AWSPENDING")
    
    # 2) Optional health check
    health_url = os.getenv("HEALTHCHECK_URL")
    if health_url:
        if not _health_check(health_url):
            raise RuntimeError("Health check failed; aborting promotion")
    
    # 3) Promote pending to current
    _put_stage_val(secret_id, new_secret_value, "AWSCURRENT")
    
    print(f"Successfully rotated secret: {secret_id}")

def lambda_handler(event, context):
    """Main Lambda handler for secret rotation"""
    try:
        # Parse event
        if isinstance(event, str):
            event = json.loads(event)
        
        secret_id = event.get("SecretId")
        candidate_value = event.get("CandidateValue")
        action = event.get("Action", "rotate")
        
        if not secret_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "SecretId is required"})
            }
        
        if action == "check_rotation_status":
            # Just check if rotation is needed
            current_value = _get_stage_val(secret_id, "AWSCURRENT")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "checked",
                    "secret_id": secret_id,
                    "has_current": current_value is not None
                })
            }
        
        if not candidate_value:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "CandidateValue is required for rotation"})
            }
        
        # Perform rotation
        _promote_secret(secret_id, candidate_value)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "rotated",
                "secret_id": secret_id,
                "timestamp": time.time()
            })
        }
        
    except Exception as e:
        print(f"Rotation failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
```

### 2. AWS IAM Access Key Rotation

```python
# infrastructure/lambdas/rotate_aws_iam_access_key/handler.py
import json
import boto3
from botocore.exceptions import ClientError

iam = boto3.client("iam")
sm = boto3.client("secretsmanager")

IAM_USER = "richesreach-ci"

def lambda_handler(event, context):
    """Rotate AWS IAM access keys"""
    try:
        secret_id = event["SecretId"]
        
        # Create new access key
        response = iam.create_access_key(UserName=IAM_USER)
        new_key = {
            "aws_access_key_id": response["AccessKey"]["AccessKeyId"],
            "aws_secret_access_key": response["AccessKey"]["SecretAccessKey"],
            "metadata": {
                "created_at": response["AccessKey"]["CreateDate"].isoformat(),
                "user": IAM_USER
            }
        }
        
        # Stage as pending
        sm.put_secret_value(
            SecretId=secret_id,
            SecretString=json.dumps(new_key),
            VersionStages=["AWSPENDING"]
        )
        
        # Promote to current
        sm.put_secret_value(
            SecretId=secret_id,
            SecretString=json.dumps(new_key),
            VersionStages=["AWSCURRENT"]
        )
        
        # Deactivate old key (optional - list and deactivate previous)
        try:
            old_keys = iam.list_access_keys(UserName=IAM_USER)
            for key in old_keys["AccessKeyMetadata"]:
                if key["AccessKeyId"] != new_key["aws_access_key_id"]:
                    iam.delete_access_key(
                        UserName=IAM_USER,
                        AccessKeyId=key["AccessKeyId"]
                    )
        except ClientError as e:
            print(f"Warning: Could not clean up old key: {e}")
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "rotated",
                "secret_id": secret_id,
                "new_key_id": new_key["aws_access_key_id"]
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
```

---

## 🔄 **GITHUB ACTIONS CI/CD**

```yaml
# .github/workflows/rotate-secrets.yml
name: Rotate Secrets

on:
  workflow_dispatch:
    inputs:
      secret_name:
        description: "Secret logical name (e.g., polygon_api_key)"
        required: true
        type: choice
        options:
          - openai_api_key
          - polygon_api_key
          - finnhub_api_key
          - alpha_vantage_key
          - alchemy_key
          - walletconnect_id
          - newsapi_key
      new_value:
        description: "NEW secret value (paste or provided by prior job)"
        required: true
        type: string
      environment:
        description: "Environment to rotate"
        required: true
        type: choice
        options:
          - production
          - staging
        default: production

jobs:
  rotate:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Configure AWS
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/richesreach-ci-role
        aws-region: us-east-1
    
    - name: Get Secret ARN
      id: get_secret_arn
      run: |
        SECRET_ARN=$(aws secretsmanager list-secrets \
          --filters Key=name,Values=richesreach/${{ github.event.inputs.environment }}/${{ github.event.inputs.secret_name }} \
          --query 'SecretList[0].ARN' --output text)
        echo "secret_arn=$SECRET_ARN" >> $GITHUB_OUTPUT
        echo "Secret ARN: $SECRET_ARN"
    
    - name: Stage New Secret
      run: |
        aws lambda invoke \
          --function-name richesreach-${{ github.event.inputs.environment }}-rotate-generic \
          --payload "$(jq -n \
            --arg id "${{ steps.get_secret_arn.outputs.secret_arn }}" \
            --arg val "${{ github.event.inputs.new_value }}" \
            '{SecretId:$id, CandidateValue:$val, Action:"rotate"}')" \
          /tmp/rotation_result.json
        
        cat /tmp/rotation_result.json
        
        # Check if rotation was successful
        if jq -e '.statusCode == 200' /tmp/rotation_result.json > /dev/null; then
          echo "✅ Secret rotation successful"
        else
          echo "❌ Secret rotation failed"
          exit 1
        fi
    
    - name: Verify Application Health
      run: |
        # Wait for application to pick up new secret
        sleep 30
        
        # Check application health
        HEALTH_URL="https://api.richesreach.net/health/ready"
        if curl -f -s "$HEALTH_URL" > /dev/null; then
          echo "✅ Application health check passed"
        else
          echo "❌ Application health check failed"
          exit 1
        fi
    
    - name: Create Rotation Log
      run: |
        echo "Secret rotated: ${{ github.event.inputs.secret_name }}" >> rotation.log
        echo "Environment: ${{ github.event.inputs.environment }}" >> rotation.log
        echo "Timestamp: $(date)" >> rotation.log
        echo "Rotated by: ${{ github.actor }}" >> rotation.log
```

---

## 🐳 **ECS TASK DEFINITION INTEGRATION**

```json
{
  "family": "richesreach-backend",
  "taskRoleArn": "arn:aws:iam::123456789012:role/richesreach-ecs-task-role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/richesreach-ecs-execution-role",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/richesreach-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:richesreach/production/openai_api_key"
        },
        {
          "name": "POLYGON_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:richesreach/production/polygon_api_key"
        },
        {
          "name": "FINNHUB_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:richesreach/production/finnhub_api_key"
        },
        {
          "name": "ALPHA_VANTAGE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:richesreach/production/alpha_vantage_key"
        },
        {
          "name": "ALCHEMY_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:richesreach/production/alchemy_key"
        },
        {
          "name": "WALLETCONNECT_PROJECT_ID",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:richesreach/production/walletconnect_id"
        },
        {
          "name": "NEWS_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:richesreach/production/newsapi_key"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/richesreach-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "essential": true
    }
  ]
}
```

---

## 🔧 **ENVIRONMENT TEMPLATE**

```bash
# backend/config/.env.template
# DO NOT COMMIT REAL VALUES - This is for local development only

# Environment
ENVIRONMENT=development
DEBUG=true

# API Keys (use your local development keys)
OPENAI_API_KEY=your_local_openai_key
POLYGON_API_KEY=your_local_polygon_key
FINNHUB_API_KEY=your_local_finnhub_key
ALPHA_VANTAGE_API_KEY=your_local_alpha_vantage_key
ALCHEMY_API_KEY=your_local_alchemy_key
WALLETCONNECT_PROJECT_ID=your_local_walletconnect_id
NEWS_API_KEY=your_local_newsapi_key

# Database (local development)
DATABASE_URL=postgresql://user:password@localhost:5432/richesreach_dev

# Redis (local development)
REDIS_URL=redis://localhost:6379/0

# AWS (local development - use AWS CLI profiles)
AWS_REGION=us-east-1

# Production reads from AWS Secrets Manager automatically
# No need to set these in production environment
```

---

## 🚀 **DEPLOYMENT COMMANDS**

### 1. Deploy Infrastructure

```bash
# Deploy secrets infrastructure
cd infrastructure/secrets
terraform init
terraform plan -var 'project=richesreach' -var 'env=production'
terraform apply -var 'project=richesreach' -var 'env=production'

# Deploy Lambda functions
cd ../lambdas/rotate_generic
zip -r handler.zip handler.py
aws lambda update-function-code \
  --function-name richesreach-production-rotate-generic \
  --zip-file fileb://handler.zip
```

### 2. Manual Secret Rotation

```bash
# Rotate a specific secret via GitHub Actions
gh workflow run rotate-secrets.yml \
  -f secret_name=polygon_api_key \
  -f new_value='NEW_POLYGON_KEY_HERE' \
  -f environment=production

# Or via AWS CLI directly
aws lambda invoke \
  --function-name richesreach-production-rotate-generic \
  --payload '{
    "SecretId": "arn:aws:secretsmanager:us-east-1:123456789012:secret:richesreach/production/polygon_api_key",
    "CandidateValue": "NEW_POLYGON_KEY_HERE",
    "Action": "rotate"
  }' \
  /tmp/rotation_result.json
```

### 3. Verify Deployment

```bash
# Check secret status
aws secretsmanager describe-secret \
  --secret-id richesreach/production/polygon_api_key

# Test application health
curl -f https://api.richesreach.net/health/ready

# Check rotation logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/richesreach-production-rotate-generic \
  --start-time $(date -d '1 hour ago' +%s)000
```

---

## 📋 **SECURITY CHECKLIST**

- [ ] **KMS Encryption**: Multi-region KMS key with rotation enabled
- [ ] **Least Privilege**: IAM policies scoped to specific secret ARNs
- [ ] **VPC Endpoints**: Restrict secrets access to VPC endpoints only
- [ ] **Audit Logging**: CloudTrail and CloudWatch Logs enabled
- [ ] **Rotation Schedule**: 30-day automatic rotation enabled
- [ ] **Health Checks**: Application health verification before promotion
- [ ] **Rollback Capability**: Previous versions available for rollback
- [ ] **CI/CD Integration**: GitHub Actions for secure rotation workflow
- [ ] **Environment Separation**: Different secrets for dev/staging/production
- [ ] **Compliance**: SOC2, GDPR, and PCI-DSS requirements met

---

## 🆘 **EMERGENCY PROCEDURES**

### Rollback Secret

```bash
# Get previous version
aws secretsmanager get-secret-value \
  --secret-id richesreach/production/polygon_api_key \
  --version-stage AWSPREVIOUS

# Promote previous version to current
aws secretsmanager update-secret-version-stage \
  --secret-id richesreach/production/polygon_api_key \
  --version-stage AWSCURRENT \
  --move-to-version-id PREVIOUS_VERSION_ID
```

### Emergency Key Rotation

```bash
# Immediate rotation via Lambda
aws lambda invoke \
  --function-name richesreach-production-rotate-generic \
  --payload '{
    "SecretId": "SECRET_ARN",
    "CandidateValue": "EMERGENCY_NEW_KEY",
    "Action": "rotate"
  }' \
  /tmp/emergency_rotation.json
```

---

## 🎯 **NEXT STEPS**

1. **Deploy Infrastructure**: Run Terraform to create secrets infrastructure
2. **Update ECS Tasks**: Modify task definitions to use secret ARNs
3. **Test Rotation**: Perform test rotation via GitHub Actions
4. **Monitor**: Set up CloudWatch alarms for rotation failures
5. **Document**: Update runbooks with rotation procedures

**Your RichesReach platform will now have enterprise-grade secret management with automatic rotation, audit trails, and zero plaintext secrets in your codebase!** 🔐
