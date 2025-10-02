"""
SBLOC GraphQL Schema
GraphQL types and resolvers for SBLOC aggregator integration
"""
import graphene
from graphene_django import DjangoObjectType
from decimal import Decimal
from django.utils import timezone
from .models import SBLOCBank, SBLOCReferral, SBLOCSession
from .sbloc_service import SBLOCDataProcessor

# GraphQL Types
class SBLOCBankType(DjangoObjectType):
    class Meta:
        model = SBLOCBank
        fields = "__all__"
    
    # Frontend-compatible field names
    logoUrl = graphene.String()
    minApr = graphene.Float()
    maxApr = graphene.Float()
    minLtv = graphene.Float()
    maxLtv = graphene.Float()
    minLoanUsd = graphene.Int()
    regions = graphene.List(graphene.String)
    
    # Legacy field names
    min_ltv = graphene.Float()
    max_ltv = graphene.Float()
    min_line_usd = graphene.Float()
    max_line_usd = graphene.Float()
    typical_apr_min = graphene.Float()
    typical_apr_max = graphene.Float()
    
    def resolve_logoUrl(self, info):
        return getattr(self, 'logo_url', None)
    
    def resolve_minApr(self, info):
        return float(self.typical_apr_min) if hasattr(self, 'typical_apr_min') else None
    
    def resolve_maxApr(self, info):
        return float(self.typical_apr_max) if hasattr(self, 'typical_apr_max') else None
    
    def resolve_minLtv(self, info):
        return float(self.min_ltv) if hasattr(self, 'min_ltv') else None
    
    def resolve_maxLtv(self, info):
        return float(self.max_ltv) if hasattr(self, 'max_ltv') else None
    
    def resolve_minLoanUsd(self, info):
        return int(self.min_line_usd) if hasattr(self, 'min_line_usd') else None
    
    def resolve_regions(self, info):
        # Return default regions for now
        return ['US']
    
    def resolve_min_ltv(self, info):
        return float(self.min_ltv) if hasattr(self, 'min_ltv') else None
    
    def resolve_max_ltv(self, info):
        return float(self.max_ltv) if hasattr(self, 'max_ltv') else None
    
    def resolve_min_line_usd(self, info):
        return float(self.min_line_usd) if hasattr(self, 'min_line_usd') else None
    
    def resolve_max_line_usd(self, info):
        return float(self.max_line_usd) if hasattr(self, 'max_line_usd') else None
    
    def resolve_typical_apr_min(self, info):
        return float(self.typical_apr_min) if hasattr(self, 'typical_apr_min') else None
    
    def resolve_typical_apr_max(self, info):
        return float(self.typical_apr_max) if hasattr(self, 'typical_apr_max') else None


class SBLOCReferralType(DjangoObjectType):
    class Meta:
        model = SBLOCReferral
        fields = "__all__"
    
    requested_amount_usd = graphene.Float()
    portfolio_value_usd = graphene.Float()
    eligible_collateral_usd = graphene.Float()
    estimated_ltv = graphene.Float()
    
    def resolve_requested_amount_usd(self, info):
        return float(self.requested_amount_usd)
    
    def resolve_portfolio_value_usd(self, info):
        return float(self.portfolio_value_usd)
    
    def resolve_eligible_collateral_usd(self, info):
        return float(self.eligible_collateral_usd)
    
    def resolve_estimated_ltv(self, info):
        return float(self.estimated_ltv)


class SBLOCSessionType(DjangoObjectType):
    class Meta:
        model = SBLOCSession
        fields = "__all__"
    
    sessionId = graphene.String()
    applicationUrl = graphene.String()
    lastUpdatedIso = graphene.String()
    lenderName = graphene.String()
    requestedAmountUsd = graphene.Int()
    message = graphene.String()
    is_expired = graphene.Boolean()
    
    def resolve_sessionId(self, info):
        return str(self.id)
    
    def resolve_applicationUrl(self, info):
        return self.application_url
    
    def resolve_lastUpdatedIso(self, info):
        return self.created_at.isoformat()
    
    def resolve_lenderName(self, info):
        return self.referral.bank.name if self.referral and self.referral.bank else None
    
    def resolve_requestedAmountUsd(self, info):
        return self.referral.requested_amount_usd if self.referral else None
    
    def resolve_message(self, info):
        # Return a helpful message based on status
        status_messages = {
            'CREATED': 'Application created successfully',
            'APPLICATION_STARTED': 'Application in progress',
            'KYC_PENDING': 'KYC verification pending',
            'UNDER_REVIEW': 'Application under review',
            'APPROVED': 'Application approved',
            'DECLINED': 'Application declined',
            'CANCELLED': 'Application cancelled',
            'EXPIRED': 'Application expired'
        }
        return status_messages.get(self.status, 'Status unknown')
    
    def resolve_is_expired(self, info):
        return self.is_expired


class SblocSessionPayloadType(graphene.ObjectType):
    session_url = graphene.String()
    expires_at = graphene.DateTime()
    referral = graphene.Field(SBLOCReferralType)


class CreateSblocSessionResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    session_payload = graphene.Field(SblocSessionPayloadType)


class CreateSblocReferralResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    referral = graphene.Field(SBLOCReferralType)


# Queries
class SBLOCQuery(graphene.ObjectType):
    sblocBanks = graphene.List(SBLOCBankType, description="Get available SBLOC banks")
    sblocSession = graphene.Field(SBLOCSessionType, sessionId=graphene.ID(required=True), description="Get SBLOC session by ID")
    sbloc_referral = graphene.Field(SBLOCReferralType, id=graphene.ID(required=True), description="Get SBLOC referral by ID")
    sbloc_referrals = graphene.List(SBLOCReferralType, description="Get user's SBLOC referrals")
    
    def resolve_sblocBanks(self, info):
        """Get active SBLOC banks"""
        return SBLOCBank.objects.filter(is_active=True).order_by('-priority', 'name')
    
    def resolve_sblocSession(self, info, sessionId):
        """Get SBLOC session by ID"""
        try:
            return SBLOCSession.objects.get(id=sessionId)
        except SBLOCSession.DoesNotExist:
            return None
    
    def resolve_sbloc_referral(self, info, id):
        """Get specific SBLOC referral"""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return None
        
        try:
            return SBLOCReferral.objects.get(id=id, user=user)
        except SBLOCReferral.DoesNotExist:
            return None
    
    def resolve_sbloc_referrals(self, info):
        """Get user's SBLOC referrals"""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return []
        
        return SBLOCReferral.objects.filter(user=user).order_by('-created_at')


# Mutations
class CreateSblocSession(graphene.Mutation):
    class Arguments:
        bankId = graphene.ID(required=True, description="Bank ID")
        amountUsd = graphene.Int(required=True, description="Requested amount in USD")
    
    success = graphene.Boolean()
    applicationUrl = graphene.String()
    sessionId = graphene.String()
    error = graphene.String()
    
    def mutate(self, info, bankId, amountUsd):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return CreateSblocSession(
                success=False,
                error="Authentication required"
            )
        
        try:
            from .sbloc_service import create_application_session
            
            # Get bank
            bank = SBLOCBank.objects.get(id=bankId)
            
            # Create referral
            referral = SBLOCReferral.objects.create(
                user=user,
                bank=bank,
                requested_amount_usd=amountUsd,
                user_consent_text="User consented to share portfolio summary with selected bank.",
                user_consent_ts=timezone.now(),
            )
            
            # Create session with aggregator
            if settings.USE_SBLOC_AGGREGATOR:
                data = create_application_session(user, bank.ext_id, amountUsd)
                referral.aggregator_app_id = data["applicationId"]
                referral.save(update_fields=["aggregator_app_id"])
                
                session = SBLOCSession.objects.create(
                    referral=referral,
                    application_url=data["sessionUrl"],
                    external_session_id=data["applicationId"]
                )
            else:
                # Mock session for development
                session = SBLOCSession.objects.create(
                    referral=referral,
                    application_url="https://mock-sbloc-aggregator.com/application/mock-session",
                    external_session_id=f"mock-session-{referral.id}"
                )
            
            return CreateSblocSession(
                success=True,
                applicationUrl=session.application_url,
                sessionId=str(session.id),
                error=None
            )
            
        except Exception as e:
            logger.error(f"Failed to create SBLOC session: {e}")
            return CreateSblocSession(
                success=False,
                error=f"Failed to create SBLOC session: {str(e)}"
            )


class CreateSblocReferral(graphene.Mutation):
    class Arguments:
        bank_id = graphene.ID(required=True, description="Bank ID")
        requested_amount_usd = graphene.Float(required=True, description="Requested amount in USD")
        consent_data = graphene.JSONString(required=True, description="User consent and data sharing preferences")
    
    Output = CreateSblocReferralResultType
    
    def mutate(self, info, bank_id, requested_amount_usd, consent_data):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return CreateSblocReferralResultType(
                success=False,
                message="Authentication required"
            )
        
        try:
            processor = SBLOCDataProcessor()
            
            # Create referral
            referral = processor.create_referral(
                user=user,
                bank_id=bank_id,
                requested_amount=Decimal(str(requested_amount_usd)),
                consent_data=consent_data
            )
            
            return CreateSblocReferralResultType(
                success=True,
                message="SBLOC referral created successfully",
                referral=referral
            )
            
        except Exception as e:
            return CreateSblocReferralResultType(
                success=False,
                message=f"Failed to create SBLOC referral: {str(e)}"
            )


class SyncSblocBanks(graphene.Mutation):
    class Arguments:
        pass
    
    success = graphene.Boolean()
    message = graphene.String()
    banks_created = graphene.Int()
    
    def mutate(self, info):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return SyncSblocBanks(
                success=False,
                message="Authentication required",
                banks_created=0
            )
        
        # Only allow admin users to sync banks
        if not user.is_staff:
            return SyncSblocBanks(
                success=False,
                message="Admin access required",
                banks_created=0
            )
        
        try:
            processor = SBLOCDataProcessor()
            banks_created = processor.sync_banks_from_aggregator()
            
            return SyncSblocBanks(
                success=True,
                message=f"Successfully synced {banks_created} banks",
                banks_created=banks_created
            )
            
        except Exception as e:
            return SyncSblocBanks(
                success=False,
                message=f"Failed to sync banks: {str(e)}",
                banks_created=0
            )


class SBLOCMutation(graphene.ObjectType):
    createSblocSession = CreateSblocSession.Field(description="Create SBLOC application session")
    create_sbloc_referral = CreateSblocReferral.Field(description="Create SBLOC referral")
    sync_sbloc_banks = SyncSblocBanks.Field(description="Sync banks from aggregator (admin only)")
