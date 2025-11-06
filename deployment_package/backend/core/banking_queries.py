"""
GraphQL Queries for Banking Operations
"""
import graphene
from graphene_django import DjangoObjectType
from .banking_types import BankAccountType, BankTransactionType, BankProviderAccountType
from .banking_models import BankAccount, BankTransaction, BankProviderAccount
from .yodlee_client import YodleeClient
from django.utils import timezone
from datetime import timedelta


class BankingQueries(graphene.ObjectType):
    """GraphQL queries for banking operations"""
    
    bank_accounts = graphene.List(
        BankAccountType,
        description="Get user's linked bank accounts"
    )
    bank_account = graphene.Field(
        BankAccountType,
        id=graphene.Int(required=True),
        description="Get a specific bank account by ID"
    )
    bank_transactions = graphene.List(
        BankTransactionType,
        account_id=graphene.Int(),
        from_date=graphene.String(),
        to_date=graphene.String(),
        limit=graphene.Int(default_value=50),
        description="Get bank transactions"
    )
    bank_provider_accounts = graphene.List(
        BankProviderAccountType,
        description="Get user's bank provider accounts"
    )
    
    def resolve_bank_accounts(self, info):
        """Get all bank accounts for authenticated user"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Return from database
        accounts = BankAccount.objects.filter(user=user, is_verified=True)
        
        # Optionally refresh from Yodlee if needed (can be done async)
        # For now, just return DB records
        return accounts
    
    def resolve_bank_account(self, info, id):
        """Get a specific bank account"""
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            return BankAccount.objects.get(id=id, user=user, is_verified=True)
        except BankAccount.DoesNotExist:
            return None
    
    def resolve_bank_transactions(self, info, account_id=None, from_date=None, to_date=None, limit=50):
        """Get bank transactions"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Default to last 30 days if not specified
        if not to_date:
            to_date = timezone.now().date()
        else:
            from datetime import datetime
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        
        if not from_date:
            from_date = to_date - timedelta(days=30)
        else:
            from datetime import datetime
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        
        transactions = BankTransaction.objects.filter(
            user=user,
            posted_date__gte=from_date,
            posted_date__lte=to_date,
        )
        
        if account_id:
            try:
                bank_account = BankAccount.objects.get(id=account_id, user=user)
                transactions = transactions.filter(bank_account=bank_account)
            except BankAccount.DoesNotExist:
                return []
        
        return transactions.order_by('-posted_date')[:limit]
    
    def resolve_bank_provider_accounts(self, info):
        """Get user's bank provider accounts"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        return BankProviderAccount.objects.filter(user=user, status='ACTIVE')

