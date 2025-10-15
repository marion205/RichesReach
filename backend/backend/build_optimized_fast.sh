#!/usr/bin/env bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Use ARM64 for Apple Silicon (much faster than emulation)
PLATFORM="linux/arm64/v8"

print_status "Building optimized Docker images for RichesReach (ARM64 for speed)..."
echo

# Pre-pull base images to avoid stalls
print_status "Pre-pulling base images..."
docker pull --platform $PLATFORM python:3.11-slim || true
docker pull --platform $PLATFORM rust:1.79-slim || true
echo

# Create buildx builder if it doesn't exist
docker buildx ls >/dev/null 2>&1 || docker buildx create --use --name rr-builder

# Build Backend with proper context and caching
print_status "Building backend image (context: backend/)..."
docker buildx build \
    --file backend/Dockerfile.optimized \
    --platform $PLATFORM \
    --progress=plain \
    --cache-from type=local,src=.buildx-cache-backend \
    --cache-to type=local,dest=.buildx-cache-backend,mode=max \
    -t richesreach-backend:local \
    backend/

print_success "Backend image built successfully"
echo

# Build Rust Engine with proper context and caching
print_status "Building Rust crypto engine image (context: rust_crypto_engine/)..."
docker buildx build \
    --file rust_crypto_engine/Dockerfile.optimized \
    --platform $PLATFORM \
    --progress=plain \
    --cache-from type=local,src=.buildx-cache-rust \
    --cache-to type=local,dest=.buildx-cache-rust,mode=max \
    -t richesreach-rust:local \
    rust_crypto_engine/

print_success "Rust crypto engine image built successfully"
echo

# Build Streaming Pipeline
print_status "Building streaming pipeline image (context: .)..."
docker buildx build \
    --file Dockerfile.streaming.optimized \
    --platform $PLATFORM \
    --progress=plain \
    --cache-from type=local,src=.buildx-cache-streaming \
    --cache-to type=local,dest=.buildx-cache-streaming,mode=max \
    -t richesreach-streaming:local \
    .

print_success "Streaming pipeline image built successfully"
echo

# Show image sizes
print_status "Image sizes:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep richesreach

print_success "🎉 All optimized images built successfully!"
print_status "Images are ready for local testing."
print_warning "Note: These are ARM64 images for local development. Use the original build_optimized.sh for AMD64 production builds."
