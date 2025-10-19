#!/usr/bin/env python3
"""
Test script to verify GraphQL schema is working correctly
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local_prod')

def test_schema():
    print("🧪 Testing GraphQL Schema...")
    
    try:
        # Import Django
        django.setup()
        
        # Import schema
        from core.schema import schema
        
        print("✅ Schema imported successfully")
        
        # Test introspection query
        introspection_query = """
        query IntrospectionQuery {
          __schema {
            mutationType {
              fields {
                name
                description
              }
            }
          }
        }
        """
        
        result = schema.execute(introspection_query)
        
        if result.errors:
            print("❌ Schema introspection failed:")
            for error in result.errors:
                print(f"   - {error.message}")
            return False
        
        # Check if watchlist mutations are present
        mutation_fields = result.data['__schema']['mutationType']['fields']
        mutation_names = [field['name'] for field in mutation_fields]
        
        print(f"📊 Found {len(mutation_names)} mutations:")
        for name in mutation_names:
            print(f"   - {name}")
        
        # Check for watchlist mutations
        if 'addToWatchlist' in mutation_names:
            print("✅ addToWatchlist mutation found")
        else:
            print("❌ addToWatchlist mutation NOT found")
            return False
            
        if 'removeFromWatchlist' in mutation_names:
            print("✅ removeFromWatchlist mutation found")
        else:
            print("❌ removeFromWatchlist mutation NOT found")
            return False
        
        # Test a simple query
        simple_query = """
        query {
          ping
        }
        """
        
        result = schema.execute(simple_query)
        if result.errors:
            print("❌ Simple query failed:")
            for error in result.errors:
                print(f"   - {error.message}")
            return False
        
        print("✅ Simple query works")
        print("🎉 Schema is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_schema()
    sys.exit(0 if success else 1)
