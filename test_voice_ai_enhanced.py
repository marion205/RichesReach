#!/usr/bin/env python3
"""
Comprehensive Voice AI Test Script for RichesReach
Tests all voice endpoints for naturalness and quality
"""

import asyncio
import json
import requests
import time
from typing import Dict, List, Any

class VoiceAITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test the health endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/health/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data.get('status', 'unknown')}")
                return {"status": "passed", "data": data}
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_voices_endpoint(self) -> Dict[str, Any]:
        """Test the voices endpoint"""
        print("🔍 Testing voices endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/voices/")
            if response.status_code == 200:
                data = response.json()
                voices = data.get('voices', {})
                print(f"✅ Voices endpoint passed: {len(voices)} voices available")
                return {"status": "passed", "data": data}
            else:
                print(f"❌ Voices endpoint failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Voices endpoint error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_synthesis_endpoint(self, text: str, voice: str = "default", 
                                    speed: float = 1.0, emotion: str = "neutral") -> Dict[str, Any]:
        """Test the synthesis endpoint"""
        print(f"🔍 Testing synthesis endpoint with voice '{voice}'...")
        try:
            payload = {
                "text": text,
                "voice": voice,
                "speed": speed,
                "emotion": emotion
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/synthesize/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    audio_url = data.get('audio_url')
                    print(f"✅ Synthesis passed: {audio_url} (took {end_time - start_time:.2f}s)")
                    return {
                        "status": "passed", 
                        "data": data,
                        "duration": end_time - start_time,
                        "audio_url": audio_url
                    }
                else:
                    print(f"❌ Synthesis failed: {data.get('error', 'Unknown error')}")
                    return {"status": "failed", "error": data.get('error')}
            else:
                print(f"❌ Synthesis failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Synthesis error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_preview_endpoint(self, voice: str = "default", 
                                  speed: float = 1.0, emotion: str = "neutral") -> Dict[str, Any]:
        """Test the preview endpoint"""
        print(f"🔍 Testing preview endpoint with voice '{voice}'...")
        try:
            payload = {
                "voice": voice,
                "speed": speed,
                "emotion": emotion
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/preview/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    audio_url = data.get('audio_url')
                    print(f"✅ Preview passed: {audio_url} (took {end_time - start_time:.2f}s)")
                    return {
                        "status": "passed", 
                        "data": data,
                        "duration": end_time - start_time,
                        "audio_url": audio_url
                    }
                else:
                    print(f"❌ Preview failed: {data.get('error', 'Unknown error')}")
                    return {"status": "failed", "error": data.get('error')}
            else:
                print(f"❌ Preview failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Preview error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_batch_endpoint(self, texts: List[str], voice: str = "default", 
                                speed: float = 1.0, emotion: str = "neutral") -> Dict[str, Any]:
        """Test the batch endpoint"""
        print(f"🔍 Testing batch endpoint with {len(texts)} texts...")
        try:
            payload = {
                "texts": texts,
                "voice": voice,
                "speed": speed,
                "emotion": emotion
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/batch/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results = data.get('results', [])
                    successful = len([r for r in results if r.get('success')])
                    print(f"✅ Batch passed: {successful}/{len(texts)} successful (took {end_time - start_time:.2f}s)")
                    return {
                        "status": "passed", 
                        "data": data,
                        "duration": end_time - start_time,
                        "successful": successful,
                        "total": len(texts)
                    }
                else:
                    print(f"❌ Batch failed: {data.get('error', 'Unknown error')}")
                    return {"status": "failed", "error": data.get('error')}
            else:
                print(f"❌ Batch failed: {response.status_code}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Batch error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_all_voices(self) -> Dict[str, Any]:
        """Test all available voices"""
        print("🔍 Testing all available voices...")
        
        # Get available voices
        voices_response = await self.test_voices_endpoint()
        if voices_response["status"] != "passed":
            return {"status": "failed", "error": "Could not get voices list"}
        
        voices = voices_response["data"].get("voices", {})
        test_text = "Hello, I'm your AI financial advisor. I can help you understand market trends and analyze your portfolio."
        
        results = {}
        for voice_id, voice_info in voices.items():
            print(f"  Testing voice: {voice_info.get('name', voice_id)}")
            result = await self.test_synthesis_endpoint(test_text, voice_id)
            results[voice_id] = result
            
            # Test different emotions for each voice
            emotions = voice_info.get('emotions', ['neutral'])
            for emotion in emotions:
                print(f"    Testing emotion: {emotion}")
                emotion_result = await self.test_synthesis_endpoint(test_text, voice_id, 1.0, emotion)
                results[f"{voice_id}_{emotion}"] = emotion_result
        
        return {"status": "completed", "results": results}
    
    async def test_finance_terminology(self) -> Dict[str, Any]:
        """Test finance-specific terminology pronunciation"""
        print("🔍 Testing finance terminology pronunciation...")
        
        finance_terms = [
            "Your portfolio has a 12.5% ROI this quarter.",
            "The S&P 500 ETF shows strong performance.",
            "Consider diversifying with a 401k and Roth IRA.",
            "The Federal Reserve's inflation target is 2%.",
            "Market volatility measured by VIX is increasing.",
            "Your Sharpe ratio indicates good risk-adjusted returns.",
            "The Black-Scholes model values your options at $1,250.",
            "GARCH analysis shows heteroscedasticity in returns.",
            "Monte Carlo simulation predicts 95% confidence interval.",
            "Your beta of 1.2 indicates higher market sensitivity."
        ]
        
        results = []
        for i, text in enumerate(finance_terms):
            print(f"  Testing finance term {i+1}/{len(finance_terms)}: {text[:50]}...")
            result = await self.test_synthesis_endpoint(text, "finance_expert", 1.0, "analytical")
            results.append({
                "text": text,
                "result": result
            })
        
        return {"status": "completed", "results": results}
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("🎤 Starting Comprehensive Voice AI Test Suite")
        print("=" * 50)
        
        test_results = {}
        
        # Test basic endpoints
        test_results["health"] = await self.test_health_endpoint()
        test_results["voices"] = await self.test_voices_endpoint()
        
        # Test synthesis with different parameters
        test_text = "Welcome to RichesReach, your comprehensive wealth management platform."
        test_results["synthesis_default"] = await self.test_synthesis_endpoint(test_text)
        test_results["synthesis_finance_expert"] = await self.test_synthesis_endpoint(test_text, "finance_expert", 1.0, "confident")
        test_results["synthesis_friendly"] = await self.test_synthesis_endpoint(test_text, "friendly_advisor", 0.9, "friendly")
        
        # Test preview endpoint
        test_results["preview"] = await self.test_preview_endpoint("default", 1.0, "neutral")
        
        # Test batch endpoint
        batch_texts = [
            "Market analysis shows positive trends.",
            "Your portfolio performance is excellent.",
            "Consider rebalancing your investments."
        ]
        test_results["batch"] = await self.test_batch_endpoint(batch_texts)
        
        # Test all voices
        test_results["all_voices"] = await self.test_all_voices()
        
        # Test finance terminology
        test_results["finance_terminology"] = await self.test_finance_terminology()
        
        # Generate summary
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for test_name, result in test_results.items():
            if isinstance(result, dict):
                if result.get("status") == "passed":
                    passed_tests += 1
                elif result.get("status") == "failed":
                    failed_tests += 1
                total_tests += 1
        
        print("\n" + "=" * 50)
        print("🎤 Voice AI Test Suite Results")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0
            },
            "results": test_results
        }

async def main():
    """Main test function"""
    tester = VoiceAITester()
    results = await tester.run_comprehensive_test()
    
    # Save results to file
    with open("voice_ai_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to voice_ai_test_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
