# Deployment Execution Plan

**Date**: November 10, 2024  
**Status**: Ready to Execute

---

## Step 1: Review Environment Configuration ✅

**File**: `ENV_REVIEW_REPORT.md`

**Key Findings**:
- ✅ Database: Configured (PostgreSQL RDS)
- ✅ Sentry: Configured with DSN
- ✅ Security: All keys set
- ⚠️ Redis: Currently localhost (needs ElastiCache endpoint)
- ⚠️ Email: Placeholder values
- ⚠️ S3 Bucket: Placeholder name

**Action**: Review complete. Redis can be updated post-deployment.

---

## Step 2: Update Redis Endpoint

### Option A: If ElastiCache Already Exists

**Find your ElastiCache endpoint**:
```bash
aws elasticache describe-cache-clusters \
  --region us-east-1 \
  --show-cache-node-info \
  --query 'CacheClusters[*].{ID:CacheClusterId,Endpoint:ConfigurationEndpoint.Address}'
```

**Update .env**:
```bash
cd deployment_package/backend
# Edit .env and update:
REDIS_HOST=your-elasticache-endpoint.cache.amazonaws.com
CELERY_BROKER_URL=redis://your-elasticache-endpoint.cache.amazonaws.com:6379/0
CELERY_RESULT_BACKEND=redis://your-elasticache-endpoint.cache.amazonaws.com:6379/1
```

### Option B: If ElastiCache Not Ready

**For now**: Keep localhost settings  
**After deployment**: Create ElastiCache cluster and update

**Create ElastiCache (if needed)**:
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id riches-reach-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --region us-east-1
```

---

## Step 3: Deploy Application

### Quick Deployment (Recommended)

**Option 1: Backend Only**
```bash
./deploy_backend.sh
```

**Option 2: Full Deployment (Mobile + Backend)**
```bash
./deploy.sh
```

### Manual Deployment Steps

1. **Verify AWS Credentials**:
```bash
aws sts get-caller-identity
```

2. **Build and Push Docker Image**:
```bash
cd deployment_package/backend
docker build -t richesreach-ai:production .
docker tag richesreach-ai:production 498606688292.dkr.ecr.us-east-1.amazonaws.com/richesreach-ai:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 498606688292.dkr.ecr.us-east-1.amazonaws.com
docker push 498606688292.dkr.ecr.us-east-1.amazonaws.com/richesreach-ai:latest
```

3. **Update ECS Service**:
```bash
aws ecs update-service \
  --cluster richesreach-cluster \
  --service richesreach-service \
  --force-new-deployment \
  --region us-east-1
```

4. **Monitor Deployment**:
```bash
aws ecs describe-services \
  --cluster richesreach-cluster \
  --services richesreach-service \
  --region us-east-1 \
  --query 'services[0].deployments'
```

---

## Step 4: Verify Deployment

### Health Check
```bash
curl https://api.richesreach.com/health/
# or
curl http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/health/
```

### GraphQL Test
```bash
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

### Check Logs
```bash
aws logs tail /ecs/riches-reach-backend --follow --region us-east-1
```

---

## Step 5: Set Up Sentry Alerts

### Quick Setup (5 minutes)

1. **Go to Sentry Dashboard**:
   - https://sentry.io
   - Navigate to: **elite-algorithmics** → **react-native**

2. **Create Critical Error Alert**:
   - Go to **Alerts** → **Create Alert Rule**
   - **Name**: "Critical Errors"
   - **Condition**: `level:error OR level:fatal`
   - **Threshold**: 1 event in 5 minutes
   - **Action**: Email notification
   - **Save**

3. **Create High Volume Alert**:
   - **Name**: "High Volume Errors"
   - **Condition**: `level:error OR level:fatal`
   - **Threshold**: 10 events in 10 minutes
   - **Action**: Email + Slack (if configured)
   - **Save**

4. **Test Alert**:
   - Use Sentry Test Button in app
   - Or trigger test error from backend
   - Verify alert is received

### Detailed Setup

Follow: `MONITORING_SETUP.md` for complete alert configuration

---

## Deployment Checklist

### Pre-Deployment
- [x] Environment variables configured
- [x] Sentry DSN added
- [x] Database credentials verified
- [ ] Redis endpoint updated (if ElastiCache ready)
- [ ] Email credentials updated (if needed)
- [ ] S3 bucket name updated (if needed)

### Deployment
- [ ] AWS credentials verified
- [ ] Docker image built
- [ ] Image pushed to ECR
- [ ] ECS service updated
- [ ] Deployment monitored

### Post-Deployment
- [ ] Health check passed
- [ ] GraphQL endpoint working
- [ ] Sentry receiving errors
- [ ] Logs accessible
- [ ] Alerts configured

---

## Troubleshooting

### Deployment Fails
- Check ECS service logs
- Verify task definition
- Check security groups
- Verify environment variables

### Health Check Fails
- Check ALB target group health
- Verify container is running
- Check application logs
- Verify database connection

### Sentry Not Working
- Verify DSN in .env
- Check Sentry project is active
- Review Sentry dashboard
- Check network connectivity

---

## Quick Reference

**Environment File**: `deployment_package/backend/.env`  
**Health Endpoint**: `https://api.richesreach.com/health/`  
**GraphQL Endpoint**: `https://api.richesreach.com/graphql/`  
**Sentry Dashboard**: https://sentry.io (elite-algorithmics/react-native)  
**ECS Console**: https://us-east-1.console.aws.amazon.com/ecs/

---

**Status**: Ready to execute  
**Estimated Time**: 15-30 minutes

