# Final Testing and Verification Checklist

**Date**: November 10, 2024  
**Purpose**: Comprehensive production verification

---

## Pre-Testing Setup

- [ ] Redis endpoint updated (if ElastiCache ready)
- [ ] Email configuration updated (if sending emails)
- [ ] .env file backed up
- [ ] Changes committed/noted
- [ ] Deployment completed (if config changed)

---

## 1. Infrastructure Tests

### Health Endpoint ✅
```bash
curl https://api.richesreach.com/health/
```
- [ ] Returns 200 OK
- [ ] Response time < 1 second
- [ ] Response contains expected data

**Expected**: `{"status": "ok"}` or similar

### GraphQL Endpoint ✅
```bash
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```
- [ ] Returns 200 OK
- [ ] Response contains `{"data":{"__typename":"Query"}}`
- [ ] Response time < 2 seconds

### Load Balancer ✅
```bash
curl http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/health/
```
- [ ] ALB responding
- [ ] Health checks passing
- [ ] Target group healthy

---

## 2. Database Tests

### Connection Test
```bash
cd deployment_package/backend
python manage.py check --database default
```
- [ ] No connection errors
- [ ] Database accessible
- [ ] Migrations applied

### Query Test
```bash
python manage.py shell
```
```python
from django.contrib.auth import get_user_model
User = get_user_model()
print(f"Users in database: {User.objects.count()}")
```
- [ ] Can query database
- [ ] No errors
- [ ] Returns expected data

---

## 3. Redis/Cache Tests (If Updated)

### Connection Test
```bash
python manage.py shell
```
```python
from django.core.cache import cache
cache.set('test_key', 'test_value', 60)
result = cache.get('test_key')
print(f"Redis test: {result}")
```
- [ ] Cache set successful
- [ ] Cache get successful
- [ ] Returns: `Redis test: test_value`

### Celery Test (If Using)
```bash
python manage.py shell
```
```python
from core.banking_tasks import refresh_bank_accounts_task
# Test task can be queued (don't actually run)
print("Celery connection OK")
```
- [ ] Celery broker accessible
- [ ] Tasks can be queued

---

## 4. Email Tests (If Updated)

### Configuration Test
```bash
python manage.py shell
```
```python
from django.conf import settings
print(f"Email host: {settings.EMAIL_HOST}")
print(f"Email port: {settings.EMAIL_PORT}")
print(f"Email user: {settings.EMAIL_HOST_USER}")
```
- [ ] Email settings loaded
- [ ] Credentials configured

### Send Test Email
```python
from django.core.mail import send_mail
try:
    send_mail(
        'RichesReach Test Email',
        'This is a test email from RichesReach production.',
        'noreply@richesreach.com',
        ['your-email@example.com'],
        fail_silently=False,
    )
    print("✅ Email sent successfully")
except Exception as e:
    print(f"❌ Email failed: {e}")
```
- [ ] Email sent without errors
- [ ] Email received in inbox
- [ ] Check spam folder if not received

---

## 5. Authentication Tests

### GraphQL Authentication
```bash
# Test unauthenticated query
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ me { id email } }"}'
```
- [ ] Returns appropriate error for unauthenticated
- [ ] No 500 errors

### JWT Token Test (If Applicable)
- [ ] Can obtain token
- [ ] Token works for authenticated queries
- [ ] Token expiration works

---

## 6. API Endpoint Tests

### REST Endpoints
```bash
# Health
curl https://api.richesreach.com/health/

# GraphQL
curl -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```
- [ ] All endpoints responding
- [ ] No 500 errors
- [ ] Appropriate error handling

---

## 7. Sentry Integration Tests

### Mobile App Test
1. Open mobile app
2. Navigate to `sentry-test` screen
3. Tap "Test Error & Message"
- [ ] Error appears in Sentry dashboard
- [ ] Error has stack trace
- [ ] Error has context

### Backend Test
```bash
python manage.py shell
```
```python
import sentry_sdk
sentry_sdk.capture_exception(Exception("Test error from backend"))
print("✅ Test error sent to Sentry")
```
- [ ] Error appears in Sentry
- [ ] Error has proper metadata
- [ ] Environment is "production"

---

## 8. Performance Tests

### Response Times
```bash
# Health endpoint
time curl -s https://api.richesreach.com/health/

# GraphQL endpoint
time curl -s -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```
- [ ] Health: < 1 second
- [ ] GraphQL: < 2 seconds
- [ ] No timeouts

### Load Test (Optional)
```bash
# Simple load test with Apache Bench
ab -n 100 -c 10 https://api.richesreach.com/health/
```
- [ ] Handles concurrent requests
- [ ] No errors under load
- [ ] Response times acceptable

---

## 9. Logs Verification

### CloudWatch Logs
```bash
aws logs tail /ecs/riches-reach-backend --follow --region us-east-1
```
- [ ] Logs accessible
- [ ] No critical errors
- [ ] Application started successfully
- [ ] Database connections logged
- [ ] Redis connections logged (if updated)

### Error Logs
- [ ] No unexpected errors
- [ ] Errors have proper context
- [ ] Sentry integration logging

---

## 10. Security Tests

### SSL/TLS
```bash
curl -I https://api.richesreach.com/health/
```
- [ ] HTTPS working
- [ ] Valid SSL certificate
- [ ] No mixed content warnings

### Security Headers
```bash
curl -I https://api.richesreach.com/health/
```
- [ ] HSTS header present
- [ ] Secure cookies configured
- [ ] CORS configured correctly

### Environment Variables
- [ ] DEBUG=False
- [ ] SECRET_KEY set
- [ ] No secrets in logs
- [ ] API keys configured

---

## 11. Monitoring Verification

### Sentry
- [ ] Errors being captured
- [ ] Performance data collected
- [ ] Alerts configured
- [ ] Dashboard created

### CloudWatch
- [ ] Logs being collected
- [ ] Metrics available
- [ ] Alarms configured (if any)

---

## 12. Mobile App Integration

### API Connection
- [ ] Mobile app can connect to API
- [ ] Authentication works
- [ ] GraphQL queries work
- [ ] No connection errors

### Sentry Mobile
- [ ] Mobile errors appear in Sentry
- [ ] Performance data collected
- [ ] User context included

---

## Test Results Summary

### Infrastructure
- [ ] Health endpoint: ✅ / ❌
- [ ] GraphQL endpoint: ✅ / ❌
- [ ] Database: ✅ / ❌
- [ ] Redis: ✅ / ❌ / N/A
- [ ] Email: ✅ / ❌ / N/A

### Functionality
- [ ] Authentication: ✅ / ❌
- [ ] API endpoints: ✅ / ❌
- [ ] Mobile integration: ✅ / ❌

### Monitoring
- [ ] Sentry: ✅ / ❌
- [ ] Logs: ✅ / ❌
- [ ] Alerts: ✅ / ❌

### Performance
- [ ] Response times: ✅ / ❌
- [ ] Load handling: ✅ / ❌

---

## Issues Found

**List any issues discovered during testing:**

1. 
2. 
3. 

---

## Sign-Off

**Tested By**: _________________  
**Date**: _________________  
**Status**: ✅ Ready for Production / ⚠️ Issues Found

---

**Next Steps After Testing**:
- Fix any issues found
- Re-test fixed issues
- Update documentation
- Proceed with launch

