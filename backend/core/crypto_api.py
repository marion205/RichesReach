"""
Crypto Trading API endpoints
Provides REST and GraphQL endpoints for crypto functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .crypto_models import (
    Cryptocurrency, CryptoPrice, CryptoPortfolio, CryptoHolding, 
    CryptoTrade, CryptoMLPrediction, CryptoSBLOCLoan
)
from .crypto_ml_engine import CryptoMLPredictionService
from .auth_utils import get_current_user

logger = logging.getLogger(__name__)

# Create router
crypto_router = APIRouter(prefix="/api/crypto", tags=["crypto"])

# Initialize ML service
ml_service = CryptoMLPredictionService()


@crypto_router.get("/currencies")
async def get_supported_currencies():
    """Get list of supported cryptocurrencies"""
    try:
        currencies = Cryptocurrency.objects.filter(is_active=True).values(
            'symbol', 'name', 'coingecko_id', 'is_staking_available',
            'min_trade_amount', 'precision', 'volatility_tier',
            'is_sec_compliant', 'regulatory_status'
        )
        return {"currencies": list(currencies)}
    except Exception as e:
        logger.error(f"Error fetching currencies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch currencies")


@crypto_router.get("/prices/{symbol}")
async def get_crypto_price(symbol: str):
    """Get current price and data for a cryptocurrency"""
    try:
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
        
        if not latest_price:
            raise HTTPException(status_code=404, detail="Price data not available")
        
        return {
            "symbol": currency.symbol,
            "name": currency.name,
            "price_usd": float(latest_price.price_usd),
            "price_btc": float(latest_price.price_btc) if latest_price.price_btc else None,
            "volume_24h": float(latest_price.volume_24h) if latest_price.volume_24h else None,
            "market_cap": float(latest_price.market_cap) if latest_price.market_cap else None,
            "price_change_24h": float(latest_price.price_change_24h) if latest_price.price_change_24h else None,
            "price_change_percentage_24h": float(latest_price.price_change_percentage_24h) if latest_price.price_change_percentage_24h else None,
            "rsi_14": float(latest_price.rsi_14) if latest_price.rsi_14 else None,
            "volatility_7d": float(latest_price.volatility_7d) if latest_price.volatility_7d else None,
            "volatility_30d": float(latest_price.volatility_30d) if latest_price.volatility_30d else None,
            "momentum_score": float(latest_price.momentum_score) if latest_price.momentum_score else None,
            "sentiment_score": float(latest_price.sentiment_score) if latest_price.sentiment_score else None,
            "timestamp": latest_price.timestamp.isoformat()
        }
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price data")


@crypto_router.get("/portfolio")
async def get_crypto_portfolio(current_user=Depends(get_current_user)):
    """Get user's crypto portfolio"""
    try:
        portfolio, created = CryptoPortfolio.objects.get_or_create(user=current_user)
        
        if created:
            return {
                "total_value_usd": 0.0,
                "total_cost_basis": 0.0,
                "total_pnl": 0.0,
                "total_pnl_percentage": 0.0,
                "portfolio_volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "diversification_score": 0.0,
                "top_holding_percentage": 0.0,
                "holdings": [],
                "created_at": portfolio.created_at.isoformat(),
                "updated_at": portfolio.updated_at.isoformat()
            }
        
        holdings = []
        for holding in portfolio.holdings.all():
            holdings.append({
                "symbol": holding.cryptocurrency.symbol,
                "name": holding.cryptocurrency.name,
                "quantity": float(holding.quantity),
                "average_cost": float(holding.average_cost),
                "current_price": float(holding.current_price),
                "current_value": float(holding.current_value),
                "unrealized_pnl": float(holding.unrealized_pnl),
                "unrealized_pnl_percentage": float(holding.unrealized_pnl_percentage),
                "staked_quantity": float(holding.staked_quantity),
                "staking_rewards": float(holding.staking_rewards),
                "staking_apy": float(holding.staking_apy) if holding.staking_apy else None,
                "is_collateralized": holding.is_collateralized,
                "collateral_value": float(holding.collateral_value),
                "loan_amount": float(holding.loan_amount)
            })
        
        return {
            "total_value_usd": float(portfolio.total_value_usd),
            "total_cost_basis": float(portfolio.total_cost_basis),
            "total_pnl": float(portfolio.total_pnl),
            "total_pnl_percentage": float(portfolio.total_pnl_percentage),
            "portfolio_volatility": float(portfolio.portfolio_volatility),
            "sharpe_ratio": float(portfolio.sharpe_ratio),
            "max_drawdown": float(portfolio.max_drawdown),
            "diversification_score": float(portfolio.diversification_score),
            "top_holding_percentage": float(portfolio.top_holding_percentage),
            "holdings": holdings,
            "created_at": portfolio.created_at.isoformat(),
            "updated_at": portfolio.updated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio")


@crypto_router.post("/trade")
async def execute_crypto_trade(
    symbol: str,
    trade_type: str,
    quantity: float,
    price_per_unit: Optional[float] = None,
    current_user=Depends(get_current_user)
):
    """Execute a crypto trade"""
    try:
        # Validate trade type
        if trade_type not in ['BUY', 'SELL']:
            raise HTTPException(status_code=400, detail="Invalid trade type")
        
        # Get cryptocurrency
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        
        # Get current price if not provided
        if price_per_unit is None:
            latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
            if not latest_price:
                raise HTTPException(status_code=404, detail="Price data not available")
            price_per_unit = float(latest_price.price_usd)
        
        # Calculate total amount
        total_amount = quantity * price_per_unit
        
        # Check minimum trade amount
        if total_amount < float(currency.min_trade_amount):
            raise HTTPException(
                status_code=400, 
                detail=f"Trade amount must be at least ${currency.min_trade_amount}"
            )
        
        # Create trade record
        trade = CryptoTrade.objects.create(
            user=current_user,
            cryptocurrency=currency,
            trade_type=trade_type,
            quantity=Decimal(str(quantity)),
            price_per_unit=Decimal(str(price_per_unit)),
            total_amount=Decimal(str(total_amount)),
            order_id=f"{trade_type}_{currency.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status='COMPLETED'
        )
        
        # Update portfolio (simplified - in production, this would be more complex)
        portfolio, _ = CryptoPortfolio.objects.get_or_create(user=current_user)
        holding, created = CryptoHolding.objects.get_or_create(
            portfolio=portfolio,
            cryptocurrency=currency
        )
        
        if trade_type == 'BUY':
            if created:
                holding.quantity = Decimal(str(quantity))
                holding.average_cost = Decimal(str(price_per_unit))
            else:
                # Update average cost
                total_cost = (holding.quantity * holding.average_cost) + (Decimal(str(quantity)) * Decimal(str(price_per_unit)))
                total_quantity = holding.quantity + Decimal(str(quantity))
                holding.average_cost = total_cost / total_quantity
                holding.quantity = total_quantity
        else:  # SELL
            if created or holding.quantity < Decimal(str(quantity)):
                raise HTTPException(status_code=400, detail="Insufficient holdings")
            holding.quantity -= Decimal(str(quantity))
        
        # Update current values
        holding.current_price = Decimal(str(price_per_unit))
        holding.current_value = holding.quantity * holding.current_price
        holding.unrealized_pnl = (holding.current_price - holding.average_cost) * holding.quantity
        holding.unrealized_pnl_percentage = (holding.unrealized_pnl / (holding.average_cost * holding.quantity)) * 100
        holding.save()
        
        return {
            "trade_id": trade.id,
            "order_id": trade.order_id,
            "symbol": currency.symbol,
            "trade_type": trade_type,
            "quantity": float(quantity),
            "price_per_unit": price_per_unit,
            "total_amount": total_amount,
            "status": "COMPLETED",
            "execution_time": trade.execution_time.isoformat()
        }
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute trade")


@crypto_router.get("/predictions/{symbol}")
async def get_crypto_predictions(symbol: str, current_user=Depends(get_current_user)):
    """Get ML predictions for a cryptocurrency"""
    try:
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        
        # Get recent predictions
        predictions = CryptoMLPrediction.objects.filter(
            cryptocurrency=currency,
            expires_at__gt=datetime.now()
        ).order_by('-created_at')[:5]
        
        result = []
        for pred in predictions:
            result.append({
                "prediction_type": pred.prediction_type,
                "probability": float(pred.probability),
                "confidence_level": pred.confidence_level,
                "features_used": pred.features_used,
                "model_version": pred.model_version,
                "prediction_horizon_hours": pred.prediction_horizon_hours,
                "created_at": pred.created_at.isoformat(),
                "expires_at": pred.expires_at.isoformat(),
                "was_correct": pred.was_correct,
                "actual_return": float(pred.actual_return) if pred.actual_return else None
            })
        
        return {"symbol": currency.symbol, "predictions": result}
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except Exception as e:
        logger.error(f"Error fetching predictions for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch predictions")


@crypto_router.post("/predictions/generate")
async def generate_crypto_prediction(
    symbol: str,
    current_user=Depends(get_current_user)
):
    """Generate a new ML prediction for a cryptocurrency"""
    try:
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        
        # Get recent price data (last 365 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        price_data = CryptoPrice.objects.filter(
            cryptocurrency=currency,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        if len(price_data) < 100:  # Need sufficient data
            raise HTTPException(status_code=400, detail="Insufficient price data for prediction")
        
        # Convert to DataFrame for ML engine
        df_data = []
        for price in price_data:
            df_data.append({
                'timestamp': price.timestamp,
                'open': float(price.price_usd),  # Simplified - using price_usd for all OHLC
                'high': float(price.price_usd),
                'low': float(price.price_usd),
                'close': float(price.price_usd),
                'volume': float(price.volume_24h) if price.volume_24h else 1000000,
                'funding_rate': 0.0,  # Placeholder
                'open_interest': 1000000  # Placeholder
            })
        
        import pandas as pd
        df = pd.DataFrame(df_data)
        
        # Generate prediction
        prediction = ml_service.predict_big_day(df, currency.symbol)
        
        if not prediction:
            raise HTTPException(status_code=500, detail="Failed to generate prediction")
        
        # Save prediction to database
        ml_prediction = CryptoMLPrediction.objects.create(
            cryptocurrency=currency,
            prediction_type=prediction.prediction_type,
            probability=Decimal(str(prediction.probability)),
            confidence_level=prediction.confidence_level,
            features_used=prediction.features_used,
            model_version='v1.0',
            prediction_horizon_hours=prediction.prediction_horizon_hours,
            expires_at=prediction.expires_at
        )
        
        return {
            "prediction_id": ml_prediction.id,
            "symbol": currency.symbol,
            "prediction_type": prediction.prediction_type,
            "probability": prediction.probability,
            "confidence_level": prediction.confidence_level,
            "explanation": prediction.explanation,
            "features_used": prediction.features_used,
            "created_at": ml_prediction.created_at.isoformat(),
            "expires_at": ml_prediction.expires_at.isoformat()
        }
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except Exception as e:
        logger.error(f"Error generating prediction for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate prediction")


@crypto_router.get("/sbloc/loans")
async def get_sbloc_loans(current_user=Depends(get_current_user)):
    """Get user's SBLOC loans backed by crypto"""
    try:
        loans = CryptoSBLOCLoan.objects.filter(user=current_user).order_by('-created_at')
        
        result = []
        for loan in loans:
            result.append({
                "loan_id": loan.id,
                "symbol": loan.cryptocurrency.symbol,
                "collateral_quantity": float(loan.collateral_quantity),
                "collateral_value_at_loan": float(loan.collateral_value_at_loan),
                "loan_amount": float(loan.loan_amount),
                "interest_rate": float(loan.interest_rate),
                "maintenance_margin": float(loan.maintenance_margin),
                "liquidation_threshold": float(loan.liquidation_threshold),
                "status": loan.status,
                "created_at": loan.created_at.isoformat(),
                "updated_at": loan.updated_at.isoformat()
            })
        
        return {"loans": result}
        
    except Exception as e:
        logger.error(f"Error fetching SBLOC loans for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch SBLOC loans")


@crypto_router.post("/sbloc/create-loan")
async def create_sbloc_loan(
    symbol: str,
    collateral_quantity: float,
    loan_amount: float,
    current_user=Depends(get_current_user)
):
    """Create a new SBLOC loan backed by crypto collateral"""
    try:
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        
        # Get current price
        latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
        if not latest_price:
            raise HTTPException(status_code=404, detail="Price data not available")
        
        current_price = float(latest_price.price_usd)
        collateral_value = collateral_quantity * current_price
        
        # Check if user has sufficient holdings
        portfolio, _ = CryptoPortfolio.objects.get_or_create(user=current_user)
        holding = CryptoHolding.objects.filter(
            portfolio=portfolio,
            cryptocurrency=currency,
            quantity__gte=collateral_quantity
        ).first()
        
        if not holding:
            raise HTTPException(status_code=400, detail="Insufficient crypto holdings")
        
        # Calculate loan-to-value ratio
        ltv = loan_amount / collateral_value
        if ltv > 0.5:  # Max 50% LTV
            raise HTTPException(status_code=400, detail="Loan amount exceeds maximum LTV of 50%")
        
        # Create loan
        loan = CryptoSBLOCLoan.objects.create(
            user=current_user,
            cryptocurrency=currency,
            collateral_quantity=Decimal(str(collateral_quantity)),
            collateral_value_at_loan=Decimal(str(collateral_value)),
            loan_amount=Decimal(str(loan_amount)),
            interest_rate=Decimal('0.05'),  # 5% default rate
            status='ACTIVE'
        )
        
        # Update holding to mark as collateralized
        holding.is_collateralized = True
        holding.collateral_value = Decimal(str(collateral_value))
        holding.loan_amount = Decimal(str(loan_amount))
        holding.save()
        
        return {
            "loan_id": loan.id,
            "symbol": currency.symbol,
            "collateral_quantity": float(collateral_quantity),
            "collateral_value": collateral_value,
            "loan_amount": loan_amount,
            "ltv": ltv,
            "interest_rate": 0.05,
            "status": "ACTIVE",
            "created_at": loan.created_at.isoformat()
        }
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except Exception as e:
        logger.error(f"Error creating SBLOC loan: {e}")
        raise HTTPException(status_code=500, detail="Failed to create SBLOC loan")


@crypto_router.get("/analytics/portfolio")
async def get_portfolio_analytics(current_user=Depends(get_current_user)):
    """Get detailed portfolio analytics"""
    try:
        portfolio, _ = CryptoPortfolio.objects.get_or_create(user=current_user)
        
        # Calculate additional metrics
        holdings = portfolio.holdings.all()
        total_value = float(portfolio.total_value_usd)
        
        # Sector allocation (simplified - using volatility tiers as "sectors")
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
        
        # Risk metrics
        risk_metrics = {
            "portfolio_volatility": float(portfolio.portfolio_volatility),
            "sharpe_ratio": float(portfolio.sharpe_ratio),
            "max_drawdown": float(portfolio.max_drawdown),
            "diversification_score": float(portfolio.diversification_score),
            "top_holding_percentage": float(portfolio.top_holding_percentage)
        }
        
        # Performance metrics
        performance_metrics = {
            "total_value_usd": total_value,
            "total_cost_basis": float(portfolio.total_cost_basis),
            "total_pnl": float(portfolio.total_pnl),
            "total_pnl_percentage": float(portfolio.total_pnl_percentage),
            "best_performer": None,
            "worst_performer": None
        }
        
        # Find best and worst performers
        if holdings:
            performers = []
            for holding in holdings:
                pnl_pct = float(holding.unrealized_pnl_percentage)
                performers.append((holding.cryptocurrency.symbol, pnl_pct))
            
            performers.sort(key=lambda x: x[1], reverse=True)
            if performers:
                performance_metrics["best_performer"] = {
                    "symbol": performers[0][0],
                    "pnl_percentage": performers[0][1]
                }
                performance_metrics["worst_performer"] = {
                    "symbol": performers[-1][0],
                    "pnl_percentage": performers[-1][1]
                }
        
        return {
            "portfolio_summary": {
                "total_value_usd": total_value,
                "total_holdings": len(holdings),
                "last_updated": portfolio.updated_at.isoformat()
            },
            "sector_allocation": sector_allocation,
            "risk_metrics": risk_metrics,
            "performance_metrics": performance_metrics
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio analytics for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio analytics")


@crypto_router.get("/education/progress")
async def get_education_progress(current_user=Depends(get_current_user)):
    """Get user's crypto education progress"""
    try:
        from .crypto_models import CryptoEducationProgress
        
        progress = CryptoEducationProgress.objects.filter(user=current_user).order_by('module_type', 'module_name')
        
        result = []
        for p in progress:
            result.append({
                "module_name": p.module_name,
                "module_type": p.module_type,
                "progress_percentage": float(p.progress_percentage),
                "is_completed": p.is_completed,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                "quiz_attempts": p.quiz_attempts,
                "best_quiz_score": float(p.best_quiz_score)
            })
        
        return {"education_progress": result}
        
    except Exception as e:
        logger.error(f"Error fetching education progress for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch education progress")
