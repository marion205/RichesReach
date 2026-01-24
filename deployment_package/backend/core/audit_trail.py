# core/audit_trail.py
"""
Audit Trail for Regulatory Compliance
Logs all AI decisions for SEC/FINRA compliance (2026 standards).

Regulators now expect an Audit Trail of AI decisions. This module provides
structured logging of all AI interactions for compliance and debugging.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    """Types of AI decisions"""
    ROUTING = "routing"
    TOOL_CALL = "tool_call"
    ALGORITHM_EXECUTION = "algorithm_execution"
    RESPONSE_GENERATION = "response_generation"
    COMPLIANCE_CHECK = "compliance_check"


@dataclass
class AuditTrailEntry:
    """
    Audit trail entry for a single AI decision.
    
    Fields required by 2026 SEC/FINRA standards:
    - raw_llm_input: What the user actually said (scrubbed of PII)
    - tool_called: The specific Python function used
    - tool_output_raw: The exact math returned before AI "translated" it
    - disclosure_version: Which legal footer was shown
    """
    timestamp: str
    user_id: Optional[str]
    session_id: Optional[str]
    decision_type: DecisionType
    
    # Input tracking
    raw_llm_input: str  # User query (PII-scrubbed)
    user_context: Optional[str] = None
    
    # Routing tracking
    routing_decision: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None
    
    # Tool/Algorithm tracking
    tool_called: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    tool_output_raw: Optional[Dict[str, Any]] = None  # Exact algorithm output
    
    # Response tracking
    llm_response: Optional[str] = None
    final_response: Optional[str] = None
    
    # Compliance tracking
    disclosure_version: Optional[str] = None
    disclosure_type: Optional[str] = None  # "standard" | "algorithmic"
    compliance_flags: Optional[List[str]] = None
    
    # Performance tracking
    latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    
    # Metadata
    intent_classified: Optional[str] = None
    pii_scrubbed: bool = False
    pii_scrubbing_stats: Optional[Dict[str, Any]] = None


class AuditTrailLogger:
    """
    Logs AI decisions for regulatory compliance.
    
    In production, these logs should be:
    1. Stored in a secure, immutable database
    2. Encrypted at rest
    3. Accessible only to compliance officers
    4. Retained for required period (typically 7 years for financial records)
    """
    
    def __init__(self, enable_database_logging: bool = False):
        """
        Initialize audit trail logger.
        
        Args:
            enable_database_logging: If True, logs to database (requires DB model)
        """
        self.enable_database_logging = enable_database_logging
        self.audit_logger = logging.getLogger("audit_trail")
        
        # Configure audit logger (separate from application logs)
        if not self.audit_logger.handlers:
            handler = logging.FileHandler("logs/audit_trail.log")
            handler.setFormatter(
                logging.Formatter('%(asctime)s | %(message)s')
            )
            self.audit_logger.addHandler(handler)
            self.audit_logger.setLevel(logging.INFO)
    
    def log_decision(
        self,
        entry: AuditTrailEntry
    ) -> str:
        """
        Log an AI decision to audit trail.
        
        Args:
            entry: Audit trail entry
            
        Returns:
            Audit trail entry ID (for database storage)
        """
        # Convert to dict for logging
        entry_dict = asdict(entry)
        
        # Log to file (JSON format for easy parsing)
        log_message = json.dumps(entry_dict, default=str)
        self.audit_logger.info(log_message)
        
        # Log to database if enabled
        if self.enable_database_logging:
            # TODO: Implement database storage
            # from core.models import AuditTrail
            # AuditTrail.objects.create(**entry_dict)
            pass
        
        # Also log to application logger for debugging
        logger.debug(f"Audit trail: {entry.decision_type} | Tool: {entry.tool_called} | Model: {entry.model_used}")
        
        return entry_dict.get("timestamp", datetime.now().isoformat())
    
    def create_entry(
        self,
        decision_type: DecisionType,
        raw_llm_input: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AuditTrailEntry:
        """
        Create an audit trail entry.
        
        Args:
            decision_type: Type of decision
            raw_llm_input: User's input (PII-scrubbed)
            user_id: User ID (if available)
            session_id: Session ID (if available)
            **kwargs: Additional fields for the entry
            
        Returns:
            AuditTrailEntry
        """
        return AuditTrailEntry(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            session_id=session_id,
            decision_type=decision_type,
            raw_llm_input=raw_llm_input,
            **kwargs
        )
    
    def log_routing_decision(
        self,
        user_query: str,
        routing_decision: Dict[str, Any],
        model_used: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Log a routing decision"""
        entry = self.create_entry(
            decision_type=DecisionType.ROUTING,
            raw_llm_input=user_query,
            user_id=user_id,
            session_id=session_id,
            routing_decision=routing_decision,
            model_used=model_used,
            intent_classified=routing_decision.get("intent", {}).get("value") if isinstance(routing_decision.get("intent"), dict) else str(routing_decision.get("intent", ""))
        )
        return self.log_decision(entry)
    
    def log_tool_call(
        self,
        user_query: str,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        tool_output: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Log a tool/algorithm call"""
        entry = self.create_entry(
            decision_type=DecisionType.TOOL_CALL,
            raw_llm_input=user_query,
            user_id=user_id,
            session_id=session_id,
            tool_called=tool_name,
            tool_arguments=tool_arguments,
            tool_output_raw=tool_output  # Exact algorithm output
        )
        return self.log_decision(entry)
    
    def log_final_response(
        self,
        user_query: str,
        llm_response: str,
        final_response: str,
        disclosure_version: str,
        disclosure_type: str,
        model_used: str,
        tool_called: Optional[str] = None,
        tool_output: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        latency_ms: Optional[int] = None,
        tokens_used: Optional[int] = None
    ) -> str:
        """Log final response with full audit trail"""
        entry = self.create_entry(
            decision_type=DecisionType.RESPONSE_GENERATION,
            raw_llm_input=user_query,
            user_id=user_id,
            session_id=session_id,
            model_used=model_used,
            tool_called=tool_called,
            tool_output_raw=tool_output,
            llm_response=llm_response,
            final_response=final_response,
            disclosure_version=disclosure_version,
            disclosure_type=disclosure_type,
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )
        return self.log_decision(entry)


# Singleton instance
_audit_trail = AuditTrailLogger()


def get_audit_trail() -> AuditTrailLogger:
    """Get singleton audit trail logger"""
    return _audit_trail

