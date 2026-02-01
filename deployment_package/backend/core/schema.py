# core/schema.py
import logging
import graphene
from django.contrib.auth import get_user_model

# Import base Query and Mutation
from .queries import Query
try:
    from .mutations import Mutation
except (ImportError, SyntaxError):
    # Create empty Mutation class if mutations can't be imported
    class Mutation(graphene.ObjectType):
        pass

# Import all types to ensure they're registered
from .types import *
from .benchmark_types import BenchmarkSeriesType, BenchmarkDataPointType
from .portfolio_history_types import PortfolioHistoryDataPointType
from .broker_types import BrokerAccountType, BrokerOrderType, BrokerPositionType

# Import premium queries and mutations
try:
    from .premium_types import PremiumQueries, PremiumMutations, ProfileInput, AIRecommendationsType
except (ImportError, SyntaxError):
    # Create empty classes if premium_types can't be imported
    class PremiumQueries(graphene.ObjectType):
        pass
    class PremiumMutations(graphene.ObjectType):
        pass
    ProfileInput = None
    AIRecommendationsType = None

# Import other feature modules (optional - create empty if not available)
try:
    from .broker_queries import BrokerQueries
except (ImportError, SyntaxError):
    class BrokerQueries(graphene.ObjectType):
        pass

try:
    from .broker_mutations import BrokerMutations
except (ImportError, SyntaxError):
    class BrokerMutations(graphene.ObjectType):
        pass

try:
    from .banking_queries import BankingQueries
except (ImportError, SyntaxError):
    class BankingQueries(graphene.ObjectType):
        pass

try:
    from .banking_mutations import BankingMutations
except (ImportError, SyntaxError):
    class BankingMutations(graphene.ObjectType):
        pass

try:
    from .sbloc_queries import SBLOCQueries
except (ImportError, SyntaxError):
    class SBLOCQueries(graphene.ObjectType):
        pass

try:
    from .sbloc_mutations import SBLOCMutations
except (ImportError, SyntaxError):
    class SBLOCMutations(graphene.ObjectType):
        pass

try:
    from .paper_trading_types import PaperTradingQueries, PaperTradingMutations
except (ImportError, SyntaxError):
    class PaperTradingQueries(graphene.ObjectType):
        pass
    class PaperTradingMutations(graphene.ObjectType):
        pass

try:
    from .social_types import SocialQueries, SocialMutations
except (ImportError, SyntaxError):
    class SocialQueries(graphene.ObjectType):
        pass
    class SocialMutations(graphene.ObjectType):
        pass

try:
    from .privacy_types import PrivacyQueries, PrivacyMutations
except (ImportError, SyntaxError):
    class PrivacyQueries(graphene.ObjectType):
        pass
    class PrivacyMutations(graphene.ObjectType):
        pass

try:
    from .ai_insights_types import AIInsightsQueries, AIInsightsMutations
except (ImportError, SyntaxError):
    class AIInsightsQueries(graphene.ObjectType):
        pass
    class AIInsightsMutations(graphene.ObjectType):
        pass

try:
    from .ai_scans_types import AIScansQueries
except (ImportError, SyntaxError):
    class AIScansQueries(graphene.ObjectType):
        pass

logger = logging.getLogger(__name__)
User = get_user_model()

# -------------------- QUERY --------------------
# Base Query has resolve_me which will be available in ExtendedQuery
# The resolve_me in queries.py should work, but let's ensure it uses proper context

try:
    from .risk_management_types import RiskManagementQueries
except (ImportError, SyntaxError):
    class RiskManagementQueries(graphene.ObjectType):
        pass

try:
    from .options_alert_queries import OptionsAlertQueries
except (ImportError, SyntaxError):
    class OptionsAlertQueries(graphene.ObjectType):
        pass

try:
    from .blockchain_queries import BlockchainQueries
except (ImportError, SyntaxError):
    class BlockchainQueries(graphene.ObjectType):
        pass

try:
    from .raha_queries import RAHAQueries
except (ImportError, SyntaxError):
    class RAHAQueries(graphene.ObjectType):
        pass

try:
    from .chan_quant_types import ChanQuantQueries, ChanQuantSignalsType
    CHAN_QUANT_AVAILABLE = True
except (ImportError, SyntaxError) as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"ChanQuantQueries not available: {e}")
    CHAN_QUANT_AVAILABLE = False
    class ChanQuantQueries(graphene.ObjectType):
        pass
    # Create a dummy type for the field definition
    class ChanQuantSignalsType(graphene.ObjectType):
        pass

try:
    from .raha_mutations import RAHAMutations
except (ImportError, SyntaxError):
    class RAHAMutations(graphene.ObjectType):
        pass

try:
    from .raha_advanced_mutations import RAHAAdvancedMutations
except (ImportError, SyntaxError):
    class RAHAAdvancedMutations(graphene.ObjectType):
        pass

try:
    from .transparency_types import TransparencyQueries
except (ImportError, SyntaxError) as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import TransparencyQueries: {e}")
    class TransparencyQueries(graphene.ObjectType):
        pass

try:
    from .speed_optimization_types import SpeedOptimizationQueries
except (ImportError, SyntaxError) as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import SpeedOptimizationQueries: {e}")
    class SpeedOptimizationQueries(graphene.ObjectType):
        pass

class ExtendedQuery(PremiumQueries, BrokerQueries, BankingQueries, SBLOCQueries, PaperTradingQueries, SocialQueries, PrivacyQueries, AIInsightsQueries, AIScansQueries, RiskManagementQueries, OptionsAlertQueries, BlockchainQueries, RAHAQueries, ChanQuantQueries, TransparencyQueries, SpeedOptimizationQueries, Query, graphene.ObjectType):
    """
    Final Query type exposed by the schema.

    - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
    - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
    - Adds Broker, Banking, and SBLOC queries
    - The base Query class has resolve_me which will be available here
    """
    
    # Explicitly expose chanQuantSignals to ensure it's available
    # This helps with MRO (Method Resolution Order) issues in multiple inheritance
    # Always define the field (even if unavailable) so GraphQL schema recognizes it
    chanQuantSignals = graphene.Field(
        ChanQuantSignalsType,
        symbol=graphene.String(required=True),
        description="Get Chan quantitative signals (mean reversion, momentum, Kelly, regime robustness) for a symbol"
    )
    
    def resolve_chanQuantSignals(self, info, symbol: str):
        """Delegate to ChanQuantQueries resolver"""
        # Call the resolver from ChanQuantQueries directly
        # This ensures the method is found even with complex MRO
        if not CHAN_QUANT_AVAILABLE:
            return None
        try:
            resolver = getattr(ChanQuantQueries, 'resolve_chanQuantSignals', None)
            if resolver:
                return resolver(self, info, symbol)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in resolve_chanQuantSignals: {e}", exc_info=True)
        return None
    
    # Legacy aliases for backward compatibility with mobile app
    # These map old field names to new canonical names
    
    alpaca_account = graphene.Field(
        BrokerAccountType,
        user_id=graphene.Int(required=True),
        name='alpacaAccount',
        description="Deprecated alias for brokerAccount. Use brokerAccount instead."
    )
    
    trading_account = graphene.Field(
        BrokerAccountType,
        name='tradingAccount',
        description="Deprecated alias for brokerAccount. Use brokerAccount instead."
    )
    
    trading_positions = graphene.List(
        BrokerPositionType,
        name='tradingPositions',
        description="Deprecated alias for brokerPositions. Use brokerPositions instead."
    )
    
    trading_orders = graphene.List(
        BrokerOrderType,
        status=graphene.String(),
        limit=graphene.Int(),
        name='tradingOrders',
        description="Deprecated alias for brokerOrders. Use brokerOrders instead."
    )
    
    # Stock chart data query
    stock_chart_data = graphene.Field(
        'core.types.StockChartDataType',
        symbol=graphene.String(required=True),
        timeframe=graphene.String(required=True),
        name='stockChartData',
        description="Get stock chart data (OHLCV) for a symbol and timeframe."
    )
    
    # Explicit resolvers for budgetData to ensure they're found
    # Copy the implementation directly to avoid MRO issues with multiple inheritance
    def resolve_budget_data(self, info):
        """Get user's budget data - direct implementation"""
        from .banking_types import BudgetDataType, BudgetCategoryType
        from .banking_models import BankTransaction
        
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            # Calculate budget from transactions
            transactions = BankTransaction.objects.filter(user=user)
            
            # Group by category
            categories = {}
            total_spent = 0
            
            for transaction in transactions:
                category = transaction.category or 'Other'
                amount = abs(float(transaction.amount)) if transaction.amount else 0
                
                if category not in categories:
                    categories[category] = {'spent': 0, 'budgeted': 0}
                
                categories[category]['spent'] += amount
                total_spent += amount
            
            # Create budget categories (simplified - would use actual budget settings)
            budget_categories = []
            for category, data in categories.items():
                budgeted = data['spent'] * 1.1  # 10% buffer
                percentage = (data['spent'] / budgeted * 100) if budgeted > 0 else 0
                
                budget_categories.append(BudgetCategoryType(
                    name=category,
                    budgeted=budgeted,
                    spent=data['spent'],
                    percentage=percentage
                ))
            
            # Calculate monthly income (simplified)
            monthly_income = 5000.0  # Would come from user profile or transactions
            monthly_expenses = total_spent
            remaining = monthly_income - monthly_expenses
            savings_rate = (remaining / monthly_income * 100) if monthly_income > 0 else 0
            
            # If no transactions, return mock data for development
            if not transactions.exists() or total_spent == 0:
                mock_categories = [
                    BudgetCategoryType(name='Housing', budgeted=1500, spent=1450, percentage=96.7),
                    BudgetCategoryType(name='Food', budgeted=600, spent=580, percentage=96.7),
                    BudgetCategoryType(name='Transportation', budgeted=400, spent=420, percentage=105),
                    BudgetCategoryType(name='Entertainment', budgeted=300, spent=250, percentage=83.3),
                    BudgetCategoryType(name='Utilities', budgeted=200, spent=180, percentage=90),
                    BudgetCategoryType(name='Other', budgeted=500, spent=620, percentage=124),
                ]
                return BudgetDataType(
                    monthlyIncome=5000.0,
                    monthlyExpenses=3500.0,
                    categories=mock_categories,
                    remaining=1500.0,
                    savingsRate=30.0
                )
            
            return BudgetDataType(
                monthlyIncome=monthly_income,
                monthlyExpenses=monthly_expenses,
                categories=budget_categories,
                remaining=remaining,
                savingsRate=savings_rate
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error resolving budget data: {e}", exc_info=True)
            # Return mock data on error for development
            mock_categories = [
                BudgetCategoryType(name='Housing', budgeted=1500, spent=1450, percentage=96.7),
                BudgetCategoryType(name='Food', budgeted=600, spent=580, percentage=96.7),
                BudgetCategoryType(name='Transportation', budgeted=400, spent=420, percentage=105),
                BudgetCategoryType(name='Entertainment', budgeted=300, spent=250, percentage=83.3),
                BudgetCategoryType(name='Utilities', budgeted=200, spent=180, percentage=90),
                BudgetCategoryType(name='Other', budgeted=500, spent=620, percentage=124),
            ]
            return BudgetDataType(
                monthlyIncome=5000.0,
                monthlyExpenses=3500.0,
                categories=mock_categories,
                remaining=1500.0,
                savingsRate=30.0
            )
    
    def resolve_budgetData(self, info):
        """CamelCase alias for budget_data - calls the ExtendedQuery version directly"""
        # Call the ExtendedQuery.resolve_budget_data method directly (not through inheritance)
        return ExtendedQuery.resolve_budget_data(self, info)
    
    # Explicit resolver for spendingAnalysis to ensure it's found
    def resolve_spending_analysis(self, info, period='month'):
        """Get spending analysis for a period - direct implementation"""
        from .banking_types import SpendingAnalysisType, SpendingCategoryType, TopMerchantType
        from .banking_models import BankTransaction
        from django.utils import timezone
        from datetime import timedelta
        
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            # Calculate date range based on period
            end_date = timezone.now().date()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            transactions = BankTransaction.objects.filter(
                user=user,
                posted_date__gte=start_date,
                posted_date__lte=end_date
            )
            
            # Group by category
            category_data = {}
            merchant_data = {}
            total_spent = 0
            
            for transaction in transactions:
                category = transaction.category or 'Other'
                merchant = transaction.merchant_name or 'Unknown'
                amount = abs(float(transaction.amount)) if transaction.amount else 0
                
                total_spent += amount
                
                # Category aggregation
                if category not in category_data:
                    category_data[category] = {'amount': 0, 'transactions': 0}
                category_data[category]['amount'] += amount
                category_data[category]['transactions'] += 1
                
                # Merchant aggregation
                if merchant not in merchant_data:
                    merchant_data[merchant] = {'amount': 0, 'count': 0}
                merchant_data[merchant]['amount'] += amount
                merchant_data[merchant]['count'] += 1
            
            # Create category list
            categories = []
            for category, data in category_data.items():
                percentage = (data['amount'] / total_spent * 100) if total_spent > 0 else 0
                categories.append(SpendingCategoryType(
                    name=category,
                    amount=data['amount'],
                    percentage=percentage,
                    transactions=data['transactions'],
                    trend='stable'  # Would calculate from historical data
                ))
            
            # Sort by amount descending
            categories.sort(key=lambda x: x.amount, reverse=True)
            
            # Create top merchants list
            top_merchants = []
            for merchant, data in sorted(merchant_data.items(), key=lambda x: x[1]['amount'], reverse=True)[:10]:
                top_merchants.append(TopMerchantType(
                    name=merchant,
                    amount=data['amount'],
                    count=data['count']
                ))
            
            # Create trends (simplified - would use historical data)
            trends = []
            
            # If no transactions, return mock data for development
            if not transactions.exists() or total_spent == 0:
                mock_categories = [
                    SpendingCategoryType(name='Housing', amount=1450, percentage=41.4, transactions=2, trend='stable'),
                    SpendingCategoryType(name='Food', amount=580, percentage=16.6, transactions=45, trend='up'),
                    SpendingCategoryType(name='Transportation', amount=420, percentage=12, transactions=12, trend='down'),
                    SpendingCategoryType(name='Entertainment', amount=250, percentage=7.1, transactions=8, trend='up'),
                    SpendingCategoryType(name='Utilities', amount=180, percentage=5.1, transactions=4, trend='stable'),
                    SpendingCategoryType(name='Other', amount=620, percentage=17.7, transactions=23, trend='up'),
                ]
                mock_merchants = [
                    TopMerchantType(name='Amazon', amount=320, count=15),
                    TopMerchantType(name='Whole Foods', amount=280, count=12),
                    TopMerchantType(name='Uber', amount=180, count=25),
                    TopMerchantType(name='Netflix', amount=15, count=1),
                ]
                return SpendingAnalysisType(
                    totalSpent=3500.0,
                    categories=mock_categories,
                    topMerchants=mock_merchants,
                    trends=trends
                )
            
            return SpendingAnalysisType(
                totalSpent=total_spent,
                categories=categories,
                topMerchants=top_merchants,
                trends=trends
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error resolving spending analysis: {e}", exc_info=True)
            # Return mock data on error for development
            mock_categories = [
                SpendingCategoryType(name='Housing', amount=1450, percentage=41.4, transactions=2, trend='stable'),
                SpendingCategoryType(name='Food', amount=580, percentage=16.6, transactions=45, trend='up'),
                SpendingCategoryType(name='Transportation', amount=420, percentage=12, transactions=12, trend='down'),
                SpendingCategoryType(name='Entertainment', amount=250, percentage=7.1, transactions=8, trend='up'),
                SpendingCategoryType(name='Utilities', amount=180, percentage=5.1, transactions=4, trend='stable'),
                SpendingCategoryType(name='Other', amount=620, percentage=17.7, transactions=23, trend='up'),
            ]
            mock_merchants = [
                TopMerchantType(name='Amazon', amount=320, count=15),
                TopMerchantType(name='Whole Foods', amount=280, count=12),
                TopMerchantType(name='Uber', amount=180, count=25),
                TopMerchantType(name='Netflix', amount=15, count=1),
            ]
            trends = []
            return SpendingAnalysisType(
                totalSpent=3500.0,
                categories=mock_categories,
                topMerchants=mock_merchants,
                trends=trends
            )
    
    def resolve_spendingAnalysis(self, info, period='month'):
        """CamelCase alias for spending_analysis - inline implementation to avoid MRO issues"""
        # Copy the implementation directly to avoid method resolution issues
        from .banking_types import SpendingAnalysisType, SpendingCategoryType, TopMerchantType
        from .banking_models import BankTransaction
        from django.utils import timezone
        from datetime import timedelta
        
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            # Calculate date range based on period
            end_date = timezone.now().date()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            transactions = BankTransaction.objects.filter(
                user=user,
                posted_date__gte=start_date,
                posted_date__lte=end_date
            )
            
            # Group by category
            category_data = {}
            merchant_data = {}
            total_spent = 0
            
            for transaction in transactions:
                category = transaction.category or 'Other'
                merchant = transaction.merchant_name or 'Unknown'
                amount = abs(float(transaction.amount)) if transaction.amount else 0
                
                total_spent += amount
                
                # Category aggregation
                if category not in category_data:
                    category_data[category] = {'amount': 0, 'transactions': 0}
                category_data[category]['amount'] += amount
                category_data[category]['transactions'] += 1
                
                # Merchant aggregation
                if merchant not in merchant_data:
                    merchant_data[merchant] = {'amount': 0, 'count': 0}
                merchant_data[merchant]['amount'] += amount
                merchant_data[merchant]['count'] += 1
            
            # Create category list
            categories = []
            for category, data in category_data.items():
                percentage = (data['amount'] / total_spent * 100) if total_spent > 0 else 0
                categories.append(SpendingCategoryType(
                    name=category,
                    amount=data['amount'],
                    percentage=percentage,
                    transactions=data['transactions'],
                    trend='stable'  # Would calculate from historical data
                ))
            
            # Sort by amount descending
            categories.sort(key=lambda x: x.amount, reverse=True)
            
            # Create top merchants list
            top_merchants = []
            for merchant, data in sorted(merchant_data.items(), key=lambda x: x[1]['amount'], reverse=True)[:10]:
                top_merchants.append(TopMerchantType(
                    name=merchant,
                    amount=data['amount'],
                    count=data['count']
                ))
            
            # Create trends (simplified - would use historical data)
            trends = []
            
            # If no transactions, return mock data for development
            if not transactions.exists() or total_spent == 0:
                mock_categories = [
                    SpendingCategoryType(name='Housing', amount=1450, percentage=41.4, transactions=2, trend='stable'),
                    SpendingCategoryType(name='Food', amount=580, percentage=16.6, transactions=45, trend='up'),
                    SpendingCategoryType(name='Transportation', amount=420, percentage=12, transactions=12, trend='down'),
                    SpendingCategoryType(name='Entertainment', amount=250, percentage=7.1, transactions=8, trend='up'),
                    SpendingCategoryType(name='Utilities', amount=180, percentage=5.1, transactions=4, trend='stable'),
                    SpendingCategoryType(name='Other', amount=620, percentage=17.7, transactions=23, trend='up'),
                ]
                mock_merchants = [
                    TopMerchantType(name='Amazon', amount=320, count=15),
                    TopMerchantType(name='Whole Foods', amount=280, count=12),
                    TopMerchantType(name='Uber', amount=180, count=25),
                    TopMerchantType(name='Netflix', amount=15, count=1),
                ]
                return SpendingAnalysisType(
                    totalSpent=3500.0,
                    categories=mock_categories,
                    topMerchants=mock_merchants,
                    trends=trends
                )
            
            return SpendingAnalysisType(
                totalSpent=total_spent,
                categories=categories,
                topMerchants=top_merchants,
                trends=trends
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error resolving spending analysis: {e}", exc_info=True)
            # Return mock data on error for development
            mock_categories = [
                SpendingCategoryType(name='Housing', amount=1450, percentage=41.4, transactions=2, trend='stable'),
                SpendingCategoryType(name='Food', amount=580, percentage=16.6, transactions=45, trend='up'),
                SpendingCategoryType(name='Transportation', amount=420, percentage=12, transactions=12, trend='down'),
                SpendingCategoryType(name='Entertainment', amount=250, percentage=7.1, transactions=8, trend='up'),
                SpendingCategoryType(name='Utilities', amount=180, percentage=5.1, transactions=4, trend='stable'),
                SpendingCategoryType(name='Other', amount=620, percentage=17.7, transactions=23, trend='up'),
            ]
            mock_merchants = [
                TopMerchantType(name='Amazon', amount=320, count=15),
                TopMerchantType(name='Whole Foods', amount=280, count=12),
                TopMerchantType(name='Uber', amount=180, count=25),
                TopMerchantType(name='Netflix', amount=15, count=1),
            ]
            trends = []
            return SpendingAnalysisType(
                totalSpent=3500.0,
                categories=mock_categories,
                topMerchants=mock_merchants,
                trends=trends
            )
    
    def resolve_alpaca_account(self, info, user_id):
        """Legacy alias: resolve alpacaAccount by delegating to brokerAccount"""
        # For now, just return the current user's broker account
        # The old API took user_id, but new API uses authenticated user
        user = info.context.user
        if not user.is_authenticated:
            return None
        return self.resolve_broker_account(info)
    
    def resolve_trading_account(self, info):
        """Legacy alias: resolve tradingAccount by delegating to brokerAccount"""
        return self.resolve_broker_account(info)
    
    def resolve_trading_positions(self, info, **kwargs):
        """Legacy alias: resolve tradingPositions by delegating to brokerPositions"""
        return self.resolve_broker_positions(info)
    
    def resolve_trading_orders(self, info, status=None, limit=None):
        """Legacy alias: resolve tradingOrders by delegating to brokerOrders"""
        return self.resolve_broker_orders(info, status=status, limit=limit or 50)
    
    def resolve_stock_chart_data(self, info, symbol, timeframe):
        """Resolve stockChartData - returns chart data in the format expected by frontend"""
        from .types import StockChartDataType, ChartDataPointType
        import asyncio
        from datetime import datetime, timedelta
        
        try:
            chart_data_points = []
            
            # Try to get real data from MarketDataAPIService
            try:
                from .queries import _get_intraday_data
                
                # Use existing _get_intraday_data function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    ohlcv_1m, ohlcv_5m = loop.run_until_complete(_get_intraday_data(symbol.upper()))
                    
                    # Use 5m data if available, otherwise 1m
                    ohlcv_data = ohlcv_5m if ohlcv_5m and len(ohlcv_5m) > 0 else ohlcv_1m
                    
                    if ohlcv_data and len(ohlcv_data) > 0:
                        # Convert to frontend format
                        for row in ohlcv_data[-100:]:  # Last 100 bars
                            if len(row) >= 6:  # timestamp, open, high, low, close, volume
                                timestamp_str = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                                chart_data_points.append(ChartDataPointType(
                                    timestamp=timestamp_str,
                                    open=float(row[1]),
                                    high=float(row[2]),
                                    low=float(row[3]),
                                    close=float(row[4]),
                                    volume=int(row[5]) if len(row) > 5 else 0
                                ))
                finally:
                    loop.close()
            except Exception as e:
                logger.warning(f"Failed to fetch real chart data for {symbol}: {e}")
            
            # Fallback: Generate mock data if no real data available
            if not chart_data_points:
                try:
                    from .market_data_api_service import MarketDataAPIService
                    async def get_current_price():
                        async with MarketDataAPIService() as service:
                            quote = await service.get_quote(symbol.upper())
                            return quote.get('price', 100.0) if quote else 100.0
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        current_price = loop.run_until_complete(get_current_price())
                    finally:
                        loop.close()
                except:
                    current_price = 100.0
                
                # Generate mock chart data
                import random
                now = datetime.now()
                base_price = current_price
                
                # Generate 100 data points
                for i in range(100, 0, -1):
                    timestamp = now - timedelta(minutes=i * 5)
                    # Random walk around base price
                    change = random.uniform(-0.02, 0.02) * base_price
                    base_price = base_price + change
                    
                    high = base_price * (1 + abs(random.uniform(0, 0.01)))
                    low = base_price * (1 - abs(random.uniform(0, 0.01)))
                    open_price = base_price * (1 + random.uniform(-0.005, 0.005))
                    close_price = base_price
                    volume = random.randint(100000, 1000000)
                    
                    chart_data_points.append(ChartDataPointType(
                        timestamp=timestamp.isoformat(),
                        open=round(open_price, 2),
                        high=round(high, 2),
                        low=round(low, 2),
                        close=round(close_price, 2),
                        volume=volume
                    ))
            
            # Return StockChartDataType object
            return StockChartDataType(
                symbol=symbol.upper(),
                data=chart_data_points
            )
            
        except Exception as e:
            logger.error(f"Error resolving stockChartData for {symbol}: {e}")
            # Return empty chart data on error
            return StockChartDataType(
                symbol=symbol.upper(),
                data=[]
            )


# ------------------- MUTATION ------------------

try:
    from .options_alert_mutations import OptionsAlertMutations
except (ImportError, SyntaxError):
    class OptionsAlertMutations(graphene.ObjectType):
        pass

class ExtendedMutation(PremiumMutations, BrokerMutations, BankingMutations, SBLOCMutations, PaperTradingMutations, SocialMutations, PrivacyMutations, AIInsightsMutations, OptionsAlertMutations, RAHAMutations, RAHAAdvancedMutations, Mutation, graphene.ObjectType):
    """
    Final Mutation type exposed by the schema.

    - Includes base mutations (create_user, add_to_watchlist, etc.)
    - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
    - Includes Broker, Banking, and SBLOC mutations
    """
    pass


# -------------------- SCHEMA --------------------

# Collect all types that need explicit registration
try:
    from .sbloc_types import SBLOCBankType, SBLOCSessionType
    SBLOC_TYPES_AVAILABLE = True
except ImportError:
    SBLOC_TYPES_AVAILABLE = False
    SBLOCBankType = None
    SBLOCSessionType = None

# Import Rust types explicitly to ensure they're registered
try:
    from .types import RustOptionsAnalysisType, ForexAnalysisType, SentimentAnalysisType, CorrelationAnalysisType
    RUST_TYPES_AVAILABLE = True
except ImportError:
    RUST_TYPES_AVAILABLE = False
    RustOptionsAnalysisType = None
    ForexAnalysisType = None
    SentimentAnalysisType = None
    CorrelationAnalysisType = None

schema_types = [BenchmarkSeriesType, BenchmarkDataPointType, PortfolioHistoryDataPointType]
if ProfileInput:
    # InputObjectType doesn't need to be in types, but ensure it's imported
    pass
if AIRecommendationsType:
    schema_types.append(AIRecommendationsType)
if SBLOC_TYPES_AVAILABLE and SBLOCBankType:
    schema_types.append(SBLOCBankType)
    if SBLOCSessionType:
        schema_types.append(SBLOCSessionType)
if RUST_TYPES_AVAILABLE and RustOptionsAnalysisType:
    schema_types.append(RustOptionsAnalysisType)
    if ForexAnalysisType:
        schema_types.append(ForexAnalysisType)
    if SentimentAnalysisType:
        schema_types.append(SentimentAnalysisType)
    if CorrelationAnalysisType:
        schema_types.append(CorrelationAnalysisType)

# Add Options Flow Type
try:
    from .options_flow_types import OptionsFlowType, UnusualActivityType, LargestTradeType, ScannedOptionType
    if OptionsFlowType:
        schema_types.append(OptionsFlowType)
    
    from .edge_prediction_types import EdgePredictionType
    if EdgePredictionType:
        schema_types.append(EdgePredictionType)
    
    from .one_tap_trade_types import OneTapTradeType, OneTapLegType
    if OneTapTradeType:
        schema_types.append(OneTapTradeType)
        schema_types.append(OneTapLegType)
    
    from .iv_forecast_types import IVSurfaceForecastType, IVChangePointType
    if IVSurfaceForecastType:
        schema_types.append(IVSurfaceForecastType)
        schema_types.append(IVChangePointType)
        schema_types.append(UnusualActivityType)
        schema_types.append(LargestTradeType)
        schema_types.append(ScannedOptionType)
except ImportError:
    pass

# Add Options Alert Types
try:
    from .options_alert_types import OptionsAlertType, OptionsAlertNotificationType
    if OptionsAlertType:
        schema_types.append(OptionsAlertType)
        schema_types.append(OptionsAlertNotificationType)
except ImportError:
    pass

# Add RAHA Types
try:
    from .raha_types import (
        StrategyType, StrategyVersionType, UserStrategySettingsType,
        RAHASignalType, RAHABacktestRunType, RAHAMetricsType, EquityPointType
    )
    schema_types.extend([
        StrategyType, StrategyVersionType, UserStrategySettingsType,
        RAHASignalType, RAHABacktestRunType, RAHAMetricsType, EquityPointType
    ])
except ImportError:
    pass

# Add Stock Chart Data Types
try:
    from .types import StockChartDataType, ChartDataPointType
    schema_types.extend([
        StockChartDataType, ChartDataPointType
    ])
except ImportError:
    pass

# Add Chan Quantitative Signal Types
try:
    from .chan_quant_types import (
        MeanReversionSignalType, MomentumSignalType, MomentumAlignmentType,
        KellyPositionSizeType, RegimeRobustnessScoreType, ChanQuantSignalsType
    )
    schema_types.extend([
        MeanReversionSignalType, MomentumSignalType, MomentumAlignmentType,
        KellyPositionSizeType, RegimeRobustnessScoreType, ChanQuantSignalsType
    ])
except ImportError:
    pass

# Add Speed Optimization Types
try:
    from .speed_optimization_types import LatencyStatsType, OptimizationStatusType
    schema_types.extend([
        LatencyStatsType, OptimizationStatusType
    ])
except ImportError:
    pass

schema = graphene.Schema(
    query=ExtendedQuery,
    mutation=ExtendedMutation,
    types=schema_types
)
