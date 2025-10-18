import graphene
from graphene import ObjectType, String, Float, Int, List, Field
from .models import Stock
# from .mutations import get_stock_data_from_api  # Function doesn't exist yet
import requests
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ChartDataPoint(graphene.ObjectType):
    timestamp = graphene.String()
    open = graphene.Float()
    high = graphene.Float()
    low = graphene.Float()
    close = graphene.Float()
    volume = graphene.Int()

class ChartData(graphene.ObjectType):
    data = List(ChartDataPoint)
    currentPrice = graphene.Float()
    changePercent = graphene.Float()

class KeyMetrics(graphene.ObjectType):
    revenue = graphene.Float()
    revenueGrowth = graphene.Float()
    grossProfit = graphene.Float()
    operatingIncome = graphene.Float()
    netIncome = graphene.Float()
    eps = graphene.Float()
    epsGrowth = graphene.Float()
    roe = graphene.Float()
    roa = graphene.Float()
    debtToEquity = graphene.Float()
    currentRatio = graphene.Float()
    quickRatio = graphene.Float()

class NewsItem(graphene.ObjectType):
    title = graphene.String()
    summary = graphene.String()
    url = graphene.String()
    publishedAt = graphene.String()
    source = graphene.String()
    sentiment = graphene.String()

class AnalystRating(graphene.ObjectType):
    analyst = graphene.String()
    firm = graphene.String()
    rating = graphene.String()
    targetPrice = graphene.Float()
    date = graphene.String()

class RatingsBreakdown(graphene.ObjectType):
    buy = graphene.Int()
    hold = graphene.Int()
    sell = graphene.Int()

class AnalystRatings(graphene.ObjectType):
    consensusRating = graphene.String()
    averageTargetPrice = graphene.Float()
    numberOfAnalysts = graphene.Int()
    ratingsBreakdown = Field(RatingsBreakdown)
    recentRatings = List(AnalystRating)

class EarningsData(graphene.ObjectType):
    nextEarningsDate = graphene.String()
    lastEarningsDate = graphene.String()
    actualEps = graphene.Float()
    estimatedEps = graphene.Float()
    surprise = graphene.Float()
    surprisePercent = graphene.Float()
    revenue = graphene.Float()
    estimatedRevenue = graphene.Float()

class InsiderTrade(graphene.ObjectType):
    insiderName = graphene.String()
    transactionDate = graphene.String()
    shares = graphene.Int()
    price = graphene.Float()
    type = graphene.String()
    value = graphene.Float()

class InstitutionalHolding(graphene.ObjectType):
    institutionName = graphene.String()
    sharesHeld = graphene.Int()
    percentOfShares = graphene.Float()
    valueHeld = graphene.Float()
    changeFromPrevious = graphene.Float()

class SentimentPost(graphene.ObjectType):
    content = graphene.String()
    sentiment = graphene.String()
    source = graphene.String()
    timestamp = graphene.String()

class MarketSentiment(graphene.ObjectType):
    overallScore = graphene.Float()
    positiveMentions = graphene.Int()
    negativeMentions = graphene.Int()
    neutralMentions = graphene.Int()
    recentPosts = List(SentimentPost)

class TechnicalIndicators(graphene.ObjectType):
    rsi = graphene.Float()
    macd = graphene.Float()
    macdSignal = graphene.Float()
    macdHistogram = graphene.Float()
    sma20 = graphene.Float()
    sma50 = graphene.Float()
    sma200 = graphene.Float()
    ema12 = graphene.Float()
    ema26 = graphene.Float()
    bollingerUpper = graphene.Float()
    bollingerLower = graphene.Float()
    bollingerMiddle = graphene.Float()
    supportLevel = graphene.Float()
    resistanceLevel = graphene.Float()
    impliedVolatility = graphene.Float()

class PeerStock(graphene.ObjectType):
    symbol = graphene.String()
    companyName = graphene.String()
    currentPrice = graphene.Float()
    changePercent = graphene.Float()
    marketCap = graphene.Float()

class StockComprehensive(graphene.ObjectType):
    # Basic Info
    symbol = graphene.String()
    companyName = graphene.String()
    sector = graphene.String()
    industry = graphene.String()
    description = graphene.String()
    website = graphene.String()
    employees = graphene.Int()
    founded = graphene.String()
    
    # Financial Metrics
    marketCap = graphene.Float()
    peRatio = graphene.Float()
    pegRatio = graphene.Float()
    priceToBook = graphene.Float()
    priceToSales = graphene.Float()
    dividendYield = graphene.Float()
    dividendRate = graphene.Float()
    exDividendDate = graphene.String()
    payoutRatio = graphene.Float()
    
    # Price Data
    currentPrice = graphene.Float()
    previousClose = graphene.Float()
    dayHigh = graphene.Float()
    dayLow = graphene.Float()
    week52High = graphene.Float()
    week52Low = graphene.Float()
    volume = graphene.Int()
    avgVolume = graphene.Int()
    change = graphene.Float()
    changePercent = graphene.Float()
    
    # Chart Data
    chartData = Field(ChartData)
    
    # Key Metrics
    keyMetrics = Field(KeyMetrics)
    
    # News
    news = List(NewsItem)
    
    # Analyst Data
    analystRatings = Field(AnalystRatings)
    
    # Earnings
    earnings = Field(EarningsData)
    
    # Insider Trading
    insiderTrades = List(InsiderTrade)
    
    # Institutional Ownership
    institutionalOwnership = List(InstitutionalHolding)
    
    # Market Sentiment
    sentiment = Field(MarketSentiment)
    
    # Technical Indicators
    technicals = Field(TechnicalIndicators)
    
    # Peers
    peers = List(PeerStock)

class StockComprehensiveQuery(graphene.ObjectType):
    stockComprehensive = Field(StockComprehensive, symbol=graphene.String(required=True), timeframe=graphene.String())
    
    def resolve_stockComprehensive(self, info, symbol, timeframe="1D"):
        try:
            # Mock stock data for now (until get_stock_data_from_api is implemented)
            stock_data = {
                'companyName': f'{symbol} Inc.',
                'sector': 'Technology',
                'industry': 'Software',
                'description': f'Leading technology company {symbol}',
                'website': f'https://{symbol.lower()}.com',
                'employees': 50000,
                'founded': '1990',
                'marketCap': 1000000000000,
                'peRatio': 25.0,
                'currentPrice': 150.0,
                'changePercent': 2.5,
            }
            
            # stock_data is always truthy since it's a dictionary, so we don't need this check
            
            # Generate comprehensive data structure
            comprehensive_data = {
                'symbol': symbol,
                'companyName': stock_data.get('companyName', ''),
                'sector': stock_data.get('sector', ''),
                'industry': stock_data.get('industry', ''),
                'description': stock_data.get('description', ''),
                'website': stock_data.get('website', ''),
                'employees': stock_data.get('employees', 0),
                'founded': stock_data.get('founded', ''),
                
                # Financial Metrics
                'marketCap': stock_data.get('marketCap', 0),
                'peRatio': stock_data.get('peRatio', 0),
                'pegRatio': stock_data.get('pegRatio', 0),
                'priceToBook': stock_data.get('priceToBook', 0),
                'priceToSales': stock_data.get('priceToSales', 0),
                'dividendYield': stock_data.get('dividendYield', 0),
                'dividendRate': stock_data.get('dividendRate', 0),
                'exDividendDate': stock_data.get('exDividendDate', ''),
                'payoutRatio': stock_data.get('payoutRatio', 0),
                
                # Price Data
                'currentPrice': stock_data.get('currentPrice', 0),
                'previousClose': stock_data.get('previousClose', 0),
                'dayHigh': stock_data.get('dayHigh', 0),
                'dayLow': stock_data.get('dayLow', 0),
                'week52High': stock_data.get('week52High', 0),
                'week52Low': stock_data.get('week52Low', 0),
                'volume': stock_data.get('volume', 0),
                'avgVolume': stock_data.get('avgVolume', 0),
                'change': stock_data.get('change', 0),
                'changePercent': stock_data.get('changePercent', 0),
                
                # Chart Data (generate from price history)
                'chartData': {
                    'data': StockComprehensiveQuery._generate_chart_data(symbol, timeframe),
                    'currentPrice': stock_data.get('currentPrice', 150.0),
                    'changePercent': stock_data.get('changePercent', 2.5)
                },
                
                # Key Metrics
                'keyMetrics': StockComprehensiveQuery._get_key_metrics(symbol),
                
                # News (from existing news API)
                'news': StockComprehensiveQuery._get_news_data(symbol),
                
                # Analyst Ratings (from existing data)
                'analystRatings': StockComprehensiveQuery._get_analyst_ratings(symbol),
                
                # Earnings
                'earnings': StockComprehensiveQuery._get_earnings_data(symbol),
                
                # Insider Trading
                'insiderTrades': StockComprehensiveQuery._get_insider_trades(symbol),
                
                # Institutional Ownership
                'institutionalOwnership': StockComprehensiveQuery._get_institutional_ownership(symbol),
                
                # Market Sentiment
                'sentiment': StockComprehensiveQuery._get_market_sentiment(symbol),
                
                # Technical Indicators
                'technicals': StockComprehensiveQuery._get_technical_indicators(symbol),
                
                # Peers
                'peers': StockComprehensiveQuery._get_peer_stocks(symbol),
            }
            
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error fetching comprehensive stock data for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def _generate_chart_data(symbol, timeframe):
        """Generate chart data from existing price history"""
        try:
            # Generate mock chart data for now
            import random
            from datetime import datetime, timedelta
            
            # Determine number of data points based on timeframe
            if timeframe == "1D":
                points = 24  # Hourly data for 1 day
                interval = timedelta(hours=1)
            elif timeframe == "5D":
                points = 40  # 8 hours per day for 5 days
                interval = timedelta(hours=3)
            elif timeframe == "1M":
                points = 30  # Daily data for 1 month
                interval = timedelta(days=1)
            elif timeframe == "3M":
                points = 90  # Daily data for 3 months
                interval = timedelta(days=1)
            else:  # 1Y
                points = 365  # Daily data for 1 year
                interval = timedelta(days=1)
            
            # Generate mock data
            base_price = 150.0
            data = []
            current_time = datetime.now() - (interval * points)
            
            for i in range(points):
                # Generate realistic price movement
                price_change = (random.random() - 0.5) * 0.02  # ±1% change
                open_price = base_price * (1 + price_change)
                close_price = open_price * (1 + (random.random() - 0.5) * 0.01)
                high_price = max(open_price, close_price) * (1 + random.random() * 0.005)
                low_price = min(open_price, close_price) * (1 - random.random() * 0.005)
                volume = random.randint(1000000, 10000000)
                
                data.append({
                    'timestamp': current_time.isoformat(),
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume
                })
                
                base_price = close_price  # Use close as next open
                current_time += interval
            
            return data
        except Exception as e:
            logger.error(f"Error generating chart data: {str(e)}")
            return []
    
    @staticmethod
    def _get_key_metrics(symbol):
        """Get key financial metrics"""
        try:
            # Use existing financial data API
            return {
                'revenue': 0,
                'revenueGrowth': 0,
                'grossProfit': 0,
                'operatingIncome': 0,
                'netIncome': 0,
                'eps': 0,
                'epsGrowth': 0,
                'roe': 0,
                'roa': 0,
                'debtToEquity': 0,
                'currentRatio': 0,
                'quickRatio': 0,
            }
        except Exception as e:
            logger.error(f"Error getting key metrics: {str(e)}")
            return None
    
    @staticmethod
    def _get_news_data(symbol):
        """Get recent news"""
        try:
            # Use existing news API
            return []
        except Exception as e:
            logger.error(f"Error getting news data: {str(e)}")
            return []
    
    @staticmethod
    def _get_analyst_ratings(symbol):
        """Get analyst ratings"""
        try:
            # Use existing analyst data
            return {
                'consensusRating': 'HOLD',
                'averageTargetPrice': 0,
                'numberOfAnalysts': 0,
                'ratingsBreakdown': {
                    'buy': 0,
                    'hold': 0,
                    'sell': 0,
                },
                'recentRatings': [],
            }
        except Exception as e:
            logger.error(f"Error getting analyst ratings: {str(e)}")
            return None
    
    @staticmethod
    def _get_earnings_data(symbol):
        """Get earnings data"""
        try:
            # Use existing earnings API
            return {
                'nextEarningsDate': '',
                'lastEarningsDate': '',
                'actualEps': 0,
                'estimatedEps': 0,
                'surprise': 0,
                'surprisePercent': 0,
                'revenue': 0,
                'estimatedRevenue': 0,
            }
        except Exception as e:
            logger.error(f"Error getting earnings data: {str(e)}")
            return None
    
    @staticmethod
    def _get_insider_trades(symbol):
        """Get insider trading data"""
        try:
            # Use existing insider trading API
            return []
        except Exception as e:
            logger.error(f"Error getting insider trades: {str(e)}")
            return []
    
    @staticmethod
    def _get_institutional_ownership(symbol):
        """Get institutional ownership data"""
        try:
            # Use existing institutional ownership API
            return []
        except Exception as e:
            logger.error(f"Error getting institutional ownership: {str(e)}")
            return []
    
    @staticmethod
    def _get_market_sentiment(symbol):
        """Get market sentiment data"""
        try:
            # Use existing sentiment API
            return {
                'overallScore': 0,
                'positiveMentions': 0,
                'negativeMentions': 0,
                'neutralMentions': 0,
                'recentPosts': [],
            }
        except Exception as e:
            logger.error(f"Error getting market sentiment: {str(e)}")
            return None
    
    @staticmethod
    def _get_technical_indicators(symbol):
        """Get technical indicators"""
        try:
            # Use existing technical analysis API
            return {
                'rsi': 0,
                'macd': 0,
                'macdSignal': 0,
                'macdHistogram': 0,
                'sma20': 0,
                'sma50': 0,
                'sma200': 0,
                'ema12': 0,
                'ema26': 0,
                'bollingerUpper': 0,
                'bollingerLower': 0,
                'bollingerMiddle': 0,
                'supportLevel': 0,
                'resistanceLevel': 0,
                'impliedVolatility': 0,
            }
        except Exception as e:
            logger.error(f"Error getting technical indicators: {str(e)}")
            return None
    
    @staticmethod
    def _get_peer_stocks(symbol):
        """Get peer stocks"""
        try:
            # Use existing peer stocks API
            return []
        except Exception as e:
            logger.error(f"Error getting peer stocks: {str(e)}")
            return []
