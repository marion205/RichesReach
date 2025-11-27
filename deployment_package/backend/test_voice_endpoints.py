#!/usr/bin/env python3
"""
Unit tests for voice endpoints.
Tests for 404s, server errors, and basic functionality.
"""
import pytest
import asyncio
import aiohttp
import json
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8000"

class TestVoiceEndpoints:
    """Test suite for voice endpoints."""
    
    @pytest.mark.asyncio
    async def test_streaming_endpoint_exists(self):
        """Test that /api/voice/stream endpoint exists (not 404)."""
        url = f"{BASE_URL}/api/voice/stream"
        payload = {
            "transcript": "test",
            "history": [],
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                assert response.status != 404, f"Endpoint not found (404): {url}"
                assert response.status in [200, 400, 500], f"Unexpected status: {response.status}"
    
    @pytest.mark.asyncio
    async def test_streaming_endpoint_valid_request(self):
        """Test streaming endpoint with valid request."""
        url = f"{BASE_URL}/api/voice/stream"
        payload = {
            "transcript": "What should I invest in today?",
            "history": [],
            "last_trade": None,
        }
        
        tokens_received = 0
        full_text = ""
        error_occurred = False
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                
                # Read streaming response
                async for line in response.content:
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line.decode('utf-8').strip())
                        
                        if data.get("type") == "token":
                            tokens_received += 1
                            full_text += data.get("text", "")
                        elif data.get("type") == "done":
                            full_text = data.get("full_text", full_text)
                            break
                        elif data.get("type") == "error":
                            error_occurred = True
                            break
                    except json.JSONDecodeError:
                        continue
        
        assert not error_occurred, "Error occurred in streaming response"
        assert tokens_received > 0, "No tokens received"
        assert len(full_text) > 0, "Empty response"
    
    @pytest.mark.asyncio
    async def test_streaming_endpoint_missing_transcript(self):
        """Test streaming endpoint with missing transcript (should handle gracefully)."""
        url = f"{BASE_URL}/api/voice/stream"
        payload = {
            "history": [],
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                # Should return error but not crash
                assert response.status in [200, 400, 422], f"Unexpected status: {response.status}"
    
    @pytest.mark.asyncio
    async def test_streaming_endpoint_different_intents(self):
        """Test streaming endpoint with different intents."""
        test_cases = [
            ("What should I invest in today?", "get_trade_idea"),
            ("Show me Bitcoin price", "crypto_query"),
            ("What's my portfolio?", "portfolio_query"),
            ("Execute the trade", "execute_trade"),
        ]
        
        for transcript, expected_intent in test_cases:
            url = f"{BASE_URL}/api/voice/stream"
            payload = {
                "transcript": transcript,
                "history": [],
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    assert response.status == 200, f"Failed for: {transcript}"
                    
                    # Read at least one chunk to verify it works
                    chunk_received = False
                    async for line in response.content:
                        if line:
                            chunk_received = True
                            break
                    
                    assert chunk_received, f"No chunks received for: {transcript}"
    
    @pytest.mark.asyncio
    async def test_process_endpoint_exists(self):
        """Test that /api/voice/process/ endpoint exists (not 404)."""
        url = f"{BASE_URL}/api/voice/process/"
        
        # Create minimal form data
        form_data = aiohttp.FormData()
        form_data.add_field('audio', b'fake_audio', filename='test.wav', content_type='audio/wav')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data) as response:
                assert response.status != 404, f"Endpoint not found (404): {url}"
                # May return 400 for invalid audio, but not 404
                assert response.status in [200, 400, 422, 500], f"Unexpected status: {response.status}"
    
    @pytest.mark.asyncio
    async def test_process_endpoint_returns_transcription(self):
        """Test that process endpoint returns transcription in response."""
        url = f"{BASE_URL}/api/voice/process/"
        
        form_data = aiohttp.FormData()
        form_data.add_field('audio', b'fake_audio_data', filename='test.wav', content_type='audio/wav')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data) as response:
                if response.status == 200:
                    data = await response.json()
                    assert "response" in data, "Missing 'response' field"
                    assert "transcription" in data.get("response", {}), "Missing 'transcription' field"
    
    @pytest.mark.asyncio
    async def test_streaming_endpoint_with_history(self):
        """Test streaming endpoint with conversation history."""
        url = f"{BASE_URL}/api/voice/stream"
        payload = {
            "transcript": "Yes, execute it",
            "history": [
                {"type": "user", "text": "What should I buy?"},
                {"type": "assistant", "text": "I recommend NVIDIA at $179.50"},
            ],
            "last_trade": {
                "symbol": "NVDA",
                "quantity": 100,
                "price": 179.50,
            },
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                
                # Verify we get a response
                response_received = False
                async for line in response.content:
                    if line:
                        response_received = True
                        break
                
                assert response_received, "No response received with history"

def run_tests():
    """Run all tests."""
    pytest.main([__file__, "-v", "-s"])

if __name__ == "__main__":
    run_tests()

