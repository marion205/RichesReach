# PostgreSQL & GraphQL Production Setup

## ✅ Changes Applied

### 1. **Production Settings Detection**
- Server now automatically detects and uses production settings:
  - `richesreach.settings_aws` (if exists) - Production AWS settings
  - `richesreach.settings` (if exists) - Standard Django settings
  - `richesreach.settings_local` (fallback) - Local development settings

### 2. **GraphQL Endpoint Updated**
- **Primary**: Uses Django Graphene schema with PostgreSQL
  - Imports `core.schema` (production schema)
  - Executes queries via `graphene_schema.execute()`
  - Connects to PostgreSQL database
  - Uses real Django models (Portfolio, PortfolioPosition, Stock, etc.)

- **Fallback**: Custom handlers if schema not available
  - Maintains backward compatibility
  - Uses mock data if database unavailable

### 3. **Database Connection Verification**
- Server checks database connection on startup
- Logs database name and host
- Warns if connection fails

## 📊 How It Works

### Startup Sequence:
1. **Django Initialization**:
   ```
   ✅ Django initialized with database: your_db_name on your_host
   ✅ Using Django Graphene schema with PostgreSQL
   ```

2. **GraphQL Query Flow**:
   - Query received → Django schema.execute() → PostgreSQL query → Real data returned
   - If schema fails → Fallback to custom handlers → Mock data (if needed)

### Production Schema:
- Uses `core.schema.schema` (extended schema with premium features)
- Includes: Query, Mutation, PremiumQueries, PremiumMutations
- All resolvers use Django ORM to query PostgreSQL
- Returns real data from database

## 🔧 Configuration

### Environment Variables:
Set these for PostgreSQL connection:
```bash
DB_NAME=your_database_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DJANGO_SETTINGS_MODULE=richesreach.settings_aws  # or richesreach.settings
```

### Settings File:
Production settings should have:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

## 🚀 Expected Behavior

### When PostgreSQL is Connected:
- ✅ All GraphQL queries use real database
- ✅ `portfolioMetrics` → Real portfolio data from PostgreSQL
- ✅ `myPortfolios` → Real portfolios from PostgreSQL
- ✅ `createPortfolio` → Creates real portfolio in database
- ✅ All mutations persist to PostgreSQL

### When Database Unavailable:
- ⚠️ Falls back to custom handlers
- ⚠️ Uses mock data for queries
- ⚠️ Mutations may not persist

## 📝 Logs to Watch

**Successful PostgreSQL Connection:**
```
📊 Using production settings: richesreach.settings_aws
✅ Django initialized with database: richesreach_db on db.example.com
✅ Using Django Graphene schema with PostgreSQL
✅ GraphQL query executed successfully via Django schema (PostgreSQL)
```

**Fallback Mode:**
```
⚠️ Database connection check failed: ...
⚠️ Could not import Django schema, using fallback: ...
⚠️ Using custom GraphQL handlers (fallback mode)
```

## ✅ Next Steps

1. **Ensure PostgreSQL is running** and accessible
2. **Set environment variables** for database connection
3. **Restart server** to pick up new configuration
4. **Check logs** to verify PostgreSQL connection
5. **Test GraphQL queries** to ensure they return real data

The server will now use PostgreSQL and the production GraphQL schema automatically!

