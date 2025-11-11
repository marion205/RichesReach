#!/bin/bash
# RichesReach Deployment Execution Script
# Guides through deployment process

set -e

echo "🚀 RichesReach Deployment Execution"
echo "===================================="
echo ""

# Step 1: Review Environment
echo "📋 Step 1: Review Environment Configuration"
echo "   ✅ Review complete - see ENV_REVIEW_REPORT.md"
echo ""

# Step 2: Check Redis
echo "📋 Step 2: Redis Configuration"
read -p "Do you have an ElastiCache endpoint? (y/n): " HAS_REDIS
if [ "$HAS_REDIS" = "y" ]; then
  read -p "Enter ElastiCache endpoint: " REDIS_ENDPOINT
  echo "Updating .env with Redis endpoint..."
  cd deployment_package/backend
  sed -i.bak "s|REDIS_HOST=localhost|REDIS_HOST=$REDIS_ENDPOINT|" .env
  sed -i.bak "s|CELERY_BROKER_URL=redis://localhost|CELERY_BROKER_URL=redis://$REDIS_ENDPOINT|" .env
  sed -i.bak "s|CELERY_RESULT_BACKEND=redis://localhost|CELERY_RESULT_BACKEND=redis://$REDIS_ENDPOINT|" .env
  echo "✅ Redis endpoint updated"
  cd ../..
else
  echo "⚠️  Keeping localhost for now. Update after ElastiCache is created."
fi
echo ""

# Step 3: Deploy
echo "📋 Step 3: Deploy Application"
echo "Choose deployment method:"
echo "1) Quick deploy (deploy_backend.sh)"
echo "2) Full deploy (deploy.sh)"
echo "3) Manual deployment"
read -p "Enter choice (1-3): " DEPLOY_CHOICE

case $DEPLOY_CHOICE in
  1)
    echo "Running quick backend deployment..."
    ./deploy_backend.sh
    ;;
  2)
    echo "Running full deployment..."
    ./deploy.sh
    ;;
  3)
    echo "See DEPLOYMENT_GUIDE.md for manual steps"
    exit 0
    ;;
esac

echo ""
echo "✅ Deployment initiated!"
echo ""

# Step 4: Verify
echo "📋 Step 4: Verify Deployment"
read -p "Wait for deployment to complete, then press Enter to verify..."
echo "Testing health endpoint..."
curl -f https://api.richesreach.com/health/ || curl -f http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/health/
echo ""
echo "✅ Health check complete"
echo ""

# Step 5: Sentry Alerts
echo "📋 Step 5: Set Up Sentry Alerts"
echo "   See MONITORING_SETUP.md for detailed instructions"
echo "   Quick setup:"
echo "   1. Go to https://sentry.io"
echo "   2. Navigate to: elite-algorithmics → react-native"
echo "   3. Create 'Critical Errors' alert"
echo "   4. Create 'High Volume Errors' alert"
echo ""

echo "🎉 Deployment Process Complete!"
echo ""
echo "Next steps:"
echo "  - Monitor deployment in AWS Console"
echo "  - Set up Sentry alerts"
echo "  - Test application endpoints"
echo ""
