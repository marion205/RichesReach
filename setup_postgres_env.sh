#!/bin/bash
# Setup script for PostgreSQL and GraphQL production environment

echo "🚀 Setting up RichesReach PostgreSQL Environment"
echo "================================================"

# Get current user
CURRENT_USER=$(whoami)
echo "Current user: $CURRENT_USER"

# Check if PostgreSQL is running
if pg_isready -h localhost > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not running. Please start it first:"
    echo "   brew services start postgresql@14"
    exit 1
fi

# Create database if it doesn't exist
echo ""
echo "📊 Creating database (if it doesn't exist)..."
createdb richesreach 2>/dev/null && echo "✅ Database 'richesreach' created" || echo "⚠️  Database may already exist"

# Set environment variables
export DB_NAME=richesreach
export DB_USER=$CURRENT_USER
export DB_PASSWORD=""
export DB_HOST=localhost
export DB_PORT=5432
export DJANGO_SETTINGS_MODULE=richesreach.settings

echo ""
echo "✅ Environment variables set:"
echo "   DB_NAME=$DB_NAME"
echo "   DB_USER=$DB_USER"
echo "   DB_HOST=$DB_HOST"
echo "   DB_PORT=$DB_PORT"
echo "   DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# Test database connection
echo ""
echo "🔍 Testing database connection..."
if psql -d richesreach -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ Database connection successful!"
else
    echo "⚠️  Could not connect to database. Trying with different user..."
    # Try with postgres user
    if psql -U postgres -d richesreach -c "SELECT version();" > /dev/null 2>&1; then
        export DB_USER=postgres
        echo "✅ Connected as 'postgres' user"
        echo "   Updated DB_USER=$DB_USER"
    else
        echo "❌ Could not connect. You may need to:"
        echo "   1. Set a password for PostgreSQL"
        echo "   2. Update DB_USER and DB_PASSWORD in your environment"
    fi
fi

echo ""
echo "📝 Next steps:"
echo "1. Export these environment variables in your shell:"
echo "   export DB_NAME=$DB_NAME"
echo "   export DB_USER=$DB_USER"
echo "   export DB_HOST=$DB_HOST"
echo "   export DB_PORT=$DB_PORT"
echo "   export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo ""
echo "2. Or add them to your .env file in backend/backend/.env"
echo ""
echo "3. Restart the server:"
echo "   python main_server.py"
echo ""
echo "✅ Setup complete!"

