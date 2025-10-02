"""
SBLOC Aggregator Service (Streamlined)
Handles SBLOC referrals through third-party aggregator platform
"""
import requests
import time
import logging
from typing import Dict, Any
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import SBLOCBank, SBLOCReferral, SBLOCSession, User

logger = logging.getLogger(__name__)


def create_application_session(user: User, bank_ext_id: str, requested_usd: float) -> Dict[str, Any]:
    """Create application session with aggregator"""
    try:
        response = requests.post(
            f"{settings.SBLOC_AGGREGATOR_BASE_URL}/applications/session",
            headers={
                "Authorization": f"Bearer {settings.SBLOC_AGGREGATOR_API_KEY}",
                "Idempotency-Key": f"sbloc-{user.id}-{int(time.time())}"
            },
            json={
                "bankId": bank_ext_id,
                "requestedAmountUsd": requested_usd,
                "applicant": {
                    "name": user.get_full_name() or "",
                    "email": user.email or ""
                },
                "redirectUri": settings.SBLOC_REDIRECT_URI,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()  # {sessionUrl, expiresAt, applicationId}
    except Exception as e:
        logger.error(f"Failed to create application session: {e}")
        raise


def get_application_status(application_id: str) -> Dict[str, Any]:
    """Get application status from aggregator"""
    try:
        response = requests.get(
            f"{settings.SBLOC_AGGREGATOR_BASE_URL}/applications/{application_id}",
            headers={"Authorization": f"Bearer {settings.SBLOC_AGGREGATOR_API_KEY}"},
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get application status: {e}")
        raise


class SBLOCDataProcessor:
    """Process and manage SBLOC referral data"""
    
    def __init__(self):
        self.aggregator_service = SBLOCAggregatorService()
    
    def create_referral(self, user: User, bank_id: str, requested_amount: Decimal, 
                       consent_data: Dict[str, Any]) -> SBLOCReferral:
        """Create a new SBLOC referral"""
        try:
            # Get bank
            bank = SBLOCBank.objects.get(aggregator_bank_id=bank_id, is_active=True)
            
            # Get portfolio data
            portfolio_data = self.aggregator_service._get_portfolio_data(user)
            
            # Create referral
            referral = SBLOCReferral.objects.create(
                user=user,
                bank=bank,
                requested_amount_usd=requested_amount,
                portfolio_value_usd=Decimal(str(portfolio_data["totalValue"])),
                eligible_collateral_usd=Decimal(str(portfolio_data["eligibleCollateral"])),
                estimated_ltv=requested_amount / Decimal(str(portfolio_data["eligibleCollateral"])),
                consent_given=consent_data.get("consent", False),
                data_scope=consent_data.get("dataScope", {}),
                consent_timestamp=timezone.now() if consent_data.get("consent") else None,
                timeline=[{
                    "status": "DRAFT",
                    "timestamp": timezone.now().isoformat(),
                    "note": "Referral created"
                }]
            )
            
            return referral
            
        except Exception as e:
            logger.error(f"Failed to create SBLOC referral: {e}")
            raise
    
    def create_session(self, referral: SBLOCReferral) -> SBLOCSession:
        """Create application session for referral"""
        try:
            if not settings.USE_SBLOC_AGGREGATOR:
                # Mock session for development
                return SBLOCSession.objects.create(
                    referral=referral,
                    session_url="https://mock-sbloc-aggregator.com/application/mock-session",
                    session_token="mock-session-token",
                    expires_at=timezone.now() + timezone.timedelta(hours=1)
                )
            
            # Create real session with aggregator
            session_data = self.aggregator_service.create_application_session(
                user=referral.user,
                bank_id=referral.bank.aggregator_bank_id,
                requested_amount=referral.requested_amount_usd
            )
            
            # Update referral with aggregator app ID
            referral.aggregator_app_id = session_data.get("applicationId", "")
            referral.status = "SUBMITTED"
            referral.timeline.append({
                "status": "SUBMITTED",
                "timestamp": timezone.now().isoformat(),
                "note": "Application submitted to aggregator"
            })
            referral.save()
            
            # Create session
            session = SBLOCSession.objects.create(
                referral=referral,
                session_url=session_data["sessionUrl"],
                session_token=session_data.get("sessionToken", ""),
                expires_at=timezone.datetime.fromisoformat(session_data["expiresAt"].replace('Z', '+00:00'))
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to create SBLOC session: {e}")
            raise
    
    def update_referral_status(self, referral: SBLOCReferral, new_status: str, 
                              note: str = "", source: str = "aggregator") -> None:
        """Update referral status and timeline"""
        try:
            old_status = referral.status
            referral.status = new_status
            referral.timeline.append({
                "status": new_status,
                "timestamp": timezone.now().isoformat(),
                "note": note,
                "source": source,
                "previousStatus": old_status
            })
            referral.save()
            
            logger.info(f"Updated SBLOC referral {referral.id} status: {old_status} → {new_status}")
            
        except Exception as e:
            logger.error(f"Failed to update referral status: {e}")
            raise
    
    def sync_banks_from_aggregator(self) -> int:
        """Sync bank catalog from aggregator"""
        try:
            if not settings.USE_SBLOC_AGGREGATOR:
                # Create mock banks for development
                mock_banks = [
                    {
                        "id": "schwab",
                        "name": "Charles Schwab",
                        "logoUrl": "https://example.com/schwab-logo.png",
                        "minLtv": 0.30,
                        "maxLtv": 0.50,
                        "minLineUsd": 10000,
                        "maxLineUsd": 5000000,
                        "typicalAprMin": 0.0699,
                        "typicalAprMax": 0.1099
                    },
                    {
                        "id": "fidelity",
                        "name": "Fidelity",
                        "logoUrl": "https://example.com/fidelity-logo.png",
                        "minLtv": 0.30,
                        "maxLtv": 0.50,
                        "minLineUsd": 10000,
                        "maxLineUsd": 5000000,
                        "typicalAprMin": 0.0699,
                        "typicalAprMax": 0.1099
                    },
                    {
                        "id": "ibkr",
                        "name": "Interactive Brokers",
                        "logoUrl": "https://example.com/ibkr-logo.png",
                        "minLtv": 0.30,
                        "maxLtv": 0.50,
                        "minLineUsd": 10000,
                        "maxLineUsd": 5000000,
                        "typicalAprMin": 0.0599,
                        "typicalAprMax": 0.0999
                    }
                ]
                
                created_count = 0
                for bank_data in mock_banks:
                    bank, created = SBLOCBank.objects.get_or_create(
                        aggregator_bank_id=bank_data["id"],
                        defaults={
                            "name": bank_data["name"],
                            "logo_url": bank_data["logoUrl"],
                            "min_ltv": Decimal(str(bank_data["minLtv"])),
                            "max_ltv": Decimal(str(bank_data["maxLtv"])),
                            "min_line_usd": Decimal(str(bank_data["minLineUsd"])),
                            "max_line_usd": Decimal(str(bank_data["maxLineUsd"])),
                            "typical_apr_min": Decimal(str(bank_data["typicalAprMin"])),
                            "typical_apr_max": Decimal(str(bank_data["typicalAprMax"])),
                            "priority": created_count
                        }
                    )
                    if created:
                        created_count += 1
                
                return created_count
            
            # Real aggregator integration
            banks_data = self.aggregator_service.get_banks()
            created_count = 0
            
            for bank_data in banks_data:
                bank, created = SBLOCBank.objects.get_or_create(
                    aggregator_bank_id=bank_data["id"],
                    defaults={
                        "name": bank_data["name"],
                        "logo_url": bank_data.get("logoUrl", ""),
                        "min_ltv": Decimal(str(bank_data.get("minLtv", 0.30))),
                        "max_ltv": Decimal(str(bank_data.get("maxLtv", 0.50))),
                        "min_line_usd": Decimal(str(bank_data.get("minLineUsd", 10000))),
                        "max_line_usd": Decimal(str(bank_data.get("maxLineUsd", 5000000))),
                        "typical_apr_min": Decimal(str(bank_data.get("typicalAprMin", 0.0699))),
                        "typical_apr_max": Decimal(str(bank_data.get("typicalAprMax", 0.1099))),
                        "is_active": bank_data.get("isActive", True),
                        "priority": bank_data.get("priority", 0)
                    }
                )
                if created:
                    created_count += 1
            
            return created_count
            
        except Exception as e:
            logger.error(f"Failed to sync banks from aggregator: {e}")
            return 0
