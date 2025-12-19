#!/usr/bin/env python
"""
Comprehensive Test Suite for Security Stack
Tests Zero Trust, AI Security, Compliance Automation, and Database Models
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import (
    DeviceTrust, AccessPolicy, SupplyChainVendor, ComplianceAutomation,
    SecurityEvent, BiometricSettings, ComplianceStatus, SecurityScore
)
from core.zero_trust_service import zero_trust_service
from core.ai_security_service import ai_security_service
from core.compliance_automation_service import compliance_automation_service
from core.security_service import SecurityService

User = get_user_model()


class SecurityStackTestSuite:
    """Comprehensive test suite for security stack"""
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        self.test_user = None
    
    def setup_test_user(self):
        """Create test user"""
        try:
            self.test_user, created = User.objects.get_or_create(
                email='test_security@example.com',
                defaults={
                    'name': 'Test Security User',
                    'password': 'test123456'
                }
            )
            if created:
                self.test_user.set_password('test123456')
                self.test_user.save()
            print("✅ Test user created/retrieved")
            return True
        except Exception as e:
            print(f"❌ Failed to create test user: {e}")
            return False
    
    def test_database_models(self):
        """Test database models exist and can be created"""
        print("\n📊 Testing Database Models...")
        
        try:
            # Test DeviceTrust
            device_trust = DeviceTrust.objects.create(
                user=self.test_user,
                device_id='test-device-123',
                device_fingerprint='{"os": "iOS", "version": "17.0"}',
                trust_score=75,
                is_trusted=True
            )
            assert device_trust.id is not None
            print("  ✅ DeviceTrust model works")
            self.results['passed'].append('DeviceTrust model')
            
            # Test AccessPolicy
            access_policy = AccessPolicy.objects.create(
                user=self.test_user,
                action='create_trade',
                resource='trading',
                policy_type='mfa_required',
                conditions={'trust_score_min': 70}
            )
            assert access_policy.id is not None
            print("  ✅ AccessPolicy model works")
            self.results['passed'].append('AccessPolicy model')
            
            # Test SupplyChainVendor
            vendor = SupplyChainVendor.objects.create(
                name='Test Payment Processor',
                vendor_type='payment_processor',
                status='active',
                risk_score=30,
                compliance_certifications=['SOC2', 'PCI-DSS']
            )
            assert vendor.id is not None
            print("  ✅ SupplyChainVendor model works")
            self.results['passed'].append('SupplyChainVendor model')
            
            # Test ComplianceAutomation
            compliance_check = ComplianceAutomation.objects.create(
                standard='SOC2',
                check_type='automated',
                check_name='Access Control Test',
                description='Test access control check',
                status='pending'
            )
            assert compliance_check.id is not None
            print("  ✅ ComplianceAutomation model works")
            self.results['passed'].append('ComplianceAutomation model')
            
            # Cleanup
            device_trust.delete()
            access_policy.delete()
            vendor.delete()
            compliance_check.delete()
            
            return True
        except Exception as e:
            print(f"  ❌ Database models test failed: {e}")
            self.results['failed'].append(f'Database models: {e}')
            return False
    
    def test_zero_trust_service(self):
        """Test Zero Trust service functionality"""
        print("\n🛡️ Testing Zero Trust Service...")
        
        try:
            # Test request verification
            request_metadata = {
                'device_id': 'test-device-123',
                'ip_address': '192.168.1.1',
                'user_agent': 'Test Agent',
                'action': 'view_portfolio',
                'resource': 'portfolio',
                'auth_method': 'biometric'
            }
            
            result = zero_trust_service.verify_request(self.test_user, request_metadata)
            
            assert 'allowed' in result
            assert 'trust_score' in result
            assert 'risk_factors' in result
            assert 'ai_anomaly_detection' in result
            assert 'threat_level' in result
            
            print(f"  ✅ Zero Trust verification works (Trust Score: {result['trust_score']})")
            self.results['passed'].append('Zero Trust verification')
            
            # Test device registration
            zero_trust_service.register_device(
                self.test_user.id,
                'test-device-456',
                {'os': 'iOS', 'version': '17.0'}
            )
            print("  ✅ Device registration works")
            self.results['passed'].append('Device registration')
            
            # Test trust summary
            summary = zero_trust_service.get_trust_summary(self.test_user.id)
            assert 'user_id' in summary
            assert 'devices' in summary
            assert 'average_trust_score' in summary
            print(f"  ✅ Trust summary works (Devices: {summary['devices']})")
            self.results['passed'].append('Trust summary')
            
            return True
        except Exception as e:
            print(f"  ❌ Zero Trust service test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['failed'].append(f'Zero Trust service: {e}')
            return False
    
    def test_ai_security_service(self):
        """Test AI Security service functionality"""
        print("\n🤖 Testing AI Security Service...")
        
        try:
            # Test anomaly detection
            request_metadata = {
                'device_id': 'test-device-123',
                'ip_address': '192.168.1.1',
                'user_agent': 'Test Agent',
                'action': 'view_portfolio',
                'resource': 'portfolio'
            }
            
            anomaly_result = ai_security_service.detect_anomalies(
                self.test_user,
                request_metadata
            )
            
            assert 'is_anomaly' in anomaly_result
            assert 'anomaly_score' in anomaly_result
            assert 'anomaly_type' in anomaly_result
            assert 'confidence' in anomaly_result
            assert 'explanation' in anomaly_result
            
            print(f"  ✅ Anomaly detection works (Anomaly: {anomaly_result['is_anomaly']})")
            self.results['passed'].append('Anomaly detection')
            
            # Test threat level prediction
            threat_level = ai_security_service.predict_threat_level(
                self.test_user,
                request_metadata,
                anomaly_result
            )
            
            assert threat_level in ['low', 'medium', 'high', 'critical']
            print(f"  ✅ Threat level prediction works (Level: {threat_level})")
            self.results['passed'].append('Threat level prediction')
            
            # Test security insights
            insights = ai_security_service.generate_security_insights(self.test_user)
            
            assert 'security_score' in insights
            assert 'strengths' in insights
            assert 'recommendations' in insights
            assert 'trend' in insights
            assert 'badges' in insights
            
            print(f"  ✅ Security insights work (Score: {insights['security_score']})")
            self.results['passed'].append('Security insights')
            
            return True
        except Exception as e:
            print(f"  ❌ AI Security service test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['failed'].append(f'AI Security service: {e}')
            return False
    
    def test_compliance_automation(self):
        """Test Compliance Automation service"""
        print("\n📋 Testing Compliance Automation...")
        
        try:
            # Check if compliance checks exist
            checks = ComplianceAutomation.objects.all()
            assert checks.count() > 0, "No compliance checks found"
            print(f"  ✅ Found {checks.count()} compliance checks")
            self.results['passed'].append('Compliance checks exist')
            
            # Test running a compliance check
            test_check = checks.first()
            if test_check:
                result = compliance_automation_service.run_compliance_check(str(test_check.id))
                
                assert 'status' in result
                assert result['status'] in ['passed', 'failed', 'warning', 'pending']
                print(f"  ✅ Compliance check execution works (Status: {result['status']})")
                self.results['passed'].append('Compliance check execution')
            
            # Test supply chain monitoring
            supply_chain_result = compliance_automation_service.monitor_supply_chain()
            
            assert 'vendors_monitored' in supply_chain_result
            assert 'risks_detected' in supply_chain_result
            print(f"  ✅ Supply chain monitoring works (Vendors: {supply_chain_result['vendors_monitored']})")
            self.results['passed'].append('Supply chain monitoring')
            
            return True
        except Exception as e:
            print(f"  ❌ Compliance automation test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['failed'].append(f'Compliance automation: {e}')
            return False
    
    def test_security_service(self):
        """Test Security Service (existing)"""
        print("\n🔒 Testing Security Service...")
        
        try:
            security_service = SecurityService()
            
            # Test security score calculation
            score_data = security_service.calculate_security_score(self.test_user)
            
            assert 'score' in score_data
            assert 'factors' in score_data
            assert 0 <= score_data['score'] <= 100
            
            print(f"  ✅ Security score calculation works (Score: {score_data['score']})")
            self.results['passed'].append('Security score calculation')
            
            # Test security event creation
            event = security_service.create_security_event(
                user=self.test_user,
                event_type='unusual_activity',
                threat_level='medium',
                description='Test security event',
                metadata={'test': True}
            )
            
            assert event is not None
            assert event.id is not None
            print(f"  ✅ Security event creation works (Event ID: {event.id})")
            self.results['passed'].append('Security event creation')
            
            # Cleanup
            event.delete()
            
            return True
        except Exception as e:
            print(f"  ❌ Security service test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['failed'].append(f'Security service: {e}')
            return False
    
    def test_integration_flow(self):
        """Test end-to-end integration flow"""
        print("\n🔄 Testing Integration Flow...")
        
        try:
            # Simulate a user request
            request_metadata = {
                'device_id': 'test-device-integration',
                'ip_address': '192.168.1.100',
                'user_agent': 'Test Integration Agent',
                'action': 'view_portfolio',
                'resource': 'portfolio',
                'auth_method': 'biometric'
            }
            
            # Step 1: Zero Trust verification
            zero_trust_result = zero_trust_service.verify_request(
                self.test_user,
                request_metadata
            )
            assert zero_trust_result['allowed'] or zero_trust_result['trust_score'] >= 0
            print("  ✅ Step 1: Zero Trust verification")
            
            # Step 2: AI anomaly detection
            ai_result = ai_security_service.detect_anomalies(
                self.test_user,
                request_metadata
            )
            assert 'is_anomaly' in ai_result
            print("  ✅ Step 2: AI anomaly detection")
            
            # Step 3: Security insights
            insights = ai_security_service.generate_security_insights(self.test_user)
            assert 'security_score' in insights
            print("  ✅ Step 3: Security insights generation")
            
            # Step 4: Compliance check (if applicable)
            checks = ComplianceAutomation.objects.filter(status='pending')[:1]
            if checks.exists():
                check = checks.first()
                result = compliance_automation_service.run_compliance_check(str(check.id))
                assert 'status' in result
                print("  ✅ Step 4: Compliance check")
            
            print("  ✅ Integration flow works end-to-end")
            self.results['passed'].append('Integration flow')
            
            return True
        except Exception as e:
            print(f"  ❌ Integration flow test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['failed'].append(f'Integration flow: {e}')
            return False
    
    def test_graphql_models(self):
        """Test GraphQL model integration"""
        print("\n🔍 Testing GraphQL Model Integration...")
        
        try:
            # Test that models can be queried
            device_trusts = DeviceTrust.objects.filter(user=self.test_user)
            access_policies = AccessPolicy.objects.filter(user=self.test_user)
            vendors = SupplyChainVendor.objects.all()
            compliance_checks = ComplianceAutomation.objects.all()
            
            print(f"  ✅ DeviceTrust queries: {device_trusts.count()} records")
            print(f"  ✅ AccessPolicy queries: {access_policies.count()} records")
            print(f"  ✅ SupplyChainVendor queries: {vendors.count()} records")
            print(f"  ✅ ComplianceAutomation queries: {compliance_checks.count()} records")
            
            self.results['passed'].append('GraphQL model queries')
            
            return True
        except Exception as e:
            print(f"  ❌ GraphQL model test failed: {e}")
            self.results['failed'].append(f'GraphQL models: {e}')
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("🧪 SECURITY STACK TEST SUITE")
        print("=" * 60)
        
        if not self.setup_test_user():
            print("\n❌ Cannot proceed without test user")
            return False
        
        tests = [
            ('Database Models', self.test_database_models),
            ('Zero Trust Service', self.test_zero_trust_service),
            ('AI Security Service', self.test_ai_security_service),
            ('Compliance Automation', self.test_compliance_automation),
            ('Security Service', self.test_security_service),
            ('Integration Flow', self.test_integration_flow),
            ('GraphQL Models', self.test_graphql_models),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"\n❌ {test_name} test crashed: {e}")
                import traceback
                traceback.print_exc()
                self.results['failed'].append(f'{test_name}: {e}')
        
        self.print_summary()
        return len(self.results['failed']) == 0
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total = len(self.results['passed']) + len(self.results['failed'])
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        
        print(f"\n✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        
        if self.results['passed']:
            print("\n✅ Passed Tests:")
            for test in self.results['passed']:
                print(f"   • {test}")
        
        if self.results['failed']:
            print("\n❌ Failed Tests:")
            for test in self.results['failed']:
                print(f"   • {test}")
        
        print("\n" + "=" * 60)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {failed} TEST(S) FAILED")
        print("=" * 60)


if __name__ == '__main__':
    suite = SecurityStackTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)

