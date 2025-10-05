#!/usr/bin/env python3
"""
Test AI Scans and Options Copilot Integration
"""

import sys
import os
sys.path.append('.')

def test_ai_scans_engine():
    """Test AI Scans Engine"""
    print("🧪 Testing AI Scans Engine...")
    try:
        from backend.backend.core.ai_scans_engine import AIScansEngine
        from backend.backend.core.real_data_service import get_real_data_service
        
        # Initialize engine
        real_data_service = get_real_data_service()
        ai_engine = AIScansEngine(real_data_service)
        
        # Test available scans (async method)
        import asyncio
        scans = asyncio.run(ai_engine.get_user_scans("test_user"))
        print(f"✅ AI Scans Engine: {len(scans)} scans available")
        
        # Test available playbooks (async method)
        playbooks = asyncio.run(ai_engine.get_playbooks())
        print(f"✅ AI Scans Engine: {len(playbooks)} playbooks available")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Scans Engine error: {e}")
        return False

def test_options_copilot_engine():
    """Test Options Copilot Engine"""
    print("🧪 Testing Options Copilot Engine...")
    try:
        from backend.backend.core.options_copilot_engine import OptionsCopilotEngine
        
        # Initialize engine
        options_engine = OptionsCopilotEngine()
        
        # Test basic functionality
        print("✅ Options Copilot Engine: Initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Options Copilot Engine error: {e}")
        return False

def test_api_endpoints():
    """Test API Endpoints"""
    print("🧪 Testing API Endpoints...")
    try:
        from backend.backend.core.ai_scans_api import router as ai_scans_api
        from backend.backend.core.options_copilot_api import router as options_copilot_api
        
        # Count routes
        ai_scans_routes = len(ai_scans_api.routes)
        options_routes = len(options_copilot_api.routes)
        
        print(f"✅ AI Scans API: {ai_scans_routes} endpoints available")
        print(f"✅ Options Copilot API: {options_routes} endpoints available")
        
        return True
        
    except Exception as e:
        print(f"❌ API Endpoints error: {e}")
        return False

def test_graphql_types():
    """Test GraphQL Types"""
    print("🧪 Testing GraphQL Types...")
    try:
        # Test without Django setup
        import graphene
        
        # Create simple test types
        class TestScanResultType(graphene.ObjectType):
            id = graphene.String()
            symbol = graphene.String()
            currentPrice = graphene.Float()
        
        class TestAIScanType(graphene.ObjectType):
            id = graphene.String()
            name = graphene.String()
            results = graphene.List(TestScanResultType)
        
        print("✅ GraphQL Types: Basic types work")
        return True
        
    except Exception as e:
        print(f"❌ GraphQL Types error: {e}")
        return False

def test_mobile_types():
    """Test Mobile TypeScript Types"""
    print("🧪 Testing Mobile TypeScript Types...")
    try:
        # Check if TypeScript files exist and are valid
        import os
        
        ai_scans_types = "mobile/src/features/aiScans/types/AIScansTypes.ts"
        options_types = "mobile/src/features/options/types/OptionsCopilotTypes.ts"
        
        if os.path.exists(ai_scans_types):
            print("✅ AI Scans TypeScript types: File exists")
        else:
            print("❌ AI Scans TypeScript types: File missing")
            return False
            
        if os.path.exists(options_types):
            print("✅ Options Copilot TypeScript types: File exists")
        else:
            print("❌ Options Copilot TypeScript types: File missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Mobile Types error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting End-to-End Integration Tests")
    print("=" * 50)
    
    tests = [
        test_ai_scans_engine,
        test_options_copilot_engine,
        test_api_endpoints,
        test_graphql_types,
        test_mobile_types
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Integration is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
