# Quick Start Guide for Testing

This guide will help you start the entire RichesReach application for comprehensive testing.

## Prerequisites

- **Docker & Docker Compose**: For PostgreSQL and Redis databases
- **Python 3.10+**: For Django backend
- **Node.js 18+**: For React Native mobile app (optional)
- **Expo CLI**: For mobile development (optional)

## Quick Start

### Option 1: Automated Startup (Recommended)

Run the automated startup script that handles everything:

```bash
./run_full_app.sh
```

This script will:
1. ✅ Start PostgreSQL database (via Docker)
2. ✅ Start Redis cache (via Docker, optional)
3. ✅ Run Django database migrations
4. ✅ Start Django backend server on port 8000
5. ✅ **Automatically start React Native mobile app (Expo)**

### Option 2: Manual Startup

If you prefer to start services manually:

#### 1. Start Databases

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379

#### 2. Start Django Backend

```bash
cd backend/backend

# Activate virtual environment (if exists)
source ../venv/bin/activate

# Run migrations
python3 manage.py migrate --settings=richesreach.settings_local

# Start server
python3 manage.py runserver 127.0.0.1:8000 --settings=richesreach.settings_local
```

#### 3. Start Mobile App

**Option A: Using the startup script (automatically started with `./run_full_app.sh`)**

**Option B: Start mobile app separately**

```bash
# Quick start
./start_mobile.sh

# Or manually
cd mobile
npm start
```

The Expo development server will start and display a QR code that you can scan with the Expo Go app on your phone.

## Services & Ports

Once running, you'll have access to:

| Service | URL | Description |
|---------|-----|-------------|
| Django Backend | http://127.0.0.1:8000 | Main API server |
| GraphQL API | http://127.0.0.1:8000/graphql | GraphQL endpoint |
| Admin Panel | http://127.0.0.1:8000/admin | Django admin |
| Health Check | http://127.0.0.1:8000/health/ | Service health |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache (optional) |
| Expo | http://localhost:8081 | Mobile dev server |

## Testing Endpoints

### Health Check
```bash
curl http://127.0.0.1:8000/health/
```

### GraphQL Query
```bash
curl -X POST http://127.0.0.1:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}'
```

### Test Authentication
```bash
# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## Stopping Services

### Option 1: Use Stop Script
```bash
./stop_full_app.sh
```

### Option 2: Manual Stop

```bash
# Stop Django
pkill -f "manage.py runserver"

# Stop Expo
pkill -f "expo start"

# Stop Docker services
docker-compose down
```

## Troubleshooting

### Port Already in Use

If a port is already in use, the script will prompt you to kill the existing process. Alternatively:

```bash
# Find process using port 8000
lsof -ti:8000

# Kill it
kill -9 $(lsof -ti:8000)
```

### Database Connection Issues

1. Check if PostgreSQL is running:
   ```bash
   docker-compose ps
   ```

2. Check database logs:
   ```bash
   docker-compose logs db
   ```

### Django Migration Errors

If migrations fail:

```bash
cd backend/backend
python3 manage.py makemigrations --settings=richesreach.settings_local
python3 manage.py migrate --settings=richesreach.settings_local
```

### Missing Virtual Environment

Create one:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Missing Dependencies

Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Install mobile dependencies:

```bash
cd mobile
npm install
```

**Note**: The `run_full_app.sh` script will automatically detect missing mobile dependencies and offer to install them.

## Logs

- **Django logs**: `/tmp/django_server.log` (when run via script)
- **Docker logs**: `docker-compose logs`
- **Expo logs**: Shown in terminal or `/tmp/expo_server.log`

## Test Credentials

Default test credentials:
- **Email**: `test@example.com`
- **Password**: `password123`

## Environment Variables

If you need to configure environment variables, create a `.env` file in `backend/backend/`:

```bash
# Database
DATABASE_URL=postgresql://dev:dev@localhost:5432/dev

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
ENABLE_REDIS=1

# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
```

## Testing Mobile App

Once the mobile app is running:

1. **Install Expo Go** on your phone:
   - iOS: [App Store](https://apps.apple.com/app/expo-go/id982107779)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

2. **Scan QR Code**: Open Expo Go and scan the QR code displayed in the terminal

3. **Or Use Simulators**:
   - iOS Simulator: Press `i` in the Expo terminal
   - Android Emulator: Press `a` in the Expo terminal (requires Android Studio)
   - Web Browser: Press `w` in the Expo terminal

4. **Hot Reload**: The app will automatically reload when you make changes

## Next Steps

1. ✅ Verify all services are running
2. ✅ Test API endpoints
3. ✅ Test GraphQL queries
4. ✅ Test mobile app connectivity (scan QR code or use simulator)
5. ✅ Run comprehensive test suite

## Additional Resources

- **Full Documentation**: See [README.md](README.md)
- **API Documentation**: http://127.0.0.1:8000/docs (if available)
- **GraphQL Playground**: http://127.0.0.1:8000/graphql

---

**Happy Testing! 🚀**

