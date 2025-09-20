"""
AI-Powered Options Recommendation Engine (cleaned)
Drop-in: safe outputs, schema-friendly, async wrapper over blocking I/O.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm

logger = logging.getLogger(__name__)


# ----------------------------- Utilities ---------------------------------- #

def _clamp(x: float, lo: float, hi: float) -> float:
    try:
        return max(lo, min(hi, float(x)))
    except Exception:
        return lo

def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default

def _sentiment_desc(sentiment: str, confidence: Optional[float]) -> str:
    base = {
        "BULLISH": "Bullish — model expects upside",
        "BEARISH": "Bearish — model expects downside",
        "NEUTRAL": "Neutral — limited directional edge",
        "PROTECTIVE": "Protective — reduce downside risk",
        "RANGE": "Range-bound — harvest theta",
    }.get((sentiment or "").upper(), "Unknown")
    if isinstance(confidence, (int, float)):
        return f"{base} (confidence {int(_clamp(confidence, 0, 1)*100)}%)"
    return base


# ------------------------------ Models ------------------------------------ #

@dataclass
class OptionsRecommendation:
    strategy_name: str
    strategy_type: str  # 'income', 'hedge', 'speculation', 'arbitrage'
    confidence_score: float  # 0..100
    symbol: str
    current_price: float
    options: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    reasoning: Dict[str, Any]
    risk_score: float  # 0..100
    expected_return: float  # ratio 0..1 per year (if annualized) or scenario value
    max_profit: float
    max_loss: float
    probability_of_profit: float  # 0..1
    days_to_expiration: int
    market_outlook: str
    created_at: str  # ISO string for JSON safety
    # computed, not stored
    @property
    def sentiment(self) -> str:
        m = (self.market_outlook or "").lower()
        if "bull" in m:
            return "BULLISH"
        if "bear" in m:
            return "BEARISH"
        if "protect" in m:
            return "PROTECTIVE"
        if "range" in m:
            return "NEUTRAL"
        return "NEUTRAL"

    def to_public_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # bounds & types for API
        d["confidence_score"] = round(_clamp(self.confidence_score, 0, 100), 1)
        d["risk_score"] = round(_clamp(self.risk_score, 0, 100), 1)
        d["probability_of_profit"] = round(_clamp(self.probability_of_profit, 0, 1), 3)
        d["expected_return"] = round(float(self.expected_return), 4)
        d["max_profit"] = round(float(self.max_profit), 2)
        d["max_loss"] = round(float(self.max_loss), 2)
        d["sentiment"] = self.sentiment
        # ensure client field exists
        d["sentimentDescription"] = _sentiment_desc(d["sentiment"], d.get("probability_of_profit"))
        return d


@dataclass
class MarketAnalysis:
    symbol: str
    current_price: float
    volatility: float
    implied_volatility: float
    volume: int
    market_cap: float
    sector: str
    sentiment_score: float  # -100..100
    trend_direction: str  # 'bullish', 'bearish', 'neutral'
    support_levels: List[float]
    resistance_levels: List[float]
    earnings_date: Optional[str]
    dividend_yield: float
    beta: float


# ------------------------------ Engine ------------------------------------ #

class AIOptionsEngine:
    def __init__(self) -> None:
        self.risk_free_rate = 0.05  # 5%
        self.volatility_lookback = 30

    # ---------- Public API ---------- #

    async def generate_recommendations(
        self,
        symbol: str,
        user_risk_tolerance: str = "medium",
        portfolio_value: float = 10_000,
        time_horizon: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Return a list of up to 5 recommendations (dicts ready for JSON).
        """
        try:
            logger.info("AIOptionsEngine: start for %s", symbol)

            ma = await self._analyze_market(symbol)
            chain = await self._get_options_data(symbol)

            recs: List[OptionsRecommendation] = []

            # Always produce a baseline set
            tasks = [
                self._create_covered_call_strategy(symbol, ma, chain, portfolio_value, time_horizon),
                self._create_cash_secured_put_strategy(symbol, ma, chain, portfolio_value, time_horizon),
                self._create_protective_put_strategy(symbol, ma, chain, portfolio_value, time_horizon),
                self._create_iron_condor_strategy(symbol, ma, chain, portfolio_value, time_horizon),
                self._create_long_call_strategy(symbol, ma, chain, portfolio_value, time_horizon),
            ]
            baseline = await asyncio.gather(*tasks)
            recs.extend([r for r in baseline if r])

            # Simple gating for advanced sets
            if ma.current_price != 100.0:
                adv_tasks = [
                    self._create_collar_strategy(symbol, ma, chain, portfolio_value, time_horizon),
                    self._create_calendar_spread_strategy(symbol, ma, chain, portfolio_value, time_horizon),
                    self._create_volatility_arbitrage_strategy(symbol, ma, chain, portfolio_value, time_horizon),
                ]
                more = await asyncio.gather(*adv_tasks)
                recs.extend([r for r in more if r])

            recs = self._rank_recommendations(recs, user_risk_tolerance, portfolio_value)[:5]
            return [r.to_public_dict() for r in recs]
        except Exception as e:
            logger.exception("AIOptionsEngine failure: %s", e)
            return []

    # ---------- Data ---------- #

    async def _analyze_market(self, symbol: str) -> MarketAnalysis:
        def _blocking_fetch() -> MarketAnalysis:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1y")
                if hist is None or hist.empty:
                    raise RuntimeError("empty history")

                info = stock.info or {}
                px = float(hist["Close"].iloc[-1])
                vol = float(hist["Close"].pct_change().std() * np.sqrt(252))
                vol = vol if np.isfinite(vol) and vol > 0 else 0.2

                support = self._support_resistance(hist["Close"], is_res=False)
                resist = self._support_resistance(hist["Close"], is_res=True)

                sent = self._sentiment(hist)
                trend = self._trend(hist["Close"])

                ed = info.get("earningsDate")
                if isinstance(ed, (list, tuple)) and ed:
                    ed = int(ed[0])
                if isinstance(ed, (int, float)):
                    ed_iso = datetime.utcfromtimestamp(ed).isoformat() + "Z"
                else:
                    ed_iso = None

                return MarketAnalysis(
                    symbol=symbol,
                    current_price=px,
                    volatility=vol,
                    implied_volatility=vol * 1.2,
                    volume=int(_safe_float(hist["Volume"].iloc[-1], 0)),
                    market_cap=float(info.get("marketCap") or 0),
                    sector=str(info.get("sector") or "Unknown"),
                    sentiment_score=float(sent),
                    trend_direction=trend,
                    support_levels=[round(float(x), 2) for x in support],
                    resistance_levels=[round(float(x), 2) for x in resist],
                    earnings_date=ed_iso,
                    dividend_yield=float(info.get("dividendYield") or 0.0),
                    beta=float(info.get("beta") or 1.0),
                )
            except Exception as e:
                logger.warning("Market analysis fallback for %s: %s", symbol, e)
                return MarketAnalysis(
                    symbol=symbol,
                    current_price=100.0,
                    volatility=0.2,
                    implied_volatility=0.25,
                    volume=1_000_000,
                    market_cap=1_000_000_000,
                    sector="Unknown",
                    sentiment_score=0.0,
                    trend_direction="neutral",
                    support_levels=[],
                    resistance_levels=[],
                    earnings_date=None,
                    dividend_yield=0.0,
                    beta=1.0,
                )

        return await asyncio.to_thread(_blocking_fetch)

    async def _get_options_data(self, symbol: str) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        def _blocking_chain() -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
            out: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
            try:
                t = yf.Ticker(symbol)
                expirations = list(t.options or [])[:3]
                for exp in expirations:
                    try:
                        chain = t.option_chain(exp)
                        out[exp] = {
                            "calls": chain.calls.to_dict("records"),
                            "puts": chain.puts.to_dict("records"),
                        }
                    except Exception as e:
                        logger.debug("chain error %s %s", exp, e)
                return out
            except Exception as e:
                logger.warning("options data fallback for %s: %s", symbol, e)
                return {}
        return await asyncio.to_thread(_blocking_chain)

    # ---------- Ranking ---------- #

    def _rank_recommendations(
        self,
        recs: List[OptionsRecommendation],
        risk_tolerance: str,
        portfolio_value: float,
    ) -> List[OptionsRecommendation]:
        def score(r: OptionsRecommendation) -> float:
            base = _clamp(r.confidence_score, 0, 100)
            # portfolio tilt
            size_bonus = 10 if portfolio_value >= 100_000 else (5 if portfolio_value >= 50_000 else 0)
            # risk penalty
            risk_pen = 0
            if risk_tolerance == "low" and r.risk_score > 50:
                risk_pen = 20
            elif risk_tolerance == "medium" and r.risk_score > 80:
                risk_pen = 10
            # return & PoP bonuses
            ret_bonus = _clamp(r.expected_return * 100, 0, 20)  # cap
            pop_bonus = _clamp(r.probability_of_profit * 100 * 0.2, 0, 20)
            return float(_clamp(base - risk_pen + size_bonus + ret_bonus + pop_bonus, 0, 100))

        for r in recs:
            r.confidence_score = score(r)
        return sorted(recs, key=lambda x: x.confidence_score, reverse=True)

    # ---------- Strategies (kept simple & safe) ---------- #

    async def _create_covered_call_strategy(
        self, symbol: str, ma: MarketAnalysis, chain: Dict[str, Any], portfolio_value: float, horizon: int
    ) -> Optional[OptionsRecommendation]:
        try:
            best = None
            best_s = -1.0
            for exp, data in (chain or {}).items():
                for c in data.get("calls", []):
                    strike = _safe_float(c.get("strike"))
                    bid = _safe_float(c.get("bid"))
                    ask = _safe_float(c.get("ask"))
                    if strike <= 0 or (bid <= 0 and ask <= 0):
                        continue
                    mid = (bid + ask) / 2 if (bid > 0 and ask > 0) else max(bid, ask)
                    dte = self._days_to_exp(exp)
                    if dte < 7 or dte > 60:
                        continue
                    pop = self._prob_profit(ma.current_price, strike, ma.volatility, dte, kind="call")
                    ann = (mid / max(ma.current_price, 1e-6)) * (365 / max(dte, 1))
                    s = (pop * 0.4 + ann * 0.6) * 100
                    if s > best_s:
                        best_s = s
                        best = dict(strike=strike, premium=mid, expiration=exp, dte=dte, pop=pop, ann=ann)

            if not best:
                # conservative baseline
                return OptionsRecommendation(
                    strategy_name="Covered Call",
                    strategy_type="income",
                    confidence_score=60,
                    symbol=symbol,
                    current_price=ma.current_price,
                    options=[],
                    analytics=dict(max_profit=200.0, max_loss=0.0, probability_of_profit=0.7, expected_return=0.10),
                    reasoning=dict(
                        market_outlook=f"Neutral outlook for {symbol}",
                        strategy_rationale="Sell call option to generate income",
                        risk_factors=["Stock could be called away", "Limited upside"],
                        key_benefits=["Generate income", "Reduce cost basis"],
                    ),
                    risk_score=30,
                    expected_return=0.10,
                    max_profit=200.0,
                    max_loss=0.0,
                    probability_of_profit=0.7,
                    days_to_expiration=30,
                    market_outlook="neutral",
                    created_at=_now_iso(),
                )

            shares = 100
            max_profit = best["premium"] * shares
            max_loss = max(ma.current_price - best["strike"], 0) * shares
            return OptionsRecommendation(
                strategy_name="Covered Call",
                strategy_type="income",
                confidence_score=float(best_s),
                symbol=symbol,
                current_price=ma.current_price,
                options=[
                    dict(type="call", action="sell", strike=best["strike"], expiration=best["expiration"], premium=best["premium"], quantity=shares)
                ],
                analytics=dict(
                    max_profit=max_profit,
                    max_loss=max_loss,
                    probability_of_profit=float(best["pop"]),
                    expected_return=float(best["ann"]),
                    breakeven=ma.current_price - best["premium"],
                ),
                reasoning=dict(
                    market_outlook=f"Neutral to slightly bullish outlook for {symbol}",
                    strategy_rationale=f"Sell call at ${best['strike']:.2f} for ${best['premium']:.2f} premium",
                    risk_factors=["Stock could be called away", "Limited upside potential"],
                    key_benefits=["Generate income", "Reduce cost basis", "High probability of profit"],
                ),
                risk_score=30,
                expected_return=float(best["ann"]),
                max_profit=float(max_profit),
                max_loss=float(max_loss),
                probability_of_profit=float(best["pop"]),
                days_to_expiration=int(best["dte"]),
                market_outlook="neutral",
                created_at=_now_iso(),
            )
        except Exception as e:
            logger.debug("covered call error: %s", e)
            return None

    async def _create_cash_secured_put_strategy(self, symbol: str, ma: MarketAnalysis, *_args) -> Optional[OptionsRecommendation]:
        try:
            return OptionsRecommendation(
                strategy_name="Cash-Secured Put",
                strategy_type="income",
                confidence_score=75,
                symbol=symbol,
                current_price=ma.current_price,
                options=[],
                analytics=dict(max_profit=200.0, max_loss=1000.0, probability_of_profit=0.7, expected_return=0.12),
                reasoning=dict(
                    market_outlook=f"Neutral to slightly bearish outlook for {symbol}",
                    strategy_rationale="Sell put option to generate income",
                    risk_factors=["Stock assignment risk", "Limited upside"],
                    key_benefits=["Generate income", "Buy stock at discount"],
                ),
                risk_score=40,
                expected_return=0.12,
                max_profit=200.0,
                max_loss=1000.0,
                probability_of_profit=0.7,
                days_to_expiration=30,
                market_outlook="neutral",
                created_at=_now_iso(),
            )
        except Exception:
            return None

    async def _create_protective_put_strategy(self, symbol: str, ma: MarketAnalysis, *_args) -> Optional[OptionsRecommendation]:
        try:
            px = ma.current_price
            return OptionsRecommendation(
                strategy_name="Protective Put",
                strategy_type="hedge",
                confidence_score=80,
                symbol=symbol,
                current_price=px,
                options=[],
                analytics=dict(max_profit=px * 0.15, max_loss=px * 0.03, probability_of_profit=0.5, expected_return=-0.03),
                reasoning=dict(
                    market_outlook=f"Protective strategy for {symbol}",
                    strategy_rationale="Buy put option for downside protection",
                    risk_factors=["Cost of protection", "Time decay"],
                    key_benefits=["Downside protection", "Keep upside potential"],
                ),
                risk_score=20,
                expected_return=-0.03,
                max_profit=px * 0.15,
                max_loss=px * 0.03,
                probability_of_profit=0.5,
                days_to_expiration=30,
                market_outlook="protective",
                created_at=_now_iso(),
            )
        except Exception:
            return None

    async def _create_iron_condor_strategy(self, symbol: str, ma: MarketAnalysis, *_args) -> Optional[OptionsRecommendation]:
        try:
            return OptionsRecommendation(
                strategy_name="Iron Condor",
                strategy_type="income",
                confidence_score=70,
                symbol=symbol,
                current_price=ma.current_price,
                options=[],
                analytics=dict(max_profit=400.0, max_loss=600.0, probability_of_profit=0.65, expected_return=0.15),
                reasoning=dict(
                    market_outlook=f"Range-bound outlook for {symbol}",
                    strategy_rationale="Sell call and put spreads for income",
                    risk_factors=["Limited profit", "Assignment risk"],
                    key_benefits=["Generate income", "Limited risk", "High probability"],
                ),
                risk_score=45,
                expected_return=0.15,
                max_profit=400.0,
                max_loss=600.0,
                probability_of_profit=0.65,
                days_to_expiration=30,
                market_outlook="range-bound",
                created_at=_now_iso(),
            )
        except Exception:
            return None

    async def _create_long_call_strategy(self, symbol: str, ma: MarketAnalysis, *_args) -> Optional[OptionsRecommendation]:
        try:
            px = ma.current_price
            return OptionsRecommendation(
                strategy_name="Long Call",
                strategy_type="speculation",
                confidence_score=60,
                symbol=symbol,
                current_price=px,
                options=[],
                analytics=dict(max_profit=px * 0.30, max_loss=px * 0.03, probability_of_profit=0.4, expected_return=0.20),
                reasoning=dict(
                    market_outlook=f"Bullish outlook for {symbol}",
                    strategy_rationale="Buy call option for upside exposure",
                    risk_factors=["Time decay", "High cost", "Needs upward move"],
                    key_benefits=["Unlimited upside", "Leverage", "Limited risk"],
                ),
                risk_score=70,
                expected_return=0.20,
                max_profit=px * 0.30,
                max_loss=px * 0.03,
                probability_of_profit=0.4,
                days_to_expiration=30,
                market_outlook="bullish",
                created_at=_now_iso(),
            )
        except Exception:
            return None

    async def _create_collar_strategy(self, symbol: str, ma: MarketAnalysis, *_args) -> Optional[OptionsRecommendation]:
        try:
            return OptionsRecommendation(
                strategy_name="Collar",
                strategy_type="hedge",
                confidence_score=75,
                symbol=symbol,
                current_price=ma.current_price,
                options=[],
                analytics=dict(max_profit=500.0, max_loss=200.0, probability_of_profit=0.8, expected_return=0.05),
                reasoning=dict(
                    market_outlook=f"Conservative strategy for {symbol}",
                    strategy_rationale="Buy put protection, sell call for income",
                    risk_factors=["Limited upside", "Assignment risk"],
                    key_benefits=["Downside protection", "Generate income", "Low cost"],
                ),
                risk_score=25,
                expected_return=0.05,
                max_profit=500.0,
                max_loss=200.0,
                probability_of_profit=0.8,
                days_to_expiration=30,
                market_outlook="conservative",
                created_at=_now_iso(),
            )
        except Exception:
            return None

    async def _create_calendar_spread_strategy(self, symbol: str, ma: MarketAnalysis, *_args) -> Optional[OptionsRecommendation]:
        try:
            return OptionsRecommendation(
                strategy_name="Calendar Spread",
                strategy_type="arbitrage",
                confidence_score=60,
                symbol=symbol,
                current_price=ma.current_price,
                options=[],
                analytics=dict(max_profit=300.0, max_loss=200.0, probability_of_profit=0.6, expected_return=0.10),
                reasoning=dict(
                    market_outlook=f"Neutral outlook for {symbol}",
                    strategy_rationale="Sell short-term, buy long-term option",
                    risk_factors=["Complex strategy", "Time decay risk"],
                    key_benefits=["Profit from time decay", "Limited risk"],
                ),
                risk_score=50,
                expected_return=0.10,
                max_profit=300.0,
                max_loss=200.0,
                probability_of_profit=0.6,
                days_to_expiration=30,
                market_outlook="neutral",
                created_at=_now_iso(),
            )
        except Exception:
            return None

    async def _create_volatility_arbitrage_strategy(self, symbol: str, ma: MarketAnalysis, *_args) -> Optional[OptionsRecommendation]:
        try:
            return OptionsRecommendation(
                strategy_name="Volatility Arbitrage",
                strategy_type="arbitrage",
                confidence_score=55,
                symbol=symbol,
                current_price=ma.current_price,
                options=[],
                analytics=dict(max_profit=200.0, max_loss=150.0, probability_of_profit=0.55, expected_return=0.08),
                reasoning=dict(
                    market_outlook=f"Volatility mispricing opportunity for {symbol}",
                    strategy_rationale="Exploit volatility mispricing between options",
                    risk_factors=["Complex strategy", "Model risk", "Market timing"],
                    key_benefits=["Market neutral", "Consistent returns", "Low correlation"],
                ),
                risk_score=60,
                expected_return=0.08,
                max_profit=200.0,
                max_loss=150.0,
                probability_of_profit=0.55,
                days_to_expiration=30,
                market_outlook="volatile",
                created_at=_now_iso(),
            )
        except Exception:
            return None

    # ---------- Math / Tech ---------- #

    def _support_resistance(self, prices: pd.Series, is_res: bool) -> List[float]:
        try:
            highs = prices.rolling(20).max()
            lows = prices.rolling(20).min()
            vals: List[float] = []
            if is_res:
                for i in range(20, len(highs) - 20):
                    if highs.iloc[i] == highs.iloc[i - 20 : i + 20].max():
                        vals.append(float(highs.iloc[i]))
                return sorted(set(vals), reverse=True)[:3]
            else:
                for i in range(20, len(lows) - 20):
                    if lows.iloc[i] == lows.iloc[i - 20 : i + 20].min():
                        vals.append(float(lows.iloc[i]))
                return sorted(set(vals))[:3]
        except Exception:
            return []

    def _sentiment(self, hist: pd.DataFrame) -> float:
        try:
            rets = hist["Close"].pct_change().dropna()
            recent = rets.tail(10).mean()
            vol = rets.std()
            if not np.isfinite(vol) or vol == 0:
                return 0.0
            score = (recent / vol) * 50.0  # scale
            return float(_clamp(score, -100, 100))
        except Exception:
            return 0.0

    def _trend(self, prices: pd.Series) -> str:
        try:
            sma20 = float(prices.rolling(20).mean().iloc[-1])
            sma50 = float(prices.rolling(50).mean().iloc[-1])
            px = float(prices.iloc[-1])
            if px > sma20 > sma50:
                return "bullish"
            if px < sma20 < sma50:
                return "bearish"
            return "neutral"
        except Exception:
            return "neutral"

    def _days_to_exp(self, exp: str) -> int:
        try:
            return max((datetime.fromisoformat(exp) - datetime.utcnow()).days, 0)
        except Exception:
            return 30

    def _prob_profit(self, s0: float, k: float, vol: float, dte: int, kind: str = "call") -> float:
        """Risk-neutral probability S_T > K (call) or < K (put). Uses N(d2)."""
        try:
            if dte <= 0 or vol <= 0 or s0 <= 0 or k <= 0:
                return 0.5
            t = dte / 365.0
            d1 = (np.log(s0 / k) + (self.risk_free_rate + 0.5 * vol ** 2) * t) / (vol * np.sqrt(t))
            d2 = d1 - vol * np.sqrt(t)
            p_call_itm = float(norm.cdf(d2))
            if kind == "call":
                return _clamp(p_call_itm, 0.0, 1.0)
            return _clamp(1.0 - p_call_itm, 0.0, 1.0)
        except Exception:
            return 0.5


__all__ = ["AIOptionsEngine", "OptionsRecommendation", "MarketAnalysis"]