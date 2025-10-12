# core/schema_simple.py
import graphene
from graphene import ObjectType, String, Float, Int, List

class StockType(graphene.ObjectType):
    id = graphene.ID()
    symbol = graphene.String()  # Mobile app expects 'symbol', not 'ticker'
    companyName = graphene.String()  # Changed from company_name to companyName (camelCase)
    sector = graphene.String()
    industry = graphene.String()
    currentPrice = graphene.Float()  # Changed from current_price to currentPrice
    marketCap = graphene.Float()  # Changed from market_cap to marketCap
    peRatio = graphene.Float()  # Changed from pe_ratio to peRatio
    dividendYield = graphene.Float()  # Changed from dividend_yield to dividendYield
    dividendScore = graphene.Float()  # Changed from dividend_score to dividendScore
    debtRatio = graphene.Float()  # Changed from debt_ratio to debtRatio
    beginnerFriendlyScore = graphene.Float()  # Changed from beginner_friendly_score to beginnerFriendlyScore
    volatility = graphene.Float()

# Mock stock data that matches frontend expectations
MOCK_STOCKS = [
    {
        "id": "1",
        "symbol": "AAPL",
        "companyName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "currentPrice": 175.50,
        "marketCap": 2800000000000,
        "peRatio": 28.5,
        "dividendYield": 0.44,
        "dividendScore": 0.7,
        "debtRatio": 0.15,
        "beginnerFriendlyScore": 0.9,
        "volatility": 0.25
    },
    {
        "id": "2",
        "symbol": "MSFT",
        "companyName": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software",
        "currentPrice": 380.25,
        "marketCap": 2800000000000,
        "peRatio": 32.1,
        "dividendYield": 0.68,
        "dividendScore": 0.8,
        "debtRatio": 0.12,
        "beginnerFriendlyScore": 0.85,
        "volatility": 0.22
    },
    {
        "id": "3",
        "symbol": "TSLA",
        "companyName": "Tesla, Inc.",
        "sector": "Automotive",
        "industry": "Electric Vehicles",
        "currentPrice": 250.75,
        "marketCap": 800000000000,
        "peRatio": 45.2,
        "dividendYield": 0.0,
        "dividendScore": 0.1,
        "debtRatio": 0.08,
        "beginnerFriendlyScore": 0.6,
        "volatility": 0.45
    },
    {
        "id": "4",
        "symbol": "NVDA",
        "companyName": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "currentPrice": 450.30,
        "marketCap": 1100000000000,
        "peRatio": 65.8,
        "dividendYield": 0.04,
        "dividendScore": 0.3,
        "debtRatio": 0.05,
        "beginnerFriendlyScore": 0.7,
        "volatility": 0.35
    },
    {
        "id": "5",
        "symbol": "GOOGL",
        "companyName": "Alphabet Inc.",
        "sector": "Technology",
        "industry": "Internet Services",
        "currentPrice": 140.85,
        "marketCap": 1800000000000,
        "peRatio": 24.3,
        "dividendYield": 0.0,
        "dividendScore": 0.2,
        "debtRatio": 0.10,
        "beginnerFriendlyScore": 0.8,
        "volatility": 0.28
    }
]

class Query(ObjectType):
    stocks = graphene.List(StockType)
    beginnerFriendlyStocks = graphene.List(StockType)
    
    def resolve_stocks(self, info, search=None, limit=10, offset=0):
        """Return mock stock data - no database queries"""
        print("DEBUG: resolve_stocks called - returning mock data")
        return [StockType(**stock) for stock in MOCK_STOCKS]
    
    def resolve_beginnerFriendlyStocks(self, info, limit=10):
        """Return beginner-friendly stocks from mock data"""
        print("DEBUG: resolve_beginnerFriendlyStocks called - returning mock data")
        # Filter stocks with high beginner-friendly scores
        beginner_stocks = [stock for stock in MOCK_STOCKS if stock.get('beginnerFriendlyScore', 0) >= 0.7]
        return [StockType(**stock) for stock in beginner_stocks[:limit]]

schema = graphene.Schema(query=Query)