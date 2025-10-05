# Phase 3 Deployment Guide

This document provides comprehensive instructions for deploying Phase 3 components of RichesReach, including AI Router, Advanced Analytics, Performance Optimization, and Multi-region deployment.

---

## 🚀 **Phase 3 Deployment Overview**

### **Components Deployed**
- ✅ **AI Router** - Multi-model AI routing with GPT-4, Claude, and Gemini
- ✅ **Advanced Analytics** - Real-time business intelligence and market analytics
- ✅ **Performance Optimization** - Advanced caching, CDN, and database optimization
- ✅ **Multi-region Infrastructure** - Global deployment with edge computing
- ✅ **Advanced AI Integration** - GPT-5, Claude 3.5, and multi-model orchestration

---

## 📋 **Prerequisites**

### **Required Tools**
```bash
# AWS CLI
aws --version

# Docker
docker --version

# Python 3.10+
python3 --version

# jq (for JSON processing)
jq --version
```

### **AWS Permissions**
Your AWS user/role needs the following permissions:
- ECS (Elastic Container Service)
- ECR (Elastic Container Registry)
- CloudFormation
- IAM
- CloudWatch
- Route 53
- CloudFront
- Secrets Manager

### **Environment Setup**
1. **AWS Credentials**: Configure AWS CLI with your credentials
2. **Environment Variables**: Copy and configure `phase3.env.template`
3. **Dependencies**: Install required Python packages

---

## 🔧 **Configuration**

### **1. Environment Configuration**

Copy the environment template:
```bash
cp phase3.env.template .env
```

Edit `.env` with your actual values:
```bash
# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# Database Configuration
DATABASE_HOST=your_database_host_here
DATABASE_PASSWORD=your_database_password_here

# Redis Configuration
REDIS_HOST=your_redis_host_here
REDIS_PASSWORD=your_redis_password_here

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
CLOUDFRONT_DISTRIBUTION_ID=your_cloudfront_distribution_id_here
```

### **2. Configuration Validation**

Validate your configuration:
```bash
python3 phase3_config.py --load-env --validate
```

Create a configuration file:
```bash
python3 phase3_config.py --create-default phase3_config.yaml
```

---

## 🚀 **Deployment Process**

### **Step 1: Automated Deployment**

Run the automated deployment script:
```bash
./deploy_phase3.sh
```

This script will:
1. ✅ Check prerequisites and AWS credentials
2. ✅ Build and push Docker image to ECR
3. ✅ Create Phase 3 task definition
4. ✅ Update ECS service
5. ✅ Run health checks
6. ✅ Provide deployment summary

### **Step 2: Manual Deployment (Alternative)**

If you prefer manual deployment:

#### **Build and Push Docker Image**
```bash
# Build image
docker build -f Dockerfile.prod -t richesreach:phase3 .

# Tag for ECR
docker tag richesreach:phase3 $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/richesreach:phase3

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/richesreach:phase3
```

#### **Update ECS Service**
```bash
# Register new task definition
aws ecs register-task-definition --cli-input-json file://phase3-task-definition.json

# Update service
aws ecs update-service \
    --cluster richesreach-cluster \
    --service richesreach-service \
    --task-definition richesreach:phase3 \
    --force-new-deployment
```

---

## 🧪 **Testing and Validation**

### **1. Offline Component Testing**

Test Phase 3 components without running server:
```bash
python3 test_phase3_offline.py
```

Expected output:
```
📊 Test Results Summary
Total Tests: 24
Passed: 21
Failed: 3 (missing dependencies)
Success Rate: 87.5%
```

### **2. Online Integration Testing**

Test with running server:
```bash
# Start server
cd backend && python3 -m uvicorn backend.final_complete_server:app --host 0.0.0.0 --port 8000

# Run tests (in another terminal)
python3 test_phase3.py --url http://localhost:8000
```

### **3. Health Checks**

Run comprehensive health checks:
```bash
python3 health_check_phase3.py --url http://localhost:8000
```

Expected health check results:
```
📊 Health Check Summary
Total Components: 9
Healthy: 9
Degraded: 0
Unhealthy: 0
Health Score: 100.0%
```

---

## 📊 **Monitoring and Observability**

### **1. Health Endpoints**

Monitor system health:
```bash
# Basic health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed

# Performance metrics
curl http://localhost:8000/performance/metrics

# Analytics status
curl http://localhost:8000/analytics/status

# AI Router status
curl http://localhost:8000/ai-router/status
```

### **2. Performance Monitoring**

Monitor performance metrics:
```bash
# Cache performance
curl http://localhost:8000/performance/metrics/cache

# CDN performance
curl http://localhost:8000/performance/metrics/cdn

# Database performance
curl http://localhost:8000/performance/metrics/database
```

### **3. CloudWatch Integration**

Monitor in AWS CloudWatch:
- ECS service metrics
- Application logs
- Performance metrics
- Error rates

---

## 🌍 **Multi-Region Deployment**

### **1. Infrastructure Setup**

Deploy multi-region infrastructure:
```bash
# Deploy to primary region (us-east-1)
cd infrastructure
terraform init
terraform plan -var="region=us-east-1"
terraform apply

# Deploy to secondary regions
terraform plan -var="region=eu-west-1"
terraform apply

terraform plan -var="region=ap-southeast-1"
terraform apply
```

### **2. Route 53 Configuration**

Configure global routing:
```bash
# Create latency-based routing
aws route53 create-health-check --caller-reference phase3-health-check

# Update DNS records for global routing
aws route53 change-resource-record-sets --hosted-zone-id YOUR_ZONE_ID --change-batch file://route53-changes.json
```

### **3. CloudFront Distribution**

Configure global CDN:
```bash
# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json

# Update distribution settings
aws cloudfront update-distribution --id YOUR_DISTRIBUTION_ID --distribution-config file://updated-config.json
```

---

## 🔒 **Security Configuration**

### **1. Secrets Management**

Store sensitive data in AWS Secrets Manager:
```bash
# Store API keys
aws secretsmanager create-secret --name "richesreach/openai-api-key" --secret-string "your_openai_key"

aws secretsmanager create-secret --name "richesreach/anthropic-api-key" --secret-string "your_anthropic_key"

aws secretsmanager create-secret --name "richesreach/database-url" --secret-string "postgresql://user:pass@host:port/db"
```

### **2. IAM Roles**

Create necessary IAM roles:
```bash
# ECS Task Execution Role
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://ecs-trust-policy.json

# ECS Task Role
aws iam create-role --role-name ecsTaskRole --assume-role-policy-document file://ecs-trust-policy.json
```

### **3. Network Security**

Configure security groups:
```bash
# Application security group
aws ec2 create-security-group --group-name richesreach-app-sg --description "RichesReach Application Security Group"

# Database security group
aws ec2 create-security-group --group-name richesreach-db-sg --description "RichesReach Database Security Group"
```

---

## 📈 **Performance Optimization**

### **1. Cache Configuration**

Optimize caching:
```bash
# Configure Redis cluster
aws elasticache create-cache-cluster --cache-cluster-id richesreach-redis --engine redis --cache-node-type cache.t3.micro

# Update cache settings
curl -X POST http://localhost:8000/performance/cache/clear
curl -X POST http://localhost:8000/performance/cache/preload -d '{"keys": ["popular_data"]}'
```

### **2. CDN Optimization**

Optimize CDN:
```bash
# Invalidate CDN cache
curl -X POST http://localhost:8000/performance/cdn/invalidate -d '{"paths": ["/api/stocks", "/api/portfolio"]}'

# Preload CDN cache
curl -X POST http://localhost:8000/performance/cdn/preload -d '{"paths": ["/api/market/overview"]}'
```

### **3. Database Optimization**

Optimize database:
```bash
# Analyze slow queries
curl http://localhost:8000/performance/database/slow-queries

# Get query metrics
curl http://localhost:8000/performance/database/query-metrics

# Optimize specific query
curl -X POST http://localhost:8000/performance/database/optimize-query -d '{"query": "SELECT * FROM stocks WHERE symbol = ?"}'
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Server Won't Start**
```bash
# Check logs
docker logs richesreach-container

# Check dependencies
pip install -r requirements.production.txt

# Check configuration
python3 phase3_config.py --validate
```

#### **2. Health Checks Failing**
```bash
# Run health check
python3 health_check_phase3.py --verbose

# Check individual components
curl http://localhost:8000/health/detailed
```

#### **3. Performance Issues**
```bash
# Check performance metrics
curl http://localhost:8000/performance/metrics

# Check cache status
curl http://localhost:8000/performance/metrics/cache

# Check database performance
curl http://localhost:8000/performance/metrics/database
```

### **Log Analysis**

Check application logs:
```bash
# ECS logs
aws logs describe-log-groups --log-group-name-prefix /ecs/richesreach

# Application logs
aws logs get-log-events --log-group-name /ecs/richesreach --log-stream-name ecs/richesreach-service
```

---

## 📚 **API Documentation**

### **Phase 3 Endpoints**

#### **AI Router**
- `GET /ai-router/status` - AI Router status
- `GET /ai-router/models` - Available AI models
- `POST /ai-router/route` - Route request to AI model

#### **Advanced Analytics**
- `GET /analytics/status` - Analytics status
- `GET /analytics/dashboards` - Available dashboards
- `GET /analytics/metrics` - Analytics metrics
- `WebSocket /ws/analytics/dashboard` - Real-time dashboard

#### **Performance Optimization**
- `GET /performance/metrics` - Performance metrics
- `GET /performance/health` - Performance health
- `POST /performance/cache/operation` - Cache operations
- `POST /performance/cdn/invalidate` - CDN invalidation

#### **Advanced AI Integration**
- `GET /advanced-ai/status` - Advanced AI status
- `GET /advanced-ai/models` - Advanced AI models
- `POST /advanced-ai/analyze` - Advanced AI analysis

#### **AI Training**
- `GET /ai-training/status` - Training status
- `POST /ai-training/start` - Start training job
- `GET /ai-training/jobs` - List training jobs

---

## 🎯 **Success Metrics**

### **Performance Targets**
- **API Response Time**: < 200ms globally
- **Cache Hit Rate**: > 95%
- **Database Query Time**: < 50ms
- **Global Latency**: < 100ms
- **Uptime**: 99.9%

### **Monitoring Dashboard**
Access the monitoring dashboard at:
- **Local**: http://localhost:8000/analytics/dashboard
- **Production**: https://api.richesreach.com/analytics/dashboard

---

## 🔄 **Rollback Procedures**

### **Emergency Rollback**
```bash
# Rollback to previous task definition
aws ecs update-service \
    --cluster richesreach-cluster \
    --service richesreach-service \
    --task-definition richesreach:previous-version

# Rollback CloudFront
aws cloudfront update-distribution \
    --id YOUR_DISTRIBUTION_ID \
    --distribution-config file://previous-cloudfront-config.json
```

### **Gradual Rollback**
```bash
# Reduce traffic to new version
aws ecs update-service \
    --cluster richesreach-cluster \
    --service richesreach-service \
    --desired-count 1

# Monitor for issues
python3 health_check_phase3.py --url https://api.richesreach.com
```

---

## 📞 **Support and Maintenance**

### **Regular Maintenance**
- **Daily**: Health checks and performance monitoring
- **Weekly**: Cache optimization and CDN analysis
- **Monthly**: Security updates and dependency updates
- **Quarterly**: Performance optimization and capacity planning

### **Support Contacts**
- **Technical Issues**: Check logs and run health checks
- **Performance Issues**: Monitor metrics and optimize
- **Security Issues**: Review IAM roles and secrets

---

## ✅ **Deployment Checklist**

### **Pre-Deployment**
- [ ] Environment variables configured
- [ ] AWS credentials set up
- [ ] Dependencies installed
- [ ] Configuration validated
- [ ] Tests passing

### **Deployment**
- [ ] Docker image built and pushed
- [ ] ECS task definition updated
- [ ] ECS service updated
- [ ] Health checks passing
- [ ] Performance metrics normal

### **Post-Deployment**
- [ ] All endpoints responding
- [ ] AI Router functional
- [ ] Analytics working
- [ ] Performance optimization active
- [ ] Monitoring configured
- [ ] Documentation updated

---

**🎉 Phase 3 Deployment Complete!**

Your RichesReach application now includes:
- ✅ Advanced AI Router with multi-model support
- ✅ Real-time analytics and business intelligence
- ✅ Performance optimization with caching and CDN
- ✅ Multi-region deployment infrastructure
- ✅ Comprehensive monitoring and health checks

The system is now ready for production use with enterprise-grade performance and reliability! 🚀
