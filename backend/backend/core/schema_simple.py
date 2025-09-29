# core/schema_simple.py
import graphene
from graphene import ObjectType, String, Float, Int, List

class StockType(graphene.ObjectType):
    id = graphene.ID()
    symbol = graphene.String()
    company_name = graphene.String()
    sector = graphene.String()
    current_price = graphene.Float()
    market_cap = graphene.Float()
    pe_ratio = graphene.Float()
    dividend_yield = graphene.Float()
    dividend_score = graphene.Float()
    debt_ratio = graphene.Float()
    beginner_friendly_score = graphene.Float()
    volatility = graphene.Float()

class Query(ObjectType):
    stocks = graphene.List(StockType)
    
    def resolve_stocks(self, info):
        # Return mock stock data instead of querying the database
        return [
            StockType(
                id="1",
                symbol="AAPL",
                company_name="Apple Inc.",
                sector="Technology",
                current_price=175.50,
                market_cap=2800000000000,
                pe_ratio=28.5,
                dividend_yield=0.44,
                dividend_score=0.7,
                debt_ratio=0.15,
                beginner_friendly_score=0.9,
                volatility=0.25
            ),
            StockType(
                id="2",
                symbol="MSFT",
                company_name="Microsoft Corporation",
                sector="Technology",
                current_price=380.25,
                market_cap=2800000000000,
                pe_ratio=32.1,
                dividend_yield=0.68,
                dividend_score=0.8,
                debt_ratio=0.12,
                beginner_friendly_score=0.85,
                volatility=0.22
            ),
            StockType(
                id="3",
                symbol="TSLA",
                company_name="Tesla, Inc.",
                sector="Automotive",
                current_price=250.75,
                market_cap=800000000000,
                pe_ratio=45.2,
                dividend_yield=0.0,
                dividend_score=0.1,
                debt_ratio=0.08,
                beginner_friendly_score=0.6,
                volatility=0.45
            ),
            StockType(
                id="4",
                symbol="NVDA",
                company_name="NVIDIA Corporation",
                sector="Technology",
                current_price=450.30,
                market_cap=1100000000000,
                pe_ratio=65.8,
                dividend_yield=0.04,
                dividend_score=0.3,
                debt_ratio=0.05,
                beginner_friendly_score=0.7,
                volatility=0.35
            ),
            StockType(
                id="5",
                symbol="GOOGL",
                company_name="Alphabet Inc.",
                sector="Technology",
                current_price=140.85,
                market_cap=1800000000000,
                pe_ratio=24.3,
                dividend_yield=0.0,
                dividend_score=0.2,
                debt_ratio=0.10,
                beginner_friendly_score=0.8,
                volatility=0.28
            )
        ]

schema = graphene.Schema(query=Query)