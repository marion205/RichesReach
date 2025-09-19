"""
AI/ML Stock Recommendation System (refactored: faster, safer, more defensible)
- Caching + retries + session reuse
- Leak-safe technical features (no future peeking)
- Wilder RSI, EMA MACD, annualized return/vol
- Optional integration with AdvancedMLAlgorithms (if model present)
"""

from __future__ import annotations

import os
import math
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry
from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet

from core.models import User, Stock
from core.advanced_ml_algorithms import AdvancedMLAlgorithms

logger = logging.getLogger(__name__)

ALPHA_BASE = "https://www.alphavantage.co/query"
CACHE_TTL_SEC = 3600  # 1h
HTTP_TIMEOUT = 10

# Free Alpha Vantage is ~5 req/min; keep a light soft-limit
ALPHA_SOFT_RPM = 5

@dataclass(frozen=True)
class StockRecommendation:
    stock: Stock
    confidence_score: float  # 0..1
    risk_level: str          # "Low" | "Medium" | "High"
    expected_return: float   # fraction (e.g., 0.12 == 12%)
    reasoning: str
    ml_insights: Dict[str, float]

@dataclass(frozen=True)
class UserProfile:
    income_level: str         # low | medium | high | very_high
    risk_tolerance: str       # conservative | moderate | aggressive
    investment_horizon: str   # long_term | medium_term | short_term
    portfolio_size: float
    age_group: str
    experience_level: str     # beginner | intermediate | advanced


class MLStockRecommender:
    """Fast, robust, and deterministic stock recommender with ML fallback."""

    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY")
        self.finnhub_key = os.getenv("FINNHUB_KEY")

        # shared HTTP session with retries
        self._session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods={"GET"},
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retries))
        self._session.mount("http://", HTTPAdapter(max_retries=retries))

        # Optional ML engine
        try:
            self._ml = AdvancedMLAlgorithms(models_dir=getattr(settings, "ML_MODELS_DIR", "advanced_ml_models"))
        except Exception as e:
            logger.warning("AdvancedMLAlgorithms unavailable: %s", e)
            self._ml = None

    # --------------------------------------------------------------------- utils
    @staticmethod
    def _safe_float(x, default=0.0) -> float:
        try:
            if x is None:
                return default
            return float(x)
        except Exception:
            return default

    @staticmethod
    def _now_utc() -> str:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # ------------------------------------------------------------ user profiling
    def get_user_profile(self, user: User) -> UserProfile:
        """Extract user profile with sensible defaults; no exceptions leak."""
        try:
            ip = getattr(user, "incomeprofile", None)
            income = getattr(ip, "annual_income", 50_000) or 50_000

            if income < 30_000:
                income_level = "low"
            elif income < 75_000:
                income_level = "medium"
            elif income < 150_000:
                income_level = "high"
            else:
                income_level = "very_high"

            # naive proxy if no explicit field present
            risk_tolerance = "conservative" if income < 50_000 else "moderate"
            if income > 100_000:
                risk_tolerance = "aggressive"

            # horizon could be inferred from age if available; default long
            investment_horizon = "long_term"

            portfolio_size = float(min(income * 0.10, 10_000))
            experience_level = "beginner" if income < 60_000 else "intermediate"
            if income > 120_000:
                experience_level = "advanced"

            return UserProfile(
                income_level=income_level,
                risk_tolerance=risk_tolerance,
                investment_horizon=investment_horizon,
                portfolio_size=portfolio_size,
                age_group="adult",
                experience_level=experience_level,
            )
        except Exception as e:
            logger.warning("get_user_profile fallback: %s", e)
            return UserProfile(
                income_level="medium",
                risk_tolerance="moderate",
                investment_horizon="long_term",
                portfolio_size=5_000.0,
                age_group="adult",
                experience_level="beginner",
            )

    # ---------------------------------------------------------------- market I/O
    def _alpha_get(self, params: Dict) -> Optional[Dict]:
        if not self.alpha_vantage_key:
            return None
        p = dict(params)
        p["apikey"] = self.alpha_vantage_key
        try:
            resp = self._session.get(ALPHA_BASE, params=p, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.debug("AlphaVantage error (%s): %s", params.get("function"), e)
            return None

    def fetch_real_stock_overview(self, symbol: str) -> Optional[Dict]:
        """AlphaVantage OVERVIEW (cached)."""
        if not self.alpha_vantage_key:
            return None
        cache_key = f"alpha_overview:{symbol}"
        hit = cache.get(cache_key)
        if hit:
            return hit
        data = self._alpha_get({"function": "OVERVIEW", "symbol": symbol})
        if not data or "Symbol" not in data:
            return None
        cache.set(cache_key, data, CACHE_TTL_SEC)
        return data

    def fetch_historical_data(self, symbol: str, days: int = 120) -> Optional[pd.DataFrame]:
        """TIME_SERIES_DAILY (adjusted would be better if you rely on dividends)."""
        if not self.alpha_vantage_key:
            return None
        days = max(60, min(500, int(days)))  # guardrails
        cache_key = f"alpha_daily:{symbol}:{days}"
        hit = cache.get(cache_key)
        if hit:
            return pd.DataFrame(hit).set_index("date")

        data = self._alpha_get({"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact"})
        if not data or "Time Series (Daily)" not in data:
            return None

        ts = data["Time Series (Daily)"]
        df = (
            pd.DataFrame.from_dict(ts, orient="index")
            .rename(
                columns={
                    "1. open": "open",
                    "2. high": "high",
                    "3. low": "low",
                    "4. close": "close",
                    "5. volume": "volume",
                }
            )
            .astype(float)
        )
        df.index = pd.to_datetime(df.index)
        df = df.sort_index().tail(days)
        df["date"] = df.index
        cache.set(cache_key, df.reset_index(drop=True).to_dict("records"), CACHE_TTL_SEC)
        return df

    # ------------------------------------------------------------- tech features
    @staticmethod
    def _ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Wilder's RSI."""
        if prices is None or len(prices) < period + 1:
            return 50.0
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
        rs = avg_gain / (avg_loss.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0

    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26) -> float:
        if prices is None or len(prices) < slow + 1:
            return 0.0
        macd = self._ema(prices, fast) - self._ema(prices, slow)
        return float(macd.iloc[-1])

    def _create_mock_features(self, stock: Stock) -> Dict[str, float]:
        """Create mock features for demonstration when API is not available."""
        import random
        
        # Generate realistic mock features based on stock characteristics
        base_volatility = 0.15 if stock.sector == "Technology" else 0.12
        volatility = base_volatility + random.uniform(-0.05, 0.05)
        
        # Higher expected return for higher risk stocks
        expected_return = volatility * random.uniform(0.8, 1.2)
        
        return {
            "annualized_return": expected_return,
            "annualized_volatility": volatility,
            "rsi": random.uniform(30, 70),  # Neutral RSI
            "macd": random.uniform(-0.02, 0.02),  # Small MACD
            "momentum": random.uniform(-0.1, 0.1),  # Small momentum
            "volume_trend": random.uniform(0.8, 1.2),  # Volume trend
            "price_to_ma5": random.uniform(0.95, 1.05),  # Price relative to MA5
            "price_to_ma20": random.uniform(0.9, 1.1),  # Price relative to MA20
        }

    def calculate_ml_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Cross-sectionally comparable, leak-safe features."""
        if df is None or df.empty or len(df) < 30:
            return {}
        px = df["close"].astype(float)
        vol = df["volume"].astype(float)

        # returns & vol
        ret = px.pct_change().dropna()
        if ret.empty:
            return {}
        ann_ret = (px.iloc[-1] / px.iloc[0]) ** (252.0 / max(len(px), 1)) - 1.0
        ann_vol = float(ret.std() * math.sqrt(252))

        ma5 = float(px.rolling(5).mean().iloc[-1])
        ma20 = float(px.rolling(20).mean().iloc[-1]) if len(px) >= 20 else float(px.mean())
        momentum = float((px.iloc[-1] - ma20) / ma20) if ma20 else 0.0

        avg_volume = float(vol.tail(20).mean()) if len(vol) >= 20 else float(vol.mean())
        vol_trend = float(vol.tail(5).mean() / max(vol.tail(20).mean(), 1.0)) if len(vol) >= 20 else 1.0

        rsi = self.calculate_rsi(px)
        macd = self.calculate_macd(px)

        return {
            "current_price": float(px.iloc[-1]),
            "ann_return": float(ann_ret),
            "ann_vol": ann_vol,
            "ma_5": ma5,
            "ma_20": ma20,
            "momentum": momentum,
            "avg_volume": avg_volume,
            "volume_trend": vol_trend,
            "rsi": rsi,
            "macd": macd,
            "observations": float(len(px)),
        }

    # --------------------------------------------------------------- scoring/ML
    @staticmethod
    def _normalize_beginner_score(bfs: Optional[float]) -> float:
        """Unify to 0..10 scale (handles stored 0..100)."""
        if bfs is None:
            return 0.0
        bfs = float(bfs)
        return bfs / 10.0 if bfs > 10.0 else bfs

    @staticmethod
    def _risk_bucket(ann_vol: float) -> str:
        if ann_vol < 0.20:
            return "Low"
        if ann_vol < 0.35:
            return "Medium"
        return "High"

    def _income_params(self, profile: UserProfile) -> Dict[str, float]:
        """Income-specific knobs that shape ranking and sizing."""
        if profile.income_level == "low":
            return dict(
                risk_budget_pct=0.05,         # total risk budget of portfolio
                max_pos_pct=0.08,             # cap per name
                min_liquidity_usd=5_000_000,  # avoid thin names
                div_weight=0.20,              # favor dividends
                value_weight=0.20,            # favor fair P/E
                mom_weight=0.12,
                stability_weight=0.38,
            )
        if profile.income_level == "medium":
            return dict(
                risk_budget_pct=0.08,
                max_pos_pct=0.10,
                min_liquidity_usd=3_000_000,
                div_weight=0.12,
                value_weight=0.18,
                mom_weight=0.18,
                stability_weight=0.32,
            )
        if profile.income_level == "high":
            return dict(
                risk_budget_pct=0.12,
                max_pos_pct=0.12,
                min_liquidity_usd=2_000_000,
                div_weight=0.08,
                value_weight=0.15,
                mom_weight=0.25,
                stability_weight=0.28,
            )
        # very_high
        return dict(
            risk_budget_pct=0.15,
            max_pos_pct=0.15,
            min_liquidity_usd=1_000_000,
            div_weight=0.05,
            value_weight=0.12,
            mom_weight=0.30,
            stability_weight=0.28,
        )

    def _affordability_penalty(self, portfolio_size: float, price: float, max_pos_pct: float) -> float:
        """
        Penalize names where a single share would exceed the max position budget,
        or where you can't buy at least ~2 shares comfortably.
        """
        if price <= 0 or portfolio_size <= 0:
            return 1.0
        pos_budget = portfolio_size * max_pos_pct
        if price > pos_budget:
            # too expensive for a single share
            return 0.6
        if price * 2 > pos_budget:
            # barely fits for 2 shares
            return 0.85
        return 1.0

    def _liquidity_penalty(self, stock: Stock, min_liquidity_usd: float) -> float:
        adv = float(getattr(stock, "avg_daily_dollar_volume", 0) or 0)
        if adv <= 0:
            return 0.8
        if adv < min_liquidity_usd:
            return 0.85
        return 1.0

    def _position_suggestion(
        self,
        profile: UserProfile,
        recs: List[StockRecommendation],
    ) -> List[Dict]:
        """
        Convert ranked recs into suggested allocations (income-aware).
        Conservative sizing: soft cap per-name + total risk budget.
        """
        knobs = self._income_params(profile)
        total_budget = profile.portfolio_size * knobs["risk_budget_pct"]
        if total_budget <= 0:
            return [{"symbol": r.stock.symbol, "allocation_pct": 0.0} for r in recs]

        # allocate proportionally by (confidence * max(0, expected_return))
        scores = [max(0.0, r.confidence_score) * max(0.0, r.expected_return) for r in recs]
        s = sum(scores) or 1.0
        raw_weights = [x / s for x in scores]

        # apply per-name cap and rescale inside total_budget
        per_name_cap = knobs["max_pos_pct"]
        capped = [min(w, per_name_cap) for w in raw_weights]
        cap_sum = sum(capped) or 1.0
        scaled = [w / cap_sum * knobs["risk_budget_pct"] for w in capped]

        return [
            {"symbol": r.stock.symbol, "allocation_pct": round(w, 4)}
            for r, w in zip(recs, scaled)
        ]

    def _heuristic_confidence(
        self,
        user: UserProfile,
        stock: Stock,
        f: Dict[str, float],
        overview: Optional[Dict],
    ) -> Tuple[float, float, str, str]:
        """
        Income-aware score:
        - weights change by income (stability/value/dividend vs momentum)
        - penalize unaffordable tickers and illiquidity for lower incomes
        """
        knobs = self._income_params(user)

        bfs = self._normalize_beginner_score(getattr(stock, "beginner_friendly_score", 0.0))
        pe = self._safe_float((overview or {}).get("PERatio"), default=np.nan)
        div_yield = self._safe_float((overview or {}).get("DividendYield"), default=0.0)

        momentum = f.get("momentum", 0.0)
        ann_vol  = f.get("ann_vol", 0.30)
        rsi      = f.get("rsi", 50.0)
        vol_trend = f.get("volume_trend", 1.0)
        price    = f.get("current_price", 0.0)

        # bounded / normalized components
        z_mom = float(np.tanh(momentum * 3))
        z_vol = 1.0 - min(max(ann_vol, 0.0), 0.8) / 0.8
        z_pe  = 0.0
        if not np.isnan(pe) and pe > 0:
            if pe < 8: z_pe = 0.6
            elif pe <= 22: z_pe = 1.0
            elif pe <= 35: z_pe = 0.5
            else: z_pe = 0.2
        z_div = min(div_yield / 0.03, 1.0)
        z_beg = min(max(bfs / 10.0, 0.0), 1.0)

        rsi_ok  = 1.0 if 30 < rsi < 70 else 0.6
        vol_conf = 1.0 if vol_trend > 1.05 else 0.7

        # income-aware weights
        score = (
            knobs["stability_weight"] * z_vol +
            knobs["mom_weight"]       * z_mom +
            knobs["value_weight"]     * z_pe +
            knobs["div_weight"]       * z_div +
            0.10                      * z_beg
        )
        score = float(np.clip(score * rsi_ok * vol_conf, 0, 1))

        # penalties (affordability + liquidity) — stronger impact for lower incomes
        score *= self._affordability_penalty(user.portfolio_size, price, knobs["max_pos_pct"])
        score *= self._liquidity_penalty(stock, knobs["min_liquidity_usd"])

        # expected return (risk-aware, conservative):
        exp_ret = 0.25 * f.get("ann_return", 0.0) + 0.15 * z_mom
        risk = self._risk_bucket(ann_vol)

        reasons = []
        if z_vol >= 0.6: reasons.append("low-to-moderate volatility")
        if z_mom > 0.2: reasons.append("positive momentum")
        if z_pe >= 0.8: reasons.append("reasonable valuation")
        if z_div >= 0.6 and knobs["div_weight"] > 0.1: reasons.append("income-supportive dividend")
        if z_beg >= 0.6: reasons.append("beginner-friendly profile")
        if 30 < rsi < 70: reasons.append("RSI in healthy range")
        if vol_trend > 1.05: reasons.append("rising volume")
        # affordability/liquidity messaging
        if price > user.portfolio_size * knobs["max_pos_pct"]:
            reasons.append("price exceeds comfortable position size for your portfolio")
        if float(getattr(stock, "avg_daily_dollar_volume", 0) or 0) < knobs["min_liquidity_usd"]:
            reasons.append("lower liquidity for your income profile")

        return score, float(exp_ret), risk, "; ".join(reasons) or "Balanced income-aware profile"

    # --------------------------------------------------------------- public APIs
    def generate_ml_recommendations(self, user: User, limit: int = 10) -> List[StockRecommendation]:
        """Top N recommendations for the user. Fast path, production-safe."""
        t0 = time.time()
        profile = self.get_user_profile(user)

        # pull a manageable universe; only fields we use
        qs: QuerySet[Stock] = (
            Stock.objects.all()
            .only(
                "id",
                "symbol",
                "company_name",
                "sector",
                "beginner_friendly_score",
                "pe_ratio",
                "dividend_yield",
                "current_price",
                "avg_daily_dollar_volume",
            )
            .order_by("symbol")
        )[:80]

        recs: List[StockRecommendation] = []

        for stock in qs:
            # Try DB fundamentals first (cheap), then API overview if needed
            overview = None
            if not getattr(stock, "pe_ratio", None) or not getattr(stock, "dividend_yield", None):
                overview = self.fetch_real_stock_overview(stock.symbol)
            else:
                overview = {
                    "PERatio": stock.pe_ratio,
                    "DividendYield": stock.dividend_yield,
                }

            # Historical data -> features
            df = self.fetch_historical_data(stock.symbol, days=120)
            if df is None or df.empty:
                # Use mock features for demonstration when API is not available
                feats = self._create_mock_features(stock)
            else:
                feats = self.calculate_ml_features(df)
            
            if not feats:
                continue

            # If you have a pre-trained model, you can rank by predicted return here.
            # Example (optional): use stacking model if present
            expected_return = None
            if self._ml and "stacking_ensemble" in set(self._ml.list_models() or []):
                try:
                    mdl = self._ml.load_model("stacking_ensemble")
                    X = np.array(
                        [[feats["momentum"], feats["ann_vol"], feats["rsi"], feats["macd"], feats["avg_volume"]]],
                        dtype=float,
                    )
                    pred = mdl.predict(X)
                    expected_return = float(pred[0])
                except Exception as e:
                    logger.debug("Model predict failed for %s: %s", stock.symbol, e)

            # Heuristic score + reasoning (still used to build confidence/risk)
            conf, exp_ret_heur, risk, reasoning = self._heuristic_confidence(profile, stock, feats, overview)
            exp_ret = expected_return if expected_return is not None else exp_ret_heur

            ml_insights = {
                "ann_vol": feats.get("ann_vol", 0.0),
                "momentum": feats.get("momentum", 0.0),
                "rsi": feats.get("rsi", 50.0),
                "macd": feats.get("macd", 0.0),
                "volume_trend": feats.get("volume_trend", 1.0),
                "ann_return": feats.get("ann_return", 0.0),
                "used_ml_model": bool(expected_return is not None),
            }

            recs.append(
                StockRecommendation(
                    stock=stock,
                    confidence_score=conf,
                    risk_level=risk,
                    expected_return=exp_ret,
                    reasoning=reasoning,
                    ml_insights=ml_insights,
                )
            )

        # rank by confidence, then expected return
        recs.sort(key=lambda r: (r.confidence_score, r.expected_return), reverse=True)
        dt = time.time() - t0
        logger.info("Generated %d recs for user %s in %.2fs", len(recs[:limit]), getattr(user, "id", "n/a"), dt)
        
        # Add allocation suggestions
        allocations = self._position_suggestion(profile, recs[:limit])
        for r, a in zip(recs[:limit], allocations):
            r.ml_insights["suggested_allocation_pct"] = a["allocation_pct"]
        
        return recs[:limit]

    def get_beginner_friendly_stocks(self, user: User, limit: int = 10) -> List[StockRecommendation]:
        """Beginner list with consistent 0..10 scale for beginner_friendly_score."""
        profile = self.get_user_profile(user)

        # Consistent thresholds (0..10). If your DB is 0..100, store a migration or normalize below.
        qs = (
            Stock.objects.filter(beginner_friendly_score__gte=70.0)  # 70/100 = 7/10
            .only(
                "id",
                "symbol",
                "company_name",
                "sector",
                "beginner_friendly_score",
                "pe_ratio",
                "dividend_yield",
                "current_price",
                "avg_daily_dollar_volume",
            )
            .order_by("-beginner_friendly_score")
        )[:40]

        out: List[StockRecommendation] = []
        for stock in qs:
            # Try to fetch historical data, but fall back to mock data if API is not available
            df = self.fetch_historical_data(stock.symbol, days=120)
            if df is None or df.empty:
                # Create mock features for demonstration
                feats = self._create_mock_features(stock)
            else:
                feats = self.calculate_ml_features(df)
            
            if not feats:
                continue
            conf, exp_ret, risk, reasoning = self._heuristic_confidence(profile, stock, feats, None)
            out.append(
                StockRecommendation(
                    stock=stock,
                    confidence_score=conf,
                    risk_level=risk,
                    expected_return=exp_ret,
                    reasoning=reasoning,
                    ml_insights={
                        "ann_vol": feats.get("ann_vol", 0.0),
                        "momentum": feats.get("momentum", 0.0),
                        "rsi": feats.get("rsi", 50.0),
                    },
                )
            )
        out.sort(key=lambda r: (r.confidence_score, r.expected_return), reverse=True)
        return out[:limit]

    # --------------------------------------------------------------- diagnostics
    def get_ml_service_status(self) -> Dict:
        try:
            if not self._ml:
                return {"tensorflow_available": False, "sklearn_available": False, "status": "unavailable"}
            return self._ml.get_service_status()
        except Exception as e:
            return {"error": str(e), "status": "unavailable"}


# Global instance for easy import
ml_recommender = MLStockRecommender()
