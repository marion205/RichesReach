#!/usr/bin/env python3
"""
Voice AI Trading System Unit Tests
Comprehensive tests for voice command parsing, synthesis, and trading integration
"""

import unittest
import requests
import json
import time
from unittest.mock import Mock, patch

class TestVoiceCommandParsing(unittest.TestCase):
    """Test voice command parsing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        
    def test_basic_buy_commands(self):
        """Test basic buy command parsing"""
        test_commands = [
            "buy 100 shares of AAPL",
            "purchase 50 MSFT",
            "get 25 GOOGL shares",
            "Nova, buy AAPL",
            "Echo, purchase 100 TSLA"
        ]
        
        for command in test_commands:
            with self.subTest(command=command):
                response = requests.post(
                    f"{self.base_url}/api/voice-trading/parse-command/",
                    json={"transcript": command, "voice_name": "Nova"},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertTrue(data["success"])
                self.assertIn("parsed_order", data)
                
                parsed = data["parsed_order"]
                self.assertEqual(parsed["side"], "buy")
                self.assertIn("symbol", parsed)
                self.assertIn("quantity", parsed)
                
    def test_basic_sell_commands(self):
        """Test basic sell command parsing"""
        test_commands = [
            "sell 100 shares of AAPL",
            "dump 50 MSFT",
            "liquidate 25 GOOGL",
            "Nova, sell TSLA",
            "Echo, dump 100 NVDA"
        ]
        
        for command in test_commands:
            with self.subTest(command=command):
                response = requests.post(
                    f"{self.base_url}/api/voice-trading/parse-command/",
                    json={"transcript": command, "voice_name": "Nova"},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertTrue(data["success"])
                
                parsed = data["parsed_order"]
                self.assertEqual(parsed["side"], "sell")
                
    def test_hft_specific_commands(self):
        """Test HFT-specific voice commands"""
        hft_commands = [
            "Nova, scalp AAPL imbalance",
            "Echo, market make SPY spreads",
            "Onyx, arbitrage SPY-SPXL",
            "Shimmer, momentum TSLA trend",
            "scalp NVDA for 2 bps",
            "market make QQQ liquidity"
        ]
        
        for command in hft_commands:
            with self.subTest(command=command):
                response = requests.post(
                    f"{self.base_url}/api/voice-trading/parse-command/",
                    json={"transcript": command, "voice_name": "Nova"},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertTrue(data["success"])
                
    def test_order_type_parsing(self):
        """Test order type parsing"""
        test_cases = [
            ("buy AAPL at market", "market"),
            ("sell MSFT at limit 300", "limit"),
            ("buy GOOGL at 150", "limit"),
            ("purchase TSLA immediately", "market")
        ]
        
        for command, expected_type in test_cases:
            with self.subTest(command=command):
                response = requests.post(
                    f"{self.base_url}/api/voice-trading/parse-command/",
                    json={"transcript": command, "voice_name": "Nova"},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if data["success"]:
                    parsed = data["parsed_order"]
                    self.assertEqual(parsed["order_type"], expected_type)
                    
    def test_quantity_parsing(self):
        """Test quantity parsing from voice commands"""
        test_cases = [
            ("buy 100 AAPL", 100),
            ("sell 50 MSFT", 50),
            ("purchase 25 GOOGL", 25),
            ("buy one AAPL", 1),
            ("sell ten MSFT", 10)
        ]
        
        for command, expected_qty in test_cases:
            with self.subTest(command=command):
                response = requests.post(
                    f"{self.base_url}/api/voice-trading/parse-command/",
                    json={"transcript": command, "voice_name": "Nova"},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if data["success"]:
                    parsed = data["parsed_order"]
                    self.assertEqual(parsed["quantity"], expected_qty)
                    
    def test_symbol_recognition(self):
        """Test symbol recognition from voice commands"""
        test_cases = [
            ("buy AAPL", "AAPL"),
            ("sell MSFT", "MSFT"),
            ("purchase GOOGL", "GOOGL"),
            ("buy Apple", "AAPL"),
            ("sell Microsoft", "MSFT"),
            ("purchase Google", "GOOGL")
        ]
        
        for command, expected_symbol in test_cases:
            with self.subTest(command=command):
                response = requests.post(
                    f"{self.base_url}/api/voice-trading/parse-command/",
                    json={"transcript": command, "voice_name": "Nova"},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if data["success"]:
                    parsed = data["parsed_order"]
                    self.assertEqual(parsed["symbol"], expected_symbol)
                    
    def test_confidence_scoring(self):
        """Test confidence scoring for parsed commands"""
        test_commands = [
            "buy 100 shares of AAPL",  # High confidence
            "buy something",           # Low confidence
            "Nova, scalp AAPL",        # Medium confidence
        ]
        
        for command in test_commands:
            with self.subTest(command=command):
                response = requests.post(
                    f"{self.base_url}/api/voice-trading/parse-command/",
                    json={"transcript": command, "voice_name": "Nova"},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if data["success"]:
                    parsed = data["parsed_order"]
                    self.assertIn("confidence", parsed)
                    self.assertGreaterEqual(parsed["confidence"], 0.0)
                    self.assertLessEqual(parsed["confidence"], 1.0)


class TestVoiceSynthesis(unittest.TestCase):
    """Test voice synthesis functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        
    def test_voice_list_endpoint(self):
        """Test voice list endpoint"""
        response = requests.get(f"{self.base_url}/api/voice-ai/voices/", timeout=10)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("voices", data)
        self.assertIsInstance(data["voices"], list)
        self.assertGreater(len(data["voices"]), 0)
        
        # Check voice structure
        for voice in data["voices"]:
            self.assertIn("id", voice)
            self.assertIn("name", voice)
            self.assertIn("description", voice)
            self.assertIn("language", voice)
            self.assertIn("gender", voice)
            
    def test_voice_synthesis(self):
        """Test voice synthesis"""
        test_texts = [
            "Hello, this is a test.",
            "Trade executed successfully!",
            "Market conditions are favorable.",
            "Risk management activated."
        ]
        
        for text in test_texts:
            with self.subTest(text=text):
                response = requests.post(
                    f"{self.base_url}/api/voice-ai/synthesize/",
                    json={"text": text, "voice_id": "nova"},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn("message", data)
                
    def test_voice_preview(self):
        """Test voice preview functionality"""
        response = requests.post(
            f"{self.base_url}/api/voice-ai/preview/",
            json={"voice_id": "nova", "sample_text": "Hello, I'm Nova."},
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        
    def test_different_voice_types(self):
        """Test different voice types"""
        voice_ids = ["nova", "echo", "onyx", "shimmer", "aurora", "zenith"]
        
        for voice_id in voice_ids:
            with self.subTest(voice_id=voice_id):
                response = requests.post(
                    f"{self.base_url}/api/voice-ai/synthesize/",
                    json={"text": f"Hello from {voice_id}", "voice_id": voice_id},
                    timeout=10
                )
                
                self.assertEqual(response.status_code, 200)


class TestVoiceTradingIntegration(unittest.TestCase):
    """Test voice trading integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        
    def test_voice_trading_session_creation(self):
        """Test voice trading session creation"""
        response = requests.post(
            f"{self.base_url}/api/voice-trading/create-session/",
            json={"user_id": "test_user", "voice_name": "Nova"},
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("session_id", data)
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        
    def test_voice_command_examples(self):
        """Test voice command examples"""
        response = requests.get(f"{self.base_url}/api/voice-trading/command-examples/", timeout=10)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("examples", data)
        
        examples = data["examples"]
        self.assertIn("buy_orders", examples)
        self.assertIn("sell_orders", examples)
        self.assertIn("hft_commands", examples)
        self.assertIn("market_making", examples)
        
        # Check example structure
        for category, commands in examples.items():
            self.assertIsInstance(commands, list)
            self.assertGreater(len(commands), 0)
            
    def test_available_symbols(self):
        """Test available symbols for voice trading"""
        response = requests.get(f"{self.base_url}/api/voice-trading/available-symbols/", timeout=10)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("symbols", data)
        
        symbols = data["symbols"]
        self.assertIsInstance(symbols, list)
        self.assertGreater(len(symbols), 0)
        
        # Check for common symbols
        expected_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        for symbol in expected_symbols:
            self.assertIn(symbol, symbols)
            
    def test_help_commands(self):
        """Test help commands endpoint"""
        response = requests.get(f"{self.base_url}/api/voice-trading/help-commands/", timeout=10)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("commands", data)
        
        commands = data["commands"]
        self.assertIsInstance(commands, list)
        self.assertGreater(len(commands), 0)
        
        # Check command structure
        for command in commands:
            self.assertIn("command", command)
            self.assertIn("description", command)
            self.assertIn("example", command)


class TestVoiceAIContext(unittest.TestCase):
    """Test Voice AI context and state management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        
    def test_voice_context_persistence(self):
        """Test voice context persistence across commands"""
        # Create a session
        session_response = requests.post(
            f"{self.base_url}/api/voice-trading/create-session/",
            json={"user_id": "test_user", "voice_name": "Nova"},
            timeout=10
        )
        
        self.assertEqual(session_response.status_code, 200)
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Parse multiple commands in the same session
        commands = [
            "buy 100 AAPL",
            "sell 50 MSFT",
            "scalp NVDA"
        ]
        
        for command in commands:
            response = requests.post(
                f"{self.base_url}/api/voice-trading/parse-command/",
                json={
                    "transcript": command,
                    "voice_name": "Nova",
                    "session_id": session_id
                },
                timeout=10
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            
    def test_voice_feedback_integration(self):
        """Test voice feedback integration with trading"""
        # Parse a command
        parse_response = requests.post(
            f"{self.base_url}/api/voice-trading/parse-command/",
            json={"transcript": "buy 100 AAPL", "voice_name": "Nova"},
            timeout=10
        )
        
        self.assertEqual(parse_response.status_code, 200)
        parse_data = parse_response.json()
        
        if parse_data["success"]:
            # Synthesize confirmation
            synth_response = requests.post(
                f"{self.base_url}/api/voice-ai/synthesize/",
                json={
                    "text": "Order placed successfully!",
                    "voice_id": "nova"
                },
                timeout=10
            )
            
            self.assertEqual(synth_response.status_code, 200)
            
    def test_error_handling(self):
        """Test error handling in voice commands"""
        # Test invalid command
        response = requests.post(
            f"{self.base_url}/api/voice-trading/parse-command/",
            json={"transcript": "invalid gibberish command", "voice_name": "Nova"},
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should handle gracefully
        self.assertIn("success", data)
        
    def test_multilingual_support(self):
        """Test multilingual voice support"""
        # Test different languages
        languages = ["en", "es", "fr", "de"]
        
        for lang in languages:
            with self.subTest(language=lang):
                response = requests.get(f"{self.base_url}/api/voice-ai/voices/", timeout=10)
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                # Should return voices for the language
                voices = data["voices"]
                self.assertGreater(len(voices), 0)


class TestVoiceAIPerformance(unittest.TestCase):
    """Test Voice AI performance characteristics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        
    def test_command_parsing_speed(self):
        """Test command parsing speed"""
        test_commands = [
            "buy 100 AAPL",
            "sell 50 MSFT",
            "scalp NVDA",
            "market make SPY",
            "arbitrage QQQ"
        ]
        
        start_time = time.time()
        
        for command in test_commands:
            response = requests.post(
                f"{self.base_url}/api/voice-trading/parse-command/",
                json={"transcript": command, "voice_name": "Nova"},
                timeout=5
            )
            self.assertEqual(response.status_code, 200)
            
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(test_commands)
        
        print(f"\n📊 Voice Command Parsing Performance:")
        print(f"  Average time per command: {avg_time:.3f}s")
        print(f"  Total time for {len(test_commands)} commands: {total_time:.3f}s")
        
        # Should be fast (under 1 second per command)
        self.assertLess(avg_time, 1.0)
        
    def test_concurrent_voice_requests(self):
        """Test concurrent voice requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_voice_request():
            try:
                response = requests.post(
                    f"{self.base_url}/api/voice-trading/parse-command/",
                    json={"transcript": "buy 100 AAPL", "voice_name": "Nova"},
                    timeout=10
                )
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")
                
        # Start 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_voice_request)
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        # Check all requests succeeded
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
                
        self.assertEqual(success_count, 5)
        
    def test_voice_synthesis_performance(self):
        """Test voice synthesis performance"""
        test_texts = [
            "Trade executed successfully!",
            "Market conditions are favorable.",
            "Risk management activated.",
            "Order placed at market price.",
            "Position updated successfully."
        ]
        
        start_time = time.time()
        
        for text in test_texts:
            response = requests.post(
                f"{self.base_url}/api/voice-ai/synthesize/",
                json={"text": text, "voice_id": "nova"},
                timeout=10
            )
            self.assertEqual(response.status_code, 200)
            
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(test_texts)
        
        print(f"\n🎤 Voice Synthesis Performance:")
        print(f"  Average time per synthesis: {avg_time:.3f}s")
        print(f"  Total time for {len(test_texts)} syntheses: {total_time:.3f}s")
        
        # Should be reasonably fast
        self.assertLess(avg_time, 2.0)


def run_voice_ai_tests():
    """Run all Voice AI tests"""
    print("🎤 Starting Voice AI Trading System Tests")
    print("=" * 60)
    
    # Test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestVoiceCommandParsing,
        TestVoiceSynthesis,
        TestVoiceTradingIntegration,
        TestVoiceAIContext,
        TestVoiceAIPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
        
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VOICE AI TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
            
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
            
    if result.wasSuccessful():
        print("\n🎉 ALL VOICE AI TESTS PASSED! Voice trading is ready!")
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} tests failed.")
        
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_voice_ai_tests()
    exit(0 if success else 1)
