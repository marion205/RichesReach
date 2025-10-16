# 🚀 Local Development with Production Database

This setup allows you to test fixes locally using your production database, eliminating the need to push to production for every test.

## 📋 Quick Setup

### 1. Get Your Production Database Credentials

You'll need these from your production environment:
- Database host
- Database password
- Secret key

### 2. Create Environment File

```bash
cd backend/backend/backend/backend
cp env.local.template .env.local
```

Edit `.env.local` and fill in your production database credentials:

```bash
# Database Configuration
DJANGO_DB_NAME=appdb
DJANGO_DB_USER=appuser
DJANGO_DB_PASSWORD=your_actual_production_password
DJANGO_DB_HOST=your_actual_production_host
DJANGO_DB_PORT=5432
SSLMODE=require

# Django Configuration
SECRET_KEY=your_actual_production_secret_key
```

### 3. Start Local Development Server

```bash
cd backend/backend/backend/backend
python3 run_local_dev.py
```

The server will start at `http://localhost:8000`

### 4. Update Mobile App to Use Local Server

Update your mobile app's Apollo configuration to use:
```typescript
const getGraphQLURL = () => {
  if (__DEV__) {
    return 'http://YOUR_LOCAL_IP:8000/graphql/';  // Your computer's IP
  }
  return 'http://54.160.139.56:8000/graphql/';  // Production
};
```

## 🧪 Testing Workflow

1. **Make changes** to your backend code
2. **Test locally** - changes are instant, no deployment needed
3. **Verify fixes** work with real production data
4. **Deploy to production** only when everything works

## 🔧 Benefits

- ✅ **Instant testing** - no waiting for deployments
- ✅ **Real data** - test with actual production database
- ✅ **Debug mode** - better error messages and stack traces
- ✅ **Fast iteration** - make changes and test immediately
- ✅ **Safe testing** - no risk of breaking production

## 🚨 Important Notes

- **Read-only recommended** - be careful with database writes
- **Use test data** when possible for destructive operations
- **Keep credentials secure** - don't commit `.env.local` to git

## 🐛 Debugging

If you see the error `Cannot query field 'addToWatchlist' on type 'Mutation'`:

1. **Check GraphQL schema** is properly loaded
2. **Restart the local server** after making changes
3. **Verify mutations are imported** in your schema file
4. **Check for syntax errors** in your mutation files

## 📱 Mobile App Testing

Once your local server is running:

1. **Start Expo**: `npx expo start`
2. **Update IP address** in Apollo configuration
3. **Test watchlist functionality** - should work instantly
4. **Debug any issues** with full stack traces

This setup will save you hours of deployment time! 🎉
