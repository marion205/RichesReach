"""
GraphQL Types for SBLOC (Securities-Based Line of Credit) Operations
"""
import graphene
from graphene_django import DjangoObjectType
from .sbloc_models import SBLOCBank, SBLOCSession


class SBLOCBankType(DjangoObjectType):
    """GraphQL type for SBLOC Bank"""
    
    class Meta:
        model = SBLOCBank
        fields = (
            'id',
            'name',
            'logo_url',
            'min_apr',
            'max_apr',
            'min_ltv',
            'max_ltv',
            'notes',
            'regions',
            'min_loan_usd',
            'is_active',
            'priority',
        )
    
    # Add computed fields for GraphQL
    logoUrl = graphene.String(description="Bank logo URL")
    minApr = graphene.Float(description="Minimum APR (as decimal)")
    maxApr = graphene.Float(description="Maximum APR (as decimal)")
    minLtv = graphene.Float(description="Minimum LTV (as decimal)")
    maxLtv = graphene.Float(description="Maximum LTV (as decimal)")
    minLoanUsd = graphene.Int(description="Minimum loan amount in USD")
    
    def resolve_logoUrl(self, info):
        """Resolve logo URL"""
        return self.logo_url
    
    def resolve_minApr(self, info):
        """Resolve minimum APR"""
        return float(self.min_apr) if self.min_apr else None
    
    def resolve_maxApr(self, info):
        """Resolve maximum APR"""
        return float(self.max_apr) if self.max_apr else None
    
    def resolve_minLtv(self, info):
        """Resolve minimum LTV"""
        return float(self.min_ltv) if self.min_ltv else None
    
    def resolve_maxLtv(self, info):
        """Resolve maximum LTV"""
        return float(self.max_ltv) if self.max_ltv else None
    
    def resolve_minLoanUsd(self, info):
        """Resolve minimum loan amount"""
        return int(self.min_loan_usd) if self.min_loan_usd else None


class SBLOCSessionType(DjangoObjectType):
    """GraphQL type for SBLOC Session"""
    
    class Meta:
        model = SBLOCSession
        fields = (
            'id',
            'user',
            'bank',
            'amount_usd',
            'session_id',
            'application_url',
            'status',
            'created_at',
            'updated_at',
        )
    
    # Add computed fields
    sessionId = graphene.String(description="Session ID")
    applicationUrl = graphene.String(description="Application URL")
    amountUsd = graphene.Int(description="Loan amount in USD")
    
    def resolve_sessionId(self, info):
        """Resolve session ID"""
        return self.session_id
    
    def resolve_applicationUrl(self, info):
        """Resolve application URL"""
        return self.application_url
    
    def resolve_amountUsd(self, info):
        """Resolve amount in USD"""
        return int(self.amount_usd) if self.amount_usd else None

