#!/bin/bash

# Fast Docker Build Script for RichesReach AI
# This script optimizes Docker builds for maximum speed

set -e

echo "🚀 Starting Fast Docker Build for RichesReach AI..."

# Enable Docker BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Clean up Docker to free space
echo "🧹 Cleaning up Docker to free space..."
docker system prune -f
docker builder prune -f

# Check available disk space
echo "💾 Checking disk space..."
df -h

# Build with optimizations
echo "🔨 Building optimized Docker image..."
cd backend

# Use the optimized Dockerfile
docker build \
    --file Dockerfile.optimized \
    --tag richesreach-ai:latest \
    --tag richesreach-ai:$(date +%Y%m%d-%H%M%S) \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    .

echo "✅ Docker build completed successfully!"

# Test the image
echo "🧪 Testing the built image..."
docker run --rm -d --name test-container -p 8000:8000 richesreach-ai:latest

# Wait for service to start
sleep 10

# Test health endpoint
if curl -f http://localhost:8000/health; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    docker logs test-container
    exit 1
fi

# Clean up test container
docker stop test-container

echo "🎉 Fast Docker build and test completed successfully!"
echo "📦 Image: richesreach-ai:latest"
echo "🌐 Ready to deploy!"
