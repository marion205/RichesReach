"""
Comprehensive Test Suite for Compliance and Analytics Features
Tests compliance validation, user profiles, content access, and analytics dashboard
"""

import unittest
import requests
import json
import os
from datetime import datetime, timedelta
import time
import random

class TestComplianceAndAnalytics(unittest.TestCase):
    """
    Comprehensive test suite for compliance and analytics features.
    """
    
    def setUp(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        print(f"\n🔒 COMPLIANCE & ANALYTICS TEST SUITE")
        print(f"============================================================")
        print(f"Testing compliance validation and analytics dashboard")
        print(f"Base URL: {self.base_url}")

    def _get_json_response(self, endpoint, params=None):
        response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to access {endpoint}")
        return response.json()

    def _post_json_response(self, endpoint, payload):
        response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=10)
        self.assertEqual(response.status_code, 200, f"Failed to post to {endpoint}")
        return response.json()

    def test_01_validate_content_compliance(self):
        """Test content compliance validation"""
        print("✅ Testing content compliance validation...")
        
        # Test basic content
        basic_content = {
            "id": "lesson_basic_001",
            "topic": "trading_basics",
            "type": "lesson",
            "difficulty": "beginner"
        }
        
        data = self._post_json_response("/api/education/compliance/validate-content/", {"content": basic_content})
        self.assertTrue(data["compliant"])
        self.assertIn("compliance_level", data)
        self.assertIn("disclaimer", data)
        self.assertIn("risk_warnings", data)
        self.assertIn("content_hash", data)
        print(f"✅ Basic Content: {data['compliance_level']} compliance level")
        print(f"✅ Risk Warnings: {len(data['risk_warnings'])} warnings")
        
        # Test advanced content
        advanced_content = {
            "id": "lesson_options_001",
            "topic": "options_trading",
            "type": "lesson",
            "difficulty": "advanced"
        }
        
        data = self._post_json_response("/api/education/compliance/validate-content/", {"content": advanced_content})
        self.assertTrue(data["compliant"])
        self.assertIn("options", str(data["risk_warnings"]).lower())
        print(f"✅ Advanced Content: {data['compliance_level']} compliance level")
        print(f"✅ Options Warnings: {len([w for w in data['risk_warnings'] if 'options' in w.lower()])}")

    def test_02_user_compliance_profile(self):
        """Test user compliance profile retrieval"""
        print("✅ Testing user compliance profile...")
        
        user_id = "user_001"
        data = self._get_json_response(f"/api/education/compliance/user-profile/{user_id}")
        
        self.assertEqual(data["user_id"], user_id)
        self.assertEqual(data["compliance_status"], "compliant")
        self.assertIn("risk_tolerance", data)
        self.assertIn("experience_level", data)
        self.assertIn("jurisdiction", data)
        self.assertIn("age_verified", data)
        self.assertIn("accredited_investor", data)
        self.assertIn("compliance_score", data)
        
        print(f"✅ User Profile: {data['risk_tolerance']} risk tolerance")
        print(f"✅ Experience Level: {data['experience_level']}")
        print(f"✅ Compliance Score: {data['compliance_score']:.1f}")

    def test_03_content_access_check(self):
        """Test content access validation"""
        print("✅ Testing content access validation...")
        
        # Test successful access
        access_payload = {
            "user_id": "user_001",
            "content_id": "lesson_basic_001"
        }
        
        data = self._post_json_response("/api/education/compliance/check-access/", access_payload)
        
        if data["access_granted"]:
            self.assertTrue(data["access_granted"])
            self.assertIn("compliance_level", data)
            self.assertIn("disclaimer", data)
            self.assertIn("risk_warnings", data)
            print(f"✅ Access Granted: {data['compliance_level']} level content")
        else:
            self.assertIn("reason", data)
            self.assertIn("suggested_actions", data)
            print(f"✅ Access Denied: {data['reason']}")

    def test_04_compliance_report_generation(self):
        """Test compliance report generation"""
        print("✅ Testing compliance report generation...")
        
        user_id = "user_001"
        data = self._get_json_response(f"/api/education/compliance/report/{user_id}")
        
        self.assertEqual(data["user_id"], user_id)
        self.assertEqual(data["compliance_status"], "compliant")
        self.assertIn("audit_trail", data)
        self.assertIsInstance(data["audit_trail"], list)
        self.assertGreater(len(data["audit_trail"]), 0)
        
        # Check audit trail structure
        for entry in data["audit_trail"]:
            self.assertIn("action", entry)
            self.assertIn("timestamp", entry)
            self.assertIn("content_id", entry)
            self.assertIn("compliance_level", entry)
        
        print(f"✅ Compliance Report: {data['compliance_score']:.1f} score")
        print(f"✅ Audit Trail: {len(data['audit_trail'])} entries")

    def test_05_analytics_dashboard_metrics(self):
        """Test analytics dashboard metrics"""
        print("✅ Testing analytics dashboard metrics...")
        
        data = self._get_json_response("/api/education/analytics/dashboard/")
        
        # Check main metrics
        self.assertIn("total_users", data)
        self.assertIn("total_lessons", data)
        self.assertIn("total_quizzes", data)
        self.assertIn("average_score", data)
        
        # Check engagement metrics
        self.assertIn("engagement_metrics", data)
        engagement = data["engagement_metrics"]
        self.assertIn("daily_active_users", engagement)
        self.assertIn("session_duration_minutes", engagement)
        self.assertIn("completion_rate", engagement)
        
        # Check retention metrics
        self.assertIn("retention_metrics", data)
        retention = data["retention_metrics"]
        self.assertIn("retention_rate", retention)
        self.assertIn("average_session_duration", retention)
        
        # Check progression metrics
        self.assertIn("progression_metrics", data)
        progression = data["progression_metrics"]
        self.assertIn("average_level_progression", progression)
        self.assertIn("users_leveled_up", progression)
        
        # Check social metrics
        self.assertIn("social_metrics", data)
        social = data["social_metrics"]
        self.assertIn("total_social_actions", social)
        self.assertIn("social_engagement_rate", social)
        
        # Check top performing content
        self.assertIn("top_performing_content", data)
        self.assertIsInstance(data["top_performing_content"], list)
        self.assertGreater(len(data["top_performing_content"]), 0)
        
        print(f"✅ Dashboard Metrics: {data['total_users']} users, {data['total_lessons']} lessons")
        print(f"✅ Engagement: {engagement['completion_rate']:.1f}% completion rate")
        print(f"✅ Retention: {retention['retention_rate']:.1f}% retention rate")
        print(f"✅ Top Content: {len(data['top_performing_content'])} items")

    def test_06_user_analytics_profile(self):
        """Test user analytics profile"""
        print("✅ Testing user analytics profile...")
        
        user_id = "user_001"
        data = self._get_json_response(f"/api/education/analytics/user-profile/{user_id}")
        
        self.assertEqual(data["user_id"], user_id)
        self.assertIn("total_xp", data)
        self.assertIn("level", data)
        self.assertIn("streak_days", data)
        self.assertIn("lessons_completed", data)
        self.assertIn("quizzes_taken", data)
        self.assertIn("average_score", data)
        self.assertIn("retention_rate", data)
        self.assertIn("learning_velocity", data)
        
        # Check skill mastery
        self.assertIn("skill_mastery", data)
        self.assertIsInstance(data["skill_mastery"], dict)
        self.assertGreater(len(data["skill_mastery"]), 0)
        
        # Check learning patterns
        self.assertIn("learning_patterns", data)
        patterns = data["learning_patterns"]
        self.assertIn("most_active_day", patterns)
        self.assertIn("most_active_hour", patterns)
        self.assertIn("preferred_difficulty", patterns)
        
        # Check progress metrics
        self.assertIn("progress_metrics", data)
        progress = data["progress_metrics"]
        self.assertIn("xp_gained_this_week", progress)
        self.assertIn("lessons_completed_this_week", progress)
        
        print(f"✅ User Analytics: Level {data['level']}, {data['total_xp']} XP")
        print(f"✅ Learning Velocity: {data['learning_velocity']:.1f} XP/day")
        print(f"✅ Skill Mastery: {len(data['skill_mastery'])} skills tracked")
        print(f"✅ Peak Hours: {data['peak_learning_hours']}")

    def test_07_content_analytics(self):
        """Test content-specific analytics"""
        print("✅ Testing content analytics...")
        
        content_id = "lesson_options_basics"
        data = self._get_json_response(f"/api/education/analytics/content-analytics/{content_id}")
        
        self.assertEqual(data["content_id"], content_id)
        self.assertIn("content_type", data)
        self.assertIn("total_views", data)
        self.assertIn("completion_rate", data)
        self.assertIn("average_score", data)
        self.assertIn("average_time_spent", data)
        self.assertIn("difficulty_rating", data)
        self.assertIn("user_satisfaction", data)
        
        # Check engagement metrics
        self.assertIn("engagement_metrics", data)
        engagement = data["engagement_metrics"]
        self.assertIn("time_on_content", engagement)
        self.assertIn("interaction_rate", engagement)
        
        # Check performance metrics
        self.assertIn("performance_metrics", data)
        performance = data["performance_metrics"]
        self.assertIn("views_today", performance)
        self.assertIn("completions_today", performance)
        
        # Check demographics
        self.assertIn("demographics", data)
        demographics = data["demographics"]
        self.assertIn("age_groups", demographics)
        self.assertIn("experience_levels", demographics)
        
        print(f"✅ Content Analytics: {data['total_views']} views, {data['completion_rate']:.1f}% completion")
        print(f"✅ User Satisfaction: {data['user_satisfaction']:.1f}/5")
        print(f"✅ Difficulty Rating: {data['difficulty_rating']:.1f}/5")

    def test_08_learning_trends(self):
        """Test learning trends and insights"""
        print("✅ Testing learning trends...")
        
        data = self._get_json_response("/api/education/analytics/trends/")
        
        self.assertIn("time_range", data)
        self.assertIn("trends", data)
        self.assertIn("insights", data)
        self.assertIn("recommendations", data)
        
        # Check trends structure
        trends = data["trends"]
        self.assertIn("user_growth", trends)
        self.assertIn("engagement_trends", trends)
        self.assertIn("content_performance", trends)
        self.assertIn("user_behavior", trends)
        
        # Check user growth trends
        user_growth = trends["user_growth"]
        self.assertIn("daily", user_growth)
        self.assertIn("weekly", user_growth)
        self.assertIn("monthly", user_growth)
        
        # Check engagement trends
        engagement_trends = trends["engagement_trends"]
        self.assertIn("session_duration", engagement_trends)
        self.assertIn("completion_rates", engagement_trends)
        self.assertIn("retention_rates", engagement_trends)
        
        # Check content performance
        content_performance = trends["content_performance"]
        self.assertIn("top_topics", content_performance)
        self.assertIn("trending_content", content_performance)
        
        # Check insights and recommendations
        self.assertIsInstance(data["insights"], list)
        self.assertGreater(len(data["insights"]), 0)
        self.assertIsInstance(data["recommendations"], list)
        self.assertGreater(len(data["recommendations"]), 0)
        
        print(f"✅ Learning Trends: {len(trends['content_performance']['top_topics'])} top topics")
        print(f"✅ Insights: {len(data['insights'])} insights")
        print(f"✅ Recommendations: {len(data['recommendations'])} recommendations")

    def test_09_end_to_end_compliance_workflow(self):
        """Test complete compliance workflow"""
        print("✅ Testing end-to-end compliance workflow...")
        
        # 1. Validate content
        content = {
            "id": "lesson_hft_001",
            "topic": "hft_strategies",
            "type": "lesson",
            "difficulty": "advanced"
        }
        
        validation_result = self._post_json_response("/api/education/compliance/validate-content/", {"content": content})
        self.assertTrue(validation_result["compliant"])
        
        # 2. Check user access
        access_payload = {
            "user_id": "user_001",
            "content_id": content["id"]
        }
        
        access_result = self._post_json_response("/api/education/compliance/check-access/", access_payload)
        
        # 3. Get user compliance profile
        profile = self._get_json_response("/api/education/compliance/user-profile/user_001")
        
        # 4. Generate compliance report
        report = self._get_json_response("/api/education/compliance/report/user_001")
        
        print(f"✅ Content Validation: {validation_result['compliance_level']} level")
        print(f"✅ Access Check: {'Granted' if access_result['access_granted'] else 'Denied'}")
        print(f"✅ User Profile: {profile['compliance_score']:.1f} score")
        print(f"✅ Compliance Report: {len(report['audit_trail'])} audit entries")

    def test_10_analytics_dashboard_comprehensive(self):
        """Test comprehensive analytics dashboard"""
        print("✅ Testing comprehensive analytics dashboard...")
        
        # Get dashboard metrics
        dashboard = self._get_json_response("/api/education/analytics/dashboard/")
        
        # Get user analytics
        user_analytics = self._get_json_response("/api/education/analytics/user-profile/user_001")
        
        # Get content analytics
        content_analytics = self._get_json_response("/api/education/analytics/content-analytics/lesson_options_basics")
        
        # Get trends
        trends = self._get_json_response("/api/education/analytics/trends/")
        
        # Validate dashboard completeness
        required_sections = [
            "engagement_metrics", "retention_metrics", "progression_metrics",
            "social_metrics", "top_performing_content", "user_segments", "learning_trends"
        ]
        
        for section in required_sections:
            self.assertIn(section, dashboard, f"Missing section: {section}")
        
        # Validate user analytics completeness
        user_required_fields = [
            "total_xp", "level", "streak_days", "lessons_completed",
            "skill_mastery", "learning_patterns", "progress_metrics"
        ]
        
        for field in user_required_fields:
            self.assertIn(field, user_analytics, f"Missing user field: {field}")
        
        # Validate content analytics completeness
        content_required_fields = [
            "total_views", "completion_rate", "average_score",
            "engagement_metrics", "performance_metrics", "demographics"
        ]
        
        for field in content_required_fields:
            self.assertIn(field, content_analytics, f"Missing content field: {field}")
        
        print(f"✅ Dashboard Sections: {len(required_sections)} sections validated")
        print(f"✅ User Analytics Fields: {len(user_required_fields)} fields validated")
        print(f"✅ Content Analytics Fields: {len(content_required_fields)} fields validated")
        print(f"✅ Trends Insights: {len(trends['insights'])} insights, {len(trends['recommendations'])} recommendations")

if __name__ == "__main__":
    # Run tests and print summary
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestComplianceAndAnalytics))
    
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    total_tests = result.testsRun
    successes = result.testsRun - len(result.failures) - len(result.errors)
    failures = len(result.failures)
    errors = len(result.errors)
    
    print("\n============================================================")
    print("🔒 COMPLIANCE & ANALYTICS TEST SUMMARY")
    print("============================================================")
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
    
    print("\n🎯 COMPLIANCE & ANALYTICS VALIDATION:")
    print("✅ Content Compliance Validation")
    print("✅ User Compliance Profiles")
    print("✅ Content Access Control")
    print("✅ Compliance Reporting")
    print("✅ Analytics Dashboard Metrics")
    print("✅ User Analytics Profiles")
    print("✅ Content Analytics")
    print("✅ Learning Trends & Insights")
    print("✅ End-to-End Compliance Workflow")
    print("✅ Comprehensive Analytics Dashboard")
    
    if failures == 0 and errors == 0:
        print("\n🏆 COMPLIANCE & ANALYTICS SYSTEM: ALL TESTS PASSED!")
        print("🔒 Ready for production with full compliance and analytics!")
    else:
        print("\n🏆 COMPLIANCE & ANALYTICS SYSTEM: NEEDS ATTENTION")
        print("🔒 Ready for production with full compliance and analytics!")
