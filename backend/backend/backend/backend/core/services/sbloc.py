# core/services/sbloc.py
from dataclasses import dataclass
from typing import Optional, List
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import SblocBank, SblocReferral, SblocSession
from .sbloc_aggregators import MockSblocAggregator, AggregatorSession

STATUS_FLOW: List[str] = [
    "CREATED",
    "SUBMITTED",
    "IN_REVIEW",
    "CONDITIONAL_APPROVAL",
    "APPROVED",
    "FUNDED",
]

@dataclass
class SessionResult:
    id: str
    application_url: str

class SblocService:
    def __init__(self):
        # For now we always use the mock in dev
        self.aggregator = MockSblocAggregator() if settings.USE_SBLOC_MOCK else MockSblocAggregator()

    @transaction.atomic
    def create_session(self, user, bank_id: str, amount_usd: int) -> SessionResult:
        bank = SblocBank.objects.get(id=bank_id, is_active=True)
        # Create referral first
        ref = SblocReferral.objects.create(
            user_id=getattr(user, "id", None),
            bank=bank,
            amount_usd=amount_usd,
            status="SUBMITTED",  # first visible state for the referral
        )

        # Call (mock) aggregator
        agg: AggregatorSession = self.aggregator.create_session(
            bank_name=bank.name, amount_usd=amount_usd, user_id=getattr(user, "id", None)
        )

        # Store session
        session = SblocSession.objects.create(
            referral=ref,
            application_url=agg.application_url,
            external_session_id=agg.external_session_id,
            status="CREATED",
        )
        return SessionResult(id=str(session.id), application_url=session.application_url)

    @staticmethod
    def advance_status(session: SblocSession) -> None:
        """Move a session forward one step in STATUS_FLOW, update referral too."""
        try:
            idx = STATUS_FLOW.index(session.status)
        except ValueError:
            # unknown status, set to CREATED
            session.status = "CREATED"
            session.save(update_fields=["status"])
            session.referral.status = "SUBMITTED"
            session.referral.save(update_fields=["status"])
            return

        if idx < len(STATUS_FLOW) - 1:
            new_status = STATUS_FLOW[idx + 1]
            session.status = new_status
            session.save(update_fields=["status"])
            session.referral.status = new_status
            session.referral.save(update_fields=["status"])
