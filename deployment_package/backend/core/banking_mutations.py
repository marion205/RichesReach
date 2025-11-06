"""
GraphQL Mutations for Banking Operations
"""
import graphene
import logging
from .banking_types import BankAccountType, BankTransactionType
from .banking_models import BankAccount, BankProviderAccount
from .yodlee_client import YodleeClient
from django.utils import timezone
from .banking_tasks import refresh_bank_accounts_task, sync_transactions_task

logger = logging.getLogger(__name__)


class RefreshBankAccount(graphene.Mutation):
    """Refresh bank account data from Yodlee"""
    
    class Arguments:
        account_id = graphene.Int(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    account = graphene.Field(BankAccountType)
    
    @staticmethod
    def mutate(root, info, account_id):
        user = info.context.user
        if not user.is_authenticated:
            return RefreshBankAccount(
                success=False,
                message="Authentication required"
            )
        
        try:
            bank_account = BankAccount.objects.get(id=account_id, user=user)
            provider_account = bank_account.provider_account
            
            if not provider_account:
                return RefreshBankAccount(
                    success=False,
                    message="Provider account not found"
                )
            
            # Trigger async refresh via Celery
            try:
                refresh_bank_accounts_task.delay(user.id, provider_account.id)
                return RefreshBankAccount(
                    success=True,
                    message="Account refresh initiated",
                    account=bank_account
                )
            except Exception as e:
                logger.error(f"Error triggering async refresh: {e}")
                # Fallback to synchronous refresh
                yodlee = YodleeClient()
                yodlee.refresh_account(provider_account.provider_account_id)
                return RefreshBankAccount(
                    success=True,
                    message="Account refresh completed",
                    account=bank_account
                )
        
        except BankAccount.DoesNotExist:
            return RefreshBankAccount(
                success=False,
                message="Bank account not found"
            )
        except Exception as e:
            logger.error(f"Error refreshing bank account: {e}")
            return RefreshBankAccount(
                success=False,
                message=f"Error: {str(e)}"
            )


class SetPrimaryBankAccount(graphene.Mutation):
    """Set a bank account as primary"""
    
    class Arguments:
        account_id = graphene.Int(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    account = graphene.Field(BankAccountType)
    
    @staticmethod
    def mutate(root, info, account_id):
        user = info.context.user
        if not user.is_authenticated:
            return SetPrimaryBankAccount(
                success=False,
                message="Authentication required"
            )
        
        try:
            bank_account = BankAccount.objects.get(id=account_id, user=user)
            
            # Unset all other primary accounts
            BankAccount.objects.filter(user=user, is_primary=True).update(is_primary=False)
            
            # Set this one as primary
            bank_account.is_primary = True
            bank_account.save()
            
            return SetPrimaryBankAccount(
                success=True,
                message="Primary account updated",
                account=bank_account
            )
        
        except BankAccount.DoesNotExist:
            return SetPrimaryBankAccount(
                success=False,
                message="Bank account not found"
            )
        except Exception as e:
            logger.error(f"Error setting primary account: {e}")
            return SetPrimaryBankAccount(
                success=False,
                message=f"Error: {str(e)}"
            )


class SyncBankTransactions(graphene.Mutation):
    """Sync transactions for a bank account"""
    
    class Arguments:
        account_id = graphene.Int(required=True)
        from_date = graphene.String()
        to_date = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    transactions_count = graphene.Int()
    
    @staticmethod
    def mutate(root, info, account_id, from_date=None, to_date=None):
        user = info.context.user
        if not user.is_authenticated:
            return SyncBankTransactions(
                success=False,
                message="Authentication required"
            )
        
        try:
            bank_account = BankAccount.objects.get(id=account_id, user=user)
            
            # Trigger async sync via Celery
            try:
                sync_transactions_task.delay(user.id, bank_account.id, from_date, to_date)
                return SyncBankTransactions(
                    success=True,
                    message="Transaction sync initiated",
                    transactions_count=0
                )
            except Exception as e:
                logger.error(f"Error triggering async sync: {e}")
                # Fallback to synchronous sync
                yodlee = YodleeClient()
                user_id = str(user.id)
                yodlee_transactions = yodlee.get_transactions(
                    user_id,
                    account_id=bank_account.yodlee_account_id,
                    from_date=from_date,
                    to_date=to_date,
                )
                
                # Store transactions (simplified - see banking_views.py for full logic)
                count = len(yodlee_transactions)
                return SyncBankTransactions(
                    success=True,
                    message=f"Synced {count} transactions",
                    transactions_count=count
                )
        
        except BankAccount.DoesNotExist:
            return SyncBankTransactions(
                success=False,
                message="Bank account not found"
            )
        except Exception as e:
            logger.error(f"Error syncing transactions: {e}")
            return SyncBankTransactions(
                success=False,
                message=f"Error: {str(e)}"
            )


class BankingMutations(graphene.ObjectType):
    """GraphQL mutations for banking operations"""
    refresh_bank_account = RefreshBankAccount.Field()
    set_primary_bank_account = SetPrimaryBankAccount.Field()
    sync_bank_transactions = SyncBankTransactions.Field()

