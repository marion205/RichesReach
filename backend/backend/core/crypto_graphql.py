"""
GraphQL types and resolvers for crypto functionality (AAVE-style lending)
"""

import logging
from decimal import Decimal

import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model

from .crypto_models import (
    Cryptocurrency, CryptoPrice, CryptoPortfolio, CryptoHolding,
    CryptoTrade, CryptoMLPrediction, CryptoSBLOCLoan, CryptoEducationProgress,
    # New AAVE-style models
    LendingReserve, SupplyPosition, BorrowPosition,
)
from .crypto_ml_engine import CryptoMLPredictionService
from .auth_utils import MLMutationAuth

# Risk helpers (same ones used by the REST layer)
from .aave_risk import (
    total_collateral_usd, total_debt_usd, available_borrow_usd, health_factor
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ------------ small helpers ------------
def _to_dec(n) -> Decimal:
    return n if isinstance(n, Decimal) else Decimal(str(n or "0"))

def _fmt8(d: Decimal) -> float:
    return float(_to_dec(d).quantize(Decimal("0.00000001")))

def _latest_price_map(symbols):
    out = {}
    qs = Cryptocurrency.objects.filter(symbol__in=[s.upper() for s in symbols], is_active=True)
    for c in qs:
        p = CryptoPrice.objects.filter(cryptocurrency=c).first()
        if p:
            out[c.symbol] = _to_dec(p.price_usd)
    return out

def _weighted(reserves, quantities, prices, field_name: str) -> Decimal:
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


# ------------ existing types (unchanged) ------------
class CryptocurrencyType(DjangoObjectType):
    class Meta:
        model = Cryptocurrency
        fields = "__all__"

    def resolve_volatilityTier(self, info): return self.volatility_tier
    def resolve_coingeckoId(self, info): return self.coingecko_id
    def resolve_isStakingAvailable(self, info): return self.is_staking_available
    def resolve_minTradeAmount(self, info): return float(self.min_trade_amount)
    def resolve_isSecCompliant(self, info): return self.is_sec_compliant
    def resolve_regulatoryStatus(self, info): return self.regulatory_status


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

    def resolve_expiresAt(self, info): return self.expires_at
    def resolve_createdAt(self, info): return self.created_at
    def resolve_predictionType(self, info): return self.prediction_type
    def resolve_confidenceLevel(self, info): return self.confidence_level
    def resolve_featuresUsed(self, info): return self.features_used
    def resolve_modelVersion(self, info): return self.model_version
    def resolve_predictionHorizonHours(self, info): return self.prediction_horizon_hours
    def resolve_wasCorrect(self, info): return self.was_correct
    def resolve_actualReturn(self, info): return self.actual_return


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
    symbol = graphene.String()
    prediction_type = graphene.String()
    probability = graphene.Float()
    confidence_level = graphene.String()
    explanation = graphene.String()
    features_used = graphene.JSONString()
    created_at = graphene.DateTime()
    expires_at = graphene.DateTime()

    def resolve_expiresAt(self, info): return self.expires_at
    def resolve_createdAt(self, info): return self.created_at
    def resolve_predictionType(self, info): return self.prediction_type
    def resolve_confidenceLevel(self, info): return self.confidence_level
    def resolve_featuresUsed(self, info): return self.features_used


# ------------ NEW AAVE-style GraphQL types ------------
class LendingReserveType(DjangoObjectType):
    class Meta:
        model = LendingReserve
        fields = "__all__"

class SupplyPositionType(DjangoObjectType):
    class Meta:
        model = SupplyPosition
        fields = "__all__"

class BorrowPositionType(DjangoObjectType):
    class Meta:
        model = BorrowPosition
        fields = "__all__"

class DeFiAccountType(graphene.ObjectType):
    collateral_usd = graphene.Float()
    debt_usd = graphene.Float()
    ltv_weighted = graphene.Float()
    liq_threshold_weighted = graphene.Float()
    available_borrow_usd = graphene.Float()
    health_factor = graphene.Float()
    supplies = graphene.List(SupplyPositionType)
    borrows = graphene.List(BorrowPositionType)
    prices_usd = graphene.JSONString()


# ------------ Queries ------------
class CryptoQuery(graphene.ObjectType):
    # existing
    supported_currencies = graphene.List(CryptocurrencyType)
    crypto_price = graphene.Field(CryptoPriceType, symbol=graphene.String(required=True))
    crypto_portfolio = graphene.Field(CryptoPortfolioType)
    crypto_analytics = graphene.Field(CryptoAnalyticsType)
    crypto_trades = graphene.List(CryptoTradeType, symbol=graphene.String(), limit=graphene.Int(default_value=50))
    crypto_predictions = graphene.List(CryptoMLPredictionType, symbol=graphene.String(required=True))
    crypto_ml_signal = graphene.Field(CryptoMLSignalType, symbol=graphene.String(required=True))
    crypto_sbloc_loans = graphene.List(
        CryptoSBLOCLoanType,
        deprecation_reason="Deprecated—migrate to defiReserves/defiAccount + lending mutations."
    )

    # NEW AAVE-style
    defi_reserves = graphene.List(LendingReserveType, description="Active reserves with risk params/APYs")
    defi_account = graphene.Field(DeFiAccountType, description="User's lending account overview")

    # ---- existing resolvers ----
    def resolve_supported_currencies(self, info):
        return Cryptocurrency.objects.filter(is_active=True).order_by('symbol')

    def resolve_crypto_price(self, info, symbol):
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            return CryptoPrice.objects.filter(cryptocurrency=currency).first()
        except Cryptocurrency.DoesNotExist:
            return None

    def resolve_crypto_portfolio(self, info):
        user = MLMutationAuth.require_authentication(info.context)
        if not user: return None
        portfolio, _ = CryptoPortfolio.objects.get_or_create(user=user)
        return portfolio

    def resolve_crypto_analytics(self, info):
        user = MLMutationAuth.require_authentication(info.context)
        if not user: return None
        try:
            portfolio, _ = CryptoPortfolio.objects.get_or_create(user=user)
            holdings = portfolio.holdings.all()
            total_value = float(portfolio.total_value_usd)
            sector_allocation = {}
            for h in holdings:
                tier = h.cryptocurrency.volatility_tier
                sector_allocation[tier] = sector_allocation.get(tier, 0) + float(h.current_value)
            for tier in sector_allocation:
                sector_allocation[tier] = (sector_allocation[tier] / total_value * 100) if total_value > 0 else 0

            best_performer = worst_performer = None
            if holdings:
                perf = [{"symbol": h.cryptocurrency.symbol, "pnl_percentage": float(h.unrealized_pnl_percentage)} for h in holdings]
                perf.sort(key=lambda x: x["pnl_percentage"], reverse=True)
                best_performer = perf[0] if perf else None
                worst_performer = perf[-1] if perf else None

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
                last_updated=portfolio.updated_at,
            )
        except Exception as e:
            logger.error(f"Error resolving crypto analytics: {e}")
            return None

    def resolve_crypto_trades(self, info, symbol=None, limit=50):
        user = MLMutationAuth.require_authentication(info.context)
        if not user: return []
        trades = CryptoTrade.objects.filter(user=user)
        if symbol:
            try:
                currency = Cryptocurrency.objects.get(symbol=symbol.upper())
                trades = trades.filter(cryptocurrency=currency)
            except Cryptocurrency.DoesNotExist:
                return []
        return trades.order_by('-execution_time')[:limit]

    def resolve_crypto_predictions(self, info, symbol):
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            return CryptoMLPrediction.objects.filter(cryptocurrency=currency).order_by('-created_at')[:10]
        except Cryptocurrency.DoesNotExist:
            return []

    def resolve_crypto_ml_signal(self, info, symbol):
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            p = CryptoMLPrediction.objects.filter(cryptocurrency=currency).order_by('-created_at').first()
            if not p: return None
            return CryptoMLSignalType(
                symbol=currency.symbol,
                prediction_type=p.prediction_type,
                probability=float(p.probability),
                confidence_level=p.confidence_level,
                explanation=f"Probability of {p.prediction_type.lower()}: {float(p.probability):.1%}",
                features_used=p.features_used,
                created_at=p.created_at,
                expires_at=p.expires_at,
            )
        except Cryptocurrency.DoesNotExist:
            return None

    def resolve_crypto_sbloc_loans(self, info):
        # Deprecated path kept for backwards-compat
        user = MLMutationAuth.require_authentication(info.context)
        if not user: return []
        return CryptoSBLOCLoan.objects.filter(user=user).order_by('-created_at')

    # ---- NEW AAVE resolvers ----
    def resolve_defi_reserves(self, info):
        return LendingReserve.objects.filter(is_active=True).select_related("cryptocurrency").order_by("cryptocurrency__symbol")

    def resolve_defi_account(self, info):
        user = MLMutationAuth.require_authentication(info.context)
        if not user: return None

        supplies = SupplyPosition.objects.filter(user=user).select_related("reserve__cryptocurrency")
        borrows = BorrowPosition.objects.filter(user=user, is_active=True).select_related("reserve__cryptocurrency")

        symbols = list({*[s.reserve.cryptocurrency.symbol for s in supplies], *[b.reserve.cryptocurrency.symbol for b in borrows]})
        prices = _latest_price_map(symbols)

        # Collateral (with weighted liquidation threshold)
        triplets = [(s.reserve, s.quantity, s.use_as_collateral) for s in supplies]
        coll_usd, liq_th = total_collateral_usd(triplets, prices)

        # Weighted LTV across collateral
        w_ltv = _weighted([s.reserve for s in supplies], [s.quantity for s in supplies], prices, "ltv")

        # Debt
        debt_usd = total_debt_usd([(b.reserve, b.amount) for b in borrows], prices)

        # Headroom & HF
        avail_usd = available_borrow_usd(coll_usd, w_ltv, debt_usd)
        hf = health_factor(coll_usd, liq_th, debt_usd)

        return DeFiAccountType(
            collateral_usd=_fmt8(coll_usd),
            debt_usd=_fmt8(debt_usd),
            ltv_weighted=_fmt8(w_ltv),
            liq_threshold_weighted=_fmt8(liq_th),
            available_borrow_usd=_fmt8(avail_usd),
            health_factor=float(hf),
            supplies=list(supplies),
            borrows=list(borrows),
            prices_usd={k: _fmt8(v) for k, v in prices.items()},
        )


# ------------ Mutations ------------
class ExecuteCryptoTrade(graphene.Mutation):
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
        user = MLMutationAuth.require_authentication(info.context)
        if not user:
            return ExecuteCryptoTrade(success=False, message="Authentication required")

        try:
            if trade_type not in ['BUY', 'SELL']:
                return ExecuteCryptoTrade(success=False, message="Invalid trade type")

            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            if price_per_unit is None:
                latest_price = CryptoPrice.objects.filter(cryptocurrency=currency).first()
                if not latest_price:
                    return ExecuteCryptoTrade(success=False, message="Price data not available")
                price_per_unit = float(latest_price.price_usd)

            total_amount = quantity * price_per_unit
            if total_amount < float(currency.min_trade_amount):
                return ExecuteCryptoTrade(success=False, message=f"Trade amount must be at least ${currency.min_trade_amount}")

            from datetime import datetime
            trade = CryptoTrade.objects.create(
                user=user, cryptocurrency=currency, trade_type=trade_type,
                quantity=quantity, price_per_unit=price_per_unit, total_amount=total_amount,
                order_id=f"{trade_type}_{currency.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                status='COMPLETED'
            )
            return ExecuteCryptoTrade(success=True, trade_id=trade.id, order_id=trade.order_id, message="Trade executed successfully")
        except Cryptocurrency.DoesNotExist:
            return ExecuteCryptoTrade(success=False, message="Cryptocurrency not found")
        except Exception as e:
            logger.error(f"Error executing crypto trade: {e}")
            return ExecuteCryptoTrade(success=False, message="Failed to execute trade")


# ---- Deprecated SBLOC mutation (kept for compatibility) ----
class CreateSBLOCLoan(graphene.Mutation):
    class Arguments:
        symbol = graphene.String(required=True)
        collateral_quantity = graphene.Float(required=True)
        loan_amount = graphene.Float(required=True)

    success = graphene.Boolean()
    loan_id = graphene.Int()
    message = graphene.String()

    def mutate(self, info, symbol, collateral_quantity, loan_amount):
        return CreateSBLOCLoan(success=False, message="Deprecated—use DeFi lending mutations instead.")


# ---- NEW AAVE-style mutations ----
class DefiSupply(graphene.Mutation):
    class Arguments:
        symbol = graphene.String(required=True)
        quantity = graphene.Float(required=True)
        use_as_collateral = graphene.Boolean(required=False, default_value=True)

    success = graphene.Boolean()
    message = graphene.String()
    position = graphene.Field(SupplyPositionType)

    def mutate(self, info, symbol, quantity, use_as_collateral=True):
        user = MLMutationAuth.require_authentication(info.context)
        if not user:
            return DefiSupply(success=False, message="Authentication required")

        try:
            asset = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True)
            qty = _to_dec(quantity)
            if qty <= 0:
                return DefiSupply(success=False, message="Quantity must be > 0")

            sp, _ = SupplyPosition.objects.get_or_create(user=user, reserve=reserve)
            sp.quantity = _to_dec(sp.quantity) + qty
            sp.use_as_collateral = bool(use_as_collateral)
            sp.save()
            return DefiSupply(success=True, message="Supplied", position=sp)
        except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist):
            return DefiSupply(success=False, message="Reserve not found")
        except Exception as e:
            logger.error(f"supply mutation error: {e}")
            return DefiSupply(success=False, message="Failed to supply")


class DefiWithdraw(graphene.Mutation):
    class Arguments:
        symbol = graphene.String(required=True)
        quantity = graphene.Float(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    remaining = graphene.Float()

    def mutate(self, info, symbol, quantity):
        user = MLMutationAuth.require_authentication(info.context)
        if not user:
            return DefiWithdraw(success=False, message="Authentication required")

        try:
            asset = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True)
            sp = SupplyPosition.objects.get(user=user, reserve=reserve)
            qty = _to_dec(quantity)
            if qty <= 0 or qty > _to_dec(sp.quantity):
                return DefiWithdraw(success=False, message="Invalid quantity")

            supplies = SupplyPosition.objects.filter(user=user).select_related("reserve__cryptocurrency")
            borrows = BorrowPosition.objects.filter(user=user, is_active=True).select_related("reserve__cryptocurrency")
            symbols = list({*[s.reserve.cryptocurrency.symbol for s in supplies], *[b.reserve.cryptocurrency.symbol for b in borrows]})
            prices = _latest_price_map(symbols)

            # simulate after
            triplets = []
            for s in supplies:
                new_q = _to_dec(s.quantity) - qty if s.id == sp.id else _to_dec(s.quantity)
                triplets.append((s.reserve, new_q, s.use_as_collateral))

            coll_usd, liq_th = total_collateral_usd(triplets, prices)
            debt_usd = total_debt_usd([(b.reserve, b.amount) for b in borrows], prices)
            hf_after = health_factor(coll_usd, liq_th, debt_usd)
            if hf_after <= Decimal("1"):
                return DefiWithdraw(success=False, message="Withdrawal would drop Health Factor ≤ 1")

            sp.quantity = _to_dec(sp.quantity) - qty
            sp.save(update_fields=["quantity"])

            return DefiWithdraw(success=True, message="Withdrawn", remaining=_fmt8(sp.quantity))
        except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist, SupplyPosition.DoesNotExist):
            return DefiWithdraw(success=False, message="Position not found")
        except Exception as e:
            logger.error(f"withdraw mutation error: {e}")
            return DefiWithdraw(success=False, message="Failed to withdraw")


class DefiBorrow(graphene.Mutation):
    class Arguments:
        symbol = graphene.String(required=True)
        amount = graphene.Float(required=True)  # in asset units
        rate_mode = graphene.String(required=False, default_value="VARIABLE")  # VARIABLE|STABLE

    success = graphene.Boolean()
    message = graphene.String()
    position = graphene.Field(BorrowPositionType)
    health_factor_after = graphene.Float()

    def mutate(self, info, symbol, amount, rate_mode="VARIABLE"):
        user = MLMutationAuth.require_authentication(info.context)
        if not user:
            return DefiBorrow(success=False, message="Authentication required")

        try:
            asset = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True, can_borrow=True)
            amt = _to_dec(amount)
            if amt <= 0:
                return DefiBorrow(success=False, message="Amount must be > 0")

            supplies = SupplyPosition.objects.filter(user=user).select_related("reserve__cryptocurrency")
            borrows = BorrowPosition.objects.filter(user=user, is_active=True).select_related("reserve__cryptocurrency")

            price_symbols = list({symbol.upper(), *[s.reserve.cryptocurrency.symbol for s in supplies], *[b.reserve.cryptocurrency.symbol for b in borrows]})
            prices = _latest_price_map(price_symbols)

            coll_usd, liq_th = total_collateral_usd([(s.reserve, s.quantity, s.use_as_collateral) for s in supplies], prices)
            w_ltv = _weighted([s.reserve for s in supplies], [s.quantity for s in supplies], prices, "ltv")
            debt_usd = total_debt_usd([(b.reserve, b.amount) for b in borrows], prices)

            avail_usd = available_borrow_usd(coll_usd, w_ltv, debt_usd)
            borrow_usd = amt * _to_dec(prices.get(symbol.upper(), 0))
            if borrow_usd <= 0:
                return DefiBorrow(success=False, message="Missing price for borrow asset")
            if borrow_usd > avail_usd:
                return DefiBorrow(success=False, message="Borrow exceeds available headroom")

            hf_after = health_factor(coll_usd, liq_th, debt_usd + borrow_usd)
            if hf_after <= Decimal("1"):
                return DefiBorrow(success=False, message="Borrow would drop Health Factor ≤ 1")

            bp, created = BorrowPosition.objects.get_or_create(
                user=user, reserve=reserve, is_active=True,
                defaults=dict(amount=amt, rate_mode=rate_mode)
            )
            if not created:
                bp.amount = _to_dec(bp.amount) + amt
                bp.rate_mode = rate_mode
            bp.save()

            return DefiBorrow(success=True, message="Borrowed", position=bp, health_factor_after=float(hf_after))
        except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist):
            return DefiBorrow(success=False, message="Reserve not found")
        except Exception as e:
            logger.error(f"borrow mutation error: {e}")
            return DefiBorrow(success=False, message="Failed to borrow")


class DefiRepay(graphene.Mutation):
    class Arguments:
        symbol = graphene.String(required=True)
        amount = graphene.Float(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    remaining = graphene.Float()
    is_active = graphene.Boolean()

    def mutate(self, info, symbol, amount):
        user = MLMutationAuth.require_authentication(info.context)
        if not user:
            return DefiRepay(success=False, message="Authentication required")

        try:
            asset = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True)
            bp = BorrowPosition.objects.get(user=user, reserve=reserve, is_active=True)

            amt = _to_dec(amount)
            if amt <= 0:
                return DefiRepay(success=False, message="Amount must be > 0")

            new_amt = _to_dec(bp.amount) - amt
            if new_amt <= 0:
                bp.amount = Decimal("0")
                bp.is_active = False
            else:
                bp.amount = new_amt
            bp.save(update_fields=["amount", "is_active"])

            return DefiRepay(success=True, message="Repaid", remaining=_fmt8(bp.amount), is_active=bp.is_active)
        except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist, BorrowPosition.DoesNotExist):
            return DefiRepay(success=False, message="Borrow position not found")
        except Exception as e:
            logger.error(f"repay mutation error: {e}")
            return DefiRepay(success=False, message="Failed to repay")


class DefiToggleCollateral(graphene.Mutation):
    class Arguments:
        symbol = graphene.String(required=True)
        use_as_collateral = graphene.Boolean(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    use_as_collateral = graphene.Boolean()
    health_factor_after = graphene.Float()

    def mutate(self, info, symbol, use_as_collateral):
        user = MLMutationAuth.require_authentication(info.context)
        if not user:
            return DefiToggleCollateral(success=False, message="Authentication required")

        try:
            asset = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)
            reserve = LendingReserve.objects.get(cryptocurrency=asset, is_active=True)
            sp = SupplyPosition.objects.get(user=user, reserve=reserve)

            supplies = SupplyPosition.objects.filter(user=user).select_related("reserve__cryptocurrency")
            borrows = BorrowPosition.objects.filter(user=user, is_active=True).select_related("reserve__cryptocurrency")
            prices = _latest_price_map(list({*[s.reserve.cryptocurrency.symbol for s in supplies], *[b.reserve.cryptocurrency.symbol for b in borrows]}))

            triplets = []
            for s in supplies:
                flag = bool(use_as_collateral) if s.id == sp.id else s.use_as_collateral
                triplets.append((s.reserve, s.quantity, flag))

            coll_usd, liq_th = total_collateral_usd(triplets, prices)
            debt_usd = total_debt_usd([(b.reserve, b.amount) for b in borrows], prices)
            hf_after = health_factor(coll_usd, liq_th, debt_usd)

            if hf_after <= Decimal("1"):
                return DefiToggleCollateral(success=False, message="Toggle would drop Health Factor ≤ 1")

            sp.use_as_collateral = bool(use_as_collateral)
            sp.save(update_fields=["use_as_collateral"])

            return DefiToggleCollateral(
                success=True, message="Updated",
                use_as_collateral=sp.use_as_collateral,
                health_factor_after=float(hf_after)
            )
        except (Cryptocurrency.DoesNotExist, LendingReserve.DoesNotExist, SupplyPosition.DoesNotExist):
            return DefiToggleCollateral(success=False, message="Supply position not found")
        except Exception as e:
            logger.error(f"toggle collateral mutation error: {e}")
            return DefiToggleCollateral(success=False, message="Failed to toggle collateral")


class GenerateMLPrediction(graphene.Mutation):
    class Arguments:
        symbol = graphene.String(required=True)

    success = graphene.Boolean()
    prediction_id = graphene.Int()
    probability = graphene.Float()
    explanation = graphene.String()
    message = graphene.String()

    def mutate(self, info, symbol):
        user = MLMutationAuth.require_authentication(info.context)
        if not user:
            return GenerateMLPrediction(success=False, message="Authentication required")
        try:
            currency = Cryptocurrency.objects.get(symbol=symbol.upper(), is_active=True)

            # recent price data
            from datetime import datetime, timedelta
            end_date = datetime.now(); start_date = end_date - timedelta(days=365)
            price_data = CryptoPrice.objects.filter(
                cryptocurrency=currency, timestamp__gte=start_date, timestamp__lte=end_date
            ).order_by('timestamp')
            if len(price_data) < 100:
                return GenerateMLPrediction(success=False, message="Insufficient price data for prediction")

            import pandas as pd
            df = pd.DataFrame([{
                'timestamp': p.timestamp, 'open': float(p.price_usd), 'high': float(p.price_usd),
                'low': float(p.price_usd), 'close': float(p.price_usd),
                'volume': float(p.volume_24h) if p.volume_24h else 1000000,
                'funding_rate': 0.0, 'open_interest': 1000000
            } for p in price_data])

            ml_service = CryptoMLPredictionService()
            prediction = ml_service.predict_big_day(df, currency.symbol)
            if not prediction:
                return GenerateMLPrediction(success=False, message="Failed to generate prediction")

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
                success=True, prediction_id=ml_prediction.id,
                probability=prediction.probability, explanation=prediction.explanation,
                message="Prediction generated successfully"
            )
        except Cryptocurrency.DoesNotExist:
            return GenerateMLPrediction(success=False, message="Cryptocurrency not found")
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            return GenerateMLPrediction(success=False, message="Failed to generate prediction")


class StressTestHF(graphene.Mutation):
    """Stress test Health Factor with price shocks"""
    class Arguments:
        shocks = graphene.List(graphene.Float, default_value=[-0.2, -0.3, -0.5])

    success = graphene.Boolean()
    results = graphene.JSONString()
    message = graphene.String()

    def mutate(self, info, shocks=None):
        user = MLMutationAuth.require_authentication(info.context)
        if not user:
            return StressTestHF(success=False, message="Authentication required")
        
        try:
            from .aave_risk import stress_test_hf
            
            # Get user's current positions
            supplies = SupplyPosition.objects.filter(user=user).select_related("reserve__cryptocurrency")
            borrows = BorrowPosition.objects.filter(user=user, is_active=True).select_related("reserve__cryptocurrency")
            
            # Get current prices
            symbols = list({*[s.reserve.cryptocurrency.symbol for s in supplies], *[b.reserve.cryptocurrency.symbol for b in borrows]})
            prices = _latest_price_map(symbols)
            
            # Convert to tuples for risk engine
            supplies_tuples = [(s.reserve, s.quantity, s.use_as_collateral) for s in supplies]
            borrows_tuples = [(b.reserve, b.amount) for b in borrows]
            
            # Run stress test
            results = stress_test_hf(supplies_tuples, borrows_tuples, prices, shocks or [-0.2, -0.3, -0.5])
            
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
            
            return StressTestHF(success=True, results=results_data, message="Stress test completed")
            
        except Exception as e:
            logger.error(f"Error running stress test: {e}")
            return StressTestHF(success=False, message="Failed to run stress test")


class CryptoMutation(graphene.ObjectType):
    execute_crypto_trade = ExecuteCryptoTrade.Field()
    # Deprecated SBLOC mutation kept for compatibility
    create_sbloc_loan = CreateSBLOCLoan.Field(
        deprecation_reason="Deprecated—use DeFi lending mutations instead."
    )

    # NEW DeFi lending mutations
    defi_supply = DefiSupply.Field()
    defi_withdraw = DefiWithdraw.Field()
    defi_borrow = DefiBorrow.Field()
    defi_repay = DefiRepay.Field()
    defi_toggle_collateral = DefiToggleCollateral.Field()
    generate_ml_prediction = GenerateMLPrediction.Field()
    stress_test_hf = StressTestHF.Field()