
#!/usr/bin/env python3
"""
Train Improved ML Models for Better R² Scores
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend" / "backend"))

from improved_ml_learning_system import train_improved_models

if __name__ == "__main__":
    print("🚀 Training Improved ML Models...")
    results = train_improved_models()
    
    print("\n📊 Results Summary:")
    for mode, result in results.items():
        if result:
            print(f"  {mode}: R² = {result['r2_score']:.4f} (Target: 0.15+)")
        else:
            print(f"  {mode}: Training failed")
    
    # Calculate average R²
    valid_results = [r['r2_score'] for r in results.values() if r]
    if valid_results:
        avg_r2 = sum(valid_results) / len(valid_results)
        print(f"\n🎯 Average R² Score: {avg_r2:.4f}")
        if avg_r2 >= 0.15:
            print("✅ Target achieved! R² score meets industry standard.")
        else:
            print("⚠️  R² score below industry standard. Consider more training data or feature engineering.")
