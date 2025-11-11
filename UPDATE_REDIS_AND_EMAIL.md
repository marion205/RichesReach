# Update Redis and Email Configuration

**Date**: November 10, 2024

---

## 1. Redis/ElastiCache Endpoint Update

### Check ElastiCache Status

**Command to find ElastiCache**:
```bash
# Check for Replication Groups (recommended)
aws elasticache describe-replication-groups \
  --region us-east-1 \
  --query 'ReplicationGroups[*].{ID:ReplicationGroupId,Endpoint:NodeGroups[0].PrimaryEndpoint.Address,Status:Status}' \
  --output table

# Or check for Cache Clusters
aws elasticache describe-cache-clusters \
  --region us-east-1 \
  --show-cache-node-info \
  --query 'CacheClusters[*].{ID:CacheClusterId,Endpoint:ConfigurationEndpoint.Address,Status:CacheClusterStatus}' \
  --output table
```

### If ElastiCache Exists

**Update .env file**:
```bash
cd deployment_package/backend

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update Redis configuration
# Replace YOUR_ENDPOINT with actual ElastiCache endpoint
sed -i.bak "s|REDIS_HOST=localhost|REDIS_HOST=YOUR_ENDPOINT.cache.amazonaws.com|" .env
sed -i.bak "s|CELERY_BROKER_URL=redis://localhost|CELERY_BROKER_URL=redis://YOUR_ENDPOINT.cache.amazonaws.com:6379/0|" .env
sed -i.bak "s|CELERY_RESULT_BACKEND=redis://localhost|CELERY_RESULT_BACKEND=redis://YOUR_ENDPOINT.cache.amazonaws.com:6379/1|" .env

# Verify changes
grep -E "^REDIS_HOST=|^CELERY_BROKER_URL=|^CELERY_RESULT_BACKEND=" .env
```

**Then redeploy**:
```bash
cd ../..
./deploy_backend.sh
```

### If ElastiCache Doesn't Exist

**Option 1: Create ElastiCache Cluster** (Recommended for Production)

```bash
aws elasticache create-replication-group \
  --replication-group-id riches-reach-redis \
  --description "RichesReach Redis Cache" \
  --node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-clusters 1 \
  --cache-subnet-group-name default \
  --security-group-ids sg-031f029375f188e04 \
  --region us-east-1
```

**Wait for cluster to be available** (5-10 minutes), then get endpoint and update .env.

**Option 2: Keep Localhost for Now**
- Current configuration works for development/testing
- Update when ElastiCache is ready
- No immediate action needed

---

## 2. Email Configuration Update

### Current Status

Check current email configuration:
```bash
cd deployment_package/backend
grep -E "^EMAIL_HOST=|^EMAIL_HOST_USER=|^EMAIL_HOST_PASSWORD=|^DEFAULT_FROM_EMAIL=" .env
```

### Update Email Settings

**For Gmail**:
```bash
cd deployment_package/backend

# Edit .env and update:
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password  # NOT your regular password!
DEFAULT_FROM_EMAIL=noreply@richesreach.com
```

**For AWS SES** (Recommended for Production):
```bash
# Update .env:
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=YOUR_SES_SMTP_USERNAME
EMAIL_HOST_PASSWORD=YOUR_SES_SMTP_PASSWORD
DEFAULT_FROM_EMAIL=noreply@richesreach.com
```

**Get AWS SES Credentials**:
1. Go to AWS Console → SES → SMTP Settings
2. Create SMTP credentials
3. Use the username and password in .env

### Test Email Configuration

**Django Shell Test**:
```bash
cd deployment_package/backend
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from RichesReach.',
    'noreply@richesreach.com',
    ['your-email@example.com'],
    fail_silently=False,
)
```

**If successful**: Email received ✅  
**If failed**: Check credentials and SMTP settings

### Redeploy After Email Update

```bash
cd ../..
./deploy_backend.sh
```

---

## 3. Final Testing and Verification

### Pre-Deployment Checklist

- [ ] Redis endpoint updated (if ElastiCache ready)
- [ ] Email configuration updated (if sending emails)
- [ ] .env file backed up
- [ ] Changes verified

### Post-Deployment Verification

#### 1. Health Check
```bash
curl https://api.richesreach.com/health/
# Expected: {"status": "ok"} or 200 OK
```

#### 2. GraphQL Endpoint
```bash
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
# Expected: {"data":{"__typename":"Query"}}
```

#### 3. Database Connection
```bash
cd deployment_package/backend
python manage.py check --database default
# Expected: System check identified no issues
```

#### 4. Redis Connection (If Updated)
```bash
python manage.py shell
```

```python
from django.core.cache import cache
cache.set('test_key', 'test_value', 60)
result = cache.get('test_key')
print(f"Redis test: {result}")  # Should print: Redis test: test_value
```

#### 5. Email Test (If Updated)
```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    'RichesReach Test',
    'Email configuration test.',
    'noreply@richesreach.com',
    ['your-email@example.com'],
    fail_silently=False,
)
# Check your email inbox
```

#### 6. Sentry Integration
- Use Sentry Test Button in mobile app
- Verify error appears in Sentry dashboard
- Check that alerts are configured

#### 7. Logs Verification
```bash
aws logs tail /ecs/riches-reach-backend --follow --region us-east-1
# Check for:
# - No critical errors
# - Application started successfully
# - Database connections working
# - Redis connections working (if updated)
```

#### 8. Performance Check
```bash
# Test response times
time curl -s https://api.richesreach.com/health/
# Should be < 1 second
```

---

## Complete Verification Checklist

### Infrastructure
- [ ] ECS service running (1/1 tasks)
- [ ] Health endpoint responding (200 OK)
- [ ] GraphQL endpoint working
- [ ] Database connection verified
- [ ] Redis connection verified (if updated)
- [ ] Logs accessible

### Configuration
- [ ] Redis endpoint updated (if ElastiCache ready)
- [ ] Email configuration updated (if needed)
- [ ] Environment variables correct
- [ ] Security settings enabled

### Monitoring
- [ ] Sentry receiving errors
- [ ] Sentry alerts configured
- [ ] Monitoring dashboard created
- [ ] Logs being collected

### Functionality
- [ ] Authentication working
- [ ] GraphQL queries working
- [ ] Database operations working
- [ ] Cache operations working (if Redis updated)
- [ ] Email sending working (if email updated)

---

## Troubleshooting

### Redis Connection Issues
- Verify ElastiCache endpoint is correct
- Check security groups allow ECS → ElastiCache
- Verify Redis port (6379) is open
- Check ElastiCache cluster status

### Email Sending Issues
- Verify SMTP credentials
- Check email service limits (Gmail: 500/day, SES: check limits)
- Verify sender email is verified (SES)
- Check spam folder
- Review email logs

### Deployment Issues
- Check ECS service events
- Review container logs
- Verify environment variables
- Check task definition

---

## Quick Commands Reference

**Check ElastiCache**:
```bash
aws elasticache describe-replication-groups --region us-east-1
```

**Update Redis in .env**:
```bash
cd deployment_package/backend
# Edit .env manually or use sed commands above
```

**Test Redis**:
```bash
python manage.py shell
# Then: from django.core.cache import cache; cache.set('test', 'value')
```

**Test Email**:
```bash
python manage.py shell
# Then: from django.core.mail import send_mail; send_mail(...)
```

**Redeploy**:
```bash
./deploy_backend.sh
```

---

**Status**: Ready to update configuration  
**Next**: Follow steps above based on your needs

