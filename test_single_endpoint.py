#!/usr/bin/env python3
"""
Test a single GenAI endpoint to debug the 500 error
"""

import requests
import json

def test_tutor_ask():
    """Test the tutor/ask endpoint"""
    url = "http://127.0.0.1:8124/tutor/ask"
    payload = {
        "user_id": "test-user",
        "question": "What is a stock?"
    }
    
    try:
        print(f"Testing {url}...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Success!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print("❌ Error!")
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_tutor_ask()
