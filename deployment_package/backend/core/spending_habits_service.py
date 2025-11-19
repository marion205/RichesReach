"""
Spending Habits Analysis Service
Analyzes bank transactions to understand user spending patterns and calculate discretionary income
"""
from django.db.models import Sum, Q, Count, F
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async
from datetime import timedelta, datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging
from .banking_models import BankTransaction, BankAccount
from .models import IncomeProfile

logger = logging.getLogger(__name__)

# Cache TTL for spending analysis (1 hour)
SPENDING_ANALYSIS_CACHE_TTL = 3600


class SpendingHabitsService:
    """Service to analyze spending habits from bank transactions"""
    
    # Spending categories mapping
    SPENDING_CATEGORIES = {
        'Technology': ['APPLE', 'MICROSOFT', 'GOOGLE', 'AMAZON', 'NETFLIX', 'SPOTIFY', 'ADOBE', 'SOFTWARE', 'APP STORE'],
        'Travel': ['AIRLINE', 'HOTEL', 'UBER', 'LYFT', 'TRAVEL', 'VACATION', 'TRIP', 'AIRBNB', 'EXPEDIA', 'BOOKING'],
        'Food & Dining': ['RESTAURANT', 'STARBUCKS', 'MCDONALD', 'UBER EATS', 'DOORDASH', 'GRUBHUB', 'GROCERY', 'FOOD'],
        'Shopping': ['AMAZON', 'TARGET', 'WALMART', 'EBAY', 'SHOP', 'RETAIL', 'STORE'],
        'Subscriptions': ['NETFLIX', 'SPOTIFY', 'APPLE', 'ADOBE', 'MICROSOFT', 'SUBSCRIPTION', 'MONTHLY', 'ANNUAL'],
        'Entertainment': ['MOVIE', 'THEATER', 'CONCERT', 'EVENT', 'TICKET', 'ENTERTAINMENT'],
        'Healthcare': ['HOSPITAL', 'DOCTOR', 'PHARMACY', 'CVS', 'WALGREENS', 'MEDICAL', 'HEALTH'],
        'Transportation': ['GAS', 'FUEL', 'PARKING', 'TOLL', 'TRANSPORT', 'CAR', 'AUTO'],
        'Utilities': ['ELECTRIC', 'WATER', 'GAS', 'INTERNET', 'PHONE', 'UTILITY', 'BILL'],
        'Education': ['SCHOOL', 'UNIVERSITY', 'COURSE', 'EDUCATION', 'TUTOR', 'TRAINING'],
    }
    
    ESSENTIAL_CATEGORIES = ['Healthcare', 'Utilities', 'Transportation', 'Food & Dining']
    
    def __init__(self):
        self.logger = logger
    
    def analyze_spending_habits(self, user_id: int, months: int = 3) -> Dict[str, Any]:
        """
        Analyze user spending habits from bank transactions (with caching)
        Synchronous version - kept for backward compatibility
        
        Args:
            user_id: User ID
            months: Number of months to analyze (default: 3)
            
        Returns:
            Dictionary with spending analysis
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.analyze_spending_habits_async(user_id, months))
    
    async def analyze_spending_habits_async(self, user_id: int, months: int = 3) -> Dict[str, Any]:
        """
        Analyze user spending habits from bank transactions (async version with caching)
        
        Args:
            user_id: User ID
            months: Number of months to analyze (default: 3)
            
        Returns:
            Dictionary with spending analysis including:
            - spending_by_category: Dict of category -> total amount
            - monthly_average: Average monthly spending
            - discretionary_income: Income - essential expenses
            - spending_patterns: Analysis of spending behavior
            - suggested_budget: Recommended investment budget
        """
        # Check cache first (cache operations are thread-safe)
        cache_key = f"spending_analysis:{user_id}:{months}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            self.logger.debug(f"Cache hit for spending analysis: {cache_key}")
            return cached_result
        
        try:
            # Get date range
            end_date = timezone.now()
            start_date = end_date - timedelta(days=months * 30)
            
            # OPTIMIZATION: Use async database aggregation
            # Get total spending using database Sum() aggregation
            total_spending_result = await sync_to_async(
                lambda: BankTransaction.objects.filter(
                    user_id=user_id,
                    transaction_type='DEBIT',
                    transaction_date__gte=start_date,
                    transaction_date__lte=end_date
                ).aggregate(total=Sum('amount'))
            )()
            
            total_spending = abs(float(total_spending_result['total'] or 0))
            
            if total_spending == 0:
                self.logger.warning(f"No transactions found for user {user_id}")
                result = await self._get_default_analysis_async(user_id)
                # Cache the default result too
                cache.set(cache_key, result, SPENDING_ANALYSIS_CACHE_TTL)
                return result
            
            # OPTIMIZATION: Use async database aggregation for category totals
            # Get spending by category using database aggregation
            category_totals_list = await sync_to_async(list)(
                BankTransaction.objects.filter(
                    user_id=user_id,
                    transaction_type='DEBIT',
                    transaction_date__gte=start_date,
                    transaction_date__lte=end_date
                ).values('category').annotate(
                    total=Sum('amount')
                )
            )
            
            # Build spending_by_category from database results
            spending_by_category = {}
            for item in category_totals_list:
                category = item['category'] or 'Other'
                amount = abs(float(item['total'] or 0))
                if category not in spending_by_category:
                    spending_by_category[category] = Decimal('0')
                spending_by_category[category] += Decimal(str(amount))
            
            # Still need to categorize by merchant/description for better accuracy
            # But we can optimize this by only fetching needed fields
            uncategorized_transactions_list = await sync_to_async(list)(
                BankTransaction.objects.filter(
                    user_id=user_id,
                    transaction_type='DEBIT',
                    transaction_date__gte=start_date,
                    transaction_date__lte=end_date
                ).exclude(
                    category__in=[cat for cat in spending_by_category.keys() if cat != 'Other']
                ).only('description', 'merchant_name', 'category', 'amount')
            )
            
            # Categorize uncategorized transactions (smaller set)
            for transaction in uncategorized_transactions_list:
                matched_category = self._match_transaction_category(transaction)
                amount = abs(float(transaction.amount))
                if matched_category not in spending_by_category:
                    spending_by_category[matched_category] = Decimal('0')
                spending_by_category[matched_category] += Decimal(str(amount))
            
            monthly_average = total_spending / months if months > 0 else 0
            
            # OPTIMIZATION: Use async select_related to avoid extra query
            # Get user income with select_related if possible
            try:
                income_profile = await sync_to_async(
                    lambda: IncomeProfile.objects.select_related('user').get(user_id=user_id)
                )()
                income_bracket = income_profile.income_bracket
                monthly_income = self._estimate_monthly_income(income_bracket)
            except IncomeProfile.DoesNotExist:
                self.logger.warning(f"No income profile for user {user_id}")
                monthly_income = 0
                income_bracket = None
            
            # Calculate essential expenses
            essential_expenses = sum(
                spending_by_category.get(cat, 0) 
                for cat in self.ESSENTIAL_CATEGORIES
            )
            essential_monthly = essential_expenses / months if months > 0 else 0
            
            # Calculate discretionary income
            discretionary_income = monthly_income - essential_monthly
            if discretionary_income < 0:
                discretionary_income = 0
            
            # Analyze spending patterns
            spending_patterns = self._analyze_spending_patterns(
                spending_by_category, 
                monthly_average,
                monthly_income
            )
            
            # Calculate suggested investment budget (30% of discretionary income)
            suggested_budget = discretionary_income * Decimal('0.30')
            
            # Get top spending categories
            top_categories = sorted(
                spending_by_category.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Get transaction count async
            transaction_count = await sync_to_async(
                lambda: BankTransaction.objects.filter(
                    user_id=user_id,
                    transaction_type='DEBIT',
                    transaction_date__gte=start_date,
                    transaction_date__lte=end_date
                ).count()
            )()
            
            result = {
                'spending_by_category': {k: float(v) for k, v in spending_by_category.items()},
                'total_spending': float(total_spending),
                'monthly_average': float(monthly_average),
                'monthly_income': float(monthly_income),
                'income_bracket': income_bracket,
                'essential_expenses': float(essential_expenses),
                'essential_monthly': float(essential_monthly),
                'discretionary_income': float(discretionary_income),
                'spending_patterns': spending_patterns,
                'suggested_budget': float(suggested_budget),
                'top_categories': [
                    {'category': cat, 'amount': float(amt)} 
                    for cat, amt in top_categories
                ],
                'analysis_period_months': months,
                'transaction_count': transaction_count,
            }
            
            # Cache the result
            cache.set(cache_key, result, SPENDING_ANALYSIS_CACHE_TTL)
            self.logger.debug(f"Cached spending analysis: {cache_key}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing spending habits for user {user_id}: {e}", exc_info=True)
            return await self._get_default_analysis_async(user_id)
    
    def _match_transaction_category(self, transaction) -> str:
        """Match a single transaction to a spending category (optimized helper)"""
        description_upper = transaction.description.upper()
        merchant_upper = (transaction.merchant_name or '').upper()
        category_upper = (transaction.category or '').upper()
        
        # Check merchant name first
        for category, keywords in self.SPENDING_CATEGORIES.items():
            if any(keyword in merchant_upper for keyword in keywords):
                return category
        
        # Check description if no merchant match
        for category, keywords in self.SPENDING_CATEGORIES.items():
            if any(keyword in description_upper for keyword in keywords):
                return category
        
        # Check transaction category
        if category_upper:
            category_mapping = {
                'FOOD': 'Food & Dining',
                'TRAVEL': 'Travel',
                'SHOPPING': 'Shopping',
                'ENTERTAINMENT': 'Entertainment',
                'HEALTHCARE': 'Healthcare',
                'TRANSPORTATION': 'Transportation',
                'UTILITIES': 'Utilities',
                'EDUCATION': 'Education',
            }
            return category_mapping.get(category_upper, 'Other')
        
        return 'Other'
    
    def _categorize_transactions(self, transactions) -> Dict[str, Decimal]:
        """Categorize transactions by spending category (legacy method - kept for compatibility)"""
        spending_by_category = {}
        
        for transaction in transactions:
            matched_category = self._match_transaction_category(transaction)
            
            # Add to category total
            if matched_category not in spending_by_category:
                spending_by_category[matched_category] = Decimal('0')
            spending_by_category[matched_category] += abs(transaction.amount)
        
        return spending_by_category
    
    def _analyze_spending_patterns(
        self, 
        spending_by_category: Dict[str, Decimal],
        monthly_average: Decimal,
        monthly_income: Decimal
    ) -> Dict[str, Any]:
        """Analyze spending patterns and provide insights"""
        patterns = {
            'savings_rate': 0.0,
            'spending_rate': 0.0,
            'high_spending_categories': [],
            'spending_health': 'unknown',
        }
        
        if monthly_income > 0:
            spending_rate = (monthly_average / monthly_income) * 100
            savings_rate = 100 - spending_rate
            
            patterns['savings_rate'] = float(savings_rate)
            patterns['spending_rate'] = float(spending_rate)
            
            # Determine spending health
            if savings_rate >= 20:
                patterns['spending_health'] = 'excellent'
            elif savings_rate >= 10:
                patterns['spending_health'] = 'good'
            elif savings_rate >= 5:
                patterns['spending_health'] = 'fair'
            else:
                patterns['spending_health'] = 'poor'
        
        # Find high spending categories (>20% of total)
        total = sum(spending_by_category.values())
        if total > 0:
            for category, amount in spending_by_category.items():
                percentage = (amount / total) * 100
                if percentage > 20:
                    patterns['high_spending_categories'].append({
                        'category': category,
                        'percentage': float(percentage),
                        'amount': float(amount)
                    })
        
        return patterns
    
    def _estimate_monthly_income(self, income_bracket: str) -> Decimal:
        """Estimate monthly income from income bracket"""
        # Convert annual income bracket to monthly estimate
        bracket_ranges = {
            'Under $30,000': 25000,
            '$30,000 - $50,000': 40000,
            '$50,000 - $75,000': 62500,
            '$75,000 - $100,000': 87500,
            '$100,000 - $150,000': 125000,
            'Over $150,000': 175000,
        }
        
        annual_income = bracket_ranges.get(income_bracket, 50000)
        monthly_income = annual_income / 12
        
        return Decimal(str(monthly_income))
    
    def _get_default_analysis(self, user_id: int) -> Dict[str, Any]:
        """Return default analysis when no transactions are available (sync version)"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._get_default_analysis_async(user_id))
    
    async def _get_default_analysis_async(self, user_id: int) -> Dict[str, Any]:
        """Return default analysis when no transactions are available (async version)"""
        try:
            # OPTIMIZATION: Use async select_related to avoid extra query
            income_profile = await sync_to_async(
                lambda: IncomeProfile.objects.select_related('user').get(user_id=user_id)
            )()
            monthly_income = self._estimate_monthly_income(income_profile.income_bracket)
            # Assume 70% spending rate if no data
            suggested_budget = monthly_income * Decimal('0.30') * Decimal('0.30')  # 30% of 30% discretionary
            income_bracket = income_profile.income_bracket
        except IncomeProfile.DoesNotExist:
            monthly_income = Decimal('0')
            suggested_budget = Decimal('0')
            income_bracket = None
        
        return {
            'spending_by_category': {},
            'total_spending': 0.0,
            'monthly_average': 0.0,
            'monthly_income': float(monthly_income),
            'income_bracket': income_bracket,
            'essential_expenses': 0.0,
            'essential_monthly': 0.0,
            'discretionary_income': float(monthly_income * Decimal('0.30')),  # Assume 30% discretionary
            'spending_patterns': {
                'savings_rate': 30.0,
                'spending_rate': 70.0,
                'high_spending_categories': [],
                'spending_health': 'unknown',
            },
            'suggested_budget': float(suggested_budget),
            'top_categories': [],
            'analysis_period_months': 0,
            'transaction_count': 0,
        }
    
    def get_spending_based_stock_preferences(
        self, 
        spending_analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Get stock preferences based on spending categories
        
        Returns weights for different stock sectors based on spending habits
        """
        spending_by_category = spending_analysis.get('spending_by_category', {})
        total_spending = sum(spending_by_category.values())
        
        if total_spending == 0:
            return {}
        
        # Map spending categories to stock sectors
        category_to_sector = {
            'Technology': 'Technology',
            'Subscriptions': 'Technology',
            'Travel': 'Consumer Discretionary',
            'Food & Dining': 'Consumer Staples',
            'Shopping': 'Consumer Discretionary',
            'Entertainment': 'Communication Services',
            'Healthcare': 'Healthcare',
            'Transportation': 'Industrials',
            'Utilities': 'Utilities',
            'Education': 'Consumer Discretionary',
        }
        
        sector_weights = {}
        for category, amount in spending_by_category.items():
            sector = category_to_sector.get(category, 'Other')
            weight = float(amount / total_spending)
            
            if sector not in sector_weights:
                sector_weights[sector] = 0.0
            sector_weights[sector] += weight
        
        # Normalize weights
        total_weight = sum(sector_weights.values())
        if total_weight > 0:
            sector_weights = {
                sector: weight / total_weight 
                for sector, weight in sector_weights.items()
            }
        
        return sector_weights

