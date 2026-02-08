from __future__ import annotations

import os

os.environ.setdefault("YFINANCE_CACHE_DISABLE", "1")  # disable yfinance cache

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


OptionSide = Literal["call", "put"]
TradeDirection = Literal["buy", "sell"]
Sentiment = Literal["bullish", "bearish", "neutral"]


@dataclass
class OptionsRecommendation:
    """
    A single options trading recommendation.

    This is intentionally generic so you can wire it to whatever GraphQL
    type / serializer you already have.
    """

    symbol: str
    side: OptionSide  # "call" or "put"
    direction: TradeDirection  # "buy" or "sell"
    strike: float
    expiry: str  # ISO date string, e.g. "2025-01-17"
    confidence: float  # 0.0 – 1.0
    rationale: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    timeframe_days: Optional[int] = None


@dataclass
class MarketAnalysis:
    """
    Aggregated view of the underlying market conditions for a symbol.
    """

    symbol: str
    sentiment: Sentiment
    volatility: float  # e.g. annualized implied volatility
    trend_score: float  # -1.0 (strong down) → +1.0 (strong up)
    liquidity_score: float  # 0.0 – 1.0
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    notes: Optional[str] = None


class AIOptionsEngine:
    """
    High-level facade for generating options recommendations from
    market data + (optionally) an ML model.

    Uses a heuristic baseline (RSI, MACD, IV) for market analysis and
    near-the-money option selection. Accepts an optional ML model via
    the constructor for confidence scoring upgrades.
    """

    def __init__(
        self,
        model: Any = None,
        min_confidence: float = 0.45,
        max_recommendations: int = 5,
    ) -> None:
        self.model = model
        self.min_confidence = min_confidence
        self.max_recommendations = max_recommendations

    # ---------------------------------------------------------------------
    # Public entrypoint
    # ---------------------------------------------------------------------
    def generate_recommendations(
        self,
        symbol: str,
        spot_price: float,
        options_chain: List[Dict[str, Any]],
        indicators: Dict[str, float],
        news_sentiment: Optional[Sentiment] = None,
    ) -> List[OptionsRecommendation]:
        """
        Main method used by the rest of the app / GraphQL layer.

        :param symbol: The underlying ticker (e.g. "TSLA")
        :param spot_price: Current price of the underlying.
        :param options_chain: List of raw option data dicts from your data provider.
        :param indicators: TA metrics (RSI, MACD, etc.).
        :param news_sentiment: Optional aggregated news sentiment.
        """
        try:
            analysis = self._analyze_market(
                symbol=symbol,
                spot_price=spot_price,
                indicators=indicators,
                news_sentiment=news_sentiment,
            )

            recommendations = self._build_recommendations_from_chain(
                analysis=analysis,
                options_chain=options_chain,
            )

            # Enforce confidence + count limits
            filtered = [r for r in recommendations if r.confidence >= self.min_confidence]
            filtered.sort(key=lambda r: r.confidence, reverse=True)
            return filtered[: self.max_recommendations]

        except Exception:
            logger.exception("AIOptionsEngine.generate_recommendations failed")
            # Fail closed: no recs is safer than broken recs
            return []

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _analyze_market(
        self,
        symbol: str,
        spot_price: float,
        indicators: Dict[str, float],
        news_sentiment: Optional[Sentiment] = None,
    ) -> MarketAnalysis:
        """
        Build a simplified MarketAnalysis object using indicators and (optionally)
        an ML model. Replace the heuristics here with your real pipeline.
        """
        # --- Simple heuristic baseline (safe to run without a model) ----
        rsi = indicators.get("rsi", 50.0)
        macd = indicators.get("macd", 0.0)
        iv = indicators.get("implied_volatility", 0.3)

        # Trend score: crude combo of MACD + RSI deviation from 50
        trend_score = max(-1.0, min(1.0, (macd / 5.0) + (rsi - 50.0) / 50.0))

        # Liquidity heuristic (you can later base this on open interest / volume)
        liquidity_score = indicators.get("liquidity_score", 0.7)

        sentiment = self._derive_sentiment(
            trend_score=trend_score,
            news_sentiment=news_sentiment,
        )

        return MarketAnalysis(
            symbol=symbol,
            sentiment=sentiment,
            volatility=iv,
            trend_score=trend_score,
            liquidity_score=liquidity_score,
            support_level=indicators.get("support"),
            resistance_level=indicators.get("resistance"),
            notes=None,
        )

    def _derive_sentiment(
        self,
        trend_score: float,
        news_sentiment: Optional[Sentiment] = None,
    ) -> Sentiment:
        """
        Combine price/indicator signal + news sentiment into a simple label.
        """
        if news_sentiment is not None:
            # Nudge toward news sentiment if trend_score is not strongly opposite
            if trend_score > -0.25 and news_sentiment == "bullish":
                return "bullish"
            if trend_score < 0.25 and news_sentiment == "bearish":
                return "bearish"

        if trend_score > 0.2:
            return "bullish"
        if trend_score < -0.2:
            return "bearish"
        return "neutral"

    def _build_recommendations_from_chain(
        self,
        analysis: MarketAnalysis,
        options_chain: List[Dict[str, Any]],
    ) -> List[OptionsRecommendation]:
        """
        Transform a raw options chain into structured recommendations.

        This is a very conservative baseline:
        - Bullish → calls near-the-money
        - Bearish → puts near-the-money
        - Neutral → no recommendation (you can later add spreads/straddles)
        """
        if analysis.sentiment == "neutral":
            return []

        desired_side: OptionSide = "call" if analysis.sentiment == "bullish" else "put"

        # Filter chain to the relevant side + reasonable expiries
        filtered = [o for o in options_chain if o.get("type") in (desired_side, desired_side.upper())]

        # Sort by closest-to-money
        def _moneyness(option: Dict[str, Any]) -> float:
            try:
                strike = float(option.get("strike"))
                underlying = float(option.get("underlying_price", 0.0))
            except (TypeError, ValueError):
                return float("inf")
            if underlying <= 0:
                return float("inf")
            return abs(strike - underlying)

        filtered.sort(key=_moneyness)

        recommendations: List[OptionsRecommendation] = []
        for raw in filtered[: self.max_recommendations * 2]:
            try:
                rec = self._build_single_recommendation(
                    analysis=analysis,
                    raw_option=raw,
                )
                recommendations.append(rec)
            except Exception:
                logger.exception("Failed to build recommendation for option: %s", raw)
                continue

        return recommendations

    def _build_single_recommendation(
        self,
        analysis: MarketAnalysis,
        raw_option: Dict[str, Any],
    ) -> OptionsRecommendation:
        """
        Convert a single raw option dict into an OptionsRecommendation.
        """
        symbol = raw_option.get("symbol") or raw_option.get("underlying") or analysis.symbol
        side_raw = str(raw_option.get("type", "")).lower()
        side: OptionSide = "call" if side_raw == "call" else "put"

        strike = float(raw_option.get("strike"))
        expiry = str(raw_option.get("expiry"))
        mark_price = float(raw_option.get("mark_price", raw_option.get("last_price", 0.0)))

        # Super simple confidence heuristic – replace with model score later
        base_conf = 0.5 + (analysis.trend_score * 0.3)
        if analysis.sentiment == "bullish" and side == "call":
            base_conf += 0.1
        if analysis.sentiment == "bearish" and side == "put":
            base_conf += 0.1
        confidence = max(0.0, min(1.0, base_conf))

        rationale_parts = [
            f"Market sentiment: {analysis.sentiment}",
            f"Trend score: {analysis.trend_score:.2f}",
            f"Volatility: {analysis.volatility:.2f}",
        ]
        if analysis.support_level is not None:
            rationale_parts.append(f"Support near {analysis.support_level}")
        if analysis.resistance_level is not None:
            rationale_parts.append(f"Resistance near {analysis.resistance_level}")

        rationale = "; ".join(rationale_parts)

        # Optional: naive target/stop based on mark_price
        target_price = mark_price * (1.3 if analysis.sentiment == "bullish" else 1.25)
        stop_loss = mark_price * 0.6

        return OptionsRecommendation(
            symbol=symbol,
            side=side,
            direction="buy",
            strike=strike,
            expiry=expiry,
            confidence=confidence,
            rationale=rationale,
            target_price=round(target_price, 2),
            stop_loss=round(stop_loss, 2),
            timeframe_days=None,
        )

    # ---------------------------------------------------------------------
    # Compatibility layer for existing API
    # ---------------------------------------------------------------------
    async def generate_recommendations_legacy(
        self,
        symbol: str,
        user_risk_tolerance: str = "medium",
        portfolio_value: float = 10000,
        time_horizon: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Legacy API compatibility method.
        Maintains the old API signature while using the new engine internally.
        
        Returns a list of recommendation dicts in the old format.
        """
        # Initialize fallback values
        spot_price = 150.0
        iv = 0.3
        options_chain = []
        
        try:
            # Fetch market data (simplified - you may want to use your existing market data service)
            import yfinance as yf
            
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1mo")
                info = stock.info
                
                if hist.empty:
                    logger.warning(f"No data for {symbol}, using fallback")
                else:
                    spot_price = float(hist['Close'].iloc[-1])
                    iv = info.get('impliedVolatility', 0.3) or 0.3
                    
                    # Get options chain
                    try:
                        expirations = stock.options[:3] if stock.options else []
                        options_chain = []
                        for exp in expirations:
                            opt_chain = stock.option_chain(exp)
                            for call in opt_chain.calls.head(5).itertuples():
                                options_chain.append({
                                    'type': 'call',
                                    'strike': float(call.strike),
                                    'expiry': exp,
                                    'mark_price': float(call.lastPrice) if call.lastPrice else float(call.bid + call.ask) / 2,
                                    'underlying_price': spot_price,
                                })
                            for put in opt_chain.puts.head(5).itertuples():
                                options_chain.append({
                                    'type': 'put',
                                    'strike': float(put.strike),
                                    'expiry': exp,
                                    'mark_price': float(put.lastPrice) if put.lastPrice else float(put.bid + put.ask) / 2,
                                    'underlying_price': spot_price,
                                })
                    except Exception as e:
                        logger.warning(f"Could not fetch options chain: {e}")
                        options_chain = []
            except Exception as e:
                logger.error(f"Error fetching market data for {symbol}: {e}")
                # Fallback values already set above
            
            # Calculate indicators from historical data
            rsi = 50.0
            macd = 0.0
            support = spot_price * 0.9
            resistance = spot_price * 1.1
            try:
                if not hist.empty and len(hist) >= 14:
                    closes = hist['Close'].values
                    # RSI (Wilder's smoothing, 14-period)
                    deltas = np.diff(closes)
                    gains = np.where(deltas > 0, deltas, 0.0)
                    losses = np.where(deltas < 0, -deltas, 0.0)
                    avg_gain = np.mean(gains[-14:])
                    avg_loss = np.mean(losses[-14:])
                    if avg_loss > 0:
                        rs = avg_gain / avg_loss
                        rsi = 100.0 - (100.0 / (1.0 + rs))
                    else:
                        rsi = 100.0 if avg_gain > 0 else 50.0

                    # MACD (12/26 EMA difference)
                    if len(closes) >= 26:
                        ema12 = pd.Series(closes).ewm(span=12, adjust=False).mean().iloc[-1]
                        ema26 = pd.Series(closes).ewm(span=26, adjust=False).mean().iloc[-1]
                        macd = float(ema12 - ema26)

                    # Support/Resistance from recent highs/lows
                    if 'Low' in hist.columns and 'High' in hist.columns:
                        support = float(hist['Low'].rolling(20).min().iloc[-1])
                        resistance = float(hist['High'].rolling(20).max().iloc[-1])
            except Exception as ind_err:
                logger.debug(f"Indicator calculation error, using defaults: {ind_err}")

            # Build indicators dict
            indicators = {
                'rsi': rsi,
                'macd': macd,
                'implied_volatility': iv,
                'support': support,
                'resistance': resistance,
                'liquidity_score': 0.7,
            }
            
            # Generate recommendations using new API
            recommendations = self.generate_recommendations(
                symbol=symbol,
                spot_price=spot_price,
                options_chain=options_chain,
                indicators=indicators,
                news_sentiment=None,
            )
            
            # Transform to legacy format
            legacy_recs = []
            for rec in recommendations:
                # Map confidence from 0-1 to 0-100
                confidence_score = rec.confidence * 100
                
                # Determine strategy type from side
                strategy_type = "speculation"  # default
                if rec.side == "call":
                    strategy_type = "speculation" if user_risk_tolerance in ["medium", "high"] else "income"
                else:
                    strategy_type = "hedge" if user_risk_tolerance == "low" else "speculation"
                
                legacy_rec = {
                    'strategy_name': f"{rec.side.capitalize()} Option",
                    'strategy_type': strategy_type,
                    'confidence_score': confidence_score,
                    'symbol': rec.symbol,
                    'current_price': spot_price,
                    'options': [{
                        'type': rec.side,
                        'action': rec.direction,
                        'strike': rec.strike,
                        'expiration': rec.expiry,
                        'premium': rec.target_price or 0,
                        'quantity': 1,
                    }],
                    'analytics': {
                        'max_profit': rec.target_price or spot_price * 0.2,
                        'max_loss': rec.stop_loss or spot_price * 0.1,
                        'probability_of_profit': rec.confidence,
                        'expected_return': rec.confidence * 0.15,  # Estimate
                        'breakeven': rec.strike,
                    },
                    'reasoning': {
                        'market_outlook': rec.rationale,
                        'strategy_rationale': f"{rec.side.capitalize()} option based on market analysis",
                        'risk_factors': ['Market volatility', 'Time decay'],
                        'key_benefits': ['Leveraged exposure', 'Limited risk'],
                    },
                    'risk_score': (1 - rec.confidence) * 100,
                    'expected_return': rec.confidence * 0.15,
                    'max_profit': rec.target_price or spot_price * 0.2,
                    'max_loss': rec.stop_loss or spot_price * 0.1,
                    'probability_of_profit': rec.confidence,
                    'days_to_expiration': rec.timeframe_days or time_horizon,
                    'market_outlook': 'neutral',
                    'created_at': datetime.now(),
                }
                legacy_recs.append(legacy_rec)
            
            logger.info("LEGACY ENGINE: built %d recommendations", len(legacy_recs))
            
            # If nothing made it through, build a simple fallback so the UI isn't empty
            if not legacy_recs:
                logger.warning(
                    "LEGACY ENGINE: no recommendations built, creating fallback recommendation"
                )
                legacy_recs = [
                    {
                        "strategy_name": "Basic Call Idea",
                        "strategy_type": "speculation",
                        "confidence_score": 55.0,
                        "symbol": symbol,
                        "current_price": float(spot_price),
                        "options": [],
                        "analytics": {},
                        "reasoning": {
                            "summary": "Fallback recommendation generated when AI engine returned no ideas."
                        },
                        "risk_score": 50.0,
                        "expected_return": 0.05,
                        "max_profit": 0.0,
                        "max_loss": 0.01 * portfolio_value if 'portfolio_value' in locals() else 100.0,
                        "probability_of_profit": 0.5,
                        "days_to_expiration": time_horizon if 'time_horizon' in locals() else 30,
                        "market_outlook": "neutral",
                        "created_at": datetime.now(),
                    }
                ]
            
            return legacy_recs
            
        except Exception as e:
            logger.exception(f"Error in generate_recommendations_legacy: {e}")
            # Even on exception, return a fallback so UI doesn't break
            return [
                {
                    "strategy_name": "Error Fallback",
                    "strategy_type": "speculation",
                    "confidence_score": 50.0,
                    "symbol": symbol if 'symbol' in locals() else "UNKNOWN",
                    "current_price": 100.0,
                    "options": [],
                    "analytics": {},
                    "reasoning": {
                        "summary": f"Error occurred: {str(e)}. This is a fallback recommendation."
                    },
                    "risk_score": 50.0,
                    "expected_return": 0.0,
                    "max_profit": 0.0,
                    "max_loss": 0.0,
                    "probability_of_profit": 0.5,
                    "days_to_expiration": 30,
                    "market_outlook": "neutral",
                    "created_at": datetime.now(),
                }
            ]
