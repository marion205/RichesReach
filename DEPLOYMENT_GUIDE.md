# RichesReach Production Deployment Guide

**Status**: Ready for Deployment  
**Last Updated**: November 10, 2024

---

## Pre-Deployment Checklist

### ✅ Completed
- [x] Environment variables configured
- [x] Sentry DSN added
- [x] Database credentials set
- [x] AWS credentials configured
- [x] Security settings enabled (DEBUG=False, SSL, HSTS)
- [x] Monitoring configured

### ⚠️ Before Deployment
- [ ] Update Redis endpoint (ElastiCache)
- [ ] Update email credentials
- [ ] Update S3 bucket name
- [ ] Run database migrations
- [ ] Test database connection

---

## Deployment Steps

### 1. Update Redis Configuration

**If using AWS ElastiCache**:
```bash
# Get your ElastiCache endpoint from AWS Console
# Update .env file:
REDIS_HOST=your-elasticache-endpoint.cache.amazonaws.com
CELERY_BROKER_URL=redis://your-elasticache-endpoint.cache.amazonaws.com:6379/0
CELERY_RESULT_BACKEND=redis://your-elasticache-endpoint.cache.amazonaws.com:6379/1
```

**If using local Redis for now**:
- Keep current localhost settings
- Update after ElastiCache is provisioned

---

### 2. Run Database Migrations

**Local (for testing)**:
```bash
cd deployment_package/backend
python manage.py migrate
```

**Production (on ECS)**:
- Migrations run automatically on container startup
- Or run manually via ECS task:
```bash
aws ecs run-task \
  --cluster riches-reach-cluster \
  --task-definition riches-reach-migration \
  --launch-type FARGATE
```

---

### 3. Test Database Connection

```bash
cd deployment_package/backend
python manage.py check --database default
```

---

### 4. Deploy to AWS ECS

### Option A: Using Existing Deployment Script

```bash
# If you have a deployment script
./deploy.sh
# or
./deploy_backend.sh
```

### Option B: Manual ECS Deployment

1. **Build Docker Image**:
```bash
docker build -t riches-reach-backend:latest .
docker tag riches-reach-backend:latest YOUR_ECR_REPO/riches-reach-backend:latest
docker push YOUR_ECR_REPO/riches-reach-backend:latest
```

2. **Update ECS Service**:
```bash
aws ecs update-service \
  --cluster riches-reach-cluster \
  --service riches-reach-backend \
  --force-new-deployment
```

3. **Monitor Deployment**:
```bash
aws ecs describe-services \
  --cluster riches-reach-cluster \
  --services riches-reach-backend
```

---

### 5. Verify Deployment

**Health Check**:
```bash
curl https://api.richesreach.com/health/
```

**GraphQL Endpoint**:
```bash
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

---

## Post-Deployment

### 1. Verify Sentry Integration

1. Go to https://sentry.io
2. Navigate to: elite-algorithmics → react-native
3. Check for any errors
4. Verify environment is "production"

### 2. Test Critical Endpoints

```bash
# Health check
curl https://api.richesreach.com/health/

# GraphQL
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'

# Authentication (if needed)
curl -X POST https://api.richesreach.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

### 3. Monitor Logs

**CloudWatch Logs**:
```bash
aws logs tail /ecs/riches-reach-backend --follow
```

**ECS Task Logs**:
```bash
aws ecs describe-tasks \
  --cluster riches-reach-cluster \
  --tasks TASK_ID
```

### 4. Set Up Sentry Alerts

Follow: `SENTRY_ALERTS_SETUP.md`

---

## Rollback Procedure

If deployment fails:

1. **Stop New Service**:
```bash
aws ecs update-service \
  --cluster riches-reach-cluster \
  --service riches-reach-backend \
  --desired-count 0
```

2. **Revert to Previous Task Definition**:
```bash
aws ecs update-service \
  --cluster riches-reach-cluster \
  --service riches-reach-backend \
  --task-definition riches-reach-backend:PREVIOUS_REVISION
```

3. **Restart Service**:
```bash
aws ecs update-service \
  --cluster riches-reach-cluster \
  --service riches-reach-backend \
  --desired-count 2
```

---

## Troubleshooting

### Database Connection Issues
- Verify security groups allow ECS → RDS
- Check RDS endpoint is correct
- Verify credentials in `.env`

### Redis Connection Issues
- Update ElastiCache endpoint
- Verify security groups
- Check Redis password (if set)

### Sentry Not Working
- Verify DSN in `.env`
- Check Sentry project is active
- Review Sentry dashboard for errors

---

## Quick Reference

**Environment File**: `deployment_package/backend/.env`  
**Health Endpoint**: `https://api.richesreach.com/health/`  
**GraphQL Endpoint**: `https://api.richesreach.com/graphql/`  
**Sentry Dashboard**: https://sentry.io (elite-algorithmics/react-native)

---

**Status**: Ready for deployment  
**Last Verified**: November 10, 2024

