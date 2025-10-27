"""
Compliance and Trust Engine for RichesReach Education System
Ensures regulatory compliance, content verification, and user safety
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import logging

class ComplianceLevel(Enum):
    """Compliance levels for educational content"""
    BASIC = "basic"           # General educational content
    INTERMEDIATE = "intermediate"  # Trading concepts with disclaimers
    ADVANCED = "advanced"      # Complex strategies with full disclaimers
    PROFESSIONAL = "professional"  # Professional-grade content

class ContentType(Enum):
    """Types of educational content"""
    LESSON = "lesson"
    QUIZ = "quiz"
    SIMULATION = "simulation"
    VIDEO = "video"
    ARTICLE = "article"
    WEBINAR = "webinar"

@dataclass
class ComplianceMetadata:
    """Metadata for compliance tracking"""
    content_id: str
    content_type: ContentType
    compliance_level: ComplianceLevel
    created_at: datetime
    last_reviewed: datetime
    reviewer_id: Optional[str]
    version: str
    source_citations: List[str]
    disclaimer_text: str
    risk_warnings: List[str]
    target_audience: str
    prerequisites: List[str]
    regulatory_approval: bool
    content_hash: str

@dataclass
class UserComplianceProfile:
    """User's compliance and risk profile"""
    user_id: str
    risk_tolerance: str  # "conservative", "moderate", "aggressive"
    experience_level: str  # "beginner", "intermediate", "advanced", "professional"
    jurisdiction: str  # Country/region for regulatory compliance
    age_verified: bool
    accredited_investor: bool
    opt_in_live_trading: bool
    compliance_agreements: Dict[str, datetime]
    last_compliance_check: datetime
    restricted_content_access: List[str]

class ComplianceEngine:
    """Main compliance and trust engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.content_registry = {}
        self.user_profiles = {}
        self.disclaimer_templates = self._load_disclaimer_templates()
        self.risk_warnings = self._load_risk_warnings()
        
    def _load_disclaimer_templates(self) -> Dict[str, str]:
        """Load disclaimer templates for different content types"""
        return {
            "basic": "This educational content is for informational purposes only and does not constitute financial advice.",
            "intermediate": "This content discusses trading strategies for educational purposes. Past performance does not guarantee future results. Trading involves risk of loss.",
            "advanced": "Advanced trading strategies carry significant risk. This content is for educational purposes only. Consult a financial advisor before making investment decisions.",
            "professional": "Professional-grade content requires appropriate qualifications and risk management. This material is for educational purposes only and does not constitute investment advice."
        }
    
    def _load_risk_warnings(self) -> Dict[str, List[str]]:
        """Load risk warnings for different content types"""
        return {
            "options": [
                "Options trading involves significant risk and may not be suitable for all investors",
                "Options can expire worthless, resulting in total loss of investment",
                "Complex options strategies carry additional risks"
            ],
            "hft": [
                "High-frequency trading requires sophisticated technology and significant capital",
                "HFT strategies involve substantial risk and may not be suitable for retail investors",
                "Market conditions can change rapidly, affecting HFT performance"
            ],
            "leverage": [
                "Leveraged trading amplifies both gains and losses",
                "Margin trading can result in losses exceeding initial investment",
                "Leverage increases risk of margin calls"
            ],
            "crypto": [
                "Cryptocurrency trading is highly speculative and volatile",
                "Regulatory changes may affect cryptocurrency values",
                "Cryptocurrency exchanges may be subject to security risks"
            ]
        }
    
    def generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash for content integrity verification"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def validate_content_compliance(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content against compliance requirements"""
        content_id = content.get("id", "unknown")
        content_type = ContentType(content.get("type", "lesson"))
        
        # Determine compliance level based on content complexity
        compliance_level = self._determine_compliance_level(content)
        
        # Generate compliance metadata
        metadata = ComplianceMetadata(
            content_id=content_id,
            content_type=content_type,
            compliance_level=compliance_level,
            created_at=datetime.now(),
            last_reviewed=datetime.now(),
            reviewer_id="system_auto",
            version="1.0",
            source_citations=content.get("sources", []),
            disclaimer_text=self.disclaimer_templates[compliance_level.value],
            risk_warnings=self._get_relevant_risk_warnings(content),
            target_audience=content.get("target_audience", "general"),
            prerequisites=content.get("prerequisites", []),
            regulatory_approval=self._check_regulatory_approval(content),
            content_hash=self.generate_content_hash(str(content))
        )
        
        # Store in registry
        self.content_registry[content_id] = metadata
        
        return {
            "compliant": True,
            "compliance_level": compliance_level.value,
            "disclaimer": metadata.disclaimer_text,
            "risk_warnings": metadata.risk_warnings,
            "regulatory_approval": metadata.regulatory_approval,
            "content_hash": metadata.content_hash,
            "review_required": compliance_level in [ComplianceLevel.ADVANCED, ComplianceLevel.PROFESSIONAL]
        }
    
    def _determine_compliance_level(self, content: Dict[str, Any]) -> ComplianceLevel:
        """Determine appropriate compliance level based on content"""
        topic = content.get("topic", "").lower()
        difficulty = content.get("difficulty", "beginner").lower()
        
        # Advanced topics require higher compliance
        if any(term in topic for term in ["hft", "leverage", "margin", "derivatives", "crypto"]):
            return ComplianceLevel.ADVANCED
        
        if difficulty in ["advanced", "expert"] or "professional" in topic:
            return ComplianceLevel.PROFESSIONAL
        
        if difficulty == "intermediate":
            return ComplianceLevel.INTERMEDIATE
        
        return ComplianceLevel.BASIC
    
    def _get_relevant_risk_warnings(self, content: Dict[str, Any]) -> List[str]:
        """Get relevant risk warnings for content"""
        topic = content.get("topic", "").lower()
        warnings = []
        
        # Add topic-specific warnings
        for warning_type, warning_list in self.risk_warnings.items():
            if warning_type in topic:
                warnings.extend(warning_list)
        
        # Add general trading warnings
        warnings.extend([
            "All trading involves risk of financial loss",
            "Never invest more than you can afford to lose",
            "Past performance does not guarantee future results"
        ])
        
        return list(set(warnings))  # Remove duplicates
    
    def _check_regulatory_approval(self, content: Dict[str, Any]) -> bool:
        """Check if content requires regulatory approval"""
        compliance_level = self._determine_compliance_level(content)
        return compliance_level in [ComplianceLevel.ADVANCED, ComplianceLevel.PROFESSIONAL]
    
    def create_user_compliance_profile(self, user_id: str, user_data: Dict[str, Any]) -> UserComplianceProfile:
        """Create compliance profile for new user"""
        profile = UserComplianceProfile(
            user_id=user_id,
            risk_tolerance=user_data.get("risk_tolerance", "moderate"),
            experience_level=user_data.get("experience_level", "beginner"),
            jurisdiction=user_data.get("jurisdiction", "US"),
            age_verified=user_data.get("age_verified", False),
            accredited_investor=user_data.get("accredited_investor", False),
            opt_in_live_trading=user_data.get("opt_in_live_trading", False),
            compliance_agreements={},
            last_compliance_check=datetime.now(),
            restricted_content_access=[]
        )
        
        self.user_profiles[user_id] = profile
        return profile
    
    def check_content_access(self, user_id: str, content_id: str) -> Dict[str, Any]:
        """Check if user can access specific content based on compliance"""
        if user_id not in self.user_profiles:
            return {"access_granted": False, "reason": "User profile not found"}
        
        user_profile = self.user_profiles[user_id]
        content_metadata = self.content_registry.get(content_id)
        
        if not content_metadata:
            return {"access_granted": False, "reason": "Content not found in registry"}
        
        # Check age verification for advanced content
        if content_metadata.compliance_level in [ComplianceLevel.ADVANCED, ComplianceLevel.PROFESSIONAL]:
            if not user_profile.age_verified:
                return {"access_granted": False, "reason": "Age verification required for advanced content"}
        
        # Check accredited investor status for professional content
        if content_metadata.compliance_level == ComplianceLevel.PROFESSIONAL:
            if not user_profile.accredited_investor:
                return {"access_granted": False, "reason": "Accredited investor status required"}
        
        # Check jurisdiction restrictions
        if content_metadata.compliance_level == ComplianceLevel.ADVANCED:
            restricted_jurisdictions = ["EU", "UK"]  # Example restrictions
            if user_profile.jurisdiction in restricted_jurisdictions:
                return {"access_granted": False, "reason": "Content restricted in your jurisdiction"}
        
        return {
            "access_granted": True,
            "compliance_level": content_metadata.compliance_level.value,
            "disclaimer": content_metadata.disclaimer_text,
            "risk_warnings": content_metadata.risk_warnings,
            "requires_acknowledgment": True
        }
    
    def log_content_interaction(self, user_id: str, content_id: str, action: str) -> None:
        """Log user interactions with content for compliance tracking"""
        timestamp = datetime.now()
        log_entry = {
            "user_id": user_id,
            "content_id": content_id,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "compliance_level": self.content_registry.get(content_id, {}).compliance_level.value if content_id in self.content_registry else "unknown"
        }
        
        self.logger.info(f"Content interaction logged: {json.dumps(log_entry)}")
    
    def generate_compliance_report(self, user_id: str) -> Dict[str, Any]:
        """Generate compliance report for user"""
        if user_id not in self.user_profiles:
            return {"error": "User profile not found"}
        
        user_profile = self.user_profiles[user_id]
        
        return {
            "user_id": user_id,
            "compliance_status": "compliant",
            "risk_tolerance": user_profile.risk_tolerance,
            "experience_level": user_profile.experience_level,
            "jurisdiction": user_profile.jurisdiction,
            "age_verified": user_profile.age_verified,
            "accredited_investor": user_profile.accredited_investor,
            "opt_in_live_trading": user_profile.opt_in_live_trading,
            "last_compliance_check": user_profile.last_compliance_check.isoformat(),
            "agreements_signed": list(user_profile.compliance_agreements.keys()),
            "restricted_content_access": user_profile.restricted_content_access,
            "recommended_content_level": self._get_recommended_content_level(user_profile)
        }
    
    def _get_recommended_content_level(self, user_profile: UserComplianceProfile) -> str:
        """Get recommended content level based on user profile"""
        if user_profile.experience_level == "professional" and user_profile.accredited_investor:
            return "professional"
        elif user_profile.experience_level == "advanced":
            return "advanced"
        elif user_profile.experience_level == "intermediate":
            return "intermediate"
        else:
            return "basic"
    
    def audit_content_integrity(self) -> Dict[str, Any]:
        """Audit all content for integrity and compliance"""
        audit_results = {
            "total_content": len(self.content_registry),
            "compliant_content": 0,
            "non_compliant_content": 0,
            "review_required": 0,
            "issues": []
        }
        
        for content_id, metadata in self.content_registry.items():
            if metadata.regulatory_approval:
                audit_results["compliant_content"] += 1
            else:
                audit_results["non_compliant_content"] += 1
            
            if metadata.compliance_level in [ComplianceLevel.ADVANCED, ComplianceLevel.PROFESSIONAL]:
                audit_results["review_required"] += 1
            
            # Check if content needs re-review (older than 90 days)
            if (datetime.now() - metadata.last_reviewed).days > 90:
                audit_results["issues"].append({
                    "content_id": content_id,
                    "issue": "Content needs re-review",
                    "days_since_review": (datetime.now() - metadata.last_reviewed).days
                })
        
        return audit_results
