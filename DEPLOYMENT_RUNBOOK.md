# RichesReach Deployment Runbook

## Quick Release Process

### 1. Deploy via GitHub Actions
- Push to `main` branch → "Build and Deploy to ECS" workflow runs automatically
- Workflow builds & pushes image with both commit SHA and human-friendly tags
- Clones TD 139 (baseline with secrets & healthcheck), swaps only the image
- Registers new TD, updates service, waits for stabilization
- Runs migrations, shows logs

### 2. Verify Deployment

```bash
# Service status
aws ecs describe-services \
  --cluster riches-reach-ai-production-cluster \
  --services riches-reach-ai-ai --region us-east-1 \
  --query 'services[0].{td:taskDefinition,running:runningCount,pending:pendingCount}'

# Current task details
TASK_ARN=$(aws ecs list-tasks --cluster riches-reach-ai-production-cluster \
  --service-name riches-reach-ai-ai --region us-east-1 --output text)
aws ecs describe-tasks --cluster riches-reach-ai-production-cluster \
  --tasks "$TASK_ARN" --region us-east-1 \
  --query 'tasks[0].{image:containers[0].image,last:lastStatus,health:healthStatus}'
```

### 3. Rollback (Instant)

```bash
# Rollback to stable anchor (TD 100)
aws ecs update-service --cluster riches-reach-ai-production-cluster \
  --service riches-reach-ai-ai --task-definition riches-reach-ai-task:100 \
  --force-new-deployment --region us-east-1

# Rollback to last good with secrets (TD 139)
aws ecs update-service --cluster riches-reach-ai-production-cluster \
  --service riches-reach-ai-ai --task-definition riches-reach-ai-task:139 \
  --force-new-deployment --region us-east-1
```

## Day-2 Commands

### List Recent Task Definitions
```bash
aws ecs list-task-definitions \
  --family-prefix riches-reach-ai-task --status ACTIVE --region us-east-1 \
  --sort DESC --max-items 5
```

### Check Image in Task Definition
```bash
aws ecs describe-task-definition --task-definition riches-reach-ai-task:<REV> \
  --region us-east-1 \
  --query 'taskDefinition.containerDefinitions[?name==`riches-reach-ai`].image' --output text
```

### Tail Live Logs
```bash
LG=/ecs/riches-reach-ai
TASK_ARN=$(aws ecs list-tasks --cluster riches-reach-ai-production-cluster \
  --service-name riches-reach-ai-ai --region us-east-1 --output text)
aws logs tail "$LG" --log-stream-names "ecs/riches-reach-ai/${TASK_ARN##*/}" \
  --since 10m --region us-east-1 --follow
```

## Features

- ✅ **Immutable Tags**: Uses commit SHA for perfect traceability
- ✅ **Circuit Breaker**: Auto-rollback on deployment failure
- ✅ **Secrets Management**: All database credentials from AWS Secrets Manager
- ✅ **Health Checks**: Configured and monitored
- ✅ **OIDC Authentication**: No long-lived keys
- ✅ **Baseline Preservation**: Future deployments inherit all production settings

## Current Configuration

- **Baseline TD**: `riches-reach-ai-task:139` (has all secrets/healthchecks)
- **ECR Repository**: `riches-reach-ai`
- **Database**: PostgreSQL on RDS with `appuser` credentials
- **Logs**: CloudWatch `/ecs/riches-reach-ai`
- **Circuit Breaker**: ENABLED (auto-rollback on failure)
