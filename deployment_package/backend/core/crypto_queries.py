"""
GraphQL Queries for Crypto Trading Features
- Supported currencies
- Crypto prices
- Crypto ML signals
- Crypto recommendations
- Crypto SBLOC loans
- Crypto portfolio
"""
import graphene
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class CryptocurrencyType(graphene.ObjectType):
    """GraphQL type for cryptocurrency"""
    id = graphene.String()
    symbol = graphene.String()
    name = graphene.String()
    coingeckoId = graphene.String()
    isStakingAvailable = graphene.Boolean()
    minTradeAmount = graphene.Float()
    precision = graphene.Int()
    volatilityTier = graphene.String()
    isSecCompliant = graphene.Boolean()
    regulatoryStatus = graphene.String()


class CryptoPriceType(graphene.ObjectType):
    """GraphQL type for crypto price"""
    id = graphene.String()
    priceUsd = graphene.Float()
    priceBtc = graphene.Float()
    volume24h = graphene.Float()
    marketCap = graphene.Float()
    priceChange24h = graphene.Float()
    priceChangePercentage24h = graphene.Float()
    rsi14 = graphene.Float()
    volatility7d = graphene.Float()
    volatility30d = graphene.Float()
    momentumScore = graphene.Float()
    sentimentScore = graphene.Float()
    timestamp = graphene.String()


class CryptoMlSignalType(graphene.ObjectType):
    """GraphQL type for crypto ML signal"""
    symbol = graphene.String()
    predictionType = graphene.String()
    probability = graphene.Float()
    confidenceLevel = graphene.String()
    explanation = graphene.String()
    featuresUsed = graphene.List(graphene.String)
    createdAt = graphene.String()
    expiresAt = graphene.String()


class CryptoRecommendationType(graphene.ObjectType):
    """GraphQL type for crypto recommendation"""
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


class CryptoSblocLoanType(graphene.ObjectType):
    """GraphQL type for crypto SBLOC loan"""
    id = graphene.String()
    collateralQuantity = graphene.Float()
    collateralValueAtLoan = graphene.Float()
    loanAmount = graphene.Float()
    interestRate = graphene.Float()
    maintenanceMargin = graphene.Float()
    liquidationThreshold = graphene.Float()
    status = graphene.String()
    createdAt = graphene.String()
    updatedAt = graphene.String()
    cryptocurrency = graphene.Field(CryptocurrencyType)


class CryptoHoldingType(graphene.ObjectType):
    """GraphQL type for crypto holding"""
    id = graphene.String()
    quantity = graphene.Float()
    averageCost = graphene.Float()
    currentPrice = graphene.Float()
    currentValue = graphene.Float()
    unrealizedPnl = graphene.Float()
    unrealizedPnlPercentage = graphene.Float()
    stakedQuantity = graphene.Float()
    stakingRewards = graphene.Float()
    stakingApy = graphene.Float()
    isCollateralized = graphene.Boolean()
    collateralValue = graphene.Float()
    loanAmount = graphene.Float()
    createdAt = graphene.String()
    updatedAt = graphene.String()
    cryptocurrency = graphene.Field(CryptocurrencyType)


class CryptoPortfolioType(graphene.ObjectType):
    """GraphQL type for crypto portfolio"""
    id = graphene.String()
    totalValueUsd = graphene.Float()
    totalCostBasis = graphene.Float()
    totalPnl = graphene.Float()
    totalPnlPercentage = graphene.Float()
    portfolioVolatility = graphene.Float()
    sharpeRatio = graphene.Float()
    maxDrawdown = graphene.Float()
    diversificationScore = graphene.Float()
    topHoldingPercentage = graphene.Float()
    createdAt = graphene.String()
    updatedAt = graphene.String()
    holdings = graphene.List(CryptoHoldingType)


class CryptoQueries(graphene.ObjectType):
    """GraphQL queries for crypto trading features"""
    
    supported_currencies = graphene.List(
        CryptocurrencyType,
        description="Get supported cryptocurrencies"
    )
    supportedCurrencies = graphene.List(
        CryptocurrencyType,
        description="Get supported cryptocurrencies (camelCase alias)"
    )
    
    crypto_price = graphene.Field(
        CryptoPriceType,
        symbol=graphene.String(required=True),
        description="Get crypto price for a symbol"
    )
    cryptoPrice = graphene.Field(
        CryptoPriceType,
        symbol=graphene.String(required=True),
        description="Get crypto price (camelCase alias)"
    )
    
    crypto_ml_signal = graphene.Field(
        CryptoMlSignalType,
        symbol=graphene.String(required=True),
        description="Get crypto ML signal for a symbol"
    )
    cryptoMlSignal = graphene.Field(
        CryptoMlSignalType,
        symbol=graphene.String(required=True),
        description="Get crypto ML signal (camelCase alias)"
    )
    
    crypto_recommendations = graphene.List(
        CryptoRecommendationType,
        limit=graphene.Int(),
        symbols=graphene.List(graphene.String),
        description="Get crypto recommendations"
    )
    cryptoRecommendations = graphene.List(
        CryptoRecommendationType,
        limit=graphene.Int(),
        symbols=graphene.List(graphene.String),
        description="Get crypto recommendations (camelCase alias)"
    )
    
    crypto_sbloc_loans = graphene.List(
        CryptoSblocLoanType,
        symbol=graphene.String(),
        description="Get crypto SBLOC loans"
    )
    cryptoSblocLoans = graphene.List(
        CryptoSblocLoanType,
        symbol=graphene.String(),
        description="Get crypto SBLOC loans (camelCase alias)"
    )
    
    crypto_portfolio = graphene.Field(
        CryptoPortfolioType,
        description="Get user's crypto portfolio"
    )
    cryptoPortfolio = graphene.Field(
        CryptoPortfolioType,
        description="Get user's crypto portfolio (camelCase alias)"
    )
    
    def resolve_supported_currencies(self, info):
        """Get supported cryptocurrencies"""
        try:
            # In production, this would query from database or external API
            # For now, return common cryptocurrencies
            return [
                CryptocurrencyType(
                    id="btc",
                    symbol="BTC",
                    name="Bitcoin",
                    coingeckoId="bitcoin",
                    isStakingAvailable=False,
                    minTradeAmount=0.0001,
                    precision=8,
                    volatilityTier="High",
                    isSecCompliant=False,
                    regulatoryStatus="Commodity"
                ),
                CryptocurrencyType(
                    id="eth",
                    symbol="ETH",
                    name="Ethereum",
                    coingeckoId="ethereum",
                    isStakingAvailable=True,
                    minTradeAmount=0.001,
                    precision=8,
                    volatilityTier="High",
                    isSecCompliant=False,
                    regulatoryStatus="Commodity"
                ),
            ]
        except Exception as e:
            logger.error(f"Error fetching supported currencies: {e}", exc_info=True)
            return []
    
    def resolve_supportedCurrencies(self, info):
        """CamelCase alias for supported_currencies"""
        return self.resolve_supported_currencies(info)
    
    def resolve_crypto_price(self, info, symbol):
        """Get crypto price"""
        try:
            # In production, this would fetch from CoinGecko or similar API
            # For now, return mock data
            return CryptoPriceType(
                id=f"price-{symbol.lower()}",
                priceUsd=50000.0 if symbol.upper() == "BTC" else 3000.0,
                priceBtc=1.0 if symbol.upper() == "BTC" else 0.06,
                volume24h=1000000000.0,
                marketCap=1000000000000.0,
                priceChange24h=1000.0,
                priceChangePercentage24h=2.0,
                rsi14=55.0,
                volatility7d=0.05,
                volatility30d=0.15,
                momentumScore=0.7,
                sentimentScore=0.6,
                timestamp="2024-01-01T00:00:00Z"
            )
        except Exception as e:
            logger.error(f"Error fetching crypto price: {e}", exc_info=True)
            return None
    
    def resolve_cryptoPrice(self, info, symbol):
        """CamelCase alias for crypto_price"""
        return self.resolve_crypto_price(info, symbol)
    
    def resolve_crypto_ml_signal(self, info, symbol):
        """Get crypto ML signal"""
        try:
            # In production, this would query ML model predictions
            return CryptoMlSignalType(
                symbol=symbol.upper(),
                predictionType="BUY",
                probability=0.75,
                confidenceLevel="HIGH",
                explanation="Strong bullish signals detected",
                featuresUsed=["price_momentum", "volume_trend", "sentiment"],
                createdAt="2024-01-01T00:00:00Z",
                expiresAt="2024-01-02T00:00:00Z"
            )
        except Exception as e:
            logger.error(f"Error fetching crypto ML signal: {e}", exc_info=True)
            return None
    
    def resolve_cryptoMlSignal(self, info, symbol):
        """CamelCase alias for crypto_ml_signal"""
        return self.resolve_crypto_ml_signal(info, symbol)
    
    def resolve_crypto_recommendations(self, info, limit=None, symbols=None):
        """Get crypto recommendations"""
        try:
            # In production, this would query ML model or recommendation engine
            default_symbols = symbols or ["BTC", "ETH", "SOL", "ADA", "DOT"]
            recommendations = []
            for sym in default_symbols[:limit or 5]:
                recommendations.append(CryptoRecommendationType(
                    symbol=sym,
                    score=8.5,
                    probability=0.7,
                    confidenceLevel="HIGH",
                    priceUsd=50000.0 if sym == "BTC" else 3000.0,
                    volatilityTier="HIGH",
                    liquidity24hUsd=1000000000.0,
                    rationale="Strong technical indicators",
                    recommendation="BUY",
                    riskLevel="MEDIUM"
                ))
            return recommendations
        except Exception as e:
            logger.error(f"Error fetching crypto recommendations: {e}", exc_info=True)
            return []
    
    def resolve_cryptoRecommendations(self, info, limit=None, symbols=None):
        """CamelCase alias for crypto_recommendations"""
        return self.resolve_crypto_recommendations(info, limit, symbols)
    
    def resolve_crypto_sbloc_loans(self, info, symbol=None):
        """Get crypto SBLOC loans"""
        try:
            # In production, this would query user's loans from database
            return []
        except Exception as e:
            logger.error(f"Error fetching crypto SBLOC loans: {e}", exc_info=True)
            return []
    
    def resolve_cryptoSblocLoans(self, info, symbol=None):
        """CamelCase alias for crypto_sbloc_loans"""
        return self.resolve_crypto_sbloc_loans(info, symbol)
    
    def resolve_crypto_portfolio(self, info):
        """Get user's crypto portfolio"""
        try:
            # In production, this would query user's portfolio from database
            return CryptoPortfolioType(
                id="portfolio-1",
                totalValueUsd=125000.0,
                totalCostBasis=100000.0,
                totalPnl=25000.0,
                totalPnlPercentage=25.0,
                portfolioVolatility=0.35,
                sharpeRatio=1.2,
                maxDrawdown=-0.15,
                diversificationScore=0.75,
                topHoldingPercentage=0.35,
                createdAt="2024-01-01T00:00:00Z",
                updatedAt="2024-01-01T00:00:00Z",
                holdings=[]
            )
        except Exception as e:
            logger.error(f"Error fetching crypto portfolio: {e}", exc_info=True)
            return None
    
    def resolve_cryptoPortfolio(self, info):
        """CamelCase alias for crypto_portfolio"""
        return self.resolve_crypto_portfolio(info)
    
    # Alpaca Crypto Trading Queries
    crypto_assets = graphene.List(
        CryptocurrencyType,
        status=graphene.String(),
        description="Get crypto assets (for trading)"
    )
    cryptoAssets = graphene.List(
        CryptocurrencyType,
        status=graphene.String(),
        description="Get crypto assets (camelCase alias)"
    )
    
    alpaca_crypto_account = graphene.Field(
        'core.crypto_mutations.AlpacaCryptoAccountType',
        userId=graphene.Int(required=True),
        description="Get Alpaca crypto account"
    )
    alpacaCryptoAccount = graphene.Field(
        'core.crypto_mutations.AlpacaCryptoAccountType',
        userId=graphene.Int(required=True),
        description="Get Alpaca crypto account (camelCase alias)"
    )
    
    alpaca_crypto_balances = graphene.List(
        'core.crypto_mutations.AlpacaCryptoBalanceType',
        accountId=graphene.Int(required=True),
        description="Get Alpaca crypto balances"
    )
    alpacaCryptoBalances = graphene.List(
        'core.crypto_mutations.AlpacaCryptoBalanceType',
        accountId=graphene.Int(required=True),
        description="Get Alpaca crypto balances (camelCase alias)"
    )
    
    alpaca_crypto_orders = graphene.List(
        'core.crypto_mutations.AlpacaCryptoOrderType',
        accountId=graphene.Int(required=True),
        status=graphene.String(),
        description="Get Alpaca crypto orders"
    )
    alpacaCryptoOrders = graphene.List(
        'core.crypto_mutations.AlpacaCryptoOrderType',
        accountId=graphene.Int(required=True),
        status=graphene.String(),
        description="Get Alpaca crypto orders (camelCase alias)"
    )
    
    def resolve_crypto_assets(self, info, status=None):
        """Get crypto assets for trading"""
        return self.resolve_supported_currencies(info)
    
    def resolve_cryptoAssets(self, info, status=None):
        """CamelCase alias for crypto_assets"""
        return self.resolve_crypto_assets(info, status)
    
    def resolve_alpaca_crypto_account(self, info, userId):
        """Get Alpaca crypto account"""
        try:
            from .crypto_mutations import AlpacaCryptoAccountType
            # In production, query from database
            return AlpacaCryptoAccountType(
                id="1",
                status="ACTIVE",
                alpacaCryptoAccountId="alpaca-123",
                isApproved=True,
                usdBalance=10000.0,
                totalCryptoValue=10500.0,
                createdAt="2024-01-01T00:00:00Z"
            )
        except Exception as e:
            logger.error(f"Error resolving Alpaca crypto account: {e}", exc_info=True)
            return None
    
    def resolve_alpacaCryptoAccount(self, info, userId):
        """CamelCase alias for alpaca_crypto_account"""
        return self.resolve_alpaca_crypto_account(info, userId)
    
    def resolve_alpaca_crypto_balances(self, info, accountId):
        """Get Alpaca crypto balances"""
        try:
            from .crypto_mutations import AlpacaCryptoBalanceType
            # In production, query from database
            return [
                AlpacaCryptoBalanceType(
                    id="1",
                    symbol="BTC",
                    totalAmount=0.5,
                    availableAmount=0.3,
                    usdValue=25000.0,
                    updatedAt="2024-01-01T00:00:00Z"
                )
            ]
        except Exception as e:
            logger.error(f"Error resolving Alpaca crypto balances: {e}", exc_info=True)
            return []
    
    def resolve_alpacaCryptoBalances(self, info, accountId):
        """CamelCase alias for alpaca_crypto_balances"""
        return self.resolve_alpaca_crypto_balances(info, accountId)
    
    def resolve_alpaca_crypto_orders(self, info, accountId, status=None):
        """Get Alpaca crypto orders"""
        try:
            from .crypto_mutations import AlpacaCryptoOrderType
            # In production, query from database
            return []
        except Exception as e:
            logger.error(f"Error resolving Alpaca crypto orders: {e}", exc_info=True)
            return []
    
    def resolve_alpacaCryptoOrders(self, info, accountId, status=None):
        """CamelCase alias for alpaca_crypto_orders"""
        return self.resolve_alpaca_crypto_orders(info, accountId, status)

