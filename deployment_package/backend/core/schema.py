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

try:
    from .graphql_repairs_resolvers import (
        PortfolioType, PositionType, RepairPlanType, PortfolioHealthType,
        FlightManualType, RepairHistoryType
    )
except (ImportError, SyntaxError) as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import repair types: {e}")
    # Create dummy types if import fails
    class PortfolioType(graphene.ObjectType):
        pass
    class PositionType(graphene.ObjectType):
        pass
    class RepairPlanType(graphene.ObjectType):
        pass
    class PortfolioHealthType(graphene.ObjectType):
        pass
    class FlightManualType(graphene.ObjectType):
        pass
    class RepairHistoryType(graphene.ObjectType):
        pass

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
    from .defi_queries import DefiQueries
except (ImportError, SyntaxError):
    class DefiQueries(graphene.ObjectType):
        pass

try:
    from .defi_mutations import DefiMutations
except (ImportError, SyntaxError):
    class DefiMutations(graphene.ObjectType):
        pass

try:
    from .crypto_queries import CryptoQueries
except (ImportError, SyntaxError):
    class CryptoQueries(graphene.ObjectType):
        pass

try:
    from .crypto_mutations import CryptoMutations
except (ImportError, SyntaxError):
    class CryptoMutations(graphene.ObjectType):
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

try:
    from .options_graphql_types import OptionsQueries
    OPTIONS_QUERIES_AVAILABLE = True
except (ImportError, SyntaxError) as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import OptionsQueries: {e}")
    OPTIONS_QUERIES_AVAILABLE = False
    class OptionsQueries(graphene.ObjectType):
        pass

try:
    from .graphql_repairs_resolvers import Query as RepairQueries
    REPAIR_QUERIES_AVAILABLE = True
except (ImportError, SyntaxError) as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import RepairQueries: {e}")
    REPAIR_QUERIES_AVAILABLE = False
    class RepairQueries(graphene.ObjectType):
        pass

try:
    from .graphql.queries import (
        TradingQuery,
        BudgetSpendingQuery,
        SocialQuery,
        MarketDataQuery,
        AnalyticsQuery,
        SecurityQuery,
        SignalsQuery,
        OptionsRustQuery,
        DiscussionsQuery,
    )
except (ImportError, SyntaxError) as e:
    logger.warning(f"GraphQL domain queries not available: {e}")
    class TradingQuery(graphene.ObjectType):
        pass
    class BudgetSpendingQuery(graphene.ObjectType):
        pass
    class SocialQuery(graphene.ObjectType):
        pass
    class MarketDataQuery(graphene.ObjectType):
        pass
    class AnalyticsQuery(graphene.ObjectType):
        pass
    class SecurityQuery(graphene.ObjectType):
        pass
    class SignalsQuery(graphene.ObjectType):
        pass
    class OptionsRustQuery(graphene.ObjectType):
        pass
    class DiscussionsQuery(graphene.ObjectType):
        pass

class ExtendedQuery(PremiumQueries, BrokerQueries, TradingQuery, BudgetSpendingQuery, SocialQuery, MarketDataQuery, AnalyticsQuery, SecurityQuery, SignalsQuery, OptionsRustQuery, DiscussionsQuery, BankingQueries, SBLOCQueries, PaperTradingQueries, SocialQueries, PrivacyQueries, AIInsightsQueries, AIScansQueries, RiskManagementQueries, OptionsAlertQueries, BlockchainQueries, DefiQueries, CryptoQueries, RAHAQueries, ChanQuantQueries, TransparencyQueries, SpeedOptimizationQueries, OptionsQueries, RepairQueries, Query, graphene.ObjectType):
    """
    Final Query type exposed by the schema.

    - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
    - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
    - Adds Broker, Banking, and SBLOC queries
    - The base Query class has resolve_me which will be available here
    """
    
    # Explicitly expose Phase 8 repairs queries to ensure they're available
    # This helps with MRO (Method Resolution Order) issues in multiple inheritance
    portfolio = graphene.Field(
        PortfolioType,
        user_id=graphene.String(required=True),
        account_id=graphene.String(required=True),
        description="Get portfolio summary with total Greeks and health status"
    )
    
    positions = graphene.List(
        PositionType,
        user_id=graphene.String(required=True),
        account_id=graphene.String(required=True),
        description="Get all open positions for user"
    )
    
    active_repair_plans = graphene.List(
        RepairPlanType,
        user_id=graphene.String(required=True),
        account_id=graphene.String(required=True),
        description="Get active repair plans available"
    )
    
    portfolio_health = graphene.Field(
        PortfolioHealthType,
        user_id=graphene.String(required=True),
        account_id=graphene.String(required=True),
        description="Get portfolio health snapshot"
    )
    
    repair_history = graphene.List(
        RepairHistoryType,
        user_id=graphene.String(required=True),
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
        description="Get historical repairs"
    )
    
    def resolve_portfolio(self, info, user_id: str, account_id: str):
        """Delegate to RepairQueries resolver"""
        resolver = getattr(RepairQueries, 'resolve_portfolio', None)
        if resolver:
            return resolver(self, info, user_id, account_id)
        return None
    
    def resolve_positions(self, info, user_id: str, account_id: str):
        """Delegate to RepairQueries resolver"""
        resolver = getattr(RepairQueries, 'resolve_positions', None)
        if resolver:
            return resolver(self, info, user_id, account_id)
        return None
    
    def resolve_active_repair_plans(self, info, user_id: str, account_id: str):
        """Delegate to RepairQueries resolver"""
        resolver = getattr(RepairQueries, 'resolve_active_repair_plans', None)
        if resolver:
            return resolver(self, info, user_id, account_id)
        return None
    
    def resolve_portfolio_health(self, info, user_id: str, account_id: str):
        """Delegate to RepairQueries resolver"""
        resolver = getattr(RepairQueries, 'resolve_portfolio_health', None)
        if resolver:
            return resolver(self, info, user_id, account_id)
        return None
    
    def resolve_repair_history(self, info, user_id: str, limit: int = 50, offset: int = 0):
        """Delegate to RepairQueries resolver"""
        resolver = getattr(RepairQueries, 'resolve_repair_history', None)
        if resolver:
            return resolver(self, info, user_id, limit, offset)
        return None
    
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
    
    # Legacy trading aliases live in core.graphql.queries.trading.TradingQuery.
    # budgetData / spendingAnalysis live in core.graphql.queries.banking.BudgetSpendingQuery.
    
# ------------------- MUTATION ------------------

try:
    from .options_alert_mutations import OptionsAlertMutations
except (ImportError, SyntaxError):
    class OptionsAlertMutations(graphene.ObjectType):
        pass

class ExtendedMutation(PremiumMutations, BrokerMutations, BankingMutations, SBLOCMutations, PaperTradingMutations, SocialMutations, PrivacyMutations, AIInsightsMutations, OptionsAlertMutations, DefiMutations, CryptoMutations, RAHAMutations, RAHAAdvancedMutations, Mutation, graphene.ObjectType):
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

# Add DeFi Types
try:
    from .defi_queries import (
        DefiReserveType, DefiAccountType,
        SupplyPositionType, BorrowPositionType,
        DeFiProtocolInfoType, DeFiChainInfoType, DeFiPoolSummaryType,
        DeFiPositionSummaryType, UserDeFiPositionType,
        AchievementType, PortfolioAnalyticsType, GhostWhisperType,
    )
    from .defi_mutations import (
        DefiPositionType, YieldPoolType, OptimizedPoolType,
        YieldOptimizerResultType, PoolAnalyticsPointType,
        StakeIntentResultType, RecordStakeTransactionResultType,
        ProtocolInfoType, ChainInfoType, PoolSummaryType,
        PositionSummaryType, ActionSummaryType
    )
    schema_types.extend([
        DefiReserveType, DefiAccountType, DefiPositionType,
        SupplyPositionType, BorrowPositionType,
        DeFiProtocolInfoType, DeFiChainInfoType, DeFiPoolSummaryType,
        DeFiPositionSummaryType, UserDeFiPositionType,
        YieldPoolType, OptimizedPoolType, YieldOptimizerResultType,
        PoolAnalyticsPointType, StakeIntentResultType, RecordStakeTransactionResultType,
        ProtocolInfoType, ChainInfoType, PoolSummaryType,
        PositionSummaryType, ActionSummaryType,
        AchievementType, PortfolioAnalyticsType, GhostWhisperType,
    ])
except ImportError:
    pass

# Add Crypto Types
try:
    from .crypto_queries import (
        CryptocurrencyType, CryptoPriceType, CryptoMlSignalType,
        CryptoRecommendationType, CryptoSblocLoanType, CryptoHoldingType,
        CryptoPortfolioType
    )
    from .crypto_mutations import (
        AlpacaCryptoAccountType, AlpacaCryptoBalanceType,
        AlpacaCryptoOrderType, CreateAlpacaCryptoOrderResultType,
        CancelAlpacaCryptoOrderResultType
    )
    schema_types.extend([
        CryptocurrencyType, CryptoPriceType, CryptoMlSignalType,
        CryptoRecommendationType, CryptoSblocLoanType, CryptoHoldingType,
        CryptoPortfolioType, AlpacaCryptoAccountType, AlpacaCryptoBalanceType,
        AlpacaCryptoOrderType, CreateAlpacaCryptoOrderResultType,
        CancelAlpacaCryptoOrderResultType
    ])
except ImportError:
    pass

schema = graphene.Schema(
    query=ExtendedQuery,
    mutation=ExtendedMutation,
    types=schema_types
)
