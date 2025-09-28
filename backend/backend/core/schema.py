import graphene
import graphql_jwt
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from core.graphql.queries import Query as SwingQuery, RunBacktestMutation, PortfolioMetricsType, PortfolioHoldingType, _mock_portfolio_metrics, StockType, AdvancedStockScreeningResultType, WatchlistItemType, WatchlistStockType, RustStockAnalysisType, TechnicalIndicatorsType, FundamentalAnalysisType, get_mock_stocks, get_mock_advanced_screening_results, get_mock_watchlist, get_mock_rust_stock_analysis, TargetPriceResultType, PositionSizeResultType, DynamicStopResultType

User = get_user_model()

# Simple auth payload that doesn't use UserType
class AuthPayload(graphene.ObjectType):
    token = graphene.String()
    user = graphene.Field(lambda: UserType)

class UserType(graphene.ObjectType):
    id = graphene.ID()
    email = graphene.String()
    name = graphene.String()
    username = graphene.String()  # Add username field for signals
    # Add missing fields that mobile app expects
    incomeProfile = graphene.String()
    followedTickers = graphene.List(graphene.String)

# Research-related types
class CompanySnapshotType(graphene.ObjectType):
    name = graphene.String()
    sector = graphene.String()
    marketCap = graphene.Float()
    country = graphene.String()
    website = graphene.String()

class QuoteType(graphene.ObjectType):
    price = graphene.Float()
    chg = graphene.Float()
    chgPct = graphene.Float()
    high = graphene.Float()
    low = graphene.Float()
    volume = graphene.Float()

class TechnicalType(graphene.ObjectType):
    rsi = graphene.Float()
    macd = graphene.Float()
    macdhistogram = graphene.Float()
    movingAverage50 = graphene.Float()
    movingAverage200 = graphene.Float()
    supportLevel = graphene.Float()
    resistanceLevel = graphene.Float()
    impliedVolatility = graphene.Float()

class SentimentType(graphene.ObjectType):
    label = graphene.String()
    score = graphene.Float()
    confidence = graphene.Float()
    # Use a field name that won't be auto-converted
    article_count = graphene.Int(name='article_count')
    articleCount = graphene.Int()
    
    def resolve_article_count(self, info):
        return getattr(self, 'article_count', 15)
    
    def resolve_articleCount(self, info):
        return getattr(self, 'article_count', 15)

class MacroType(graphene.ObjectType):
    vix = graphene.Float()
    marketSentiment = graphene.String()
    riskAppetite = graphene.String()

class MarketRegimeType(graphene.ObjectType):
    confidence = graphene.Float()
    # Use field names that won't be auto-converted
    market_regime = graphene.String(name='market_regime')
    marketRegime = graphene.String()
    recommended_strategy = graphene.String(name='recommended_strategy')
    recommendedStrategy = graphene.String()
    
    def resolve_market_regime(self, info):
        return getattr(self, 'market_regime', 'bull_market')
    
    def resolve_marketRegime(self, info):
        return getattr(self, 'market_regime', 'bull_market')
    
    def resolve_recommended_strategy(self, info):
        return getattr(self, 'recommended_strategy', 'momentum_trading')
    
    def resolve_recommendedStrategy(self, info):
        return getattr(self, 'recommended_strategy', 'momentum_trading')

class ResearchHubType(graphene.ObjectType):
    symbol = graphene.String()
    snapshot = graphene.Field(CompanySnapshotType)
    quote = graphene.Field(QuoteType)
    technical = graphene.Field(TechnicalType)
    sentiment = graphene.Field(SentimentType)
    macro = graphene.Field(MacroType)
    marketRegime = graphene.Field(MarketRegimeType)
    peers = graphene.List(graphene.String)
    updatedAt = graphene.String()

class ChartDataType(graphene.ObjectType):
    timestamp = graphene.String()
    open = graphene.Float()
    high = graphene.Float()
    low = graphene.Float()
    close = graphene.Float()
    volume = graphene.Float()

class IndicatorsType(graphene.ObjectType):
    SMA20 = graphene.Float()
    SMA50 = graphene.Float()
    EMA12 = graphene.Float()
    EMA26 = graphene.Float()
    BB_upper = graphene.Float()
    BB_middle = graphene.Float()
    BB_lower = graphene.Float()
    RSI14 = graphene.Float()
    MACD = graphene.Float()
    MACD_signal = graphene.Float()
    MACD_hist = graphene.Float()
    # camelCase aliases
    BBUpper = graphene.Float()
    BBMiddle = graphene.Float()
    BBLower = graphene.Float()
    MACDSignal = graphene.Float()
    MACDHist = graphene.Float()

class StockChartDataType(graphene.ObjectType):
    symbol = graphene.String()
    interval = graphene.String()
    limit = graphene.Int()
    currentPrice = graphene.Float()
    change = graphene.Float()
    changePercent = graphene.Float()
    data = graphene.List(ChartDataType)
    indicators = graphene.Field(IndicatorsType)

class CryptoMLSignalType(graphene.ObjectType):
    symbol = graphene.String()
    probability = graphene.Float()
    confidenceLevel = graphene.String()  # Changed from Float to String
    explanation = graphene.String()
    features = graphene.List(graphene.String)
    modelVersion = graphene.String()
    timestamp = graphene.String()

class CryptocurrencyType(graphene.ObjectType):
    symbol = graphene.String()
    name = graphene.String()
    priceUsd = graphene.Float()
    marketCap = graphene.Float()
    volume24h = graphene.Float()
    change24h = graphene.Float()
    changePercent24h = graphene.Float()

class CryptoRecommendationType(graphene.ObjectType):
    symbol = graphene.String()
    score = graphene.Float()
    probability = graphene.Float()
    confidenceLevel = graphene.String()
    priceUsd = graphene.Float()
    volatilityTier = graphene.String()
    liquidity24hUsd = graphene.Float()
    rationale = graphene.String()
    recommendation = graphene.String()
    riskLevel = graphene.String()

class CryptoHoldingType(graphene.ObjectType):
    cryptocurrency = graphene.Field(CryptocurrencyType)
    quantity = graphene.Float()
    valueUsd = graphene.Float()
    gainLoss = graphene.Float()
    gainLossPercent = graphene.Float()

class CryptoPortfolioType(graphene.ObjectType):
    totalValueUsd = graphene.Float()
    totalGainLoss = graphene.Float()
    totalGainLossPercent = graphene.Float()
    holdings = graphene.List(CryptoHoldingType)

class ObtainJSONWebToken(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    token = graphene.String()
    user = graphene.Field(UserType)
    
    def mutate(self, info, email, password):
        # For development, always return a mock token and user
        # In production, you would validate credentials here
        mock_token = "mock_jwt_token_for_development"
        mock_user = UserType(
            id=1,
            email=email,
            name='Test User'
        )
        return ObtainJSONWebToken(token=mock_token, user=mock_user)

class BaseQuery(graphene.ObjectType):
    ping = graphene.String()
    me = graphene.Field(UserType)
    portfolioMetrics = graphene.Field(PortfolioMetricsType)
    stocks = graphene.List(
        StockType,
        search=graphene.String(),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
    )
    advancedStockScreening = graphene.List(
        AdvancedStockScreeningResultType,
        sector=graphene.String(),
        minMarketCap=graphene.Float(),
        maxMarketCap=graphene.Float(),
        minPeRatio=graphene.Float(),
        maxPeRatio=graphene.Float(),
        minDividendYield=graphene.Float(),
        minBeginnerScore=graphene.Int(),
        sortBy=graphene.String(),
        limit=graphene.Int(default_value=10),
    )
    myWatchlist = graphene.List(
        WatchlistItemType,
        limit=graphene.Int(default_value=10),
    )
    rustStockAnalysis = graphene.Field(
        RustStockAnalysisType,
        symbol=graphene.String(required=True),
    )
    beginnerFriendlyStocks = graphene.List(
        StockType,
        limit=graphene.Int(default_value=10),
    )
    calculateTargetPrice = graphene.Field(
        TargetPriceResultType,
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskRewardRatio=graphene.Float(),
        atr=graphene.Float(),
        resistanceLevel=graphene.Float(),
        supportLevel=graphene.Float(),
        signalType=graphene.String(),
    )
    calculatePositionSize = graphene.Field(
        PositionSizeResultType,
        accountBalance=graphene.Float(),
        accountEquity=graphene.Float(),
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskPercentage=graphene.Float(),
        riskPerTrade=graphene.Float(),
        riskAmount=graphene.Float(),
        maxPositionSize=graphene.Float(),
        maxPositionPct=graphene.Float(),
        confidence=graphene.Float(),
        method=graphene.String(),
    )
    calculateDynamicStop = graphene.Field(
        DynamicStopResultType,
        entryPrice=graphene.Float(required=True),
        atr=graphene.Float(required=True),
        atrMultiplier=graphene.Float(),
        supportLevel=graphene.Float(),
        resistanceLevel=graphene.Float(),
        signalType=graphene.String(),
    )
    # Add missing queries that mobile app expects
    stockDiscussions = graphene.List(graphene.String)
    researchHub = graphene.Field(ResearchHubType, symbol=graphene.String(required=True))
    stockChartData = graphene.Field(StockChartDataType, 
        symbol=graphene.String(required=True),
        timeframe=graphene.String(),
        interval=graphene.String(),
        limit=graphene.Int(),
        indicators=graphene.List(graphene.String)
    )
    cryptoMlSignal = graphene.Field(CryptoMLSignalType, symbol=graphene.String(required=True))
    cryptoRecommendations = graphene.List(
        CryptoRecommendationType,
        limit=graphene.Int(),
        symbols=graphene.List(graphene.String)
    )
    supportedCurrencies = graphene.List(CryptocurrencyType)
    cryptoPortfolio = graphene.Field(lambda: CryptoPortfolioType)

    def resolve_ping(root, info):
        return "pong"
    
    def resolve_me(self, info):
        # Return mock user without authentication for development
        return UserType(
            id=1,
            email='test@example.com',
            name='Test User',
            username='testuser',  # Add username for signals
            incomeProfile='premium',
            followedTickers=['AAPL', 'TSLA', 'NVDA']
        )
    
    def resolve_portfolioMetrics(self, info):
        d = _mock_portfolio_metrics()
        # Safest: return typed objects (avoids dict key/name mismatches)
        return PortfolioMetricsType(
            total_value=d["total_value"],
            total_cost=d["total_cost"],
            total_return=d["total_return"],
            total_return_percent=d["total_return_percent"],
            holdings=[PortfolioHoldingType(**h) for h in d["holdings"]],
        )
    
    def resolve_stocks(self, info, search=None, limit=10, offset=0):
        from core.models import Stock
        from django.db import models
        
        # Get real stocks from database
        queryset = Stock.objects.all()
        
        if search:
            search_lower = search.lower()
            queryset = queryset.filter(
                models.Q(symbol__icontains=search_lower) |
                models.Q(company_name__icontains=search_lower)
            )
        
        # Apply pagination
        stocks = queryset[offset:offset + limit]
        
        # Convert to GraphQL format
        result = []
        for stock in stocks:
            # Safely get dividend_score field, default to None if it doesn't exist
            dividend_score = getattr(stock, 'dividend_score', None)
            
            result.append(StockType(
                id=str(stock.id),
                symbol=stock.symbol,
                company_name=stock.company_name,
                sector=stock.sector,
                current_price=float(stock.current_price) if stock.current_price else None,
                market_cap=float(stock.market_cap) if stock.market_cap else None,
                pe_ratio=stock.pe_ratio,
                dividend_yield=stock.dividend_yield,
                beginner_friendly_score=float(stock.beginner_friendly_score) if stock.beginner_friendly_score else None,
                dividend_score=dividend_score,
                # camelCase aliases
                companyName=stock.company_name,
                currentPrice=float(stock.current_price) if stock.current_price else None,
                marketCap=float(stock.market_cap) if stock.market_cap else None,
                peRatio=stock.pe_ratio,
                dividendYield=stock.dividend_yield,
                beginnerFriendlyScore=float(stock.beginner_friendly_score) if stock.beginner_friendly_score else None
            ))
        
        return result
    
    def resolve_advancedStockScreening(self, info, sector=None, minMarketCap=None, 
                                     maxMarketCap=None, minPeRatio=None, maxPeRatio=None, 
                                     minDividendYield=None, minBeginnerScore=None, 
                                     sortBy=None, limit=10):
        results = get_mock_advanced_screening_results()
        
        # Apply filters
        filtered_results = []
        for result in results:
            # Sector filter
            if sector and result['sector'] != sector:
                continue
            
            # Market cap filters
            if minMarketCap and result['market_cap'] < minMarketCap:
                continue
            if maxMarketCap and result['market_cap'] > maxMarketCap:
                continue
            
            # PE ratio filters
            if minPeRatio and result['pe_ratio'] < minPeRatio:
                continue
            if maxPeRatio and result['pe_ratio'] > maxPeRatio:
                continue
            
            # Dividend yield filter
            if minDividendYield and result['dividend_yield'] < minDividendYield:
                continue
            
            # Beginner score filter (convert to float for comparison)
            if minBeginnerScore is not None and result['beginner_friendly_score'] < (minBeginnerScore / 100.0):
                continue
            
            filtered_results.append(result)
        
        # Apply sorting
        if sortBy:
            if sortBy == 'ml_score':
                filtered_results.sort(key=lambda x: x['ml_score'], reverse=True)
            elif sortBy == 'score':
                filtered_results.sort(key=lambda x: x['score'], reverse=True)
            elif sortBy == 'market_cap':
                filtered_results.sort(key=lambda x: x['market_cap'], reverse=True)
            elif sortBy == 'pe_ratio':
                filtered_results.sort(key=lambda x: x['pe_ratio'], reverse=True)
            elif sortBy == 'volatility':
                filtered_results.sort(key=lambda x: x['volatility'], reverse=True)
        
        # Apply limit
        return [AdvancedStockScreeningResultType(**result) for result in filtered_results[:limit]]
    
    def resolve_myWatchlist(self, info, limit=10):
        watchlist = get_mock_watchlist()
        result = []
        for item in watchlist[:limit]:
            # Create the nested stock object
            stock_data = item['stock']
            stock = WatchlistStockType(
                id=stock_data['id'],
                symbol=stock_data['symbol'],
                company_name=stock_data['company_name'],
                companyName=stock_data['companyName'],
                sector=stock_data['sector'],
                current_price=stock_data['current_price'],
                currentPrice=stock_data['currentPrice'],
                beginner_friendly_score=stock_data['beginner_friendly_score'],
                change=stock_data['change'],
                changePercent=stock_data['changePercent']
            )
            
            # Create the watchlist item with the nested stock
            watchlist_item = WatchlistItemType(
                id=item['id'],
                stock=stock,
                added_at=item['added_at'],
                notes=item['notes'],
                target_price=item['target_price'],
                # Direct fields for mobile app compatibility
                symbol=stock_data['symbol'],
                companyName=stock_data['companyName'],
                currentPrice=stock_data['currentPrice'],
                change=stock_data['change'],
                changePercent=stock_data['changePercent']
            )
            result.append(watchlist_item)
        
        return result
    
    def resolve_rustStockAnalysis(self, info, symbol):
        analysis_data = get_mock_rust_stock_analysis(symbol)
        
        # Create technical indicators object
        tech_data = analysis_data['technical_indicators']
        technical_indicators = TechnicalIndicatorsType(
            rsi=tech_data['rsi'],
            macd=tech_data['macd'],
            macd_signal=tech_data['macd_signal'],
            macd_histogram=tech_data['macd_histogram'],
            sma20=tech_data['sma20'],
            sma50=tech_data['sma50'],
            ema12=tech_data['ema12'],
            ema26=tech_data['ema26'],
            bollinger_upper=tech_data['bollinger_upper'],
            bollinger_lower=tech_data['bollinger_lower'],
            bollinger_middle=tech_data['bollinger_middle']
        )
        
        # Create fundamental analysis object
        fund_data = analysis_data['fundamental_analysis']
        fundamental_analysis = FundamentalAnalysisType(
            valuation_score=fund_data['valuation_score'],
            growth_score=fund_data['growth_score'],
            stability_score=fund_data['stability_score'],
            debt_score=fund_data['debt_score']
        )
        
        # Create the main analysis object
        return RustStockAnalysisType(
            symbol=analysis_data['symbol'],
            beginner_friendly_score=analysis_data['beginner_friendly_score'],
            risk_level=analysis_data['risk_level'],
            recommendation=analysis_data['recommendation'],
            technical_indicators=technical_indicators,
            fundamental_analysis=fundamental_analysis,
            reasoning=analysis_data['reasoning']
        )
    
    def resolve_beginnerFriendlyStocks(self, info, limit=10):
        from core.models import Stock
        
        # Get real stocks from database with beginner-friendly score >= 80
        stocks = Stock.objects.filter(
            beginner_friendly_score__gte=80
        ).order_by('-beginner_friendly_score')[:limit]
        
        # Convert to GraphQL format
        result = []
        for stock in stocks:
            # Safely get dividend_score field, default to None if it doesn't exist
            dividend_score = getattr(stock, 'dividend_score', None)
            
            result.append(StockType(
                id=str(stock.id),
                symbol=stock.symbol,
                company_name=stock.company_name,
                sector=stock.sector,
                current_price=float(stock.current_price) if stock.current_price else None,
                market_cap=float(stock.market_cap) if stock.market_cap else None,
                pe_ratio=stock.pe_ratio,
                dividend_yield=stock.dividend_yield,
                beginner_friendly_score=float(stock.beginner_friendly_score) if stock.beginner_friendly_score else None,
                dividend_score=dividend_score,
                # camelCase aliases
                companyName=stock.company_name,
                currentPrice=float(stock.current_price) if stock.current_price else None,
                marketCap=float(stock.market_cap) if stock.market_cap else None,
                peRatio=stock.pe_ratio,
                dividendYield=stock.dividend_yield,
                beginnerFriendlyScore=float(stock.beginner_friendly_score) if stock.beginner_friendly_score else None
            ))
        
        return result
    
    def resolve_calculateTargetPrice(self, info, entryPrice, stopPrice, riskRewardRatio=None, atr=None, resistanceLevel=None, supportLevel=None, signalType=None):
        # Import the resolver from queries.py
        from core.graphql.queries import Query as SwingQuery
        swing_query = SwingQuery()
        return swing_query.resolve_calculateTargetPrice(info, entryPrice, stopPrice, riskRewardRatio, atr, resistanceLevel, supportLevel, signalType)
    
    def resolve_calculatePositionSize(self, info, accountBalance=None, accountEquity=None, entryPrice=None, stopPrice=None, riskPercentage=None, riskPerTrade=None, riskAmount=None, maxPositionSize=None, maxPositionPct=None, confidence=None, method=None):
        # Import the resolver from queries.py
        from core.graphql.queries import Query as SwingQuery
        swing_query = SwingQuery()
        return swing_query.resolve_calculatePositionSize(info, accountBalance, accountEquity, entryPrice, stopPrice, riskPercentage, riskPerTrade, riskAmount, maxPositionSize, maxPositionPct, confidence, method)
    
    def resolve_calculateDynamicStop(self, info, entryPrice, atr, atrMultiplier=None, supportLevel=None, resistanceLevel=None, signalType=None):
        # Import the resolver from queries.py
        from core.graphql.queries import Query as SwingQuery
        swing_query = SwingQuery()
        return swing_query.resolve_calculateDynamicStop(info, entryPrice, atr, atrMultiplier, supportLevel, resistanceLevel, signalType)
    
    def resolve_stockDiscussions(self, info):
        # Mock stock discussions for demo
        return [
            "AAPL showing strong technical breakout",
            "TSLA volatility expected to continue",
            "NVDA AI chip demand remains high"
        ]
    
    def resolve_researchHub(self, info, symbol):
        # Mock research hub data for demo
        return ResearchHubType(
            symbol=symbol,
            snapshot=CompanySnapshotType(
                name=f"{symbol} Inc.",
                sector="Technology",
                marketCap=2000000000000.0,
                country="USA",
                website=f"https://{symbol.lower()}.com"
            ),
            quote=QuoteType(
                price=150.0,
                chg=2.5,
                chgPct=1.69,
                high=152.0,
                low=148.0,
                volume=50000000.0
            ),
            technical=TechnicalType(
                rsi=65.0,
                macd=1.2,
                macdhistogram=0.3,
                movingAverage50=145.0,
                movingAverage200=140.0,
                supportLevel=145.0,
                resistanceLevel=155.0,
                impliedVolatility=0.25
            ),
            sentiment=SentimentType(
                label="Bullish",
                score=0.75,
                article_count=25,
                confidence=0.8,
                articleCount=25
            ),
            macro=MacroType(
                vix=18.5,
                marketSentiment="Risk On",
                riskAppetite="High"
            ),
            marketRegime=MarketRegimeType(
                market_regime="Bull Market",
                confidence=0.85,
                recommended_strategy="Growth",
                marketRegime="Bull Market",
                recommendedStrategy="Growth"
            ),
            peers=["MSFT", "GOOGL", "AMZN"],
            updatedAt="2025-09-25T16:45:00Z"
        )
    
    def resolve_stockChartData(self, info, symbol, timeframe="1D", interval="1D", limit=180, indicators=None):
        # Mock chart data for demo
        import time
        current_time = int(time.time())
        
        # Generate mock chart data
        chart_data = []
        base_price = 150.0
        for i in range(min(limit, 30)):  # Limit to 30 data points for demo
            timestamp = current_time - (i * 3600)  # Hourly data
            price = base_price + (i * 0.5) + (i % 3 - 1) * 2  # Some variation
            chart_data.append(ChartDataType(
                timestamp=str(timestamp),
                open=price,
                high=price + 1.0,
                low=price - 1.0,
                close=price + 0.5,
                volume=1000000.0
            ))
        
        return StockChartDataType(
            symbol=symbol,
            interval=interval,
            limit=limit,
            currentPrice=base_price,
            change=2.5,
            changePercent=1.69,
            data=chart_data,
            indicators=IndicatorsType(
                SMA20=148.0,
                SMA50=145.0,
                EMA12=149.0,
                EMA26=146.0,
                BB_upper=155.0,
                BB_middle=150.0,
                BB_lower=145.0,
                RSI14=65.0,
                MACD=1.2,
                MACD_signal=1.0,
                MACD_hist=0.2,
                # camelCase aliases
                BBUpper=155.0,
                BBMiddle=150.0,
                BBLower=145.0,
                MACDSignal=1.0,
                MACDHist=0.2
            )
        )

    def resolve_cryptoMlSignal(self, info, symbol):
        # Mock crypto ML signal data for demo
        import time
        current_time = int(time.time())
        
        # Mock probability based on symbol
        if symbol.upper() == 'BTC':
            probability = 0.75
            confidence_level = 0.85
            confidence_level_str = "HIGH"
            explanation = "Strong bullish momentum detected with high volume and positive sentiment indicators"
            features = ["price_momentum", "volume_spike", "sentiment_score", "technical_breakout"]
        elif symbol.upper() == 'ETH':
            probability = 0.68
            confidence_level = 0.78
            confidence_level_str = "HIGH"
            explanation = "Moderate bullish signal with improving technical indicators"
            features = ["rsi_oversold_recovery", "moving_average_crossover", "volume_trend"]
        else:
            probability = 0.55
            confidence_level = 0.65
            confidence_level_str = "MEDIUM"
            explanation = "Neutral to slightly bullish signal with mixed indicators"
            features = ["price_action", "market_sentiment", "volatility_analysis"]
        
        return CryptoMLSignalType(
            symbol=symbol.upper(),
            probability=probability,
            confidenceLevel=confidence_level_str,  # Return string instead of number
            explanation=explanation,
            features=features,
            modelVersion="v2.1.0",
            timestamp=str(current_time)
        )

    def resolve_cryptoRecommendations(self, info, limit=10, symbols=None):
        # Mock crypto recommendations data
        recommendations = [
            {
                'symbol': 'BTC',
                'score': 0.85,
                'probability': 0.75,
                'confidenceLevel': 'HIGH',
                'priceUsd': 45000.0,
                'volatilityTier': 'MEDIUM',
                'liquidity24hUsd': 25000000000.0,
                'rationale': 'Strong institutional adoption and limited supply',
                'recommendation': 'BUY',
                'riskLevel': 'MEDIUM'
            },
            {
                'symbol': 'ETH',
                'score': 0.78,
                'probability': 0.68,
                'confidenceLevel': 'HIGH',
                'priceUsd': 3000.0,
                'volatilityTier': 'HIGH',
                'liquidity24hUsd': 15000000000.0,
                'rationale': 'Ethereum 2.0 upgrades and DeFi growth',
                'recommendation': 'BUY',
                'riskLevel': 'HIGH'
            },
            {
                'symbol': 'ADA',
                'score': 0.65,
                'probability': 0.55,
                'confidenceLevel': 'MEDIUM',
                'priceUsd': 0.45,
                'volatilityTier': 'HIGH',
                'liquidity24hUsd': 500000000.0,
                'rationale': 'Smart contract platform with strong fundamentals',
                'recommendation': 'HOLD',
                'riskLevel': 'HIGH'
            },
            {
                'symbol': 'SOL',
                'score': 0.72,
                'probability': 0.62,
                'confidenceLevel': 'MEDIUM',
                'priceUsd': 95.0,
                'volatilityTier': 'HIGH',
                'liquidity24hUsd': 2000000000.0,
                'rationale': 'Fast blockchain with growing ecosystem',
                'recommendation': 'BUY',
                'riskLevel': 'HIGH'
            },
            {
                'symbol': 'DOT',
                'score': 0.68,
                'probability': 0.58,
                'confidenceLevel': 'MEDIUM',
                'priceUsd': 6.5,
                'volatilityTier': 'MEDIUM',
                'liquidity24hUsd': 800000000.0,
                'rationale': 'Interoperability protocol with strong development',
                'recommendation': 'HOLD',
                'riskLevel': 'MEDIUM'
            },
            {
                'symbol': 'MATIC',
                'score': 0.70,
                'probability': 0.60,
                'confidenceLevel': 'MEDIUM',
                'priceUsd': 0.85,
                'volatilityTier': 'HIGH',
                'liquidity24hUsd': 600000000.0,
                'rationale': 'Layer 2 scaling solution for Ethereum',
                'recommendation': 'BUY',
                'riskLevel': 'MEDIUM'
            }
        ]
        
        # Filter by symbols if provided
        if symbols:
            recommendations = [r for r in recommendations if r['symbol'] in symbols]
        
        # Limit results
        recommendations = recommendations[:limit]
        
        return [CryptoRecommendationType(**rec) for rec in recommendations]

    def resolve_supportedCurrencies(self, info):
        # Mock supported currencies data
        currencies = [
            CryptocurrencyType(
                symbol='BTC',
                name='Bitcoin',
                priceUsd=45000.0,
                marketCap=850000000000.0,
                volume24h=25000000000.0,
                change24h=1200.0,
                changePercent24h=2.74
            ),
            CryptocurrencyType(
                symbol='ETH',
                name='Ethereum',
                priceUsd=3000.0,
                marketCap=360000000000.0,
                volume24h=15000000000.0,
                change24h=85.0,
                changePercent24h=2.91
            ),
            CryptocurrencyType(
                symbol='USDC',
                name='USD Coin',
                priceUsd=1.0,
                marketCap=32000000000.0,
                volume24h=5000000000.0,
                change24h=0.0,
                changePercent24h=0.0
            ),
            CryptocurrencyType(
                symbol='ADA',
                name='Cardano',
                priceUsd=0.45,
                marketCap=15000000000.0,
                volume24h=500000000.0,
                change24h=0.02,
                changePercent24h=4.65
            ),
            CryptocurrencyType(
                symbol='SOL',
                name='Solana',
                priceUsd=95.0,
                marketCap=40000000000.0,
                volume24h=2000000000.0,
                change24h=3.5,
                changePercent24h=3.82
            )
        ]
        return currencies

    def resolve_cryptoPortfolio(self, info):
        # Mock crypto portfolio data
        holdings = [
            CryptoHoldingType(
                cryptocurrency=CryptocurrencyType(
                    symbol='BTC',
                    name='Bitcoin',
                    priceUsd=45000.0,
                    marketCap=850000000000.0,
                    volume24h=25000000000.0,
                    change24h=1200.0,
                    changePercent24h=2.74
                ),
                quantity=0.5,
                valueUsd=22500.0,
                gainLoss=2500.0,
                gainLossPercent=12.5
            ),
            CryptoHoldingType(
                cryptocurrency=CryptocurrencyType(
                    symbol='ETH',
                    name='Ethereum',
                    priceUsd=3000.0,
                    marketCap=360000000000.0,
                    volume24h=15000000000.0,
                    change24h=85.0,
                    changePercent24h=2.91
                ),
                quantity=2.0,
                valueUsd=6000.0,
                gainLoss=800.0,
                gainLossPercent=15.38
            ),
            CryptoHoldingType(
                cryptocurrency=CryptocurrencyType(
                    symbol='USDC',
                    name='USD Coin',
                    priceUsd=1.0,
                    marketCap=32000000000.0,
                    volume24h=5000000000.0,
                    change24h=0.0,
                    changePercent24h=0.0
                ),
                quantity=1000.0,
                valueUsd=1000.0,
                gainLoss=0.0,
                gainLossPercent=0.0
            )
        ]
        
        total_value = sum(h.valueUsd for h in holdings)
        total_gain_loss = sum(h.gainLoss for h in holdings)
        total_gain_loss_percent = (total_gain_loss / (total_value - total_gain_loss)) * 100 if total_value > total_gain_loss else 0
        
        return CryptoPortfolioType(
            totalValueUsd=total_value,
            totalGainLoss=total_gain_loss,
            totalGainLossPercent=total_gain_loss_percent,
            holdings=holdings
        )

class Query(SwingQuery, BaseQuery, graphene.ObjectType):
    # merging by multiple inheritance; keep simple to avoid MRO issues
    pass

class Mutation(graphene.ObjectType):
    token_auth = ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    runBacktest = RunBacktestMutation.Field()
    
    # Signal mutations
    likeSignal = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        signalId=graphene.ID(required=True),
        description="Like or unlike a signal"
    )
    
    commentSignal = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        signalId=graphene.ID(required=True),
        content=graphene.String(required=True),
        description="Add a comment to a signal"
    )
    
    def resolve_likeSignal(self, info, signalId):
        # Mock implementation - always return success
        return True
    
    def resolve_commentSignal(self, info, signalId, content):
        # Mock implementation - always return success
        return True

schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=True)