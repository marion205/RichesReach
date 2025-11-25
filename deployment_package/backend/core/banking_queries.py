"""
GraphQL Queries for Banking Operations
"""
import graphene
import logging
from graphene_django import DjangoObjectType
from .banking_types import BankAccountType, BankTransactionType, BankProviderAccountType, FundingHistoryType
from .banking_models import BankAccount, BankTransaction, BankProviderAccount
from .yodlee_client import YodleeClient
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class BankingQueries(graphene.ObjectType):
    """GraphQL queries for banking operations"""
    
    bank_accounts = graphene.List(
        BankAccountType,
        description="Get user's linked bank accounts"
    )
    # CamelCase alias for frontend compatibility
    bankAccounts = graphene.List(
        BankAccountType,
        description="Get user's linked bank accounts (camelCase alias)"
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
    funding_history = graphene.List(
        FundingHistoryType,
        description="Get funding history for broker account"
    )
    # CamelCase alias for frontend compatibility
    fundingHistory = graphene.List(
        FundingHistoryType,
        description="Get funding history for broker account (camelCase alias)"
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
    
    def resolve_bankAccounts(self, info):
        """CamelCase alias for bank_accounts"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        # Return from database
        accounts = BankAccount.objects.filter(user=user, is_verified=True)
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
    
    def resolve_funding_history(self, info):
        """Get funding history for user's broker account"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            from .broker_models import BrokerAccount, BrokerFunding
            
            # Get user's broker account
            try:
                broker_account = BrokerAccount.objects.get(user=user)
            except BrokerAccount.DoesNotExist:
                return []
            
            # Get funding records
            funding_records = BrokerFunding.objects.filter(
                broker_account=broker_account
            ).order_by('-created_at')[:50]
            
            # Format for frontend
            result = []
            for record in funding_records:
                result.append(FundingHistoryType(
                    id=str(record.id),
                    amount=float(record.amount),
                    status=record.status,
                    bankAccountId=record.bank_link_id or '',
                    initiatedAt=record.created_at.isoformat() if record.created_at else None,
                    completedAt=record.updated_at.isoformat() if record.status == 'COMPLETED' and record.updated_at else None,
                ))
            
            return result
        except Exception as e:
            logger.error(f"Error resolving funding history: {e}", exc_info=True)
            return []
    
    def resolve_fundingHistory(self, info):
        """CamelCase alias for funding_history"""
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            from .broker_models import BrokerAccount, BrokerFunding
            
            # Get user's broker account
            try:
                broker_account = BrokerAccount.objects.get(user=user)
            except BrokerAccount.DoesNotExist:
                return []
            
            # Get funding records
            funding_records = BrokerFunding.objects.filter(
                broker_account=broker_account
            ).order_by('-created_at')[:50]
            
            # Format for frontend
            result = []
            for record in funding_records:
                result.append(FundingHistoryType(
                    id=str(record.id),
                    amount=float(record.amount),
                    status=record.status,
                    bankAccountId=record.bank_link_id or '',
                    initiatedAt=record.created_at.isoformat() if record.created_at else None,
                    completedAt=record.updated_at.isoformat() if record.status == 'COMPLETED' and record.updated_at else None,
                ))
            
            return result
        except Exception as e:
            logger.error(f"Error resolving funding history: {e}", exc_info=True)
            return []

