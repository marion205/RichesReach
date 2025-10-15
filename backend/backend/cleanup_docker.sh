#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get disk usage
get_disk_usage() {
    if command -v docker &> /dev/null; then
        docker system df -v 2>/dev/null || echo "Docker not running or not accessible"
    else
        echo "Docker not installed"
    fi
}

# Function to check Docker.raw size
check_docker_raw_size() {
    local docker_raw_path="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
    if [[ -f "$docker_raw_path" ]]; then
        local size=$(du -sh "$docker_raw_path" 2>/dev/null | cut -f1)
        echo "Docker.raw size: $size"
    else
        echo "Docker.raw not found (Docker Desktop may not be installed)"
    fi
}

# Main cleanup function
main() {
    echo "=========================================="
    echo "🐳 Docker Cleanup Script for RichesReach"
    echo "=========================================="
    echo

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi

    print_status "Starting Docker cleanup process..."
    echo

    # Show initial state
    print_status "=== BEFORE CLEANUP ==="
    get_disk_usage
    echo
    check_docker_raw_size
    echo

    # Stop running containers and stacks
    print_status "Stopping running containers and stacks..."
    if docker compose down --remove-orphans 2>/dev/null; then
        print_success "Docker Compose stacks stopped"
    else
        print_warning "No Docker Compose stacks found or already stopped"
    fi

    # Stop all running containers
    local running_containers=$(docker ps -q)
    if [[ -n "$running_containers" ]]; then
        print_status "Stopping running containers..."
        docker stop $running_containers
        print_success "All running containers stopped"
    else
        print_status "No running containers to stop"
    fi

    echo

    # Safe cleanup - containers and dangling images
    print_status "Pruning stopped containers and dangling images..."
    docker container prune -f || print_warning "Failed to prune containers"
    docker image prune -f || print_warning "Failed to prune dangling images"
    docker builder prune -f || print_warning "Failed to prune build cache"
    print_success "Safe cleanup completed"

    echo

    # Deeper cleanup - unused images and build caches
    print_status "Performing deeper cleanup (unused images and build caches)..."
    docker image prune -a -f || print_warning "Failed to prune unused images"
    docker builder prune -af || print_warning "Failed to prune all build caches"
    print_success "Deep cleanup completed"

    echo

    # Optional: Clean old caches (older than 7 days)
    print_status "Cleaning build caches older than 7 days..."
    docker builder prune -af --filter 'until=168h' || print_warning "Failed to prune old caches"
    print_success "Old cache cleanup completed"

    echo

    # Volume cleanup (with warning)
    print_warning "⚠️  VOLUME CLEANUP - This will remove ALL unused volumes!"
    print_warning "This includes databases and persistent data. Only proceed if you're sure."
    echo
    read -p "Do you want to remove unused volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Listing current volumes..."
        docker volume ls
        echo
        print_status "Removing unused volumes..."
        docker volume prune -f || print_warning "Failed to prune volumes"
        print_success "Volume cleanup completed"
    else
        print_status "Skipping volume cleanup"
    fi

    echo

    # Show final state
    print_status "=== AFTER CLEANUP ==="
    get_disk_usage
    echo
    check_docker_raw_size
    echo

    # Additional cleanup suggestions
    print_status "=== ADDITIONAL CLEANUP SUGGESTIONS ==="
    echo "If you still need more space, consider:"
    echo "1. Docker Desktop → Troubleshoot → Clean / Purge data"
    echo "2. Docker Desktop → Settings → Resources → Advanced → 'Reclaim disk space'"
    echo "3. Resize Docker Desktop disk image if oversized"
    echo

    # Build optimization tips
    print_status "=== BUILD OPTIMIZATION TIPS ==="
    echo "For future builds, use these optimized commands:"
    echo
    echo "# Backend (Python/FastAPI):"
    echo "export DOCKER_BUILDKIT=1"
    echo "docker buildx build --platform linux/amd64 --load --progress=plain \\"
    echo "  -t richesreach/backend:dev -f backend/Dockerfile.optimized backend/"
    echo
    echo "# Streaming Pipeline:"
    echo "docker buildx build --platform linux/amd64 --load --progress=plain \\"
    echo "  -t richesreach/streaming:dev -f Dockerfile.streaming.optimized ."
    echo
    echo "# Rust Crypto Engine:"
    echo "docker buildx build --platform linux/amd64 --load --progress=plain \\"
    echo "  -t richesreach/crypto:dev -f rust_crypto_engine/Dockerfile.optimized rust_crypto_engine/"
    echo

    print_success "🎉 Docker cleanup completed successfully!"
    print_status "Your Docker environment is now optimized for faster, smaller builds."
}

# Run the main function
main "$@"
