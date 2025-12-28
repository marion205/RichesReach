"""
REST API Views for Market Data
"""
import json

import asyncio

import logging

from typing import Dict, Any, List



from django.http import JsonResponse

from django.views import View

from django.views.decorators.csrf import csrf_exempt

from django.utils.decorators import method_decorator



logger = logging.getLogger(__name__)



# Try to import market data service

try:

    from .market_data_api_service import MarketDataAPIService, DataProvider



    market_data_service = MarketDataAPIService()

    MARKET_DATA_AVAILABLE = True

except Exception as e:

    logger.warning(f"MarketDataAPIService not available: {e}")

    MARKET_DATA_AVAILABLE = False

    market_data_service = None





# CSRF exempt - Bearer token auth only (see CSRF_VERIFICATION_CHECKLIST.md)
@method_decorator(csrf_exempt, name="dispatch")

class QuotesView(View):

    """

    GET /api/market/quotes?symbols=AAPL,MSFT,GOOGL

    Returns real-time or cached stock quotes

    """



    def get(self, request):

        try:

            symbols_param = request.GET.get("symbols", "")

            if not symbols_param:

                return JsonResponse(

                    {"error": "symbols parameter is required"}, status=400

                )



            symbols = [

                s.strip().upper()

                for s in symbols_param.split(",")

                if s.strip()

            ]

            if not symbols:

                return JsonResponse(

                    {"error": "No valid symbols provided"}, status=400

                )



            logger.info(

                f"📊 [Quotes API] Fetching quotes for {len(symbols)} symbols: "

                f'{", ".join(symbols)}'

            )



            # If market data service is available, use it

            if MARKET_DATA_AVAILABLE and market_data_service:

                quotes: List[Dict[str, Any]] = []



                # Create a loop once per request, not per symbol

                loop = asyncio.new_event_loop()

                asyncio.set_event_loop(loop)

                try:

                    tasks = [

                        market_data_service.get_stock_quote(symbol)

                        for symbol in symbols

                    ]

                    results = loop.run_until_complete(

                        asyncio.gather(*tasks, return_exceptions=True)

                    )

                finally:

                    loop.close()



                for symbol, result in zip(symbols, results):

                    if isinstance(result, Exception):

                        logger.warning(

                            f"Error fetching quote for {symbol}: {result}"

                        )

                        quotes.append(self._get_mock_quote(symbol))

                        continue



                    quote_data = result or {}

                    if quote_data:

                        quotes.append(

                            {

                                "symbol": symbol,

                                "price": quote_data.get("price", 0.0),

                                "change": quote_data.get("change", 0.0),

                                "changePercent": quote_data.get(

                                    "change_percent", 0.0

                                ),

                                "volume": quote_data.get("volume", 0),

                                "high": quote_data.get("high", 0.0),

                                "low": quote_data.get("low", 0.0),

                                "open": quote_data.get("open", 0.0),

                                "previousClose": quote_data.get(

                                    "previous_close", 0.0

                                ),

                                "timestamp": quote_data.get("timestamp", ""),

                            }

                        )

                    else:

                        quotes.append(self._get_mock_quote(symbol))



                logger.info(f"✅ [Quotes API] Returning {len(quotes)} quotes")

                return JsonResponse(quotes, safe=False)



            else:

                # Fallback to mock data if service unavailable

                logger.warning(

                    "⚠️ [Quotes API] MarketDataAPIService unavailable, using mock data"

                )

                quotes = [self._get_mock_quote(symbol) for symbol in symbols]

                return JsonResponse(quotes, safe=False)



        except Exception as e:

            logger.error(f"❌ [Quotes API] Error: {e}", exc_info=True)

            return JsonResponse({"error": str(e)}, status=500)



    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:

        """Generate mock quote data for a symbol."""

        base_price = 100.0 + (hash(symbol) % 500)

        change = (hash(symbol) % 20) - 10

        return {

            "symbol": symbol,

            "price": base_price,

            "change": change,

            "changePercent": (change / base_price) * 100,

            "volume": (hash(symbol) % 10_000_000) + 1_000_000,

            "high": base_price + 5,

            "low": base_price - 5,

            "open": base_price + 2,

            "previousClose": base_price - 2,

            "timestamp": "",

        }
