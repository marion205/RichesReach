import graphene
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from django.contrib.auth import get_user_model
from .real_market_data_service import real_market_data_service
from .advanced_analytics_service import advanced_analytics_service
from .custom_benchmark_service import custom_benchmark_service

User = get_user_model()
logger = logging.getLogger(__name__)

class BenchmarkDataPoint(graphene.ObjectType):
    """Single data point for benchmark performance"""
    timestamp = graphene.String(description="ISO timestamp of the data point")
    value = graphene.Float(description="Benchmark value at this timestamp")
    change = graphene.Float(description="Change from previous point")
    changePercent = graphene.Float(description="Percentage change from previous point")

class BenchmarkAnalytics(graphene.ObjectType):
    """Advanced analytics for benchmark performance"""
    # Basic metrics
    portfolioReturn = graphene.Float(description="Portfolio return percentage")
    benchmarkReturn = graphene.Float(description="Benchmark return percentage")
    excessReturn = graphene.Float(description="Excess return percentage")
    
    # Risk metrics
    portfolioVolatility = graphene.Float(description="Portfolio volatility")
    benchmarkVolatility = graphene.Float(description="Benchmark volatility")
    trackingError = graphene.Float(description="Tracking error")
    maxDrawdown = graphene.Float(description="Maximum drawdown")
    benchmarkMaxDrawdown = graphene.Float(description="Benchmark maximum drawdown")
    
    # Risk-adjusted metrics
    sharpeRatio = graphene.Float(description="Portfolio Sharpe ratio")
    benchmarkSharpeRatio = graphene.Float(description="Benchmark Sharpe ratio")
    informationRatio = graphene.Float(description="Information ratio")
    sortinoRatio = graphene.Float(description="Sortino ratio")
    calmarRatio = graphene.Float(description="Calmar ratio")
    
    # Correlation and beta
    beta = graphene.Float(description="Beta relative to benchmark")
    correlation = graphene.Float(description="Correlation coefficient")
    rSquared = graphene.Float(description="R-squared")
    
    # Advanced metrics
    alpha = graphene.Float(description="Alpha")
    treynorRatio = graphene.Float(description="Treynor ratio")
    jensenAlpha = graphene.Float(description="Jensen's alpha")
    m2Measure = graphene.Float(description="M2 measure")
    m2Alpha = graphene.Float(description="M2 alpha")
    
    # Downside risk metrics
    downsideDeviation = graphene.Float(description="Downside deviation")
    upsideCapture = graphene.Float(description="Upside capture ratio")
    downsideCapture = graphene.Float(description="Downside capture ratio")
    
    # Tail risk metrics
    var95 = graphene.Float(description="95% Value at Risk")
    var99 = graphene.Float(description="99% Value at Risk")
    cvar95 = graphene.Float(description="95% Conditional VaR")
    cvar99 = graphene.Float(description="99% Conditional VaR")
    
    # Distribution metrics
    skewness = graphene.Float(description="Skewness")
    kurtosis = graphene.Float(description="Kurtosis")
    excessKurtosis = graphene.Float(description="Excess kurtosis")
    
    # Performance attribution
    activeReturn = graphene.Float(description="Active return")
    activeRisk = graphene.Float(description="Active risk")
    activeShare = graphene.Float(description="Active share")
    
    # Time period analysis
    winRate = graphene.Float(description="Win rate percentage")
    averageWin = graphene.Float(description="Average win")
    averageLoss = graphene.Float(description="Average loss")
    profitFactor = graphene.Float(description="Profit factor")

class BenchmarkHolding(graphene.ObjectType):
    """Individual holding in a custom benchmark"""
    symbol = graphene.String(description="Stock symbol")
    weight = graphene.Float(description="Weight in portfolio")
    name = graphene.String(description="Company name")
    sector = graphene.String(description="Sector classification")
    description = graphene.String(description="Additional description")

class CustomBenchmark(graphene.ObjectType):
    """Custom benchmark portfolio"""
    id = graphene.ID(description="Custom benchmark ID")
    name = graphene.String(description="Benchmark name")
    description = graphene.String(description="Benchmark description")
    holdings = graphene.List(BenchmarkHolding, description="Portfolio holdings")
    totalHoldings = graphene.Int(description="Total number of holdings")
    totalWeight = graphene.Float(description="Total weight (should be 1.0)")
    createdAt = graphene.String(description="Creation timestamp")
    updatedAt = graphene.String(description="Last update timestamp")

class BenchmarkSeries(graphene.ObjectType):
    """Complete benchmark series for a timeframe"""
    symbol = graphene.String(description="Benchmark symbol (e.g., SPY, QQQ)")
    name = graphene.String(description="Human-readable benchmark name")
    timeframe = graphene.String(description="Timeframe (1D, 1W, 1M, 3M, 1Y, All)")
    dataPoints = graphene.List(BenchmarkDataPoint, description="Array of data points")
    startValue = graphene.Float(description="Starting value of the series")
    endValue = graphene.Float(description="Ending value of the series")
    totalReturn = graphene.Float(description="Total return for the period")
    totalReturnPercent = graphene.Float(description="Total return percentage for the period")
    volatility = graphene.Float(description="Volatility (standard deviation) of returns")
    sharpeRatio = graphene.Float(description="Sharpe ratio")
    maxDrawdown = graphene.Float(description="Maximum drawdown")
    source = graphene.String(description="Data source (yahoo_finance, alpha_vantage, etc.)")
    analytics = graphene.Field(BenchmarkAnalytics, description="Advanced analytics")
    holdings = graphene.List(BenchmarkHolding, description="Holdings (for custom benchmarks)")

class BenchmarkQuery(graphene.ObjectType):
    """GraphQL queries for benchmark data"""
    
    benchmarkSeries = graphene.Field(
        BenchmarkSeries,
        symbol=graphene.String(required=True, description="Benchmark symbol (SPY, QQQ, etc.)"),
        timeframe=graphene.String(required=True, description="Timeframe (1D, 1W, 1M, 3M, 1Y, All)"),
        useRealData=graphene.Boolean(default_value=True, description="Whether to use real market data"),
        description="Get benchmark performance data for a specific symbol and timeframe"
    )
    
    availableBenchmarks = graphene.List(
        graphene.String,
        description="Get list of available benchmark symbols"
    )
    
    customBenchmarks = graphene.List(
        CustomBenchmark,
        description="Get user's custom benchmarks"
    )
    
    customBenchmark = graphene.Field(
        CustomBenchmark,
        id=graphene.ID(required=True, description="Custom benchmark ID"),
        description="Get a specific custom benchmark"
    )
    
    predefinedBenchmarks = graphene.List(
        graphene.JSONString,
        description="Get list of predefined benchmark portfolios"
    )
    
    benchmarkAnalytics = graphene.Field(
        BenchmarkAnalytics,
        portfolioData=graphene.JSONString(required=True, description="Portfolio performance data"),
        benchmarkData=graphene.JSONString(required=True, description="Benchmark performance data"),
        description="Get advanced analytics comparing portfolio to benchmark"
    )

    def resolve_benchmarkSeries(self, info, symbol: str, timeframe: str, useRealData: bool = True):
        """Resolve benchmark series data"""
        try:
            # Validate timeframe
            valid_timeframes = ['1D', '1W', '1M', '3M', '1Y', 'All']
            if timeframe not in valid_timeframes:
                raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}")
            
            # Check if it's a custom benchmark
            if symbol.startswith('CUSTOM_'):
                custom_id = symbol.replace('CUSTOM_', '')
                user = getattr(info.context, 'user', None)
                if not user or not user.is_authenticated:
                    logger.warning("Authentication required for custom benchmarks")
                    return None
                
                series_data = custom_benchmark_service.get_custom_benchmark_data(int(custom_id), user, timeframe)
            else:
                # Use real market data if requested
                if useRealData:
                    series_data = real_market_data_service.get_benchmark_data(symbol, timeframe)
                
                # Fallback to mock data if real data fails
                if not series_data:
                    from .benchmark_service import BenchmarkService
                    benchmark_service = BenchmarkService()
                    series_data = benchmark_service.get_benchmark_series(symbol, timeframe)
            
            if not series_data:
                logger.warning(f"No benchmark data found for {symbol} {timeframe}")
                return None
            
            # Create holdings list for custom benchmarks
            holdings = None
            if 'holdings' in series_data:
                holdings = [
                    BenchmarkHolding(
                        symbol=holding['symbol'],
                        weight=holding['weight'],
                        name=holding.get('name', ''),
                        sector=holding.get('sector', ''),
                        description=holding.get('description', '')
                    ) for holding in series_data['holdings']
                ]
                
            return BenchmarkSeries(
                symbol=series_data['symbol'],
                name=series_data['name'],
                timeframe=timeframe,
                dataPoints=[
                    BenchmarkDataPoint(
                        timestamp=point['timestamp'],
                        value=point['value'],
                        change=point.get('change', 0),
                        changePercent=point.get('changePercent', 0)
                    ) for point in series_data['dataPoints']
                ],
                startValue=series_data['startValue'],
                endValue=series_data['endValue'],
                totalReturn=series_data['totalReturn'],
                totalReturnPercent=series_data['totalReturnPercent'],
                volatility=series_data.get('volatility', 0),
                sharpeRatio=series_data.get('sharpeRatio', 0),
                maxDrawdown=series_data.get('maxDrawdown', 0),
                source=series_data.get('source', 'mock'),
                analytics=None,  # Will be calculated separately if needed
                holdings=holdings
            )
            
        except Exception as e:
            logger.error(f"Error resolving benchmark series for {symbol} {timeframe}: {e}")
            return None

    def resolve_availableBenchmarks(self, info):
        """Resolve list of available benchmark symbols"""
        return ['SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO', 'AGG', 'TLT', 'GLD', 'SLV']
    
    def resolve_customBenchmarks(self, info):
        """Resolve user's custom benchmarks"""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            logger.warning("Authentication required for custom benchmarks")
            return []
        
        try:
            custom_benchmarks = custom_benchmark_service.get_user_custom_benchmarks(user)
            return [
                CustomBenchmark(
                    id=str(benchmark.id),
                    name=benchmark.name,
                    description=benchmark.description,
                    holdings=[
                        BenchmarkHolding(
                            symbol=holding.symbol,
                            weight=float(holding.weight),
                            name=holding.name,
                            sector=holding.sector,
                            description=holding.description
                        ) for holding in benchmark.holdings.all()
                    ],
                    totalHoldings=benchmark.total_holdings,
                    totalWeight=float(benchmark.total_weight),
                    createdAt=benchmark.created_at.isoformat(),
                    updatedAt=benchmark.updated_at.isoformat()
                ) for benchmark in custom_benchmarks
            ]
        except Exception as e:
            logger.error(f"Error resolving custom benchmarks: {e}")
            return []
    
    def resolve_customBenchmark(self, info, id: str):
        """Resolve a specific custom benchmark"""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            logger.warning("Authentication required for custom benchmark")
            return None
        
        try:
            from .models_custom_benchmark import CustomBenchmark as CustomBenchmarkModel
            benchmark = CustomBenchmarkModel.objects.get(id=int(id), user=user)
            
            return CustomBenchmark(
                id=str(benchmark.id),
                name=benchmark.name,
                description=benchmark.description,
                holdings=[
                    BenchmarkHolding(
                        symbol=holding.symbol,
                        weight=float(holding.weight),
                        name=holding.name,
                        sector=holding.sector,
                        description=holding.description
                    ) for holding in benchmark.holdings.all()
                ],
                totalHoldings=benchmark.total_holdings,
                totalWeight=float(benchmark.total_weight),
                createdAt=benchmark.created_at.isoformat(),
                updatedAt=benchmark.updated_at.isoformat()
            )
        except Exception as e:
            logger.error(f"Error resolving custom benchmark {id}: {e}")
            return None
    
    def resolve_predefinedBenchmarks(self, info):
        """Resolve predefined benchmark portfolios"""
        try:
            return custom_benchmark_service.get_predefined_benchmarks()
        except Exception as e:
            logger.error(f"Error resolving predefined benchmarks: {e}")
            return []
    
    def resolve_benchmarkAnalytics(self, info, portfolioData: dict, benchmarkData: dict):
        """Resolve advanced analytics comparing portfolio to benchmark"""
        try:
            metrics = advanced_analytics_service.calculate_comprehensive_metrics(portfolioData, benchmarkData)
            
            return BenchmarkAnalytics(
                # Basic metrics
                portfolioReturn=metrics['portfolioReturn'],
                benchmarkReturn=metrics['benchmarkReturn'],
                excessReturn=metrics['excessReturn'],
                
                # Risk metrics
                portfolioVolatility=metrics['portfolioVolatility'],
                benchmarkVolatility=metrics['benchmarkVolatility'],
                trackingError=metrics['trackingError'],
                maxDrawdown=metrics['maxDrawdown'],
                benchmarkMaxDrawdown=metrics['benchmarkMaxDrawdown'],
                
                # Risk-adjusted metrics
                sharpeRatio=metrics['sharpeRatio'],
                benchmarkSharpeRatio=metrics['benchmarkSharpeRatio'],
                informationRatio=metrics['informationRatio'],
                sortinoRatio=metrics['sortinoRatio'],
                calmarRatio=metrics['calmarRatio'],
                
                # Correlation and beta
                beta=metrics['beta'],
                correlation=metrics['correlation'],
                rSquared=metrics['rSquared'],
                
                # Advanced metrics
                alpha=metrics['alpha'],
                treynorRatio=metrics['treynorRatio'],
                jensenAlpha=metrics['jensenAlpha'],
                m2Measure=metrics['m2Measure'],
                m2Alpha=metrics['m2Alpha'],
                
                # Downside risk metrics
                downsideDeviation=metrics['downsideDeviation'],
                upsideCapture=metrics['upsideCapture'],
                downsideCapture=metrics['downsideCapture'],
                
                # Tail risk metrics
                var95=metrics['var95'],
                var99=metrics['var99'],
                cvar95=metrics['cvar95'],
                cvar99=metrics['cvar99'],
                
                # Distribution metrics
                skewness=metrics['skewness'],
                kurtosis=metrics['kurtosis'],
                excessKurtosis=metrics['excessKurtosis'],
                
                # Performance attribution
                activeReturn=metrics['activeReturn'],
                activeRisk=metrics['activeRisk'],
                activeShare=metrics['activeShare'],
                
                # Time period analysis
                winRate=metrics['winRate'],
                averageWin=metrics['averageWin'],
                averageLoss=metrics['averageLoss'],
                profitFactor=metrics['profitFactor']
            )
        except Exception as e:
            logger.error(f"Error resolving benchmark analytics: {e}")
            return None

# Input types for mutations
class BenchmarkHoldingInput(graphene.InputObjectType):
    symbol = graphene.String(required=True, description="Stock symbol")
    weight = graphene.Float(required=True, description="Weight in portfolio (0.0 to 1.0)")
    name = graphene.String(description="Company name")
    sector = graphene.String(description="Sector classification")
    description = graphene.String(description="Additional description")

# Mutations
class CreateCustomBenchmark(graphene.Mutation):
    """Create a new custom benchmark portfolio"""
    
    class Arguments:
        name = graphene.String(required=True, description="Benchmark name")
        description = graphene.String(description="Benchmark description")
        holdings = graphene.List(BenchmarkHoldingInput, required=True, description="Portfolio holdings")
    
    success = graphene.Boolean()
    benchmark = graphene.Field(CustomBenchmark)
    error = graphene.String()
    
    def mutate(self, info, name: str, holdings: List[BenchmarkHoldingInput], description: str = ""):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return CreateCustomBenchmark(
                success=False,
                error="Authentication required"
            )
        
        try:
            # Convert holdings to dict format
            holdings_data = [
                {
                    'symbol': holding.symbol,
                    'weight': holding.weight,
                    'name': holding.name or '',
                    'sector': holding.sector or '',
                    'description': holding.description or ''
                }
                for holding in holdings
            ]
            
            benchmark = custom_benchmark_service.create_custom_benchmark(
                user=user,
                name=name,
                description=description,
                holdings=holdings_data
            )
            
            if benchmark:
                return CreateCustomBenchmark(
                    success=True,
                    benchmark=CustomBenchmark(
                        id=str(benchmark.id),
                        name=benchmark.name,
                        description=benchmark.description,
                        holdings=[
                            BenchmarkHolding(
                                symbol=holding.symbol,
                                weight=float(holding.weight),
                                name=holding.name,
                                sector=holding.sector,
                                description=holding.description
                            ) for holding in benchmark.holdings.all()
                        ],
                        totalHoldings=benchmark.total_holdings,
                        totalWeight=float(benchmark.total_weight),
                        createdAt=benchmark.created_at.isoformat(),
                        updatedAt=benchmark.updated_at.isoformat()
                    ),
                    error=None
                )
            else:
                return CreateCustomBenchmark(
                    success=False,
                    error="Failed to create custom benchmark"
                )
                
        except Exception as e:
            logger.error(f"Error creating custom benchmark: {e}")
            return CreateCustomBenchmark(
                success=False,
                error=f"Error creating custom benchmark: {str(e)}"
            )

class UpdateCustomBenchmark(graphene.Mutation):
    """Update an existing custom benchmark portfolio"""
    
    class Arguments:
        id = graphene.ID(required=True, description="Custom benchmark ID")
        name = graphene.String(description="Benchmark name")
        description = graphene.String(description="Benchmark description")
        holdings = graphene.List(BenchmarkHoldingInput, description="Portfolio holdings")
    
    success = graphene.Boolean()
    benchmark = graphene.Field(CustomBenchmark)
    error = graphene.String()
    
    def mutate(self, info, id: str, name: str = None, description: str = None, holdings: List[BenchmarkHoldingInput] = None):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return UpdateCustomBenchmark(
                success=False,
                error="Authentication required"
            )
        
        try:
            # Convert holdings to dict format if provided
            holdings_data = None
            if holdings:
                holdings_data = [
                    {
                        'symbol': holding.symbol,
                        'weight': holding.weight,
                        'name': holding.name or '',
                        'sector': holding.sector or '',
                        'description': holding.description or ''
                    }
                    for holding in holdings
                ]
            
            benchmark = custom_benchmark_service.update_custom_benchmark(
                benchmark_id=int(id),
                user=user,
                name=name,
                description=description,
                holdings=holdings_data
            )
            
            if benchmark:
                return UpdateCustomBenchmark(
                    success=True,
                    benchmark=CustomBenchmark(
                        id=str(benchmark.id),
                        name=benchmark.name,
                        description=benchmark.description,
                        holdings=[
                            BenchmarkHolding(
                                symbol=holding.symbol,
                                weight=float(holding.weight),
                                name=holding.name,
                                sector=holding.sector,
                                description=holding.description
                            ) for holding in benchmark.holdings.all()
                        ],
                        totalHoldings=benchmark.total_holdings,
                        totalWeight=float(benchmark.total_weight),
                        createdAt=benchmark.created_at.isoformat(),
                        updatedAt=benchmark.updated_at.isoformat()
                    ),
                    error=None
                )
            else:
                return UpdateCustomBenchmark(
                    success=False,
                    error="Failed to update custom benchmark"
                )
                
        except Exception as e:
            logger.error(f"Error updating custom benchmark: {e}")
            return UpdateCustomBenchmark(
                success=False,
                error=f"Error updating custom benchmark: {str(e)}"
            )

class DeleteCustomBenchmark(graphene.Mutation):
    """Delete a custom benchmark portfolio"""
    
    class Arguments:
        id = graphene.ID(required=True, description="Custom benchmark ID")
    
    success = graphene.Boolean()
    error = graphene.String()
    
    def mutate(self, info, id: str):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return DeleteCustomBenchmark(
                success=False,
                error="Authentication required"
            )
        
        try:
            success = custom_benchmark_service.delete_custom_benchmark(int(id), user)
            
            if success:
                return DeleteCustomBenchmark(
                    success=True,
                    error=None
                )
            else:
                return DeleteCustomBenchmark(
                    success=False,
                    error="Failed to delete custom benchmark"
                )
                
        except Exception as e:
            logger.error(f"Error deleting custom benchmark: {e}")
            return DeleteCustomBenchmark(
                success=False,
                error=f"Error deleting custom benchmark: {str(e)}"
            )

class CreatePredefinedBenchmark(graphene.Mutation):
    """Create a predefined benchmark portfolio for a user"""
    
    class Arguments:
        benchmarkName = graphene.String(required=True, description="Name of predefined benchmark")
    
    success = graphene.Boolean()
    benchmark = graphene.Field(CustomBenchmark)
    error = graphene.String()
    
    def mutate(self, info, benchmarkName: str):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return CreatePredefinedBenchmark(
                success=False,
                error="Authentication required"
            )
        
        try:
            benchmark = custom_benchmark_service.create_predefined_benchmark(user, benchmarkName)
            
            if benchmark:
                return CreatePredefinedBenchmark(
                    success=True,
                    benchmark=CustomBenchmark(
                        id=str(benchmark.id),
                        name=benchmark.name,
                        description=benchmark.description,
                        holdings=[
                            BenchmarkHolding(
                                symbol=holding.symbol,
                                weight=float(holding.weight),
                                name=holding.name,
                                sector=holding.sector,
                                description=holding.description
                            ) for holding in benchmark.holdings.all()
                        ],
                        totalHoldings=benchmark.total_holdings,
                        totalWeight=float(benchmark.total_weight),
                        createdAt=benchmark.created_at.isoformat(),
                        updatedAt=benchmark.updated_at.isoformat()
                    ),
                    error=None
                )
            else:
                return CreatePredefinedBenchmark(
                    success=False,
                    error="Failed to create predefined benchmark"
                )
                
        except Exception as e:
            logger.error(f"Error creating predefined benchmark: {e}")
            return CreatePredefinedBenchmark(
                success=False,
                error=f"Error creating predefined benchmark: {str(e)}"
            )

class BenchmarkMutation(graphene.ObjectType):
    """GraphQL mutations for benchmark operations"""
    
    createCustomBenchmark = CreateCustomBenchmark.Field(description="Create a new custom benchmark portfolio")
    updateCustomBenchmark = UpdateCustomBenchmark.Field(description="Update an existing custom benchmark portfolio")
    deleteCustomBenchmark = DeleteCustomBenchmark.Field(description="Delete a custom benchmark portfolio")
    createPredefinedBenchmark = CreatePredefinedBenchmark.Field(description="Create a predefined benchmark portfolio")
