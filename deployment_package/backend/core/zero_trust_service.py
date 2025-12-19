"""
Zero Trust Architecture Service
Implements "Never Trust, Always Verify" security model

Principles:
1. Verify every request (no implicit trust)
2. Least privilege access
3. Assume breach (defense in depth)
4. Continuous verification
5. Micro-segmentation
6. Identity-based access control
"""
import logging
import hashlib
import json
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import SecurityEvent

logger = logging.getLogger(__name__)
User = get_user_model()


class ZeroTrustService:
    """Zero Trust security service"""
    
    def __init__(self):
        self.trust_scores = {}  # {user_id: {device_id: score, last_verified: timestamp}}
        self.device_fingerprints = {}  # {device_id: fingerprint_data}
        self.access_policies = {}  # {user_id: [allowed_actions]}
    
    def verify_request(self, user, request_metadata):
        """
        Verify every request using Zero Trust principles + AI defenses
        
        Args:
            user: Authenticated user
            request_metadata: {
                'device_id': str,
                'ip_address': str,
                'user_agent': str,
                'action': str,  # e.g., 'create_trade', 'view_portfolio'
                'resource': str,  # e.g., 'portfolio', 'trading'
            }
        
        Returns:
            {
                'allowed': bool,
                'trust_score': float,  # 0-100
                'reason': str,
                'requires_mfa': bool,
                'risk_factors': list,
                'ai_anomaly_detection': dict,  # AI-powered anomaly detection
                'threat_level': str  # AI-predicted threat level
            }
        """
        if not user or user.is_anonymous:
            return {
                'allowed': False,
                'trust_score': 0,
                'reason': 'User not authenticated',
                'requires_mfa': True,
                'risk_factors': ['unauthenticated_request']
            }
        
        device_id = request_metadata.get('device_id')
        ip_address = request_metadata.get('ip_address')
        action = request_metadata.get('action')
        resource = request_metadata.get('resource')
        
        # Calculate trust score
        trust_score = self._calculate_trust_score(user, device_id, ip_address, request_metadata)
        
        # Check access policy (least privilege)
        has_permission = self._check_permission(user, action, resource)
        
        # Risk assessment
        risk_factors = self._assess_risk(user, device_id, ip_address, action, resource)
        
        # AI-powered anomaly detection
        from .ai_security_service import ai_security_service
        anomaly_result = ai_security_service.detect_anomalies(user, request_metadata)
        threat_level = ai_security_service.predict_threat_level(user, request_metadata, anomaly_result)
        
        # Adjust trust score based on AI anomaly detection
        if anomaly_result['is_anomaly']:
            anomaly_penalty = anomaly_result['anomaly_score'] * 30  # Max 30 point penalty
            trust_score = max(0, trust_score - anomaly_penalty)
            
            # Add AI-detected risk factors
            risk_factors.append({
                'type': f'ai_anomaly_{anomaly_result["anomaly_type"]}',
                'severity': threat_level,
                'description': f'AI detected {anomaly_result["anomaly_type"]} anomaly: {anomaly_result["explanation"]}',
                'confidence': anomaly_result['confidence']
            })
        
        # Decision logic (enhanced with AI)
        requires_mfa = trust_score < 70 or any(factor['severity'] == 'high' for factor in risk_factors) or threat_level in ['high', 'critical']
        allowed = has_permission and trust_score >= 50 and threat_level != 'critical' and len([f for f in risk_factors if f['severity'] == 'critical']) == 0
        
        # Log access attempt
        self._log_access_attempt(user, request_metadata, allowed, trust_score, risk_factors, anomaly_result, threat_level)
        
        return {
            'allowed': allowed,
            'trust_score': trust_score,
            'reason': 'Access granted' if allowed else 'Access denied - insufficient trust score or high risk',
            'requires_mfa': requires_mfa,
            'risk_factors': risk_factors,
            'ai_anomaly_detection': {
                'is_anomaly': anomaly_result['is_anomaly'],
                'anomaly_score': anomaly_result['anomaly_score'],
                'anomaly_type': anomaly_result['anomaly_type'],
                'confidence': anomaly_result['confidence'],
                'explanation': anomaly_result['explanation']
            },
            'threat_level': threat_level
        }
    
    def _calculate_trust_score(self, user, device_id, ip_address, request_metadata):
        """Calculate trust score (0-100) based on multiple factors"""
        score = 50  # Start with neutral score
        
        # Factor 1: Device trust (30 points)
        if device_id:
            device_trust = self._get_device_trust(user.id, device_id)
            score += device_trust * 0.3
        
        # Factor 2: Location trust (20 points)
        location_trust = self._get_location_trust(user.id, ip_address)
        score += location_trust * 0.2
        
        # Factor 3: Behavioral trust (20 points)
        behavioral_trust = self._get_behavioral_trust(user.id, request_metadata)
        score += behavioral_trust * 0.2
        
        # Factor 4: Recent security events (30 points)
        recent_events_penalty = self._get_recent_events_penalty(user.id)
        score -= recent_events_penalty * 0.3
        
        # Factor 5: Authentication method (bonus)
        auth_method = request_metadata.get('auth_method', 'password')
        if auth_method == 'biometric':
            score += 10
        elif auth_method == 'mfa':
            score += 5
        
        return max(0, min(100, score))
    
    def _get_device_trust(self, user_id, device_id):
        """Get device trust score (0-100)"""
        if not device_id:
            return 0
        
        # Check if device is known and trusted
        device_key = f"{user_id}:{device_id}"
        
        if device_key in self.trust_scores:
            device_data = self.trust_scores[device_key]
            last_verified = device_data.get('last_verified')
            
            # Trust decays over time
            if last_verified:
                hours_since_verification = (timezone.now() - last_verified).total_seconds() / 3600
                base_score = device_data.get('score', 50)
                
                # Decay: -5 points per 24 hours
                decay = min(50, hours_since_verification / 24 * 5)
                return max(0, base_score - decay)
        
        # Unknown device = low trust
        return 20
    
    def _get_location_trust(self, user_id, ip_address):
        """Get location trust score (0-100)"""
        if not ip_address:
            return 50  # Neutral if no IP
        
        # Check recent login locations
        recent_logins = SecurityEvent.objects.filter(
            user_id=user_id,
            event_type='suspicious_login',
            created_at__gte=timezone.now() - timedelta(days=30)
        ).values_list('metadata', flat=True)
        
        # If IP matches recent trusted locations, higher score
        for login_metadata in recent_logins:
            if isinstance(login_metadata, dict) and login_metadata.get('ip_address') == ip_address:
                return 80  # Known location
        
        # New location = lower trust
        return 40
    
    def _get_behavioral_trust(self, user_id, request_metadata):
        """Get behavioral trust score (0-100) based on usage patterns"""
        action = request_metadata.get('action')
        resource = request_metadata.get('resource')
        
        # Normal actions = higher trust
        normal_actions = ['view_portfolio', 'view_stocks', 'view_credit']
        if action in normal_actions:
            return 80
        
        # Sensitive actions = require more verification
        sensitive_actions = ['create_trade', 'withdraw_funds', 'change_password']
        if action in sensitive_actions:
            return 40  # Lower trust, requires MFA
        
        return 60  # Neutral
    
    def _get_recent_events_penalty(self, user_id):
        """Get penalty score (0-100) based on recent security events"""
        recent_events = SecurityEvent.objects.filter(
            user_id=user_id,
            created_at__gte=timezone.now() - timedelta(days=7),
            resolved=False
        )
        
        penalty = 0
        for event in recent_events:
            if event.threat_level == 'critical':
                penalty += 50
            elif event.threat_level == 'high':
                penalty += 30
            elif event.threat_level == 'medium':
                penalty += 15
            elif event.threat_level == 'low':
                penalty += 5
        
        return min(100, penalty)
    
    def _check_permission(self, user, action, resource):
        """Check if user has permission for action (least privilege)"""
        # Default: All authenticated users can view
        if action.startswith('view_'):
            return True
        
        # Sensitive actions require explicit permissions
        sensitive_actions = ['create_trade', 'withdraw_funds', 'delete_account']
        if action in sensitive_actions:
            # Check if user has premium access or explicit permission
            if hasattr(user, 'has_premium_access') and user.has_premium_access:
                return True
            
            # Check access policy
            user_policies = self.access_policies.get(user.id, [])
            if action in user_policies:
                return True
            
            return False
        
        return True  # Default allow for other actions
    
    def _assess_risk(self, user, device_id, ip_address, action, resource):
        """Assess risk factors for the request"""
        risk_factors = []
        
        # Risk 1: Unknown device
        if device_id and not self._is_known_device(user.id, device_id):
            risk_factors.append({
                'type': 'unknown_device',
                'severity': 'medium',
                'description': 'Request from unknown device'
            })
        
        # Risk 2: New location
        if ip_address and not self._is_known_location(user.id, ip_address):
            risk_factors.append({
                'type': 'new_location',
                'severity': 'medium',
                'description': 'Request from new IP address'
            })
        
        # Risk 3: Sensitive action
        sensitive_actions = ['create_trade', 'withdraw_funds', 'change_password']
        if action in sensitive_actions:
            risk_factors.append({
                'type': 'sensitive_action',
                'severity': 'high',
                'description': f'Attempting sensitive action: {action}'
            })
        
        # Risk 4: Recent security events
        recent_critical_events = SecurityEvent.objects.filter(
            user_id=user.id,
            threat_level='critical',
            created_at__gte=timezone.now() - timedelta(hours=24),
            resolved=False
        ).count()
        
        if recent_critical_events > 0:
            risk_factors.append({
                'type': 'recent_critical_event',
                'severity': 'critical',
                'description': f'{recent_critical_events} unresolved critical security events in last 24 hours'
            })
        
        # Risk 5: Unusual time
        current_hour = timezone.now().hour
        if current_hour < 6 or current_hour > 23:
            risk_factors.append({
                'type': 'unusual_time',
                'severity': 'low',
                'description': 'Request outside normal hours'
            })
        
        return risk_factors
    
    def _is_known_device(self, user_id, device_id):
        """Check if device is known and trusted"""
        device_key = f"{user_id}:{device_id}"
        return device_key in self.trust_scores
    
    def _is_known_location(self, user_id, ip_address):
        """Check if IP address is from known location"""
        # Check last 30 days of logins
        recent_logins = SecurityEvent.objects.filter(
            user_id=user_id,
            event_type__in=['suspicious_login', 'device_change'],
            created_at__gte=timezone.now() - timedelta(days=30)
        ).values_list('metadata', flat=True)
        
        for login_metadata in recent_logins:
            if isinstance(login_metadata, dict) and login_metadata.get('ip_address') == ip_address:
                return True
        
        return False
    
    def _log_access_attempt(self, user, request_metadata, allowed, trust_score, risk_factors, anomaly_result=None, threat_level=None):
        """Log access attempt for audit trail (enhanced with AI)"""
        from .security_service import SecurityService
        
        if not allowed or len([f for f in risk_factors if f['severity'] in ['high', 'critical']]) > 0 or (anomaly_result and anomaly_result['is_anomaly']):
            security_service = SecurityService()
            
            # Use AI-predicted threat level if available
            if threat_level:
                threat_level_map = {'low': 'low', 'medium': 'medium', 'high': 'high', 'critical': 'critical'}
                event_threat_level = threat_level_map.get(threat_level, 'medium')
            else:
                event_threat_level = 'critical' if not allowed else 'high' if trust_score < 50 else 'medium'
            
            event_type = 'api_abuse' if not allowed else 'ai_anomaly_detected' if (anomaly_result and anomaly_result['is_anomaly']) else 'unusual_activity'
            
            security_service.create_security_event(
                user=user,
                event_type=event_type,
                threat_level=event_threat_level,
                description=f"Zero Trust + AI: Access {'denied' if not allowed else 'granted with risk factors'}: {request_metadata.get('action')} on {request_metadata.get('resource')}",
                metadata={
                    'trust_score': trust_score,
                    'risk_factors': risk_factors,
                    'device_id': request_metadata.get('device_id'),
                    'ip_address': request_metadata.get('ip_address'),
                    'allowed': allowed,
                    'ai_anomaly': anomaly_result if anomaly_result else None,
                    'threat_level': threat_level
                }
            )
    
    def register_device(self, user_id, device_id, device_fingerprint):
        """Register a new device for Zero Trust"""
        device_key = f"{user_id}:{device_id}"
        
        self.trust_scores[device_key] = {
            'score': 50,  # Start with neutral
            'last_verified': timezone.now(),
            'first_seen': timezone.now()
        }
        
        self.device_fingerprints[device_key] = device_fingerprint
        
        logger.info(f"[ZeroTrust] Device registered: {device_key}")
    
    def update_device_trust(self, user_id, device_id, trust_score, reason=''):
        """Update device trust score"""
        device_key = f"{user_id}:{device_id}"
        
        if device_key in self.trust_scores:
            self.trust_scores[device_key]['score'] = trust_score
            self.trust_scores[device_key]['last_verified'] = timezone.now()
            logger.info(f"[ZeroTrust] Device trust updated: {device_key} = {trust_score} ({reason})")
    
    def get_trust_summary(self, user_id):
        """Get Zero Trust summary for user"""
        user_devices = {k: v for k, v in self.trust_scores.items() if k.startswith(f"{user_id}:")}
        
        return {
            'user_id': user_id,
            'devices': len(user_devices),
            'average_trust_score': sum(d.get('score', 50) for d in user_devices.values()) / len(user_devices) if user_devices else 50,
            'last_verification': max([d.get('last_verified') for d in user_devices.values()]) if user_devices else None
        }


# Singleton instance
zero_trust_service = ZeroTrustService()

