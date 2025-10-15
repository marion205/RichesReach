#!/usr/bin/env python3
"""
Test GraphQL Field Detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_complete_server import top_level_fields

def test_field_detection():
    """Test field detection for various queries"""
    print("🔍 Testing GraphQL Field Detection...")
    
    queries = [
        "query { cryptoMlSignal(symbol: \"BTC\") { symbol } }",
        "query { cryptoRecommendations(constraints: { maxSymbols: 1 }) { success } }",
        "query { __typename }",
        "query { nonExistentField }"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        fields = top_level_fields(query, None)
        print(f"Detected fields: {fields}")
        
        if "cryptoMlSignal" in fields:
            print("✅ cryptoMlSignal detected")
        else:
            print("❌ cryptoMlSignal NOT detected")

if __name__ == "__main__":
    test_field_detection()
