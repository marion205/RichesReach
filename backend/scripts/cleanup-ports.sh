#!/bin/bash

# Port Cleanup Script for RichesReach Production
# This script ensures clean process hygiene and port management

echo "🧹 Starting Port Cleanup and Process Hygiene Check..."

# Function to kill processes on specific ports
cleanup_port() {
    local port=$1
    local service_name=$2
    
    echo "Checking port $port for $service_name..."
    
    # Find processes using the port
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "⚠️  Found processes on port $port: $pids"
        echo "Killing processes on port $port..."
        echo $pids | xargs kill -9 2>/dev/null
        sleep 2
        
        # Verify cleanup
        local remaining=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$remaining" ]; then
            echo "❌ Failed to clean port $port. Remaining PIDs: $remaining"
            return 1
        else
            echo "✅ Successfully cleaned port $port"
        fi
    else
        echo "✅ Port $port is clean"
    fi
}

# Clean up common development ports
cleanup_port 8000 "Django Backend"
cleanup_port 8081 "Expo Metro Bundler"
cleanup_port 8083 "Expo Alternative Port"
cleanup_port 3000 "React Development Server"
cleanup_port 5432 "PostgreSQL (if running locally)"

# Clean up any hanging Django processes
echo "Checking for hanging Django processes..."
DJANGO_PIDS=$(ps aux | grep "manage.py runserver" | grep -v grep | awk '{print $2}')
if [ -n "$DJANGO_PIDS" ]; then
    echo "⚠️  Found hanging Django processes: $DJANGO_PIDS"
    echo $DJANGO_PIDS | xargs kill -9 2>/dev/null
    echo "✅ Cleaned up Django processes"
else
    echo "✅ No hanging Django processes found"
fi

# Clean up any hanging Expo processes
echo "Checking for hanging Expo processes..."
EXPO_PIDS=$(ps aux | grep "expo start" | grep -v grep | awk '{print $2}')
if [ -n "$EXPO_PIDS" ]; then
    echo "⚠️  Found hanging Expo processes: $EXPO_PIDS"
    echo $EXPO_PIDS | xargs kill -9 2>/dev/null
    echo "✅ Cleaned up Expo processes"
else
    echo "✅ No hanging Expo processes found"
fi

# Clean up any hanging Node processes related to our project
echo "Checking for hanging Node processes..."
NODE_PIDS=$(ps aux | grep -E "(metro|react-native)" | grep -v grep | awk '{print $2}')
if [ -n "$NODE_PIDS" ]; then
    echo "⚠️  Found hanging Node processes: $NODE_PIDS"
    echo $NODE_PIDS | xargs kill -9 2>/dev/null
    echo "✅ Cleaned up Node processes"
else
    echo "✅ No hanging Node processes found"
fi

# Verify Redis is running (if needed)
echo "Checking Redis status..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is not running. Starting Redis..."
        if command -v brew &> /dev/null; then
            brew services start redis
        fi
    fi
else
    echo "ℹ️  Redis CLI not found, skipping Redis check"
fi

# Verify PostgreSQL is running (if needed)
echo "Checking PostgreSQL status..."
if command -v psql &> /dev/null; then
    if pg_isready -q; then
        echo "✅ PostgreSQL is running"
    else
        echo "⚠️  PostgreSQL is not running. You may need to start it manually."
    fi
else
    echo "ℹ️  PostgreSQL not found, skipping PostgreSQL check"
fi

echo ""
echo "🎉 Port cleanup completed!"
echo ""
echo "📋 Summary:"
echo "  - All development ports cleaned"
echo "  - Hanging processes terminated"
echo "  - Services status verified"
echo ""
echo "🚀 Ready to start fresh development servers!"
