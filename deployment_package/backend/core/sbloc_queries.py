"""
GraphQL Queries for SBLOC (Securities-Based Line of Credit) Operations
"""
import graphene
import logging
from typing import List, Optional
from django.utils import timezone
from .sbloc_types import SBLOCBankType, SBLOCOfferType
from .sbloc_models import SBLOCBank, SBLOCSession

logger = logging.getLogger(__name__)


class SBLOCQueries(graphene.ObjectType):
    """GraphQL queries for SBLOC operations"""
    
    sbloc_banks = graphene.List(
        SBLOCBankType,
        description="Get list of available SBLOC banks"
    )
    
    # Alias for mobile app compatibility (camelCase)
    sblocBanks = graphene.List(
        SBLOCBankType,
        description="Get list of available SBLOC banks (alias)"
    )
    
    sbloc_bank = graphene.Field(
        SBLOCBankType,
        id=graphene.ID(required=True),
        description="Get a specific SBLOC bank by ID"
    )
    
    sbloc_session = graphene.Field(
        'core.sbloc_types.SBLOCSessionType',
        id=graphene.ID(required=True),
        description="Get SBLOC session by ID"
    )
    
    sbloc_offer = graphene.Field(
        SBLOCOfferType,
        description="Get SBLOC offer/quote for user's portfolio"
    )
    # CamelCase alias for frontend compatibility
    sblocOffer = graphene.Field(
        SBLOCOfferType,
        description="Get SBLOC offer/quote for user's portfolio (camelCase alias)"
    )
    
    def resolve_sbloc_banks(self, info):
        """Get all active SBLOC banks"""
        try:
            # Safely get user from context
            user = getattr(info.context, 'user', None)
            logger.info(f"resolve_sbloc_banks: user={user}, has_authenticated={hasattr(user, 'is_authenticated') if user else False}, is_authenticated={user.is_authenticated if user and hasattr(user, 'is_authenticated') else False}")
            
            # Return active banks, ordered by priority
            # Note: For testing, we return banks even without authentication
            # In production, you might want to require authentication
            banks = SBLOCBank.objects.filter(is_active=True).order_by('priority', 'name')
            bank_count = banks.count()
            logger.info(f"🔵 resolve_sbloc_banks: Found {bank_count} banks in database")
            
            # Convert to list - DjangoObjectType can serialize both queryset and list
            # IMPORTANT: Return the queryset directly - DjangoObjectType handles it better
            # Converting to list can sometimes cause serialization issues
            logger.info(f"🔵 resolve_sbloc_banks: Returning queryset directly (DjangoObjectType will handle serialization)")
            logger.info(f"🔵 resolve_sbloc_banks: Queryset count: {bank_count}")
            
            # Return queryset directly - DjangoObjectType is designed to handle querysets
            return banks
        except Exception as e:
            logger.error(f"Error in resolve_sbloc_banks: {e}", exc_info=True)
            # Return empty list on any error - don't break the request
            return []
    
    def resolve_sblocBanks(self, info):
        """Get all active SBLOC banks (alias for mobile app) - camelCase version"""
        logger.info("🔵🔵🔵 resolve_sblocBanks CALLED (camelCase alias)")
        try:
            # Safely get user from context
            user = getattr(info.context, 'user', None)
            logger.info(f"🔵 resolve_sblocBanks: user={user}")
            
            # Return active banks, ordered by priority
            banks = SBLOCBank.objects.filter(is_active=True).order_by('priority', 'name')
            bank_count = banks.count()
            logger.info(f"🔵 resolve_sblocBanks: Found {bank_count} banks in database")
            
            # Return queryset directly - DjangoObjectType handles serialization
            logger.info(f"🔵 resolve_sblocBanks: Returning queryset with {bank_count} banks")
            return banks
        except Exception as e:
            logger.error(f"❌ Error in resolve_sblocBanks: {e}", exc_info=True)
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []
    
    def resolve_sbloc_bank(self, info, id):
        """Get a specific SBLOC bank"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            return SBLOCBank.objects.get(id=id, is_active=True)
        except SBLOCBank.DoesNotExist:
            return None
    
    def resolve_sbloc_offer(self, info):
        """Get SBLOC offer/quote for user's portfolio"""
        user = getattr(info.context, 'user', None)
        if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            # Return default offer for unauthenticated users
            return SBLOCOfferType(
                ltv=0.5,
                apr=0.085,
                minDraw=1000,
                maxDrawMultiplier=0.95,
                disclosures=[
                    "Securities-based lines of credit involve risks, including the potential loss of collateral.",
                    "Interest rates may vary and are subject to change.",
                    "Not all securities are eligible for SBLOC.",
                    "This is not an offer of credit. Terms subject to lender approval."
                ],
                eligibleEquity=50000.0,
                updatedAt=timezone.now().isoformat()
            )
        
        try:
            # Calculate eligible equity from user's portfolio
            from .models import Portfolio
            from .premium_analytics_service import PremiumAnalyticsService
            
            # Try to get portfolio value from PremiumAnalyticsService
            eligible_equity = 50000.0  # Default fallback
            try:
                service = PremiumAnalyticsService()
                metrics = service.get_portfolio_metrics(user.id)
                if metrics and isinstance(metrics, dict):
                    eligible_equity = float(metrics.get('total_value', 50000))
                elif hasattr(metrics, 'total_value'):
                    eligible_equity = float(metrics.total_value)
            except Exception as e:
                logger.warning(f"Could not fetch portfolio value for SBLOC offer: {e}")
                # Fallback: calculate from Portfolio model
                try:
                    portfolios = Portfolio.objects.filter(user=user).select_related('stock')
                    if portfolios.exists():
                        total_value = sum(
                            float(portfolio.shares * (portfolio.stock.current_price if portfolio.stock and hasattr(portfolio.stock, 'current_price') and portfolio.stock.current_price else 0))
                            for portfolio in portfolios
                        )
                        eligible_equity = max(total_value, 10000.0)  # Minimum $10k
                except Exception as e2:
                    logger.warning(f"Could not calculate portfolio value: {e2}")
            
            # Get best available SBLOC terms (from active banks)
            banks = SBLOCBank.objects.filter(is_active=True).order_by('min_apr', 'priority')
            if banks.exists():
                best_bank = banks.first()
                ltv = float(best_bank.max_ltv) if best_bank.max_ltv else 0.5
                apr = float(best_bank.min_apr) if best_bank.min_apr else 0.085
            else:
                # Default values if no banks configured
                ltv = 0.5
                apr = 0.085
            
            return SBLOCOfferType(
                ltv=ltv,
                apr=apr,
                minDraw=1000,
                maxDrawMultiplier=0.95,
                disclosures=[
                    "Securities-based lines of credit involve risks, including the potential loss of collateral.",
                    "Interest rates may vary and are subject to change.",
                    "Not all securities are eligible for SBLOC.",
                    "This is not an offer of credit. Terms subject to lender approval."
                ],
                eligibleEquity=eligible_equity,
                updatedAt=timezone.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error resolving SBLOC offer: {e}", exc_info=True)
            # Return default offer on error
            return SBLOCOfferType(
                ltv=0.5,
                apr=0.085,
                minDraw=1000,
                maxDrawMultiplier=0.95,
                disclosures=[],
                eligibleEquity=50000.0,
                updatedAt=timezone.now().isoformat()
            )
    
    def resolve_sblocOffer(self, info):
        """CamelCase alias for sbloc_offer"""
        user = getattr(info.context, 'user', None)
        if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            # Return default offer for unauthenticated users
            return SBLOCOfferType(
                ltv=0.5,
                apr=0.085,
                minDraw=1000,
                maxDrawMultiplier=0.95,
                disclosures=[
                    "Securities-based lines of credit involve risks, including the potential loss of collateral.",
                    "Interest rates may vary and are subject to change.",
                    "Not all securities are eligible for SBLOC.",
                    "This is not an offer of credit. Terms subject to lender approval."
                ],
                eligibleEquity=50000.0,
                updatedAt=timezone.now().isoformat()
            )
        
        try:
            # Calculate eligible equity from user's portfolio
            from .models import Portfolio
            from .premium_analytics_service import PremiumAnalyticsService
            
            # Try to get portfolio value from PremiumAnalyticsService
            eligible_equity = 50000.0  # Default fallback
            try:
                service = PremiumAnalyticsService()
                metrics = service.get_portfolio_metrics(user.id)
                if metrics and isinstance(metrics, dict):
                    eligible_equity = float(metrics.get('total_value', 50000))
                elif hasattr(metrics, 'total_value'):
                    eligible_equity = float(metrics.total_value)
            except Exception as e:
                logger.warning(f"Could not fetch portfolio value for SBLOC offer: {e}")
                # Fallback: calculate from Portfolio model
                try:
                    portfolios = Portfolio.objects.filter(user=user).select_related('stock')
                    if portfolios.exists():
                        total_value = sum(
                            float(portfolio.shares * (portfolio.stock.current_price if portfolio.stock and hasattr(portfolio.stock, 'current_price') and portfolio.stock.current_price else 0))
                            for portfolio in portfolios
                        )
                        eligible_equity = max(total_value, 10000.0)  # Minimum $10k
                except Exception as e2:
                    logger.warning(f"Could not calculate portfolio value: {e2}")
            
            # Get best available SBLOC terms (from active banks)
            banks = SBLOCBank.objects.filter(is_active=True).order_by('min_apr', 'priority')
            if banks.exists():
                best_bank = banks.first()
                ltv = float(best_bank.max_ltv) if best_bank.max_ltv else 0.5
                apr = float(best_bank.min_apr) if best_bank.min_apr else 0.085
            else:
                # Default values if no banks configured
                ltv = 0.5
                apr = 0.085
            
            return SBLOCOfferType(
                ltv=ltv,
                apr=apr,
                minDraw=1000,
                maxDrawMultiplier=0.95,
                disclosures=[
                    "Securities-based lines of credit involve risks, including the potential loss of collateral.",
                    "Interest rates may vary and are subject to change.",
                    "Not all securities are eligible for SBLOC.",
                    "This is not an offer of credit. Terms subject to lender approval."
                ],
                eligibleEquity=eligible_equity,
                updatedAt=timezone.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error resolving SBLOC offer: {e}", exc_info=True)
            # Return default offer on error
            return SBLOCOfferType(
                ltv=0.5,
                apr=0.085,
                minDraw=1000,
                maxDrawMultiplier=0.95,
                disclosures=[],
                eligibleEquity=50000.0,
                updatedAt=timezone.now().isoformat()
            )
    
    def resolve_sbloc_session(self, info, id):
        """Get SBLOC session by ID"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            session = SBLOCSession.objects.get(id=id, user=user)
            return session
        except SBLOCSession.DoesNotExist:
            return None

