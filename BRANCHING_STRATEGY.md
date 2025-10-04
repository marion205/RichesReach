# RichesReach Branching Strategy

## Branch Overview

### 🌟 `main` (Production)
- **Purpose**: Production-ready code for app store releases
- **Environment**: Production servers, app stores
- **Configuration**: Production API endpoints, optimized builds
- **Deployment**: Automatic deployment to production

### 🛠️ `development` (Local Development)
- **Purpose**: Local development with mock data and test servers
- **Environment**: Local development, testing, screenshots
- **Configuration**: Mock APIs, test servers, development endpoints
- **Features**: 
  - Mock GraphQL server with comprehensive test data
  - Local development API configuration
  - Error handling with mock fallbacks
  - Debug logging and development tools

## Workflow

### For Local Development
```bash
git checkout development
# Make your changes
git add .
git commit -m "feat: your development changes"
git push origin development
```

### For Production Releases
```bash
git checkout main
git merge development
# Review and test production changes
git push origin main
# Deploy to production
```

## Key Differences

| Feature | Development Branch | Main Branch |
|---------|-------------------|-------------|
| **API Endpoints** | Mock/test servers | Production APIs |
| **Data Source** | Mock data | Real ML/AI data |
| **Error Handling** | Mock fallbacks | Production error handling |
| **Logging** | Debug logging | Production logging |
| **Configuration** | Local development | Production environment |
| **Testing** | Mock data testing | Real data testing |

## Development Features (development branch only)

- ✅ **Mock GraphQL Server**: Complete API simulation
- ✅ **Stock Data**: 5 mock stocks with ML scoring
- ✅ **AI Recommendations**: Mock AI analysis
- ✅ **Trading Data**: Mock account, positions, orders
- ✅ **Error Fallbacks**: Graceful degradation
- ✅ **Local Configuration**: Development API endpoints

## Production Features (main branch)

- ✅ **Real APIs**: Production GraphQL endpoints
- ✅ **ML/AI Integration**: Real machine learning models
- ✅ **Database**: Production PostgreSQL
- ✅ **Authentication**: Production auth system
- ✅ **Monitoring**: Production logging and monitoring
- ✅ **Security**: Production security measures

## Quick Start

### Switch to Development
```bash
git checkout development
cd backend/backend
source ../.venv/bin/activate
python3 working_test_server.py
```

### Switch to Production
```bash
git checkout main
# Follow production deployment guide
```

## Notes

- Always test changes in `development` branch first
- Use `development` branch for screenshots and demos
- Only merge to `main` when ready for production release
- Keep development-specific files only in `development` branch
