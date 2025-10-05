"""
Compliance Manager - Phase 3
Comprehensive compliance framework for GDPR, SOX, PCI-DSS, and other regulations
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
from enum import Enum
from collections import defaultdict, deque
import threading
import weakref

logger = logging.getLogger("richesreach")

class ComplianceFramework(Enum):
    """Compliance framework enumeration"""
    GDPR = "gdpr"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    CCPA = "ccpa"

class DataClassification(Enum):
    """Data classification enumeration"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    FINANCIAL = "financial"
    HEALTH = "health"

class AuditEventType(Enum):
    """Audit event type enumeration"""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_CHANGE = "permission_change"
    SYSTEM_CONFIGURATION = "system_configuration"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_VIOLATION = "compliance_violation"

@dataclass
class ComplianceRule:
    """Compliance rule data structure"""
    rule_id: str
    framework: ComplianceFramework
    name: str
    description: str
    data_classification: DataClassification
    requirements: List[str]
    controls: List[str]
    enabled: bool = True
    severity: str = "medium"
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    resource_type: str
    resource_id: str
    action: str
    result: str
    details: Dict[str, Any]
    compliance_frameworks: List[ComplianceFramework]
    data_classification: DataClassification
    retention_period: timedelta

@dataclass
class DataSubject:
    """Data subject for GDPR compliance"""
    subject_id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    consent_given: bool = False
    consent_date: Optional[datetime] = None
    data_retention_date: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None

class ComplianceManager:
    """Comprehensive compliance and audit management system"""
    
    def __init__(self):
        self.compliance_rules = {}
        self.audit_events = deque(maxlen=1000000)  # 1M events
        self.data_subjects = {}
        self.consent_records = {}
        self.data_retention_policies = {}
        self.compliance_reports = {}
        self.violation_alerts = deque(maxlen=10000)
        
        # Initialize compliance system
        asyncio.create_task(self._initialize_compliance())
        
        # Start background tasks
        asyncio.create_task(self._process_audit_events())
        asyncio.create_task(self._check_compliance_violations())
        asyncio.create_task(self._cleanup_expired_data())
        asyncio.create_task(self._generate_compliance_reports())
    
    async def _initialize_compliance(self):
        """Initialize compliance system"""
        try:
            # Load compliance rules
            await self._load_compliance_rules()
            
            # Initialize data retention policies
            await self._initialize_data_retention_policies()
            
            # Load existing data subjects
            await self._load_data_subjects()
            
            logger.info("✅ Compliance manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize compliance manager: {e}")
            raise
    
    async def _load_compliance_rules(self):
        """Load compliance rules for different frameworks"""
        try:
            # GDPR Rules
            gdpr_rules = [
                {
                    "rule_id": "gdpr_data_minimization",
                    "name": "Data Minimization",
                    "description": "Collect only necessary personal data",
                    "data_classification": DataClassification.PII,
                    "requirements": [
                        "Collect only data necessary for the stated purpose",
                        "Regularly review and delete unnecessary data",
                        "Implement data minimization in all processes"
                    ],
                    "controls": [
                        "Data collection audit",
                        "Regular data review",
                        "Automated data cleanup"
                    ]
                },
                {
                    "rule_id": "gdpr_consent_management",
                    "name": "Consent Management",
                    "description": "Proper consent collection and management",
                    "data_classification": DataClassification.PII,
                    "requirements": [
                        "Obtain explicit consent before data collection",
                        "Allow users to withdraw consent",
                        "Maintain consent records"
                    ],
                    "controls": [
                        "Consent tracking system",
                        "Consent withdrawal mechanism",
                        "Consent audit trail"
                    ]
                },
                {
                    "rule_id": "gdpr_right_to_erasure",
                    "name": "Right to Erasure",
                    "description": "Data subject's right to have data deleted",
                    "data_classification": DataClassification.PII,
                    "requirements": [
                        "Provide mechanism for data deletion requests",
                        "Delete data within 30 days of request",
                        "Maintain audit trail of deletions"
                    ],
                    "controls": [
                        "Data deletion API",
                        "Automated deletion process",
                        "Deletion audit trail"
                    ]
                }
            ]
            
            # SOX Rules
            sox_rules = [
                {
                    "rule_id": "sox_financial_controls",
                    "name": "Financial Controls",
                    "description": "Controls over financial reporting",
                    "data_classification": DataClassification.FINANCIAL,
                    "requirements": [
                        "Implement controls over financial data",
                        "Maintain audit trail of financial transactions",
                        "Regular review of financial controls"
                    ],
                    "controls": [
                        "Financial data encryption",
                        "Transaction audit trail",
                        "Regular control testing"
                    ]
                }
            ]
            
            # PCI-DSS Rules
            pci_rules = [
                {
                    "rule_id": "pci_data_protection",
                    "name": "Cardholder Data Protection",
                    "description": "Protect cardholder data",
                    "data_classification": DataClassification.FINANCIAL,
                    "requirements": [
                        "Encrypt cardholder data in transit and at rest",
                        "Implement access controls",
                        "Regular security testing"
                    ],
                    "controls": [
                        "Data encryption",
                        "Access control system",
                        "Security monitoring"
                    ]
                }
            ]
            
            # Load all rules
            all_rules = gdpr_rules + sox_rules + pci_rules
            
            for rule_data in all_rules:
                rule = ComplianceRule(
                    rule_id=rule_data["rule_id"],
                    framework=ComplianceFramework.GDPR if "gdpr" in rule_data["rule_id"] else
                             ComplianceFramework.SOX if "sox" in rule_data["rule_id"] else
                             ComplianceFramework.PCI_DSS,
                    name=rule_data["name"],
                    description=rule_data["description"],
                    data_classification=rule_data["data_classification"],
                    requirements=rule_data["requirements"],
                    controls=rule_data["controls"],
                    created_at=datetime.now()
                )
                self.compliance_rules[rule.rule_id] = rule
            
            logger.info(f"✅ Loaded {len(self.compliance_rules)} compliance rules")
            
        except Exception as e:
            logger.error(f"❌ Failed to load compliance rules: {e}")
            raise
    
    async def _initialize_data_retention_policies(self):
        """Initialize data retention policies"""
        try:
            self.data_retention_policies = {
                DataClassification.PII: timedelta(days=2555),  # 7 years
                DataClassification.FINANCIAL: timedelta(days=2555),  # 7 years
                DataClassification.HEALTH: timedelta(days=2555),  # 7 years
                DataClassification.CONFIDENTIAL: timedelta(days=1095),  # 3 years
                DataClassification.INTERNAL: timedelta(days=365),  # 1 year
                DataClassification.PUBLIC: timedelta(days=90),  # 3 months
                DataClassification.RESTRICTED: timedelta(days=2555)  # 7 years
            }
            
            logger.info("✅ Data retention policies initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize data retention policies: {e}")
            raise
    
    async def _load_data_subjects(self):
        """Load existing data subjects"""
        try:
            # This would typically load from a database
            # For now, we'll initialize with empty data
            self.data_subjects = {}
            
            logger.info("✅ Data subjects loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load data subjects: {e}")
            raise
    
    async def _process_audit_events(self):
        """Process audit events for compliance"""
        while True:
            try:
                # Process recent audit events
                recent_events = [event for event in self.audit_events 
                               if event.timestamp > datetime.now() - timedelta(minutes=5)]
                
                # Check for compliance violations
                await self._check_events_for_violations(recent_events)
                
                # Update compliance metrics
                await self._update_compliance_metrics()
                
                await asyncio.sleep(300)  # Process every 5 minutes
                
            except Exception as e:
                logger.error(f"Error processing audit events: {e}")
                await asyncio.sleep(300)
    
    async def _check_compliance_violations(self):
        """Check for compliance violations"""
        while True:
            try:
                # Check each compliance rule
                for rule in self.compliance_rules.values():
                    if not rule.enabled:
                        continue
                    
                    violations = await self._check_rule_compliance(rule)
                    
                    for violation in violations:
                        await self._handle_compliance_violation(rule, violation)
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error checking compliance violations: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_expired_data(self):
        """Clean up expired data based on retention policies"""
        while True:
            try:
                current_time = datetime.now()
                cleanup_count = 0
                
                # Check data subjects for expiration
                expired_subjects = []
                for subject_id, subject in self.data_subjects.items():
                    if subject.data_retention_date and current_time > subject.data_retention_date:
                        expired_subjects.append(subject_id)
                
                # Clean up expired subjects
                for subject_id in expired_subjects:
                    await self._delete_data_subject(subject_id)
                    cleanup_count += 1
                
                # Check audit events for expiration
                expired_events = []
                for event in self.audit_events:
                    if current_time - event.timestamp > event.retention_period:
                        expired_events.append(event.event_id)
                
                # Remove expired events
                self.audit_events = deque(
                    [event for event in self.audit_events if event.event_id not in expired_events],
                    maxlen=1000000
                )
                
                if cleanup_count > 0 or expired_events:
                    logger.info(f"✅ Cleaned up {cleanup_count} data subjects and {len(expired_events)} audit events")
                
                await asyncio.sleep(86400)  # Cleanup daily
                
            except Exception as e:
                logger.error(f"Error cleaning up expired data: {e}")
                await asyncio.sleep(86400)
    
    async def _generate_compliance_reports(self):
        """Generate compliance reports"""
        while True:
            try:
                # Generate daily compliance report
                report = await self._create_compliance_report()
                self.compliance_reports[datetime.now().date()] = report
                
                # Keep only last 30 days of reports
                cutoff_date = datetime.now().date() - timedelta(days=30)
                self.compliance_reports = {
                    date: report for date, report in self.compliance_reports.items()
                    if date > cutoff_date
                }
                
                logger.info("✅ Generated compliance report")
                
                await asyncio.sleep(86400)  # Generate daily
                
            except Exception as e:
                logger.error(f"Error generating compliance reports: {e}")
                await asyncio.sleep(86400)
    
    async def log_audit_event(self, event_type: AuditEventType, user_id: Optional[str],
                            session_id: Optional[str], ip_address: str, resource_type: str,
                            resource_id: str, action: str, result: str, 
                            details: Dict[str, Any] = None) -> str:
        """Log audit event for compliance"""
        try:
            event_id = str(uuid.uuid4())
            
            # Determine data classification
            data_classification = await self._determine_data_classification(
                resource_type, resource_id, details
            )
            
            # Determine applicable compliance frameworks
            compliance_frameworks = await self._determine_compliance_frameworks(
                data_classification, details
            )
            
            # Determine retention period
            retention_period = self.data_retention_policies.get(
                data_classification, timedelta(days=2555)
            )
            
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                result=result,
                details=details or {},
                compliance_frameworks=compliance_frameworks,
                data_classification=data_classification,
                retention_period=retention_period
            )
            
            self.audit_events.append(event)
            
            # Log to external systems if needed
            if data_classification in [DataClassification.PII, DataClassification.FINANCIAL]:
                logger.info(f"Compliance audit event: {event_type.value} - {action}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log audit event: {e}")
            return ""
    
    async def register_data_subject(self, email: str, name: Optional[str] = None,
                                  phone: Optional[str] = None, 
                                  address: Optional[Dict[str, str]] = None,
                                  consent_given: bool = False) -> str:
        """Register data subject for GDPR compliance"""
        try:
            subject_id = str(uuid.uuid4())
            current_time = datetime.now()
            
            # Determine retention date
            retention_period = self.data_retention_policies[DataClassification.PII]
            retention_date = current_time + retention_period
            
            subject = DataSubject(
                subject_id=subject_id,
                email=email,
                name=name,
                phone=phone,
                address=address,
                consent_given=consent_given,
                consent_date=current_time if consent_given else None,
                data_retention_date=retention_date,
                created_at=current_time,
                updated_at=current_time
            )
            
            self.data_subjects[subject_id] = subject
            
            # Log audit event
            await self.log_audit_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=None,
                session_id=None,
                ip_address="system",
                resource_type="data_subject",
                resource_id=subject_id,
                action="register",
                result="success",
                details={"email": email, "consent_given": consent_given}
            )
            
            logger.info(f"✅ Registered data subject: {email}")
            return subject_id
            
        except Exception as e:
            logger.error(f"❌ Failed to register data subject: {e}")
            return ""
    
    async def update_consent(self, subject_id: str, consent_given: bool) -> bool:
        """Update consent for data subject"""
        try:
            subject = self.data_subjects.get(subject_id)
            if not subject:
                return False
            
            subject.consent_given = consent_given
            subject.consent_date = datetime.now() if consent_given else None
            subject.updated_at = datetime.now()
            
            # Log audit event
            await self.log_audit_event(
                event_type=AuditEventType.DATA_MODIFICATION,
                user_id=None,
                session_id=None,
                ip_address="system",
                resource_type="data_subject",
                resource_id=subject_id,
                action="update_consent",
                result="success",
                details={"consent_given": consent_given}
            )
            
            logger.info(f"✅ Updated consent for subject {subject_id}: {consent_given}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update consent: {e}")
            return False
    
    async def request_data_deletion(self, subject_id: str, reason: str = "user_request") -> bool:
        """Request data deletion for GDPR compliance"""
        try:
            subject = self.data_subjects.get(subject_id)
            if not subject:
                return False
            
            # Log deletion request
            await self.log_audit_event(
                event_type=AuditEventType.DATA_DELETION,
                user_id=None,
                session_id=None,
                ip_address="system",
                resource_type="data_subject",
                resource_id=subject_id,
                action="deletion_request",
                result="success",
                details={"reason": reason, "email": subject.email}
            )
            
            # Schedule deletion (GDPR requires deletion within 30 days)
            deletion_date = datetime.now() + timedelta(days=30)
            subject.data_retention_date = deletion_date
            
            logger.info(f"✅ Scheduled data deletion for subject {subject_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to request data deletion: {e}")
            return False
    
    async def _delete_data_subject(self, subject_id: str):
        """Delete data subject and associated data"""
        try:
            subject = self.data_subjects.get(subject_id)
            if not subject:
                return
            
            # Log deletion
            await self.log_audit_event(
                event_type=AuditEventType.DATA_DELETION,
                user_id=None,
                session_id=None,
                ip_address="system",
                resource_type="data_subject",
                resource_id=subject_id,
                action="delete",
                result="success",
                details={"email": subject.email}
            )
            
            # Delete subject
            del self.data_subjects[subject_id]
            
            logger.info(f"✅ Deleted data subject: {subject_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to delete data subject: {e}")
    
    async def _determine_data_classification(self, resource_type: str, 
                                           resource_id: str, 
                                           details: Dict[str, Any]) -> DataClassification:
        """Determine data classification for resource"""
        try:
            # Simple classification logic
            if resource_type in ["user", "profile", "contact"]:
                return DataClassification.PII
            elif resource_type in ["transaction", "payment", "financial"]:
                return DataClassification.FINANCIAL
            elif resource_type in ["health", "medical"]:
                return DataClassification.HEALTH
            elif resource_type in ["admin", "system"]:
                return DataClassification.RESTRICTED
            elif resource_type in ["public", "marketing"]:
                return DataClassification.PUBLIC
            else:
                return DataClassification.INTERNAL
                
        except Exception as e:
            logger.error(f"❌ Failed to determine data classification: {e}")
            return DataClassification.INTERNAL
    
    async def _determine_compliance_frameworks(self, data_classification: DataClassification,
                                             details: Dict[str, Any]) -> List[ComplianceFramework]:
        """Determine applicable compliance frameworks"""
        try:
            frameworks = []
            
            if data_classification == DataClassification.PII:
                frameworks.append(ComplianceFramework.GDPR)
                frameworks.append(ComplianceFramework.CCPA)
            
            if data_classification == DataClassification.FINANCIAL:
                frameworks.append(ComplianceFramework.SOX)
                frameworks.append(ComplianceFramework.PCI_DSS)
            
            if data_classification == DataClassification.HEALTH:
                frameworks.append(ComplianceFramework.HIPAA)
            
            # Always include SOC2 for security
            frameworks.append(ComplianceFramework.SOC2)
            
            return frameworks
            
        except Exception as e:
            logger.error(f"❌ Failed to determine compliance frameworks: {e}")
            return [ComplianceFramework.SOC2]
    
    async def _check_events_for_violations(self, events: List[AuditEvent]):
        """Check events for compliance violations"""
        try:
            for event in events:
                # Check for specific violation patterns
                if event.event_type == AuditEventType.DATA_ACCESS:
                    if event.data_classification == DataClassification.PII:
                        # Check if access was authorized
                        if not event.details.get('authorized', False):
                            await self._handle_compliance_violation(
                                self.compliance_rules['gdpr_data_minimization'],
                                f"Unauthorized access to PII: {event.resource_id}"
                            )
                
                elif event.event_type == AuditEventType.DATA_DELETION:
                    if event.data_classification == DataClassification.PII:
                        # Check if deletion was properly logged
                        if not event.details.get('deletion_logged', False):
                            await self._handle_compliance_violation(
                                self.compliance_rules['gdpr_right_to_erasure'],
                                f"PII deletion not properly logged: {event.resource_id}"
                            )
            
        except Exception as e:
            logger.error(f"❌ Failed to check events for violations: {e}")
    
    async def _check_rule_compliance(self, rule: ComplianceRule) -> List[str]:
        """Check compliance for a specific rule"""
        try:
            violations = []
            
            # Check based on rule type
            if rule.rule_id == "gdpr_consent_management":
                # Check if all PII data subjects have consent
                for subject in self.data_subjects.values():
                    if not subject.consent_given:
                        violations.append(f"Data subject {subject.subject_id} lacks consent")
            
            elif rule.rule_id == "gdpr_data_minimization":
                # Check for excessive data collection
                # This would typically involve more complex logic
                pass
            
            elif rule.rule_id == "sox_financial_controls":
                # Check financial data controls
                # This would typically involve checking encryption, access controls, etc.
                pass
            
            return violations
            
        except Exception as e:
            logger.error(f"❌ Failed to check rule compliance: {e}")
            return []
    
    async def _handle_compliance_violation(self, rule: ComplianceRule, violation: str):
        """Handle compliance violation"""
        try:
            violation_data = {
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "framework": rule.framework.value,
                "violation": violation,
                "timestamp": datetime.now(),
                "severity": rule.severity
            }
            
            self.violation_alerts.append(violation_data)
            
            # Log violation
            logger.warning(f"Compliance violation: {rule.name} - {violation}")
            
            # Send alert if critical
            if rule.severity == "critical":
                await self._send_compliance_alert(violation_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to handle compliance violation: {e}")
    
    async def _send_compliance_alert(self, violation_data: Dict[str, Any]):
        """Send compliance alert"""
        try:
            # This would typically send alerts to compliance officers
            logger.critical(f"CRITICAL COMPLIANCE VIOLATION: {violation_data}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send compliance alert: {e}")
    
    async def _update_compliance_metrics(self):
        """Update compliance metrics"""
        try:
            # This would typically update compliance dashboards
            pass
            
        except Exception as e:
            logger.error(f"❌ Failed to update compliance metrics: {e}")
    
    async def _create_compliance_report(self) -> Dict[str, Any]:
        """Create compliance report"""
        try:
            current_date = datetime.now().date()
            
            # Get events for the day
            daily_events = [event for event in self.audit_events 
                          if event.timestamp.date() == current_date]
            
            # Count events by type
            events_by_type = defaultdict(int)
            for event in daily_events:
                events_by_type[event.event_type.value] += 1
            
            # Count events by framework
            events_by_framework = defaultdict(int)
            for event in daily_events:
                for framework in event.compliance_frameworks:
                    events_by_framework[framework.value] += 1
            
            # Count violations
            daily_violations = [violation for violation in self.violation_alerts
                              if violation['timestamp'].date() == current_date]
            
            report = {
                "date": current_date.isoformat(),
                "total_events": len(daily_events),
                "events_by_type": dict(events_by_type),
                "events_by_framework": dict(events_by_framework),
                "violations": len(daily_violations),
                "violations_by_severity": {
                    "low": len([v for v in daily_violations if v['severity'] == 'low']),
                    "medium": len([v for v in daily_violations if v['severity'] == 'medium']),
                    "high": len([v for v in daily_violations if v['severity'] == 'high']),
                    "critical": len([v for v in daily_violations if v['severity'] == 'critical'])
                },
                "data_subjects": len(self.data_subjects),
                "consent_rate": len([s for s in self.data_subjects.values() if s.consent_given]) / 
                              max(len(self.data_subjects), 1)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Failed to create compliance report: {e}")
            return {}
    
    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics"""
        try:
            return {
                "total_rules": len(self.compliance_rules),
                "active_rules": len([r for r in self.compliance_rules.values() if r.enabled]),
                "total_audit_events": len(self.audit_events),
                "data_subjects": len(self.data_subjects),
                "consent_rate": len([s for s in self.data_subjects.values() if s.consent_given]) / 
                              max(len(self.data_subjects), 1),
                "recent_violations": len([v for v in self.violation_alerts 
                                        if v['timestamp'] > datetime.now() - timedelta(days=7)]),
                "compliance_reports": len(self.compliance_reports),
                "frameworks_covered": list(set([r.framework.value for r in self.compliance_rules.values()]))
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get compliance metrics: {e}")
            return {}

# Global compliance manager
compliance_manager = ComplianceManager()
