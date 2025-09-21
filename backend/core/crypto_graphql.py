"""
GraphQL types and resolvers for crypto functionality
"""

import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from .crypto_models import (
    Cryptocurrency, CryptoPrice, CryptoPortfolio, CryptoHolding,
    CryptoTrade, CryptoMLPrediction, CryptoSBLOCLoan, CryptoEducationProgress
)
from .crypto_ml_engine import CryptoMLPredictionService
from .auth_utils import get_current_user_from_info
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# GraphQL Types
class CryptocurrencyType(DjangoObjectType):
    class Meta:
        model = Cryptocurrency
        fields = "__all__"
    
    def resolve_volatilityTier(self, info):
        """Resolve volatilityTier field from volatility_tier model field"""
        return self.volatility_tier
    
    def resolve_coingeckoId(self, info):
        """Resolve coingeckoId field from coingecko_id model field"""
        return self.coingecko_id
    
    def resolve_isStakingAvailable(self, info):
        """Resolve isStakingAvailable field from is_staking_available model field"""
        return self.is_staking_available
    
    def resolve_minTradeAmount(self, info):
        """Resolve minTradeAmount field from min_trade_amount model field"""
        return float(self.min_trade_amount)
    
    def resolve_isSecCompliant(self, info):
        """Resolve isSecCompliant field from is_sec_compliant model field"""
        return self.is_sec_compliant
    
    def resolve_regulatoryStatus(self, info):
        """Resolve regulatoryStatus field from regulatory_status model field"""
        return self.regulatory_status


class CryptoPriceType(DjangoObjectType):
    class Meta:
        model = CryptoPrice
        fields = "__all__"


class CryptoHoldingType(DjangoObjectType):
    class Meta:
        model = CryptoHolding
        fields = "__all__"


class CryptoTradeType(DjangoObjectType):
    class Meta:
        model = CryptoTrade
        fields = "__all__"


class CryptoMLPredictionType(DjangoObjectType):
    class Meta:
        model = CryptoMLPrediction
        fields = "__all__"
    
    def resolve_expiresAt(self, info):
        """Resolve expiresAt field from expires_at model field"""
        return self.expires_at
    
    def resolve_createdAt(self, info):
        """Resolve createdAt field from created_at model field"""
        return self.created_at
    
    def resolve_predictionType(self, info):
        """Resolve predictionType field from prediction_type model field"""
        return self.prediction_type
    
    def resolve_confidenceLevel(self, info):
        """Resolve confidenceLevel field from confidence_level model field"""
        return self.confidence_level
    
    def resolve_featuresUsed(self, info):
        """Resolve featuresUsed field from features_used model field"""
        return self.features_used
    
    def resolve_modelVersion(self, info):
        """Resolve modelVersion field from model_version model field"""
        return self.model_version
    
    def resolve_predictionHorizonHours(self, info):
        """Resolve predictionHorizonHours field from prediction_horizon_hours model field"""
        return self.prediction_horizon_hours
    
    def resolve_wasCorrect(self, info):
        """Resolve wasCorrect field from was_correct model field"""
        return self.was_correct
    
    def resolve_actualReturn(self, info):
        """Resolve actualReturn field from actual_return model field"""
        return self.actual_return


class CryptoSBLOCLoanType(DjangoObjectType):
    class Meta:
        model = CryptoSBLOCLoan
        fields = "__all__"


class CryptoEducationProgressType(DjangoObjectType):
    class Meta:
        model = CryptoEducationProgress
        fields = "__all__"


class CryptoPortfolioType(DjangoObjectType):
    holdings = graphene.List(CryptoHoldingType)
    
    class Meta:
        model = CryptoPortfolio
        fields = "__all__"
    
    def resolve_holdings(self, info):
        return self.holdings.all()


class CryptoAnalyticsType(graphene.ObjectType):
    """Crypto portfolio analytics"""
    total_value_usd = graphene.Float()
    total_cost_basis = graphene.Float()
    total_pnl = graphene.Float()
    total_pnl_percentage = graphene.Float()
    portfolio_volatility = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    diversification_score = graphene.Float()
    top_holding_percentage = graphene.Float()
    sector_allocation = graphene.JSONString()
    best_performer = graphene.JSONString()
    worst_performer = graphene.JSONString()
    last_updated = graphene.DateTime()


class CryptoMLSignalType(graphene.ObjectType):
    """ML prediction signal"""
    symbol = graphene.String()
    prediction_type = graphene.String()
    probability = graphene.Float()
    confidence_level = graphene.String()
    explanation = graphene.String()
    features_used = graphene.JSONString()
    created_at = graphene.DateTime()
    expires_at = graphene.DateTime()
    
    def resolve_expiresAt(self, info):
        """Resolve expiresAt field from expires_at model field"""
        return self.expires_at
    
    def resolve_createdAt(self, info):
        """Resolve createdAt field from created_at model field"""
        return self.created_at
    
    def resolve_predictionType(self, info):
        """Resolve predictionType field from prediction_type model field"""
        return self.prediction_type
    
    def resolve_confidenceLevel(self, info):
        """Resolve confidenceLevel field from confidence_level model field"""
        return self.confidence_level
    
    def resolve_featuresUsed(self, info):
        """Resolve featuresUsed field from features_used model field"""
        return self.features_used


# Queries
class CryptoQuery(graphene.ObjectType):
    """Crypto-related GraphQL queries"""
    
    # Get supported cryptocurrencies
    supported_currencies = graphene.List(CryptocurrencyType)
    
    # Get crypto price
    crypto_price = graphene.Field(
        CryptoPriceType,
        symbol=graphene.String(required=True)
    )
    
    # Get user's crypto portfolio
    crypto_portfolio = graphene.Field(CryptoPortfolioType)
    
    # Get crypto analytics
    crypto_analytics = graphene.Field(CryptoAnalyticsType)
    
    # Get crypto trades
    crypto_trades = graphene.List(
        CryptoTradeType,
        symbol=graphene.String(),
        limit=graphene.Int(default_value=50)
    )
    
    # Get ML predictions
    crypto_predictions = graphene.List(
        CryptoMLPredictionType,
        symbol=graphene.String(required=True)
    )
    
    # Get ML signal (latest prediction)
    crypto_ml_signal = graphene.Field(
        CryptoMLSignalType,
        symbol=graphene.String(required=True)
    )
    
    # Get SBLOC loans
    crypto_sbloc_loans = graphene.List(CryptoSBLOCLoanType)
    
    # Get education progress
    crypto_education_progress = graphene.List(CryptoEducationProgressType)
    
    def resolve_supported_currencies(self, info):
        """Get list of supported cryptocurrencies"""
        return Cryptocurrency.objects.filter(is_active=True).order_by('symbol')
    
    def resolve_crypto_price(self, info, symbol):
        """Get current price for a cryptocurrency"""
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            return CryptoPrice.objects.filter(cryptocurrency=currency).first()
        except Cryptocurrency.DoesNotExist:
            return None
    
    def resolve_crypto_portfolio(self, info):
        """Get user's crypto portfolio"""
        user = get_current_user_from_info(info)
        if not user:
            return None
        
        portfolio, created = CryptoPortfolio.objects.get_or_create(user=user)
        return portfolio
    
    def resolve_crypto_analytics(self, info):
        """Get detailed crypto portfolio analytics"""
        user = get_current_user_from_info(info)
        if not user:
            return None
        
        try:
            portfolio, _ = CryptoPortfolio.objects.get_or_create(user=user)
            holdings = portfolio.holdings.all()
            total_value = float(portfolio.total_value_usd)
            
            # Calculate sector allocation
            sector_allocation = {}
            for holding in holdings:
                tier = holding.cryptocurrency.volatility_tier
                value = float(holding.current_value)
                if tier not in sector_allocation:
                    sector_allocation[tier] = 0
                sector_allocation[tier] += value
            
            # Normalize to percentages
            for tier in sector_allocation:
                sector_allocation[tier] = (sector_allocation[tier] / total_value * 100) if total_value > 0 else 0
            
            # Find best and worst performers
            best_performer = None
            worst_performer = None
            if holdings:
                performers = []
                for holding in holdings:
                    pnl_pct = float(holding.unrealized_pnl_percentage)
                    performers.append({
                        "symbol": holding.cryptocurrency.symbol,
                        "pnl_percentage": pnl_pct
                    })
                
                performers.sort(key=lambda x: x["pnl_percentage"], reverse=True)
                if performers:
                    best_performer = performers[0]
                    worst_performer = performers[-1]
            
            return CryptoAnalyticsType(
                total_value_usd=float(portfolio.total_value_usd),
                total_cost_basis=float(portfolio.total_cost_basis),
                total_pnl=float(portfolio.total_pnl),
                total_pnl_percentage=float(portfolio.total_pnl_percentage),
                portfolio_volatility=float(portfolio.portfolio_volatility),
                sharpe_ratio=float(portfolio.sharpe_ratio),
                max_drawdown=float(portfolio.max_drawdown),
                diversification_score=float(portfolio.diversification_score),
                top_holding_percentage=float(portfolio.top_holding_percentage),
                sector_allocation=sector_allocation,
                best_performer=best_performer,
                worst_performer=worst_performer,
                last_updated=portfolio.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error resolving crypto analytics: {e}")
            return None
    
    def resolve_crypto_trades(self, info, symbol=None, limit=50):
        """Get user's crypto trades"""
        user = get_current_user_from_info(info)
        if not user:
            return []
        
        trades = CryptoTrade.objects.filter(user=user)
        
        if symbol:
            try:
                currency = Cryptocurrency.objects.get(symbol=symbol.upper())
                trades = trades.filter(cryptocurrency=currency)
            except Cryptocurrency.DoesNotExist:
                return []
        
        return trades.order_by('-execution_time')[:limit]
    
    def resolve_crypto_predictions(self, info, symbol):
        """Get ML predictions for a cryptocurrency"""
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            return CryptoMLPrediction.objects.filter(
                cryptocurrency=currency
            ).order_by('-created_at')[:10]
        except Cryptocurrency.DoesNotExist:
            return []
    
    def resolve_crypto_ml_signal(self, info, symbol):
        """Get latest ML signal for a cryptocurrency"""
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            latest_prediction = CryptoMLPrediction.objects.filter(
                cryptocurrency=currency
            ).order_by('-created_at').first()
            
            if not latest_prediction:
                return None
            
            return CryptoMLSignalType(
                symbol=currency.symbol,
                prediction_type=latest_prediction.prediction_type,
                probability=float(latest_prediction.probability),
                confidence_level=latest_prediction.confidence_level,
                explanation=f"Probability of {latest_prediction.prediction_type.lower()}: {latest_prediction.probability:.1%}",
                features_used=latest_prediction.features_used,
                created_at=latest_prediction.created_at,
                expires_at=latest_prediction.expires_at
            )
            
        except Cryptocurrency.DoesNotExist:
            return None
    
    def resolve_crypto_sbloc_loans(self, info):
        """Get user's SBLOC loans"""
        user = get_current_user_from_info(info)
        if not user:
            return []
        
        return CryptoSBLOCLoan.objects.filter(user=user).order_by('-created_at')
    
    def resolve_crypto_education_progress(self, info):
        """Get user's crypto education progress"""
        user = get_current_user_from_info(info)
        if not user:
            return []
        
        return CryptoEducationProgress.objects.filter(user=user).order_by('module_type', 'module_name')


# Mutations
class ExecuteCryptoTrade(graphene.Mutation):
    """Execute a crypto trade"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        trade_type = graphene.String(required=True)
        quantity = graphene.Float(required=True)
        price_per_unit = graphene.Float()
    
    success = graphene.Boolean()
    trade_id = graphene.Int()
    order_id = graphene.String()
    message = graphene.String()
    
    def mutate(self, info, symbol, trade_type, quantity, price_per_unit=None):
        user = get_current_user_from_info(info)
        if not user:
            return ExecuteCryptoTrade(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Validate trade type
            if trade_type not in ['BUY', 'SELL']:
                return ExecuteCryptoTrade(
                    success=False,
                    message="Invalid trade type"
                )
            
            # Get cryptocurrency
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            
            # Get current price if not provided
            if price_per_unit is None:
                latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
                if not latest_price:
                    return ExecuteCryptoTrade(
                        success=False,
                        message="Price data not available"
                    )
                price_per_unit = float(latest_price.price_usd)
            
            # Calculate total amount
            total_amount = quantity * price_per_unit
            
            # Check minimum trade amount
            if total_amount < float(currency.min_trade_amount):
                return ExecuteCryptoTrade(
                    success=False,
                    message=f"Trade amount must be at least ${currency.min_trade_amount}"
                )
            
            # Create trade record
            from datetime import datetime
            trade = CryptoTrade.objects.create(
                user=user,
                cryptocurrency=currency,
                trade_type=trade_type,
                quantity=quantity,
                price_per_unit=price_per_unit,
                total_amount=total_amount,
                order_id=f"{trade_type}_{currency.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                status='COMPLETED'
            )
            
            return ExecuteCryptoTrade(
                success=True,
                trade_id=trade.id,
                order_id=trade.order_id,
                message="Trade executed successfully"
            )
            
        except Cryptocurrency.DoesNotExist:
            return ExecuteCryptoTrade(
                success=False,
                message="Cryptocurrency not found"
            )
        except Exception as e:
            logger.error(f"Error executing crypto trade: {e}")
            return ExecuteCryptoTrade(
                success=False,
                message="Failed to execute trade"
            )


class CreateSBLOCLoan(graphene.Mutation):
    """Create a SBLOC loan backed by crypto"""
    
    class Arguments:
        symbol = graphene.String(required=True)
        collateral_quantity = graphene.Float(required=True)
        loan_amount = graphene.Float(required=True)
    
    success = graphene.Boolean()
    loan_id = graphene.Int()
    message = graphene.String()
    
    def mutate(self, info, symbol, collateral_quantity, loan_amount):
        user = get_current_user_from_info(info)
        if not user:
            return CreateSBLOCLoan(
                success=False,
                message="Authentication required"
            )
        
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            
            # Get current price
            latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
            if not latest_price:
                return CreateSBLOCLoan(
                    success=False,
                    message="Price data not available"
                )
            
            current_price = float(latest_price.price_usd)
            collateral_value = collateral_quantity * current_price
            
            # Check LTV
            ltv = loan_amount / collateral_value
            if ltv > 0.5:
                return CreateSBLOCLoan(
                    success=False,
                    message="Loan amount exceeds maximum LTV of 50%"
                )
            
            # Create loan
            loan = CryptoSBLOCLoan.objects.create(
                user=user,
                cryptocurrency=currency,
                collateral_quantity=collateral_quantity,
                collateral_value_at_loan=collateral_value,
                loan_amount=loan_amount,
                interest_rate=0.05,  # 5% default
                status='ACTIVE'
            )
            
            return CreateSBLOCLoan(
                success=True,
                loan_id=loan.id,
                message="SBLOC loan created successfully"
            )
            
        except Cryptocurrency.DoesNotExist:
            return CreateSBLOCLoan(
                success=False,
                message="Cryptocurrency not found"
            )
        except Exception as e:
            logger.error(f"Error creating SBLOC loan: {e}")
            return CreateSBLOCLoan(
                success=False,
                message="Failed to create SBLOC loan"
            )


class GenerateMLPrediction(graphene.Mutation):
    """Generate ML prediction for a cryptocurrency"""
    
    class Arguments:
        symbol = graphene.String(required=True)
    
    success = graphene.Boolean()
    prediction_id = graphene.Int()
    probability = graphene.Float()
    explanation = graphene.String()
    message = graphene.String()
    
    def mutate(self, info, symbol):
        user = get_current_user_from_info(info)
        if not user:
            return GenerateMLPrediction(
                success=False,
                message="Authentication required"
            )
        
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            
            # Get recent price data
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            price_data = CryptoPrice.objects.filter(
                cryptocurrency=currency,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')
            
            if len(price_data) < 100:
                return GenerateMLPrediction(
                    success=False,
                    message="Insufficient price data for prediction"
                )
            
            # Convert to DataFrame for ML engine
            import pandas as pd
            df_data = []
            for price in price_data:
                df_data.append({
                    'timestamp': price.timestamp,
                    'open': float(price.price_usd),
                    'high': float(price.price_usd),
                    'low': float(price.price_usd),
                    'close': float(price.price_usd),
                    'volume': float(price.volume_24h) if price.volume_24h else 1000000,
                    'funding_rate': 0.0,
                    'open_interest': 1000000
                })
            
            df = pd.DataFrame(df_data)
            
            # Generate prediction
            from .crypto_ml_engine import CryptoMLPredictionService
            ml_service = CryptoMLPredictionService()
            prediction = ml_service.predict_big_day(df, currency.symbol)
            
            if not prediction:
                return GenerateMLPrediction(
                    success=False,
                    message="Failed to generate prediction"
                )
            
            # Save prediction
            ml_prediction = CryptoMLPrediction.objects.create(
                cryptocurrency=currency,
                prediction_type=prediction.prediction_type,
                probability=prediction.probability,
                confidence_level=prediction.confidence_level,
                features_used=prediction.features_used,
                model_version='v1.0',
                prediction_horizon_hours=prediction.prediction_horizon_hours,
                expires_at=prediction.expires_at
            )
            
            return GenerateMLPrediction(
                success=True,
                prediction_id=ml_prediction.id,
                probability=prediction.probability,
                explanation=prediction.explanation,
                message="Prediction generated successfully"
            )
            
        except Cryptocurrency.DoesNotExist:
            return GenerateMLPrediction(
                success=False,
                message="Cryptocurrency not found"
            )
        except Exception as e:
            logger.error(f"Error generating ML prediction: {e}")
            return GenerateMLPrediction(
                success=False,
                message="Failed to generate prediction"
            )


class CryptoMutation(graphene.ObjectType):
    """Crypto-related GraphQL mutations"""
    execute_crypto_trade = ExecuteCryptoTrade.Field()
    create_sbloc_loan = CreateSBLOCLoan.Field()
    generate_ml_prediction = GenerateMLPrediction.Field()
