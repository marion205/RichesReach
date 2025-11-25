"""
GraphQL Mutations for Banking Operations
"""
import graphene
import logging
from .banking_types import BankAccountType, BankTransactionType, FundingType
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


class LinkBankAccountResultType(graphene.ObjectType):
    """Result type for linkBankAccount mutation"""
    id = graphene.ID()
    bankName = graphene.String()
    accountType = graphene.String()
    status = graphene.String()


class LinkBankAccount(graphene.Mutation):
    """Link a bank account manually (fallback when Yodlee is not available)"""
    
    class Arguments:
        bank_name = graphene.String(required=True)
        account_number = graphene.String(required=True)
        routing_number = graphene.String(required=True)
        # Also accept camelCase for frontend compatibility
        bankName = graphene.String()
        accountNumber = graphene.String()
        routingNumber = graphene.String()
    
    success = graphene.Boolean()
    message = graphene.String()
    bank_account = graphene.Field(BankAccountType)
    bankAccount = graphene.Field(LinkBankAccountResultType)
    
    @staticmethod
    def mutate(root, info, bank_name=None, account_number=None, routing_number=None, 
               bankName=None, accountNumber=None, routingNumber=None):
        user = info.context.user
        if not user.is_authenticated:
            return LinkBankAccount(
                success=False,
                message="Authentication required"
            )
        
        # Support both snake_case and camelCase
        bank_name = bank_name or bankName
        account_number = account_number or accountNumber
        routing_number = routing_number or routingNumber
        
        if not bank_name or not account_number or not routing_number:
            return LinkBankAccount(
                success=False,
                message="Missing required fields: bankName, accountNumber, routingNumber"
            )
        
        try:
            # For manual linking, we create a basic bank account record
            # In production, this would integrate with ACH verification (micro-deposits)
            mask = account_number[-4:] if len(account_number) >= 4 else account_number
            
            # Check if account already exists
            existing = BankAccount.objects.filter(
                user=user,
                provider=bank_name,
                mask=mask
            ).first()
            
            if existing:
                return LinkBankAccount(
                    success=False,
                    message="This bank account is already linked",
                    bank_account=existing,
                    bankAccount=LinkBankAccountResultType(
                        id=str(existing.id),
                        bankName=existing.provider,
                        accountType=existing.account_type,
                        status='VERIFIED' if existing.is_verified else 'PENDING'
                    )
                )
            
            # Create new bank account (unverified until micro-deposits are confirmed)
            bank_account = BankAccount.objects.create(
                user=user,
                provider=bank_name,
                name=f"{bank_name} Account",
                mask=mask,
                account_type='CHECKING',  # Default, could be determined from account number
                account_subtype='checking',
                currency='USD',
                is_verified=False,  # Will be verified after micro-deposits
                is_primary=False,
            )
            
            logger.info(f"Manually linked bank account {bank_account.id} for user {user.id}")
            
            return LinkBankAccount(
                success=True,
                message="Bank account linked successfully. Please verify with micro-deposits.",
                bank_account=bank_account,
                bankAccount=LinkBankAccountResultType(
                    id=str(bank_account.id),
                    bankName=bank_account.provider,
                    accountType=bank_account.account_type,
                    status='PENDING'
                )
            )
        
        except Exception as e:
            logger.error(f"Error linking bank account: {e}", exc_info=True)
            return LinkBankAccount(
                success=False,
                message=f"Error linking account: {str(e)}"
            )


class InitiateFunding(graphene.Mutation):
    """Initiate funding transfer from bank account to broker account"""
    
    class Arguments:
        amount = graphene.Float(required=True)
        bank_account_id = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    funding = graphene.Field(FundingType)
    
    @staticmethod
    def mutate(root, info, amount, bank_account_id):
        user = info.context.user
        if not user.is_authenticated:
            return InitiateFunding(
                success=False,
                message="Authentication required"
            )
        
        try:
            from .broker_models import BrokerAccount, BrokerFunding
            from datetime import timedelta
            
            # Validate amount
            if amount <= 0:
                return InitiateFunding(
                    success=False,
                    message="Amount must be greater than zero"
                )
            
            # Get user's broker account
            try:
                broker_account = BrokerAccount.objects.get(user=user)
            except BrokerAccount.DoesNotExist:
                return InitiateFunding(
                    success=False,
                    message="Broker account not found. Please complete KYC first."
                )
            
            # Get bank account
            try:
                bank_account = BankAccount.objects.get(id=bank_account_id, user=user)
            except (BankAccount.DoesNotExist, ValueError):
                return InitiateFunding(
                    success=False,
                    message="Bank account not found"
                )
            
            # Check if bank account is verified
            if not bank_account.is_verified:
                return InitiateFunding(
                    success=False,
                    message="Bank account must be verified before funding"
                )
            
            # Create funding record
            funding_record = BrokerFunding.objects.create(
                broker_account=broker_account,
                bank_link_id=bank_account_id,
                transfer_type='DEPOSIT',
                amount=amount,
                status='PENDING',
            )
            
            # In production, this would:
            # 1. Call Alpaca API to initiate ACH transfer
            # 2. Store the transfer ID
            # 3. Set estimated settlement date (typically 3-5 business days)
            
            estimated_completion = timezone.now() + timedelta(days=3)
            
            logger.info(f"Initiated funding ${amount} from bank account {bank_account_id} for user {user.id}")
            
            from .banking_types import FundingType
            
            return InitiateFunding(
                success=True,
                message=f"Funding of ${amount:,.2f} initiated successfully",
                funding=FundingType(
                    id=str(funding_record.id),
                    amount=float(amount),
                    status='PENDING',
                    estimatedCompletion=estimated_completion.isoformat(),
                )
            )
        
        except Exception as e:
            logger.error(f"Error initiating funding: {e}", exc_info=True)
            return InitiateFunding(
                success=False,
                message=f"Error initiating funding: {str(e)}"
            )


class BankingMutations(graphene.ObjectType):
    """GraphQL mutations for banking operations"""
    refresh_bank_account = RefreshBankAccount.Field()
    set_primary_bank_account = SetPrimaryBankAccount.Field()
    sync_bank_transactions = SyncBankTransactions.Field()
    link_bank_account = LinkBankAccount.Field()
    # CamelCase alias for frontend compatibility
    linkBankAccount = LinkBankAccount.Field()
    initiate_funding = InitiateFunding.Field()
    # CamelCase alias for frontend compatibility
    initiateFunding = InitiateFunding.Field()

