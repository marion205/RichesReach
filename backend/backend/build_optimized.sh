#!/usr/bin/env bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build platform (use amd64 for ECS deployment)
PLATFORM="linux/amd64"

print_status "Building optimized Docker images for RichesReach..."
echo

# Build Backend (Python/FastAPI)
print_status "Building backend image..."
docker buildx build \
    --platform $PLATFORM \
    --load \
    --progress=plain \
    -t richesreach/backend:dev \
    -f backend/Dockerfile.optimized \
    backend/

print_success "Backend image built successfully"
echo

# Build Streaming Pipeline
print_status "Building streaming pipeline image..."
docker buildx build \
    --platform $PLATFORM \
    --load \
    --progress=plain \
    -t richesreach/streaming:dev \
    -f Dockerfile.streaming.optimized \
    .

print_success "Streaming pipeline image built successfully"
echo

# Build Rust Crypto Engine
print_status "Building Rust crypto engine image..."
docker buildx build \
    --platform $PLATFORM \
    --load \
    --progress=plain \
    -t richesreach/crypto:dev \
    -f rust_crypto_engine/Dockerfile.optimized \
    rust_crypto_engine/

print_success "Rust crypto engine image built successfully"
echo

# Show image sizes
print_status "Image sizes:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep richesreach

print_success "🎉 All optimized images built successfully!"
print_status "Images are ready for deployment to ECS."
