#!/usr/bin/env python3
"""
Test Google Gemini API with correct model
"""

import os
import google.generativeai as genai

def test_google_working():
    """Test Google Gemini API with correct model"""
    try:
        genai.configure(api_key="AIzaSyBEoe_oXblnKzgEQfTahffO43lGdDw--9E")
        
        print("✅ Google API configured")
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content("What is a stock?")
        
        print("✅ Google API call successful")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_google_working()
