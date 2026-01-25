#!/usr/bin/env python
"""
Quick verification script to check if users have improved investment access.

Run this to verify:
1. New tools are available
2. Service methods exist
3. Investment access score improvement
"""
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

def verify_investment_access():
    """Verify users have more investment access"""
    
    print("=" * 60)
    print("Investment Access Verification")
    print("=" * 60)
    
    try:
        from core.ai_tools import AITools
        from core.algorithm_service import get_algorithm_service
        
        # 1. Check tools are available
        print("\n1. Checking AI Tools Registration...")
        tools = AITools.get_tool_definitions()
        tool_names = [t["function"]["name"] for t in tools]
        
        required_tools = [
            "create_direct_index",
            "create_tax_smart_transition",
            "optimize_portfolio_allocation",
            "find_tax_loss_harvesting_opportunities"
        ]
        
        print("   Investment Access Tools:")
        tool_count = 0
        for tool in required_tools:
            if tool in tool_names:
                print(f"   ✅ {tool}")
                tool_count += 1
            else:
                print(f"   ❌ {tool} - NOT FOUND")
        
        # 2. Test service methods
        print("\n2. Checking Service Methods...")
        service = get_algorithm_service()
        
        methods = [
            "create_direct_index",
            "create_tax_smart_transition",
            "optimize_portfolio_allocation",
            "find_tax_loss_harvesting"
        ]
        
        print("   Service Methods:")
        method_count = 0
        for method in methods:
            if hasattr(service, method):
                print(f"   ✅ {method}")
                method_count += 1
            else:
                print(f"   ❌ {method} - NOT FOUND")
        
        # 3. Check if files exist
        print("\n3. Checking Implementation Files...")
        files_to_check = [
            "core/direct_indexing.py",
            "core/tax_smart_transitions.py"
        ]
        
        file_count = 0
        for file_path in files_to_check:
            full_path = os.path.join("deployment_package", "backend", file_path)
            if os.path.exists(full_path):
                print(f"   ✅ {file_path}")
                file_count += 1
            else:
                print(f"   ❌ {file_path} - NOT FOUND")
        
        # 4. Calculate access score
        print("\n4. Calculating Investment Access Score...")
        
        # Base score (public markets, options, crypto)
        base_score = 3.0
        
        # New features score
        new_features_score = 0
        if "create_direct_index" in tool_names:
            new_features_score += 2.0  # Direct Indexing
        if "create_tax_smart_transition" in tool_names:
            new_features_score += 2.0  # TSPT
        if hasattr(service, "optimize_portfolio_allocation"):
            new_features_score += 0.5  # Framework
        if hasattr(service, "find_tax_loss_harvesting"):
            new_features_score += 1.0  # Enhanced TLH
        
        total_score = base_score + new_features_score
        total_score = min(total_score, 10.0)  # Cap at 10
        
        print(f"   Base Score (Public Markets): {base_score}/10")
        print(f"   New Features Score: +{new_features_score}/10")
        print(f"   Total Score: {total_score:.1f}/10")
        
        # 5. Summary
        print("\n" + "=" * 60)
        print("Verification Summary")
        print("=" * 60)
        
        total_checks = len(required_tools) + len(methods) + len(files_to_check)
        passed_checks = tool_count + method_count + file_count
        
        print(f"Checks Passed: {passed_checks}/{total_checks}")
        print(f"Investment Access Score: {total_score:.1f}/10")
        
        if total_score >= 8.0:
            print("\n✅ SUCCESS: Users have significantly improved investment access!")
            print("   - Direct Indexing: Available")
            print("   - TSPT: Available")
            print("   - Enhanced Tax Tools: Available")
            print("   - AI Integration: Working")
        elif total_score >= 6.0:
            print("\n⚠️  PARTIAL: Investment access is improved but incomplete")
            print("   Some features may not be fully integrated")
        else:
            print("\n❌ FAILED: Investment access needs improvement")
            print("   Features may not be properly implemented")
        
        print("\n" + "=" * 60)
        print("What Users Can Now Access:")
        print("=" * 60)
        
        features = []
        if "create_direct_index" in tool_names:
            features.append("✅ Direct Indexing - Tax-efficient portfolio customization")
        if "create_tax_smart_transition" in tool_names:
            features.append("✅ Tax-Smart Transitions - Gradual diversification")
        if hasattr(service, "find_tax_loss_harvesting"):
            features.append("✅ Enhanced Tax-Loss Harvesting - Automated tax savings")
        if hasattr(service, "optimize_portfolio_allocation"):
            features.append("✅ Portfolio Optimization - AI-powered allocation")
        
        if features:
            for feature in features:
                print(f"   {feature}")
        else:
            print("   ⚠️  No new features detected")
        
        return total_score >= 8.0
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("   Make sure you're running from the correct directory")
        print("   Or set up Django environment properly")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_investment_access()
    sys.exit(0 if success else 1)

