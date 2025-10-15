"""
Security API - Phase 3
FastAPI endpoints for security management, compliance, and audit
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import logging
from datetime import datetime, timedelta

from .zero_trust_security import zero_trust_engine, SecurityContext, SecurityLevel, ThreatLevel
from .encryption_manager import encryption_manager, KeyPurpose, EncryptionType
from .compliance_manager import compliance_manager, ComplianceFramework, DataClassification, AuditEventType

logger = logging.getLogger("richesreach")

# Create router
router = APIRouter(prefix="/security", tags=["Security Management"])

# Security dependency
security = HTTPBearer()

# Pydantic models for API
class AuthenticationRequest(BaseModel):
    """Authentication request model"""
    user_id: str = Field(..., description="User ID")
    password: str = Field(..., description="Password")
    mfa_code: Optional[str] = Field(None, description="MFA code")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")

class AuthenticationResponse(BaseModel):
    """Authentication response model"""
    success: bool
    session_token: Optional[str] = None
    security_level: Optional[str] = None
    risk_score: Optional[float] = None
    message: str

class AuthorizationRequest(BaseModel):
    """Authorization request model"""
    endpoint: str = Field(..., description="API endpoint")
    method: str = Field(..., description="HTTP method")
    resource_id: Optional[str] = Field(None, description="Resource ID")

class EncryptionRequest(BaseModel):
    """Encryption request model"""
    data: str = Field(..., description="Data to encrypt")
    purpose: str = Field(..., description="Encryption purpose")
    context: Optional[Dict[str, Any]] = Field(None, description="Encryption context")

class DecryptionRequest(BaseModel):
    """Decryption request model"""
    encrypted_data: str = Field(..., description="Encrypted data (base64)")
    key_id: str = Field(..., description="Key ID")
    iv: Optional[str] = Field(None, description="Initialization vector (base64)")
    tag: Optional[str] = Field(None, description="Authentication tag (base64)")

class DataSubjectRequest(BaseModel):
    """Data subject registration request"""
    email: str = Field(..., description="Email address")
    name: Optional[str] = Field(None, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[Dict[str, str]] = Field(None, description="Address")
    consent_given: bool = Field(False, description="Consent given")

class ConsentUpdateRequest(BaseModel):
    """Consent update request"""
    subject_id: str = Field(..., description="Data subject ID")
    consent_given: bool = Field(..., description="Consent status")

class DataDeletionRequest(BaseModel):
    """Data deletion request"""
    subject_id: str = Field(..., description="Data subject ID")
    reason: str = Field("user_request", description="Deletion reason")

# Security middleware
async def get_security_context(credentials: HTTPAuthorizationCredentials = Depends(security)) -> SecurityContext:
    """Get security context from token"""
    try:
        # Verify JWT token
        success, payload = await encryption_manager.verify_jwt_token(credentials.credentials)
        if not success:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get session context
        session_id = payload.get('session_id')
        if not session_id:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        # Get security context
        context = zero_trust_engine.security_contexts.get(session_id)
        if not context:
            raise HTTPException(status_code=401, detail="Session expired")
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting security context: {e}")
        raise HTTPException(status_code=401, detail="Authentication error")

# Authentication Endpoints
@router.post("/authenticate", response_model=AuthenticationResponse)
async def authenticate_user(request: AuthenticationRequest, http_request: Request):
    """Authenticate user with zero-trust principles"""
    try:
        # Get request context
        request_context = {
            'ip_address': http_request.client.host,
            'user_agent': http_request.headers.get('user-agent', ''),
            'device_fingerprint': request.device_fingerprint
        }
        
        # Authenticate user
        success, context = await zero_trust_engine.authenticate_user(
            request.user_id,
            {
                'password': request.password,
                'mfa_code': request.mfa_code
            },
            request_context
        )
        
        if not success:
            return AuthenticationResponse(
                success=False,
                message="Authentication failed"
            )
        
        # Generate session token
        session_token = await encryption_manager.generate_jwt_token({
            'user_id': context.user_id,
            'session_id': context.session_id,
            'security_level': context.security_level.value,
            'risk_score': context.risk_score
        })
        
        return AuthenticationResponse(
            success=True,
            session_token=session_token,
            security_level=context.security_level.value,
            risk_score=context.risk_score,
            message="Authentication successful"
        )
        
    except Exception as e:
        logger.error(f"Error in authentication: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/authorize")
async def authorize_request(request: AuthorizationRequest, 
                          context: SecurityContext = Depends(get_security_context),
                          http_request: Request = None):
    """Authorize request with zero-trust principles"""
    try:
        # Get request context
        request_context = {
            'ip_address': http_request.client.host if http_request else 'unknown',
            'user_agent': http_request.headers.get('user-agent', '') if http_request else '',
            'resource_id': request.resource_id
        }
        
        # Authorize request
        authorized, message = await zero_trust_engine.authorize_request(
            context.session_id,
            request.endpoint,
            request.method,
            request_context
        )
        
        if not authorized:
            raise HTTPException(status_code=403, detail=message)
        
        return {"authorized": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in authorization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Encryption Endpoints
@router.post("/encrypt")
async def encrypt_data(request: EncryptionRequest, 
                      context: SecurityContext = Depends(get_security_context)):
    """Encrypt data using appropriate encryption method"""
    try:
        # Determine key purpose
        purpose_map = {
            'data': KeyPurpose.DATA_ENCRYPTION,
            'api': KeyPurpose.API_ENCRYPTION,
            'session': KeyPurpose.SESSION_ENCRYPTION,
            'file': KeyPurpose.FILE_ENCRYPTION
        }
        
        purpose = purpose_map.get(request.purpose, KeyPurpose.DATA_ENCRYPTION)
        
        # Encrypt data
        result = await encryption_manager.encrypt_data(
            request.data,
            purpose,
            request.context
        )
        
        # Log audit event
        await compliance_manager.log_audit_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            user_id=context.user_id,
            session_id=context.session_id,
            ip_address=context.ip_address,
            resource_type="encrypted_data",
            resource_id=result.key_id,
            action="encrypt",
            result="success",
            details={"purpose": request.purpose}
        )
        
        return {
            "encrypted_data": base64.b64encode(result.encrypted_data).decode('utf-8'),
            "key_id": result.key_id,
            "iv": base64.b64encode(result.iv).decode('utf-8') if result.iv else None,
            "tag": base64.b64encode(result.tag).decode('utf-8') if result.tag else None,
            "algorithm": result.algorithm
        }
        
    except Exception as e:
        logger.error(f"Error in encryption: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decrypt")
async def decrypt_data(request: DecryptionRequest, 
                      context: SecurityContext = Depends(get_security_context)):
    """Decrypt data using appropriate decryption method"""
    try:
        # Reconstruct encryption result
        from .encryption_manager import EncryptionResult
        import base64
        
        encrypted_result = EncryptionResult(
            encrypted_data=base64.b64decode(request.encrypted_data),
            key_id=request.key_id,
            iv=base64.b64decode(request.iv) if request.iv else None,
            tag=base64.b64decode(request.tag) if request.tag else None
        )
        
        # Decrypt data (we need to determine the purpose from the key)
        # For now, we'll try data encryption purpose
        result = await encryption_manager.decrypt_data(
            encrypted_result,
            KeyPurpose.DATA_ENCRYPTION
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
        
        # Log audit event
        await compliance_manager.log_audit_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=context.user_id,
            session_id=context.session_id,
            ip_address=context.ip_address,
            resource_type="encrypted_data",
            resource_id=request.key_id,
            action="decrypt",
            result="success"
        )
        
        return {
            "decrypted_data": result.decrypted_data.decode('utf-8'),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in decryption: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Compliance Endpoints
@router.post("/data-subjects")
async def register_data_subject(request: DataSubjectRequest, 
                               context: SecurityContext = Depends(get_security_context)):
    """Register data subject for GDPR compliance"""
    try:
        # Register data subject
        subject_id = await compliance_manager.register_data_subject(
            email=request.email,
            name=request.name,
            phone=request.phone,
            address=request.address,
            consent_given=request.consent_given
        )
        
        if not subject_id:
            raise HTTPException(status_code=400, detail="Failed to register data subject")
        
        return {
            "subject_id": subject_id,
            "message": "Data subject registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Error registering data subject: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/consent")
async def update_consent(request: ConsentUpdateRequest, 
                        context: SecurityContext = Depends(get_security_context)):
    """Update consent for data subject"""
    try:
        # Update consent
        success = await compliance_manager.update_consent(
            request.subject_id,
            request.consent_given
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update consent")
        
        return {
            "success": True,
            "message": "Consent updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data-deletion")
async def request_data_deletion(request: DataDeletionRequest, 
                               context: SecurityContext = Depends(get_security_context)):
    """Request data deletion for GDPR compliance"""
    try:
        # Request data deletion
        success = await compliance_manager.request_data_deletion(
            request.subject_id,
            request.reason
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to request data deletion")
        
        return {
            "success": True,
            "message": "Data deletion requested successfully"
        }
        
    except Exception as e:
        logger.error(f"Error requesting data deletion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Security Monitoring Endpoints
@router.get("/metrics")
async def get_security_metrics(context: SecurityContext = Depends(get_security_context)):
    """Get security metrics"""
    try:
        # Get metrics from all security components
        zero_trust_metrics = zero_trust_engine.get_security_metrics()
        encryption_metrics = encryption_manager.get_encryption_metrics()
        compliance_metrics = compliance_manager.get_compliance_metrics()
        
        return {
            "zero_trust": zero_trust_metrics,
            "encryption": encryption_metrics,
            "compliance": compliance_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-events")
async def get_audit_events(limit: int = 100, 
                          event_type: Optional[str] = None,
                          context: SecurityContext = Depends(get_security_context)):
    """Get audit events"""
    try:
        # Get recent audit events
        events = list(compliance_manager.audit_events)[-limit:]
        
        # Filter by event type if specified
        if event_type:
            events = [event for event in events if event.event_type.value == event_type]
        
        # Convert to serializable format
        serializable_events = []
        for event in events:
            serializable_events.append({
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "action": event.action,
                "result": event.result,
                "compliance_frameworks": [f.value for f in event.compliance_frameworks],
                "data_classification": event.data_classification.value
            })
        
        return {
            "events": serializable_events,
            "total": len(serializable_events),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting audit events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance-report")
async def get_compliance_report(context: SecurityContext = Depends(get_security_context)):
    """Get compliance report"""
    try:
        # Get latest compliance report
        latest_date = max(compliance_manager.compliance_reports.keys()) if compliance_manager.compliance_reports else None
        
        if not latest_date:
            return {"message": "No compliance reports available"}
        
        report = compliance_manager.compliance_reports[latest_date]
        
        return {
            "report": report,
            "date": latest_date.isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/violations")
async def get_compliance_violations(limit: int = 100, 
                                   context: SecurityContext = Depends(get_security_context)):
    """Get compliance violations"""
    try:
        # Get recent violations
        violations = list(compliance_manager.violation_alerts)[-limit:]
        
        return {
            "violations": violations,
            "total": len(violations),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@router.get("/health")
async def security_health():
    """Health check for security system"""
    try:
        # Check all security components
        zero_trust_healthy = len(zero_trust_engine.security_contexts) >= 0
        encryption_healthy = len(encryption_manager.encryption_keys) > 0
        compliance_healthy = len(compliance_manager.compliance_rules) > 0
        
        overall_healthy = zero_trust_healthy and encryption_healthy and compliance_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "components": {
                "zero_trust": zero_trust_healthy,
                "encryption": encryption_healthy,
                "compliance": compliance_healthy
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
