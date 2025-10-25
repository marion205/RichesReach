#!/usr/bin/env python3
"""
Voice AI Test Script for RichesReach
Tests the voice AI service and API endpoints
"""

import os
import sys
import django
import asyncio
import requests
import json
from pathlib import Path

# Add the Django project to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')

# Setup Django
django.setup()

from core.voice_ai_service import voice_ai_service

def test_voice_ai_service():
    """Test the voice AI service directly"""
    print("🧪 Testing Voice AI Service...")
    
    async def run_tests():
        # Test model loading
        print("1. Testing model loading...")
        await voice_ai_service.load_model()
        
        if voice_ai_service.model_loaded:
            print("   ✅ Model loaded successfully")
        else:
            print("   ❌ Model failed to load")
            return False
        
        # Test speech synthesis
        print("2. Testing speech synthesis...")
        test_text = "Welcome to RichesReach Voice AI. Your portfolio is performing well today."
        
        audio_path = await voice_ai_service.synthesize_speech(
            text=test_text,
            voice="default",
            speed=1.0,
            emotion="neutral"
        )
        
        if audio_path and os.path.exists(audio_path):
            print(f"   ✅ Audio generated: {audio_path}")
            print(f"   📁 File size: {os.path.getsize(audio_path)} bytes")
        else:
            print("   ❌ Audio generation failed")
            return False
        
        # Test available voices
        print("3. Testing available voices...")
        voices = await voice_ai_service.get_available_voices()
        print(f"   ✅ Available voices: {list(voices.keys())}")
        
        return True
    
    return asyncio.run(run_tests())

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/voice-ai/health/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed: {data.get('status', 'unknown')}")
            print(f"   📊 Model status: {data.get('model_status', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Server not running. Start with: python manage.py runserver")
        return False
    
    # Test voices endpoint
    print("2. Testing voices endpoint...")
    try:
        response = requests.get(f"{base_url}/api/voice-ai/voices/")
        if response.status_code == 200:
            data = response.json()
            voices = data.get('voices', {})
            print(f"   ✅ Voices endpoint working: {len(voices)} voices available")
        else:
            print(f"   ❌ Voices endpoint failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Server not running")
        return False
    
    # Test synthesis endpoint
    print("3. Testing synthesis endpoint...")
    try:
        payload = {
            "text": "Hello, this is a test of the RichesReach Voice AI system.",
            "voice": "default",
            "speed": 1.0,
            "emotion": "neutral"
        }
        
        response = requests.post(
            f"{base_url}/api/voice-ai/synthesize/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Synthesis successful: {data.get('filename')}")
                print(f"   🔗 Audio URL: {data.get('audio_url')}")
            else:
                print(f"   ❌ Synthesis failed: {data.get('error')}")
        else:
            print(f"   ❌ Synthesis endpoint failed: {response.status_code}")
            print(f"   📝 Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Server not running")
        return False
    
    return True

def test_file_structure():
    """Test the file structure and permissions"""
    print("\n📁 Testing File Structure...")
    
    required_dirs = [
        "media/tts_audio",
        "models",
        "voices"
    ]
    
    for dir_path in required_dirs:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        if os.path.exists(full_path):
            print(f"   ✅ Directory exists: {dir_path}")
            if os.access(full_path, os.W_OK):
                print(f"   ✅ Directory writable: {dir_path}")
            else:
                print(f"   ❌ Directory not writable: {dir_path}")
        else:
            print(f"   ❌ Directory missing: {dir_path}")
            print(f"   💡 Create with: mkdir -p {dir_path}")

def main():
    """Main test function"""
    print("🎤 RichesReach Voice AI Test Suite")
    print("=" * 50)
    
    # Test file structure
    test_file_structure()
    
    # Test voice AI service
    service_success = test_voice_ai_service()
    
    # Test API endpoints
    api_success = test_api_endpoints()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Voice AI Service: {'✅ PASS' if service_success else '❌ FAIL'}")
    print(f"API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if service_success and api_success:
        print("\n🎉 All tests passed! Voice AI is ready to use.")
        print("\nNext steps:")
        print("1. Start your Django server: python manage.py runserver")
        print("2. Test the mobile app integration")
        print("3. Customize voice settings in the app")
    else:
        print("\n⚠️  Some tests failed. Check the setup:")
        print("1. Run: ./setup_voice_ai.sh")
        print("2. Install dependencies: pip install -r requirements_voice_ai.txt")
        print("3. Download models: python manage.py test_tts")

if __name__ == "__main__":
    main()
