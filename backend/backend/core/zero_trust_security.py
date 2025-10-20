"""
Zero-Trust Security Framework - Phase 3
Comprehensive security with zero-trust principles, identity verification, and continuous monitoring
"""

import asyncio
import json
import logging
import time
import hashlib
import hmac
import secrets
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import jwt
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import uuid
from enum import Enum
import ipaddress
import geoip2.database
import geoip2.errors
from collections import defaultdict, deque
import threading
import weakref

logger = logging.getLogger("richesreach")

class SecurityLevel(Enum):
    """Security level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatLevel(Enum):
    """Threat level enumeration"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityContext:
    """Security context for requests"""
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    location: Optional[Dict[str, Any]] = None
    device_fingerprint: Optional[str] = None
    risk_score: float = 0.0
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    permissions: List[str] = None
    last_activity: datetime = None
    mfa_verified: bool = False
    device_trusted: bool = False

@dataclass
class SecurityEvent:
    """Security event for monitoring"""
    event_id: str
    event_type: str
    severity: ThreatLevel
    timestamp: datetime
    user_id: Optional[str]
    ip_address: str
    description: str
    metadata: Dict[str, Any]
    risk_score: float
    action_taken: Optional[str] = None

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    policy_id: str
    name: str
    description: str
    rules: List[Dict[str, Any]]
    enabled: bool = True
    priority: int = 100
    created_at: datetime = None
    updated_at: datetime = None

class ZeroTrustEngine:
    """Zero-trust security engine"""
    
    def __init__(self):
        self.security_contexts = {}
        self.security_events = deque(maxlen=10000)
        self.security_policies = {}
        self.risk_models = {}
        self.encryption_keys = {}
        self.session_tokens = {}
        self.device_registry = {}
        self.geoip_db = None
        self.rate_limiters = defaultdict(lambda: deque())
        self.failed_attempts = defaultdict(int)
        self.blocked_ips = set()
        self.trusted_devices = set()
        
        # Initialize security components
        asyncio.create_task(self._initialize_security())
        
        # Start background tasks
        asyncio.create_task(self._monitor_security_events())
        asyncio.create_task(self._cleanup_expired_sessions())
        asyncio.create_task(self._update_risk_models())
    
    async def _initialize_security(self):
        """Initialize security components"""
        try:
            # Initialize encryption keys
            await self._initialize_encryption_keys()
            
            # Load security policies
            await self._load_security_policies()
            
            # Initialize risk models
            await self._initialize_risk_models()
            
            # Initialize GeoIP database
            await self._initialize_geoip()
            
            logger.info("✅ Zero-trust security engine initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize zero-trust security: {e}")
            raise
    
    async def _initialize_encryption_keys(self):
        """Initialize encryption keys"""
        try:
            # Generate or load encryption keys
            self.encryption_keys = {
                'session': Fernet.generate_key(),
                'data': Fernet.generate_key(),
                'api': Fernet.generate_key()
            }
            
            # Generate RSA key pair for JWT signing
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            self.encryption_keys['jwt_private'] = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            self.encryption_keys['jwt_public'] = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            logger.info("✅ Encryption keys initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption keys: {e}")
            raise
    
    async def _load_security_policies(self):
        """Load security policies"""
        try:
            # Default security policies
            default_policies = [
                {
                    "policy_id": "rate_limiting",
                    "name": "Rate Limiting Policy",
                    "description": "Rate limiting for API endpoints",
                    "rules": [
                        {
                            "type": "rate_limit",
                            "endpoint": "/api/*",
                            "max_requests": 100,
                            "window_seconds": 60
                        }
                    ]
                },
                {
                    "policy_id": "ip_blocking",
                    "name": "IP Blocking Policy",
                    "description": "Block suspicious IP addresses",
                    "rules": [
                        {
                            "type": "ip_block",
                            "max_failed_attempts": 5,
                            "block_duration_minutes": 60
                        }
                    ]
                },
                {
                    "policy_id": "mfa_required",
                    "name": "MFA Required Policy",
                    "description": "Require MFA for sensitive operations",
                    "rules": [
                        {
                            "type": "mfa_required",
                            "endpoints": ["/api/admin/*", "/api/financial/*"],
                            "risk_threshold": 0.7
                        }
                    ]
                }
            ]
            
            for policy_data in default_policies:
                policy = SecurityPolicy(
                    policy_id=policy_data["policy_id"],
                    name=policy_data["name"],
                    description=policy_data["description"],
                    rules=policy_data["rules"],
                    created_at=datetime.now()
                )
                self.security_policies[policy.policy_id] = policy
            
            logger.info(f"✅ Loaded {len(self.security_policies)} security policies")
            
        except Exception as e:
            logger.error(f"❌ Failed to load security policies: {e}")
            raise
    
    async def _initialize_risk_models(self):
        """Initialize risk assessment models"""
        try:
            # Risk factors and weights
            self.risk_models = {
                'user_behavior': {
                    'login_frequency': 0.2,
                    'location_change': 0.3,
                    'device_change': 0.25,
                    'time_pattern': 0.15,
                    'transaction_pattern': 0.1
                },
                'network_security': {
                    'ip_reputation': 0.4,
                    'geo_location': 0.3,
                    'vpn_detection': 0.2,
                    'tor_detection': 0.1
                },
                'device_security': {
                    'device_trust': 0.5,
                    'browser_security': 0.3,
                    'os_security': 0.2
                }
            }
            
            logger.info("✅ Risk models initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize risk models: {e}")
            raise
    
    async def _initialize_geoip(self):
        """Initialize GeoIP database"""
        try:
            # This would typically load a GeoIP database file
            # For now, we'll use a mock implementation
            self.geoip_db = "mock_geoip_db"
            logger.info("✅ GeoIP database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GeoIP: {e}")
            # Continue without GeoIP - not critical
    
    async def _monitor_security_events(self):
        """Monitor security events in real-time"""
        while True:
            try:
                # Process recent security events
                recent_events = [event for event in self.security_events 
                               if event.timestamp > datetime.now() - timedelta(minutes=5)]
                
                # Analyze patterns and update risk scores
                await self._analyze_security_patterns(recent_events)
                
                # Update blocked IPs based on events
                await self._update_blocked_ips(recent_events)
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring security events: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []
                
                for session_id, context in self.security_contexts.items():
                    if context.last_activity and \
                       current_time - context.last_activity > timedelta(hours=24):
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self.security_contexts[session_id]
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
                await asyncio.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                logger.error(f"Error cleaning up sessions: {e}")
                await asyncio.sleep(3600)
    
    async def _update_risk_models(self):
        """Update risk models based on recent data"""
        while True:
            try:
                # Update risk models based on recent events
                # This would typically involve machine learning model updates
                logger.info("Risk models updated")
                
                await asyncio.sleep(3600)  # Update every hour
                
            except Exception as e:
                logger.error(f"Error updating risk models: {e}")
                await asyncio.sleep(3600)
    
    async def authenticate_user(self, user_id: str, credentials: Dict[str, Any], 
                              request_context: Dict[str, Any]) -> Tuple[bool, SecurityContext]:
        """Authenticate user with zero-trust principles"""
        try:
            # Create security context
            context = SecurityContext(
                user_id=user_id,
                session_id=str(uuid.uuid4()),
                ip_address=request_context.get('ip_address', ''),
                user_agent=request_context.get('user_agent', ''),
                last_activity=datetime.now()
            )
            
            # Assess risk
            risk_score = await self._assess_risk(context, request_context)
            context.risk_score = risk_score
            
            # Determine security level
            if risk_score < 0.3:
                context.security_level = SecurityLevel.LOW
            elif risk_score < 0.6:
                context.security_level = SecurityLevel.MEDIUM
            elif risk_score < 0.8:
                context.security_level = SecurityLevel.HIGH
            else:
                context.security_level = SecurityLevel.CRITICAL
            
            # Check if authentication should be blocked
            if await self._should_block_authentication(context):
                await self._log_security_event(
                    event_type="authentication_blocked",
                    severity=ThreatLevel.HIGH,
                    user_id=user_id,
                    ip_address=context.ip_address,
                    description="Authentication blocked due to high risk",
                    metadata={"risk_score": risk_score}
                )
                return False, context
            
            # Verify credentials
            if not await self._verify_credentials(user_id, credentials):
                await self._log_security_event(
                    event_type="authentication_failed",
                    severity=ThreatLevel.MEDIUM,
                    user_id=user_id,
                    ip_address=context.ip_address,
                    description="Invalid credentials provided"
                )
                return False, context
            
            # Check MFA requirements
            if context.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                if not await self._verify_mfa(user_id, credentials.get('mfa_code')):
                    await self._log_security_event(
                        event_type="mfa_required",
                        severity=ThreatLevel.MEDIUM,
                        user_id=user_id,
                        ip_address=context.ip_address,
                        description="MFA required but not provided"
                    )
                    return False, context
                context.mfa_verified = True
            
            # Generate session token
            session_token = await self._generate_session_token(context)
            context.permissions = await self._get_user_permissions(user_id)
            
            # Store security context
            self.security_contexts[context.session_id] = context
            
            # Log successful authentication
            await self._log_security_event(
                event_type="authentication_success",
                severity=ThreatLevel.NONE,
                user_id=user_id,
                ip_address=context.ip_address,
                description="User authenticated successfully",
                metadata={"security_level": context.security_level.value}
            )
            
            return True, context
            
        except Exception as e:
            logger.error(f"Error in user authentication: {e}")
            return False, None
    
    async def authorize_request(self, session_id: str, endpoint: str, 
                              method: str, request_context: Dict[str, Any]) -> Tuple[bool, str]:
        """Authorize request with zero-trust principles"""
        try:
            # Get security context
            context = self.security_contexts.get(session_id)
            if not context:
                return False, "Invalid session"
            
            # Update last activity
            context.last_activity = datetime.now()
            
            # Check if session is expired
            if context.last_activity and \
               datetime.now() - context.last_activity > timedelta(hours=24):
                return False, "Session expired"
            
            # Check rate limiting
            if not await self._check_rate_limit(context, endpoint):
                await self._log_security_event(
                    event_type="rate_limit_exceeded",
                    severity=ThreatLevel.MEDIUM,
                    user_id=context.user_id,
                    ip_address=context.ip_address,
                    description=f"Rate limit exceeded for {endpoint}"
                )
                return False, "Rate limit exceeded"
            
            # Check endpoint permissions
            if not await self._check_endpoint_permissions(context, endpoint, method):
                await self._log_security_event(
                    event_type="unauthorized_access",
                    severity=ThreatLevel.HIGH,
                    user_id=context.user_id,
                    ip_address=context.ip_address,
                    description=f"Unauthorized access attempt to {endpoint}"
                )
                return False, "Insufficient permissions"
            
            # Check security policies
            if not await self._check_security_policies(context, endpoint, method):
                await self._log_security_event(
                    event_type="policy_violation",
                    severity=ThreatLevel.MEDIUM,
                    user_id=context.user_id,
                    ip_address=context.ip_address,
                    description=f"Security policy violation for {endpoint}"
                )
                return False, "Security policy violation"
            
            # Reassess risk for sensitive operations
            if endpoint.startswith('/api/admin/') or endpoint.startswith('/api/financial/'):
                current_risk = await self._assess_risk(context, request_context)
                if current_risk > 0.7:
                    await self._log_security_event(
                        event_type="high_risk_operation",
                        severity=ThreatLevel.HIGH,
                        user_id=context.user_id,
                        ip_address=context.ip_address,
                        description=f"High risk operation attempted: {endpoint}",
                        metadata={"risk_score": current_risk}
                    )
                    return False, "High risk operation blocked"
            
            return True, "Authorized"
            
        except Exception as e:
            logger.error(f"Error in request authorization: {e}")
            return False, "Authorization error"
    
    async def _assess_risk(self, context: SecurityContext, request_context: Dict[str, Any]) -> float:
        """Assess risk score for user and request"""
        try:
            risk_score = 0.0
            
            # User behavior risk
            behavior_risk = await self._assess_behavior_risk(context, request_context)
            risk_score += behavior_risk * 0.4
            
            # Network security risk
            network_risk = await self._assess_network_risk(context, request_context)
            risk_score += network_risk * 0.3
            
            # Device security risk
            device_risk = await self._assess_device_risk(context, request_context)
            risk_score += device_risk * 0.3
            
            return min(risk_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return 0.5  # Default medium risk
    
    async def _assess_behavior_risk(self, context: SecurityContext, request_context: Dict[str, Any]) -> float:
        """Assess user behavior risk"""
        try:
            risk = 0.0
            
            # Check login frequency
            recent_logins = len([event for event in self.security_events 
                               if event.user_id == context.user_id and 
                               event.event_type == "authentication_success" and
                               event.timestamp > datetime.now() - timedelta(hours=1)])
            
            if recent_logins > 5:
                risk += 0.3
            
            # Check location changes
            if context.location:
                # This would check against historical locations
                risk += 0.2
            
            # Check time patterns
            current_hour = datetime.now().hour
            if current_hour < 6 or current_hour > 22:
                risk += 0.1
            
            return min(risk, 1.0)
            
        except Exception as e:
            logger.error(f"Error assessing behavior risk: {e}")
            return 0.0
    
    async def _assess_network_risk(self, context: SecurityContext, request_context: Dict[str, Any]) -> float:
        """Assess network security risk"""
        try:
            risk = 0.0
            
            # Check IP reputation
            if context.ip_address in self.blocked_ips:
                risk += 0.8
            
            # Check for VPN/Tor
            if await self._detect_vpn_tor(context.ip_address):
                risk += 0.4
            
            # Check geographic location
            if context.location:
                # This would check against known risky locations
                risk += 0.2
            
            return min(risk, 1.0)
            
        except Exception as e:
            logger.error(f"Error assessing network risk: {e}")
            return 0.0
    
    async def _assess_device_risk(self, context: SecurityContext, request_context: Dict[str, Any]) -> float:
        """Assess device security risk"""
        try:
            risk = 0.0
            
            # Check device trust
            if not context.device_trusted:
                risk += 0.3
            
            # Check browser security
            user_agent = context.user_agent.lower()
            if 'bot' in user_agent or 'crawler' in user_agent:
                risk += 0.5
            
            # Check for suspicious headers
            if 'x-forwarded-for' in request_context:
                risk += 0.2
            
            return min(risk, 1.0)
            
        except Exception as e:
            logger.error(f"Error assessing device risk: {e}")
            return 0.0
    
    async def _should_block_authentication(self, context: SecurityContext) -> bool:
        """Check if authentication should be blocked"""
        try:
            # Block if IP is in blocked list
            if context.ip_address in self.blocked_ips:
                return True
            
            # Block if too many failed attempts
            failed_attempts = self.failed_attempts.get(context.ip_address, 0)
            if failed_attempts > 10:
                return True
            
            # Block if risk score is too high
            if context.risk_score > 0.9:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking authentication block: {e}")
            return False
    
    async def _verify_credentials(self, user_id: str, credentials: Dict[str, Any]) -> bool:
        """Verify user credentials"""
        try:
            # This would typically verify against a user database
            # For now, we'll use a simple mock verification
            password = credentials.get('password', '')
            if not password:
                return False
            
            # Mock password verification
            # In production, this would use proper password hashing
            return len(password) >= 8
            
        except Exception as e:
            logger.error(f"Error verifying credentials: {e}")
            return False
    
    async def _verify_mfa(self, user_id: str, mfa_code: Optional[str]) -> bool:
        """Verify MFA code"""
        try:
            if not mfa_code:
                return False
            
            # This would typically verify against a TOTP app or SMS
            # For now, we'll use a simple mock verification
            return len(mfa_code) == 6 and mfa_code.isdigit()
            
        except Exception as e:
            logger.error(f"Error verifying MFA: {e}")
            return False
    
    async def _generate_session_token(self, context: SecurityContext) -> str:
        """Generate secure session token"""
        try:
            payload = {
                'user_id': context.user_id,
                'session_id': context.session_id,
                'security_level': context.security_level.value,
                'exp': datetime.now() + timedelta(hours=24),
                'iat': datetime.now()
            }
            
            token = jwt.encode(
                payload,
                self.encryption_keys['jwt_private'],
                algorithm='RS256'
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Error generating session token: {e}")
            return ""
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions"""
        try:
            # This would typically fetch from a user database
            # For now, we'll return default permissions
            return ['read', 'write', 'api_access']
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []
    
    async def _check_rate_limit(self, context: SecurityContext, endpoint: str) -> bool:
        """Check rate limiting"""
        try:
            key = f"{context.ip_address}:{endpoint}"
            current_time = time.time()
            
            # Clean old entries
            while self.rate_limiters[key] and self.rate_limiters[key][0] < current_time - 60:
                self.rate_limiters[key].popleft()
            
            # Check if limit exceeded
            if len(self.rate_limiters[key]) >= 100:  # 100 requests per minute
                return False
            
            # Add current request
            self.rate_limiters[key].append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    async def _check_endpoint_permissions(self, context: SecurityContext, endpoint: str, method: str) -> bool:
        """Check endpoint permissions"""
        try:
            # Check if user has required permissions
            if endpoint.startswith('/api/admin/') and 'admin' not in context.permissions:
                return False
            
            if endpoint.startswith('/api/financial/') and 'financial' not in context.permissions:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking endpoint permissions: {e}")
            return False
    
    async def _check_security_policies(self, context: SecurityContext, endpoint: str, method: str) -> bool:
        """Check security policies"""
        try:
            for policy in self.security_policies.values():
                if not policy.enabled:
                    continue
                
                for rule in policy.rules:
                    if not await self._evaluate_rule(rule, context, endpoint, method):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking security policies: {e}")
            return False
    
    async def _evaluate_rule(self, rule: Dict[str, Any], context: SecurityContext, 
                           endpoint: str, method: str) -> bool:
        """Evaluate a security rule"""
        try:
            rule_type = rule.get('type')
            
            if rule_type == 'rate_limit':
                return await self._check_rate_limit(context, endpoint)
            
            elif rule_type == 'ip_block':
                return context.ip_address not in self.blocked_ips
            
            elif rule_type == 'mfa_required':
                if endpoint in rule.get('endpoints', []):
                    return context.mfa_verified
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return True
    
    async def _detect_vpn_tor(self, ip_address: str) -> bool:
        """Detect VPN or Tor usage"""
        try:
            # This would typically use a VPN/Tor detection service
            # For now, we'll use a simple mock detection
            return False
            
        except Exception as e:
            logger.error(f"Error detecting VPN/Tor: {e}")
            return False
    
    async def _log_security_event(self, event_type: str, severity: ThreatLevel, 
                                user_id: Optional[str], ip_address: str, 
                                description: str, metadata: Dict[str, Any] = None):
        """Log security event"""
        try:
            event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                severity=severity,
                timestamp=datetime.now(),
                user_id=user_id,
                ip_address=ip_address,
                description=description,
                metadata=metadata or {},
                risk_score=0.0
            )
            
            self.security_events.append(event)
            
            # Log to external systems if needed
            if severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                logger.warning(f"High severity security event: {event_type} - {description}")
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    async def _analyze_security_patterns(self, events: List[SecurityEvent]):
        """Analyze security patterns from events"""
        try:
            # Analyze patterns and update risk models
            # This would typically involve machine learning
            pass
            
        except Exception as e:
            logger.error(f"Error analyzing security patterns: {e}")
    
    async def _update_blocked_ips(self, events: List[SecurityEvent]):
        """Update blocked IPs based on events"""
        try:
            for event in events:
                if event.severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                    self.blocked_ips.add(event.ip_address)
            
        except Exception as e:
            logger.error(f"Error updating blocked IPs: {e}")
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics"""
        try:
            recent_events = [event for event in self.security_events 
                           if event.timestamp > datetime.now() - timedelta(hours=24)]
            
            return {
                "total_events": len(self.security_events),
                "recent_events": len(recent_events),
                "high_severity_events": len([e for e in recent_events if e.severity == ThreatLevel.HIGH]),
                "critical_events": len([e for e in recent_events if e.severity == ThreatLevel.CRITICAL]),
                "blocked_ips": len(self.blocked_ips),
                "active_sessions": len(self.security_contexts),
                "failed_attempts": sum(self.failed_attempts.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting security metrics: {e}")
            return {}

# Global zero-trust security engine
zero_trust_engine = ZeroTrustEngine()
