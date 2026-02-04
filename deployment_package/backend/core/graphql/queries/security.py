"""
Security Fortress and Zero Trust GraphQL queries.
Exposes securityEvents, biometricSettings, complianceStatuses, securityScore,
deviceTrusts, accessPolicies, zeroTrustSummary. Composed into ExtendedQuery.
"""
import logging
from datetime import timedelta

import graphene
from django.utils import timezone

logger = logging.getLogger(__name__)


class SecurityQuery(graphene.ObjectType):
    """Security Fortress and Zero Trust root fields."""

    security_events = graphene.List(
        "core.types.SecurityEventType",
        limit=graphene.Int(required=False),
        resolved=graphene.Boolean(required=False),
        name="securityEvents",
    )
    biometric_settings = graphene.Field(
        "core.types.BiometricSettingsType",
        name="biometricSettings",
    )
    compliance_statuses = graphene.List(
        "core.types.ComplianceStatusType",
        name="complianceStatuses",
    )
    security_score = graphene.Field(
        "core.types.SecurityScoreType",
        name="securityScore",
    )
    device_trusts = graphene.List(
        "core.types.DeviceTrustType",
        name="deviceTrusts",
    )
    access_policies = graphene.List(
        "core.types.AccessPolicyType",
        name="accessPolicies",
    )
    zero_trust_summary = graphene.Field(
        "core.types.ZeroTrustSummaryType",
        name="zeroTrustSummary",
    )

    def resolve_security_events(self, info, limit=None, resolved=None):
        """Get security events for current user."""
        from core.graphql_utils import get_user_from_context
        from core.models import SecurityEvent

        user = get_user_from_context(info.context)
        if not user or getattr(user, "is_anonymous", True):
            return []
        queryset = SecurityEvent.objects.filter(user=user)
        if resolved is not None:
            queryset = queryset.filter(resolved=resolved)
        queryset = queryset.order_by("-created_at")
        if limit:
            queryset = queryset[:limit]
        return queryset

    def resolve_biometric_settings(self, info):
        """Get biometric settings for current user."""
        from core.graphql_utils import get_user_from_context
        from core.models import BiometricSettings

        user = get_user_from_context(info.context)
        if not user or getattr(user, "is_anonymous", True):
            return None
        settings, _ = BiometricSettings.objects.get_or_create(user=user)
        return settings

    def resolve_compliance_statuses(self, info):
        """Get all compliance statuses."""
        from core.models import ComplianceStatus

        return ComplianceStatus.objects.all()

    def resolve_security_score(self, info):
        """Get latest security score for current user."""
        from core.graphql_utils import get_user_from_context
        from core.models import SecurityScore
        from core.security_service import SecurityService

        user = get_user_from_context(info.context)
        if not user or getattr(user, "is_anonymous", True):
            return None
        service = SecurityService()
        score_data = service.calculate_security_score(user)
        security_score = SecurityScore.objects.create(
            user=user,
            score=score_data["score"],
            factors=score_data["factors"],
        )
        return security_score

    def resolve_device_trusts(self, info):
        """Get trusted devices for current user."""
        from core.graphql_utils import get_user_from_context
        from core.models import DeviceTrust

        user = get_user_from_context(info.context)
        if not user or getattr(user, "is_anonymous", True):
            return []
        return DeviceTrust.objects.filter(user=user).order_by(
            "-trust_score", "-last_verified"
        )

    def resolve_access_policies(self, info):
        """Get access policies for current user."""
        from core.graphql_utils import get_user_from_context
        from core.models import AccessPolicy

        user = get_user_from_context(info.context)
        if not user or getattr(user, "is_anonymous", True):
            return []
        return AccessPolicy.objects.filter(user=user)

    def resolve_zero_trust_summary(self, info):
        """Get Zero Trust summary for current user."""
        from core.graphql_utils import get_user_from_context
        from core.models import SecurityEvent
        from core.types import ZeroTrustSummaryType
        from core.zero_trust_service import zero_trust_service

        user = get_user_from_context(info.context)
        if not user or getattr(user, "is_anonymous", True):
            return None
        summary = zero_trust_service.get_trust_summary(user.id)
        avg_score = summary["average_trust_score"]
        if avg_score >= 80:
            risk_level = "low"
        elif avg_score >= 60:
            risk_level = "medium"
        elif avg_score >= 40:
            risk_level = "high"
        else:
            risk_level = "critical"
        recent_events = SecurityEvent.objects.filter(
            user_id=user.id,
            created_at__gte=timezone.now() - timedelta(days=7),
            resolved=False,
            threat_level__in=["high", "critical"],
        ).count()
        requires_mfa = avg_score < 70 or recent_events > 0
        last_verification = summary.get("last_verification")
        return ZeroTrustSummaryType(
            userId=str(user.id),
            devices=summary["devices"],
            averageTrustScore=summary["average_trust_score"],
            lastVerification=(
                last_verification.isoformat() if last_verification else None
            ),
            requiresMfa=requires_mfa,
            riskLevel=risk_level,
        )
