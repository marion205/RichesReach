#!/usr/bin/env python3
"""
Test authentication and watchlist functionality locally
"""
import os
import sys
import django
import requests
import json

# Add the Django project to the Python path
sys.path.append('/Users/marioncollins/RichesReach/backend/backend/backend/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local_db')
django.setup()

from django.contrib.auth import get_user_model
from core.models import WatchlistItem, Stock

User = get_user_model()

def create_test_user():
    """Create a test user for authentication testing"""
    try:
        user = User.objects.get(email='test@example.com')
        print(f"✅ User already exists: {user.email}")
        return user
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='test@example.com',
            username='test_user',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"✅ Created new user: {user.email}")
        return user

def get_auth_token():
    """Get JWT token for the test user"""
    print("\n🔐 Testing authentication...")
    
    auth_mutation = """
    mutation TokenAuth($email: String!, $password: String!) {
        tokenAuth(email: $email, password: $password) {
            token
        }
    }
    """
    
    try:
        response = requests.post(
            "http://192.168.1.236:8000/graphql/",
            json={
                "query": auth_mutation,
                "variables": {
                    "email": "test@example.com",
                    "password": "testpass123"
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Auth response: {data}")
            if "data" in data and "tokenAuth" in data["data"] and data["data"]["tokenAuth"]["token"]:
                token = data["data"]["tokenAuth"]["token"]
                print("✅ Authentication successful")
                return token
            else:
                print(f"❌ Authentication failed: {data}")
                return None
        else:
            print(f"❌ Authentication request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_watchlist_mutations(token):
    """Test watchlist mutations with authentication"""
    if not token:
        print("❌ No token available for watchlist testing")
        return False
    
    print("\n📝 Testing watchlist mutations...")
    
    # Test addToWatchlist mutation
    add_mutation = """
    mutation AddToWatchlist($symbol: String!, $companyName: String, $notes: String) {
        addToWatchlist(symbol: $symbol, companyName: $companyName, notes: $notes) {
            success
            message
        }
    }
    """
    
    try:
        response = requests.post(
            "http://192.168.1.236:8000/graphql/",
            json={
                "query": add_mutation,
                "variables": {
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "notes": "Test from local database"
                }
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"JWT {token}"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Add to watchlist response: {data}")
            if "data" in data and "addToWatchlist" in data["data"]:
                result = data["data"]["addToWatchlist"]
                if result["success"]:
                    print("✅ Successfully added AAPL to watchlist")
                    return True
                else:
                    print(f"❌ Failed to add to watchlist: {result['message']}")
                    return False
            else:
                print(f"❌ Unexpected response format: {data}")
                return False
        else:
            print(f"❌ Add to watchlist request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Add to watchlist error: {e}")
        return False

def check_database():
    """Check what's in the local database"""
    print("\n🗄️ Checking local database...")
    
    # Check users
    users = User.objects.all()
    print(f"Total users in database: {users.count()}")
    for user in users:
        print(f"  - {user.email} ({user.username})")
    
    # Check watchlist items
    items = WatchlistItem.objects.all()
    print(f"Total watchlist items in database: {items.count()}")
    for item in items:
        print(f"  - {item.stock.symbol} ({item.stock.company_name}) - Added: {item.added_at}")
    
    # Check stocks
    stocks = Stock.objects.all()
    print(f"Total stocks in database: {stocks.count()}")
    for stock in stocks[:5]:  # Show first 5
        print(f"  - {stock.symbol} ({stock.company_name})")

def main():
    print("🧪 Testing Local Authentication and Watchlist Functionality")
    print("=" * 60)
    
    # Check database state
    check_database()
    
    # Create test user
    user = create_test_user()
    
    # Test authentication
    token = get_auth_token()
    
    if token:
        # Test watchlist mutations
        success = test_watchlist_mutations(token)
        
        if success:
            print("\n🎉 All tests passed!")
            print("✅ Authentication working")
            print("✅ Watchlist mutations working")
            print("✅ Local database integration working")
            
            # Check database again to see the new item
            print("\n🗄️ Final database state:")
            check_database()
        else:
            print("\n❌ Watchlist mutation test failed")
    else:
        print("\n❌ Authentication test failed")

if __name__ == "__main__":
    main()
