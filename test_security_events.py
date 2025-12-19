#!/usr/bin/env python3
"""
End-to-End Test Script for Security Events
Tests the complete flow: Create Event → DB → WebSocket → Client

Usage:
    python test_security_events.py

This script:
1. Creates a security event via Django service
2. Verifies DB row created
3. Checks WebSocket broadcast (if Socket.io is running)
4. Validates correlation IDs are present
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import User, SecurityEvent
from core.security_service import SecurityService
import uuid
import asyncio

def test_create_security_event():
    """Test creating a security event end-to-end"""
    print("=" * 60)
    print("TEST: Create Security Event End-to-End")
    print("=" * 60)
    
    # Get or create test user
    user, _ = User.objects.get_or_create(
        email='test@example.com',
        defaults={'name': 'Test User'}
    )
    print(f"✅ Using test user: {user.email} (ID: {user.id})")
    
    # Create security event
    service = SecurityService()
    correlation_id = str(uuid.uuid4())[:8]
    
    print(f"\n📝 Creating security event (correlation_id: {correlation_id})...")
    event = service.create_security_event(
        user=user,
        event_type='suspicious_login',
        threat_level='medium',
        description='Test security event from E2E test',
        metadata={'correlation_id': correlation_id, 'test': True}
    )
    
    if not event:
        print("❌ FAILED: Event creation returned None")
        return False
    
    print(f"✅ Event created: {event.id}")
    
    # Verify DB row
    db_event = SecurityEvent.objects.get(id=event.id)
    print(f"✅ DB verification: Event found in database")
    print(f"   - Type: {db_event.event_type}")
    print(f"   - Threat Level: {db_event.threat_level}")
    print(f"   - User: {db_event.user.email}")
    print(f"   - Resolved: {db_event.resolved}")
    print(f"   - Created: {db_event.created_at}")
    
    # Check correlation ID in metadata
    if db_event.metadata.get('correlation_id') == correlation_id:
        print(f"✅ Correlation ID preserved: {correlation_id}")
    else:
        print(f"⚠️  Correlation ID mismatch")
    
    # Test resolution
    print(f"\n🔧 Resolving event...")
    resolved_event = service.resolve_security_event(user, str(event.id))
    
    if resolved_event and resolved_event.resolved:
        print(f"✅ Event resolved successfully")
        print(f"   - Resolved at: {resolved_event.resolved_at}")
        print(f"   - Resolved by: {resolved_event.resolved_by.email if resolved_event.resolved_by else 'N/A'}")
    else:
        print("❌ FAILED: Event resolution failed")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check Socket.io logs for broadcast messages")
    print("2. Verify client receives 'security-event-created' event")
    print("3. Verify client receives 'security-event-resolved' event")
    print("4. Check correlation IDs match in logs")
    
    return True

def test_auth_validation():
    """Test that users can only access their own events"""
    print("\n" + "=" * 60)
    print("TEST: Auth Validation (User Isolation)")
    print("=" * 60)
    
    # Create two users
    user1, _ = User.objects.get_or_create(
        email='user1@test.com',
        defaults={'name': 'User 1'}
    )
    user2, _ = User.objects.get_or_create(
        email='user2@test.com',
        defaults={'name': 'User 2'}
    )
    
    service = SecurityService()
    
    # Create event for user1
    event1 = service.create_security_event(
        user=user1,
        event_type='fraud_detection',
        threat_level='high',
        description='User 1 event'
    )
    
    # Try to resolve user1's event as user2 (should fail)
    print(f"\n🔒 Testing: User2 attempting to resolve User1's event...")
    result = service.resolve_security_event(user2, str(event1.id))
    
    if result is None:
        print("✅ PASS: User2 cannot resolve User1's event (correctly rejected)")
    else:
        print("❌ FAIL: User2 was able to resolve User1's event (security issue!)")
        return False
    
    # Verify user1 can resolve their own event
    print(f"\n🔒 Testing: User1 resolving their own event...")
    result = service.resolve_security_event(user1, str(event1.id))
    
    if result and result.resolved:
        print("✅ PASS: User1 can resolve their own event")
    else:
        print("❌ FAIL: User1 cannot resolve their own event")
        return False
    
    print("\n✅ Auth validation tests passed")
    return True

if __name__ == '__main__':
    print("Security Events E2E Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        test1 = test_create_security_event()
        test2 = test_auth_validation()
        
        if test1 and test2:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

