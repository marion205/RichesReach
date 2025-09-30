#!/bin/bash

# Final Production Deployment Script
set -e

echo "🚀 RichesReach Final Production Deployment"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
PROJECT_NAME="richesreach-backend"
DOCKER_IMAGE="richesreach-backend:production"
CONTAINER_NAME="richesreach-backend-prod"

# Check prerequisites
log_info "Checking prerequisites..."

if [ ! -f "env.production.final" ]; then
    log_error "env.production.final not found. Please create it first."
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build production image
log_info "Building production Docker image..."
docker build -f Dockerfile.production -t $DOCKER_IMAGE .

if [ $? -ne 0 ]; then
    log_error "Docker build failed"
    exit 1
fi

# Stop existing container
if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
    log_info "Stopping existing container..."
    docker stop $CONTAINER_NAME
fi

if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
    log_info "Removing existing container..."
    docker rm $CONTAINER_NAME
fi

# Run database migrations (if needed)
log_info "Running database migrations..."
docker run --rm \
    --env-file env.production.final \
    -v $(pwd)/logs:/app/logs \
    $DOCKER_IMAGE \
    python manage.py migrate --noinput || log_warn "Migration failed, continuing..."

# Start production container
log_info "Starting production container..."
docker run -d \
    --name $CONTAINER_NAME \
    --env-file env.production.final \
    -p 8000:8000 \
    -v $(pwd)/logs:/app/logs \
    --restart unless-stopped \
    --health-cmd="curl -fsS http://localhost:8000/live/ || exit 1" \
    --health-interval=30s \
    --health-timeout=5s \
    --health-retries=3 \
    --health-start-period=60s \
    $DOCKER_IMAGE

# Wait for container to start
log_info "Waiting for container to start..."
sleep 15

# Comprehensive health checks
log_info "Running comprehensive health checks..."

# Liveness check
if curl -fsS http://localhost:8000/live/ > /dev/null 2>&1; then
    log_info "✅ Liveness check passed"
else
    log_error "❌ Liveness check failed"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Readiness check
if curl -fsS http://localhost:8000/ready/ > /dev/null 2>&1; then
    log_info "✅ Readiness check passed"
else
    log_error "❌ Readiness check failed"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Health check
if curl -fsS http://localhost:8000/health/ > /dev/null 2>&1; then
    log_info "✅ Health check passed"
else
    log_error "❌ Health check failed"
    docker logs $CONTAINER_NAME
    exit 1
fi

# AI Options API test
log_info "Testing AI Options API..."
if curl -fsS -X POST http://localhost:8000/api/ai-options/recommendations \
    -H "Content-Type: application/json" \
    -d '{"symbol":"AAPL","portfolio_value":10000,"user_risk_tolerance":"medium","time_horizon":30}' \
    > /dev/null 2>&1; then
    log_info "✅ AI Options API test passed"
else
    log_error "❌ AI Options API test failed"
    docker logs $CONTAINER_NAME
    exit 1
fi

# GraphQL test
log_info "Testing GraphQL API..."
if curl -fsS http://localhost:8000/graphql/ \
    -H "Content-Type: application/json" \
    -d '{"query":"{ quotes(symbols:[\"AAPL\"]){ symbol last changePct } }"}' \
    > /dev/null 2>&1; then
    log_info "✅ GraphQL API test passed"
else
    log_error "❌ GraphQL API test failed"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Cache status test
log_info "Testing cache status..."
if curl -fsS http://localhost:8000/api/cache-status > /dev/null 2>&1; then
    log_info "✅ Cache status test passed"
else
    log_error "❌ Cache status test failed"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Show final status
log_info "🎉 Production deployment completed successfully!"
log_info "Container status:"
docker ps -f name=$CONTAINER_NAME

log_info "📊 Service endpoints:"
log_info "  Health: http://localhost:8000/health/"
log_info "  Live: http://localhost:8000/live/"
log_info "  Ready: http://localhost:8000/ready/"
log_info "  GraphQL: http://localhost:8000/graphql/"
log_info "  AI Options: http://localhost:8000/api/ai-options/recommendations"
log_info "  Cache Status: http://localhost:8000/api/cache-status"

log_info "📝 Recent logs:"
docker logs --tail 20 $CONTAINER_NAME

log_info "🚀 Your RichesReach backend is now production-ready!"
