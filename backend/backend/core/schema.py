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

    def resolve_ping(root, info):
        return "pong"
    
    def resolve_me(self, info):
        # Return mock user without authentication for development
        return UserType(
            id=1,
            email='test@example.com',
            name='Test User'
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
                dividend_score=getattr(stock, 'dividend_score', None)
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
            stock = WatchlistStockType(**stock_data)
            
            # Create the watchlist item with the nested stock
            watchlist_item = WatchlistItemType(
                id=item['id'],
                stock=stock,
                added_at=item['added_at'],
                notes=item['notes'],
                target_price=item['target_price']
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
            dividend_score=fund_data['dividend_score'],
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
                dividend_score=getattr(stock, 'dividend_score', None)
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

class Query(SwingQuery, BaseQuery, graphene.ObjectType):
    # merging by multiple inheritance; keep simple to avoid MRO issues
    pass

class Mutation(graphene.ObjectType):
    token_auth = ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    runBacktest = RunBacktestMutation.Field()

schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=True)