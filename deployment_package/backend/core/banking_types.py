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
    
    # CamelCase aliases for frontend compatibility
    balanceCurrent = graphene.Float()
    balanceAvailable = graphene.Float()
    accountType = graphene.String()
    accountSubtype = graphene.String()
    isVerified = graphene.Boolean()
    isPrimary = graphene.Boolean()
    lastUpdated = graphene.String()
    createdAt = graphene.String()
    
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
    
    def resolve_balanceCurrent(self, info):
        """CamelCase alias for balance_current"""
        return self.resolve_balance_current(info)
    
    def resolve_balanceAvailable(self, info):
        """CamelCase alias for balance_available"""
        return self.resolve_balance_available(info)
    
    def resolve_accountType(self, info):
        """CamelCase alias for account_type"""
        return self.account_type
    
    def resolve_accountSubtype(self, info):
        """CamelCase alias for account_subtype"""
        return self.account_subtype
    
    def resolve_isVerified(self, info):
        """CamelCase alias for is_verified"""
        return self.is_verified
    
    def resolve_isPrimary(self, info):
        """CamelCase alias for is_primary"""
        return self.is_primary
    
    def resolve_lastUpdated(self, info):
        """CamelCase alias for last_updated"""
        return self.last_updated.isoformat() if self.last_updated else None
    
    def resolve_createdAt(self, info):
        """CamelCase alias for created_at"""
        return self.created_at.isoformat() if self.created_at else None


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


class FundingHistoryType(graphene.ObjectType):
    """GraphQL type for funding history"""
    id = graphene.ID()
    amount = graphene.Float()
    status = graphene.String()
    bankAccountId = graphene.String()
    initiatedAt = graphene.String()
    completedAt = graphene.String()


class FundingType(graphene.ObjectType):
    """GraphQL type for funding result"""
    id = graphene.ID()
    amount = graphene.Float()
    status = graphene.String()
    estimatedCompletion = graphene.String()


# Budget and spending analysis types (for budgetData / spendingAnalysis root fields)

class BudgetCategoryType(graphene.ObjectType):
    """GraphQL type for a budget category"""
    name = graphene.String()
    budgeted = graphene.Float()
    spent = graphene.Float()
    percentage = graphene.Float()


class BudgetDataType(graphene.ObjectType):
    """GraphQL type for budget summary"""
    monthlyIncome = graphene.Float()
    monthlyExpenses = graphene.Float()
    categories = graphene.List(BudgetCategoryType)
    remaining = graphene.Float()
    savingsRate = graphene.Float()


class SpendingCategoryType(graphene.ObjectType):
    """GraphQL type for spending by category"""
    name = graphene.String()
    amount = graphene.Float()
    percentage = graphene.Float()
    transactions = graphene.Int()
    trend = graphene.String()


class TopMerchantType(graphene.ObjectType):
    """GraphQL type for top merchant"""
    name = graphene.String()
    amount = graphene.Float()
    count = graphene.Int()


class SpendingAnalysisType(graphene.ObjectType):
    """GraphQL type for spending analysis"""
    totalSpent = graphene.Float()
    categories = graphene.List(SpendingCategoryType)
    topMerchants = graphene.List(TopMerchantType)
    trends = graphene.List(graphene.String)

