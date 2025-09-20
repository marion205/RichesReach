#!/usr/bin/env python3
"""
Debug ML Prediction Issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions
from final_complete_server import get_real_ml_prediction, ml_prediction_engine

def test_ml_prediction():
    """Test ML prediction directly"""
    print("🔍 Testing ML Prediction Directly...")
    
    try:
        # Test the ML prediction engine
        print("1. Testing ML prediction engine...")
        prediction = ml_prediction_engine.get_real_prediction("BTC")
        print(f"   Prediction: {prediction}")
        
        # Test the wrapper function
        print("\n2. Testing wrapper function...")
        prediction2 = get_real_ml_prediction("BTC")
        print(f"   Wrapper result: {prediction2}")
        
        return True
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_ml_prediction()
