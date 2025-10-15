# Docker Optimization Guide for RichesReach

This guide provides comprehensive Docker optimization for the RichesReach project, including cleanup scripts, optimized Dockerfiles, and deployment configurations.

## 🚀 Quick Start

### 1. Clean Up Existing Docker Environment
```bash
# Run the comprehensive cleanup script
./cleanup_docker.sh
```

### 2. Build Optimized Images
```bash
# Build all optimized images
./build_optimized.sh
```

## 📁 Files Created

### Docker Ignore Files
- `.dockerignore` - Root project dockerignore
- `backend/.dockerignore` - Backend-specific dockerignore
- `rust_crypto_engine/.dockerignore` - Rust engine dockerignore

### Optimized Dockerfiles
- `backend/Dockerfile.optimized` - Multi-stage Python/FastAPI build
- `Dockerfile.streaming.optimized` - Multi-stage streaming pipeline build
- `rust_crypto_engine/Dockerfile.optimized` - Multi-stage Rust build with distroless runtime

### Scripts
- `cleanup_docker.sh` - Comprehensive Docker cleanup script
- `build_optimized.sh` - Optimized build script for all services

### ECS Configuration
- `ecs_task_definition_optimized.json` - Optimized ECS task definition

## 🧹 Cleanup Script Features

The `cleanup_docker.sh` script provides:

1. **Safe Cleanup Steps**:
   - Stop running containers and Docker Compose stacks
   - Remove stopped containers and dangling images
   - Clean build caches

2. **Deep Cleanup**:
   - Remove all unused images
   - Clean all build caches
   - Remove caches older than 7 days

3. **Optional Volume Cleanup**:
   - Interactive prompt for volume removal
   - Lists volumes before removal

4. **Disk Usage Monitoring**:
   - Shows Docker system usage before/after
   - Checks Docker.raw file size

## 🏗️ Optimized Dockerfiles

### Backend (Python/FastAPI)
- **Multi-stage build** with separate dependency and runtime stages
- **Wheel-based installation** for faster builds
- **Minimal runtime image** with only necessary dependencies
- **Non-root user** for security
- **Health checks** included

### Streaming Pipeline
- **Multi-stage build** optimized for streaming workloads
- **Selective file copying** to minimize image size
- **Python 3.11** for better performance
- **Minimal runtime dependencies**

### Rust Crypto Engine
- **Multi-stage build** with separate build and runtime stages
- **Distroless runtime** for minimal attack surface
- **Dependency caching** for faster rebuilds
- **Static binary** for maximum portability

## 🚀 Build Optimization

### Environment Variables
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Build Commands
```bash
# Backend
docker buildx build --platform linux/amd64 --load --progress=plain \
  -t richesreach/backend:dev -f backend/Dockerfile.optimized backend/

# Streaming Pipeline
docker buildx build --platform linux/amd64 --load --progress=plain \
  -t richesreach/streaming:dev -f Dockerfile.streaming.optimized .

# Rust Crypto Engine
docker buildx build --platform linux/amd64 --load --progress=plain \
  -t richesreach/crypto:dev -f rust_crypto_engine/Dockerfile.optimized rust_crypto_engine/
```

## 📊 Expected Results

### Space Savings
- **10-60+ GB** freed from Docker cleanup
- **50-80% smaller** images with multi-stage builds
- **Faster builds** with better caching

### Performance Improvements
- **Faster container startup** with minimal runtime images
- **Reduced memory usage** with optimized configurations
- **Better security** with non-root users and distroless images

## 🔧 ECS Optimization

The optimized ECS task definition includes:

- **Reduced resource allocation** (1024 CPU, 2048 memory)
- **Memory reservation** for better resource management
- **Secrets management** instead of environment variables
- **Optimized logging** configuration
- **Health checks** and timeouts
- **File descriptor limits** for high-throughput workloads

## 🛠️ Maintenance

### Regular Cleanup
Run the cleanup script weekly:
```bash
./cleanup_docker.sh
```

### Build Cache Management
```bash
# Clean caches older than 7 days
docker builder prune -af --filter 'until=168h'

# Clean all build caches
docker builder prune -af
```

### Docker Desktop Optimization
1. **Docker Desktop → Troubleshoot → Clean / Purge data**
2. **Docker Desktop → Settings → Resources → Advanced → "Reclaim disk space"**
3. **Resize disk image** if oversized

## 🔍 Troubleshooting

### Common Issues

1. **Build failures**: Ensure all dependencies are in requirements files
2. **Permission errors**: Check file ownership and permissions
3. **Large images**: Verify .dockerignore files are working
4. **Slow builds**: Enable BuildKit and use multi-stage builds

### Monitoring
```bash
# Check Docker system usage
docker system df -v

# Check build cache usage
docker buildx du

# Check Docker.raw size
du -sh ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw
```

## 📈 Performance Metrics

### Before Optimization
- Large monolithic images
- Slow build times
- High disk usage
- Security concerns

### After Optimization
- Multi-stage builds
- Faster build times
- Reduced disk usage
- Enhanced security
- Better resource utilization

## 🎯 Next Steps

1. **Run cleanup script** to free space
2. **Build optimized images** for testing
3. **Deploy to ECS** using optimized task definition
4. **Monitor performance** and adjust as needed
5. **Set up regular cleanup** schedule

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-stage Builds](https://docs.docker.com/develop/dev-best-practices/dockerfile_best-practices/#use-multi-stage-builds)
- [ECS Task Definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
- [BuildKit](https://docs.docker.com/build/buildkit/)
