import graphene
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from django.contrib.auth import get_user_model
from .real_market_data_service import real_market_data_service
from .advanced_analytics_service import advanced_analytics_service
from .custom_benchmark_service import custom_benchmark_service
from .advanced_dashboard_service import advanced_dashboard_service
from .portfolio_optimization_service import portfolio_optimization_service
from .performance_attribution_service import performance_attribution_service
from .smart_alerts_service import smart_alerts_service
from .ml_anomaly_service import ml_anomaly_service
from .alert_delivery_service import alert_delivery_service

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
    
    advancedDashboard = graphene.Field(
        graphene.JSONString,
        portfolioId=graphene.String(description="Portfolio ID"),
        timeframe=graphene.String(default_value="1Y", description="Analysis timeframe"),
        description="Get comprehensive dashboard data for advanced visualization"
    )
    
    portfolioOptimization = graphene.Field(
        graphene.JSONString,
        symbols=graphene.List(graphene.String, required=True, description="List of symbols to optimize"),
        optimizationType=graphene.String(default_value="max_sharpe", description="Optimization method"),
        constraints=graphene.JSONString(description="Optimization constraints"),
        riskFreeRate=graphene.Float(default_value=0.02, description="Risk-free rate"),
        targetReturn=graphene.Float(description="Target return for optimization"),
        targetVolatility=graphene.Float(description="Target volatility for optimization"),
        description="Optimize portfolio using various methods"
    )
    
    efficientFrontier = graphene.Field(
        graphene.JSONString,
        symbols=graphene.List(graphene.String, required=True, description="List of symbols"),
        numPortfolios=graphene.Int(default_value=100, description="Number of portfolios to generate"),
        description="Generate efficient frontier"
    )
    
    performanceAttribution = graphene.Field(
        graphene.JSONString,
        portfolioId=graphene.String(required=True, description="Portfolio ID"),
        benchmarkId=graphene.String(required=True, description="Benchmark ID"),
        timeframe=graphene.String(default_value="1Y", description="Analysis timeframe"),
        description="Get detailed performance attribution analysis"
    )
    
    smartAlerts = graphene.Field(
        graphene.JSONString,
        portfolioId=graphene.String(description="Portfolio ID"),
        timeframe=graphene.String(default_value="1M", description="Analysis timeframe"),
        description="Get intelligent portfolio coaching alerts and insights"
    )
    
    alertCategories = graphene.Field(
        graphene.JSONString,
        description="Get available alert categories and their descriptions"
    )
    
    alertPreferences = graphene.Field(
        graphene.JSONString,
        description="Get user's alert preferences and settings"
    )
    
    mlAnomalies = graphene.Field(
        graphene.List(graphene.JSONString),
        portfolio_id=graphene.String(),
        timeframe=graphene.String(default_value='30d'),
        description="Get ML-detected anomalies in user's portfolio behavior"
    )
    
    deliveryPreferences = graphene.Field(
        graphene.JSONString,
        description="Get user's delivery preferences for different alert types"
    )
    
    deliveryHistory = graphene.Field(
        graphene.List(graphene.JSONString),
        alert_id=graphene.String(),
        description="Get delivery history for a specific alert"
    )

    def resolve_benchmarkSeries(self, info, symbol: str, timeframe: str, useRealData: bool = True):
        """Resolve benchmark series data"""
        try:
            # Validate timeframe
            valid_timeframes = ['1D', '1W', '1M', '3M', '6M', '1Y', 'All']
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
    
    def resolve_advancedDashboard(self, info, portfolioId: str = None, timeframe: str = "1Y"):
        """Resolve advanced dashboard data"""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            logger.warning("Authentication required for advanced dashboard")
            return None
        
        try:
            dashboard_data = advanced_dashboard_service.get_comprehensive_dashboard_data(
                user=user,
                portfolio_id=portfolioId,
                timeframe=timeframe
            )
            return dashboard_data
        except Exception as e:
            logger.error(f"Error resolving advanced dashboard: {e}")
            return None
    
    def resolve_portfolioOptimization(self, info, symbols: List[str], optimizationType: str = "max_sharpe",
                                    constraints: Dict = None, riskFreeRate: float = 0.02,
                                    targetReturn: float = None, targetVolatility: float = None):
        """Resolve portfolio optimization"""
        try:
            optimization_result = portfolio_optimization_service.optimize_portfolio(
                symbols=symbols,
                optimization_type=optimizationType,
                constraints=constraints,
                risk_free_rate=riskFreeRate,
                target_return=targetReturn,
                target_volatility=targetVolatility
            )
            return optimization_result
        except Exception as e:
            logger.error(f"Error resolving portfolio optimization: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def resolve_efficientFrontier(self, info, symbols: List[str], numPortfolios: int = 100):
        """Resolve efficient frontier"""
        try:
            frontier_data = portfolio_optimization_service.generate_efficient_frontier(
                symbols=symbols,
                num_portfolios=numPortfolios
            )
            return frontier_data
        except Exception as e:
            logger.error(f"Error resolving efficient frontier: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def resolve_performanceAttribution(self, info, portfolioId: str, benchmarkId: str, timeframe: str = "1Y"):
        """Resolve performance attribution analysis"""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            logger.warning("Authentication required for performance attribution")
            return None
        
        try:
            attribution_data = performance_attribution_service.get_comprehensive_attribution(
                user=user,
                portfolio_id=portfolioId,
                benchmark_id=benchmarkId,
                timeframe=timeframe
            )
            return attribution_data
        except Exception as e:
            logger.error(f"Error resolving performance attribution: {e}")
            return None
    
    def resolve_smartAlerts(self, info, portfolioId: str = None, timeframe: str = "1M"):
        """Resolve smart alerts for portfolio coaching"""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            logger.warning("Authentication required for smart alerts")
            return None
        
        try:
            alerts = smart_alerts_service.generate_smart_alerts(
                user=user,
                portfolio_id=portfolioId,
                timeframe=timeframe
            )
            return alerts
        except Exception as e:
            logger.error(f"Error resolving smart alerts: {e}")
            return []
    
    def resolve_alertCategories(self, info):
        """Resolve available alert categories"""
        try:
            categories = smart_alerts_service.get_alert_categories()
            return categories
        except Exception as e:
            logger.error(f"Error resolving alert categories: {e}")
            return []
    
    def resolve_alertPreferences(self, info):
        """Resolve user's alert preferences"""
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            logger.warning("Authentication required for alert preferences")
            return None
        
        try:
            preferences = smart_alerts_service.get_user_alert_preferences(user)
            return preferences
        except Exception as e:
            logger.error(f"Error resolving alert preferences: {e}")
            return None
    
    def resolve_mlAnomalies(self, info, portfolio_id: str = None, timeframe: str = '30d'):
        """Resolve ML-detected anomalies"""
        try:
            user = getattr(info.context, 'user', None)
            if not user or not user.is_authenticated:
                logger.warning("Authentication required for ML anomalies")
                return []
            
            # Get ML anomalies (synchronous call for now)
            # Note: In production, you might want to use Django Channels or Celery for async processing
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                anomalies = loop.run_until_complete(
                    ml_anomaly_service.detect_anomalies(user, portfolio_id, timeframe)
                )
            except RuntimeError:
                # If no event loop is running, create a new one
                anomalies = asyncio.run(
                    ml_anomaly_service.detect_anomalies(user, portfolio_id, timeframe)
                )
            
            # Convert to JSON strings for GraphQL
            return [json.dumps(anomaly) for anomaly in anomalies]
            
        except Exception as e:
            logger.error(f"Error resolving ML anomalies: {e}")
            return []
    
    def resolve_deliveryPreferences(self, info):
        """Resolve user's delivery preferences"""
        try:
            user = getattr(info.context, 'user', None)
            if not user or not user.is_authenticated:
                logger.warning("Authentication required for delivery preferences")
                return json.dumps({"error": "Authentication required"})
            
            # Get delivery preferences from config service
            preferences = alert_config_service.get_all_user_delivery_preferences(user)
            
            return json.dumps(preferences)
            
        except Exception as e:
            logger.error(f"Error resolving delivery preferences: {e}")
            return json.dumps({"error": "Failed to get delivery preferences"})
    
    def resolve_deliveryHistory(self, info, alert_id: str):
        """Resolve delivery history for a specific alert"""
        try:
            user = getattr(info.context, 'user', None)
            if not user or not user.is_authenticated:
                logger.warning("Authentication required for delivery history")
                return []
            
            # Get delivery history from database
            from .models_smart_alerts import AlertDeliveryHistory
            history = AlertDeliveryHistory.objects.filter(
                alert__user=user,
                alert__alert_id=alert_id
            ).order_by('-delivery_attempted_at')
            
            # Convert to JSON strings
            history_data = []
            for record in history:
                history_data.append(json.dumps({
                    'delivery_method': record.delivery_method,
                    'status': record.status,
                    'delivery_attempted_at': record.delivery_attempted_at.isoformat(),
                    'delivery_confirmed_at': record.delivery_confirmed_at.isoformat() if record.delivery_confirmed_at else None,
                    'error_message': record.error_message,
                    'external_id': record.external_id
                }))
            
            return history_data
            
        except Exception as e:
            logger.error(f"Error resolving delivery history: {e}")
            return []

# Input types for mutations
class BenchmarkHoldingInput(graphene.InputObjectType):
    symbol = graphene.String(required=True, description="Stock symbol")
    weight = graphene.Float(required=True, description="Weight in portfolio (0.0 to 1.0)")
    name = graphene.String(description="Company name")
    sector = graphene.String(description="Sector classification")
    description = graphene.String(description="Additional description")

class QuietHoursInput(graphene.InputObjectType):
    enabled = graphene.Boolean(description="Whether quiet hours are enabled")
    start = graphene.String(description="Quiet hours start time (HH:MM)")
    end = graphene.String(description="Quiet hours end time (HH:MM)")

class CustomThresholdsInput(graphene.InputObjectType):
    performance_threshold = graphene.Float(description="Performance difference threshold (%)")
    volatility_threshold = graphene.Float(description="Volatility threshold (%)")
    drawdown_threshold = graphene.Float(description="Drawdown threshold (%)")
    sector_concentration_threshold = graphene.Float(description="Sector concentration threshold (0-1)")

class AlertPreferencesInput(graphene.InputObjectType):
    enabled_categories = graphene.List(graphene.String, description="List of enabled alert categories")
    priority_threshold = graphene.String(description="Minimum priority threshold")
    frequency = graphene.String(description="Alert frequency preference")
    delivery_method = graphene.String(description="Preferred delivery method")
    quiet_hours = graphene.Field(QuietHoursInput, description="Quiet hours settings")
    custom_thresholds = graphene.Field(CustomThresholdsInput, description="Custom alert thresholds")

# Output types for mutations
class QuietHoursType(graphene.ObjectType):
    enabled = graphene.Boolean()
    start = graphene.String()
    end = graphene.String()

class CustomThresholdsType(graphene.ObjectType):
    performance_threshold = graphene.Float()
    volatility_threshold = graphene.Float()
    drawdown_threshold = graphene.Float()
    sector_concentration_threshold = graphene.Float()

class AlertPreferencesType(graphene.ObjectType):
    enabled_categories = graphene.List(graphene.String)
    priority_threshold = graphene.String()
    frequency = graphene.String()
    delivery_method = graphene.String()
    quiet_hours = graphene.Field(QuietHoursType)
    custom_thresholds = graphene.Field(CustomThresholdsType)

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

class UpdateAlertPreferences(graphene.Mutation):
    """Update user's alert preferences and thresholds"""
    
    class Arguments:
        input = AlertPreferencesInput(required=True, description="Alert preferences to update")
    
    success = graphene.Boolean()
    preferences = graphene.Field(AlertPreferencesType)
    error = graphene.String()
    
    def mutate(self, info, input: AlertPreferencesInput):
        user = getattr(info.context, 'user', None)
        if not user or not user.is_authenticated:
            return UpdateAlertPreferences(
                success=False,
                error="Authentication required"
            )
        
        try:
            # Update alert thresholds
            if input.custom_thresholds:
                thresholds = input.custom_thresholds
                
                # Update performance thresholds
                if thresholds.performance_threshold is not None:
                    alert_config_service.set_user_thresholds(
                        user, 'performance_underperformance', 
                        {'performance_diff_threshold': thresholds.performance_threshold}
                    )
                    alert_config_service.set_user_thresholds(
                        user, 'performance_outperformance', 
                        {'performance_diff_threshold': thresholds.performance_threshold}
                    )
                
                # Update volatility threshold
                if thresholds.volatility_threshold is not None:
                    alert_config_service.set_user_thresholds(
                        user, 'risk_high_volatility', 
                        {'volatility_max_threshold': thresholds.volatility_threshold}
                    )
                
                # Update drawdown threshold (convert to negative for backend)
                if thresholds.drawdown_threshold is not None:
                    alert_config_service.set_user_thresholds(
                        user, 'risk_high_drawdown', 
                        {'drawdown_max_threshold': -abs(thresholds.drawdown_threshold)}
                    )
                
                # Update sector concentration threshold
                if thresholds.sector_concentration_threshold is not None:
                    alert_config_service.set_user_thresholds(
                        user, 'allocation_tech_overweight', 
                        {'tech_weight_max_threshold': thresholds.sector_concentration_threshold}
                    )
                    alert_config_service.set_user_thresholds(
                        user, 'allocation_high_concentration', 
                        {'sector_concentration_max_threshold': thresholds.sector_concentration_threshold}
                    )
            
            # Update delivery preferences
            if input.delivery_method or input.quiet_hours:
                # Update delivery preferences for each category and priority level
                categories = ['performance', 'risk', 'allocation', 'portfolio', 'transaction', 'behavior']
                priority_levels = ['critical', 'important', 'informational']
                
                for category in categories:
                    for priority_level in priority_levels:
                        prefs = {}
                        
                        if input.delivery_method:
                            prefs['delivery_method'] = input.delivery_method
                        
                        if input.quiet_hours:
                            prefs['quiet_hours_enabled'] = input.quiet_hours.enabled
                            prefs['quiet_hours_start'] = input.quiet_hours.start
                            prefs['quiet_hours_end'] = input.quiet_hours.end
                        
                        if prefs:
                            alert_config_service.set_user_delivery_preferences(
                                user, category, priority_level, prefs
                            )
            
            # Get updated preferences
            updated_preferences = {
                'enabled_categories': input.enabled_categories or [],
                'priority_threshold': input.priority_threshold or 'medium',
                'frequency': input.frequency or 'daily',
                'delivery_method': input.delivery_method or 'in_app',
                'quiet_hours': {
                    'enabled': input.quiet_hours.enabled if input.quiet_hours else True,
                    'start': input.quiet_hours.start if input.quiet_hours else '22:00',
                    'end': input.quiet_hours.end if input.quiet_hours else '08:00',
                },
                'custom_thresholds': {
                    'performance_threshold': input.custom_thresholds.performance_threshold if input.custom_thresholds else 2.0,
                    'volatility_threshold': input.custom_thresholds.volatility_threshold if input.custom_thresholds else 20.0,
                    'drawdown_threshold': abs(input.custom_thresholds.drawdown_threshold) if input.custom_thresholds and input.custom_thresholds.drawdown_threshold else 15.0,
                    'sector_concentration_threshold': input.custom_thresholds.sector_concentration_threshold if input.custom_thresholds else 0.35,
                }
            }
            
            return UpdateAlertPreferences(
                success=True,
                preferences=updated_preferences,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error updating alert preferences: {e}")
            return UpdateAlertPreferences(
                success=False,
                error=str(e)
            )


class BenchmarkMutation(graphene.ObjectType):
    """GraphQL mutations for benchmark operations"""
    
    createCustomBenchmark = CreateCustomBenchmark.Field(description="Create a new custom benchmark portfolio")
    updateCustomBenchmark = UpdateCustomBenchmark.Field(description="Update an existing custom benchmark portfolio")
    deleteCustomBenchmark = DeleteCustomBenchmark.Field(description="Delete a custom benchmark portfolio")
    createPredefinedBenchmark = CreatePredefinedBenchmark.Field(description="Create a predefined benchmark portfolio")
    updateAlertPreferences = UpdateAlertPreferences.Field(description="Update user's alert preferences and thresholds")
