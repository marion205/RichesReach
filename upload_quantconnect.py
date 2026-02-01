#!/usr/bin/env python3
"""
QuantConnect Upload Automation Script
Helps automate the upload process to QuantConnect.
Note: This script prepares the file and provides instructions.
Actual upload must be done via QuantConnect web interface.
"""
import os
import sys
from pathlib import Path


def main():
    print("🚀 QuantConnect Upload Helper")
    print("=" * 60)
    
    # Find strategy file
    strategy_file = Path(__file__).parent / "quantconnect_strategy.py"
    
    if not strategy_file.exists():
        print(f"❌ Strategy file not found: {strategy_file}")
        print("\n💡 Run this command first:")
        print("   cd deployment_package/backend")
        print("   python manage.py export_to_quantconnect --strategy hybrid_lstm_xgboost --output ../../quantconnect_strategy.py")
        sys.exit(1)
    
    print(f"✅ Found strategy file: {strategy_file}")
    print(f"   Size: {strategy_file.stat().st_size / 1024:.1f} KB")
    
    # Read and validate file
    with open(strategy_file, 'r') as f:
        content = f.read()
    
    # Check for key components
    checks = {
        'QCAlgorithm': 'QCAlgorithm' in content,
        'Initialize': 'def Initialize' in content,
        'OnData': 'def OnData' in content,
        'Strategy Logic': '_should_enter' in content or 'should_enter' in content,
        'Net of Costs': 'total_friction' in content or 'friction' in content,
    }
    
    print("\n📋 File Validation:")
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_passed = False
    
    if not all_passed:
        print("\n⚠️  Some checks failed. File may need review.")
    else:
        print("\n✅ File validation passed!")
    
    # Display file preview
    print("\n📄 File Preview (first 30 lines):")
    print("-" * 60)
    lines = content.split('\n')[:30]
    for i, line in enumerate(lines, 1):
        print(f"{i:3d} | {line}")
    print("-" * 60)
    
    # Instructions
    print("\n📝 Upload Instructions:")
    print("=" * 60)
    print("1. Go to https://www.quantconnect.com")
    print("2. Log in (or create account)")
    print("3. Click 'Create Algorithm' → 'New Algorithm'")
    print("4. Select 'Python' as language")
    print("5. Name it: 'RichesReach Hybrid LSTM XGBoost'")
    print("6. Copy the entire contents of quantconnect_strategy.py")
    print("7. Paste into QuantConnect editor")
    print("8. Click 'Save'")
    print("9. Set backtest period: 2020-01-01 to 2023-12-31")
    print("10. Set initial capital: $100,000")
    print("11. Click 'Backtest'")
    print("12. Wait for completion (10-30 minutes)")
    print("\n💡 Tip: You can open the file in your editor:")
    print(f"   open {strategy_file}")
    
    # Offer to open file (only if interactive)
    try:
        if sys.stdin.isatty():  # Only ask if running interactively
            response = input("\n❓ Open file in default editor? (y/n): ").strip().lower()
            if response == 'y':
                if sys.platform == 'darwin':
                    os.system(f'open {strategy_file}')
                elif sys.platform == 'linux':
                    os.system(f'xdg-open {strategy_file}')
                elif sys.platform == 'win32':
                    os.system(f'start {strategy_file}')
                print("✅ File opened!")
        else:
            print(f"\n💡 To open the file manually:")
            print(f"   open {strategy_file}")
    except (KeyboardInterrupt, EOFError):
        print("\n\n✅ Script complete. Good luck with your backtest!")


if __name__ == '__main__':
    main()

