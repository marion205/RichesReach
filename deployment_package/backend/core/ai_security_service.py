"""
AI-Powered Security Service
Uses machine learning for threat detection, anomaly detection, and behavioral analysis
"""
import logging
import numpy as np
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import SecurityEvent, DeviceTrust
import json

logger = logging.getLogger(__name__)
User = get_user_model()


class AISecurityService:
    """AI-powered security threat detection and anomaly detection"""
    
    def __init__(self):
        self.behavioral_profiles = {}  # {user_id: {action_patterns, timing_patterns, device_patterns}}
        self.threat_models = {}  # Cached ML models
        self.anomaly_thresholds = {
            'low': 0.3,
            'medium': 0.5,
            'high': 0.7,
            'critical': 0.9
        }
    
    def detect_anomalies(self, user, request_metadata, historical_data=None):
        """
        Use AI to detect anomalies in user behavior
        
        Returns:
            {
                'is_anomaly': bool,
                'anomaly_score': float,  # 0-1
                'anomaly_type': str,  # 'behavioral', 'temporal', 'device', 'location'
                'confidence': float,  # 0-1
                'explanation': str
            }
        """
        if not user or user.is_anonymous:
            return {
                'is_anomaly': True,
                'anomaly_score': 1.0,
                'anomaly_type': 'authentication',
                'confidence': 1.0,
                'explanation': 'Unauthenticated request'
            }
        
        # Build behavioral profile if not exists
        if user.id not in self.behavioral_profiles:
            self._build_behavioral_profile(user)
        
        profile = self.behavioral_profiles.get(user.id, {})
        
        # Check multiple anomaly types
        anomalies = []
        
        # 1. Behavioral anomaly (unusual action patterns)
        behavioral_anomaly = self._detect_behavioral_anomaly(user, request_metadata, profile)
        if behavioral_anomaly['is_anomaly']:
            anomalies.append(behavioral_anomaly)
        
        # 2. Temporal anomaly (unusual timing)
        temporal_anomaly = self._detect_temporal_anomaly(user, request_metadata, profile)
        if temporal_anomaly['is_anomaly']:
            anomalies.append(temporal_anomaly)
        
        # 3. Device anomaly (unusual device patterns)
        device_anomaly = self._detect_device_anomaly(user, request_metadata, profile)
        if device_anomaly['is_anomaly']:
            anomalies.append(device_anomaly)
        
        # 4. Location anomaly (unusual location patterns)
        location_anomaly = self._detect_location_anomaly(user, request_metadata, profile)
        if location_anomaly['is_anomaly']:
            anomalies.append(location_anomaly)
        
        # Aggregate results
        if not anomalies:
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'anomaly_type': 'none',
                'confidence': 1.0,
                'explanation': 'No anomalies detected'
            }
        
        # Use highest anomaly score
        max_anomaly = max(anomalies, key=lambda x: x['anomaly_score'])
        
        return {
            'is_anomaly': True,
            'anomaly_score': max_anomaly['anomaly_score'],
            'anomaly_type': max_anomaly['anomaly_type'],
            'confidence': max_anomaly['confidence'],
            'explanation': max_anomaly['explanation'],
            'all_anomalies': anomalies
        }
    
    def _build_behavioral_profile(self, user):
        """Build AI behavioral profile from historical data"""
        # Get last 30 days of activity
        recent_events = SecurityEvent.objects.filter(
            user_id=user.id,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('created_at')
        
        # Analyze patterns
        action_patterns = {}
        timing_patterns = {}
        device_patterns = {}
        location_patterns = {}
        
        for event in recent_events:
            metadata = event.metadata or {}
            
            # Action patterns
            action = metadata.get('action', 'unknown')
            action_patterns[action] = action_patterns.get(action, 0) + 1
            
            # Timing patterns (hour of day)
            hour = event.created_at.hour
            timing_patterns[hour] = timing_patterns.get(hour, 0) + 1
            
            # Device patterns
            device_id = metadata.get('device_id')
            if device_id:
                device_patterns[device_id] = device_patterns.get(device_id, 0) + 1
            
            # Location patterns
            ip_address = metadata.get('ip_address')
            if ip_address:
                location_patterns[ip_address] = location_patterns.get(ip_address, 0) + 1
        
        # Normalize patterns
        total_actions = sum(action_patterns.values()) or 1
        action_patterns = {k: v / total_actions for k, v in action_patterns.items()}
        
        total_timing = sum(timing_patterns.values()) or 1
        timing_patterns = {k: v / total_timing for k, v in timing_patterns.items()}
        
        self.behavioral_profiles[user.id] = {
            'action_patterns': action_patterns,
            'timing_patterns': timing_patterns,
            'device_patterns': device_patterns,
            'location_patterns': location_patterns,
            'last_updated': timezone.now()
        }
        
        logger.info(f"[AISecurity] Built behavioral profile for user {user.id}")
    
    def _detect_behavioral_anomaly(self, user, request_metadata, profile):
        """Detect behavioral anomalies using ML"""
        action = request_metadata.get('action', 'unknown')
        action_patterns = profile.get('action_patterns', {})
        
        # Check if action is unusual
        action_frequency = action_patterns.get(action, 0)
        
        # If action has never been seen before, it's an anomaly
        if action_frequency == 0:
            # Check if it's a sensitive action (always flag)
            sensitive_actions = ['create_trade', 'withdraw_funds', 'delete_account', 'change_password']
            if action in sensitive_actions:
                return {
                    'is_anomaly': True,
                    'anomaly_score': 0.8,
                    'anomaly_type': 'behavioral',
                    'confidence': 0.9,
                    'explanation': f'First-time sensitive action: {action}'
                }
            else:
                return {
                    'is_anomaly': True,
                    'anomaly_score': 0.4,
                    'anomaly_type': 'behavioral',
                    'confidence': 0.6,
                    'explanation': f'Unusual action: {action} (never seen before)'
                }
        
        # If action frequency is very low (< 5% of actions), it's an anomaly
        if action_frequency < 0.05:
            return {
                'is_anomaly': True,
                'anomaly_score': 0.6,
                'anomaly_type': 'behavioral',
                'confidence': 0.7,
                'explanation': f'Rare action: {action} (only {action_frequency*100:.1f}% of actions)'
            }
        
        return {
            'is_anomaly': False,
            'anomaly_score': 0.0,
            'anomaly_type': 'behavioral',
            'confidence': 1.0,
            'explanation': 'Normal behavioral pattern'
        }
    
    def _detect_temporal_anomaly(self, user, request_metadata, profile):
        """Detect temporal anomalies (unusual timing)"""
        current_hour = timezone.now().hour
        timing_patterns = profile.get('timing_patterns', {})
        
        # Check if current hour is unusual
        hour_frequency = timing_patterns.get(current_hour, 0)
        
        # Normal hours: 6 AM - 11 PM (most users active)
        normal_hours = set(range(6, 23))
        
        if current_hour not in normal_hours:
            return {
                'is_anomaly': True,
                'anomaly_score': 0.5,
                'anomaly_type': 'temporal',
                'confidence': 0.7,
                'explanation': f'Unusual time: {current_hour}:00 (outside normal hours)'
            }
        
        # If hour frequency is very low (< 2% of actions), it's an anomaly
        if hour_frequency < 0.02:
            return {
                'is_anomaly': True,
                'anomaly_score': 0.4,
                'anomaly_type': 'temporal',
                'confidence': 0.6,
                'explanation': f'Rare time: {current_hour}:00 (only {hour_frequency*100:.1f}% of actions)'
            }
        
        return {
            'is_anomaly': False,
            'anomaly_score': 0.0,
            'anomaly_type': 'temporal',
            'confidence': 1.0,
            'explanation': 'Normal temporal pattern'
        }
    
    def _detect_device_anomaly(self, user, request_metadata, profile):
        """Detect device anomalies"""
        device_id = request_metadata.get('device_id')
        if not device_id:
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'anomaly_type': 'device',
                'confidence': 1.0,
                'explanation': 'No device ID provided'
            }
        
        device_patterns = profile.get('device_patterns', {})
        
        # Check if device is known
        if device_id not in device_patterns:
            # Check device trust
            try:
                device_trust = DeviceTrust.objects.get(user=user, device_id=device_id)
                if device_trust.trust_score < 50:
                    return {
                        'is_anomaly': True,
                        'anomaly_score': 0.7,
                        'anomaly_type': 'device',
                        'confidence': 0.8,
                        'explanation': f'Unknown or low-trust device: {device_id[:8]}...'
                    }
            except DeviceTrust.DoesNotExist:
                return {
                    'is_anomaly': True,
                    'anomaly_score': 0.8,
                    'anomaly_type': 'device',
                    'confidence': 0.9,
                    'explanation': f'Unknown device: {device_id[:8]}...'
                }
        
        return {
            'is_anomaly': False,
            'anomaly_score': 0.0,
            'anomaly_type': 'device',
            'confidence': 1.0,
            'explanation': 'Known device'
        }
    
    def _detect_location_anomaly(self, user, request_metadata, profile):
        """Detect location anomalies"""
        ip_address = request_metadata.get('ip_address')
        if not ip_address:
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'anomaly_type': 'location',
                'confidence': 1.0,
                'explanation': 'No IP address provided'
            }
        
        location_patterns = profile.get('location_patterns', {})
        
        # Check if location is known
        if ip_address not in location_patterns:
            return {
                'is_anomaly': True,
                'anomaly_score': 0.6,
                'anomaly_type': 'location',
                'confidence': 0.7,
                'explanation': f'New location: {ip_address}'
            }
        
        return {
            'is_anomaly': False,
            'anomaly_score': 0.0,
            'anomaly_type': 'location',
            'confidence': 1.0,
            'explanation': 'Known location'
        }
    
    def predict_threat_level(self, user, request_metadata, anomaly_result):
        """
        Use AI to predict threat level based on anomaly detection
        
        Returns: 'low', 'medium', 'high', 'critical'
        """
        if not anomaly_result['is_anomaly']:
            return 'low'
        
        anomaly_score = anomaly_result['anomaly_score']
        anomaly_type = anomaly_result['anomaly_type']
        
        # Critical: Multiple high-severity anomalies
        if anomaly_score >= self.anomaly_thresholds['critical']:
            return 'critical'
        
        # High: High-severity anomaly + sensitive action
        if anomaly_score >= self.anomaly_thresholds['high']:
            sensitive_actions = ['create_trade', 'withdraw_funds', 'delete_account']
            if request_metadata.get('action') in sensitive_actions:
                return 'high'
            return 'medium'
        
        # Medium: Medium-severity anomaly
        if anomaly_score >= self.anomaly_thresholds['medium']:
            return 'medium'
        
        # Low: Low-severity anomaly
        return 'low'
    
    def generate_security_insights(self, user):
        """
        Generate AI-powered security insights for user engagement
        
        Returns:
            {
                'security_score': float,
                'strengths': list,
                'recommendations': list,
                'trend': str,  # 'improving', 'stable', 'declining'
                'badges': list  # Achievement badges
            }
        """
        # Get recent security events
        recent_events = SecurityEvent.objects.filter(
            user_id=user.id,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Calculate security score
        total_events = recent_events.count()
        resolved_events = recent_events.filter(resolved=True).count()
        critical_events = recent_events.filter(threat_level='critical', resolved=False).count()
        
        # Base score
        security_score = 100
        
        # Penalties
        security_score -= critical_events * 20
        security_score -= (total_events - resolved_events) * 5
        security_score = max(0, min(100, security_score))
        
        # Generate insights
        strengths = []
        recommendations = []
        badges = []
        
        # Strengths
        if resolved_events == total_events and total_events > 0:
            strengths.append("All security events resolved")
            badges.append("Security Champion")
        
        if critical_events == 0:
            strengths.append("No critical security issues")
            badges.append("Fortress Master")
        
        # Recommendations
        if critical_events > 0:
            recommendations.append({
                'priority': 'high',
                'action': 'Resolve critical security events',
                'impact': 'Improve security score by 20 points'
            })
        
        if total_events - resolved_events > 5:
            recommendations.append({
                'priority': 'medium',
                'action': 'Review and resolve pending security events',
                'impact': 'Improve security score by 5 points per event'
            })
        
        # Trend analysis
        last_week_events = recent_events.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        previous_week_events = recent_events.filter(
            created_at__gte=timezone.now() - timedelta(days=14),
            created_at__lt=timezone.now() - timedelta(days=7)
        ).count()
        
        if last_week_events < previous_week_events:
            trend = 'improving'
        elif last_week_events > previous_week_events:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'security_score': security_score,
            'strengths': strengths,
            'recommendations': recommendations,
            'trend': trend,
            'badges': badges
        }


# Singleton instance
ai_security_service = AISecurityService()

