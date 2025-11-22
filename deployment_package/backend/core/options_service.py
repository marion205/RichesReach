"""
OptionsAnalysisService

Provides a unified interface to get options data, unusual flow,
recommended strategies, and market sentiment for a given symbol.

Right now this implementation returns high-quality mock data in a
stable structure that matches what `premium_types.py` expects.

Later, you can plug in real providers (Polygon, Finnhub, IEX, etc.)
inside the helper methods without changing the public API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OptionsContract:
    symbol: str
    contract_symbol: str
    strike: float
    expiration_date: str
    option_type: str  # "call" or "put"
    bid: float
    ask: float
    last_price: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    intrinsic_value: float
    time_value: float
    days_to_expiration: int


class OptionsAnalysisService:
    """
    Core service to generate a comprehensive options analysis payload.

    Public entry point:
        get_comprehensive_analysis(symbol: str) -> Dict[str, Any]

    This is what `PremiumQueries.resolve_options_analysis` calls.
    """

    def __init__(self) -> None:
        # Initialize with real data providers
        import os
        try:
            self.polygon_api_key = os.getenv("POLYGON_API_KEY") or os.getenv("EXPO_PUBLIC_POLYGON_API_KEY") or ""
            self.finnhub_api_key = os.getenv("FINNHUB_API_KEY") or "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"
            self.use_real_data = bool(self.polygon_api_key or self.finnhub_api_key)
        except Exception as e:
            logger.warning(f"Error initializing API keys: {e}")
            self.polygon_api_key = ""
            self.finnhub_api_key = ""
            self.use_real_data = False

    # --------------------------------------------------------------------- #
    # Public API                                                            #
    # --------------------------------------------------------------------- #

    def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Return a full options analysis structure for a symbol.

        The structure must match what `OptionsAnalysisType` in
        `premium_types.py` expects:

        {
            "underlying_symbol": str,
            "underlying_price": float,
            "options_chain": { ... },
            "unusual_flow": [ ... ],
            "recommended_strategies": [ ... ],
            "market_sentiment": { ... }
        }
        """
        try:
            symbol = symbol.upper().strip()
            logger.info(f"Building options analysis for: {symbol}")

            # Get real underlying price
            underlying_price = self._get_underlying_price(symbol)
            
            # Try to get real options data, fallback to mock if unavailable
            options_chain = self._get_real_options_chain(symbol, underlying_price)
            if not options_chain:
                options_chain = self._build_mock_options_chain(symbol, underlying_price)
            
            # Try to get real unusual flow, fallback to mock
            unusual_flow = self._get_real_unusual_flow(symbol, underlying_price)
            if not unusual_flow:
                unusual_flow = self._build_mock_unusual_flow(symbol, underlying_price)
            
            # Build strategies and sentiment from real or mock chain
            recommended_strategies = self._build_mock_strategies(
                symbol, underlying_price, options_chain
            )
            market_sentiment = self._calculate_real_market_sentiment(symbol, options_chain)

            result: Dict[str, Any] = {
                "underlying_symbol": symbol,
                "underlying_price": float(underlying_price),
                "options_chain": options_chain,
                "unusual_flow": unusual_flow,
                "recommended_strategies": recommended_strategies,
                "market_sentiment": market_sentiment,
            }

            logger.info(
                "Options analysis built for %s: chain_calls=%d chain_puts=%d",
                symbol,
                len(options_chain.get("calls", [])),
                len(options_chain.get("puts", [])),
            )
            return result

        except Exception as e:
            logger.error(f"Error building options analysis for {symbol}: {e}")
            # As a last resort return a minimal but valid structure so
            # GraphQL doesn't explode.
            return {
                "underlying_symbol": symbol,
                "underlying_price": 0.0,
                "options_chain": {
                    "expiration_dates": [],
                    "calls": [],
                    "puts": [],
                    "greeks": {
                        "delta": 0.0,
                        "gamma": 0.0,
                        "theta": 0.0,
                        "vega": 0.0,
                        "rho": 0.0,
                    },
                },
                "unusual_flow": [],
                "recommended_strategies": [],
                "market_sentiment": {
                    "put_call_ratio": 1.0,
                    "implied_volatility_rank": 0.0,
                    "skew": 0.0,
                    "sentiment_score": 50.0,
                    "sentiment_description": "Neutral",
                },
            }

    # --------------------------------------------------------------------- #
    # Internal helpers (mock / placeholder implementations)                 #
    # --------------------------------------------------------------------- #

    def _get_underlying_price(self, symbol: str) -> float:
        """
        Get real underlying price from APIs
        """
        try:
            import requests
        except ImportError:
            logger.warning("requests library not available, using fallback price")
            base = 100.0
            offset = (sum(ord(c) for c in symbol) % 50)
            return round(base + offset, 2)
        
        # Try Finnhub first (free tier)
        if self.finnhub_api_key:
            try:
                url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_api_key}"
                response = requests.get(url, timeout=5)
                if response.ok:
                    data = response.json()
                    if data.get('c') and data['c'] > 0:
                        logger.info(f"✅ Fetched real price for {symbol}: ${data['c']}")
                        return float(data['c'])
            except Exception as e:
                logger.warning(f"Finnhub price fetch failed for {symbol}: {e}")
        
        # Try Polygon
        if self.polygon_api_key:
            try:
                url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={self.polygon_api_key}"
                response = requests.get(url, timeout=5)
                if response.ok:
                    data = response.json()
                    if data.get('results') and len(data['results']) > 0:
                        price = data['results'][0].get('c', 0)
                        if price > 0:
                            logger.info(f"✅ Fetched real price from Polygon for {symbol}: ${price}")
                            return float(price)
            except Exception as e:
                logger.warning(f"Polygon price fetch failed for {symbol}: {e}")
        
        # Fallback to mock price
        logger.warning(f"Using fallback price for {symbol}")
        base = 100.0
        offset = (sum(ord(c) for c in symbol) % 50)
        return round(base + offset, 2)

    def _build_mock_options_chain(
        self,
        symbol: str,
        underlying_price: float,
    ) -> Dict[str, Any]:
        """
        Return a mock options chain with expiration_dates, calls, puts, and greeks.
        """
        today = datetime.utcnow().date()

        expirations = [
            (today + timedelta(days=14)).strftime("%Y-%m-%d"),
            (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            (today + timedelta(days=60)).strftime("%Y-%m-%d"),
        ]

        # Build 3 call contracts around ATM
        calls: List[Dict[str, Any]] = []
        puts: List[Dict[str, Any]] = []

        for idx, exp in enumerate(expirations):
            days_to_exp = (datetime.strptime(exp, "%Y-%m-%d").date() - today).days
            # ATM-ish strikes
            call_strike = round(underlying_price * (1 + 0.02 * idx), 2)
            put_strike = round(underlying_price * (1 - 0.02 * idx), 2)

            calls.append(
                self._make_mock_contract(
                    symbol=symbol,
                    option_type="call",
                    strike=call_strike,
                    expiration_date=exp,
                    days_to_exp=days_to_exp,
                    underlying_price=underlying_price,
                    id_suffix=f"C{idx}",
                )
            )
            puts.append(
                self._make_mock_contract(
                    symbol=symbol,
                    option_type="put",
                    strike=put_strike,
                    expiration_date=exp,
                    days_to_exp=days_to_exp,
                    underlying_price=underlying_price,
                    id_suffix=f"P{idx}",
                )
            )

        greeks = {
            "delta": 0.5,
            "gamma": 0.02,
            "theta": -0.12,
            "vega": 0.25,
            "rho": 0.04,
        }

        return {
            "expiration_dates": expirations,
            "calls": calls,
            "puts": puts,
            "greeks": greeks,
        }

    def _make_mock_contract(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        expiration_date: str,
        days_to_exp: int,
        underlying_price: float,
        id_suffix: str,
    ) -> Dict[str, Any]:
        """
        Helper to build a single mock options contract dict with all fields
        that `OptionsContractType` / frontend expects.
        """
        in_the_money = (
            underlying_price > strike if option_type == "call" else underlying_price < strike
        )
        intrinsic = max(
            (underlying_price - strike) if option_type == "call" else (strike - underlying_price),
            0.0,
        )
        base_premium = max(1.5, intrinsic + 0.5)

        last_price = round(base_premium, 2)
        bid = round(last_price - 0.1, 2)
        ask = round(last_price + 0.1, 2)

        volume = 500 + (days_to_exp * 3)
        open_interest = 2000 + (days_to_exp * 10)

        iv = 0.25 + (0.05 if in_the_money else 0.0)

        delta = 0.65 if option_type == "call" else -0.35
        gamma = 0.02
        theta = -0.15
        vega = 0.3
        rho = 0.05 if option_type == "call" else -0.03

        return {
            "symbol": symbol,
            "contract_symbol": f"{symbol.replace('.', '')}_{expiration_date}_{option_type.upper()}{id_suffix}",
            "strike": float(strike),
            "expiration_date": expiration_date,
            "option_type": option_type,
            "bid": float(bid),
            "ask": float(ask),
            "last_price": float(last_price),
            "volume": int(volume),
            "open_interest": int(open_interest),
            "implied_volatility": float(iv),
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega),
            "rho": float(rho),
            "intrinsic_value": float(round(intrinsic, 2)),
            "time_value": float(round(last_price - intrinsic, 2)),
            "days_to_expiration": int(days_to_exp),
        }

    def _build_mock_unusual_flow(
        self,
        symbol: str,
        underlying_price: float,
    ) -> List[Dict[str, Any]]:
        """
        Build a small list of mock unusual options flow events.
        """
        today = datetime.utcnow().date()
        exp = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        strike = round(underlying_price * 1.05, 2)

        return [
            {
                "symbol": symbol,
                "contract_symbol": f"{symbol.replace('.', '')}_{exp}_C_SWEEP",
                "option_type": "call",
                "strike": float(strike),
                "expiration_date": exp,
                "volume": 5000,
                "open_interest": 15000,
                "premium": float(round(5000 * 2.6, 2)),
                "implied_volatility": 0.30,
                "unusual_activity_score": 0.85,
                "activity_type": "Sweep",
            }
        ]

    def _build_mock_strategies(
        self,
        symbol: str,
        underlying_price: float,
        options_chain: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Build a few example strategies using the mock chain.
        """
        return [
            {
                "strategy_name": "Covered Call",
                "strategy_type": "Covered Call",
                "max_profit": 7.50,
                "max_loss": -142.50,
                "breakeven_points": [underlying_price - 7.5],
                "probability_of_profit": 0.65,
                "risk_reward_ratio": 0.05,
                "days_to_expiration": 30,
                "total_cost": 0.0,
                "total_credit": 2.60,
                "description": "Generate income on shares you already own by selling calls.",
                "risk_level": "Medium",
                "market_outlook": "Neutral to mildly bullish",
            },
            {
                "strategy_name": "Protective Put",
                "strategy_type": "Protective Put",
                "max_profit": float("inf"),
                "max_loss": 5.00,
                "breakeven_points": [underlying_price - 5.0],
                "probability_of_profit": 0.55,
                "risk_reward_ratio": 0.20,
                "days_to_expiration": 30,
                "total_cost": 5.00,
                "total_credit": 0.0,
                "description": "Buy puts to protect downside on your long stock.",
                "risk_level": "Low",
                "market_outlook": "Cautious / downside protection",
            },
        ]

    def _get_real_options_chain(
        self,
        symbol: str,
        underlying_price: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Try to fetch real options chain from APIs
        """
        if not self.use_real_data:
            return None
        
        # Note: Options chain data typically requires premium API access
        # For now, we'll try Polygon but may need to fallback to mock
        # Polygon options endpoint requires premium subscription
        return None  # Will use mock for now
    
    def _get_real_unusual_flow(
        self,
        symbol: str,
        underlying_price: float,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Try to fetch real unusual options flow from APIs
        """
        if not self.use_real_data:
            return None
        
        # Unusual flow typically requires premium data sources
        # Could integrate with services like FlowAlgo, Cheddar Flow, etc.
        return None  # Will use mock for now
    
    def _calculate_real_market_sentiment(
        self,
        symbol: str,
        options_chain: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate market sentiment from real or mock options chain data
        """
        calls = options_chain.get("calls", [])
        puts = options_chain.get("puts", [])
        call_volume = sum(c.get("volume", 0) for c in calls)
        put_volume = sum(p.get("volume", 0) for p in puts)
        total_volume = call_volume + put_volume

        if total_volume == 0:
            put_call_ratio = 1.0
        else:
            put_call_ratio = put_volume / max(call_volume, 1)

        # Calculate IV rank from chain if available
        iv_rank = 50.0
        if calls or puts:
            all_ivs = [c.get("implied_volatility", 0.25) for c in calls] + [p.get("implied_volatility", 0.25) for p in puts]
            if all_ivs:
                avg_iv = sum(all_ivs) / len(all_ivs)
                # Normalize IV to 0-100 rank (simplified)
                iv_rank = min(100, max(0, (avg_iv - 0.15) / 0.3 * 100))

        # Calculate skew (put/call IV skew)
        call_ivs = [c.get("implied_volatility", 0.25) for c in calls if c.get("implied_volatility")]
        put_ivs = [p.get("implied_volatility", 0.25) for p in puts if p.get("implied_volatility")]
        skew = 0.0
        if call_ivs and put_ivs:
            avg_call_iv = sum(call_ivs) / len(call_ivs)
            avg_put_iv = sum(put_ivs) / len(put_ivs)
            if avg_call_iv > 0:
                skew = (avg_put_iv - avg_call_iv) / avg_call_iv

        # Sentiment based on put/call ratio
        if put_call_ratio < 0.7:
            sentiment_desc = "Bullish"
            score = 70.0
        elif put_call_ratio > 1.2:
            sentiment_desc = "Bearish"
            score = 40.0
        else:
            sentiment_desc = "Neutral"
            score = 55.0

        return {
            "put_call_ratio": float(round(put_call_ratio, 2)),
            "implied_volatility_rank": float(round(iv_rank, 1)),
            "skew": float(round(skew, 3)),
            "sentiment_score": float(score),
            "sentiment_description": sentiment_desc,
        }
    
    def _build_mock_market_sentiment(
        self,
        symbol: str,
        options_chain: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Fallback: Build a simple sentiment snapshot from the (mock) options chain.
        """
        return self._calculate_real_market_sentiment(symbol, options_chain)
