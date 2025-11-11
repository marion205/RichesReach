"""
GraphQL Queries for SBLOC (Securities-Based Line of Credit) Operations
"""
import graphene
from typing import List, Optional
from .sbloc_types import SBLOCBankType
from .sbloc_models import SBLOCBank, SBLOCSession


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
    
    def resolve_sbloc_banks(self, info):
        """Get all active SBLOC banks"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Return active banks, ordered by priority
        banks = SBLOCBank.objects.filter(is_active=True).order_by('priority', 'name')
        return banks
    
    def resolve_sblocBanks(self, info):
        """Get all active SBLOC banks (alias for mobile app)"""
        return self.resolve_sbloc_banks(info)
    
    def resolve_sbloc_bank(self, info, id):
        """Get a specific SBLOC bank"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            return SBLOCBank.objects.get(id=id, is_active=True)
        except SBLOCBank.DoesNotExist:
            return None
    
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

