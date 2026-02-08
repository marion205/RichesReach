"""
Options Strategy Router: Multi-Factor Scoring & Candidate Selection

The Strategy Router is the "General Manager" of the options system. It:
1. Takes the regime classification from RegimeDetector
2. Looks up eligible strategies from playbooks.json config
3. Generates candidate option structures from live chains
4. Scores candidates using multi-factor algorithm (EV + efficiency + risk fit)
5. Returns top 3 ranked trades with detailed explanations

Expected output format is designed for the Flight Manual UI template.
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

from .options_valuation_engine import (
    TradeValuation,
    OptionLeg,
    OptionType,
    calculate_trade_metrics,
)

logger = logging.getLogger(__name__)


class StrategyRouter:
    """
    Routes market regime to optimal option strategies.
    
    Workflow:
    1. Load playbook config (regime → eligible strategies)
    2. Generate option structures that match regime Greeks targets
    3. Score structures by EV, efficiency, risk fit, liquidity
    4. Rank and return top 3 executable trades
    """
    
    def __init__(self, playbook_config: Dict, symbol: str, spot: float):
        """
        Initialize Strategy Router.
        
        Args:
            playbook_config: Loaded playbooks.json config
            symbol: Underlying ticker (e.g., "AAPL")
            spot: Current spot price
        """
        self.config = playbook_config
        self.symbol = symbol
        self.spot = spot
        self.valuation = TradeValuation(spot)
    
    def route_regime(
        self,
        regime: str,
        option_chain: List[Dict],
        iv: float,
        days_to_expiration: int,
        portfolio_state: Optional[Dict] = None
    ) -> Dict:
        """
        Main entry point: route regime to top 3 strategies.
        
        Args:
            regime: Current market regime (e.g., "CRASH_PANIC")
            option_chain: List of available options with strikes, bid/ask
            iv: Implied volatility (0-1 scale, e.g., 0.25 = 25%)
            days_to_expiration: DTE for the chain
            portfolio_state: Optional current portfolio state for risk fit
        
        Returns:
            Dict with:
            - regime: Current regime
            - regime_description: Human explanation
            - top_3_strategies: List of top 3 ranked trades
            - each trade contains: structure, greeks, ev, efficiency, PoP, etc.
        """
        # Step 1: Look up eligible strategies for regime
        playbook = self.config.get("regimes", {}).get(regime, {})
        eligible_strategies = playbook.get("eligible_strategies", [])
        
        if not eligible_strategies:
            logger.warning(f"No eligible strategies for regime {regime}")
            return self._empty_result(regime)
        
        logger.info(f"🎯 Routing {regime}: {len(eligible_strategies)} strategies eligible")
        
        # Step 2: Generate candidates for each strategy
        candidates = []
        for strategy_name in eligible_strategies:
            strategy_candidates = self._generate_candidates(
                strategy_name,
                option_chain,
                iv,
                days_to_expiration,
                playbook
            )
            candidates.extend(strategy_candidates)
        
        logger.info(f"📊 Generated {len(candidates)} candidate structures")
        
        if not candidates:
            return self._empty_result(regime)
        
        # Step 3: Score candidates
        scored_candidates = self._score_candidates(
            candidates,
            playbook,
            iv=iv,
            dte=days_to_expiration,
            portfolio_state=portfolio_state,
        )
        
        # Step 4: Rank and return top 3
        ranked = sorted(
            scored_candidates,
            key=lambda x: x["composite_score"],
            reverse=True
        )[:3]
        
        logger.info(f"✅ Top 3 strategies selected")
        
        return {
            "symbol": self.symbol,
            "regime": regime,
            "regime_description": playbook.get("description", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "iv": iv,
            "spot": self.spot,
            "dte": days_to_expiration,
            "top_3_strategies": ranked,
            "candidate_count": len(candidates),
            "scoring_weights": playbook.get("scoring_weights", {}),
        }
    
    def _generate_candidates(
        self,
        strategy_name: str,
        option_chain: List[Dict],
        iv: float,
        dte: int,
        playbook: Dict
    ) -> List[Dict]:
        """
        Generate candidate option structures for a specific strategy.
        
        Args:
            strategy_name: Strategy type (e.g., "IRON_CONDOR")
            option_chain: Available options
            iv: Implied volatility
            dte: Days to expiration
            playbook: Regime playbook (contains target Greeks)
        
        Returns:
            List of candidate trade structures
        """
        candidates = []
        
        # Get strategy definition
        strategy_config = self.config.get("strategies", {}).get(strategy_name, {})
        if not strategy_config:
            logger.warning(f"Strategy {strategy_name} not found in config")
            return candidates
        
        greek_profile = strategy_config.get("greek_profile", {})
        target_delta = greek_profile.get("delta", 0.0)
        
        # Strategy-specific candidate generation
        if strategy_name == "IRON_CONDOR":
            candidates = self._generate_iron_condors(
                option_chain, iv, dte, target_delta
            )
        elif strategy_name == "BULL_CALL_SPREAD":
            candidates = self._generate_bull_call_spreads(
                option_chain, iv, dte, target_delta
            )
        elif strategy_name == "BULL_PUT_SPREAD":
            candidates = self._generate_bull_put_spreads(
                option_chain, iv, dte, target_delta
            )
        elif strategy_name == "CASH_SECURED_PUT":
            candidates = self._generate_cash_secured_puts(
                option_chain, iv, dte, target_delta
            )
        elif strategy_name == "COVERED_CALL":
            candidates = self._generate_covered_calls(
                option_chain, iv, dte, target_delta
            )
        # Add more strategies as needed
        
        # Tag each candidate with strategy name
        for candidate in candidates:
            candidate["strategy_name"] = strategy_name
            candidate["complexity"] = strategy_config.get("complexity_tier", "intermediate")
        
        logger.debug(f"{strategy_name}: Generated {len(candidates)} candidates")
        
        return candidates
    
    def _generate_iron_condors(
        self,
        option_chain: List[Dict],
        iv: float,
        dte: int,
        target_delta: float
    ) -> List[Dict]:
        """
        Generate Iron Condor candidates.
        
        Iron Condor = Short Put Spread + Short Call Spread
        Structure: Long Put, Short Put, Short Call, Long Call
        
        Delta target: Usually 0.10-0.20 (slightly bullish or neutral)
        Max profit: Credit collected
        Max loss: Width of spreads - credit
        """
        candidates = []
        
        # Filter puts and calls from chain
        puts = [o for o in option_chain if o["option_type"] == "put"]
        calls = [o for o in option_chain if o["option_type"] == "call"]
        
        if len(puts) < 2 or len(calls) < 2:
            return candidates
        
        # Generate multiple condor widths (20pt, 25pt, 30pt)
        for width in [20, 25, 30]:
            # Find put legs (short put ~15-20 delta, long put further OTM)
            short_puts = [p for p in puts 
                         if p.get("delta", 0) >= -0.25 and p.get("delta", 0) <= -0.15]
            if not short_puts:
                continue
            
            short_put = short_puts[0]
            short_put_strike = short_put["strike"]
            long_put_strike = short_put_strike - width
            
            long_put = next(
                (p for p in puts if abs(p["strike"] - long_put_strike) < 2),
                None
            )
            
            if not long_put:
                continue
            
            # Find call legs (short call ~15-20 delta, long call further OTM)
            short_calls = [c for c in calls 
                          if c.get("delta", 0) >= 0.15 and c.get("delta", 0) <= 0.25]
            if not short_calls:
                continue
            
            short_call = short_calls[0]
            short_call_strike = short_call["strike"]
            long_call_strike = short_call_strike + width
            
            long_call = next(
                (c for c in calls if abs(c["strike"] - long_call_strike) < 2),
                None
            )
            
            if not long_call:
                continue
            
            # Build the structure
            candidate = {
                "structure": "Iron Condor",
                "legs": [
                    {
                        "strike": long_put_strike,
                        "option_type": "put",
                        "bid": long_put.get("bid", 0),
                        "ask": long_put.get("ask", 0),
                        "is_long": True,
                        "quantity": 1,
                    },
                    {
                        "strike": short_put_strike,
                        "option_type": "put",
                        "bid": short_put.get("bid", 0),
                        "ask": short_put.get("ask", 0),
                        "is_long": False,
                        "quantity": 1,
                    },
                    {
                        "strike": short_call_strike,
                        "option_type": "call",
                        "bid": short_call.get("bid", 0),
                        "ask": short_call.get("ask", 0),
                        "is_long": False,
                        "quantity": 1,
                    },
                    {
                        "strike": long_call_strike,
                        "option_type": "call",
                        "bid": long_call.get("bid", 0),
                        "ask": long_call.get("ask", 0),
                        "is_long": True,
                        "quantity": 1,
                    },
                ],
                "width": width,
                "profit_zone": (short_put_strike, short_call_strike),
            }
            
            candidates.append(candidate)
        
        return candidates
    
    def _generate_bull_call_spreads(
        self,
        option_chain: List[Dict],
        iv: float,
        dte: int,
        target_delta: float
    ) -> List[Dict]:
        """
        Generate Bull Call Spread candidates.
        
        Bull Call Spread = Long Call + Short Call (higher strike)
        Structure: Long lower-strike call, Short higher-strike call
        
        Delta target: Usually 0.30-0.50 (bullish)
        Max profit: Width - debit paid
        Max loss: Debit paid
        """
        candidates = []
        
        calls = [o for o in option_chain if o["option_type"] == "call"]
        if len(calls) < 2:
            return candidates
        
        # Find call spreads with various widths
        for width in [10, 15, 20, 25]:
            for i, long_call in enumerate(calls):
                short_call = next(
                    (c for c in calls 
                     if abs(c["strike"] - (long_call["strike"] + width)) < 2),
                    None
                )
                
                if short_call:
                    candidate = {
                        "structure": "Bull Call Spread",
                        "legs": [
                            {
                                "strike": long_call["strike"],
                                "option_type": "call",
                                "bid": long_call.get("bid", 0),
                                "ask": long_call.get("ask", 0),
                                "is_long": True,
                                "quantity": 1,
                            },
                            {
                                "strike": short_call["strike"],
                                "option_type": "call",
                                "bid": short_call.get("bid", 0),
                                "ask": short_call.get("ask", 0),
                                "is_long": False,
                                "quantity": 1,
                            },
                        ],
                        "width": width,
                        "long_strike": long_call["strike"],
                        "short_strike": short_call["strike"],
                    }
                    
                    candidates.append(candidate)
                    
                    if len(candidates) >= 5:  # Limit candidates
                        break
            
            if len(candidates) >= 5:
                break
        
        return candidates
    
    def _generate_bull_put_spreads(
        self,
        option_chain: List[Dict],
        iv: float,
        dte: int,
        target_delta: float
    ) -> List[Dict]:
        """Generate Bull Put Spread candidates."""
        # Similar pattern to bull call spreads but with puts
        candidates = []
        
        puts = [o for o in option_chain if o["option_type"] == "put"]
        if len(puts) < 2:
            return candidates
        
        for width in [10, 15, 20, 25]:
            for short_put in puts:
                long_put = next(
                    (p for p in puts 
                     if abs(p["strike"] - (short_put["strike"] - width)) < 2),
                    None
                )
                
                if long_put and short_put["strike"] > long_put["strike"]:
                    candidate = {
                        "structure": "Bull Put Spread",
                        "legs": [
                            {
                                "strike": short_put["strike"],
                                "option_type": "put",
                                "bid": short_put.get("bid", 0),
                                "ask": short_put.get("ask", 0),
                                "is_long": False,
                                "quantity": 1,
                            },
                            {
                                "strike": long_put["strike"],
                                "option_type": "put",
                                "bid": long_put.get("bid", 0),
                                "ask": long_put.get("ask", 0),
                                "is_long": True,
                                "quantity": 1,
                            },
                        ],
                        "width": width,
                        "short_strike": short_put["strike"],
                        "long_strike": long_put["strike"],
                    }
                    
                    candidates.append(candidate)
                    
                    if len(candidates) >= 5:
                        break
            
            if len(candidates) >= 5:
                break
        
        return candidates
    
    def _generate_cash_secured_puts(
        self,
        option_chain: List[Dict],
        iv: float,
        dte: int,
        target_delta: float
    ) -> List[Dict]:
        """
        Generate Cash Secured Put candidates.
        
        Single short put (no long protection)
        Beginner-friendly, high capital requirement
        """
        candidates = []
        
        puts = [o for o in option_chain if o["option_type"] == "put"]
        
        # Select puts with delta ~10-20% (OTM, lower risk)
        for put in puts:
            if -0.25 <= put.get("delta", 0) <= -0.10:
                candidate = {
                    "structure": "Cash Secured Put",
                    "legs": [
                        {
                            "strike": put["strike"],
                            "option_type": "put",
                            "bid": put.get("bid", 0),
                            "ask": put.get("ask", 0),
                            "is_long": False,
                            "quantity": 1,
                        },
                    ],
                    "strike": put["strike"],
                    "capital_requirement": put["strike"] * 100,  # Full width secured
                }
                
                candidates.append(candidate)
                
                if len(candidates) >= 5:
                    break
        
        return candidates
    
    def _generate_covered_calls(
        self,
        option_chain: List[Dict],
        iv: float,
        dte: int,
        target_delta: float
    ) -> List[Dict]:
        """
        Generate Covered Call candidates.
        
        Requires holding stock, generates income via short calls
        Beginner-friendly if already holding position
        """
        candidates = []
        
        calls = [o for o in option_chain if o["option_type"] == "call"]
        
        # Select calls with delta ~20-30% (OTM)
        for call in calls:
            if 0.20 <= call.get("delta", 0) <= 0.40:
                candidate = {
                    "structure": "Covered Call",
                    "legs": [
                        {
                            "strike": call["strike"],
                            "option_type": "call",
                            "bid": call.get("bid", 0),
                            "ask": call.get("ask", 0),
                            "is_long": False,
                            "quantity": 1,
                        },
                    ],
                    "strike": call["strike"],
                    "requires_stock": True,
                    "stock_requirement": 100,  # Per contract
                }
                
                candidates.append(candidate)
                
                if len(candidates) >= 5:
                    break
        
        return candidates
    
    def _score_candidates(
        self,
        candidates: List[Dict],
        playbook: Dict,
        iv: float = 0.25,
        dte: int = 30,
        portfolio_state: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Score candidates using multi-factor algorithm.
        
        Scoring formula:
        Score = (w_ev * EV_score) +
                (w_eff * Efficiency_score) +
                (w_risk * RiskFit_score) +
                (w_liq * Liquidity_score)
        
        Where each sub-score is normalized to 0-100.
        """
        weights = playbook.get("scoring_weights", {
            "ev": 0.40,
            "efficiency": 0.30,
            "risk_fit": 0.20,
            "liquidity": 0.10,
        })
        
        scored = []
        
        for candidate in candidates:
            # Value the trade using Black-Scholes
            valuation = self.valuation.value_spread(
                legs=[
                    OptionLeg(
                        symbol=self.symbol,
                        option_type=OptionType[leg["option_type"].upper()],
                        strike=leg["strike"],
                        expiration="",
                        price=(leg["bid"] + leg["ask"]) / 2,
                        bid=leg["bid"],
                        ask=leg["ask"],
                        is_long=leg["is_long"],
                        quantity=leg.get("quantity", 1)
                    )
                    for leg in candidate["legs"]
                ],
                ttm_days=dte,
                volatility=iv if iv > 0 else 0.25,  # Fallback if IV unavailable
            )
            
            # Sub-scores (normalized 0-100)
            ev_score = self._normalize_score(
                valuation["expected_value"],
                min_val=-500,
                max_val=500
            )
            
            efficiency_score = self._normalize_score(
                valuation["efficiency"],
                min_val=0,
                max_val=1.0
            )
            
            # Risk fit: prefer strategies that match regime
            risk_fit_score = 50 if candidate.get("complexity") == "beginner" else 75
            
            liquidity_score = self._normalize_score(
                valuation["liquidity_score"],
                min_val=0,
                max_val=1.0
            )
            
            # Composite score
            composite = (
                weights["ev"] * ev_score +
                weights["efficiency"] * efficiency_score +
                weights["risk_fit"] * risk_fit_score +
                weights["liquidity"] * liquidity_score
            )
            
            # Add detailed scoring info
            candidate["valuation"] = valuation
            candidate["scores"] = {
                "ev_score": ev_score,
                "efficiency_score": efficiency_score,
                "risk_fit_score": risk_fit_score,
                "liquidity_score": liquidity_score,
            }
            candidate["composite_score"] = composite
            candidate["reasoning"] = self._generate_reasoning(
                candidate, valuation
            )
            
            scored.append(candidate)
        
        return scored
    
    @staticmethod
    def _normalize_score(value: float, min_val: float, max_val: float) -> float:
        """
        Normalize value to 0-100 score range.
        
        Args:
            value: Raw value to normalize
            min_val: Minimum of expected range
            max_val: Maximum of expected range
        
        Returns:
            Normalized score 0-100
        """
        if max_val == min_val:
            return 50.0
        
        normalized = (value - min_val) / (max_val - min_val)
        clamped = max(0, min(1, normalized))
        
        return clamped * 100
    
    @staticmethod
    def _generate_reasoning(candidate: Dict, valuation: Dict) -> str:
        """
        Generate human-readable explanation of why this trade was selected.
        """
        strategy = candidate.get("strategy_name", "Unknown")
        ev = valuation.get("expected_value", 0)
        eff = valuation.get("efficiency", 0)
        pop = valuation.get("probability_of_profit", 0)
        
        reasons = [
            f"{strategy}",
            f"EV: ${ev:.0f}",
            f"Eff: {eff:.2f}",
            f"PoP: {pop*100:.0f}%",
        ]
        
        return " • ".join(reasons)
    
    def _empty_result(self, regime: str) -> Dict:
        """Return empty result when no strategies available."""
        return {
            "symbol": self.symbol,
            "regime": regime,
            "regime_description": "",
            "timestamp": datetime.utcnow().isoformat(),
            "iv": 0,
            "spot": self.spot,
            "dte": 0,
            "top_3_strategies": [],
            "candidate_count": 0,
            "error": f"No strategies found for regime {regime}",
        }
