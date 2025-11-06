"""
GraphQL Types for Banking - Bank accounts and transactions
"""
import graphene
from graphene_django import DjangoObjectType
from .banking_models import BankAccount, BankTransaction, BankProviderAccount


class BankAccountType(DjangoObjectType):
    """GraphQL type for bank account"""
    balance_current = graphene.Float()
    balance_available = graphene.Float()
    
    class Meta:
        model = BankAccount
        fields = (
            'id', 'provider', 'name', 'mask', 'account_type',
            'account_subtype', 'currency', 'is_verified', 'is_primary',
            'last_updated', 'created_at', 'updated_at'
        )
    
    def resolve_balance_current(self, info):
        """Convert Decimal to Float"""
        return float(self.balance_current) if self.balance_current else None
    
    def resolve_balance_available(self, info):
        """Convert Decimal to Float"""
        return float(self.balance_available) if self.balance_available else None


class BankTransactionType(DjangoObjectType):
    """GraphQL type for bank transaction"""
    amount = graphene.Float()
    
    class Meta:
        model = BankTransaction
        fields = (
            'id', 'amount', 'currency', 'description', 'merchant_name',
            'category', 'subcategory', 'transaction_type', 'posted_date',
            'transaction_date', 'status', 'created_at', 'updated_at'
        )
    
    def resolve_amount(self, info):
        """Convert Decimal to Float"""
        return float(self.amount) if self.amount else None


class BankProviderAccountType(DjangoObjectType):
    """GraphQL type for bank provider account"""
    
    class Meta:
        model = BankProviderAccount
        fields = (
            'id', 'provider_name', 'provider_id', 'status',
            'last_refresh', 'error_message', 'created_at', 'updated_at'
        )

