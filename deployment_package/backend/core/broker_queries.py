"""
GraphQL Queries for Broker Operations
"""
import graphene
from graphene_django import DjangoObjectType
from .broker_types import (
    BrokerAccountType, BrokerOrderType, BrokerPositionType,
    BrokerActivityType, BrokerFundingType, TradingQuoteType
)
from .broker_models import (
    BrokerAccount, BrokerOrder, BrokerPosition, BrokerActivity,
    BrokerFunding
)
from .alpaca_broker_service import AlpacaBrokerService, BrokerGuardrails

alpaca_service = AlpacaBrokerService()


# ---------------------------------------------------------------------------
# Trade Debrief GraphQL type
# ---------------------------------------------------------------------------

class PatternFlagType(graphene.ObjectType):
    """A single detected behavioural trading pattern."""
    code        = graphene.String()
    severity    = graphene.String()   # "high" | "medium" | "low"
    description = graphene.String()
    impact_dollars = graphene.Float()


class SectorStatsType(graphene.ObjectType):
    """Win/loss breakdown per sector."""
    sector    = graphene.String()
    trades    = graphene.Int()
    wins      = graphene.Int()
    losses    = graphene.Int()
    total_pnl = graphene.Float()
    win_rate  = graphene.Float()   # 0–1


class TradeDebriefType(graphene.ObjectType):
    """
    AI Trade Debrief — structured analysis of the user's trading behaviour.

    Fields
    ------
    headline            One-sentence summary of the biggest finding.
    narrative           3-5 sentence coaching paragraph.
    top_insight         Single most impactful pattern.
    recommendations     2-4 actionable bullet points.
    stats_summary       Key numbers as a JSON string (for flexible UI rendering).
    pattern_codes       Machine-readable list of detected pattern codes.
    sector_stats        Per-sector breakdown (win rate, P&L, trade count).
    pattern_flags       Detailed pattern flag objects.
    data_source         "broker" | "paper" | "mixed" | "none"
    has_enough_data     False when fewer than 5 trades in the window.
    total_trades        Total closed trades in the lookback window.
    win_rate_pct        Win rate as a percentage (0–100).
    total_pnl           Total realised P&L in dollars.
    best_sector         Sector with highest win rate (≥3 trades).
    worst_sector        Sector with lowest win rate (≥3 trades).
    counterfactual_extra_pnl  Estimated extra P&L if biases were corrected.
    lookback_days       Lookback window used.
    generated_at        ISO-8601 timestamp.
    """
    headline               = graphene.String()
    narrative              = graphene.String()
    top_insight            = graphene.String()
    recommendations        = graphene.List(graphene.String)
    stats_summary          = graphene.JSONString()
    pattern_codes          = graphene.List(graphene.String)
    sector_stats           = graphene.List(SectorStatsType)
    pattern_flags          = graphene.List(PatternFlagType)
    data_source            = graphene.String()
    has_enough_data        = graphene.Boolean()
    total_trades           = graphene.Int()
    win_rate_pct           = graphene.Float()
    total_pnl              = graphene.Float()
    best_sector            = graphene.String()
    worst_sector           = graphene.String()
    counterfactual_extra_pnl = graphene.Float()
    lookback_days          = graphene.Int()
    generated_at           = graphene.String()


class BrokerQueries(graphene.ObjectType):
    """GraphQL queries for broker operations"""
    
    broker_account = graphene.Field(BrokerAccountType)
    broker_orders = graphene.List(
        BrokerOrderType,
        status=graphene.String(),
        limit=graphene.Int(default_value=50)
    )
    broker_positions = graphene.List(BrokerPositionType)
    broker_activities = graphene.List(
        BrokerActivityType,
        activity_type=graphene.String(),
        date=graphene.String()
    )
    broker_account_info = graphene.JSONString()  # Returns account info with buying power, etc.

    # Trading quote for order placement
    trading_quote = graphene.Field(
        TradingQuoteType,
        symbol=graphene.String(required=True),
        description="Get trading quote (bid/ask) for a symbol"
    )

    # AI Trade Debrief
    trade_debrief = graphene.Field(
        TradeDebriefType,
        lookback_days=graphene.Int(default_value=90),
        description=(
            "AI-powered analysis of the user's trading behaviour over the "
            "last N days. Surfaces patterns like early-exit bias, sector "
            "concentration, and momentum-spike buying. Returns an LLM-narrated "
            "coaching paragraph alongside structured stats."
        )
    )
    
    def resolve_broker_account(self, info):
        """Get user's broker account"""
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        
        try:
            return BrokerAccount.objects.select_related("user").get(user=user)
        except BrokerAccount.DoesNotExist:
            return None
    
    def resolve_broker_orders(self, info, status=None, limit=50):
        """Get user's broker orders"""
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return []
        
        try:
            broker_account = BrokerAccount.objects.select_related("user").get(user=user)
            orders = (
                BrokerOrder.objects.filter(broker_account=broker_account)
                .select_related("broker_account", "broker_account__user")
            )
            if status:
                orders = orders.filter(status=status)
            return list(orders[:limit])
        except BrokerAccount.DoesNotExist:
            return []
    
    def resolve_broker_positions(self, info):
        """Get user's broker positions"""
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return []
        
        try:
            broker_account = BrokerAccount.objects.select_related("user").get(user=user)
            return list(
                BrokerPosition.objects.filter(broker_account=broker_account)
                .select_related("broker_account", "broker_account__user")
            )
        except BrokerAccount.DoesNotExist:
            return []
    
    def resolve_broker_activities(self, info, activity_type=None, date=None):
        """Get user's broker activities"""
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return []
        
        try:
            broker_account = BrokerAccount.objects.select_related("user").get(user=user)
            activities = (
                BrokerActivity.objects.filter(broker_account=broker_account)
                .select_related("broker_account", "broker_account__user")
            )
            if activity_type:
                activities = activities.filter(activity_type=activity_type)
            if date:
                activities = activities.filter(date=date)
            return list(activities)
        except BrokerAccount.DoesNotExist:
            return []
    
    def resolve_broker_account_info(self, info):
        """Get account info with buying power, daily limits, etc."""
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        
        try:
            broker_account = BrokerAccount.objects.select_related("user").get(user=user)
            
            if not broker_account.alpaca_account_id:
                return {
                    'error': 'Account not created yet',
                    'kyc_status': broker_account.kyc_status
                }
            
            # Fetch latest from Alpaca
            account_info = alpaca_service.get_account_info(broker_account.alpaca_account_id)
            account_status = alpaca_service.get_account_status(broker_account.alpaca_account_id)
            
            # Update local cache
            if account_info:
                broker_account.buying_power = float(account_info.get('buying_power', 0))
                broker_account.cash = float(account_info.get('cash', 0))
                broker_account.equity = float(account_info.get('equity', 0))
                broker_account.day_trading_buying_power = float(account_info.get('day_trading_buying_power', 0))
                broker_account.pattern_day_trader = account_info.get('pattern_day_trader', False)
                broker_account.trading_blocked = account_info.get('trading_blocked', False)
                broker_account.transfer_blocked = account_info.get('transfer_blocked', False)
                broker_account.save()
            
            if account_status:
                broker_account.kyc_status = account_status.get('kyc_results', {}).get('status', broker_account.kyc_status)
                broker_account.save()
            
            daily_notional_used = BrokerGuardrails.get_daily_notional_used(user)
            
            return {
                'account_id': broker_account.alpaca_account_id,
                'kyc_status': broker_account.kyc_status,
                'buying_power': float(broker_account.buying_power),
                'cash': float(broker_account.cash),
                'equity': float(broker_account.equity),
                'day_trading_buying_power': float(broker_account.day_trading_buying_power),
                'pattern_day_trader': broker_account.pattern_day_trader,
                'day_trade_count': broker_account.day_trade_count,
                'trading_blocked': broker_account.trading_blocked,
                'transfer_blocked': broker_account.transfer_blocked,
                'daily_notional_used': daily_notional_used,
                'daily_notional_remaining': BrokerGuardrails.MAX_DAILY_NOTIONAL - daily_notional_used,
                'max_per_order': BrokerGuardrails.MAX_PER_ORDER_NOTIONAL,
                'max_daily': BrokerGuardrails.MAX_DAILY_NOTIONAL,
            }
        except BrokerAccount.DoesNotExist:
            return {
                'error': 'Broker account not found',
                'kyc_status': 'NOT_STARTED'
            }
    
    def resolve_trading_quote(self, info, symbol):
        """Get trading quote (bid/ask) for a symbol - returns mock data immediately for fast response"""
        from datetime import datetime
        
        symbol = symbol.upper()
        
        # Return mock data immediately for fast response
        # In production, this could be enhanced to fetch real data asynchronously
        # For now, use realistic mock prices based on symbol
        mock_prices = {
            'AAPL': {'bid': 189.50, 'ask': 190.00},
            'MSFT': {'bid': 374.50, 'ask': 375.00},
            'GOOGL': {'bid': 139.50, 'ask': 140.00},
            'AMZN': {'bid': 149.50, 'ask': 150.00},
            'TSLA': {'bid': 244.50, 'ask': 245.00},
            'META': {'bid': 489.50, 'ask': 490.00},
            'NVDA': {'bid': 124.50, 'ask': 125.00},
        }
        
        # Get price for symbol or use default
        price_data = mock_prices.get(symbol, {'bid': 149.50, 'ask': 150.00})
        bid = price_data['bid']
        ask = price_data['ask']
        bid_size = 100
        ask_size = 200
        
        # Try to fetch real data in background (non-blocking) via facade
        try:
            from .market_data_manager import get_market_data_service
            import asyncio
            import threading

            def fetch_real_data_async():
                """Fetch real data in background thread"""
                try:
                    async def fetch():
                        service = get_market_data_service()
                        return await service.get_stock_quote(symbol)

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(fetch())
                    loop.close()
                    return result
                except Exception:
                    return None

            threading.Thread(target=fetch_real_data_async, daemon=True).start()
        except Exception:
            pass
        
        return TradingQuoteType(
            symbol=symbol,
            bid=bid,
            ask=ask,
            bidSize=bid_size,
            askSize=ask_size,
            timestamp=datetime.now().isoformat()
        )

    def resolve_trade_debrief(self, info, lookback_days=90):
        """
        Build and return an AI Trade Debrief for the authenticated user.

        Analyses real (Alpaca broker) and/or paper trade history, detects
        behavioural patterns (early-exit bias, sector concentration, etc.),
        and returns an LLM-narrated coaching report.

        Args:
            lookback_days: Number of calendar days to look back (default 90).

        Returns:
            TradeDebriefType or None if user is not authenticated.
        """
        import logging as _logging
        _log = _logging.getLogger(__name__)

        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None

        try:
            from .trade_debrief_formatter import build_debrief
            output = build_debrief(user, lookback_days=lookback_days)

            # Resolve sector_stats and pattern_flags from the underlying report
            # (build_debrief returns TradeDebriefOutput; re-run service for structured fields)
            from .trade_debrief_service import TradeDebriefService
            report = TradeDebriefService().build_report(user, lookback_days=lookback_days)

            sector_stats_gql = [
                SectorStatsType(
                    sector=s.sector,
                    trades=s.trades,
                    wins=s.wins,
                    losses=s.losses,
                    total_pnl=s.total_pnl,
                    win_rate=s.win_rate,
                )
                for s in report.sector_stats
            ]

            pattern_flags_gql = [
                PatternFlagType(
                    code=f.code,
                    severity=f.severity,
                    description=f.description,
                    impact_dollars=f.impact_dollars,
                )
                for f in report.pattern_flags
            ]

            import json as _json
            return TradeDebriefType(
                headline=output.headline,
                narrative=output.narrative,
                top_insight=output.top_insight,
                recommendations=output.recommendations,
                stats_summary=_json.dumps(output.stats_summary),
                pattern_codes=output.pattern_codes,
                sector_stats=sector_stats_gql,
                pattern_flags=pattern_flags_gql,
                data_source=output.data_source,
                has_enough_data=output.has_enough_data,
                total_trades=output.total_trades,
                win_rate_pct=output.win_rate_pct,
                total_pnl=output.total_pnl,
                best_sector=output.best_sector,
                worst_sector=output.worst_sector,
                counterfactual_extra_pnl=output.counterfactual_extra_pnl,
                lookback_days=output.lookback_days,
                generated_at=output.generated_at,
            )

        except Exception as exc:
            _log.exception("resolve_trade_debrief failed for user %s: %s", user.id, exc)
            # Return a safe minimal response rather than crashing the whole query
            from django.utils import timezone as _tz
            return TradeDebriefType(
                headline="Debrief temporarily unavailable.",
                narrative="We couldn't generate your trade debrief right now. Please try again shortly.",
                top_insight="",
                recommendations=[],
                stats_summary="{}",
                pattern_codes=[],
                sector_stats=[],
                pattern_flags=[],
                data_source="none",
                has_enough_data=False,
                total_trades=0,
                win_rate_pct=0.0,
                total_pnl=0.0,
                best_sector=None,
                worst_sector=None,
                counterfactual_extra_pnl=0.0,
                lookback_days=lookback_days,
                generated_at=_tz.now().isoformat(),
            )
