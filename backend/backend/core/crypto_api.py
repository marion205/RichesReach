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
from pydantic import BaseModel, Field

from .crypto_models import (
    Cryptocurrency, CryptoPrice, CryptoPortfolio, CryptoHolding, 
    CryptoTrade, CryptoMLPrediction, CryptoSBLOCLoan,
    LendingReserve, SupplyPosition, BorrowPosition,  # <- new
)
from .crypto_ml_engine import CryptoMLPredictionService
from .auth_utils import get_current_user
from .aave_risk import (
    total_collateral_usd, total_debt_usd, available_borrow_usd, health_factor
)

logger = logging.getLogger(__name__)

# Create router
crypto_router = APIRouter(prefix="/api/crypto", tags=["crypto"])

# Initialize ML service
ml_service = CryptoMLPredictionService()

# Tiny helpers
def _to_dec(n) -> Decimal:
    return n if isinstance(n, Decimal) else Decimal(str(n or "0"))

def _latest_price_map(symbols: List[str]) -> Dict[str, Decimal]:
    out: Dict[str, Decimal] = {}
    qs = Cryptocurrency.objects.filter(symbol__in=symbols, is_active=True)
    for c in qs:
        p = CryptoPrice.objects.filter(cryptocurrency=c).first()
        if p:
            out[c.symbol] = _to_dec(p.price_usd)
    return out

def _weighted(reserves, quantities, prices, field_name: str) -> Decimal:
    """value-weighted parameter (e.g., LTV or LiqThreshold) over supplies set to collateral."""
    total_v = Decimal("0")
    accum = Decimal("0")
    for r, q in zip(reserves, quantities):
        if not r.can_be_collateral:
            continue
        price = _to_dec(prices.get(r.cryptocurrency.symbol, 0))
        v = _to_dec(q) * price
        total_v += v
        accum += v * _to_dec(getattr(r, field_name))
    return (accum / total_v) if total_v > 0 else Decimal("0")

def _fmt(d: Decimal) -> float:
    return float(d.quantize(Decimal("0.00000001")))

# Schemas for POST bodies
class SupplyBody(BaseModel):
    symbol: str = Field(..., description="Asset to supply (e.g., ETH)")
    quantity: float = Field(..., gt=0)
    use_as_collateral: bool = True

class WithdrawBody(BaseModel):
    symbol: str
    quantity: float = Field(..., gt=0)

class BorrowBody(BaseModel):
    symbol: str = Field(..., description="Asset to borrow (e.g., USDC)")
    amount: float = Field(..., gt=0, description="Borrow amount in asset units")
    rate_mode: str = Field("VARIABLE", regex="^(VARIABLE|STABLE)$")

class RepayBody(BaseModel):
    symbol: str
    amount: float = Field(..., gt=0)

class ToggleCollateralBody(BaseModel):
    symbol: str
    use_as_collateral: bool


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


# ------------------------------ AAVE / DeFi ------------------------------

@crypto_router.get("/defi/reserves")
async def list_lending_reserves():
    """List active reserves with risk params and indicative APYs (AAVE-style)."""
    try:
        items = []
        for r in LendingReserve.objects.filter(is_active=True).select_related("cryptocurrency"):
            items.append({
                "symbol": r.cryptocurrency.symbol,
                "name": r.cryptocurrency.name,
                "ltv": _fmt(r.ltv),
                "liquidation_threshold": _fmt(r.liquidation_threshold),
                "liquidation_bonus": _fmt(r.liquidation_bonus),
                "reserve_factor": _fmt(r.reserve_factor),
                "can_borrow": r.can_borrow,
                "can_be_collateral": r.can_be_collateral,
                "supply_apy": float(r.supply_apy) if r.supply_apy is not None else None,
                "variable_borrow_apy": float(r.variable_borrow_apy) if r.variable_borrow_apy is not None else None,
                "stable_borrow_apy": float(r.stable_borrow_apy) if r.stable_borrow_apy is not None else None,
                "updated_at": r.updated_at.isoformat(),
            })
        return {"reserves": items}
    except Exception as e:
        logger.error(f"reserves list error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list reserves")


@crypto_router.get("/defi/account")
async def get_lending_account(current_user=Depends(get_current_user)):
    """
    Account overview: supplies, borrows, health factor, available borrow in USD.
    """
    try:
        supplies_qs = (
            SupplyPosition.objects
            .filter(user=current_user)
            .select_related("reserve__cryptocurrency")
        )
        borrows_qs = (
            BorrowPosition.objects
            .filter(user=current_user, is_active=True)
            .select_related("reserve__cryptocurrency")
        )

        supply_reserves = [s.reserve for s in supplies_qs]
        supply_qtys = [s.quantity for s in supplies_qs]
        borrow_reserves = [b.reserve for b in borrows_qs]
        borrow_amts = [b.amount for b in borrows_qs]

        symbols = list({*[r.cryptocurrency.symbol for r in supply_reserves],
                        *[r.cryptocurrency.symbol for r in borrow_reserves]})
        prices = _latest_price_map(symbols)

        # Collateral & weights
        coll_usd, liq_th = total_collateral_usd(
            [(r, q, s.use_as_collateral) for r, q, s in zip(supply_reserves, supply_qtys, supplies_qs)],
            prices
        )
        # Weighted LTV across collateral supplies
        w_ltv = _weighted(supply_reserves, supply_qtys, prices, "ltv")

        # Debt
        debt_usd = total_debt_usd([(r, a) for r, a in zip(borrow_reserves, borrow_amts)], prices)

        avail_usd = available_borrow_usd(coll_usd, w_ltv, debt_usd)
        hf = health_factor(coll_usd, liq_th, debt_usd)

        return {
            "collateral_usd": _fmt(coll_usd),
            "debt_usd": _fmt(debt_usd),
            "ltv_weighted": _fmt(w_ltv),
            "liq_threshold_weighted": _fmt(liq_th),
            "available_borrow_usd": _fmt(avail_usd),
            "health_factor": float(hf),  # can be very large
            "supplies": [{
                "symbol": s.reserve.cryptocurrency.symbol,
                "quantity": _fmt(s.quantity),
                "use_as_collateral": s.use_as_collateral,
            } for s in supplies_qs],
            "borrows": [{
                "symbol": b.reserve.cryptocurrency.symbol,
                "amount": _fmt(b.amount),
                "rate_mode": b.rate_mode,
                "apy_at_open": float(b.apy_at_open) if b.apy_at_open is not None else None,
                "opened_at": b.opened_at.isoformat(),
            } for b in borrows_qs],
            "prices_usd": {k: _fmt(v) for k, v in prices.items()},
        }
    except Exception as e:
        logger.error(f"account error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load lending account")


@crypto_router.post("/defi/supply")
async def supply_asset(body: SupplyBody, current_user=Depends(get_current_user)):
    """Supply an asset; optionally mark as collateral."""
    try:
        symbol = body.symbol.upper()
        asset = Cryptocurrency.objects.get(symbol=symbol, is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True)

        qty = _to_dec(body.quantity)
        if qty <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be > 0")

        sp, _ = SupplyPosition.objects.get_or_create(user=current_user, reserve=reserve)
        sp.quantity = _to_dec(sp.quantity) + qty
        sp.use_as_collateral = bool(body.use_as_collateral)
        sp.save()

        return {"status": "OK", "symbol": symbol, "new_quantity": _fmt(sp.quantity), "use_as_collateral": sp.use_as_collateral}
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Asset not found")
    except LendingReserve.DoesNotExist:
        raise HTTPException(status_code=404, detail="Reserve not found")
    except Exception as e:
        logger.error(f"supply error: {e}")
        raise HTTPException(status_code=500, detail="Failed to supply")


@crypto_router.post("/defi/withdraw")
async def withdraw_asset(body: WithdrawBody, current_user=Depends(get_current_user)):
    """Withdraw supplied asset; enforces health factor ≥ 1 after withdrawal."""
    try:
        symbol = body.symbol.upper()
        asset = Cryptocurrency.objects.get(symbol=symbol, is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True)
        sp = SupplyPosition.objects.get(user=current_user, reserve=reserve)

        qty = _to_dec(body.quantity)
        if qty <= 0 or qty > _to_dec(sp.quantity):
            raise HTTPException(status_code=400, detail="Invalid quantity")

        # Simulate post-withdraw HF
        sp_after = _to_dec(sp.quantity) - qty

        # Build state to check HF
        supplies_qs = SupplyPosition.objects.filter(user=current_user).select_related("reserve__cryptocurrency")
        borrows_qs = BorrowPosition.objects.filter(user=current_user, is_active=True).select_related("reserve__cryptocurrency")

        prices = _latest_price_map(list({*[s.reserve.cryptocurrency.symbol for s in supplies_qs],
                                         *[b.reserve.cryptocurrency.symbol for b in borrows_qs]}))

        # Compute collateral after withdrawal
        def _supply_triplets():
            for s in supplies_qs:
                q = sp_after if (s.id == sp.id) else _to_dec(s.quantity)
                yield (s.reserve, q, s.use_as_collateral)

        coll_usd, liq_th = total_collateral_usd(list(_supply_triplets()), prices)
        debt_usd = total_debt_usd([(b.reserve, b.amount) for b in borrows_qs], prices)
        hf_after = health_factor(coll_usd, liq_th, debt_usd)

        if hf_after <= Decimal("1"):
            raise HTTPException(status_code=400, detail="Withdrawal would drop Health Factor ≤ 1")

        sp.quantity = sp_after
        sp.save(update_fields=["quantity"])

        return {"status": "OK", "symbol": symbol, "remaining_quantity": _fmt(sp.quantity), "health_factor_after": float(hf_after)}
    except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist, SupplyPosition.DoesNotExist):
        raise HTTPException(status_code=404, detail="Position not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"withdraw error: {e}")
        raise HTTPException(status_code=500, detail="Failed to withdraw")


@crypto_router.post("/defi/borrow")
async def borrow_asset(body: BorrowBody, current_user=Depends(get_current_user)):
    """Borrow an asset; checks available USD headroom and HF > 1 after borrow."""
    try:
        symbol = body.symbol.upper()
        asset = Cryptocurrency.objects.get(symbol=symbol, is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True, can_borrow=True)

        amt = _to_dec(body.amount)
        if amt <= 0:
            raise HTTPException(status_code=400, detail="Amount must be > 0")

        # Build current state
        supplies_qs = SupplyPosition.objects.filter(user=current_user).select_related("reserve__cryptocurrency")
        borrows_qs = BorrowPosition.objects.filter(user=current_user, is_active=True).select_related("reserve__cryptocurrency")

        price_symbols = list({symbol, *[s.reserve.cryptocurrency.symbol for s in supplies_qs], *[b.reserve.cryptocurrency.symbol for b in borrows_qs]})
        prices = _latest_price_map(price_symbols)

        coll_usd, liq_th = total_collateral_usd([(s.reserve, s.quantity, s.use_as_collateral) for s in supplies_qs], prices)
        w_ltv = _weighted([s.reserve for s in supplies_qs], [s.quantity for s in supplies_qs], prices, "ltv")
        debt_usd = total_debt_usd([(b.reserve, b.amount) for b in borrows_qs], prices)

        avail_usd = available_borrow_usd(coll_usd, w_ltv, debt_usd)

        # Requested borrow in USD
        borrow_usd = amt * _to_dec(prices.get(symbol, 0))
        if borrow_usd <= 0:
            raise HTTPException(status_code=400, detail="Missing price for borrow asset")
        if borrow_usd > avail_usd:
            raise HTTPException(status_code=400, detail="Borrow exceeds available headroom")

        # Simulate HF after borrow
        hf_after = health_factor(coll_usd, liq_th, debt_usd + borrow_usd)
        if hf_after <= Decimal("1"):
            raise HTTPException(status_code=400, detail="Borrow would drop Health Factor ≤ 1")

        bp, created = BorrowPosition.objects.get_or_create(
            user=current_user, reserve=reserve, is_active=True,
            defaults=dict(amount=amt, rate_mode=body.rate_mode)
        )
        if not created:
            bp.amount = _to_dec(bp.amount) + amt
            bp.rate_mode = body.rate_mode
        bp.save()

        return {"status": "OK", "symbol": symbol, "new_amount": _fmt(bp.amount), "health_factor_after": float(hf_after)}
    except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist):
        raise HTTPException(status_code=404, detail="Reserve not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"borrow error: {e}")
        raise HTTPException(status_code=500, detail="Failed to borrow")


@crypto_router.post("/defi/repay")
async def repay_asset(body: RepayBody, current_user=Depends(get_current_user)):
    """Repay a borrowed asset (partial or full)."""
    try:
        symbol = body.symbol.upper()
        asset = Cryptocurrency.objects.get(symbol=symbol, is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True)
        bp = BorrowPosition.objects.get(user=current_user, reserve=reserve, is_active=True)

        amt = _to_dec(body.amount)
        if amt <= 0:
            raise HTTPException(status_code=400, detail="Amount must be > 0")

        new_amt = _to_dec(bp.amount) - amt
        if new_amt <= 0:
            bp.amount = Decimal("0")
            bp.is_active = False
        else:
            bp.amount = new_amt
        bp.save(update_fields=["amount", "is_active"])

        return {"status": "OK", "symbol": symbol, "remaining_amount": _fmt(bp.amount), "is_active": bp.is_active}
    except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist, BorrowPosition.DoesNotExist):
        raise HTTPException(status_code=404, detail="Borrow position not found")
    except Exception as e:
        logger.error(f"repay error: {e}")
        raise HTTPException(status_code=500, detail="Failed to repay")


@crypto_router.post("/defi/collateral/toggle")
async def toggle_collateral(body: ToggleCollateralBody, current_user=Depends(get_current_user)):
    """Toggle 'use_as_collateral' on a supplied asset; enforce HF ≥ 1."""
    try:
        symbol = body.symbol.upper()
        asset = Cryptocurrency.objects.get(symbol=symbol, is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True)
        sp = SupplyPosition.objects.get(user=current_user, reserve=reserve)

        supplies_qs = SupplyPosition.objects.filter(user=current_user).select_related("reserve__cryptocurrency")
        borrows_qs = BorrowPosition.objects.filter(user=current_user, is_active=True).select_related("reserve__cryptocurrency")
        prices = _latest_price_map(list({*[s.reserve.cryptocurrency.symbol for s in supplies_qs],
                                         *[b.reserve.cryptocurrency.symbol for b in borrows_qs]}))

        # Simulate new collateral set
        def _triplets():
            for s in supplies_qs:
                if s.id == sp.id:
                    yield (s.reserve, s.quantity, body.use_as_collateral)
                else:
                    yield (s.reserve, s.quantity, s.use_as_collateral)

        coll_usd, liq_th = total_collateral_usd(list(_triplets()), prices)
        debt_usd = total_debt_usd([(b.reserve, b.amount) for b in borrows_qs], prices)
        hf_after = health_factor(coll_usd, liq_th, debt_usd)

        if hf_after <= Decimal("1"):
            raise HTTPException(status_code=400, detail="Toggle would drop Health Factor ≤ 1")

        sp.use_as_collateral = body.use_as_collateral
        sp.save(update_fields=["use_as_collateral"])

        return {"status": "OK", "symbol": symbol, "use_as_collateral": sp.use_as_collateral, "health_factor_after": float(hf_after)}
    except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist, SupplyPosition.DoesNotExist):
        raise HTTPException(status_code=404, detail="Supply position not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"toggle collateral error: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle collateral")


# Hard-deprecate SBLOC routes (keep signatures, stop usage)
@crypto_router.get("/sbloc/loans")
async def get_sbloc_loans(current_user=Depends(get_current_user)):
    raise HTTPException(status_code=410, detail="SBLOC endpoints are deprecated. Use /api/crypto/defi/* instead.")

@crypto_router.post("/sbloc/create-loan")
async def create_sbloc_loan(
    symbol: str,
    collateral_quantity: float,
    loan_amount: float,
    current_user=Depends(get_current_user)
):
    raise HTTPException(status_code=410, detail="SBLOC endpoints are deprecated. Use /api/crypto/defi/* instead.")


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


# --- AAVE-style Lending API Endpoints -------------------------------------

@crypto_router.get("/lending/reserves")
async def get_lending_reserves():
    """Get all active lending reserves"""
    try:
        from .crypto_models import LendingReserve
        
        reserves = LendingReserve.objects.filter(is_active=True)
        result = []
        
        for reserve in reserves:
            result.append({
                "symbol": reserve.cryptocurrency.symbol,
                "name": reserve.cryptocurrency.name,
                "ltv": float(reserve.ltv),
                "liquidation_threshold": float(reserve.liquidation_threshold),
                "liquidation_bonus": float(reserve.liquidation_bonus),
                "reserve_factor": float(reserve.reserve_factor),
                "can_borrow": reserve.can_borrow,
                "can_be_collateral": reserve.can_be_collateral,
                "supply_apy": float(reserve.supply_apy) if reserve.supply_apy else 0,
                "variable_borrow_apy": float(reserve.variable_borrow_apy) if reserve.variable_borrow_apy else 0,
                "stable_borrow_apy": float(reserve.stable_borrow_apy) if reserve.stable_borrow_apy else 0,
                "updated_at": reserve.updated_at.isoformat()
            })
        
        return {"reserves": result}
        
    except Exception as e:
        logger.error(f"Error fetching lending reserves: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch lending reserves")


@crypto_router.get("/lending/account")
async def get_lending_account(current_user=Depends(get_current_user)):
    """Get user's complete lending account data"""
    try:
        from .crypto_models import SupplyPosition, BorrowPosition, CryptoPrice
        from .aave_risk import calculate_lending_account_data
        
        # Get user's positions
        supplies = SupplyPosition.objects.filter(user=current_user)
        borrows = BorrowPosition.objects.filter(user=current_user, is_active=True)
        
        # Get current prices for all assets
        symbols = set()
        for sp in supplies:
            symbols.add(sp.reserve.cryptocurrency.symbol)
        for bp in borrows:
            symbols.add(bp.reserve.cryptocurrency.symbol)
        
        prices = {}
        for symbol in symbols:
            try:
                from .crypto_models import Cryptocurrency
                currency = Cryptocurrency.objects.get(symbol=symbol)
                latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
                if latest_price:
                    prices[symbol] = latest_price.price_usd
            except:
                continue
        
        # Calculate account data
        supplies_data = [(sp.reserve, sp.quantity, sp.use_as_collateral) for sp in supplies]
        borrows_data = [(bp.reserve, bp.amount) for bp in borrows]
        
        account_data = calculate_lending_account_data(supplies_data, borrows_data, prices)
        
        return {
            "total_collateral_usd": float(account_data.total_collateral_usd),
            "total_debt_usd": float(account_data.total_debt_usd),
            "health_factor": float(account_data.health_factor),
            "health_factor_tier": account_data.health_factor_tier,
            "available_borrow_usd": float(account_data.available_borrow_usd),
            "weighted_ltv": float(account_data.weighted_ltv),
            "weighted_liquidation_threshold": float(account_data.weighted_liquidation_threshold),
            "supplies": account_data.supplies,
            "borrows": account_data.borrows
        }
        
    except Exception as e:
        logger.error(f"Error fetching lending account for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch lending account")


@crypto_router.post("/lending/supply")
async def supply_asset(
    symbol: str,
    quantity: float,
    use_as_collateral: bool = True,
    current_user=Depends(get_current_user)
):
    """Supply an asset to the lending pool"""
    try:
        from .crypto_models import LendingReserve, SupplyPosition, CryptoPortfolio, CryptoHolding
        from .aave_risk import to_decimal
        
        # Get cryptocurrency and reserve
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=currency, is_active=True)
        
        # Check if user has sufficient holdings
        portfolio, _ = CryptoPortfolio.objects.get_or_create(user=current_user)
        holding = CryptoHolding.objects.filter(
            portfolio=portfolio,
            cryptocurrency=currency,
            quantity__gte=quantity
        ).first()
        
        if not holding:
            raise HTTPException(status_code=400, detail=f"Insufficient {symbol} holdings")
        
        # Create or update supply position
        position, created = SupplyPosition.objects.get_or_create(
            user=current_user,
            reserve=reserve,
            defaults={
                'quantity': to_decimal(quantity),
                'use_as_collateral': use_as_collateral,
            }
        )
        
        if not created:
            position.quantity += to_decimal(quantity)
            position.use_as_collateral = use_as_collateral
            position.save()
        
        # Update holding
        holding.quantity -= to_decimal(quantity)
        holding.save()
        
        return {
            "success": True,
            "message": f"Supplied {quantity} {symbol}",
            "position_id": position.id
        }
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except LendingReserve.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lending reserve not found")
    except Exception as e:
        logger.error(f"Error supplying asset: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@crypto_router.post("/lending/borrow")
async def borrow_asset(
    symbol: str,
    amount: float,
    rate_mode: str = "VARIABLE",
    current_user=Depends(get_current_user)
):
    """Borrow an asset from the lending pool"""
    try:
        from .crypto_models import LendingReserve, BorrowPosition, CryptoPrice
        from .aave_risk import to_decimal, calculate_lending_account_data
        
        # Get cryptocurrency and reserve
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=currency, is_active=True)
        
        if not reserve.can_borrow:
            raise HTTPException(status_code=400, detail="Asset cannot be borrowed")
        
        # Get current price
        latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
        if not latest_price:
            raise HTTPException(status_code=404, detail="Price data not available")
        
        # Calculate health factor and available borrow
        supplies = SupplyPosition.objects.filter(user=current_user, use_as_collateral=True)
        borrows = BorrowPosition.objects.filter(user=current_user, is_active=True)
        
        prices = {currency.symbol: latest_price.price_usd}
        account_data = calculate_lending_account_data(
            [(sp.reserve, sp.quantity, sp.use_as_collateral) for sp in supplies],
            [(bp.reserve, bp.amount) for bp in borrows],
            prices
        )
        
        borrow_usd = amount * float(latest_price.price_usd)
        if borrow_usd > float(account_data.available_borrow_usd):
            raise HTTPException(status_code=400, detail="Insufficient borrowing capacity")
        
        # Create borrow position
        position = BorrowPosition.objects.create(
            user=current_user,
            reserve=reserve,
            amount=to_decimal(amount),
            rate_mode=rate_mode,
            apy_at_open=reserve.variable_borrow_apy if rate_mode == "VARIABLE" else reserve.stable_borrow_apy,
            usd_value_cached=to_decimal(borrow_usd),
            is_active=True
        )
        
        return {
            "success": True,
            "message": f"Borrowed {amount} {symbol}",
            "position_id": position.id
        }
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except LendingReserve.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lending reserve not found")
    except Exception as e:
        logger.error(f"Error borrowing asset: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@crypto_router.post("/lending/repay")
async def repay_asset(
    symbol: str,
    amount: float,
    current_user=Depends(get_current_user)
):
    """Repay a borrowed asset"""
    try:
        from .crypto_models import LendingReserve, BorrowPosition, CryptoPortfolio, CryptoHolding
        from .aave_risk import to_decimal
        
        # Get cryptocurrency and reserve
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=currency, is_active=True)
        
        # Get active borrow position
        position = BorrowPosition.objects.filter(
            user=current_user,
            reserve=reserve,
            is_active=True
        ).first()
        
        if not position:
            raise HTTPException(status_code=404, detail="No active borrow position found")
        
        # Check if user has sufficient balance to repay
        portfolio, _ = CryptoPortfolio.objects.get_or_create(user=current_user)
        holding = CryptoHolding.objects.filter(
            portfolio=portfolio,
            cryptocurrency=currency
        ).first()
        
        if not holding or holding.quantity < amount:
            raise HTTPException(status_code=400, detail=f"Insufficient {symbol} balance")
        
        # Update position
        position.amount -= to_decimal(amount)
        if position.amount <= 0:
            position.is_active = False
        position.save()
        
        # Update holding
        holding.quantity -= to_decimal(amount)
        holding.save()
        
        return {
            "success": True,
            "message": f"Repaid {amount} {symbol}"
        }
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except LendingReserve.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lending reserve not found")
    except Exception as e:
        logger.error(f"Error repaying asset: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@crypto_router.post("/lending/withdraw")
async def withdraw_asset(
    symbol: str,
    quantity: float,
    current_user=Depends(get_current_user)
):
    """Withdraw a supplied asset"""
    try:
        from .crypto_models import LendingReserve, SupplyPosition, CryptoPortfolio, CryptoHolding, CryptoPrice
        from .aave_risk import to_decimal, calculate_lending_account_data
        
        # Get cryptocurrency and reserve
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=currency, is_active=True)
        
        # Get supply position
        position = SupplyPosition.objects.filter(
            user=current_user,
            reserve=reserve
        ).first()
        
        if not position or position.quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient supply balance")
        
        # Check health factor after withdrawal
        supplies = SupplyPosition.objects.filter(user=current_user, use_as_collateral=True)
        borrows = BorrowPosition.objects.filter(user=current_user, is_active=True)
        
        # Get current prices
        latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
        if not latest_price:
            raise HTTPException(status_code=404, detail="Price data not available")
        
        prices = {currency.symbol: latest_price.price_usd}
        
        # Simulate withdrawal
        temp_supplies = []
        for sp in supplies:
            if sp.reserve == reserve:
                temp_qty = max(0, float(sp.quantity) - quantity)
                temp_supplies.append((sp.reserve, temp_qty, sp.use_as_collateral))
            else:
                temp_supplies.append((sp.reserve, float(sp.quantity), sp.use_as_collateral))
        
        temp_borrows = [(bp.reserve, float(bp.amount)) for bp in borrows]
        
        account_data = calculate_lending_account_data(temp_supplies, temp_borrows, prices)
        
        if account_data.health_factor < 1.0:
            raise HTTPException(status_code=400, detail="Withdrawal would result in unhealthy position")
        
        # Update position
        position.quantity -= to_decimal(quantity)
        position.save()
        
        # Update holding
        portfolio, _ = CryptoPortfolio.objects.get_or_create(user=current_user)
        holding, _ = CryptoHolding.objects.get_or_create(
            portfolio=portfolio,
            cryptocurrency=currency,
            defaults={'quantity': 0}
        )
        holding.quantity += to_decimal(quantity)
        holding.save()
        
        return {
            "success": True,
            "message": f"Withdrew {quantity} {symbol}"
        }
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except LendingReserve.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lending reserve not found")
    except Exception as e:
        logger.error(f"Error withdrawing asset: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@crypto_router.post("/lending/toggle-collateral")
async def toggle_collateral(
    symbol: str,
    use_as_collateral: bool,
    current_user=Depends(get_current_user)
):
    """Toggle collateral usage for a supplied asset"""
    try:
        from .crypto_models import LendingReserve, SupplyPosition
        
        # Get cryptocurrency and reserve
        currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
        reserve = LendingReserve.objects.get(cryptocurrency=currency, is_active=True)
        
        if not reserve.can_be_collateral and use_as_collateral:
            raise HTTPException(status_code=400, detail="Asset cannot be used as collateral")
        
        # Get supply position
        position = SupplyPosition.objects.filter(
            user=current_user,
            reserve=reserve
        ).first()
        
        if not position:
            raise HTTPException(status_code=404, detail="No supply position found")
        
        # Update position
        position.use_as_collateral = use_as_collateral
        position.save()
        
        return {
            "success": True,
            "message": f"Collateral usage {'enabled' if use_as_collateral else 'disabled'} for {symbol}"
        }
        
    except Cryptocurrency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    except LendingReserve.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lending reserve not found")
    except Exception as e:
        logger.error(f"Error toggling collateral: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@crypto_router.post("/defi/stress-test")
async def stress_test_hf(
    shocks: List[float] = [-0.2, -0.3, -0.5],
    current_user=Depends(get_current_user)
):
    """Stress test Health Factor with price shocks"""
    try:
        from .aave_risk import stress_test_hf
        
        # Get user's current positions
        supplies = SupplyPosition.objects.filter(user=current_user).select_related("reserve__cryptocurrency")
        borrows = BorrowPosition.objects.filter(user=current_user, is_active=True).select_related("reserve__cryptocurrency")
        
        # Get current prices
        symbols = list({*[s.reserve.cryptocurrency.symbol for s in supplies], *[b.reserve.cryptocurrency.symbol for b in borrows]})
        prices = _latest_price_map(symbols)
        
        # Convert to tuples for risk engine
        supplies_tuples = [(s.reserve, s.quantity, s.use_as_collateral) for s in supplies]
        borrows_tuples = [(b.reserve, b.amount) for b in borrows]
        
        # Run stress test
        results = stress_test_hf(supplies_tuples, borrows_tuples, prices, shocks)
        
        # Convert results to JSON-serializable format
        results_data = []
        for result in results:
            results_data.append({
                'shock': result.shock,
                'collateral_usd': result.collateral_usd,
                'debt_usd': result.debt_usd,
                'ltv_weighted': result.ltv_weighted,
                'liq_threshold_weighted': result.liq_threshold_weighted,
                'available_borrow_usd': result.available_borrow_usd,
                'health_factor': result.health_factor,
                'tier': result.tier
            })
        
        return {
            "success": True,
            "results": results_data,
            "message": "Stress test completed"
        }
        
    except Exception as e:
        logger.error(f"Stress test error: {e}")
        raise HTTPException(status_code=500, detail="Failed to run stress test")


@crypto_router.post("/defi/estimate-hf-after-repay")
async def estimate_hf_after_repay(
    reserve_symbol: str,
    repay_amount_usd: float,
    current_user=Depends(get_current_user)
):
    """Estimate Health Factor after repay for a specific position"""
    try:
        from .aave_risk import health_factor, total_collateral_usd, total_debt_usd
        
        # Get the specific reserve
        try:
            currency = Cryptocurrency.objects.get(symbol=reserve_symbol.upper(), is_active=True)
            reserve = LendingReserve.objects.get(cryptocurrency=currency, is_active=True)
        except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist):
            raise HTTPException(status_code=404, detail="Reserve not found")
        
        # Get user's positions for this reserve
        supplies = SupplyPosition.objects.filter(
            user=current_user, 
            reserve=reserve
        ).select_related("reserve__cryptocurrency")
        
        borrows = BorrowPosition.objects.filter(
            user=current_user, 
            reserve=reserve, 
            is_active=True
        ).select_related("reserve__cryptocurrency")
        
        if not supplies.exists() and not borrows.exists():
            raise HTTPException(status_code=404, detail="No positions found for this reserve")
        
        # Get current prices
        symbols = [reserve_symbol.upper()]
        prices = _latest_price_map(symbols)
        
        # Calculate current metrics
        supplies_tuples = [(s.reserve, s.quantity, s.use_as_collateral) for s in supplies]
        borrows_tuples = [(b.reserve, b.amount) for b in borrows]
        
        current_coll_usd, current_liq_th = total_collateral_usd(supplies_tuples, prices)
        current_debt_usd = total_debt_usd(borrows_tuples, prices)
        current_hf = health_factor(current_coll_usd, current_liq_th, current_debt_usd)
        
        # Calculate after repay metrics
        new_debt_usd = max(0, current_debt_usd - repay_amount_usd)
        new_hf = health_factor(current_coll_usd, current_liq_th, new_debt_usd)
        
        # Calculate LTV and borrow capacity
        ltv_pct = (new_debt_usd / max(0.01, current_coll_usd)) * 100 if current_coll_usd > 0 else 0
        borrow_cap_usd = current_coll_usd * reserve.ltv
        available_borrow_usd = max(0, borrow_cap_usd - new_debt_usd)
        
        # Determine risk tier
        from .aave_risk import hf_tier
        current_tier = hf_tier(current_hf)
        new_tier = hf_tier(new_hf)
        
        return {
            "success": True,
            "current": {
                "debt_usd": float(current_debt_usd),
                "collateral_usd": float(current_coll_usd),
                "health_factor": float(current_hf),
                "ltv_pct": (current_debt_usd / max(0.01, current_coll_usd) * 100) if current_coll_usd > 0 else 0,
                "tier": current_tier
            },
            "after_repay": {
                "debt_usd": float(new_debt_usd),
                "collateral_usd": float(current_coll_usd),
                "health_factor": float(new_hf),
                "ltv_pct": ltv_pct,
                "available_borrow_usd": float(available_borrow_usd),
                "tier": new_tier
            },
            "repay_amount_usd": repay_amount_usd,
            "reserve_symbol": reserve_symbol.upper()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HF estimation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to estimate health factor")


@crypto_router.post("/defi/validate-transaction")
async def validate_transaction(
    type: str,
    data: dict,
    wallet_address: str,
    current_user=Depends(get_current_user)
):
    """Validate transaction with risk engine before blockchain execution"""
    try:
        from .aave_risk import health_factor, total_collateral_usd, total_debt_usd, hf_tier
        
        # Get current user positions
        supplies = SupplyPosition.objects.filter(user=current_user).select_related("reserve__cryptocurrency")
        borrows = BorrowPosition.objects.filter(user=current_user, is_active=True).select_related("reserve__cryptocurrency")
        
        # Get current prices
        symbols = list({*[s.reserve.cryptocurrency.symbol for s in supplies], *[b.reserve.cryptocurrency.symbol for b in borrows]})
        prices = _latest_price_map(symbols)
        
        # Calculate current metrics
        supplies_tuples = [(s.reserve, s.quantity, s.use_as_collateral) for s in supplies]
        borrows_tuples = [(b.reserve, b.amount) for b in borrows]
        
        current_coll_usd, current_liq_th = total_collateral_usd(supplies_tuples, prices)
        current_debt_usd = total_debt_usd(borrows_tuples, prices)
        current_hf = health_factor(current_coll_usd, current_liq_th, current_debt_usd)
        
        # Simulate transaction and calculate new metrics
        new_coll_usd = current_coll_usd
        new_debt_usd = current_debt_usd
        
        if type == "supply":
            # Add to collateral
            asset_symbol = data.get("assetSymbol", "").upper()
            amount = float(data.get("amount", 0))
            price = prices.get(asset_symbol, 0)
            new_coll_usd += amount * price
            
        elif type == "borrow":
            # Add to debt
            asset_symbol = data.get("assetSymbol", "").upper()
            amount = float(data.get("amount", 0))
            price = prices.get(asset_symbol, 1)  # Default to 1 for stablecoins
            new_debt_usd += amount * price
            
        elif type == "repay":
            # Reduce debt
            asset_symbol = data.get("assetSymbol", "").upper()
            amount = float(data.get("amount", 0))
            price = prices.get(asset_symbol, 1)
            new_debt_usd = max(0, new_debt_usd - amount * price)
        
        # Calculate new health factor
        new_hf = health_factor(new_coll_usd, current_liq_th, new_debt_usd)
        new_tier = hf_tier(new_hf)
        
        # Validation rules
        if new_hf < 1.0:
            return {
                "isValid": False,
                "error": f"Transaction would result in Health Factor {new_hf:.2f} < 1.0 (liquidation risk)"
            }
        
        if new_hf < 1.2:
            return {
                "isValid": False,
                "error": f"Transaction would result in Health Factor {new_hf:.2f} < 1.2 (high risk)"
            }
        
        # Check if user has sufficient balance (mock check)
        if type == "supply" and amount > 10:  # Mock balance check
            return {
                "isValid": False,
                "error": "Insufficient balance for supply transaction"
            }
        
        return {
            "isValid": True,
            "riskData": {
                "current_hf": float(current_hf),
                "new_hf": float(new_hf),
                "current_tier": hf_tier(current_hf),
                "new_tier": new_tier,
                "collateral_usd": float(new_coll_usd),
                "debt_usd": float(new_debt_usd)
            }
        }
        
    except Exception as e:
        logger.error(f"Transaction validation error: {e}")
        return {
            "isValid": False,
            "error": "Failed to validate transaction"
        }


@crypto_router.post("/defi/update-transaction")
async def update_transaction(
    type: str,
    tx_hash: str,
    data: dict,
    wallet_address: str,
    current_user=Depends(get_current_user)
):
    """Update backend with blockchain transaction result"""
    try:
        # Log the transaction for audit purposes
        logger.info(f"Transaction update: {type} - {tx_hash} - {wallet_address}")
        
        # In a real implementation, you would:
        # 1. Verify the transaction on blockchain
        # 2. Update user positions in database
        # 3. Update risk metrics
        # 4. Send notifications if needed
        
        return {
            "success": True,
            "message": "Transaction recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Transaction update error: {e}")
        return {
            "success": False,
            "message": "Failed to update transaction"
        }
