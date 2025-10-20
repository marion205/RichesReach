#!/usr/bin/env python3
"""
Test Google Gemini API models
"""

import os
import google.generativeai as genai

def test_google_models():
    """Test Google Gemini API models"""
    try:
        genai.configure(api_key="AIzaSyBEoe_oXblnKzgEQfTahffO43lGdDw--9E")
        
        print("✅ Google API configured")
        
        # List available models
        models = genai.list_models()
        print("Available models:")
        for model in models:
            print(f"  - {model.name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_google_models()
