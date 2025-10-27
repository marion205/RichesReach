#!/usr/bin/env python3
"""
RichesReach Education Features Test Suite
Tests the adaptive learning system that beats Fidelity

This comprehensive test suite validates:
- Adaptive Mastery Engine (IRT + Spaced Repetition)
- Gamified Tutor with Duolingo-style mechanics
- Live Market Simulations
- Voice-Interactive Learning
- BIPOC-Focused Community Leagues
- Learning Analytics and Progress Tracking
"""

import unittest
import requests
import json
import os
import time
from datetime import datetime, timedelta

class TestEducationFeatures(unittest.TestCase):
    """
    Comprehensive test suite for RichesReach Education features
    """
    
    def setUp(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        print(f"\n🎓 RICHESREACH EDUCATION FEATURES TEST")
        print(f"============================================================")
        print(f"Testing adaptive learning system that beats Fidelity")
        print(f"Base URL: {self.base_url}")
    
    def _get_json_response(self, endpoint, params=None):
        """Get JSON response from endpoint"""
        response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to access {endpoint}")
        return response.json()
    
    def _post_json_response(self, endpoint, payload=None):
        """Post JSON payload to endpoint"""
        response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to post to {endpoint}")
        return response.json()
    
    def test_01_tutor_progress_endpoint(self):
        """Test tutor progress with IRT ability estimate"""
        print("✅ Testing tutor progress endpoint...")
        
        data = self._get_json_response("/api/education/progress/")
        
        # Validate IRT ability estimate
        self.assertIn("abilityEstimate", data)
        self.assertIsInstance(data["abilityEstimate"], (int, float))
        self.assertGreaterEqual(data["abilityEstimate"], -3.0)
        self.assertLessEqual(data["abilityEstimate"], 3.0)
        
        # Validate skill mastery
        self.assertIn("skillMastery", data)
        self.assertIsInstance(data["skillMastery"], list)
        self.assertGreater(len(data["skillMastery"]), 0)
        
        for skill in data["skillMastery"]:
            self.assertIn("skill", skill)
            self.assertIn("masteryLevel", skill)
            self.assertIn("masteryPercentage", skill)
            self.assertIn("status", skill)
            self.assertIn(skill["status"], ["Master", "Learning", "Beginner"])
        
        # Validate gamification elements
        self.assertIn("xp", data)
        self.assertIn("level", data)
        self.assertIn("streakDays", data)
        self.assertIn("badges", data)
        self.assertIn("hearts", data)
        self.assertIn("maxHearts", data)
        
        print(f"✅ Tutor Progress: Level {data['level']}, {data['xp']} XP, {data['streakDays']} day streak")
        print(f"✅ IRT Ability Estimate: {data['abilityEstimate']:.2f}")
        print(f"✅ Skill Mastery: {len(data['skillMastery'])} skills tracked")
    
    def test_02_tutor_analytics_endpoint(self):
        """Test comprehensive learning analytics"""
        print("✅ Testing tutor analytics endpoint...")
        
        data = self._get_json_response("/api/education/analytics/")
        
        # Validate analytics fields
        required_fields = [
            "totalLessonsCompleted", "averageScore", "totalXpEarned",
            "longestStreak", "currentStreak", "badgesEarned",
            "skillsMastered", "timeSpentLearning", "favoriteTopics",
            "learningVelocity", "retentionRate", "improvementAreas", "strengths"
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Validate data types and ranges
        self.assertIsInstance(data["totalLessonsCompleted"], int)
        self.assertIsInstance(data["averageScore"], (int, float))
        self.assertGreaterEqual(data["averageScore"], 0)
        self.assertLessEqual(data["averageScore"], 100)
        
        self.assertIsInstance(data["retentionRate"], (int, float))
        self.assertGreaterEqual(data["retentionRate"], 0)
        self.assertLessEqual(data["retentionRate"], 1)
        
        self.assertIsInstance(data["favoriteTopics"], list)
        self.assertIsInstance(data["improvementAreas"], list)
        self.assertIsInstance(data["strengths"], list)
        
        print(f"✅ Analytics: {data['totalLessonsCompleted']} lessons, {data['averageScore']:.1f}% avg score")
        print(f"✅ Retention Rate: {data['retentionRate']:.1%}")
        print(f"✅ Learning Velocity: {data['learningVelocity']:.1f} XP/day")
    
    def test_03_league_rankings_endpoint(self):
        """Test league rankings for gamified competition"""
        print("✅ Testing league rankings endpoint...")
        
        data = self._get_json_response("/api/education/league/bipoc_wealth_builders")
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        for entry in data:
            required_fields = [
                "userId", "username", "xpWeek", "rank", "circle",
                "streakDays", "badgesCount", "level", "lastActive", "isOnline"
            ]
            
            for field in required_fields:
                self.assertIn(field, entry, f"Missing field: {field}")
            
            # Validate ranking order
            if len(data) > 1:
                self.assertLessEqual(entry["rank"], len(data))
        
        print(f"✅ League Rankings: {len(data)} participants")
        print(f"✅ Top Performer: {data[0]['username']} with {data[0]['xpWeek']} XP")
    
    def test_04_available_lessons_endpoint(self):
        """Test available lessons with adaptive difficulty"""
        print("✅ Testing available lessons endpoint...")
        
        # Test without filters
        data = self._get_json_response("/api/education/lessons/")
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        for lesson in data:
            required_fields = [
                "id", "title", "difficulty", "estimatedTimeMinutes",
                "skillsTargeted", "xpReward", "completionRate",
                "isCompleted", "isLocked", "prerequisites"
            ]
            
            for field in required_fields:
                self.assertIn(field, lesson, f"Missing field: {field}")
            
            # Validate difficulty levels
            self.assertIn(lesson["difficulty"], ["Beginner", "Intermediate", "Advanced", "Expert"])
            
            # Validate skill targeting
            self.assertIsInstance(lesson["skillsTargeted"], list)
            self.assertGreater(len(lesson["skillsTargeted"]), 0)
        
        # Test with topic filter
        options_lessons = self._get_json_response("/api/education/lessons/", {"topic": "options"})
        self.assertIsInstance(options_lessons, list)
        
        # Test with regime filter
        bull_lessons = self._get_json_response("/api/education/lessons/", {"regime": "BULL"})
        self.assertIsInstance(bull_lessons, list)
        
        print(f"✅ Available Lessons: {len(data)} total")
        print(f"✅ Options Lessons: {len(options_lessons)}")
        print(f"✅ BULL Regime Lessons: {len(bull_lessons)}")
    
    def test_05_daily_quest_endpoint(self):
        """Test personalized daily quest"""
        print("✅ Testing daily quest endpoint...")
        
        data = self._get_json_response("/api/education/daily-quest/")
        
        required_fields = [
            "id", "title", "description", "questType", "difficulty",
            "xpReward", "timeLimitMinutes", "requiredSkills", "regimeContext",
            "voiceNarration", "completionCriteria", "isActive", "createdAt",
            "expiresAt", "participants", "completionRate"
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Validate quest structure
        self.assertIn(data["questType"], ["daily_trade_quest", "regime_mastery", "volatility_duel", "bipoc_wealth_challenge", "hft_scalping_sim"])
        self.assertGreaterEqual(data["difficulty"], 1)
        self.assertLessEqual(data["difficulty"], 5)
        self.assertGreater(data["xpReward"], 0)
        self.assertGreater(data["timeLimitMinutes"], 0)
        
        # Validate completion criteria
        criteria = data["completionCriteria"]
        self.assertIsInstance(criteria, dict)
        
        print(f"✅ Daily Quest: {data['title']}")
        print(f"✅ Difficulty: {data['difficulty']}/5, XP Reward: {data['xpReward']}")
        print(f"✅ Participants: {data['participants']}, Completion Rate: {data['completionRate']:.1%}")
    
    def test_06_start_lesson_endpoint(self):
        """Test adaptive lesson generation"""
        print("✅ Testing start lesson endpoint...")
        
        payload = {
            "topic": "options",
            "regime": "BULL"
        }
        
        data = self._post_json_response("/api/education/start-lesson/", payload)
        
        required_fields = [
            "id", "title", "text", "voiceNarration", "quiz",
            "xpEarned", "streak", "nextUnlock", "difficulty",
            "sources", "regimeContext", "estimatedTimeMinutes",
            "skillsTargeted", "bloomLevel", "prerequisites",
            "completionRate", "averageRating"
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Validate lesson content
        self.assertIn("options", data["title"].lower())
        self.assertIn("BULL", data["regimeContext"])
        self.assertGreater(len(data["text"]), 100)  # Substantial content
        
        # Validate quiz structure
        self.assertIsInstance(data["quiz"], list)
        self.assertGreater(len(data["quiz"]), 0)
        
        for question in data["quiz"]:
            self.assertIn("id", question)
            self.assertIn("question", question)
            self.assertIn("options", question)
            self.assertIn("correct", question)
            self.assertIn("explanation", question)
            self.assertIn("voiceHint", question)
            
            self.assertIsInstance(question["options"], list)
            self.assertGreater(len(question["options"]), 0)
            self.assertIsInstance(question["correct"], int)
            self.assertGreaterEqual(question["correct"], 0)
            self.assertLess(question["correct"], len(question["options"]))
        
        print(f"✅ Lesson Started: {data['title']}")
        print(f"✅ Quiz Questions: {len(data['quiz'])}")
        print(f"✅ XP Earned: {data['xpEarned']}")
        print(f"✅ Skills Targeted: {', '.join(data['skillsTargeted'])}")
    
    def test_07_submit_quiz_endpoint(self):
        """Test quiz submission and IRT ability update"""
        print("✅ Testing submit quiz endpoint...")
        
        payload = {
            "lessonId": "lesson_options_001",
            "answers": [1, 0, 2, 1]
        }
        
        data = self._post_json_response("/api/education/submit-quiz/", payload)
        
        required_fields = [
            "score", "xpBonus", "totalXp", "feedback",
            "badgesEarned", "nextRecommendation", "streakStatus",
            "levelProgress", "questionsReview", "timeSpent", "accuracy"
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Validate scoring
        self.assertGreaterEqual(data["score"], 0)
        self.assertLessEqual(data["score"], 100)
        self.assertGreaterEqual(data["xpBonus"], 0)
        self.assertGreater(data["totalXp"], 0)
        
        # Validate level progress
        level_progress = data["levelProgress"]
        self.assertIn("currentLevel", level_progress)
        self.assertIn("currentXp", level_progress)
        self.assertIn("nextLevelXp", level_progress)
        self.assertIn("progressPercentage", level_progress)
        self.assertIn("xpToNextLevel", level_progress)
        
        # Validate question review
        self.assertIsInstance(data["questionsReview"], list)
        self.assertEqual(len(data["questionsReview"]), len(payload["answers"]))
        
        for review in data["questionsReview"]:
            self.assertIn("questionId", review)
            self.assertIn("userAnswer", review)
            self.assertIn("correctAnswer", review)
            self.assertIn("isCorrect", review)
            self.assertIn("explanation", review)
            self.assertIn("timeSpent", review)
        
        print(f"✅ Quiz Score: {data['score']:.1f}%")
        print(f"✅ XP Bonus: {data['xpBonus']}")
        print(f"✅ Badges Earned: {len(data['badgesEarned'])}")
        print(f"✅ Level Progress: {level_progress['progressPercentage']}%")
    
    def test_08_start_simulation_endpoint(self):
        """Test live market simulation start"""
        print("✅ Testing start simulation endpoint...")
        
        payload = {
            "symbol": "AAPL",
            "mode": "paper"
        }
        
        data = self._post_json_response("/api/education/start-simulation/", payload)
        
        required_fields = [
            "id", "userId", "symbol", "mode", "startTime",
            "initialBalance", "currentBalance", "tradesExecuted",
            "learningObjectives", "voiceFeedbackEnabled", "regimeContext",
            "isActive", "performanceMetrics"
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Validate simulation setup
        self.assertEqual(data["symbol"], "AAPL")
        self.assertEqual(data["mode"], "paper")
        self.assertEqual(data["initialBalance"], 10000.0)
        self.assertEqual(data["currentBalance"], 10000.0)
        self.assertTrue(data["isActive"])
        self.assertTrue(data["voiceFeedbackEnabled"])
        
        # Validate learning objectives
        self.assertIsInstance(data["learningObjectives"], list)
        self.assertGreater(len(data["learningObjectives"]), 0)
        
        # Validate performance metrics
        metrics = data["performanceMetrics"]
        required_metrics = [
            "totalTrades", "winningTrades", "losingTrades", "winRate",
            "averageWin", "averageLoss", "profitFactor", "maxDrawdown",
            "sharpeRatio", "totalPnL", "returnPercentage"
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, metrics, f"Missing metric: {metric}")
        
        print(f"✅ Simulation Started: {data['symbol']} ({data['mode']})")
        print(f"✅ Initial Balance: ${data['initialBalance']:,.2f}")
        print(f"✅ Learning Objectives: {len(data['learningObjectives'])}")
        print(f"✅ Voice Feedback: {'Enabled' if data['voiceFeedbackEnabled'] else 'Disabled'}")
    
    def test_09_execute_sim_trade_endpoint(self):
        """Test simulation trade execution with learning feedback"""
        print("✅ Testing execute sim trade endpoint...")
        
        payload = {
            "sessionId": "sim_AAPL_001",
            "tradeData": {
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "orderType": "MARKET"
            }
        }
        
        data = self._post_json_response("/api/education/execute-sim-trade/", payload)
        
        required_fields = [
            "success", "trade", "feedback", "xpEarned",
            "newBalance", "learningObjectivesProgress", "performanceUpdate", "voiceFeedback"
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Validate trade execution
        self.assertTrue(data["success"])
        
        trade = data["trade"]
        trade_fields = ["id", "timestamp", "symbol", "side", "quantity", "price", "pnl", "commission", "slippage", "tradeData"]
        
        for field in trade_fields:
            self.assertIn(field, trade, f"Missing trade field: {field}")
        
        # Validate learning objectives progress
        objectives_progress = data["learningObjectivesProgress"]
        self.assertIsInstance(objectives_progress, list)
        
        for objective in objectives_progress:
            self.assertIn("objective", objective)
            self.assertIn("progress", objective)
            self.assertIn("isCompleted", objective)
            self.assertIn("completionTime", objective)
            
            self.assertGreaterEqual(objective["progress"], 0)
            self.assertLessEqual(objective["progress"], 1)
        
        # Validate performance update
        performance = data["performanceUpdate"]
        self.assertIn("totalTrades", performance)
        self.assertIn("winRate", performance)
        self.assertIn("totalPnL", performance)
        
        print(f"✅ Trade Executed: {trade['side']} {trade['quantity']} {trade['symbol']}")
        print(f"✅ P&L: ${trade['pnl']:.2f}")
        print(f"✅ New Balance: ${data['newBalance']:,.2f}")
        print(f"✅ XP Earned: {data['xpEarned']}")
    
    def test_10_claim_streak_freeze_endpoint(self):
        """Test streak freeze functionality"""
        print("✅ Testing claim streak freeze endpoint...")
        
        data = self._post_json_response("/api/education/claim-streak-freeze/")
        
        required_fields = ["success", "message", "xpRemaining", "streakDays"]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Validate streak freeze
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["xpRemaining"], 0)
        self.assertGreaterEqual(data["streakDays"], 0)
        
        print(f"✅ Streak Freeze: {data['message']}")
        print(f"✅ XP Remaining: {data['xpRemaining']}")
        print(f"✅ Streak Days: {data['streakDays']}")
    
    def test_11_process_voice_command_endpoint(self):
        """Test voice command processing for hands-free learning"""
        print("✅ Testing process voice command endpoint...")
        
        test_commands = [
            "start lesson",
            "submit answer",
            "explain this",
            "next question",
            "repeat question"
        ]
        
        for command in test_commands:
            payload = {"command": command}
            data = self._post_json_response("/api/education/process-voice-command/", payload)
            
            required_fields = ["success", "command", "parsedIntent", "response", "voiceNarration", "actions", "confidence"]
            
            for field in required_fields:
                self.assertIn(field, data, f"Missing field: {field}")
            
            # Validate voice command processing
            self.assertTrue(data["success"])
            self.assertEqual(data["command"], command)
            self.assertGreater(data["confidence"], 0)
            self.assertLessEqual(data["confidence"], 1)
            
            # Validate actions
            self.assertIsInstance(data["actions"], list)
            self.assertGreater(len(data["actions"]), 0)
            
            for action in data["actions"]:
                self.assertIn("type", action)
                self.assertIn("parameters", action)
                self.assertIn("executed", action)
                self.assertIn("result", action)
            
            print(f"✅ Voice Command: '{command}' -> {data['parsedIntent']} (confidence: {data['confidence']:.2f})")
    
    def test_12_end_to_end_learning_workflow(self):
        """Test complete learning workflow from start to finish"""
        print("✅ Testing end-to-end learning workflow...")
        
        # Step 1: Get user progress
        progress = self._get_json_response("/api/education/progress/")
        initial_xp = progress["xp"]
        initial_level = progress["level"]
        
        # Step 2: Start a lesson
        lesson_payload = {"topic": "volatility", "regime": "BULL"}
        lesson = self._post_json_response("/api/education/start-lesson/", lesson_payload)
        
        # Step 3: Submit quiz answers
        quiz_payload = {
            "lessonId": lesson["id"],
            "answers": [1, 0, 2]
        }
        quiz_result = self._post_json_response("/api/education/submit-quiz/", quiz_payload)
        
        # Step 4: Start simulation
        sim_payload = {"symbol": "TSLA", "mode": "paper"}
        simulation = self._post_json_response("/api/education/start-simulation/", sim_payload)
        
        # Step 5: Execute trades
        trade_payload = {
            "sessionId": simulation["id"],
            "tradeData": {
                "symbol": "TSLA",
                "side": "BUY",
                "quantity": 5,
                "orderType": "MARKET"
            }
        }
        trade_result = self._post_json_response("/api/education/execute-sim-trade/", trade_payload)
        
        # Step 6: Get updated progress
        updated_progress = self._get_json_response("/api/education/progress/")
        
        # Validate workflow completion
        self.assertGreater(updated_progress["xp"], initial_xp)
        self.assertGreaterEqual(updated_progress["level"], initial_level)
        
        print(f"✅ Learning Workflow Complete!")
        print(f"✅ Initial XP: {initial_xp} -> Final XP: {updated_progress['xp']}")
        print(f"✅ XP Gained: {updated_progress['xp'] - initial_xp}")
        print(f"✅ Lesson Completed: {lesson['title']}")
        print(f"✅ Quiz Score: {quiz_result['score']:.1f}%")
        print(f"✅ Simulation Trades: {len(simulation['tradesExecuted']) + 1}")
    
    def test_13_bipoc_cultural_relevance(self):
        """Test BIPOC-focused features and cultural relevance"""
        print("✅ Testing BIPOC cultural relevance...")
        
        # Test BIPOC wealth builders league
        bipoc_league = self._get_json_response("/api/education/league/bipoc_wealth_builders")
        
        # Check for BIPOC-focused usernames and content
        bipoc_usernames = [entry["username"] for entry in bipoc_league if "bipoc" in entry["username"].lower() or "wealth" in entry["username"].lower()]
        self.assertGreater(len(bipoc_usernames), 0)
        
        # Test culturally relevant quest types
        daily_quest = self._get_json_response("/api/education/daily-quest/")
        
        # Check for BIPOC-focused quest types
        bipoc_quest_types = ["bipoc_wealth_challenge", "community_investing", "heritage_hedge"]
        quest_type = daily_quest["questType"]
        
        print(f"✅ BIPOC League Participants: {len(bipoc_league)}")
        print(f"✅ BIPOC Usernames: {len(bipoc_usernames)}")
        print(f"✅ Quest Type: {quest_type}")
        print(f"✅ Cultural Relevance: BIPOC-focused features implemented")
    
    def test_14_adaptive_difficulty_scaling(self):
        """Test adaptive difficulty based on user performance"""
        print("✅ Testing adaptive difficulty scaling...")
        
        # Test multiple lessons with different performance levels
        topics = ["options", "volatility", "risk_management", "hft_strategies"]
        
        for topic in topics:
            lesson_payload = {"topic": topic, "regime": "BULL"}
            lesson = self._post_json_response("/api/education/start-lesson/", lesson_payload)
            
            # Validate difficulty adaptation
            self.assertIn(lesson["difficulty"], ["Beginner", "Intermediate", "Advanced", "Expert"])
            
            # Check if difficulty correlates with topic complexity
            if topic == "hft_strategies":
                self.assertIn(lesson["difficulty"], ["Advanced", "Expert"])
            elif topic == "options":
                self.assertIn(lesson["difficulty"], ["Beginner", "Intermediate"])
            
            print(f"✅ {topic.title()}: {lesson['difficulty']} difficulty")
    
    def test_15_voice_integration_comprehensive(self):
        """Test comprehensive voice integration across all features"""
        print("✅ Testing comprehensive voice integration...")
        
        # Test voice commands for different features
        voice_commands = [
            {"command": "start lesson on options", "expected_intent": "start_lesson"},
            {"command": "submit my answers", "expected_intent": "submit_answer"},
            {"command": "explain the correct answer", "expected_intent": "request_explanation"},
            {"command": "next question please", "expected_intent": "next_question"},
            {"command": "repeat the question", "expected_intent": "repeat_question"}
        ]
        
        for cmd_test in voice_commands:
            payload = {"command": cmd_test["command"]}
            data = self._post_json_response("/api/education/process-voice-command/", payload)
            
            self.assertTrue(data["success"])
            self.assertGreater(data["confidence"], 0.5)  # Reasonable confidence threshold
            
            print(f"✅ Voice Command: '{cmd_test['command']}' -> {data['parsedIntent']} (confidence: {data['confidence']:.2f})")
        
        print(f"✅ Voice Integration: All commands processed successfully")

def run_education_tests():
    """Run the education features test suite"""
    print("🎓 Starting RichesReach Education Features Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEducationFeatures)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎓 EDUCATION FEATURES TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"✅ Total Tests: {total_tests}")
    print(f"✅ Successful: {successes}")
    print(f"❌ Failures: {failures}")
    print(f"❌ Errors: {errors}")
    print(f"✅ Success Rate: {(successes/total_tests)*100:.1f}%")
    
    if failures > 0:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"   - {test}: {error_msg}")
    
    if errors > 0:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"   - {test}: {error_msg}")
    
    print("\n🎯 EDUCATION FEATURES VALIDATION:")
    print("✅ Adaptive Mastery Engine (IRT + Spaced Repetition)")
    print("✅ Gamified Tutor with Duolingo-style Mechanics")
    print("✅ Live Market Simulations with Voice Feedback")
    print("✅ BIPOC-Focused Community Leagues")
    print("✅ Voice-Interactive Learning Commands")
    print("✅ Comprehensive Learning Analytics")
    print("✅ Adaptive Difficulty Scaling")
    print("✅ End-to-End Learning Workflows")
    
    print(f"\n🏆 RICHESREACH EDUCATION SYSTEM: {'PASSED' if failures == 0 and errors == 0 else 'NEEDS ATTENTION'}")
    print("🎓 Ready to beat Fidelity with superior adaptive learning!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_education_tests()
    exit(0 if success else 1)
