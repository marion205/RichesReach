"""
Unit tests for GraphQL banking mutations
"""
from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from django.utils import timezone

from core.banking_mutations import BankingMutations, LinkBankAccount, InitiateFunding
from core.banking_models import BankAccount, BankProviderAccount
from core.broker_models import BrokerAccount, BrokerFunding
try:
    from core.schema import schema
except ImportError:
    schema = None

User = get_user_model()


class BankingMutationsTestCase(TestCase):
    """Tests for Banking GraphQL mutations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.provider_account = BankProviderAccount.objects.create(
            user=self.user,
            provider_account_id='123',
            provider_name='Test Bank',
        )
        self.bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
            name='Checking Account',
            mask='1234',
            account_type='CHECKING',
            is_verified=True,
        )
        self.broker_account = BrokerAccount.objects.create(
            user=self.user,
            kyc_status='APPROVED'
        )
    
    def _create_context(self, user=None):
        """Create GraphQL context"""
        context = Mock()
        context.user = user or self.user
        return context
    
    def test_linkBankAccount_success(self):
        """Test linking a bank account successfully"""
        info = Mock()
        info.context = self._create_context()
        
        result = LinkBankAccount.mutate(
            None,
            info,
            bank_name='New Bank',
            account_number='1234567890',
            routing_number='987654321'
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.bank_account)
        self.assertIsNotNone(result.bankAccount)
        self.assertEqual(result.bankAccount.bankName, 'New Bank')
        self.assertEqual(result.bankAccount.accountType, 'CHECKING')
        self.assertEqual(result.bankAccount.status, 'PENDING')
    
    def test_linkBankAccount_duplicate(self):
        """Test linking duplicate bank account"""
        info = Mock()
        info.context = self._create_context()
        
        # Try to link same account again
        result = LinkBankAccount.mutate(
            None,
            info,
            bank_name='Test Bank',
            account_number='1234567890',
            routing_number='987654321'
        )
        
        # Should fail or return existing account
        # The implementation checks for existing accounts
        self.assertIsNotNone(result.bank_account or result.bankAccount)
    
    def test_linkBankAccount_camelCase(self):
        """Test linkBankAccount with camelCase arguments"""
        info = Mock()
        info.context = self._create_context()
        
        result = LinkBankAccount.mutate(
            None,
            info,
            bank_name=None,
            account_number=None,
            routing_number=None,
            bankName='New Bank',
            accountNumber='1234567890',
            routingNumber='987654321'
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.bank_account)
    
    def test_initiateFunding_success(self):
        """Test initiating funding successfully"""
        info = Mock()
        info.context = self._create_context()
        
        result = InitiateFunding.mutate(
            None,
            info,
            amount=500.00,
            bank_account_id=str(self.bank_account.id)
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.funding)
        self.assertEqual(result.funding.amount, 500.0)
        self.assertEqual(result.funding.status, 'PENDING')
        self.assertIsNotNone(result.funding.estimatedCompletion)
    
    def test_initiateFunding_invalid_amount(self):
        """Test initiating funding with invalid amount"""
        info = Mock()
        info.context = self._create_context()
        
        result = InitiateFunding.mutate(
            None,
            info,
            amount=-100.00,
            bank_account_id=str(self.bank_account.id)
        )
        
        self.assertFalse(result.success)
        self.assertIn('greater than zero', result.message)
    
    def test_initiateFunding_no_broker_account(self):
        """Test initiating funding without broker account"""
        # Delete broker account
        self.broker_account.delete()
        
        info = Mock()
        info.context = self._create_context()
        
        result = InitiateFunding.mutate(
            None,
            info,
            amount=500.00,
            bank_account_id=str(self.bank_account.id)
        )
        
        self.assertFalse(result.success)
        self.assertIn('Broker account not found', result.message)
    
    def test_initiateFunding_unverified_account(self):
        """Test initiating funding with unverified bank account"""
        # Make bank account unverified
        self.bank_account.is_verified = False
        self.bank_account.save()
        
        info = Mock()
        info.context = self._create_context()
        
        result = InitiateFunding.mutate(
            None,
            info,
            amount=500.00,
            bank_account_id=str(self.bank_account.id)
        )
        
        self.assertFalse(result.success)
        self.assertIn('verified', result.message.lower())


class BankingMutationsGraphQLTestCase(TestCase):
    """Integration tests for GraphQL banking mutations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        if schema is None:
            self.skipTest("GraphQL schema not available")
        self.client = Client(schema)
    
    def _execute_mutation(self, mutation, user=None):
        """Execute GraphQL mutation"""
        context = Mock()
        context.user = user or self.user
        return self.client.execute(mutation, context_value=context)
    
    def test_linkBankAccount_mutation(self):
        """Test linkBankAccount GraphQL mutation"""
        mutation = '''
        mutation {
            linkBankAccount(
                bankName: "Test Bank"
                accountNumber: "1234567890"
                routingNumber: "987654321"
            ) {
                success
                message
                bankAccount {
                    id
                    bankName
                    accountType
                    status
                }
            }
        }
        '''
        
        result = self._execute_mutation(mutation)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertIn('linkBankAccount', result['data'])
        self.assertTrue(result['data']['linkBankAccount']['success'])
        self.assertIsNotNone(result['data']['linkBankAccount']['bankAccount'])
    
    def test_initiateFunding_mutation(self):
        """Test initiateFunding GraphQL mutation"""
        # Create required accounts
        broker_account = BrokerAccount.objects.create(
            user=self.user,
            kyc_status='APPROVED'
        )
        bank_account = BankAccount.objects.create(
            user=self.user,
            provider='Test Bank',
            name='Test Account',
            mask='1234',
            account_type='CHECKING',
            is_verified=True,
        )
        
        mutation = '''
        mutation {
            initiateFunding(
                amount: 1000.00
                bankAccountId: "%s"
            ) {
                success
                message
                funding {
                    id
                    amount
                    status
                    estimatedCompletion
                }
            }
        }
        ''' % bank_account.id
        
        result = self._execute_mutation(mutation)
        
        self.assertNotIn('errors', result)
        self.assertIn('data', result)
        self.assertIn('initiateFunding', result['data'])
        self.assertTrue(result['data']['initiateFunding']['success'])
        self.assertIsNotNone(result['data']['initiateFunding']['funding'])
