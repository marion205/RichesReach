"""
Unit tests for banking models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from core.banking_models import (
    BankProviderAccount,
    BankAccount,
    BankTransaction,
    BankWebhookEvent,
)

User = get_user_model()


class BankProviderAccountTestCase(TestCase):
    """Tests for BankProviderAccount model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
    
    def test_create_provider_account(self):
        """Test creating a provider account"""
        provider_account = BankProviderAccount.objects.create(
            user=self.user,
            provider_account_id='123',
            provider_name='Test Bank',
            provider_id='test_provider',
            status='ACTIVE',
        )
        
        self.assertEqual(provider_account.user, self.user)
        self.assertEqual(provider_account.provider_account_id, '123')
        self.assertEqual(provider_account.provider_name, 'Test Bank')
        self.assertEqual(provider_account.status, 'ACTIVE')
        self.assertIsNotNone(provider_account.created_at)
    
    def test_provider_account_str(self):
        """Test provider account string representation"""
        provider_account = BankProviderAccount.objects.create(
            user=self.user,
            provider_account_id='123',
            provider_name='Test Bank',
        )
        
        str_repr = str(provider_account)
        self.assertIn('testuser', str_repr)
        self.assertIn('Test Bank', str_repr)
        self.assertIn('123', str_repr)
    
    def test_provider_account_unique_constraint(self):
        """Test that provider_account_id is unique per user"""
        BankProviderAccount.objects.create(
            user=self.user,
            provider_account_id='123',
            provider_name='Test Bank',
        )
        
        # Try to create another with same provider_account_id
        with self.assertRaises(Exception):  # IntegrityError
            BankProviderAccount.objects.create(
                user=self.user,
                provider_account_id='123',
                provider_name='Another Bank',
            )
    
    def test_provider_account_status_choices(self):
        """Test provider account status choices"""
        statuses = ['ACTIVE', 'INACTIVE', 'ERROR', 'DELETED']
        
        for status in statuses:
            provider_account = BankProviderAccount.objects.create(
                user=self.user,
                provider_account_id=f'123_{status}',
                provider_name='Test Bank',
                status=status,
            )
            self.assertEqual(provider_account.status, status)


class BankAccountTestCase(TestCase):
    """Tests for BankAccount model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.provider_account = BankProviderAccount.objects.create(
            user=self.user,
            provider_account_id='123',
            provider_name='Test Bank',
        )
    
    def test_create_bank_account(self):
        """Test creating a bank account"""
        bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
            name='Checking Account',
            mask='1234',
            account_type='CHECKING',
            account_subtype='CHECKING',
            currency='USD',
            balance_current=1000.0,
            balance_available=950.0,
            is_verified=True,
        )
        
        self.assertEqual(bank_account.user, self.user)
        self.assertEqual(bank_account.provider, 'Test Bank')
        self.assertEqual(bank_account.name, 'Checking Account')
        self.assertEqual(bank_account.account_type, 'CHECKING')
        self.assertEqual(bank_account.balance_current, 1000.0)
        self.assertTrue(bank_account.is_verified)
        self.assertIsNotNone(bank_account.created_at)
    
    def test_bank_account_defaults(self):
        """Test bank account default values"""
        bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
        )
        
        self.assertFalse(bank_account.is_verified)
        self.assertFalse(bank_account.is_primary)
        self.assertEqual(bank_account.balance_current, 0.0)
        self.assertEqual(bank_account.balance_available, 0.0)
    
    def test_bank_account_unique_constraint(self):
        """Test that yodlee_account_id is unique per user"""
        BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
        )
        
        # Try to create another with same yodlee_account_id
        with self.assertRaises(Exception):  # IntegrityError
            BankAccount.objects.create(
                user=self.user,
                provider_account=self.provider_account,
                yodlee_account_id='acc_456',
                provider='Another Bank',
            )
    
    def test_bank_account_cascade_delete(self):
        """Test that bank accounts are deleted when user is deleted"""
        bank_account = BankAccount.objects.create(
            user=self.user,
            provider_account=self.provider_account,
            yodlee_account_id='acc_456',
            provider='Test Bank',
        )
        
        account_id = bank_account.id
        self.user.delete()
        
        self.assertFalse(BankAccount.objects.filter(id=account_id).exists())


class BankTransactionTestCase(TestCase):
    """Tests for BankTransaction model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
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
        )
    
    def test_create_transaction(self):
        """Test creating a transaction"""
        transaction = BankTransaction.objects.create(
            user=self.user,
            bank_account=self.bank_account,
            yodlee_transaction_id='txn_789',
            amount=-50.0,
            description='Test Transaction',
            merchant_name='Test Store',
            category='Shopping',
            posted_date=timezone.now().date(),
            transaction_type='DEBIT',
        )
        
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.bank_account, self.bank_account)
        self.assertEqual(transaction.amount, -50.0)
        self.assertEqual(transaction.description, 'Test Transaction')
        self.assertEqual(transaction.transaction_type, 'DEBIT')
    
    def test_transaction_unique_constraint(self):
        """Test transaction unique constraint"""
        posted_date = timezone.now().date()
        
        BankTransaction.objects.create(
            user=self.user,
            bank_account=self.bank_account,
            yodlee_transaction_id='txn_789',
            amount=-50.0,
            description='Test Transaction',
            posted_date=posted_date,
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            BankTransaction.objects.create(
                user=self.user,
                bank_account=self.bank_account,
                yodlee_transaction_id='txn_789',
                amount=-50.0,
                description='Test Transaction',
                posted_date=posted_date,
            )
    
    def test_transaction_positive_amount(self):
        """Test that positive amounts work for credits"""
        transaction = BankTransaction.objects.create(
            user=self.user,
            bank_account=self.bank_account,
            yodlee_transaction_id='txn_credit',
            amount=100.0,
            description='Deposit',
            posted_date=timezone.now().date(),
            transaction_type='CREDIT',
        )
        
        self.assertEqual(transaction.amount, 100.0)
        self.assertEqual(transaction.transaction_type, 'CREDIT')
    
    def test_transaction_cascade_delete(self):
        """Test that transactions are deleted when bank account is deleted"""
        transaction = BankTransaction.objects.create(
            user=self.user,
            bank_account=self.bank_account,
            yodlee_transaction_id='txn_789',
            amount=-50.0,
            description='Test Transaction',
            posted_date=timezone.now().date(),
        )
        
        transaction_id = transaction.id
        self.bank_account.delete()
        
        self.assertFalse(BankTransaction.objects.filter(id=transaction_id).exists())


class BankWebhookEventTestCase(TestCase):
    """Tests for BankWebhookEvent model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
    
    def test_create_webhook_event(self):
        """Test creating a webhook event"""
        event = BankWebhookEvent.objects.create(
            event_type='DATA_UPDATES',
            provider_account_id='123',
            payload={'test': 'data'},
            signature_valid=True,
        )
        
        self.assertEqual(event.event_type, 'DATA_UPDATES')
        self.assertEqual(event.provider_account_id, '123')
        self.assertTrue(event.signature_valid)
        self.assertFalse(event.processed)
        self.assertIsNotNone(event.created_at)
    
    def test_webhook_event_defaults(self):
        """Test webhook event default values"""
        event = BankWebhookEvent.objects.create(
            event_type='DATA_UPDATES',
            provider_account_id='123',
            payload={},
        )
        
        self.assertFalse(event.signature_valid)
        self.assertFalse(event.processed)
    
    def test_webhook_event_process(self):
        """Test marking webhook event as processed"""
        event = BankWebhookEvent.objects.create(
            event_type='DATA_UPDATES',
            provider_account_id='123',
            payload={},
        )
        
        self.assertFalse(event.processed)
        
        event.processed = True
        event.save()
        
        event.refresh_from_db()
        self.assertTrue(event.processed)

