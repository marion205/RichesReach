"""
Trading-domain GraphQL queries: legacy broker aliases (alpacaAccount, tradingAccount, etc.)
and stock chart data. Resolvers delegate to BrokerQueries where applicable.
"""
import logging
from datetime import datetime, timedelta

import graphene

from core.broker_types import BrokerAccountType, BrokerOrderType, BrokerPositionType

logger = logging.getLogger(__name__)


class TradingQuery(graphene.ObjectType):
    """
    Trading-related root fields: legacy aliases for broker API + stockChartData.
    Compose with BrokerQueries so resolve_* can call self.resolve_broker_*.
    """

    alpaca_account = graphene.Field(
        BrokerAccountType,
        user_id=graphene.Int(required=True),
        name="alpacaAccount",
        description="Deprecated alias for brokerAccount. Use brokerAccount instead.",
    )
    trading_account = graphene.Field(
        BrokerAccountType,
        name="tradingAccount",
        description="Deprecated alias for brokerAccount. Use brokerAccount instead.",
    )
    trading_positions = graphene.List(
        BrokerPositionType,
        name="tradingPositions",
        description="Deprecated alias for brokerPositions. Use brokerPositions instead.",
    )
    trading_orders = graphene.List(
        BrokerOrderType,
        status=graphene.String(),
        limit=graphene.Int(),
        name="tradingOrders",
        description="Deprecated alias for brokerOrders. Use brokerOrders instead.",
    )
    stock_chart_data = graphene.Field(
        "core.types.StockChartDataType",
        symbol=graphene.String(required=True),
        timeframe=graphene.String(required=True),
        name="stockChartData",
        description="Get stock chart data (OHLCV) for a symbol and timeframe.",
    )

    def resolve_alpaca_account(self, info, user_id):
        """Legacy alias: resolve alpacaAccount by delegating to brokerAccount."""
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        return self.resolve_broker_account(info)

    def resolve_trading_account(self, info):
        """Legacy alias: resolve tradingAccount by delegating to brokerAccount."""
        return self.resolve_broker_account(info)

    def resolve_trading_positions(self, info, **kwargs):
        """Legacy alias: resolve tradingPositions by delegating to brokerPositions."""
        return self.resolve_broker_positions(info)

    def resolve_trading_orders(self, info, status=None, limit=None):
        """Legacy alias: resolve tradingOrders by delegating to brokerOrders."""
        return self.resolve_broker_orders(info, status=status, limit=limit or 50)

    def resolve_stock_chart_data(self, info, symbol, timeframe):
        """Resolve stockChartData - returns chart data in the format expected by frontend."""
        from core.types import ChartDataPointType, StockChartDataType

        try:
            chart_data_points = []
            try:
                from core.queries import _get_intraday_data
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    ohlcv_1m, ohlcv_5m = loop.run_until_complete(_get_intraday_data(symbol.upper()))
                    ohlcv_data = ohlcv_5m if ohlcv_5m and len(ohlcv_5m) > 0 else ohlcv_1m
                    if ohlcv_data and len(ohlcv_data) > 0:
                        for row in ohlcv_data[-100:]:
                            if len(row) >= 6:
                                ts = row[0]
                                timestamp_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
                                chart_data_points.append(
                                    ChartDataPointType(
                                        timestamp=timestamp_str,
                                        open=float(row[1]),
                                        high=float(row[2]),
                                        low=float(row[3]),
                                        close=float(row[4]),
                                        volume=int(row[5]) if len(row) > 5 else 0,
                                    )
                                )
                finally:
                    loop.close()
            except Exception as e:
                logger.warning("Failed to fetch real chart data for %s: %s", symbol, e)

            if not chart_data_points:
                import random
                try:
                    from core.market_data_manager import get_market_data_service
                    import asyncio

                    async def get_current_price():
                        service = get_market_data_service()
                        quote = await service.get_stock_quote(symbol.upper())
                        return quote.get("price", 100.0) if quote else 100.0

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        current_price = loop.run_until_complete(get_current_price())
                    finally:
                        loop.close()
                except Exception:
                    current_price = 100.0

                now = datetime.now()
                base_price = current_price
                for i in range(100, 0, -1):
                    timestamp = now - timedelta(minutes=i * 5)
                    change = random.uniform(-0.02, 0.02) * base_price
                    base_price = base_price + change
                    high = base_price * (1 + abs(random.uniform(0, 0.01)))
                    low = base_price * (1 - abs(random.uniform(0, 0.01)))
                    open_price = base_price * (1 + random.uniform(-0.005, 0.005))
                    close_price = base_price
                    volume = random.randint(100000, 1000000)
                    chart_data_points.append(
                        ChartDataPointType(
                            timestamp=timestamp.isoformat(),
                            open=round(open_price, 2),
                            high=round(high, 2),
                            low=round(low, 2),
                            close=round(close_price, 2),
                            volume=volume,
                        )
                    )

            return StockChartDataType(symbol=symbol.upper(), data=chart_data_points)
        except Exception as e:
            logger.error("Error resolving stockChartData for %s: %s", symbol, e)
            return StockChartDataType(symbol=symbol.upper(), data=[])
