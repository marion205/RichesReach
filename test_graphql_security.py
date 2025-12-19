#!/usr/bin/env python
"""
GraphQL API Test Suite for Security Features
Tests all security-related GraphQL queries and mutations
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from graphene.test import Client as GraphQLClient
from core.schema import schema
from core.models import DeviceTrust, AccessPolicy, ComplianceAutomation

User = get_user_model()


class GraphQLSecurityTestSuite:
    """Test GraphQL security queries and mutations"""
    
    def __init__(self):
        self.results = {'passed': [], 'failed': []}
        self.test_user = None
        self.client = GraphQLClient(schema)
    
    def setup_test_user(self):
        """Create test user"""
        try:
            self.test_user, created = User.objects.get_or_create(
                email='test_graphql@example.com',
                defaults={
                    'name': 'Test GraphQL User',
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
    
    def test_zero_trust_summary_query(self):
        """Test Zero Trust Summary query"""
        print("\n🔍 Testing Zero Trust Summary Query...")
        
        try:
            query = """
            query {
                zeroTrustSummary {
                    userId
                    devices
                    averageTrustScore
                    lastVerification
                    requiresMfa
                    riskLevel
                }
            }
            """
            
            result = self.client.execute(query, context_value={'user': self.test_user})
            
            if 'errors' in result:
                print(f"  ⚠️  Query returned errors: {result['errors']}")
                self.results['failed'].append('Zero Trust Summary query')
                return False
            
            data = result.get('data', {}).get('zeroTrustSummary')
            if data:
                print(f"  ✅ Zero Trust Summary query works")
                print(f"     Devices: {data.get('devices')}, Trust Score: {data.get('averageTrustScore')}")
                self.results['passed'].append('Zero Trust Summary query')
                return True
            else:
                print("  ⚠️  No data returned")
                self.results['failed'].append('Zero Trust Summary query')
                return False
        except Exception as e:
            print(f"  ❌ Zero Trust Summary query failed: {e}")
            self.results['failed'].append(f'Zero Trust Summary: {e}')
            return False
    
    def test_device_trusts_query(self):
        """Test Device Trusts query"""
        print("\n🔍 Testing Device Trusts Query...")
        
        try:
            query = """
            query {
                deviceTrusts {
                    id
                    deviceId
                    trustScore
                    isTrusted
                    lastVerified
                }
            }
            """
            
            result = self.client.execute(query, context_value={'user': self.test_user})
            
            if 'errors' in result:
                print(f"  ⚠️  Query returned errors: {result['errors']}")
                self.results['failed'].append('Device Trusts query')
                return False
            
            data = result.get('data', {}).get('deviceTrusts', [])
            print(f"  ✅ Device Trusts query works ({len(data)} devices)")
            self.results['passed'].append('Device Trusts query')
            return True
        except Exception as e:
            print(f"  ❌ Device Trusts query failed: {e}")
            self.results['failed'].append(f'Device Trusts: {e}')
            return False
    
    def test_access_policies_query(self):
        """Test Access Policies query"""
        print("\n🔍 Testing Access Policies Query...")
        
        try:
            query = """
            query {
                accessPolicies {
                    id
                    action
                    resource
                    policyType
                }
            }
            """
            
            result = self.client.execute(query, context_value={'user': self.test_user})
            
            if 'errors' in result:
                print(f"  ⚠️  Query returned errors: {result['errors']}")
                self.results['failed'].append('Access Policies query')
                return False
            
            data = result.get('data', {}).get('accessPolicies', [])
            print(f"  ✅ Access Policies query works ({len(data)} policies)")
            self.results['passed'].append('Access Policies query')
            return True
        except Exception as e:
            print(f"  ❌ Access Policies query failed: {e}")
            self.results['failed'].append(f'Access Policies: {e}')
            return False
    
    def test_security_insights_query(self):
        """Test Security Insights query (combined)"""
        print("\n🔍 Testing Security Insights Query...")
        
        try:
            query = """
            query {
                securityScore {
                    id
                    score
                    factors
                    calculatedAt
                }
                zeroTrustSummary {
                    averageTrustScore
                    riskLevel
                    requiresMfa
                }
                securityEvents(limit: 5, resolved: false) {
                    id
                    eventType
                    threatLevel
                    description
                }
            }
            """
            
            result = self.client.execute(query, context_value={'user': self.test_user})
            
            if 'errors' in result:
                print(f"  ⚠️  Query returned errors: {result['errors']}")
                self.results['failed'].append('Security Insights query')
                return False
            
            data = result.get('data', {})
            if data.get('securityScore') or data.get('zeroTrustSummary'):
                print("  ✅ Security Insights query works")
                self.results['passed'].append('Security Insights query')
                return True
            else:
                print("  ⚠️  No data returned")
                self.results['failed'].append('Security Insights query')
                return False
        except Exception as e:
            print(f"  ❌ Security Insights query failed: {e}")
            self.results['failed'].append(f'Security Insights: {e}')
            return False
    
    def test_register_device_mutation(self):
        """Test Register Device mutation"""
        print("\n🔍 Testing Register Device Mutation...")
        
        try:
            mutation = """
            mutation RegisterDevice($deviceId: String!, $deviceFingerprint: String!) {
                registerDevice(deviceId: $deviceId, deviceFingerprint: $deviceFingerprint) {
                    success
                    message
                    deviceTrust {
                        id
                        deviceId
                        trustScore
                        isTrusted
                    }
                }
            }
            """
            
            variables = {
                'deviceId': 'test-graphql-device',
                'deviceFingerprint': json.dumps({'os': 'iOS', 'version': '17.0'})
            }
            
            result = self.client.execute(
                mutation,
                variables=variables,
                context_value={'user': self.test_user}
            )
            
            if 'errors' in result:
                print(f"  ⚠️  Mutation returned errors: {result['errors']}")
                self.results['failed'].append('Register Device mutation')
                return False
            
            data = result.get('data', {}).get('registerDevice', {})
            if data.get('success'):
                print(f"  ✅ Register Device mutation works")
                print(f"     Device ID: {data.get('deviceTrust', {}).get('deviceId')}")
                self.results['passed'].append('Register Device mutation')
                
                # Cleanup
                DeviceTrust.objects.filter(device_id='test-graphql-device').delete()
                return True
            else:
                print(f"  ⚠️  Mutation failed: {data.get('message')}")
                self.results['failed'].append('Register Device mutation')
                return False
        except Exception as e:
            print(f"  ❌ Register Device mutation failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['failed'].append(f'Register Device: {e}')
            return False
    
    def test_compliance_statuses_query(self):
        """Test Compliance Statuses query"""
        print("\n🔍 Testing Compliance Statuses Query...")
        
        try:
            query = """
            query {
                complianceStatuses {
                    id
                    standard
                    status
                    score
                    lastAuditDate
                    nextAuditDate
                }
            }
            """
            
            result = self.client.execute(query, context_value={'user': self.test_user})
            
            if 'errors' in result:
                print(f"  ⚠️  Query returned errors: {result['errors']}")
                self.results['failed'].append('Compliance Statuses query')
                return False
            
            data = result.get('data', {}).get('complianceStatuses', [])
            print(f"  ✅ Compliance Statuses query works ({len(data)} statuses)")
            self.results['passed'].append('Compliance Statuses query')
            return True
        except Exception as e:
            print(f"  ❌ Compliance Statuses query failed: {e}")
            self.results['failed'].append(f'Compliance Statuses: {e}')
            return False
    
    def run_all_tests(self):
        """Run all GraphQL tests"""
        print("=" * 60)
        print("🧪 GRAPHQL SECURITY API TEST SUITE")
        print("=" * 60)
        
        if not self.setup_test_user():
            print("\n❌ Cannot proceed without test user")
            return False
        
        tests = [
            ('Zero Trust Summary', self.test_zero_trust_summary_query),
            ('Device Trusts', self.test_device_trusts_query),
            ('Access Policies', self.test_access_policies_query),
            ('Security Insights', self.test_security_insights_query),
            ('Register Device', self.test_register_device_mutation),
            ('Compliance Statuses', self.test_compliance_statuses_query),
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
        print("📊 GRAPHQL TEST SUMMARY")
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
            print("🎉 ALL GRAPHQL TESTS PASSED!")
        else:
            print(f"⚠️  {failed} TEST(S) FAILED")
        print("=" * 60)


if __name__ == '__main__':
    suite = GraphQLSecurityTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)

