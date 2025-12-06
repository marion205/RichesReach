"""
Comprehensive unit tests for Budget and Spending Analysis resolvers
"""
import unittest
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.banking_queries import BankingQueries
from core.banking_models import BankAccount, BankTransaction
from core.banking_types import (
    BudgetDataType, BudgetCategoryType,
    SpendingAnalysisType, SpendingCategoryType, TopMerchantType
)

User = get_user_model()


class BudgetDataTestCase(TestCase):
    """Test suite for budget data resolver"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.queries = BankingQueries()
        
        # Create mock info object
        self.mock_info = Mock()
        self.mock_info.context = Mock()
        self.mock_info.context.user = self.user
    
    def test_resolve_budget_data_unauthenticated(self):
        """Test budget data resolver with unauthenticated user"""
        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = Mock()
        mock_info.context.user.is_authenticated = False
        
        result = self.queries.resolve_budget_data(mock_info)
        
        self.assertIsNone(result)
    
    def test_resolve_budget_data_no_transactions(self):
        """Test budget data resolver with no transactions"""
        result = self.queries.resolve_budget_data(self.mock_info)
        
        # Should return budget data even with no transactions
        self.assertIsNotNone(result)
        self.assertIsInstance(result, BudgetDataType)
        self.assertEqual(result.monthlyIncome, 5000.0)
        self.assertEqual(result.monthlyExpenses, 0.0)
        self.assertEqual(result.remaining, 5000.0)
        self.assertEqual(result.savingsRate, 100.0)
        self.assertEqual(len(result.categories), 0)
    
    def test_resolve_budget_data_with_transactions(self):
        """Test budget data resolver with transactions"""
        # Create bank account
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking',
            balance_current=Decimal('1000.00')
        )
        
        # Create transactions in different categories
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-500.00'),
            yodlee_transaction_id='test_txn_20'
        ),
            category='Housing',
            merchant_name='Rent',
            posted_date=timezone.now().date(),
            yodlee_transaction_id='test_txn_1'
        )
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-200.00'),
            yodlee_transaction_id='test_txn_21'
        ),
            category='Food',
            merchant_name='Grocery Store',
            posted_date=timezone.now().date(),
            yodlee_transaction_id='test_txn_2'
        )
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-100.00'),
            yodlee_transaction_id='test_txn_22'
        ),
            category='Transportation',
            merchant_name='Gas Station',
            posted_date=timezone.now().date(),
            yodlee_transaction_id='test_txn_3'
        )
        
        result = self.queries.resolve_budget_data(self.mock_info)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, BudgetDataType)
        self.assertEqual(result.monthlyIncome, 5000.0)
        self.assertEqual(result.monthlyExpenses, 800.0)  # 500 + 200 + 100
        self.assertEqual(result.remaining, 4200.0)
        self.assertAlmostEqual(result.savingsRate, 84.0, places=1)
        
        # Check categories
        self.assertEqual(len(result.categories), 3)
        
        # Find Housing category
        housing_cat = next((c for c in result.categories if c.name == 'Housing'), None)
        self.assertIsNotNone(housing_cat)
        self.assertEqual(housing_cat.spent, 500.0)
        self.assertEqual(housing_cat.budgeted, 550.0)  # 10% buffer
        self.assertAlmostEqual(housing_cat.percentage, 90.9, places=1)
    
    def test_resolve_budget_data_category_percentage_calculation(self):
        """Test budget category percentage calculation"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        # Create transaction that exceeds budget
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-600.00'),
            yodlee_transaction_id='test_txn_23'
        ),
            category='Housing',
            posted_date=timezone.now().date(),
            yodlee_transaction_id='test_txn_4'
        )
        
        result = self.queries.resolve_budget_data(self.mock_info)
        
        housing_cat = next((c for c in result.categories if c.name == 'Housing'), None)
        self.assertIsNotNone(housing_cat)
        # Spent 600, budgeted 660 (600 * 1.1), percentage = 600/660 * 100 = 90.9%
        self.assertAlmostEqual(housing_cat.percentage, 90.9, places=1)
    
    def test_resolve_budget_data_camelcase_alias(self):
        """Test camelCase alias for budget data"""
        result = self.queries.resolve_budgetData(self.mock_info)
        
        # Should return same as resolve_budget_data
        self.assertIsNotNone(result)
        self.assertIsInstance(result, BudgetDataType)


class SpendingAnalysisTestCase(TestCase):
    """Test suite for spending analysis resolver"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.queries = BankingQueries()
        
        self.mock_info = Mock()
        self.mock_info.context = Mock()
        self.mock_info.context.user = self.user
    
    def test_resolve_spending_analysis_unauthenticated(self):
        """Test spending analysis with unauthenticated user"""
        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = Mock()
        mock_info.context.user.is_authenticated = False
        
        result = self.queries.resolve_spending_analysis(mock_info, 'month')
        
        self.assertIsNone(result)
    
    def test_resolve_spending_analysis_no_transactions(self):
        """Test spending analysis with no transactions"""
        result = self.queries.resolve_spending_analysis(self.mock_info, 'month')
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, SpendingAnalysisType)
        self.assertEqual(result.totalSpent, 0.0)
        self.assertEqual(len(result.categories), 0)
        self.assertEqual(len(result.topMerchants), 0)
        self.assertEqual(len(result.trends), 0)
    
    def test_resolve_spending_analysis_with_transactions(self):
        """Test spending analysis with transactions"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        # Create multiple transactions
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-50.00'),
            yodlee_transaction_id='test_txn_24'
        ),
            category='Food',
            merchant_name='Grocery Store',
            posted_date=timezone.now().date() - timedelta(days=5)
        )
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-30.00'),
            yodlee_transaction_id='test_txn_25'
        ),
            category='Food',
            merchant_name='Restaurant',
            posted_date=timezone.now().date() - timedelta(days=3)
        )
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-100.00'),
            yodlee_transaction_id='test_txn_26'
        ),
            category='Transportation',
            merchant_name='Gas Station',
            posted_date=timezone.now().date() - timedelta(days=1)
        )
        
        result = self.queries.resolve_spending_analysis(self.mock_info, 'month')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.totalSpent, 180.0)  # 50 + 30 + 100
        
        # Check categories
        self.assertEqual(len(result.categories), 2)
        
        # Food category should have 2 transactions, 80 total
        food_cat = next((c for c in result.categories if c.name == 'Food'), None)
        self.assertIsNotNone(food_cat)
        self.assertEqual(food_cat.amount, 80.0)
        self.assertEqual(food_cat.transactions, 2)
        self.assertAlmostEqual(food_cat.percentage, 44.4, places=1)  # 80/180 * 100
        
        # Transportation category
        trans_cat = next((c for c in result.categories if c.name == 'Transportation'), None)
        self.assertIsNotNone(trans_cat)
        self.assertEqual(trans_cat.amount, 100.0)
        self.assertEqual(trans_cat.transactions, 1)
        self.assertAlmostEqual(trans_cat.percentage, 55.6, places=1)  # 100/180 * 100
    
    def test_resolve_spending_analysis_top_merchants(self):
        """Test top merchants calculation"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        # Create transactions with same merchant
        for i in range(5):
            BankTransaction.objects.create(
                user=self.user,
                bank_account=account,
            amount=Decimal('-20.00'),
            yodlee_transaction_id='test_txn_27'
        ),
                category='Food',
                merchant_name='Grocery Store',
                posted_date=timezone.now().date() - timedelta(days=i)
            )
        
        result = self.queries.resolve_spending_analysis(self.mock_info, 'month')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.topMerchants), 1)
        
        merchant = result.topMerchants[0]
        self.assertEqual(merchant.name, 'Grocery Store')
        self.assertEqual(merchant.amount, 100.0)  # 5 * 20
        self.assertEqual(merchant.count, 5)
    
    def test_resolve_spending_analysis_period_filtering(self):
        """Test period filtering (week/month/year)"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        # Transaction within last 7 days
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-50.00'),
            yodlee_transaction_id='test_txn_28'
        ),
            category='Food',
            posted_date=timezone.now().date() - timedelta(days=3)
        )
        
        # Transaction older than 7 days (should be excluded for 'week')
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-100.00'),
            yodlee_transaction_id='test_txn_29'
        ),
            category='Food',
            posted_date=timezone.now().date() - timedelta(days=10)
        )
        
        # Test week period
        result_week = self.queries.resolve_spending_analysis(self.mock_info, 'week')
        self.assertEqual(result_week.totalSpent, 50.0)
        
        # Test month period (should include both)
        result_month = self.queries.resolve_spending_analysis(self.mock_info, 'month')
        self.assertEqual(result_month.totalSpent, 150.0)
    
    def test_resolve_spending_analysis_category_sorting(self):
        """Test categories are sorted by amount descending"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-30.00'),
            yodlee_transaction_id='test_txn_30'
        ),
            category='Small',
            posted_date=timezone.now().date()
        )
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-100.00'),
            yodlee_transaction_id='test_txn_31'
        ),
            category='Large',
            posted_date=timezone.now().date()
        )
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-50.00'),
            yodlee_transaction_id='test_txn_32'
        ),
            category='Medium',
            posted_date=timezone.now().date()
        )
        
        result = self.queries.resolve_spending_analysis(self.mock_info, 'month')
        
        # Should be sorted: Large (100), Medium (50), Small (30)
        self.assertEqual(result.categories[0].name, 'Large')
        self.assertEqual(result.categories[0].amount, 100.0)
        self.assertEqual(result.categories[1].name, 'Medium')
        self.assertEqual(result.categories[1].amount, 50.0)
        self.assertEqual(result.categories[2].name, 'Small')
        self.assertEqual(result.categories[2].amount, 30.0)
    
    def test_resolve_spending_analysis_merchant_limit(self):
        """Test top merchants limited to 10"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        # Create transactions for 15 different merchants
        for i in range(15):
            BankTransaction.objects.create(
                user=self.user,
                bank_account=account,
            amount=Decimal('-10.00'),
            yodlee_transaction_id='test_txn_33'
        ),
                category='Other',
                merchant_name=f'Merchant {i}',
                posted_date=timezone.now().date()
            )
        
        result = self.queries.resolve_spending_analysis(self.mock_info, 'month')
        
        # Should only return top 10 merchants
        self.assertLessEqual(len(result.topMerchants), 10)
    
    def test_resolve_spending_analysis_camelcase_alias(self):
        """Test camelCase alias for spending analysis"""
        result = self.queries.resolve_spendingAnalysis(self.mock_info, 'month')
        
        # Should return same as resolve_spending_analysis
        self.assertIsNotNone(result)
        self.assertIsInstance(result, SpendingAnalysisType)
    
    def test_resolve_spending_analysis_unknown_period(self):
        """Test handling of unknown period (defaults to month)"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-50.00'),
            yodlee_transaction_id='test_txn_34'
        ),
            category='Food',
            posted_date=timezone.now().date()
        )
        
        # Unknown period should default to month
        result = self.queries.resolve_spending_analysis(self.mock_info, 'unknown')
        
        self.assertIsNotNone(result)
        # Should still include transaction (within last 30 days)
        self.assertEqual(result.totalSpent, 50.0)
    
    def test_resolve_spending_analysis_missing_category(self):
        """Test handling of transactions with no category"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-50.00'),
            yodlee_transaction_id='test_txn_35'
        ),
            category=None,  # No category
            merchant_name='Unknown',
            posted_date=timezone.now().date(),
            yodlee_transaction_id='test_txn_15'
        )
        
        result = self.queries.resolve_spending_analysis(self.mock_info, 'month')
        
        # Should categorize as 'Other'
        other_cat = next((c for c in result.categories if c.name == 'Other'), None)
        self.assertIsNotNone(other_cat)
        self.assertEqual(other_cat.amount, 50.0)
    
    def test_resolve_spending_analysis_missing_merchant(self):
        """Test handling of transactions with no merchant name"""
        account = BankAccount.objects.create(
            user=self.user,
            provider='test',
            name='Test Account',
            account_type='checking'
        )
        
        BankTransaction.objects.create(
            user=self.user,
            bank_account=account,
            amount=Decimal('-50.00'),
            yodlee_transaction_id='test_txn_36'
        ),
            category='Food',
            merchant_name='Unknown',  # No merchant - use 'Unknown' instead of None
            posted_date=timezone.now().date(),
            yodlee_transaction_id='test_txn_16'
        )
        
        result = self.queries.resolve_spending_analysis(self.mock_info, 'month')
        
        # Should use 'Unknown' as merchant name
        unknown_merchant = next((m for m in result.topMerchants if m.name == 'Unknown'), None)
        self.assertIsNotNone(unknown_merchant)
        self.assertEqual(unknown_merchant.amount, 50.0)


if __name__ == '__main__':
    unittest.main()

