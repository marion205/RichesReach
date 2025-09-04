#!/bin/bash

# Docker Optimization Script for RichesReach AI
# This script optimizes Docker for maximum performance and speed

set -e

echo "🚀 Optimizing Docker for RichesReach AI..."

# 1. Enable Docker BuildKit
echo "⚙️ Enabling Docker BuildKit..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# 2. Clean up Docker system
echo "🧹 Cleaning up Docker system..."
docker system prune -f
docker builder prune -f
docker volume prune -f

# 3. Check disk space
echo "💾 Checking disk space..."
df -h

# 4. Optimize Docker daemon settings
echo "⚙️ Optimizing Docker daemon settings..."
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    }
  }
}
EOF

# 5. Restart Docker daemon (if on Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🔄 Restarting Docker daemon..."
    sudo systemctl restart docker
fi

# 6. Create Docker build cache
echo "📦 Creating Docker build cache..."
docker buildx create --name richesreach-builder --use

echo "✅ Docker optimization completed!"
echo ""
echo "🎯 Optimization Summary:"
echo "   - Docker BuildKit enabled"
echo "   - System cleaned up"
echo "   - Daemon settings optimized"
echo "   - Build cache created"
echo ""
echo "🚀 Ready for fast Docker builds!"
