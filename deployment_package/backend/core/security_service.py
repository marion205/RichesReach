"""
Security Service - Calculate security scores and manage security features
"""
import logging
import uuid
from django.utils import timezone
from datetime import timedelta
from .models import SecurityEvent, BiometricSettings, SecurityScore

logger = logging.getLogger(__name__)


class SecurityService:
    """Service for security-related operations"""
    
    def calculate_security_score(self, user):
        """
        Calculate security score (0-100) based on various factors
        
        Factors:
        - Biometric settings enabled (30 points)
        - Recent security events (30 points)
        - Account security features (20 points)
        - Compliance status (20 points)
        """
        try:
            factors = {}
            score = 0
            
            # Factor 1: Biometric Settings (30 points max)
            biometric_score = 0
            try:
                settings = BiometricSettings.objects.get(user=user)
                enabled_count = sum([
                    settings.face_id_enabled,
                    settings.voice_id_enabled,
                    settings.behavioral_id_enabled,
                    settings.device_fingerprint_enabled,
                ])
                biometric_score = min(30, enabled_count * 7.5)  # 7.5 points per feature
                factors['biometrics'] = {
                    'score': biometric_score,
                    'max': 30,
                    'enabled_features': enabled_count,
                    'total_features': 4
                }
            except BiometricSettings.DoesNotExist:
                factors['biometrics'] = {'score': 0, 'max': 30, 'enabled_features': 0, 'total_features': 4}
            
            score += biometric_score
            
            # Factor 2: Recent Security Events (30 points max)
            # Recent unresolved events reduce score
            recent_events = SecurityEvent.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            unresolved_events = recent_events.filter(resolved=False)
            event_penalty = 0
            
            for event in unresolved_events:
                if event.threat_level == 'critical':
                    event_penalty += 10
                elif event.threat_level == 'high':
                    event_penalty += 5
                elif event.threat_level == 'medium':
                    event_penalty += 2
                elif event.threat_level == 'low':
                    event_penalty += 1
            
            event_score = max(0, 30 - event_penalty)
            factors['events'] = {
                'score': event_score,
                'max': 30,
                'unresolved_events': unresolved_events.count(),
                'total_recent_events': recent_events.count()
            }
            score += event_score
            
            # Factor 3: Account Security Features (20 points max)
            account_score = 0
            if user.email_verified:
                account_score += 5
            if user.two_factor_enabled:
                account_score += 10
            if user.failed_login_attempts == 0:
                account_score += 5
            
            factors['account'] = {
                'score': account_score,
                'max': 20,
                'email_verified': user.email_verified,
                'two_factor_enabled': user.two_factor_enabled,
                'failed_logins': user.failed_login_attempts
            }
            score += account_score
            
            # Factor 4: Compliance (20 points max)
            # Assume compliant if no recent violations
            compliance_score = 20  # Default to full score
            factors['compliance'] = {
                'score': compliance_score,
                'max': 20,
                'status': 'compliant'
            }
            score += compliance_score
            
            # Ensure score is between 0 and 100
            score = max(0, min(100, score))
            
            return {
                'score': int(score),
                'factors': factors
            }
            
        except Exception as e:
            logger.error(f"Error calculating security score for user {user.id}: {e}")
            return {
                'score': 50,  # Default score on error
                'factors': {}
            }
    
    def create_security_event(self, user, event_type, threat_level, description, metadata=None):
        """Create a new security event"""
        try:
            event = SecurityEvent.objects.create(
                user=user,
                event_type=event_type,
                threat_level=threat_level,
                description=description,
                metadata=metadata or {}
            )
            correlation_id = str(uuid.uuid4())[:8]
            logger.info(
                f"[Security] [{correlation_id}] Created security event | "
                f"event_id={event.id} user_id={user.id} type={event_type} level={threat_level}"
            )
            
            # Broadcast event via WebSocket
            self._broadcast_security_event(user, event, 'created', correlation_id)
            
            return event
        except Exception as e:
            logger.error(f"Error creating security event: {e}")
            return None
    
    def resolve_security_event(self, user, event_id):
        """Resolve a security event"""
        try:
            event = SecurityEvent.objects.get(id=event_id, user=user)
            event.resolved = True
            event.resolved_at = timezone.now()
            event.resolved_by = user
            event.save()
            correlation_id = str(uuid.uuid4())[:8]
            logger.info(
                f"[Security] [{correlation_id}] Resolved security event | "
                f"event_id={event_id} user_id={user.id}"
            )
            
            # Broadcast event resolution via WebSocket
            self._broadcast_security_event(user, event, 'resolved', correlation_id)
            
            return event
        except SecurityEvent.DoesNotExist:
            logger.warning(f"Security event {event_id} not found for user {user.id}")
            return None
        except Exception as e:
            logger.error(f"Error resolving security event: {e}")
            return None
    
    def _broadcast_security_event(self, user, event, action='created', correlation_id=None):
        """Broadcast security event via Redis (multi-instance safe)"""
        if not correlation_id:
            correlation_id = str(uuid.uuid4())[:8]
        
        try:
            from .websocket_broadcast import broadcast_security_event
            
            # Prepare event data (sanitized - no PII in logs)
            event_data = {
                'id': str(event.id),
                'eventType': event.event_type,
                'threatLevel': event.threat_level,
                'description': event.description,  # Description may contain PII - consider sanitizing
                'resolved': event.resolved,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'resolved_at': event.resolved_at.isoformat() if event.resolved_at else None,
            }
            
            # Broadcast via Redis (synchronous - Redis client handles async internally)
            success = broadcast_security_event(user.id, event_data, action)
            
            # Log with sanitized user_id (hash, not actual ID)
            user_id_hash = str(hash(str(user.id)))[:8]
            logger.info(
                f"[Security] [{correlation_id}] Broadcast {'success' if success else 'failed'} | "
                f"event_id={event.id} user_id_hash={user_id_hash} action={action}"
            )
            
        except ImportError:
            logger.debug(f"[Security] [{correlation_id}] WebSocket broadcast not available for event {event.id}")
        except Exception as e:
            logger.error(f"[Security] [{correlation_id}] Error broadcasting security event: {e}")

