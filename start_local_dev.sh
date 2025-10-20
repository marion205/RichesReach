#!/bin/bash

echo "🚀 Starting RichesReach Local Development Environment"
echo "=================================================="

# Function to start Django backend
start_django() {
    echo "📊 Starting Django Backend Server..."
    cd backend/backend
    source ../venv/bin/activate
    
    echo "🔍 Checking Django configuration..."
    python3 manage.py check --settings=richesreach.settings_local
    
    echo "📊 Running database migrations..."
    python3 manage.py migrate --settings=richesreach.settings_local
    
    echo "🚀 Starting Django server on http://localhost:8000..."
    python3 manage.py runserver 127.0.0.1:8000 --settings=richesreach.settings_local
}

# Function to start React Native frontend
start_react_native() {
    echo "📱 Starting React Native Metro Bundler..."
    cd mobile
    
    echo "🚀 Starting Expo development server..."
    npx expo start --clear --port 8081
}

# Function to test the setup
test_setup() {
    echo "🧪 Testing local setup..."
    cd ..
    python3 test_local_setup.py
}

# Main menu
echo "Choose an option:"
echo "1) Start Django Backend Only"
echo "2) Start React Native Frontend Only"
echo "3) Start Both Servers (in separate terminals)"
echo "4) Test Current Setup"
echo "5) Exit"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        start_django
        ;;
    2)
        start_react_native
        ;;
    3)
        echo "🚀 Starting both servers..."
        echo "📊 Django will start in this terminal"
        echo "📱 React Native will start in a new terminal"
        
        # Start Django in current terminal
        start_django &
        
        # Start React Native in new terminal (macOS)
        osascript -e 'tell app "Terminal" to do script "cd /Users/marioncollins/RichesReach/mobile && npx expo start --clear --port 8081"'
        
        echo "✅ Both servers starting..."
        ;;
    4)
        test_setup
        ;;
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac
