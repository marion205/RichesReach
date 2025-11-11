# Sentry Alerts Setup Guide

## Overview
This guide will help you set up alerts in Sentry to monitor errors, performance issues, and critical events in your RichesReach application.

**Organization**: elite-algorithmics  
**Project**: react-native

---

## Accessing Sentry Dashboard

1. Go to https://sentry.io
2. Log in with your account
3. Navigate to: **elite-algorithmics** → **react-native**

---

## Setting Up Alerts

### 1. Error Alerts

#### Critical Error Alert (High Priority)
**When to trigger**: Any error with severity "error" or "fatal"

**Steps**:
1. Go to **Alerts** → **Create Alert Rule**
2. **Alert Name**: "Critical Errors - Immediate Action"
3. **Conditions**:
   - **When**: An event is seen
   - **Filter**: `level:error OR level:fatal`
   - **Time Window**: Last 5 minutes
   - **Threshold**: 1 event
4. **Actions**:
   - Email: Your email
   - Slack: (if configured)
   - PagerDuty: (if configured)
5. **Save**

#### High Volume Error Alert
**When to trigger**: Multiple errors in a short time

**Steps**:
1. **Alert Name**: "High Volume Errors"
2. **Conditions**:
   - **When**: An event is seen
   - **Filter**: `level:error OR level:fatal`
   - **Time Window**: Last 10 minutes
   - **Threshold**: 10 events
3. **Actions**: Email + Slack
4. **Save**

#### New Error Alert
**When to trigger**: A new error type appears

**Steps**:
1. **Alert Name**: "New Error Types"
2. **Conditions**:
   - **When**: An issue is created
   - **Filter**: `level:error OR level:fatal`
3. **Actions**: Email
4. **Save**

---

### 2. Performance Alerts

#### Slow Transaction Alert
**When to trigger**: Transactions taking too long

**Steps**:
1. Go to **Performance** → **Alerts**
2. **Alert Name**: "Slow Transactions"
3. **Conditions**:
   - **Metric**: Transaction Duration
   - **Threshold**: p95 > 2000ms (2 seconds)
   - **Time Window**: Last 5 minutes
4. **Actions**: Email
5. **Save**

#### High Error Rate Alert
**When to trigger**: Error rate exceeds threshold

**Steps**:
1. **Alert Name**: "High Error Rate"
2. **Conditions**:
   - **Metric**: Error Rate
   - **Threshold**: > 5%
   - **Time Window**: Last 10 minutes
3. **Actions**: Email + Slack
4. **Save**

---

### 3. Release Alerts

#### New Release Alert
**When to trigger**: New release deployed

**Steps**:
1. Go to **Releases** → **Alerts**
2. **Alert Name**: "New Release Deployed"
3. **Conditions**:
   - **When**: A new release is created
4. **Actions**: Email (for tracking)
5. **Save**

#### Release Regression Alert
**When to trigger**: New errors in a release

**Steps**:
1. **Alert Name**: "Release Regression"
2. **Conditions**:
   - **When**: An issue is created
   - **Filter**: `release:latest`
   - **Time Window**: Last 1 hour
   - **Threshold**: 5 new issues
3. **Actions**: Email + Slack
4. **Save**

---

### 4. User Impact Alerts

#### Affected Users Alert
**When to trigger**: Many users affected by an error

**Steps**:
1. **Alert Name**: "High User Impact"
2. **Conditions**:
   - **When**: An issue affects users
   - **Threshold**: > 50 unique users
   - **Time Window**: Last 1 hour
3. **Actions**: Email + Slack
4. **Save**

---

## Recommended Alert Configuration

### Priority Levels

#### 🔴 Critical (Immediate Response)
- Critical Errors (fatal/error)
- High Volume Errors (>10 in 10 min)
- High User Impact (>50 users)

**Notification**: Email + Slack + PagerDuty (if available)

#### 🟡 High (Response within 1 hour)
- New Error Types
- Slow Transactions (p95 > 2s)
- High Error Rate (>5%)

**Notification**: Email + Slack

#### 🟢 Medium (Monitor)
- New Releases
- Performance Degradation
- Low Volume Errors

**Notification**: Email

---

## Setting Up Notification Channels

### Email
1. Go to **Settings** → **Notifications**
2. Add your email address
3. Verify email
4. Configure notification preferences

### Slack Integration
1. Go to **Settings** → **Integrations**
2. Click **Slack**
3. Follow the setup wizard
4. Select channels for alerts
5. Test integration

### PagerDuty Integration (Optional)
1. Go to **Settings** → **Integrations**
2. Click **PagerDuty**
3. Connect your PagerDuty account
4. Configure escalation policies

---

## Alert Rules Summary

| Alert Name | Trigger | Threshold | Priority |
|------------|---------|-----------|---------|
| Critical Errors | Error/Fatal | 1 event / 5 min | 🔴 Critical |
| High Volume Errors | Error/Fatal | 10 events / 10 min | 🔴 Critical |
| New Error Types | New issue | Any | 🟡 High |
| Slow Transactions | p95 duration | > 2000ms | 🟡 High |
| High Error Rate | Error rate | > 5% | 🟡 High |
| Release Regression | New issues | 5 issues / 1 hour | 🟡 High |
| High User Impact | Affected users | > 50 users | 🔴 Critical |
| New Release | New release | Any | 🟢 Medium |

---

## Testing Alerts

### Test Error Alert
1. Use the Sentry Test Button in the app
2. Trigger a test error
3. Verify alert is received within expected time

### Test Performance Alert
1. Use the Sentry Test Button
2. Trigger a performance transaction
3. Verify alert (if threshold exceeded)

---

## Monitoring Dashboard

### Key Metrics to Monitor

1. **Error Rate**: Should be < 1%
2. **Transaction Duration**: p95 should be < 2s
3. **User Impact**: Monitor affected users
4. **Release Health**: Track errors per release

### Creating a Dashboard

1. Go to **Dashboards** → **Create Dashboard**
2. Add widgets:
   - Error Rate Over Time
   - Transaction Duration (p95)
   - Top Errors
   - Affected Users
   - Release Health
3. Save dashboard

---

## Best Practices

1. **Start Conservative**: Begin with fewer alerts, add more as needed
2. **Tune Thresholds**: Adjust based on actual error rates
3. **Use Filters**: Filter out known issues or test environments
4. **Review Regularly**: Review and update alerts monthly
5. **Document**: Keep alert documentation updated

---

## Quick Setup Checklist

- [ ] Set up email notifications
- [ ] Configure Slack integration (optional)
- [ ] Create Critical Error Alert
- [ ] Create High Volume Error Alert
- [ ] Create New Error Type Alert
- [ ] Create Slow Transaction Alert
- [ ] Create High Error Rate Alert
- [ ] Create Release Regression Alert
- [ ] Test alerts with Sentry Test Button
- [ ] Create monitoring dashboard
- [ ] Document alert runbook

---

**Status**: Ready to configure alerts in Sentry dashboard

