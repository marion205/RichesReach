#!/usr/bin/env python3
"""
Export GraphQL schema for codegen
Run this script to generate schema-introspection.json for GraphQL Code Generator

Usage:
  # From project root:
  python3 export_graphql_schema.py
  
  # Or if using virtual environment:
  source deployment_package/backend/venv/bin/activate
  python3 export_graphql_schema.py
"""

import os
import sys
import json

# Try to use the virtual environment if it exists
venv_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend', 'venv')
if os.path.exists(venv_path):
    venv_python = os.path.join(venv_path, 'bin', 'python3')
    if os.path.exists(venv_python):
        print(f"📦 Using virtual environment: {venv_python}")
        # Note: This script should be run with the venv python directly
        # python3 deployment_package/backend/venv/bin/python3 export_graphql_schema.py

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change to backend directory
original_cwd = os.getcwd()
os.chdir(backend_path)

# Try different settings module names
settings_modules = ['core.settings', 'richesreach.settings', 'richesreach.settings_local']
settings_module = None

for module_name in settings_modules:
    try:
        os.environ['DJANGO_SETTINGS_MODULE'] = module_name
        import django
        django.setup()
        settings_module = module_name
        print(f"✅ Using Django settings: {module_name}")
        break
    except Exception as e:
        continue

if not settings_module:
    # Set Django settings - try core.settings first
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    # Initialize Django
    import django
    django.setup()
    
    # Import schema
    from core.schema import schema
    
    # Perform introspection
    print("🔍 Introspecting GraphQL schema...")
    result = schema.introspect()
    
    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'mobile', 'schema-introspection.json')
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Schema exported to: {output_path}")
    schema_types = result.get('__schema', {}).get('types', [])
    print(f"📊 Schema has {len(schema_types)} types")
    print(f"📊 Query type: {result.get('__schema', {}).get('queryType', {}).get('name', 'Unknown')}")
    
except ImportError as e:
    print(f"❌ Error: {e}")
    print("\n💡 Try running with the virtual environment:")
    print("   cd deployment_package/backend")
    print("   source venv/bin/activate")
    print("   python3 ../../export_graphql_schema.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error exporting schema: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

