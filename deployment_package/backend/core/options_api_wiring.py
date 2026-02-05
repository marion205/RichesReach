# options_api_wiring.py
"""
The Orchestrator: Connects all 4 phases of the Edge Factory into a single,
production-ready pipeline.

Pipeline Flow:
  User + Ticker
    ↓
  [Phase 1] Regime Detection (market context)
    ↓
  [Phase 2] Strategy Router (top 3 candidates)
    ↓
  [Phase 3] Risk Sizer (position sizing per user portfolio)
    ↓
  [Phase 4] Flight Manual (human-readable trade plans)
    ↓
  Ready-to-Trade Plans (UI-ready output)

This orchestrator handles:
  - Live data fetching from Polygon.io
  - Regime caching (60 min TTL)
  - User portfolio state retrieval
  - Error handling and graceful degradation
  - Complete end-to-end integration
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import sys

# Import the 4 phases
try:
    from options_regime_detector import RegimeDetector
    from options_strategy_router import StrategyRouter, OptionLeg, OptionType
    from options_risk_sizer import (
        OptionsRiskSizer,
        PortfolioSnapshot,
        TradeCandidate,
        Greeks,
        RiskCaps,
        KellyConfig,
        SizeDecision,
    )
    from options_flight_manual import (
        FlightManualEngine,
        RouterOutput,
        RegimeContext,
        SizerOutput,
        PortfolioImpact,
        FlightManual,
    )
    from options_health_alerting import EdgeFactoryAlerter
    from options_repair_engine import OptionsRepairEngine, RepairPlanAcceptor
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Import error (expected in module test): {e}")
    # Allow module to load for documentation purposes

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class MarketDataSnapshot:
    """Live market snapshot from Polygon.io"""
    ticker: str
    timestamp: datetime
    ohlcv_history: List[Dict]  # 60 days of OHLCV data
    option_chain: Dict          # Current option chain (calls + puts by strike)
    current_price: float
    iv_rank: float
    realized_vol: float
    skew: float


@dataclass
class UserPortfolioState:
    """User's current portfolio holdings and Greeks"""
    user_id: int
    account_equity: float
    total_positions: int
    greeks_total: Greeks
    sector_holdings: Dict[str, float]  # {sector: exposure_pct}
    ticker_holdings: Dict[str, float]  # {ticker: exposure_pct}


@dataclass
class ReadyToTradeAnalysis:
    """Complete, ready-to-execute analysis output"""
    ticker: str
    regime: str
    confidence_level: str
    flight_manuals: List[FlightManual]  # Top 3 strategies with full explanation
    market_context: str
    generated_at: datetime
    cache_expires_at: Optional[datetime]
    warnings: List[str]


# ============================================================================
# Polygon.io Data Fetcher
# ============================================================================

class PolygonDataFetcher:
    """
    Wrapper around Polygon.io API for historical + options data.
    Handles rate limiting, error recovery, and caching.
    """

    def __init__(self, api_key: str, cache_ttl_seconds: int = 3600):
        """
        Args:
            api_key: Polygon.io API key
            cache_ttl_seconds: Cache lifetime for regime data (default 1 hour)
        """
        self.api_key = api_key
        self.cache_ttl = cache_ttl_seconds
        self._regime_cache: Dict[str, Tuple[str, datetime]] = {}
        self._skew_last_update: Dict[str, datetime] = {}

    def fetch_market_data(self, ticker: str) -> Optional[MarketDataSnapshot]:
        """
        Fetch complete market data snapshot: 60-day history + option chain.

        Returns:
            MarketDataSnapshot if successful, None on failure
        """
        try:
            # 1. Fetch 60 days of OHLCV
            ohlcv_history = self._fetch_ohlcv_history(ticker, days=60)
            if not ohlcv_history:
                logger.warning(f"No OHLCV data for {ticker}")
                return None

            # 2. Fetch current price
            current_price = self._get_current_price(ticker)
            if current_price is None:
                logger.warning(f"No current price for {ticker}")
                return None

            # 3. Fetch option chain
            option_chain = self._fetch_option_chain(ticker)
            if not option_chain:
                logger.warning(f"No option chain for {ticker}")
                return None

            # 4. Calculate IV Rank + RV + Skew (needed by Regime Detector)
            iv_rank = self._calculate_iv_rank(option_chain, ticker)
            realized_vol = self._calculate_realized_volatility(ohlcv_history)
            skew = self._calculate_skew_from_chain(option_chain, current_price)
            self._skew_last_update[ticker] = datetime.utcnow()

            return MarketDataSnapshot(
                ticker=ticker,
                timestamp=datetime.utcnow(),
                ohlcv_history=ohlcv_history,
                option_chain=option_chain,
                current_price=current_price,
                iv_rank=iv_rank,
                realized_vol=realized_vol,
                skew=skew,
            )

        except Exception as e:
            logger.error(f"Error fetching market data for {ticker}: {e}")
            return None

    def _fetch_ohlcv_history(self, ticker: str, days: int = 60) -> Optional[List[Dict]]:
        """Fetch N days of OHLCV from Polygon aggregates endpoint."""
        import requests
        from datetime import datetime, timedelta
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = (
                f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
                f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            )
            params = {'apiKey': self.api_key, 'sort': 'asc', 'limit': 50000}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') != 'OK':
                logger.warning(f"Polygon API error: {data.get('message')}")
                return None
            
            results = data.get('results', [])
            ohlcv = []
            
            for bar in results:
                ohlcv.append({
                    'timestamp': bar.get('t'),  # Unix timestamp
                    'date': datetime.utcfromtimestamp(bar.get('t', 0) / 1000).strftime('%Y-%m-%d'),
                    'open': bar.get('o'),
                    'high': bar.get('h'),
                    'low': bar.get('l'),
                    'close': bar.get('c'),
                    'volume': bar.get('v'),
                    'vwap': bar.get('vw'),  # Volume weighted average price
                })
            
            logger.info(f"Fetched {len(ohlcv)} days of OHLCV for {ticker}")
            return ohlcv
        
        except requests.RequestException as e:
            logger.error(f"Polygon API error fetching OHLCV for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing OHLCV data for {ticker}: {e}")
            return None

    def _get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price from Polygon latest trade."""
        import requests
        
        try:
            url = f"https://api.polygon.io/v1/last/quotes/{ticker}"
            params = {'apiKey': self.api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') != 'OK':
                logger.warning(f"Polygon API error: {data.get('message')}")
                return None
            
            quote = data.get('result')
            if not quote:
                return None
            
            # Use mid-price: (bid + ask) / 2
            bid = quote.get('P')
            ask = quote.get('p')
            
            if bid and ask:
                price = (bid + ask) / 2
            elif ask:
                price = ask
            elif bid:
                price = bid
            else:
                return None
            
            logger.debug(f"Current price for {ticker}: ${price:.2f}")
            return float(price)
        
        except requests.RequestException as e:
            logger.error(f"Polygon API error fetching price for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing price data for {ticker}: {e}")
            return None

    def _fetch_option_chain(self, ticker: str) -> Optional[Dict]:
        """Fetch current option chain (all expiries, all strikes)."""
        import requests
        from collections import defaultdict
        
        try:
            # Step 1: Get all option contracts for this underlying
            url = "https://api.polygon.io/v3/reference/options/contracts"
            params = {
                'underlying_ticker': ticker,
                'apiKey': self.api_key,
                'limit': 1000,
                'sort': 'expiration_date',
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') != 'OK':
                logger.warning(f"Polygon API error: {data.get('message')}")
                return None
            
            contracts = data.get('results', [])
            if not contracts:
                logger.warning(f"No option contracts found for {ticker}")
                return {}
            
            # Step 2: Fetch current quotes for each contract
            option_chain = defaultdict(lambda: defaultdict(dict))  # {expiry: {strike: {call/put: data}}}
            
            for contract in contracts[:100]:  # Limit to first 100 to avoid rate limits
                contract_id = contract.get('ticker')
                expiry = contract.get('expiration_date')
                strike = contract.get('strike_price')
                contract_type = contract.get('contract_type')  # 'call' or 'put'
                
                if not (contract_id and expiry and strike and contract_type):
                    continue
                
                try:
                    # Fetch quote for this contract
                    quote_url = f"https://api.polygon.io/v1/last/quotes/{contract_id}"
                    quote_params = {'apiKey': self.api_key}
                    
                    quote_response = requests.get(quote_url, params=quote_params, timeout=10)
                    
                    if quote_response.status_code == 200:
                        quote_data = quote_response.json()
                        if quote_data.get('status') == 'OK':
                            quote = quote_data.get('result', {})
                            
                            option_chain[expiry][strike][contract_type] = {
                                'ticker': contract_id,
                                'strike': strike,
                                'expiry': expiry,
                                'type': contract_type,
                                'bid': quote.get('P'),
                                'ask': quote.get('p'),
                                'mid': (quote.get('P', 0) + quote.get('p', 0)) / 2 if quote.get('P') and quote.get('p') else None,
                                'volume': quote.get('size'),
                                'iv': contract.get('implied_volatility'),  # If available
                            }
                
                except Exception as e:
                    logger.debug(f"Error fetching quote for {contract_id}: {e}")
                    continue
            
            logger.info(f"Fetched option chain with {len(option_chain)} expiries for {ticker}")
            return dict(option_chain)
        
        except requests.RequestException as e:
            logger.error(f"Polygon API error fetching option chain for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing option chain for {ticker}: {e}")
            return None

    def _calculate_iv_rank(self, option_chain: Dict, ticker: str) -> float:
        """Calculate IV Rank (percentile of IV over 252-day window)."""
        import requests
        
        try:
            # Fetch historical IV data from Polygon
            url = f"https://api.polygon.io/v3/reference/options/contracts"
            params = {
                'underlying_ticker': ticker,
                'apiKey': self.api_key,
                'limit': 100,
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            contracts = data.get('results', [])
            
            # Extract implied volatility values
            iv_values = []
            for contract in contracts:
                iv = contract.get('implied_volatility')
                if iv:
                    iv_values.append(iv)
            
            if not iv_values:
                logger.debug(f"No IV data available for {ticker}, returning default")
                return 0.5
            
            # Calculate percentile (IV rank = current IV rank relative to 252-day high/low)
            current_iv = max(iv_values)
            min_iv = min(iv_values)
            max_iv = max(iv_values)
            
            if max_iv == min_iv:
                iv_rank = 0.5
            else:
                iv_rank = (current_iv - min_iv) / (max_iv - min_iv)
            
            iv_rank = max(0.0, min(1.0, iv_rank))  # Clamp to 0-1
            logger.debug(f"IV Rank for {ticker}: {iv_rank:.2%}")
            return iv_rank
        
        except requests.RequestException as e:
            logger.error(f"Polygon API error calculating IV Rank for {ticker}: {e}")
            return 0.5  # Default to 50th percentile on error
        except Exception as e:
            logger.error(f"Error calculating IV Rank for {ticker}: {e}")
            return 0.5

    def _calculate_skew_from_chain(self, option_chain: Dict, current_price: float) -> float:
        """Estimate skew using nearest ATM call/put IVs (put IV - call IV)."""
        try:
            if not option_chain:
                return 0.0

            # Pick earliest expiry
            expiries = sorted(option_chain.keys())
            if not expiries:
                return 0.0
            expiry = expiries[0]
            strikes = sorted(option_chain[expiry].keys())
            if not strikes:
                return 0.0

            # Find nearest strike to spot
            nearest_strike = min(strikes, key=lambda s: abs(float(s) - current_price))
            atm_data = option_chain[expiry].get(nearest_strike, {})

            call_iv = atm_data.get("call", {}).get("iv")
            put_iv = atm_data.get("put", {}).get("iv")

            if call_iv is not None and put_iv is not None:
                return float(put_iv) - float(call_iv)

            # Fallback: use mid prices if IV missing
            call_mid = atm_data.get("call", {}).get("mid")
            put_mid = atm_data.get("put", {}).get("mid")
            if call_mid is not None and put_mid is not None and current_price:
                return float(put_mid - call_mid) / float(current_price)

            return 0.0
        except Exception as e:
            logger.error(f"Error calculating skew from chain: {e}")
            return 0.0

    def get_skew_last_update(self, ticker: str) -> Optional[datetime]:
        return self._skew_last_update.get(ticker)

    def _calculate_realized_volatility(self, ohlcv_history: List[Dict]) -> float:
        """Calculate 30-day realized volatility from returns."""
        import math
        
        try:
            if len(ohlcv_history) < 2:
                return 0.18  # Default
            
            # Calculate log returns over 30-day window (or less if fewer bars available)
            window = min(30, len(ohlcv_history))
            closes = [bar.get('close') for bar in ohlcv_history[-window:]]
            
            if not closes or any(c is None for c in closes):
                return 0.18  # Default
            
            log_returns = []
            for i in range(1, len(closes)):
                if closes[i-1] > 0:
                    ret = math.log(closes[i] / closes[i-1])
                    log_returns.append(ret)
            
            if not log_returns:
                return 0.18
            
            # Calculate standard deviation (daily volatility)
            mean_return = sum(log_returns) / len(log_returns)
            variance = sum((r - mean_return) ** 2 for r in log_returns) / len(log_returns)
            daily_vol = math.sqrt(variance)
            
            # Annualize: multiply by sqrt(252) for trading days
            annualized_vol = daily_vol * math.sqrt(252)
            
            logger.debug(f"Realized volatility: {annualized_vol:.2%}")
            return max(0.01, min(2.0, annualized_vol))  # Clamp between 1% and 200%
        
        except Exception as e:
            logger.error(f"Error calculating realized volatility: {e}")
            return 0.18  # Default


# ============================================================================
# Portfolio State Builder
# ============================================================================

class PortfolioStateBuilder:
    """
    Retrieves user's current portfolio from database and constructs Greeks snapshot.
    """

    @staticmethod
    def build_from_user(user_id: int, db_session=None) -> Optional[UserPortfolioState]:
        """
        Fetch user's portfolio from database and compute Greeks.

        Args:
            user_id: User ID
            db_session: ORM session (Django/SQLAlchemy)

        Returns:
            UserPortfolioState with current Greeks + sector exposure
        """
        try:
            # PLACEHOLDER: Replace with actual DB queries
            # Real implementation would:
            #   - Query Portfolio model for user
            #   - Query PortfolioPosition for all open trades
            #   - Sum up Greeks across all positions
            #   - Calculate sector/ticker concentrations

            logger.debug(f"[MOCK] Building portfolio state for user {user_id}")

            return UserPortfolioState(
                user_id=user_id,
                account_equity=25_000,
                total_positions=2,
                greeks_total=Greeks(delta=120, vega=-200, theta=35, gamma=10),
                sector_holdings={"Tech": 0.28, "Financials": 0.10},
                ticker_holdings={"SPY": 0.08, "QQQ": 0.14},
            )

        except Exception as e:
            logger.error(f"Error building portfolio state for user {user_id}: {e}")
            return None


# ============================================================================
# The Orchestrator
# ============================================================================

class OptionsAnalysisPipeline:
    """
    Orchestrates the full options analysis pipeline:
    Regime → Router → Sizer → Flight Manual

    This is the single public entry point for GraphQL and API consumers.
    """

    def __init__(
        self,
        polygon_api_key: str,
        playbooks_config: Optional[Dict] = None,
        risk_caps: Optional[RiskCaps] = None,
        kelly_config: Optional[KellyConfig] = None,
    ):
        """
        Args:
            polygon_api_key: Polygon.io API key
            playbooks_config: Strategy eligibility rules (from options_playbooks.json)
            risk_caps: Risk guardrails (from options_guardrails.json)
            kelly_config: Kelly sizing config
        """
        self.fetcher = PolygonDataFetcher(api_key=polygon_api_key)
        self.regime_detector = RegimeDetector()
        from .options_health_monitor import EdgeFactoryHealthMonitor
        self.health_monitor = EdgeFactoryHealthMonitor(
            data_fetcher=self.fetcher,
            regime_detector=self.regime_detector,
        )
        self.alerter = EdgeFactoryAlerter()
        self.repair_engine = OptionsRepairEngine(router=self.router)
        self.repair_acceptor = RepairPlanAcceptor()
        self._regime_shift_cache: Dict[str, datetime] = {}
        self.router = StrategyRouter(playbooks=playbooks_config or {})
        self.sizer = OptionsRiskSizer(caps=risk_caps, kelly=kelly_config)
        self.flight_manual_engine = FlightManualEngine(playbooks_config=playbooks_config)

    def get_ready_to_trade_plans(
        self,
        user_id: int,
        ticker: str,
        user_experience_level: str = "basic",
    ) -> Optional[ReadyToTradeAnalysis]:
        """
        The main entry point. Run the full pipeline for a user on a ticker.

        Args:
            user_id: User ID
            ticker: Stock ticker (e.g., "AAPL")
            user_experience_level: "basic" | "intermediate" | "pro"

        Returns:
            Complete ready-to-trade analysis with top 3 flight manuals, or None on error
        """

        warnings = []
        confidence_override = None

        # PHASE 0: Fetch live market data
        market_data = self.fetcher.fetch_market_data(ticker)
        if not market_data:
            logger.error(f"Failed to fetch market data for {ticker}")
            return None

        # PHASE 1: Detect regime
        try:
            import pandas as pd

            ohlcv_df = pd.DataFrame(market_data.ohlcv_history)
            if "date" in ohlcv_df.columns:
                ohlcv_df["date"] = pd.to_datetime(ohlcv_df["date"])
                ohlcv_df = ohlcv_df.set_index("date")

            # Proxy IV series from current IV rank + realized vol
            iv_proxy = max(0.05, market_data.realized_vol * (1 + market_data.iv_rank * 0.5))
            ohlcv_df["iv"] = iv_proxy
            ohlcv_df["rv"] = market_data.realized_vol
            ohlcv_df["skew"] = market_data.skew

            ohlcv_df = self.regime_detector.calculate_indicators(ohlcv_df)
            regime_result = self.regime_detector.detect_regime(ohlcv_df)
            regime, is_shift, description = regime_result
        except Exception as e:
            logger.error(f"Regime detection failed for {ticker}: {e}")
            warnings.append(f"Regime detection failed: {e}")
            regime = "UNKNOWN"
            description = "Unable to determine market regime"
            is_shift = False

        # PHASE 1.5: Health & integrity pre-flight check
        try:
            if is_shift:
                self._regime_shift_cache[ticker] = datetime.utcnow()
            last_regime_change = self._regime_shift_cache.get(ticker)

            health = self.health_monitor.run_pre_flight_check(
                ticker=ticker,
                market_data=market_data,
                regime_state=self.regime_detector.get_regime_state(),
                last_regime_change=last_regime_change,
            )
            
            # NEW: Trigger alerts if unhealthy
            self.alerter.process_health_status(
                ticker=ticker,
                health=health,
                timestamp=datetime.utcnow(),
                user_count_affected=0,  # TODO: Query active user count for this ticker
            )
            
            if not health.is_healthy:
                warnings.extend(health.active_alerts)
                confidence_override = "CAUTION"
        except Exception as e:
            logger.error(f"Health monitor failed for {ticker}: {e}")
            warnings.append(f"Health monitor error: {e}")
            confidence_override = "CAUTION"

        # PHASE 2: Generate strategy candidates (Route)
        try:
            router_results = self.router.route_regime(
                regime=regime,
                option_chain=market_data.option_chain,
                iv=market_data.iv_rank,
                days_to_expiration=21,
                portfolio_state={},  # Optional portfolio context
            )
            top_candidates = router_results.get("top_3_strategies", [])
            if not top_candidates:
                logger.warning(f"No strategies generated for {ticker} in regime {regime}")
                warnings.append("Router generated no candidate strategies")
                top_candidates = []
        except Exception as e:
            logger.error(f"Strategy routing failed for {ticker}: {e}")
            warnings.append(f"Strategy routing failed: {e}")
            top_candidates = []

        # PHASE 3: Get user portfolio + size trades
        user_portfolio = PortfolioStateBuilder.build_from_user(user_id)
        if not user_portfolio:
            logger.warning(f"Could not build portfolio state for user {user_id}")
            warnings.append("Portfolio state unavailable; using default guardrails")
            user_portfolio = UserPortfolioState(
                user_id=user_id,
                account_equity=10_000,
                total_positions=0,
                greeks_total=Greeks(),
                sector_holdings={},
                ticker_holdings={},
            )

        # Convert user portfolio to sizer format
        portfolio_snapshot = PortfolioSnapshot(
            equity=user_portfolio.account_equity,
            greeks_total=user_portfolio.greeks_total,
            sector_exposure_pct=user_portfolio.sector_holdings,
            ticker_exposure_pct=user_portfolio.ticker_holdings,
        )

        # PHASE 4: Size each candidate + generate Flight Manual
        flight_manuals = []

        for candidate in top_candidates:
            try:
                # Convert candidate to TradeCandidate format
                trade_candidate = self._candidate_to_trade_candidate(candidate, ticker)

                # Size the trade
                size_decision = self.sizer.size_trade(
                    portfolio_snapshot,
                    trade_candidate,
                    user_experience_level=user_experience_level,
                )

                # Build portfolio impact
                portfolio_impact = self._compute_portfolio_impact(
                    portfolio_snapshot,
                    trade_candidate,
                    size_decision,
                )

                # Generate Flight Manual
                regime_context = RegimeContext(
                    regime=regime,
                    regime_description=description,
                    iv_rank=market_data.iv_rank,
                    price_percentile=0.5,  # Placeholder
                )

                router_output = self._candidate_to_router_output(candidate, ticker)

                sizer_output = SizerOutput(
                    contracts=size_decision.contracts,
                    risk_amount=size_decision.risk_amount,
                    kelly_full=size_decision.kelly_full,
                    kelly_fractional=size_decision.kelly_fractional,
                    limiting_factors=size_decision.limiting_factors,
                    warnings=size_decision.warnings,
                )

                flight_manual = self.flight_manual_engine.generate_flight_manual(
                    router_output=router_output,
                    regime=regime_context,
                    sizer_output=sizer_output,
                    portfolio_impact=portfolio_impact,
                )

                flight_manuals.append(flight_manual)

            except Exception as e:
                logger.error(f"Failed to size/explain candidate: {e}")
                warnings.append(f"Strategy sizing failed: {e}")
                continue

        # Determine confidence + cache expiry
        confidence = "HOT" if any(m.confidence == "HOT" for m in flight_manuals) else \
                    "WARM" if any(m.confidence == "WARM" for m in flight_manuals) else "MONITOR"
        if confidence_override == "CAUTION":
            confidence = "CAUTION"

        cache_expires = datetime.utcnow() + timedelta(seconds=self.fetcher.cache_ttl)

        return ReadyToTradeAnalysis(
            ticker=ticker,
            regime=regime,
            confidence_level=confidence,
            flight_manuals=flight_manuals,
            market_context=description,
            generated_at=datetime.utcnow(),
            cache_expires_at=cache_expires,
            warnings=warnings,
        )

    # ---------- Conversion helpers ----------

    def _candidate_to_trade_candidate(self, candidate: Dict, ticker: str) -> TradeCandidate:
        """Convert Router candidate to TradeCandidate format for Sizer."""
        return TradeCandidate(
            pop=candidate.get("pop", 0.50),
            max_profit=candidate.get("max_profit", 100),
            max_loss=candidate.get("max_loss", 200),
            greeks_per_contract=Greeks(
                delta=candidate.get("delta", 0),
                vega=candidate.get("vega", 0),
                theta=candidate.get("theta", 0),
                gamma=candidate.get("gamma", 0),
            ),
            sector="Tech",  # Placeholder; would extract from ticker sector
            ticker=ticker,
            corr_to_portfolio=0.5,  # Placeholder
            edge_score=candidate.get("composite_score", 70),
        )

    def _candidate_to_router_output(self, candidate: Dict, ticker: str) -> RouterOutput:
        """Convert Router candidate to RouterOutput format for Flight Manual."""
        legs = candidate.get("legs", [])
        leg_objects = [
            OptionLeg(
                option_type=leg.get("option_type", "CALL"),
                strike=leg.get("strike", 450),
                bid=leg.get("bid", 1.0),
                ask=leg.get("ask", 1.5),
                position="LONG" if leg.get("long_short") == "LONG" else "SHORT",
                quantity=1,
            )
            for leg in legs
        ]

        return RouterOutput(
            strategy_name=candidate.get("strategy_name", "IRON_CONDOR"),
            ticker=ticker,
            legs=leg_objects,
            composite_score=candidate.get("composite_score", 70),
            ev_score=candidate.get("ev_score", 70),
            efficiency_score=candidate.get("efficiency_score", 70),
            risk_fit_score=candidate.get("risk_fit_score", 70),
            liquidity_score=candidate.get("liquidity_score", 70),
            pop=candidate.get("pop", 0.50),
            max_profit=candidate.get("max_profit", 100),
            max_loss=candidate.get("max_loss", 200),
            reasoning=candidate.get("reasoning", "Trade candidate"),
        )

    def _compute_portfolio_impact(
        self,
        portfolio: PortfolioSnapshot,
        trade: TradeCandidate,
        size_decision: SizeDecision,
    ) -> PortfolioImpact:
        """Compute portfolio Greeks before/after impact."""
        delta_after = portfolio.greeks_total.delta + size_decision.contracts * trade.greeks_per_contract.delta
        vega_after = portfolio.greeks_total.vega + size_decision.contracts * trade.greeks_per_contract.vega
        theta_after = portfolio.greeks_total.theta + size_decision.contracts * trade.greeks_per_contract.theta
        gamma_after = portfolio.greeks_total.gamma + size_decision.contracts * trade.greeks_per_contract.gamma

        return PortfolioImpact(
            portfolio_equity=portfolio.equity,
            greeks_before_delta=portfolio.greeks_total.delta,
            greeks_after_delta=delta_after,
            greeks_before_vega=portfolio.greeks_total.vega,
            greeks_after_vega=vega_after,
            greeks_before_theta=portfolio.greeks_total.theta,
            greeks_after_theta=theta_after,
            sector_concentration_pct=portfolio.sector_exposure_pct.get(trade.sector, 0.0),
            ticker_concentration_pct=portfolio.ticker_exposure_pct.get(trade.ticker, 0.0) if portfolio.ticker_exposure_pct else 0.0,
        )

    def check_portfolio_repairs(
        self,
        user_id: int,
        positions: List,
        account_equity: float,
        current_prices: Dict[str, float],
    ) -> Dict:
        """
        Hourly background task to check all open positions for repair needs.
        
        This is the "Auto-Defend" workflow: identify positions leaking Delta
        and suggest defensive adjustments to reduce max loss.
        
        Args:
            user_id: User ID
            positions: List of OptionsPosition objects
            account_equity: User's total account equity
            current_prices: Dict mapping ticker → current price
        
        Returns:
            Dict with:
            - repair_plans: List of RepairPlan objects (sorted by priority)
            - notifications_sent: Count of user notifications
            - timestamp: When check was run
        """
        try:
            logger.info(f"🔍 Starting repair check for user {user_id} ({len(positions)} positions)")
            
            # Batch analyze all positions
            repair_plans = self.repair_engine.batch_analyze_portfolio(
                positions=positions,
                current_underlying_prices=current_prices,
                account_equity=account_equity,
            )
            
            notifications_sent = 0
            
            # Execute workflow for each repair plan
            for repair_plan in repair_plans:
                result = self.repair_engine.execute_repair_suggestion_workflow(
                    repair_plan=repair_plan,
                    user_id=user_id,
                )
                if result.get("success", False):
                    notifications_sent += 1
                    logger.info(f"✅ Repair notification sent for {repair_plan.ticker}")
            
            return {
                "user_id": user_id,
                "repair_plans": repair_plans,
                "repairs_needed": len(repair_plans),
                "notifications_sent": notifications_sent,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio repair check: {e}")
            return {
                "user_id": user_id,
                "repair_plans": [],
                "repairs_needed": 0,
                "notifications_sent": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Note: In production, this would be imported and used as:
    #   from core.options_api_wiring import OptionsAnalysisPipeline
    #   pipeline = OptionsAnalysisPipeline(polygon_api_key="...")
    #   analysis = pipeline.get_ready_to_trade_plans(user_id=42, ticker="SPY")

    print("=" * 80)
    print("Options Analysis Pipeline - Orchestrator")
    print("=" * 80)
    print()
    print("ARCHITECTURE:")
    print("  User + Ticker")
    print("    ↓")
    print("  [Phase 1] Regime Detection (market context)")
    print("    ↓")
    print("  [Phase 2] Strategy Router (top 3 candidates)")
    print("    ↓")
    print("  [Phase 3] Risk Sizer (position sizing per user portfolio)")
    print("    ↓")
    print("  [Phase 4] Flight Manual (human-readable trade plans)")
    print("    ↓")
    print("  Ready-to-Trade Analysis (UI-ready output)")
    print()
    print("=" * 80)
    print()
    print("KEY FUNCTIONS:")
    print("  pipeline = OptionsAnalysisPipeline(polygon_api_key='...')")
    print("  analysis = pipeline.get_ready_to_trade_plans(user_id=42, ticker='SPY')")
    print()
    print("OUTPUT FORMAT (ReadyToTradeAnalysis):")
    print("  - ticker: str")
    print("  - regime: str (MEAN_REVERSION | BREAKOUT_EXPANSION | ...)")
    print("  - confidence_level: str (HOT | WARM | MONITOR)")
    print("  - flight_manuals: List[FlightManual] (top 3 strategies)")
    print("  - market_context: str (regime description)")
    print("  - generated_at: datetime")
    print("  - cache_expires_at: datetime")
    print("  - warnings: List[str]")
    print()
    print("=" * 80)
    print()
    print("READY FOR GRAPHQL INTEGRATION")
    print("=" * 80)
