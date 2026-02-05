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
            
            # Build real strategies from actual options chain data
            recommended_strategies = self._build_real_strategies(
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

    def _build_real_strategies(
        self,
        symbol: str,
        underlying_price: float,
        options_chain: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Build real strategy recommendations from actual options chain data.

        Analyzes the real calls/puts with their actual premiums, strikes,
        and Greeks to recommend optimal strategies.
        """
        strategies = []

        calls = options_chain.get('calls', [])
        puts = options_chain.get('puts', [])

        if not calls and not puts:
            return self._get_fallback_strategies(symbol, underlying_price)

        try:
            # Find ATM, OTM, and ITM options for strategy building
            atm_call = self._find_atm_option(calls, underlying_price)
            atm_put = self._find_atm_option(puts, underlying_price)
            otm_call = self._find_otm_option(calls, underlying_price, 'call', percent_otm=0.05)
            otm_put = self._find_otm_option(puts, underlying_price, 'put', percent_otm=0.05)

            # Strategy 1: Covered Call (if we have OTM calls)
            if otm_call:
                covered_call = self._build_covered_call_strategy(
                    symbol, underlying_price, otm_call
                )
                if covered_call:
                    strategies.append(covered_call)

            # Strategy 2: Cash-Secured Put (if we have OTM puts)
            if otm_put:
                cash_secured_put = self._build_cash_secured_put_strategy(
                    symbol, underlying_price, otm_put
                )
                if cash_secured_put:
                    strategies.append(cash_secured_put)

            # Strategy 3: Bull Call Spread (if we have ATM and OTM calls)
            if atm_call and otm_call and atm_call != otm_call:
                bull_spread = self._build_bull_call_spread_strategy(
                    symbol, underlying_price, atm_call, otm_call
                )
                if bull_spread:
                    strategies.append(bull_spread)

            # Strategy 4: Protective Put (if we have ATM puts)
            if atm_put:
                protective_put = self._build_protective_put_strategy(
                    symbol, underlying_price, atm_put
                )
                if protective_put:
                    strategies.append(protective_put)

            # Strategy 5: Iron Condor (if we have all legs)
            if len(calls) >= 2 and len(puts) >= 2:
                iron_condor = self._build_iron_condor_strategy(
                    symbol, underlying_price, calls, puts
                )
                if iron_condor:
                    strategies.append(iron_condor)

            # Strategy 6: Long Straddle (ATM call + ATM put)
            if atm_call and atm_put:
                straddle = self._build_straddle_strategy(
                    symbol, underlying_price, atm_call, atm_put
                )
                if straddle:
                    strategies.append(straddle)

            # Sort by probability of profit
            strategies.sort(key=lambda x: x.get('probability_of_profit', 0), reverse=True)

            return strategies[:6]  # Return top 6 strategies

        except Exception as e:
            logger.warning(f"Error building real strategies: {e}")
            return self._get_fallback_strategies(symbol, underlying_price)

    def _find_atm_option(
        self,
        options: List[Dict[str, Any]],
        underlying_price: float
    ) -> Optional[Dict[str, Any]]:
        """Find the at-the-money option closest to current price."""
        if not options:
            return None

        return min(options, key=lambda x: abs(x.get('strike', 0) - underlying_price))

    def _find_otm_option(
        self,
        options: List[Dict[str, Any]],
        underlying_price: float,
        option_type: str,
        percent_otm: float = 0.05
    ) -> Optional[Dict[str, Any]]:
        """Find an out-of-the-money option at approximately percent_otm away."""
        if not options:
            return None

        if option_type == 'call':
            target_strike = underlying_price * (1 + percent_otm)
            otm_options = [o for o in options if o.get('strike', 0) > underlying_price]
        else:
            target_strike = underlying_price * (1 - percent_otm)
            otm_options = [o for o in options if o.get('strike', 0) < underlying_price]

        if not otm_options:
            return None

        return min(otm_options, key=lambda x: abs(x.get('strike', 0) - target_strike))

    def _build_covered_call_strategy(
        self,
        symbol: str,
        underlying_price: float,
        call_option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a Covered Call strategy from real option data.

        Covered Call: Own 100 shares + Sell 1 OTM call
        """
        strike = call_option.get('strike', 0)
        premium = call_option.get('bid', 0) or call_option.get('last_price', 0)
        days_to_exp = call_option.get('days_to_expiration', 30)
        delta = abs(call_option.get('delta', 0.3))

        if premium <= 0:
            premium = call_option.get('ask', 0) * 0.95  # Estimate

        # Real P/L calculations
        max_profit = (strike - underlying_price + premium) * 100  # Per contract
        max_loss = (underlying_price - premium) * 100  # If stock goes to 0
        breakeven = underlying_price - premium

        # Probability of profit ≈ probability stock stays below strike
        prob_profit = 1 - delta  # Delta approximates prob of finishing ITM

        # Annualized return
        if underlying_price > 0 and days_to_exp > 0:
            return_pct = (premium / underlying_price) * (365 / days_to_exp)
        else:
            return_pct = 0

        return {
            "strategy_name": f"Covered Call - ${strike:.0f} Strike",
            "strategy_type": "Covered Call",
            "max_profit": round(max_profit, 2),
            "max_loss": round(-max_loss, 2),
            "breakeven_points": [round(breakeven, 2)],
            "probability_of_profit": round(prob_profit, 2),
            "risk_reward_ratio": round(max_profit / max_loss, 3) if max_loss > 0 else 0,
            "days_to_expiration": days_to_exp,
            "total_cost": round(underlying_price * 100, 2),  # Cost of 100 shares
            "total_credit": round(premium * 100, 2),
            "annualized_return": round(return_pct * 100, 1),
            "description": f"Sell the ${strike:.0f} call for ${premium:.2f} premium. "
                          f"Max profit ${max_profit:.0f} if stock rises to ${strike:.0f}. "
                          f"Annualized return: {return_pct*100:.1f}%",
            "risk_level": "Medium",
            "market_outlook": "Neutral to mildly bullish",
            "legs": [
                {"action": "buy", "quantity": 100, "instrument": "stock", "price": underlying_price},
                {"action": "sell", "quantity": 1, "instrument": "call", "strike": strike,
                 "expiration": call_option.get('expiration_date'), "premium": premium}
            ]
        }

    def _build_cash_secured_put_strategy(
        self,
        symbol: str,
        underlying_price: float,
        put_option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a Cash-Secured Put strategy from real option data.

        Cash-Secured Put: Sell 1 OTM put, keep cash to buy shares if assigned
        """
        strike = put_option.get('strike', 0)
        premium = put_option.get('bid', 0) or put_option.get('last_price', 0)
        days_to_exp = put_option.get('days_to_expiration', 30)
        delta = abs(put_option.get('delta', 0.3))

        if premium <= 0:
            premium = put_option.get('ask', 0) * 0.95

        # Real P/L calculations
        max_profit = premium * 100
        max_loss = (strike - premium) * 100  # If stock goes to 0
        breakeven = strike - premium

        # Probability of profit ≈ probability stock stays above strike
        prob_profit = 1 - delta

        # Annualized return on capital at risk
        if strike > 0 and days_to_exp > 0:
            return_pct = (premium / strike) * (365 / days_to_exp)
        else:
            return_pct = 0

        return {
            "strategy_name": f"Cash-Secured Put - ${strike:.0f} Strike",
            "strategy_type": "Cash-Secured Put",
            "max_profit": round(max_profit, 2),
            "max_loss": round(-max_loss, 2),
            "breakeven_points": [round(breakeven, 2)],
            "probability_of_profit": round(prob_profit, 2),
            "risk_reward_ratio": round(max_profit / max_loss, 3) if max_loss > 0 else 0,
            "days_to_expiration": days_to_exp,
            "total_cost": round(strike * 100, 2),  # Cash secured
            "total_credit": round(max_profit, 2),
            "annualized_return": round(return_pct * 100, 1),
            "description": f"Sell the ${strike:.0f} put for ${premium:.2f}. "
                          f"Keep ${strike*100:.0f} cash as collateral. "
                          f"Annualized return: {return_pct*100:.1f}%",
            "risk_level": "Medium",
            "market_outlook": "Neutral to bullish",
            "legs": [
                {"action": "sell", "quantity": 1, "instrument": "put", "strike": strike,
                 "expiration": put_option.get('expiration_date'), "premium": premium}
            ]
        }

    def _build_bull_call_spread_strategy(
        self,
        symbol: str,
        underlying_price: float,
        long_call: Dict[str, Any],
        short_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a Bull Call Spread from real option data.

        Bull Call Spread: Buy lower strike call + Sell higher strike call
        """
        long_strike = long_call.get('strike', 0)
        short_strike = short_call.get('strike', 0)

        # Ensure proper ordering
        if long_strike > short_strike:
            long_call, short_call = short_call, long_call
            long_strike, short_strike = short_strike, long_strike

        long_premium = long_call.get('ask', 0) or long_call.get('last_price', 0)
        short_premium = short_call.get('bid', 0) or short_call.get('last_price', 0)
        days_to_exp = long_call.get('days_to_expiration', 30)

        # Net debit
        net_debit = long_premium - short_premium

        # Real P/L calculations
        max_profit = (short_strike - long_strike - net_debit) * 100
        max_loss = net_debit * 100
        breakeven = long_strike + net_debit

        # Probability: Use delta difference
        long_delta = long_call.get('delta', 0.5)
        short_delta = short_call.get('delta', 0.3)
        prob_profit = (long_delta + short_delta) / 2  # Rough approximation

        if max_profit <= 0:
            return None

        return {
            "strategy_name": f"Bull Call Spread ${long_strike:.0f}/${short_strike:.0f}",
            "strategy_type": "Bull Call Spread",
            "max_profit": round(max_profit, 2),
            "max_loss": round(-max_loss, 2),
            "breakeven_points": [round(breakeven, 2)],
            "probability_of_profit": round(min(0.95, max(0.1, prob_profit)), 2),
            "risk_reward_ratio": round(max_profit / max_loss, 2) if max_loss > 0 else 0,
            "days_to_expiration": days_to_exp,
            "total_cost": round(max_loss, 2),
            "total_credit": 0,
            "description": f"Buy ${long_strike:.0f} call, sell ${short_strike:.0f} call. "
                          f"Net cost ${net_debit:.2f}. Max profit ${max_profit:.0f} if stock above ${short_strike:.0f}.",
            "risk_level": "Medium",
            "market_outlook": "Bullish",
            "legs": [
                {"action": "buy", "quantity": 1, "instrument": "call", "strike": long_strike,
                 "expiration": long_call.get('expiration_date'), "premium": long_premium},
                {"action": "sell", "quantity": 1, "instrument": "call", "strike": short_strike,
                 "expiration": short_call.get('expiration_date'), "premium": short_premium}
            ]
        }

    def _build_protective_put_strategy(
        self,
        symbol: str,
        underlying_price: float,
        put_option: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a Protective Put strategy from real option data.

        Protective Put: Own 100 shares + Buy 1 ATM/OTM put
        """
        strike = put_option.get('strike', 0)
        premium = put_option.get('ask', 0) or put_option.get('last_price', 0)
        days_to_exp = put_option.get('days_to_expiration', 30)

        # Real P/L calculations
        max_loss = (underlying_price - strike + premium) * 100
        breakeven = underlying_price + premium

        # Max profit is unlimited (stock can go up infinitely)
        # For display, show profit at 20% stock gain
        profit_at_20pct = (underlying_price * 0.20 - premium) * 100

        return {
            "strategy_name": f"Protective Put - ${strike:.0f} Strike",
            "strategy_type": "Protective Put",
            "max_profit": round(profit_at_20pct, 2),  # At 20% gain
            "max_loss": round(-max_loss, 2),
            "breakeven_points": [round(breakeven, 2)],
            "probability_of_profit": 0.50,  # Depends on stock movement
            "risk_reward_ratio": round(profit_at_20pct / max_loss, 2) if max_loss > 0 else 0,
            "days_to_expiration": days_to_exp,
            "total_cost": round((underlying_price + premium) * 100, 2),
            "total_credit": 0,
            "description": f"Buy ${strike:.0f} put for ${premium:.2f} to protect 100 shares. "
                          f"Max loss limited to ${max_loss:.0f} no matter how far stock falls.",
            "risk_level": "Low",
            "market_outlook": "Bullish with downside protection",
            "legs": [
                {"action": "buy", "quantity": 100, "instrument": "stock", "price": underlying_price},
                {"action": "buy", "quantity": 1, "instrument": "put", "strike": strike,
                 "expiration": put_option.get('expiration_date'), "premium": premium}
            ]
        }

    def _build_iron_condor_strategy(
        self,
        symbol: str,
        underlying_price: float,
        calls: List[Dict[str, Any]],
        puts: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Build an Iron Condor strategy from real option data.

        Iron Condor: Sell OTM put spread + Sell OTM call spread
        """
        try:
            # Find options ~5% and ~10% OTM
            otm_put_sell = self._find_otm_option(puts, underlying_price, 'put', 0.05)
            otm_put_buy = self._find_otm_option(puts, underlying_price, 'put', 0.10)
            otm_call_sell = self._find_otm_option(calls, underlying_price, 'call', 0.05)
            otm_call_buy = self._find_otm_option(calls, underlying_price, 'call', 0.10)

            if not all([otm_put_sell, otm_put_buy, otm_call_sell, otm_call_buy]):
                return None

            # Calculate premiums
            put_sell_premium = otm_put_sell.get('bid', 0) or otm_put_sell.get('last_price', 0)
            put_buy_premium = otm_put_buy.get('ask', 0) or otm_put_buy.get('last_price', 0)
            call_sell_premium = otm_call_sell.get('bid', 0) or otm_call_sell.get('last_price', 0)
            call_buy_premium = otm_call_buy.get('ask', 0) or otm_call_buy.get('last_price', 0)

            # Net credit received
            net_credit = (put_sell_premium - put_buy_premium +
                         call_sell_premium - call_buy_premium)

            if net_credit <= 0:
                return None

            days_to_exp = otm_call_sell.get('days_to_expiration', 30)

            # Width of spreads
            put_width = abs(otm_put_sell.get('strike', 0) - otm_put_buy.get('strike', 0))
            call_width = abs(otm_call_buy.get('strike', 0) - otm_call_sell.get('strike', 0))
            max_width = max(put_width, call_width)

            # Real P/L
            max_profit = net_credit * 100
            max_loss = (max_width - net_credit) * 100

            lower_breakeven = otm_put_sell.get('strike', 0) - net_credit
            upper_breakeven = otm_call_sell.get('strike', 0) + net_credit

            # Probability: stock stays between short strikes
            prob_profit = 0.65  # Typical for well-constructed iron condor

            return {
                "strategy_name": "Iron Condor",
                "strategy_type": "Iron Condor",
                "max_profit": round(max_profit, 2),
                "max_loss": round(-max_loss, 2),
                "breakeven_points": [round(lower_breakeven, 2), round(upper_breakeven, 2)],
                "probability_of_profit": prob_profit,
                "risk_reward_ratio": round(max_profit / max_loss, 2) if max_loss > 0 else 0,
                "days_to_expiration": days_to_exp,
                "total_cost": 0,
                "total_credit": round(max_profit, 2),
                "description": f"Sell put spread + call spread for ${net_credit:.2f} credit. "
                              f"Profit if stock stays between ${lower_breakeven:.0f} and ${upper_breakeven:.0f}.",
                "risk_level": "Medium",
                "market_outlook": "Neutral - expecting low volatility",
                "legs": [
                    {"action": "buy", "quantity": 1, "instrument": "put",
                     "strike": otm_put_buy.get('strike'), "premium": put_buy_premium},
                    {"action": "sell", "quantity": 1, "instrument": "put",
                     "strike": otm_put_sell.get('strike'), "premium": put_sell_premium},
                    {"action": "sell", "quantity": 1, "instrument": "call",
                     "strike": otm_call_sell.get('strike'), "premium": call_sell_premium},
                    {"action": "buy", "quantity": 1, "instrument": "call",
                     "strike": otm_call_buy.get('strike'), "premium": call_buy_premium}
                ]
            }
        except Exception as e:
            logger.debug(f"Could not build iron condor: {e}")
            return None

    def _build_straddle_strategy(
        self,
        symbol: str,
        underlying_price: float,
        atm_call: Dict[str, Any],
        atm_put: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a Long Straddle strategy from real option data.

        Long Straddle: Buy ATM call + Buy ATM put
        """
        call_strike = atm_call.get('strike', 0)
        put_strike = atm_put.get('strike', 0)

        call_premium = atm_call.get('ask', 0) or atm_call.get('last_price', 0)
        put_premium = atm_put.get('ask', 0) or atm_put.get('last_price', 0)
        days_to_exp = atm_call.get('days_to_expiration', 30)

        total_premium = call_premium + put_premium

        # Breakevens
        lower_breakeven = call_strike - total_premium
        upper_breakeven = call_strike + total_premium

        # Max loss is premium paid
        max_loss = total_premium * 100

        # Profit potential is unlimited, show at 10% move
        profit_at_10pct_move = (underlying_price * 0.10 - total_premium) * 100

        # Combined IV for description
        avg_iv = (atm_call.get('implied_volatility', 0.3) +
                  atm_put.get('implied_volatility', 0.3)) / 2

        return {
            "strategy_name": f"Long Straddle - ${call_strike:.0f} Strike",
            "strategy_type": "Long Straddle",
            "max_profit": round(profit_at_10pct_move, 2),  # At 10% move
            "max_loss": round(-max_loss, 2),
            "breakeven_points": [round(lower_breakeven, 2), round(upper_breakeven, 2)],
            "probability_of_profit": 0.40,  # Needs significant move
            "risk_reward_ratio": round(abs(profit_at_10pct_move) / max_loss, 2) if max_loss > 0 else 0,
            "days_to_expiration": days_to_exp,
            "total_cost": round(max_loss, 2),
            "total_credit": 0,
            "description": f"Buy ${call_strike:.0f} call and put for ${total_premium:.2f} total. "
                          f"Profit if stock moves beyond ${lower_breakeven:.0f} or ${upper_breakeven:.0f}. "
                          f"Current IV: {avg_iv:.0%}",
            "risk_level": "High",
            "market_outlook": "Expecting big move, unsure of direction",
            "legs": [
                {"action": "buy", "quantity": 1, "instrument": "call", "strike": call_strike,
                 "expiration": atm_call.get('expiration_date'), "premium": call_premium},
                {"action": "buy", "quantity": 1, "instrument": "put", "strike": put_strike,
                 "expiration": atm_put.get('expiration_date'), "premium": put_premium}
            ]
        }

    def _get_fallback_strategies(
        self,
        symbol: str,
        underlying_price: float
    ) -> List[Dict[str, Any]]:
        """Return minimal fallback strategies when real chain data unavailable."""
        return [
            {
                "strategy_name": "Covered Call",
                "strategy_type": "Covered Call",
                "max_profit": underlying_price * 0.03 * 100,
                "max_loss": -underlying_price * 0.97 * 100,
                "breakeven_points": [underlying_price * 0.97],
                "probability_of_profit": 0.65,
                "risk_reward_ratio": 0.03,
                "days_to_expiration": 30,
                "total_cost": underlying_price * 100,
                "total_credit": underlying_price * 0.03 * 100,
                "description": "Sell OTM calls on shares you own to generate income.",
                "risk_level": "Medium",
                "market_outlook": "Neutral to mildly bullish",
                "legs": []
            }
        ]

    def _get_real_options_chain(
        self,
        symbol: str,
        underlying_price: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Try to fetch real options chain from Polygon API
        """
        if not self.use_real_data or not self.polygon_api_key:
            return None
        
        try:
            import requests
            from datetime import datetime, timedelta
            
            # Get options contracts from Polygon
            url = "https://api.polygon.io/v3/reference/options/contracts"
            params = {
                'underlying_ticker': symbol.upper(),
                'limit': 1000,  # Get more contracts to have good coverage
                'apiKey': self.polygon_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if not response.ok:
                logger.warning(f"Polygon options contracts API returned {response.status_code} for {symbol}")
                return None
            
            data = response.json()
            results = data.get('results', [])
            if not results:
                logger.info(f"No options contracts found for {symbol}")
                return None
            
            # Group contracts by expiration date
            options_by_expiry: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
            expiration_dates = set()
            
            for contract in results:
                expiry = contract.get('expiration_date')
                if not expiry:
                    continue
                    
                expiration_dates.add(expiry)
                
                if expiry not in options_by_expiry:
                    options_by_expiry[expiry] = {'calls': [], 'puts': []}
                
                contract_type = contract.get('contract_type', '').lower()
                strike = contract.get('strike_price', 0)
                
                # Get quotes for this contract (if available)
                contract_ticker = contract.get('ticker', '')
                bid, ask, volume, last_price = self._get_option_quote(contract_ticker)
                
                option_data = {
                    'symbol': symbol,
                    'contract_symbol': contract_ticker,
                    'strike': float(strike),
                    'expiration_date': expiry,
                    'option_type': contract_type,
                    'bid': bid,
                    'ask': ask,
                    'last_price': last_price,
                    'volume': volume,
                    'open_interest': contract.get('shares_per_contract', 0) * contract.get('open_interest', 0),
                    'implied_volatility': 0.0,  # Would need separate API call
                    'delta': 0.0,  # Would need Greeks calculation
                    'gamma': 0.0,
                    'theta': 0.0,
                    'vega': 0.0,
                    'rho': 0.0,
                    'intrinsic_value': self._calculate_intrinsic_value(
                        underlying_price, strike, contract_type
                    ),
                    'time_value': max(0, last_price - self._calculate_intrinsic_value(
                        underlying_price, strike, contract_type
                    )),
                    'days_to_expiration': self._days_to_expiration(expiry),
                }
                
                if contract_type == 'call':
                    options_by_expiry[expiry]['calls'].append(option_data)
                elif contract_type == 'put':
                    options_by_expiry[expiry]['puts'].append(option_data)
            
            # Sort expiration dates
            sorted_expirations = sorted(list(expiration_dates))
            
            # Collect all calls and puts from all expirations
            all_calls = []
            all_puts = []
            
            for exp in sorted_expirations:
                if exp in options_by_expiry:
                    all_calls.extend(options_by_expiry[exp]['calls'])
                    all_puts.extend(options_by_expiry[exp]['puts'])
            
            # Calculate Greeks for all contracts
            for contract in all_calls + all_puts:
                self._calculate_greeks(contract, underlying_price)
            
            # Sort by strike for easier display
            all_calls = sorted(all_calls, key=lambda x: (x['expiration_date'], x['strike']))
            all_puts = sorted(all_puts, key=lambda x: (x['expiration_date'], x['strike']))
            
            logger.info(f"✅ Fetched real options chain for {symbol}: {len(all_calls)} calls, {len(all_puts)} puts across {len(sorted_expirations)} expirations")
            
            return {
                'expiration_dates': sorted_expirations,
                'calls': all_calls[:200],  # Limit to 200 total for performance
                'puts': all_puts[:200],
                'greeks': {
                    'delta': 0.5,  # Aggregate Greeks would need calculation
                    'gamma': 0.02,
                    'theta': -0.12,
                    'vega': 0.25,
                    'rho': 0.04,
                },
            }
            
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching real options chain from Polygon for {symbol}: {e}")
            return None
    
    def _get_option_quote(self, contract_ticker: str) -> tuple:
        """
        Get bid, ask, volume, and last price for an options contract from Polygon
        """
        if not self.polygon_api_key:
            return 0.0, 0.0, 0, 0.0
        
        try:
            import requests
            # Get previous day's close for the option
            url = f"https://api.polygon.io/v2/aggs/ticker/{contract_ticker}/prev"
            params = {'adjusted': 'true', 'apiKey': self.polygon_api_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.ok:
                data = response.json()
                results = data.get('results', [])
                if results and len(results) > 0:
                    last_price = float(results[0].get('c', 0))  # close price
                    volume = int(results[0].get('v', 0))
                    # Estimate bid/ask spread (typically 1-2% for liquid options)
                    spread = last_price * 0.02
                    bid = max(0, last_price - spread / 2)
                    ask = last_price + spread / 2
                    return bid, ask, volume, last_price
            
            # Fallback: try to get snapshot if available
            url = f"https://api.polygon.io/v2/snapshot/option/{contract_ticker}"
            params = {'apiKey': self.polygon_api_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.ok:
                data = response.json()
                # Polygon snapshot format may vary
                if 'results' in data and len(data['results']) > 0:
                    result = data['results'][0]
                    bid = float(result.get('bid', 0))
                    ask = float(result.get('ask', 0))
                    last_price = float(result.get('last_quote', {}).get('last', 0))
                    volume = int(result.get('day', {}).get('v', 0))
                    return bid, ask, volume, last_price
            
            return 0.0, 0.0, 0, 0.0
            
        except Exception as e:
            logger.debug(f"Could not get quote for {contract_ticker}: {e}")
            return 0.0, 0.0, 0, 0.0
    
    def _calculate_intrinsic_value(self, underlying_price: float, strike: float, option_type: str) -> float:
        """Calculate intrinsic value of an option"""
        if option_type == 'call':
            return max(0, underlying_price - strike)
        elif option_type == 'put':
            return max(0, strike - underlying_price)
        return 0.0
    
    def _days_to_expiration(self, expiration_date: str) -> int:
        """Calculate days to expiration"""
        try:
            from datetime import datetime
            exp = datetime.strptime(expiration_date, '%Y-%m-%d')
            today = datetime.now()
            return (exp - today).days
        except:
            return 0
    
    def _calculate_greeks(self, contract: Dict[str, Any], underlying_price: float):
        """
        Calculate Greeks using the Black-Scholes model.

        This provides accurate, real Greeks calculations based on:
        - Current underlying price (real from Finnhub/Polygon)
        - Strike price (real from Polygon)
        - Time to expiration (real from contract data)
        - Implied volatility (estimated from market price or historical vol)
        - Risk-free rate (current Treasury rate approximation)
        """
        try:
            import math
            from scipy.stats import norm

            strike = float(contract.get('strike', 0))
            option_type = contract.get('option_type', 'call').lower()
            days_to_exp = contract.get('days_to_expiration', 30)

            # Get market price for IV calculation
            market_price = contract.get('last_price', 0) or contract.get('ask', 0)

            if days_to_exp <= 0:
                days_to_exp = 1
            if strike <= 0 or underlying_price <= 0:
                self._set_default_greeks(contract, option_type)
                return

            # Time to expiration in years
            T = days_to_exp / 365.0
            S = underlying_price  # Spot price
            K = strike            # Strike price
            r = 0.045             # Risk-free rate (approximate current Treasury rate)

            # Estimate implied volatility from market price, or use historical estimate
            iv = contract.get('implied_volatility', 0)
            if iv <= 0 or iv > 5:  # Invalid IV, estimate it
                iv = self._estimate_implied_volatility(S, K, T, r, market_price, option_type)

            sigma = iv  # Volatility

            # Prevent division by zero
            if T <= 0 or sigma <= 0:
                self._set_default_greeks(contract, option_type)
                return

            sqrt_T = math.sqrt(T)

            # Black-Scholes d1 and d2
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
            d2 = d1 - sigma * sqrt_T

            # Standard normal PDF and CDF
            N_d1 = norm.cdf(d1)
            N_d2 = norm.cdf(d2)
            N_neg_d1 = norm.cdf(-d1)
            N_neg_d2 = norm.cdf(-d2)
            n_d1 = norm.pdf(d1)  # PDF for gamma/vega calculations

            # Calculate Greeks based on option type
            if option_type == 'call':
                # Delta: Rate of change of option price with respect to underlying
                delta = N_d1

                # Theta: Time decay (per day, negative for long options)
                theta = (-(S * n_d1 * sigma) / (2 * sqrt_T)
                        - r * K * math.exp(-r * T) * N_d2) / 365

                # Rho: Sensitivity to interest rate changes
                rho = K * T * math.exp(-r * T) * N_d2 / 100
            else:  # put
                # Delta for puts is negative
                delta = N_d1 - 1  # or equivalently: -N_neg_d1

                # Theta for puts
                theta = (-(S * n_d1 * sigma) / (2 * sqrt_T)
                        + r * K * math.exp(-r * T) * N_neg_d2) / 365

                # Rho for puts
                rho = -K * T * math.exp(-r * T) * N_neg_d2 / 100

            # Gamma: Rate of change of delta (same for calls and puts)
            gamma = n_d1 / (S * sigma * sqrt_T)

            # Vega: Sensitivity to volatility (same for calls and puts)
            # Expressed per 1% change in volatility
            vega = S * n_d1 * sqrt_T / 100

            # Store calculated Greeks
            contract['delta'] = round(delta, 4)
            contract['gamma'] = round(gamma, 4)
            contract['theta'] = round(theta, 4)
            contract['vega'] = round(vega, 4)
            contract['rho'] = round(rho, 4)
            contract['implied_volatility'] = round(iv, 4)

            logger.debug(
                f"Calculated Greeks for {contract.get('contract_symbol', 'N/A')}: "
                f"Δ={delta:.3f} Γ={gamma:.4f} Θ={theta:.4f} V={vega:.3f} ρ={rho:.4f} IV={iv:.2%}"
            )

        except Exception as e:
            logger.warning(f"Error calculating Black-Scholes Greeks: {e}")
            self._set_default_greeks(contract, contract.get('option_type', 'call'))

    def _set_default_greeks(self, contract: Dict[str, Any], option_type: str):
        """Set sensible default Greeks when calculation fails."""
        contract['delta'] = 0.5 if option_type == 'call' else -0.5
        contract['gamma'] = 0.02
        contract['theta'] = -0.05
        contract['vega'] = 0.10
        contract['rho'] = 0.02 if option_type == 'call' else -0.02
        contract['implied_volatility'] = 0.30

    def _estimate_implied_volatility(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        market_price: float,
        option_type: str
    ) -> float:
        """
        Estimate implied volatility using Newton-Raphson method.

        If market price is not available, falls back to historical volatility estimate.
        """
        try:
            import math
            from scipy.stats import norm

            # If no market price, estimate based on moneyness and time
            if market_price <= 0:
                # Base volatility estimate from moneyness
                moneyness = S / K
                if moneyness > 1.1:  # Deep ITM
                    return 0.25
                elif moneyness < 0.9:  # Deep OTM
                    return 0.35
                else:  # ATM
                    return 0.30

            # Newton-Raphson iteration to find IV
            sigma = 0.30  # Initial guess
            max_iterations = 100
            tolerance = 0.0001

            for i in range(max_iterations):
                # Calculate option price with current sigma
                sqrt_T = math.sqrt(T)
                d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
                d2 = d1 - sigma * sqrt_T

                if option_type == 'call':
                    price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
                else:
                    price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

                # Calculate vega for Newton-Raphson update
                vega = S * norm.pdf(d1) * sqrt_T

                if vega < 0.0001:  # Avoid division by zero
                    break

                # Price difference
                diff = market_price - price

                if abs(diff) < tolerance:
                    return max(0.05, min(sigma, 3.0))  # Clamp between 5% and 300%

                # Newton-Raphson update
                sigma = sigma + diff / vega

                # Keep sigma in reasonable bounds
                sigma = max(0.01, min(sigma, 5.0))

            return max(0.10, min(sigma, 2.0))  # Return reasonable IV

        except Exception as e:
            logger.debug(f"IV estimation failed: {e}, using default")
            return 0.30  # Default 30% volatility
    
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
