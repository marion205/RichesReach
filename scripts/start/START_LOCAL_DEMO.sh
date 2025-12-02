#!/bin/bash
# Quick start script for local demo with PostgreSQL

echo "🚀 Starting Local Demo with PostgreSQL"
echo "======================================"

# Set environment variables for local PostgreSQL
export DB_NAME=richesreach
export DB_USER=$(whoami)
export DB_HOST=localhost
export DB_PORT=5432
export DJANGO_SETTINGS_MODULE=richesreach.settings

echo ""
echo "✅ Environment Variables Set:"
echo "   DB_NAME=$DB_NAME"
echo "   DB_USER=$DB_USER"
echo "   DB_HOST=$DB_HOST"
echo "   DB_PORT=$DB_PORT"
echo "   DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h localhost > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running"
    echo "   Start it with: brew services start postgresql@14"
    exit 1
fi

echo "✅ PostgreSQL is running"
echo ""

# Check if database exists
if psql -d richesreach -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database 'richesreach' is accessible"
else
    echo "⚠️  Database 'richesreach' not accessible, creating..."
    createdb richesreach 2>/dev/null && echo "✅ Database created" || echo "⚠️  Could not create database"
fi

echo ""
echo "📊 Starting Backend Server..."
echo "   GraphQL endpoint: http://localhost:8000/graphql/"
echo ""
echo "📱 Mobile app should connect to: http://localhost:8000/graphql/"
echo "   (For physical devices, use your Mac's LAN IP)"
echo ""

# Activate virtual environment and start server
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || echo "⚠️  Virtual environment not found, using system Python"

python main_server.py

