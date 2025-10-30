#!/bin/bash

# Production Deployment Script for RichesReach Backend
set -e

echo "🚀 Starting RichesReach Backend Production Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="richesreach-backend"
DOCKER_IMAGE="richesreach-backend:latest"
CONTAINER_NAME="richesreach-backend-prod"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please do not run this script as root"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    log_warn ".env.production not found. Creating from template..."
    if [ -f "env.production.template" ]; then
        cp env.production.template .env.production
        log_warn "Please update .env.production with your actual values before deploying"
        exit 1
    else
        log_error "No environment template found. Please create .env.production manually."
        exit 1
    fi
fi

# Build Docker image
log_info "Building Docker image..."
docker build -f Dockerfile.production -t $DOCKER_IMAGE .

if [ $? -ne 0 ]; then
    log_error "Docker build failed"
    exit 1
fi

# Stop existing container if running
if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
    log_info "Stopping existing container..."
    docker stop $CONTAINER_NAME
fi

# Remove existing container if exists
if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
    log_info "Removing existing container..."
    docker rm $CONTAINER_NAME
fi

# Run database migrations
log_info "Running database migrations..."
docker run --rm \
    --env-file .env.production \
    -v $(pwd)/logs:/app/logs \
    $DOCKER_IMAGE \
    python manage.py migrate --noinput

# Start new container
log_info "Starting production container..."
docker run -d \
    --name $CONTAINER_NAME \
    --env-file .env.production \
    -p 8000:8000 \
    -v $(pwd)/logs:/app/logs \
    --restart unless-stopped \
    $DOCKER_IMAGE

# Wait for container to start
log_info "Waiting for container to start..."
sleep 10

# Health check
log_info "Performing health check..."
if curl -f http://process.env.API_BASE_URL || "localhost:8000"/health/ > /dev/null 2>&1; then
    log_info "✅ Health check passed!"
else
    log_error "❌ Health check failed!"
    log_info "Container logs:"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Show container status
log_info "Container status:"
docker ps -f name=$CONTAINER_NAME

log_info "🎉 Deployment completed successfully!"
log_info "Backend is running at: http://process.env.API_BASE_URL || "localhost:8000""
log_info "Health check: http://process.env.API_BASE_URL || "localhost:8000"/health/"
log_info "API docs: http://process.env.API_BASE_URL || "localhost:8000"/graphql/"

# Show logs
log_info "Recent logs:"
docker logs --tail 20 $CONTAINER_NAME
