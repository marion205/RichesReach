#!/bin/bash

echo "🚀 DEPLOYING RICHESREACH AI TO PRODUCTION AWS"
echo "=============================================="

# Set production environment variables
export ENVIRONMENT=production
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=498606688292

# Production API Keys (from your secret file)
export OPENAI_API_KEY="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"
export OPENAI_MODEL="gpt-4o"
export FINNHUB_API_KEY="d2rnitpr01qv11lfegugd2rnitpr01qfegv0"
export POLYGON_API_KEY="uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2"
export ALPHA_VANTAGE_API_KEY="OHYSFF1AE446O7CR"
export NEWS_API_KEY="94a335c7316145f79840edd62f77e11e"
export WALLETCONNECT_PROJECT_ID="42421cf8-2df7-45c6-9475-df4f4b115ffc"
export ALCHEMY_API_KEY="nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM"
export SEPOLIA_ETH_RPC_URL="https://eth-sepolia.g.alchemy.com/v2/2-rJhszNwQ6I3NuBdN5pz"
export AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID_PLACEHOLDER"
export AWS_SECRET_ACCESS_KEY="5ZT7z1M7ReIDCAKCxWyx9AdM8NrWrZJ2/CHzGWYW"

# Production Database
export DATABASE_URL="postgresql://appuser:@Master22@riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com:5432/postgres"

# Enable all production features
export USE_OPENAI=true
export USE_YODLEE=true
export USE_SBLOC_AGGREGATOR=true
export USE_SBLOC_MOCK=false
export ENABLE_STREAMING=true
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export STREAMING_MODE=true
export DATA_LAKE_BUCKET="riches-reach-ai-datalake-20251005"
export S3_REGION="us-east-1"

echo "✅ Environment variables set for production"

# Build and deploy to AWS ECS
echo "📦 Building Docker image for production..."
cd backend/backend

# Create production Dockerfile
cat > Dockerfile.production << 'DOCKERFILE'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "richesreach.wsgi:application"]
DOCKERFILE

# Build the image
docker build -f Dockerfile.production -t richesreach-ai:production .

echo "✅ Docker image built successfully"

# Tag for ECR
docker tag richesreach-ai:production 498606688292.dkr.ecr.us-east-1.amazonaws.com/richesreach-ai:latest

echo "✅ Image tagged for ECR"

# Push to ECR (you'll need to login first)
echo "📤 Pushing to ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 498606688292.dkr.ecr.us-east-1.amazonaws.com
docker push 498606688292.dkr.ecr.us-east-1.amazonaws.com/richesreach-ai:latest

echo "✅ Image pushed to ECR"

# Update ECS service
echo "🔄 Updating ECS service..."
aws ecs update-service \
    --cluster richesreach-cluster \
    --service richesreach-service \
    --force-new-deployment \
    --region us-east-1

echo "✅ ECS service updated"

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster richesreach-cluster \
    --services richesreach-service \
    --region us-east-1

echo "🎉 DEPLOYMENT COMPLETE!"
echo "🌐 Production URL: http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com"
echo "📊 Monitor at: https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/richesreach-cluster/services"

