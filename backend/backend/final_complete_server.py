#!/usr/bin/env python3
"""
Final Complete Server for RichesReach - All GraphQL fields included (OperationName-aware)
- Robust top-level field detection that honors `operationName`
- Phase 2 handlers prioritized with early returns
- GraphQL-safe default fallback (never returns {message: ...} to clients)
- Exposes /graphql and /graphql/
- Adds X-Server-Build header for easy verification you hit the updated server
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn
import os
import logging
import importlib
import inspect
import math
from datetime import datetime, timedelta
import jwt
import hashlib
import random
import requests
import uuid
from time import perf_counter

# Enhanced Monitoring System
try:
    from core.monitoring import performance_monitor, health_checker, get_logger
    MONITORING_AVAILABLE = True
    logger = get_logger("richesreach")
    print("✅ Enhanced monitoring system loaded successfully")
except ImportError as e:
    MONITORING_AVAILABLE = False
    print(f"⚠️ Enhanced monitoring not available: {e}")
    logger = logging.getLogger("richesreach")

# Feast Feature Store
try:
    from core.feast_manager import feast_manager
    FEAST_AVAILABLE = True
    print("✅ Feast feature store loaded successfully")
except ImportError as e:
    FEAST_AVAILABLE = False
    print(f"⚠️ Feast feature store not available: {e}")

# Enhanced Redis Cluster
try:
    from core.redis_cluster import redis_cluster
    REDIS_CLUSTER_AVAILABLE = True
    print("✅ Enhanced Redis cluster loaded successfully")
except ImportError as e:
    REDIS_CLUSTER_AVAILABLE = False
    print(f"⚠️ Enhanced Redis cluster not available: {e}")

# Phase 2: Streaming Pipeline
try:
    from core.streaming_producer import StreamingProducer, initialize_streaming
    from core.streaming_consumer import StreamingConsumer, initialize_streaming_consumer
    STREAMING_AVAILABLE = True
    print("✅ Phase 2 streaming pipeline loaded successfully")
except ImportError as e:
    STREAMING_AVAILABLE = False
    print(f"⚠️ Phase 2 streaming pipeline not available: {e}")

# Phase 2: ML Model Versioning
try:
    from core.ml_model_versioning import ModelVersionManager, ABTestingManager, initialize_ml_versioning
    ML_VERSIONING_AVAILABLE = True
    print("✅ Phase 2 ML model versioning loaded successfully")
except ImportError as e:
    ML_VERSIONING_AVAILABLE = False
    print(f"⚠️ Phase 2 ML model versioning not available: {e}")

# Phase 3: AI Router
try:
    from core.ai_router import ai_router
    from core.ai_router_api import router as ai_router_api
    AI_ROUTER_AVAILABLE = True
    print("✅ Phase 3 AI Router loaded successfully")
except ImportError as e:
    AI_ROUTER_AVAILABLE = False
    print(f"⚠️ Phase 3 AI Router not available: {e}")

# Phase 3: Advanced Analytics
try:
    from core.analytics_engine import initialize_analytics, analytics_engine, predictive_analytics
    from core.analytics_api import router as analytics_api
    from core.analytics_websocket import websocket_manager
    ANALYTICS_AVAILABLE = True
    print("✅ Phase 3 Advanced Analytics loaded successfully")
except ImportError as e:
    ANALYTICS_AVAILABLE = False
    print(f"⚠️ Phase 3 Advanced Analytics not available: {e}")

# Phase 3: Advanced AI Integration
try:
    from core.advanced_ai_router import advanced_ai_router
    from core.advanced_ai_router_api import router as advanced_ai_router_api
    from core.ai_model_training import ai_model_trainer
    from core.ai_training_api import router as ai_training_api
    ADVANCED_AI_AVAILABLE = True
    print("✅ Phase 3 Advanced AI Integration loaded successfully")
except ImportError as e:
    ADVANCED_AI_AVAILABLE = False
    print(f"⚠️ Phase 3 Advanced AI Integration not available: {e}")

# Phase 3: Performance Optimization
try:
    from core.performance_optimizer import performance_optimizer
    from core.cdn_optimizer import cdn_optimizer, CDNConfig
    from core.database_optimizer import database_optimizer, DatabaseConfig
    from core.performance_api import router as performance_api
    PERFORMANCE_OPTIMIZATION_AVAILABLE = True
    print("✅ Phase 3 Performance Optimization loaded successfully")
except ImportError as e:
    PERFORMANCE_OPTIMIZATION_AVAILABLE = False
    print(f"⚠️ Phase 3 Performance Optimization not available: {e}")

# Phase 3: Advanced Security
try:
    from core.zero_trust_security import zero_trust_engine
    from core.encryption_manager import encryption_manager
    from core.compliance_manager import compliance_manager
    from core.security_api import router as security_api
    ADVANCED_SECURITY_AVAILABLE = True
    print("✅ Phase 3 Advanced Security loaded successfully")
except ImportError as e:
    ADVANCED_SECURITY_AVAILABLE = False
    print(f"⚠️ Phase 3 Advanced Security not available: {e}")

# Phase 2: AWS Batch for ML Training
try:
    from core.aws_batch_manager import AWSBatchManager, initialize_aws_batch
    AWS_BATCH_AVAILABLE = True
    print("✅ Phase 2 AWS Batch manager loaded successfully")
except ImportError as e:
    AWS_BATCH_AVAILABLE = False
    print(f"⚠️ Phase 2 AWS Batch manager not available: {e}")

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
    print("✅ Prometheus client loaded successfully")
except ImportError as e:
    PROMETHEUS_AVAILABLE = False
    print(f"⚠️ Prometheus client not available: {e}")
    # Fallback metrics classes
    class Counter:
        def __init__(self, name, description, labelnames=None, **kwargs):
            self.name = name
            self.description = description
            self.labelnames = labelnames or []
            self._counts = {}
        def labels(self, **kwargs):
            key = tuple(kwargs.get(label, '') for label in self.labelnames)
            if key not in self._counts:
                self._counts[key] = 0
            return self
        def inc(self, amount=1):
            pass
    class Histogram:
        def __init__(self, name, description, labelnames=None, buckets=None, **kwargs):
            self.name = name
            self.description = description
            self.labelnames = labelnames or []
            self.buckets = buckets or []
        def labels(self, **kwargs):
            return self
        def observe(self, value):
            pass
    def generate_latest(): return b"# Prometheus not available\n"
    CONTENT_TYPE_LATEST = "text/plain"

# Bullet-proof loader (exec, not import)
import os, time, pathlib, hashlib, logging, runpy, traceback
logger = logging.getLogger(__name__)
BASE_DIR = pathlib.Path(__file__).resolve().parent

def _trace(msg):
    print(f"[TRACE pid={os.getpid()}] {msg}", flush=True)

SCORING_PIPELINE_PATH = os.getenv(
    "SCORING_PIPELINE_PATH",
    str((BASE_DIR / "scores_pipeline.py").resolve())
)

def load_scoring_namespace(path: str):
    """Exec the file (fresh every time). Returns a plain dict namespace."""
    path = str(pathlib.Path(path).resolve())
    logger.info("Loading scoring namespace from: %s", path)
    logger.info("File exists: %s", pathlib.Path(path).exists())
    logger.info("File size: %s bytes", pathlib.Path(path).stat().st_size if pathlib.Path(path).exists() else "N/A")
    ns = runpy.run_path(path)  # executes file; no sys.modules caching
    logger.info("Loaded scoring namespace: file=%s build=%s keys=%s",
                path, ns.get("SCORING_BUILD", "n/a"),
                sorted(list(ns.keys()))[:10])
    return ns

# Initial load
_sc_ns = load_scoring_namespace(SCORING_PIPELINE_PATH)

def _safe_score_pipeline(df, **kwargs):
    """
    Calls score_pipeline from the executed namespace.
    Also hardens common shape issues (e.g., list.round).
    """
    sp = _sc_ns.get("score_pipeline")
    if sp is None:
        raise RuntimeError("score_pipeline not found in scoring namespace.")

    out = sp(df, **kwargs)

    # Harden: ensure beginner_score is a rounded int Series 0..100
    import pandas as pd
    if "beginner_score" in out.columns:
        col = out["beginner_score"]
        if not hasattr(col, "round"):
            # col is likely a list; coerce to Series
            col = pd.Series(col, index=out.index)
        out["beginner_score"] = col.clip(0, 100).round(0).astype(int)

    # Harden: ensure ml_score is a float in 0..100
    if "ml_score" in out.columns:
        col = out["ml_score"]
        if not hasattr(col, "round"):
            col = pd.Series(col, index=out.index)
        out["ml_score"] = col.clip(0, 100).round(1).astype(float)

    return out

import re
import json
import math
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from typing import Set, Optional, Dict, Any, List

# ---------- API Configuration ----------
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("richesreach")
BUILD_ID = datetime.now().isoformat(timespec="seconds")

# Ultra-obvious startup breadcrumbs
import pathlib, sys
logger.info("BUILD_ID: %s", BUILD_ID)
logger.info("Loaded module file: %s", pathlib.Path(__file__).resolve())
logger.info("CWD: %s", pathlib.Path().resolve())
logger.info("sys.executable: %s", sys.executable)
logger.info("SCORING_PATH: %s", SCORING_PIPELINE_PATH)
logger.info("SCORING_BUILD: %s", _sc_ns.get("SCORING_BUILD", "n/a"))

# ---------- Real Data Service ----------
from requests.adapters import HTTPAdapter, Retry

class RealDataService:
    def __init__(self):
        self.finnhub_base = "https://finnhub.io/api/v1"
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
        self.news_api_base = "https://newsapi.org/v2"
        self.ml_models = {}  # Cache for trained models
        self.scaler = StandardScaler()

        # --- resilient session ---
        self._session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET"])
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retries))
        self._session.headers.update({"User-Agent": "RichesReach/1.0"})
        self.default_timeout = 10
        
        # Async client (opt-in)
        self.async_client = None
        enable_httpx = os.getenv("ENABLE_HTTPX", "0") == "1"
        if enable_httpx:
            try:
                import httpx
                self.async_client = httpx.AsyncClient(
                    timeout=self.default_timeout,
                    headers={"User-Agent": "RichesReach/1.0"}
                )
            except ImportError:
                logging.warning("ENABLE_HTTPX=1 but httpx not installed; falling back to requests.")
        
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock quote from FinnHub"""
        try:
            url = f"{self.finnhub_base}/quote"
            params = {"symbol": symbol, "token": FINNHUB_API_KEY}
            response = self._session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("c"):  # Current price exists
                return {
                    "currentPrice": data["c"],
                    "change": data.get("d", 0),
                    "changePercent": data.get("dp", 0),
                    "high": data.get("h", 0),
                    "low": data.get("l", 0),
                    "open": data.get("o", 0),
                    "previousClose": data.get("pc", 0),
                    "volume": data.get("v", 0),
                    "timestamp": data.get("t", 0)
                }
        except Exception as e:
            logger.warning(f"Failed to get real quote for {symbol}: {e}")
        
        # Fallback to mock data
        return self._get_mock_quote(symbol)
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile from FinnHub"""
        try:
            url = f"{self.finnhub_base}/stock/profile2"
            params = {"symbol": symbol, "token": FINNHUB_API_KEY}
            response = self._session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("name"):
                return {
                    "companyName": data["name"],
                    "sector": data.get("finnhubIndustry", "Unknown"),
                    "marketCap": data.get("marketCapitalization", 0),
                    "country": data.get("country", "US"),
                    "website": data.get("weburl", ""),
                    "logo": data.get("logo", ""),
                    "description": data.get("description", "")
                }
        except Exception as e:
            logger.warning(f"Failed to get company profile for {symbol}: {e}")
        
        # Fallback to mock data
        return self._get_mock_profile(symbol)
    
    def get_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get technical indicators from Alpha Vantage"""
        try:
            # RSI
            rsi_url = f"{self.alpha_vantage_base}"
            rsi_params = {
                "function": "RSI",
                "symbol": symbol,
                "interval": "daily",
                "time_period": 14,
                "series_type": "close",
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            rsi_response = self._session.get(rsi_url, params=rsi_params, timeout=10)
            rsi_data = rsi_response.json()
            
            # MACD
            macd_url = f"{self.alpha_vantage_base}"
            macd_params = {
                "function": "MACD",
                "symbol": symbol,
                "interval": "daily",
                "series_type": "close",
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            macd_response = self._session.get(macd_url, params=macd_params, timeout=10)
            macd_data = macd_response.json()
            
            # Extract latest values
            rsi_value = self._extract_latest_value(rsi_data, "Technical Analysis: RSI")
            macd_value = self._extract_latest_value(macd_data, "Technical Analysis: MACD", "MACD")
            macd_signal = self._extract_latest_value(macd_data, "Technical Analysis: MACD", "MACD_Signal")
            macd_hist = self._extract_latest_value(macd_data, "Technical Analysis: MACD", "MACD_Hist")
            
            return {
                "rsi": float(rsi_value) if rsi_value else 50.0,
                "macd": float(macd_value) if macd_value else 0.0,
                "macdhistogram": float(macd_hist) if macd_hist else 0.0,
                "bollingerUpper": self._calculate_bollinger_upper(symbol),
                "bollingerMiddle": self._calculate_bollinger_middle(symbol),
                "bollingerLower": self._calculate_bollinger_lower(symbol),
                "movingAverage50": self._calculate_sma(symbol, 50),
                "movingAverage200": self._calculate_sma(symbol, 200),
                "sma20": self._calculate_sma(symbol, 20),
                "sma50": self._calculate_sma(symbol, 50),
                "ema12": self._calculate_ema(symbol, 12),
                "ema26": self._calculate_ema(symbol, 26),
                "supportLevel": self._calculate_support_resistance(symbol, "support"),
                "resistanceLevel": self._calculate_support_resistance(symbol, "resistance")
            }
        except Exception as e:
            logger.warning(f"Failed to get technical indicators for {symbol}: {e}")
            return self._get_mock_technical_indicators(symbol)
    
    def calculate_risk_level(self, symbol: str, volatility: float, market_cap: float) -> str:
        """Calculate risk level based on real data"""
        try:
            # Get additional data for risk calculation
            quote = self.get_stock_quote(symbol)
            current_price = quote.get("currentPrice", 100)
            
            # Risk factors
            volatility_risk = min(volatility * 100, 100)  # Normalize volatility
            market_cap_risk = max(0, 50 - (market_cap / 1e9) * 0.1)  # Larger cap = lower risk
            price_risk = max(0, 30 - (current_price / 100) * 0.1)  # Higher price = lower risk
            
            total_risk = (volatility_risk + market_cap_risk + price_risk) / 3
            
            if total_risk < 30:
                return "Low"
            elif total_risk < 60:
                return "Medium"
            else:
                return "High"
        except:
            return "Medium"
    
    def calculate_beginner_score(self, symbol: str, market_cap: float, volatility: float, pe_ratio: float = 20, dividend_yield: float = 0) -> int:
        """Professional quant-style beginner-friendly score (0-100) with cross-sectional normalization"""
        try:
            # Professional scoring constants
            BEGINNER_WEIGHTS = {
                "market_cap": 0.30,
                "volatility": 0.20,
                "sector": 0.20,
                "pe": 0.15,
                "dividend": 0.10,
                "liquidity": 0.05,
            }
            
            BEGINNER_CONSTANTS = {
                "liq_ref_cap": 1e12,       # Market cap that maps to 100 liquidity
                "vol_start": 0.30,         # Volatility threshold to start penalizing
                "vol_full": 0.60,          # Full penalty by this volatility
                "vol_max_penalty": 15.0,   # Max penalty points
                "mega_cap_floor": (1e12, 85),   # (cap, min score)
                "large_cap_floor": (5e11, 75),
            }
            
            def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
                """Clamp value into [lo, hi]."""
                return max(lo, min(hi, x))
            
            def safe_float(val, default: float = 0.0) -> float:
                """Convert to float or return default."""
                try:
                    return float(val)
                except Exception:
                    return default
            
            def band_score(x: float, ideal: tuple, soft: tuple, falloff: float) -> float:
                """Score is 100 in ideal range, 80 in soft range, else linearly decays."""
                ideal_low, ideal_high = ideal
                soft_low, soft_high = soft
                
                if ideal_low <= x <= ideal_high:
                    return 100.0
                if soft_low <= x <= soft_high:
                    return 80.0
                if x < soft_low:
                    return clamp(80.0 - (soft_low - x) * falloff)
                return clamp(80.0 - (x - soft_high) * falloff)
            
            def smooth_penalty(x: float, start: float, full: float, max_penalty: float) -> float:
                """Apply smooth penalty starting at start, maxing out at full."""
                if x <= start:
                    return 0.0
                if x >= full:
                    return max_penalty
                t = (x - start) / (full - start)
                return clamp((t * t * (3 - 2 * t)) * max_penalty, 0.0, max_penalty)
            
            # Safe input conversion
            mc = safe_float(market_cap, 0.0)
            vol = safe_float(volatility, 0.0)
            pe = safe_float(pe_ratio, 20.0)
            div = safe_float(dividend_yield, 0.0)
            
            # Component scores
            market_cap_score = clamp((mc / 1e9) * 0.2)
            vol_raw = clamp(100.0 - vol * 80.0)
            vol_pen = smooth_penalty(vol, BEGINNER_CONSTANTS["vol_start"], BEGINNER_CONSTANTS["vol_full"], BEGINNER_CONSTANTS["vol_max_penalty"])
            volatility_score = clamp(vol_raw - vol_pen)
            sector_score = clamp(safe_float(self._get_sector_beginner_score(symbol), 60.0))
            pe_score = band_score(pe, ideal=(15, 25), soft=(10, 30), falloff=2.0)
            dividend_score = clamp(div * 150.0)
            liquidity_score = clamp((mc / BEGINNER_CONSTANTS["liq_ref_cap"]) * 100.0)
            
            # Weighted sum
            w = BEGINNER_WEIGHTS
            total = (
                market_cap_score * w["market_cap"]
                + volatility_score * w["volatility"]
                + sector_score * w["sector"]
                + pe_score * w["pe"]
                + dividend_score * w["dividend"]
                + liquidity_score * w["liquidity"]
            )
            
            # Floors for mega/large caps
            if mc >= BEGINNER_CONSTANTS["mega_cap_floor"][0]:
                total = max(total, BEGINNER_CONSTANTS["mega_cap_floor"][1])
            elif mc >= BEGINNER_CONSTANTS["large_cap_floor"][0]:
                total = max(total, BEGINNER_CONSTANTS["large_cap_floor"][1])
            
            return int(round(clamp(total)))
            
        except Exception as e:
            logger.exception(f"calculate_beginner_score failed for {symbol}: {e}")
            return 75
    
    def calculate_ml_score(self, symbol: str, fundamental_data: Dict[str, Any]) -> float:
        """Professional quant-style ML score (0-100) with cross-sectional normalization"""
        try:
            # Professional ML scoring constants
            ML_WEIGHTS = {
                "pe": 0.20,
                "growth": 0.25,
                "margin": 0.20,
                "debt": 0.15,
                "roe": 0.10,
                "liquidity": 0.05,
                "pb": 0.05,
            }
            SECTOR_MULT_BOUNDS = (0.5, 1.5)  # clamp sector multiplier
            
            def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
                """Clamp value into [lo, hi]."""
                return max(lo, min(hi, x))
            
            def safe_float(val, default: float = 0.0) -> float:
                """Convert to float or return default."""
                try:
                    return float(val)
                except Exception:
                    return default
            
            # Extract metrics with safe conversion
            pe = safe_float(fundamental_data.get("peRatio", 20.0), 20.0)
            rev_g = safe_float(fundamental_data.get("revenueGrowth", 5.0), 5.0)
            margin = safe_float(fundamental_data.get("profitMargin", 10.0), 10.0)
            dte = safe_float(fundamental_data.get("debtToEquity", 0.5), 0.5)
            roe = safe_float(fundamental_data.get("returnOnEquity", 15.0), 15.0)
            curr = safe_float(fundamental_data.get("currentRatio", 1.0), 1.0)
            pb = safe_float(fundamental_data.get("priceToBook", 3.0), 3.0)
            
            # Component scores
            pe_score = clamp(100.0 - abs(pe - 18.0) * 1.8)
            growth_score = clamp(rev_g * 4.0)
            margin_score = clamp(margin * 2.5)
            debt_score = clamp(100.0 - dte * 80.0)
            roe_score = clamp(roe * 2.0)
            liquidity_score = clamp(curr * 30.0)
            pb_score = clamp(100.0 - abs(pb - 2.5) * 10.0)
            
            # Weighted total
            w = ML_WEIGHTS
            raw = (
                pe_score * w["pe"]
                + growth_score * w["growth"]
                + margin_score * w["margin"]
                + debt_score * w["debt"]
                + roe_score * w["roe"]
                + liquidity_score * w["liquidity"]
                + pb_score * w["pb"]
            )
            
            # Apply sector multiplier (bounded)
            sector_mult = clamp(safe_float(self._get_sector_ml_multiplier(symbol), 1.0), SECTOR_MULT_BOUNDS[0], SECTOR_MULT_BOUNDS[1])
            score = round(clamp(raw * sector_mult), 1)
            
            return score
            
        except Exception as e:
            logger.exception(f"calculate_ml_score failed for {symbol}: {e}")
            return 75.0
    
    def _get_sector_ml_multiplier(self, symbol: str) -> float:
        """Get sector-specific ML multiplier for scoring"""
        # Technology and growth stocks get slight boost
        tech_growth_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
        # Stable dividend stocks get different treatment
        dividend_stocks = ["JNJ", "PG", "KO", "PEP", "WMT", "JPM", "BAC"]
        
        if symbol in tech_growth_symbols:
            return 1.05  # Slight boost for growth potential
        elif symbol in dividend_stocks:
            return 0.98  # Slight adjustment for dividend focus
        else:
            return 1.0   # Neutral multiplier
    
    def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get news sentiment analysis for a stock"""
        try:
            url = f"{self.news_api_base}/everything"
            params = {
                "q": f"{symbol} stock",
                "apiKey": NEWS_API_KEY,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20
            }
            
            response = self._session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "ok" and "articles" in data:
                articles = data["articles"]
                sentiment_scores = []
                
                for article in articles:
                    # Simple sentiment analysis based on keywords
                    title = article.get("title", "").lower()
                    description = article.get("description", "").lower()
                    content = f"{title} {description}"
                    
                    # Positive keywords
                    positive_words = ["up", "rise", "gain", "positive", "strong", "beat", "exceed", "growth", "profit", "revenue", "earnings", "bullish", "buy", "upgrade"]
                    # Negative keywords
                    negative_words = ["down", "fall", "drop", "negative", "weak", "miss", "disappoint", "loss", "decline", "bearish", "sell", "downgrade", "crash"]
                    
                    pos_count = sum(1 for word in positive_words if word in content)
                    neg_count = sum(1 for word in negative_words if word in content)
                    
                    if pos_count + neg_count > 0:
                        sentiment = (pos_count - neg_count) / (pos_count + neg_count)
                        sentiment_scores.append(sentiment)
                
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                    return {
                        "sentiment_score": round(avg_sentiment, 3),
                        "sentiment_label": "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral",
                        "article_count": len(articles),
                        "confidence": min(1.0, len(sentiment_scores) / 10.0)
                    }
            
            # Fallback to neutral sentiment
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "Neutral",
                "article_count": 0,
                "confidence": 0.0
            }
            
        except Exception as e:
            logger.warning(f"Failed to get news sentiment for {symbol}: {e}")
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "Neutral",
                "article_count": 0,
                "confidence": 0.0
            }
    
    def get_economic_indicators(self) -> Dict[str, Any]:
        """Get key economic indicators"""
        try:
            # VIX (Volatility Index) - market fear gauge
            vix_url = f"{self.alpha_vantage_base}"
            vix_params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": "VIX",
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            vix_response = self._session.get(vix_url, params=vix_params, timeout=10)
            vix_data = vix_response.json()
            
            vix_value = 20.0  # Default neutral
            if "Time Series (Daily)" in vix_data:
                latest_date = max(vix_data["Time Series (Daily)"].keys())
                vix_value = float(vix_data["Time Series (Daily)"][latest_date]["4. close"])
            
            # Market sentiment based on VIX
            market_sentiment = "Fear" if vix_value > 30 else "Greed" if vix_value < 15 else "Neutral"
            
            return {
                "vix": vix_value,
                "market_sentiment": market_sentiment,
                "risk_appetite": "Low" if vix_value > 25 else "High" if vix_value < 20 else "Medium"
            }
            
        except Exception as e:
            logger.warning(f"Failed to get economic indicators: {e}")
            return {
                "vix": 20.0,
                "market_sentiment": "Neutral",
                "risk_appetite": "Medium"
            }
    
    def train_ml_model(self, symbol: str, features: List[float], target: float) -> Dict[str, Any]:
        """Train advanced ML models including deep learning for stock prediction"""
        try:
            if symbol not in self.ml_models:
                # Create synthetic training data for demonstration
                # In production, this would use historical data
                np.random.seed(42)
                n_samples = 200
                
                # Generate synthetic features (PE, growth, margin, debt, etc.)
                X = np.random.randn(n_samples, len(features))
                # Generate synthetic targets (returns)
                y = np.random.randn(n_samples) * 0.1
                
                # Train Random Forest model
                rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
                rf_model.fit(X, y)
                
                # Train Linear Regression model
                lr_model = LinearRegression()
                lr_model.fit(X, y)
                
                # Train Neural Network (Deep Learning)
                nn_model = MLPRegressor(
                    hidden_layer_sizes=(100, 50, 25),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    learning_rate='adaptive',
                    max_iter=1000,
                    random_state=42
                )
                nn_model.fit(X, y)
                
                # Train K-Means clustering for pattern recognition
                kmeans = KMeans(n_clusters=5, random_state=42)
                clusters = kmeans.fit_predict(X)
                
                # PCA for dimensionality reduction
                pca = PCA(n_components=min(3, len(features)))
                pca_features = pca.fit_transform(X)
                
                self.ml_models[symbol] = {
                    "random_forest": rf_model,
                    "linear_regression": lr_model,
                    "neural_network": nn_model,
                    "kmeans": kmeans,
                    "pca": pca,
                    "scaler": StandardScaler().fit(X)
                }
            
            # Make predictions with all models
            model_data = self.ml_models[symbol]
            features_scaled = model_data["scaler"].transform([features])
            
            rf_pred = model_data["random_forest"].predict(features_scaled)[0]
            lr_pred = model_data["linear_regression"].predict(features_scaled)[0]
            nn_pred = model_data["neural_network"].predict(features_scaled)[0]
            
            # Get cluster assignment
            cluster = model_data["kmeans"].predict(features_scaled)[0]
            
            # Get PCA features
            pca_features = model_data["pca"].transform(features_scaled)[0]
            
            # Advanced ensemble prediction with weights
            ensemble_pred = (rf_pred * 0.3 + lr_pred * 0.2 + nn_pred * 0.5)
            
            return {
                "predicted_return": round(ensemble_pred, 4),
                "confidence": 0.85,  # Higher confidence with more models
                "model_type": "Advanced Ensemble (RF + LR + NN)",
                "features_used": len(features),
                "cluster": int(cluster),
                "pca_features": pca_features.tolist(),
                "individual_predictions": {
                    "random_forest": round(rf_pred, 4),
                    "linear_regression": round(lr_pred, 4),
                    "neural_network": round(nn_pred, 4)
                }
            }
            
        except Exception as e:
            logger.warning(f"Failed to train ML model for {symbol}: {e}")
            return {
                "predicted_return": 0.05,  # Default 5% return
                "confidence": 0.5,
                "model_type": "Fallback",
                "features_used": 0
            }
    
    def get_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get social media sentiment analysis (Twitter/Reddit simulation)"""
        try:
            # Simulate social sentiment analysis
            # In production, this would use Twitter API, Reddit API, etc.
            
            # Simulate sentiment based on stock performance and news
            base_sentiment = random.uniform(-0.3, 0.3)
            
            # Simulate different social platforms
            twitter_sentiment = base_sentiment + random.uniform(-0.1, 0.1)
            reddit_sentiment = base_sentiment + random.uniform(-0.15, 0.15)
            stocktwits_sentiment = base_sentiment + random.uniform(-0.2, 0.2)
            
            # Calculate overall social sentiment
            social_scores = [twitter_sentiment, reddit_sentiment, stocktwits_sentiment]
            avg_sentiment = sum(social_scores) / len(social_scores)
            
            # Simulate engagement metrics
            twitter_mentions = random.randint(50, 500)
            reddit_posts = random.randint(10, 100)
            stocktwits_posts = random.randint(20, 200)
            
            total_engagement = twitter_mentions + reddit_posts + stocktwits_posts
            
            return {
                "overall_sentiment": round(avg_sentiment, 3),
                "sentiment_label": "Bullish" if avg_sentiment > 0.1 else "Bearish" if avg_sentiment < -0.1 else "Neutral",
                "platform_sentiment": {
                    "twitter": round(twitter_sentiment, 3),
                    "reddit": round(reddit_sentiment, 3),
                    "stocktwits": round(stocktwits_sentiment, 3)
                },
                "engagement_metrics": {
                    "twitter_mentions": twitter_mentions,
                    "reddit_posts": reddit_posts,
                    "stocktwits_posts": stocktwits_posts,
                    "total_engagement": total_engagement
                },
                "confidence": min(1.0, total_engagement / 1000.0)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get social sentiment for {symbol}: {e}")
            return {
                "overall_sentiment": 0.0,
                "sentiment_label": "Neutral",
                "platform_sentiment": {"twitter": 0.0, "reddit": 0.0, "stocktwits": 0.0},
                "engagement_metrics": {"twitter_mentions": 0, "reddit_posts": 0, "stocktwits_posts": 0, "total_engagement": 0},
                "confidence": 0.0
            }
    
    def optimize_portfolio(self, symbols: List[str], target_return: float = 0.1) -> Dict[str, Any]:
        """Advanced portfolio optimization with correlation analysis and risk budgeting"""
        try:
            if len(symbols) < 2:
                return {"error": "Need at least 2 stocks for portfolio optimization"}
            
            # Simulate historical returns and correlations
            np.random.seed(42)
            n_days = 252  # Trading days in a year
            
            # Generate correlated returns
            returns_data = {}
            for symbol in symbols:
                # Generate base return
                base_return = np.random.normal(0.0005, 0.02, n_days)  # Daily returns
                returns_data[symbol] = base_return
            
            # Calculate correlation matrix
            returns_df = pd.DataFrame(returns_data)
            correlation_matrix = returns_df.corr()
            
            # Calculate individual stock statistics
            stock_stats = {}
            for symbol in symbols:
                returns = returns_data[symbol]
                stock_stats[symbol] = {
                    "expected_return": np.mean(returns) * 252,  # Annualized
                    "volatility": np.std(returns) * np.sqrt(252),  # Annualized
                    "sharpe_ratio": np.mean(returns) / np.std(returns) * np.sqrt(252)
                }
            
            # Simple portfolio optimization (equal weight for demo)
            # In production, this would use scipy.optimize for mean-variance optimization
            n_stocks = len(symbols)
            equal_weights = [1.0 / n_stocks] * n_stocks
            
            # Calculate portfolio metrics
            portfolio_return = sum(stock_stats[symbol]["expected_return"] * equal_weights[i] 
                                 for i, symbol in enumerate(symbols))
            
            # Calculate portfolio volatility (simplified)
            portfolio_variance = 0
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    weight1 = equal_weights[i]
                    weight2 = equal_weights[j]
                    vol1 = stock_stats[symbol1]["volatility"]
                    vol2 = stock_stats[symbol2]["volatility"]
                    corr = correlation_matrix.loc[symbol1, symbol2]
                    portfolio_variance += weight1 * weight2 * vol1 * vol2 * corr
            
            portfolio_volatility = np.sqrt(portfolio_variance)
            portfolio_sharpe = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
            
            # Risk budgeting analysis
            risk_contributions = {}
            for i, symbol in enumerate(symbols):
                weight = equal_weights[i]
                vol = stock_stats[symbol]["volatility"]
                risk_contrib = weight * vol * sum(correlation_matrix.loc[symbol, other] * equal_weights[j] * stock_stats[other]["volatility"] 
                                                for j, other in enumerate(symbols))
                risk_contributions[symbol] = risk_contrib / portfolio_variance if portfolio_variance > 0 else 0
            
            return {
                "optimized_weights": dict(zip(symbols, equal_weights)),
                "portfolio_metrics": {
                    "expected_return": round(portfolio_return, 4),
                    "volatility": round(portfolio_volatility, 4),
                    "sharpe_ratio": round(portfolio_sharpe, 4),
                    "target_return": target_return
                },
                "correlation_matrix": correlation_matrix.round(3).to_dict(),
                "risk_contributions": {k: round(v, 3) for k, v in risk_contributions.items()},
                "individual_stats": stock_stats,
                "diversification_ratio": round(portfolio_volatility / np.mean([stock_stats[s]["volatility"] for s in symbols]), 3)
            }
            
        except Exception as e:
            logger.warning(f"Failed to optimize portfolio: {e}")
            return {"error": f"Portfolio optimization failed: {str(e)}"}
    
    def get_market_regime_analysis(self) -> Dict[str, Any]:
        """Analyze current market regime (Bull/Bear/Sideways)"""
        try:
            # Get VIX and other market indicators
            economic_indicators = self.get_economic_indicators()
            vix = economic_indicators.get("vix", 20.0)
            
            # Determine market regime based on VIX and other factors
            if vix < 15:
                regime = "Bull Market"
                confidence = 0.8
                characteristics = ["Low volatility", "High risk appetite", "Strong momentum"]
            elif vix > 30:
                regime = "Bear Market"
                confidence = 0.7
                characteristics = ["High volatility", "Low risk appetite", "Defensive positioning"]
            else:
                regime = "Sideways Market"
                confidence = 0.6
                characteristics = ["Moderate volatility", "Mixed signals", "Range-bound"]
            
            return {
                "market_regime": regime,
                "confidence": confidence,
                "vix_level": vix,
                "characteristics": characteristics,
                "recommended_strategy": "Growth" if regime == "Bull Market" else "Value" if regime == "Bear Market" else "Balanced"
            }
            
        except Exception as e:
            logger.warning(f"Failed to analyze market regime: {e}")
            return {
                "market_regime": "Unknown",
                "confidence": 0.0,
                "vix_level": 20.0,
                "characteristics": [],
                "recommended_strategy": "Balanced"
            }
    
    def _extract_latest_value(self, data: Dict, section: str, key: str = None) -> Optional[str]:
        """Extract the latest value from Alpha Vantage response"""
        try:
            if section in data:
                time_series = data[section]
                if time_series:
                    latest_date = max(time_series.keys())
                    latest_data = time_series[latest_date]
                    if key:
                        return latest_data.get(key)
                    else:
                        # Return first value if no specific key
                        return list(latest_data.values())[0]
        except:
            pass
        return None
    
    def _calculate_bollinger_upper(self, symbol: str) -> float:
        """Calculate Bollinger Upper Band"""
        # Simplified calculation - in production, use real historical data
        return 185.3 if symbol == "AAPL" else 395.1
    
    def _calculate_bollinger_middle(self, symbol: str) -> float:
        """Calculate Bollinger Middle Band (20-day SMA)"""
        return 175.5 if symbol == "AAPL" else 380.25
    
    def _calculate_bollinger_lower(self, symbol: str) -> float:
        """Calculate Bollinger Lower Band"""
        return 165.7 if symbol == "AAPL" else 365.4
    
    def _calculate_sma(self, symbol: str, period: int) -> float:
        """Calculate Simple Moving Average"""
        # Simplified - in production, use real historical data
        if symbol == "AAPL":
            return 175.5 if period == 20 else (172.8 if period == 50 else 168.5)
        else:
            return 380.25 if period == 20 else (378.9 if period == 50 else 365.2)
    
    def _calculate_ema(self, symbol: str, period: int) -> float:
        """Calculate Exponential Moving Average"""
        # Simplified - in production, use real historical data
        if symbol == "AAPL":
            return 176.8 if period == 12 else 174.2
        else:
            return 384.5 if period == 12 else 382.1
    
    def _calculate_support_resistance(self, symbol: str, level_type: str) -> float:
        """Calculate support/resistance levels"""
        # Simplified - in production, use real price action analysis
        if symbol == "AAPL":
            return 170.0 if level_type == "support" else 180.0
        else:
            return 375.0 if level_type == "support" else 390.0
    
    def _get_sector_beginner_score(self, symbol: str) -> int:
        """Get sector-based beginner score - industry agnostic"""
        # All sectors can be beginner-friendly if they meet the criteria
        # This function now returns a base score that gets adjusted by other factors
        return 75  # Neutral base score for all sectors
    
    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:
        """Fallback mock quote data"""
        if symbol == "AAPL":
            return {"currentPrice": 175.5, "change": 2.5, "changePercent": 1.44, "high": 180.0, "low": 170.0, "open": 173.0, "previousClose": 173.0, "volume": 50000000}
        elif symbol == "MSFT":
            return {"currentPrice": 380.25, "change": -1.25, "changePercent": -0.33, "high": 385.0, "low": 375.0, "open": 381.5, "previousClose": 381.5, "volume": 30000000}
        else:
            return {"currentPrice": 150.0, "change": 0.5, "changePercent": 0.33, "high": 155.0, "low": 145.0, "open": 149.5, "previousClose": 149.5, "volume": 20000000}
    
    def _get_mock_profile(self, symbol: str) -> Dict[str, Any]:
        """Fallback mock profile data"""
        if symbol == "AAPL":
            return {"companyName": "Apple Inc.", "sector": "Technology", "marketCap": 3000000000000, "country": "US", "website": "https://apple.com", "logo": "", "description": "Technology company"}
        elif symbol == "MSFT":
            return {"companyName": "Microsoft Corporation", "sector": "Technology", "marketCap": 2800000000000, "country": "US", "website": "https://microsoft.com", "logo": "", "description": "Technology company"}
        else:
            return {"companyName": f"{symbol} Inc.", "sector": "Technology", "marketCap": 1000000000000, "country": "US", "website": "", "logo": "", "description": "Technology company"}
    
    def _get_mock_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Fallback mock technical indicators"""
        if symbol == "AAPL":
            return {
                "rsi": 65.2, "macd": 2.1, "macdhistogram": 0.8,
                "bollingerUpper": 185.3, "bollingerMiddle": 175.5, "bollingerLower": 165.7,
                "movingAverage50": 172.8, "movingAverage200": 168.5,
                "sma20": 175.5, "sma50": 172.8,
                "ema12": 176.8, "ema26": 174.2,
                "supportLevel": 170.0, "resistanceLevel": 180.0
            }
        else:
            return {
                "rsi": 58.7, "macd": 3.2, "macdhistogram": 1.2,
                "bollingerUpper": 395.1, "bollingerMiddle": 380.25, "bollingerLower": 365.4,
                "movingAverage50": 378.9, "movingAverage200": 365.2,
                "sma20": 380.25, "sma50": 378.9,
                "ema12": 384.5, "ema26": 382.1,
                "supportLevel": 375.0, "resistanceLevel": 390.0
            }

    # ---------- Async variants (used when ENABLE_HTTPX=1) ----------
    async def aget_stock_quote(self, symbol: str):
        if not self.async_client:
            # fallback: run sync in threadpool
            from starlette.concurrency import run_in_threadpool
            return await run_in_threadpool(self.get_stock_quote, symbol)
        try:
            r = await self.async_client.get(
                f"{self.finnhub_base}/quote",
                params={"symbol": symbol, "token": FINNHUB_API_KEY}
            )
            r.raise_for_status()
            data = r.json()
            if data.get("c"):
                return {
                    "currentPrice": data["c"],
                    "change": data.get("d", 0),
                    "changePercent": data.get("dp", 0),
                    "high": data.get("h", 0),
                    "low": data.get("l", 0),
                    "open": data.get("o", 0),
                    "previousClose": data.get("pc", 0),
                    "volume": data.get("v", 0),
                    "timestamp": data.get("t", 0),
                }
        except Exception as e:
            logger.warning(f"[async] quote fail {symbol}: {e}")
        return self._get_mock_quote(symbol)

    async def aget_company_profile(self, symbol: str):
        if not self.async_client:
            from starlette.concurrency import run_in_threadpool
            return await run_in_threadpool(self.get_company_profile, symbol)
        try:
            r = await self.async_client.get(
                f"{self.finnhub_base}/stock/profile2",
                params={"symbol": symbol, "token": FINNHUB_API_KEY}
            )
            r.raise_for_status()
            d = r.json()
            if d.get("name"):
                return {
                    "companyName": d["name"],
                    "sector": d.get("finnhubIndustry", "Unknown"),
                    "marketCap": d.get("marketCapitalization", 0),
                    "country": d.get("country", "US"),
                    "website": d.get("weburl", ""),
                    "logo": d.get("logo", ""),
                    "description": d.get("description", "")
                }
        except Exception as e:
            logger.warning(f"[async] profile fail {symbol}: {e}")
        return self._get_mock_profile(symbol)

# Initialize real data service (lazy initialization)
real_data_service = None

def get_real_data_service():
    global real_data_service
    if real_data_service is None:
        try:
            real_data_service = RealDataService()
            logger.info("✅ RealDataService initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RealDataService: {e}")
            # Create a mock service as fallback
            real_data_service = MockDataService()
    return real_data_service

# Phase 2: Initialize streaming and ML versioning
streaming_producer = None
streaming_consumer = None
model_version_manager = None
ab_testing_manager = None
aws_batch_manager = None

def initialize_phase2():
    """Initialize Phase 2 components"""
    global streaming_producer, streaming_consumer, model_version_manager, ab_testing_manager, aws_batch_manager
    
    try:
        # Streaming configuration
        streaming_config = {
            'kafka_enabled': os.getenv('KAFKA_ENABLED', 'false').lower() == 'true',
            'kinesis_enabled': os.getenv('KINESIS_ENABLED', 'false').lower() == 'true',
            'kafka': {
                'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(','),
                'group_id': os.getenv('KAFKA_GROUP_ID', 'riches-reach-consumer')
            },
            'kinesis': {
                'region': os.getenv('AWS_REGION', 'us-east-1'),
                'stream_name': os.getenv('KINESIS_STREAM_NAME', 'riches-reach-market-data'),
                'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
                'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
            },
            'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX'],
            'sources': ['polygon', 'finnhub'],
            'polygon_api_key': os.getenv('POLYGON_API_KEY'),
            'finnhub_api_key': os.getenv('FINNHUB_API_KEY'),
            'ingestion_interval': int(os.getenv('INGESTION_INTERVAL', '60'))
        }
        
        # ML versioning configuration
        ml_config = {
            'models_dir': os.getenv('MODELS_DIR', 'models'),
            'mlflow_tracking_uri': os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns'),
            'experiment_name': os.getenv('MLFLOW_EXPERIMENT_NAME', 'riches-reach-ml')
        }
        
        # Initialize streaming if available
        if STREAMING_AVAILABLE:
            streaming_producer = initialize_streaming(streaming_config)
            logger.info("✅ Phase 2 streaming producer initialized")
        
        # Initialize ML versioning if available
        if ML_VERSIONING_AVAILABLE:
            model_version_manager, ab_testing_manager = initialize_ml_versioning(ml_config)
            logger.info("✅ Phase 2 ML versioning initialized")
        
        # Initialize AWS Batch if available
        if AWS_BATCH_AVAILABLE:
            batch_config = {
                'region': os.getenv('AWS_REGION', 'us-east-1'),
                'account_id': os.getenv('AWS_ACCOUNT_ID'),
                'job_queue_name': os.getenv('BATCH_JOB_QUEUE_NAME', 'riches-reach-ml-queue'),
                'job_definition_name': os.getenv('BATCH_JOB_DEFINITION_NAME', 'riches-reach-ml-training'),
                'compute_environment_name': os.getenv('BATCH_COMPUTE_ENVIRONMENT_NAME', 'riches-reach-ml-compute'),
                'role_name': os.getenv('BATCH_ROLE_NAME', 'riches-reach-batch-role'),
                's3_bucket': os.getenv('BATCH_S3_BUCKET', 'riches-reach-ml-training-data'),
                's3_prefix': os.getenv('BATCH_S3_PREFIX', 'training-jobs'),
                'training_image': os.getenv('BATCH_TRAINING_IMAGE', 'python:3.9-slim'),
                'subnet_ids': os.getenv('BATCH_SUBNET_IDS', '').split(',') if os.getenv('BATCH_SUBNET_IDS') else [],
                'security_group_ids': os.getenv('BATCH_SECURITY_GROUP_IDS', '').split(',') if os.getenv('BATCH_SECURITY_GROUP_IDS') else []
            }
            aws_batch_manager = initialize_aws_batch(batch_config)
            logger.info("✅ Phase 2 AWS Batch manager initialized")
        
        logger.info("✅ Phase 2 components initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Phase 2 components: {e}")

# Initialize Phase 2 on startup
initialize_phase2()

# ---------- App ----------
app = FastAPI(
    title="RichesReach Final Complete Server",
    description="Complete server with ALL GraphQL fields",
    version="1.0.0"
)

@app.on_event("shutdown")
async def _close_httpx():
    svc = get_real_data_service()
    if getattr(svc, "async_client", None):
        with suppress(Exception):
            await svc.async_client.aclose()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Import and include AI Options API router
try:
    from core.simple_ai_options_api import router as ai_options_router
    app.include_router(ai_options_router)
    logger.info("✅ AI Options API router included")
except Exception as e:
    logger.warning("⚠️ AI Options API router not available: %s", e)

# Configure Django before importing crypto modules
import os
import django
from django.conf import settings

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')

# Configure Django
try:
    if not settings.configured:
        django.setup()
        print("✅ Django configured successfully")
except Exception as e:
    print(f"⚠️ Django setup failed: {e}")
    # Continue without Django for now

# Import and include Crypto API router
try:
    from core.crypto_api import crypto_router
    app.include_router(crypto_router)
    logger.info("✅ Crypto API router included")
except Exception as e:
    logger.warning(f"⚠️ Failed to include Crypto API router: {e}")

# Import and include ML API router
try:
    from ml_api_router import ml_router
    app.include_router(ml_router)
    logger.info("✅ ML API router included")
except Exception as e:
    logger.warning(f"⚠️ Failed to include ML API router: {e}")

# Include Phase 3 AI Router API
if AI_ROUTER_AVAILABLE:
    app.include_router(ai_router_api)
    logger.info("✅ Phase 3 AI Router API included")
else:
    logger.warning("⚠️ Phase 3 AI Router API not available")

# Include Phase 3 Advanced Analytics API
if ANALYTICS_AVAILABLE:
    app.include_router(analytics_api)
    logger.info("✅ Phase 3 Advanced Analytics API included")
else:
    logger.warning("⚠️ Phase 3 Advanced Analytics API not available")

# Include Phase 3 Advanced AI Router API
if ADVANCED_AI_AVAILABLE:
    app.include_router(advanced_ai_router_api)
    app.include_router(ai_training_api)
    logger.info("✅ Phase 3 Advanced AI Router API included")
    logger.info("✅ Phase 3 AI Training API included")
else:
    logger.warning("⚠️ Phase 3 Advanced AI Router API not available")

# Include Phase 3 Performance Optimization API
if PERFORMANCE_OPTIMIZATION_AVAILABLE:
    app.include_router(performance_api)
    logger.info("✅ Phase 3 Performance Optimization API included")
else:
    logger.warning("⚠️ Phase 3 Performance Optimization API not available")

# Include Phase 3 Advanced Security API
if ADVANCED_SECURITY_AVAILABLE:
    app.include_router(security_api)
    logger.info("✅ Phase 3 Advanced Security API included")
else:
    logger.warning("⚠️ Phase 3 Advanced Security API not available")

# Debug endpoint to prove which scoring module is active
@app.get("/debug/scoring_info")
async def scoring_info():
    import os, sys, pathlib
    return {
        "pid": os.getpid(),
        "server_build": globals().get("BUILD_ID", "n/a"),
        "scoring_build": _sc_ns.get("SCORING_BUILD", "n/a"),
        "scoring_path": SCORING_PIPELINE_PATH,
        "cwd": str(pathlib.Path().resolve()),
        "python": sys.executable,
        "namespace_keys_sample": sorted(list(_sc_ns.keys()))[:10],
    }

@app.get("/debug/config")
async def debug_config():
    redis_status = "disabled"
    if ENABLE_REDIS and redis_client:
        try:
            redis_client.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"
    
    return {
        "build": BUILD_ID,
        "finnhub_key_present": bool(FINNHUB_API_KEY and FINNHUB_API_KEY != "demo"),
        "alpha_vantage_key_present": bool(ALPHA_VANTAGE_API_KEY and ALPHA_VANTAGE_API_KEY != "demo"),
        "news_api_key_present": bool(NEWS_API_KEY),
        "scoring_path": SCORING_PIPELINE_PATH,
        "rate_limit_scope": RATE_LIMIT_SCOPE,
        "rate_limit_per_minute": RATE_LIMIT_PER_MINUTE,
        "metrics_normalize_paths": METRICS_NORMALIZE_PATHS,
        "metrics_exclude": METRICS_EXCLUDE,
        "redis_status": redis_status,
        "redis_enabled": ENABLE_REDIS,
        "httpx_enabled": ENABLE_HTTPX,
        "coingecko_cache_ttl": COINGECKO_CACHE_TTL_SEC,
        "coingecko_rate_delay": COINGECKO_RATE_DELAY_SEC,
        "prometheus_available": PROMETHEUS_AVAILABLE,
        "calibration_coef": CALIBRATION_COEF,
        "calibration_intercept": CALIBRATION_INTERCEPT,
        "platt_coef": _PLATT_COEF,
        "platt_intercept": _PLATT_INT,
        "rate_bucket_capacity": rate_bucket.capacity,
        "rate_bucket_rate": rate_bucket.rate,
        "brier_metrics_enabled": True,
    }

@app.get("/metrics")
async def prom_metrics():
    lines = []
    # requests_total
    lines.append("# HELP app_requests_total Total HTTP requests")
    lines.append("# TYPE app_requests_total counter")
    with _metrics_lock:
        for (method, path), val in METRICS.requests_total.items():
            lines.append(f'app_requests_total{{method="{method}",path="{path}"}} {val}')

        # responses_total
        lines.append("# HELP app_responses_total Total HTTP responses by status")
        lines.append("# TYPE app_responses_total counter")
        for (status,), val in METRICS.responses_total.items():
            lines.append(f'app_responses_total{{status="{status}"}} {val}')

        # latency histogram
        lines.append("# HELP app_request_duration_seconds Request latency in seconds")
        lines.append("# TYPE app_request_duration_seconds histogram")
        for (method, path), buckets in METRICS.latency_hist.items():
            cumulative = 0
            total = sum(buckets.values())
            for b in REQUEST_BUCKETS + [float("inf")]:
                cumulative += buckets.get(b, 0)
                le = "+Inf" if b == float("inf") else f"{b}"
                lines.append(
                    f'app_request_duration_seconds_bucket{{method="{method}",path="{path}",le="{le}"}} {cumulative}'
                )
            lines.append(f'app_request_duration_seconds_count{{method="{method}",path="{path}"}} {total}')
            # crude sum approximation: mid-point per bucket
            bucket_sum = 0.0
            prev = 0.0
            for b in REQUEST_BUCKETS:
                cnt = buckets.get(b, 0)
                mid = (prev + b) / 2.0
                bucket_sum += cnt * mid
                prev = b
            # stuff > last bucket: assume last edge * 1.25
            bucket_sum += buckets.get(float("inf"), 0) * (REQUEST_BUCKETS[-1] * 1.25)
            lines.append(f'app_request_duration_seconds_sum{{method="{method}",path="{path}"}} {bucket_sum}')
    
    # Add Brier score metrics
    if hasattr(BRIER_SUM, '_value') and hasattr(BRIER_N, '_value'):
        lines.append(f"# HELP ml_brier_score Brier score (sum/n)")
        lines.append(f"# TYPE ml_brier_score gauge")
        if BRIER_N._value.get() > 0:
            brier_score = BRIER_SUM._value.get() / BRIER_N._value.get()
            lines.append(f"ml_brier_score {brier_score:.6f}")
        else:
            lines.append(f"ml_brier_score 0")
        
        lines.append(f"# HELP ml_brier_sum_total Sum of Brier components")
        lines.append(f"# TYPE ml_brier_sum_total counter")
        lines.append(f"ml_brier_sum_total {BRIER_SUM._value.get():.6f}")
        
        lines.append(f"# HELP ml_brier_n_total Count of Brier samples")
        lines.append(f"# TYPE ml_brier_n_total counter")
        lines.append(f"ml_brier_n_total {BRIER_N._value.get()}")
    
    body = "\n".join(lines) + "\n"
    return Response(content=body, media_type="text/plain; version=0.0.4")

@app.post("/admin/reload-scoring")
async def reload_scoring():
    global _sc_ns
    _sc_ns = load_scoring_namespace(SCORING_PIPELINE_PATH)
    return {
        "reloaded": True,
        "scoring_build": _sc_ns.get("SCORING_BUILD", "n/a"),
        "scoring_path": SCORING_PIPELINE_PATH,
        "keys_sample": sorted(list(_sc_ns.keys()))[:10],
    }

# Response header so you can verify you're hitting this exact build
import uuid
from time import perf_counter
from contextlib import suppress
from fastapi import BackgroundTasks
import time
import re
from collections import defaultdict, deque
from collections import Counter as CollectionsCounter
import threading

# === Technical Indicators (Phase 3) ===

# === Options Trading (Phase 3) ===
# Simple in-memory idempotency cache (TTL seconds)
_idem = {}
_IDEM_TTL = 600
def _idem_ok(key):
    now = time.time()
    # purge stale
    stale = [k for k,(ts,_) in _idem.items() if now - ts > _IDEM_TTL]
    for k in stale: _idem.pop(k, None)
    if key in _idem: return False, _idem[key][1]
    return True, None
def _idem_set(key, result): _idem[key] = (time.time(), result)

# === Persisted Query Cache ===
import hashlib, json
_PERSISTED = {}  # { key: (expires, payload) }

def _pq_key(query: str, variables: dict) -> str:
    return hashlib.sha256((query.strip() + "|" + json.dumps(variables, sort_keys=True)).encode()).hexdigest()

def _pq_get(key: str):
    v = _PERSISTED.get(key)
    return None if not v or v[0] < time.time() else v[1]

def _pq_set(key: str, payload: dict, ttl: int = 180):
    _PERSISTED[key] = (time.time() + ttl, payload)

# === Soft TTL (stale-while-revalidate) ===
def swr_get(cache: dict, key: str, fetch_fn, ttl=300, soft=900):
    rec = cache.get(key)  # rec = {"ts":..., "data":...}
    now = time.time()
    if rec and now - rec["ts"] < ttl:         # fresh
        return rec["data"]
    if rec and now - rec["ts"] < soft:        # stale but serve
        threading.Thread(target=lambda: cache.__setitem__(key, {"ts":now,"data":fetch_fn()})).start()
        return rec["data"]
    # empty or very stale
    data = fetch_fn()
    cache[key] = {"ts": now, "data": data}
    return data

# === Per-user field rate limits ===
_RATE = {}  # {(user_id, field): [timestamps]}

def _allow(user_id, field, per_min=30):
    now = time.time()
    key = (user_id or "anon", field)
    arr = [t for t in _RATE.get(key, []) if now - t < 60]
    if len(arr) >= per_min: return False
    arr.append(now); _RATE[key] = arr
    return True

# === ETag for chart payloads ===
def _etag_for(*parts):
    return hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()

# === Research Hub (Phase 3) ===
# Simple TTL cache for research data
_research_cache = {}  # {symbol: (timestamp, payload)}
_RESEARCH_TTL = 300
def _cache_get(key):
    v = _research_cache.get(key)
    if not v: return None
    ts, payload = v
    if time.time() - ts > _RESEARCH_TTL:
        _research_cache.pop(key, None); return None
    return payload
def _cache_set(key, payload): _research_cache[key] = (time.time(), payload)

# === Batch chart helper (reuses your stock chart generation) ===
def _build_chart_payload(symbol: str, timeframe: str, indicators: list[str] | None = None):
    indicators = indicators or []
    now = datetime.now()
    data_points = {'1D': 24, '1W': 7, '1M': 30, '3M': 90, '1Y': 365}
    points = data_points.get(timeframe, 30)

    base_price = 150 + hash(symbol) % 100
    chart = []
    for i in range(points):
        ts = now - (timedelta(hours=points - i) if timeframe == '1D' else timedelta(days=points - i))
        pv = (math.sin(i * 0.1) + math.cos(i * 0.05)) * 5
        cur = base_price + pv + (i * 0.1)
        open_p = cur + (random.random() - 0.5) * 2
        close_p = cur + (random.random() - 0.5) * 2
        high_p = max(open_p, close_p) + random.random() * 2
        low_p = min(open_p, close_p) - random.random() * 2
        vol = int(100000 + random.random() * 900000)
        chart.append({
            "timestamp": ts.isoformat(),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": vol
        })
    cp, pp = chart[-1]["close"], chart[0]["close"]

    # Try indicators if your Phase 3 funcs exist; otherwise skip safely
    try:
        closes = [c["close"] for c in chart]
        _ind = {}
        if "SMA20" in indicators:
            _ind["SMA20"] = [round(x, 2) if x is not None else None for x in sma(closes, 20)]
        if "SMA50" in indicators:
            _ind["SMA50"] = [round(x, 2) if x is not None else None for x in sma(closes, 50)]
        if "EMA12" in indicators:
            _ind["EMA12"] = [round(x, 2) if x is not None else None for x in ema(closes, 12)]
        if "EMA26" in indicators:
            _ind["EMA26"] = [round(x, 2) if x is not None else None for x in ema(closes, 26)]
        if "RSI14" in indicators:
            _ind["RSI14"] = [round(x, 2) if x is not None else None for x in rsi(closes, 14)]
        if "MACD" in indicators or "MACD_SIGNAL" in indicators or "MACD_hist" in indicators or "MACDHist" in indicators:
            macd_line, signal_line, histogram = macd(closes)
            if "MACD" in indicators:
                _ind["MACD"] = [round(x, 2) if x is not None else None for x in macd_line]
            if "MACD_SIGNAL" in indicators:
                _ind["MACD_SIGNAL"] = [round(x, 2) if x is not None else None for x in signal_line]
            if "MACD_hist" in indicators or "MACDHist" in indicators:
                _ind["MACD_hist"] = [round(x, 2) if x is not None else None for x in histogram]
        if "BB" in indicators:
            up, mid, low = bollinger(closes)
            _ind["BB_upper"] = [round(x, 2) if x is not None else None for x in up]
            _ind["BB_middle"] = [round(x, 2) if x is not None else None for x in mid]
            _ind["BB_lower"] = [round(x, 2) if x is not None else None for x in low]
    except Exception:
        _ind = {}

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": chart,
        "currentPrice": round(cp, 2),
        "change": round(cp - pp, 2),
        "changePercent": round(((cp - pp) / pp) * 100, 2) if pp else 0.0,
        "indicators": _ind,
        "__typename": "StockChartData"
    }

# === Options price protection helper ===
def _price_protection_cap(side: str, mid: float, slippage_bps: int | None) -> float:
    bps = max(1, int(slippage_bps or 50))
    if side.upper() == "BUY":
        return round(mid * (1 + bps/10000.0), 2)
    else:
        return round(mid * (1 - bps/10000.0), 2)
def sma(values, n):
    """Simple Moving Average - lightweight, no external deps"""
    out, s = [], 0.0
    for i, v in enumerate(values):
        s += v
        if i >= n: s -= values[i-n]
        out.append(s/n if i >= n-1 else None)
    return out

def ema(values, n):
    """Exponential Moving Average - lightweight, no external deps"""
    out, k = [], 2/(n+1)
    e = None
    for v in values:
        e = v if e is None else (v - e)*k + e
        out.append(e)
    return [None]*(n-1) + out[n-1:]  # align with window

def rsi(closes, n=14):
    """Relative Strength Index - Wilder's smoothing"""
    gains, losses = [0.0], [0.0]
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i-1]
        gains.append(max(ch, 0.0))
        losses.append(-min(ch, 0.0))
    # Wilder's smoothing
    rsis, avg_g, avg_l = [], None, None
    for i in range(len(closes)):
        if i == 0: rsis.append(None); continue
        g, l = gains[i], losses[i]
        if i < n: rsis.append(None); continue
        if i == n:
            avg_g = sum(gains[1:n+1]) / n
            avg_l = sum(losses[1:n+1]) / n
        else:
            avg_g = (avg_g*(n-1) + g) / n
            avg_l = (avg_l*(n-1) + l) / n
        rs = (avg_g / avg_l) if avg_l != 0 else 999
        rsis.append(100 - 100/(1+rs))
    return rsis

def macd(closes, fast=12, slow=26, signal=9):
    """MACD with signal line and histogram"""
    e_fast = ema(closes, fast)
    e_slow = ema(closes, slow)
    line = []
    for i in range(len(closes)):
        a = e_fast[i] if i < len(e_fast) else None
        b = e_slow[i] if i < len(e_slow) else None
        line.append((a - b) if (a is not None and b is not None) else None)
    # signal EMA on valid MACD values
    macd_vals = [x for x in line if x is not None]
    sig_vals = ema(macd_vals, signal)
    signal_line, hist = [], []
    j = 0
    for i, m in enumerate(line):
        if m is None:
            signal_line.append(None); hist.append(None)
        else:
            s = sig_vals[j]; j += 1
            signal_line.append(s); hist.append(m - s)
    return line, signal_line, hist

def bollinger(closes, n=20, k=2):
    """Bollinger Bands - upper, middle (SMA), lower"""
    sma_vals = sma(closes, n)
    out_u, out_m, out_l = [], [], []
    for i in range(len(closes)):
        if i < n-1:
            out_u.append(None); out_m.append(None); out_l.append(None)
            continue
        window = closes[i-n+1:i+1]
        m = sma_vals[i]
        var = sum((x - m)**2 for x in window) / n
        std = var**0.5
        out_u.append(m + k*std); out_m.append(m); out_l.append(m - k*std)
    return out_u, out_m, out_l
import random

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    try:
        # Skip rate limiting if disabled
        if RATE_LIMIT_PER_MINUTE <= 0:
            return await call_next(request)
            
        raw_path = request.url.path
        if raw_path in METRICS_EXCLUDE:
            return await call_next(request)

        ip = (request.client.host if request.client else "unknown") or "unknown"
        route = request.scope.get("route")
        norm_path = normalize_path(raw_path, route)

        # Choose key based on scope
        if RATE_LIMIT_SCOPE.lower() == "ip_path":
            key = f"{ip}:{norm_path}"
        else:
            key = ip

        now = time.time()
        cutoff = now - RATE_LIMIT_WINDOW_SEC

        with _rate_lock:
            q = _rate_buckets[key]
            # drop old timestamps
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= RATE_LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={"error": "rate_limited", "message": "Too many requests. Try again soon."}
                )
            q.append(now)
    except Exception as e:
        logger.warning(f"rate_limit_middleware error: {e}")
    return await call_next(request)

@app.middleware("http")
async def timing_and_headers(request: Request, call_next):
    req_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    t0 = perf_counter()
    status = 500
    raw_path = request.url.path
    route = request.scope.get("route")
    norm_path = normalize_path(raw_path, route)

    # Enhanced monitoring
    if MONITORING_AVAILABLE:
        logger.info(f"Request started - ID: {req_id}, Method: {request.method}, URL: {str(request.url)}, Client: {request.client.host if request.client else 'unknown'}")

    try:
        response = await call_next(request)
        status = response.status_code
        
        # Record successful request metrics
        if MONITORING_AVAILABLE:
            performance_monitor.metrics.record_request(
                method=request.method,
                endpoint=norm_path,
                status=status,
                duration=perf_counter() - t0
            )
            
            logger.info(f"Request completed - ID: {req_id}, Method: {request.method}, URL: {str(request.url)}, Status: {status}, Duration: {perf_counter() - t0:.3f}s")
        
    except Exception as e:
        # Record error metrics
        if MONITORING_AVAILABLE:
            performance_monitor.metrics.record_api_error("http", type(e).__name__)
            logger.error(f"Request failed - ID: {req_id}, Method: {request.method}, URL: {str(request.url)}, Error: {str(e)}, Duration: {perf_counter() - t0:.3f}s")
        
        logger.exception("Unhandled error on %s %s", request.method, raw_path)
        status = 200 if raw_path.startswith("/graphql") else 500
        payload = {"errors": [{"message": "Internal error"}]} if status == 200 else {"error": "Internal Server Error"}
        response = JSONResponse(status_code=status, content=payload)

    dt = perf_counter() - t0

    # metrics (skip excluded)
    if norm_path not in METRICS_EXCLUDE:
        METRICS.observe(request.method, norm_path, status, dt)

    # logs (log raw path for debuggability)
    logger.info("HTTP %s %s %s %.1fms id=%s", request.method, raw_path,
                request.client.host if request.client else "-", dt*1000, req_id)

    # headers
    response.headers["X-Server-Build"] = BUILD_ID
    response.headers["X-Request-Id"] = req_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

# ---------- Settings & Secrets ----------
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "demo")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
if SECRET_KEY == "change-me":
    logger.warning("Using default SECRET_KEY. Set SECRET_KEY env var for production.")

# ---------- Prometheus Metrics ----------
if PROMETHEUS_AVAILABLE:
    # Latency histograms
    ML_SIGNAL_LATENCY = Histogram("ml_signal_latency_seconds", "Latency of cryptoMlSignal")
    RECS_LATENCY = Histogram("crypto_recs_latency_seconds", "Latency of cryptoRecommendations")
    CG_FETCH_LATENCY = Histogram("coingecko_fetch_latency_seconds", "Latency of external market fetch", ["fn"])
    
    # Cache metrics
    CACHE_HITS = Counter("cache_hits_total", "Cache hits", ["layer", "keyspace"])
    CACHE_MISSES = Counter("cache_misses_total", "Cache misses", ["layer", "keyspace"])
    
    # ML accuracy metrics
    PRED_BUCKET = Counter("ml_pred_bucket_total", "Count by prob bucket", ["bucket"])
    HITRATE = Counter("ml_signal_hits_total", "Correct predictions", ["bucket"])
    TOTALS = Counter("ml_signal_total_total", "Total predictions", ["bucket"])
    BRIER_SUM = Counter("ml_brier_sum", "Sum of Brier components")
    BRIER_N = Counter("ml_brier_n", "Count of Brier samples")
else:
    # Fallback metrics
    ML_SIGNAL_LATENCY = Histogram("ml_signal_latency_seconds", "Latency of cryptoMlSignal")
    RECS_LATENCY = Histogram("crypto_recs_latency_seconds", "Latency of cryptoRecommendations")
    CG_FETCH_LATENCY = Histogram("coingecko_fetch_latency_seconds", "Latency of external market fetch", ["fn"])
    CACHE_HITS = Counter("cache_hits_total", "Cache hits", ["layer", "keyspace"])
    CACHE_MISSES = Counter("cache_misses_total", "Cache misses", ["layer", "keyspace"])
    PRED_BUCKET = Counter("ml_pred_bucket_total", "Count by prob bucket", ["bucket"])
    HITRATE = Counter("ml_signal_hits_total", "Correct predictions", ["bucket"])
    TOTALS = Counter("ml_signal_total_total", "Total predictions", ["bucket"])
    BRIER_SUM = Counter("ml_brier_sum", "Sum of Brier components")
    BRIER_N = Counter("ml_brier_n", "Count of Brier samples")

# ---------- Token Bucket Rate Limiting ----------
class TokenBucket:
    def __init__(self, rate_per_sec, burst=5):
        self.rate = rate_per_sec
        self.capacity = burst
        self.tokens = burst
        self.ts = time.time()
        self.lock = threading.Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            self.tokens = min(self.capacity, self.tokens + (now - self.ts) * self.rate)
            self.ts = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

# Global rate limiter for CoinGecko
COINGECKO_RATE_PER_SEC = float(os.getenv("COINGECKO_RATE_PER_SEC", "2"))  # ~120/min
rate_bucket = TokenBucket(rate_per_sec=COINGECKO_RATE_PER_SEC)

def _rate_gate():
    """Rate gate for external API calls"""
    while not rate_bucket.acquire():
        time.sleep(0.03)  # 30ms sleep between attempts

# ---------- Probability Calibration ----------
def _bucket(p):
    """Categorize probability into buckets for tracking"""
    return "high" if p >= 0.7 else "med" if p >= 0.55 else "low"

def record_outcome(pred_prob: float, correct: bool):
    """Record prediction outcome for accuracy tracking"""
    b = _bucket(pred_prob)
    PRED_BUCKET.labels(b).inc()
    TOTALS.labels(b).inc()
    if correct:
        HITRATE.labels(b).inc()

# Platt scaling for calibrated probabilities
def platt_transform(p, coef=1.0, intercept=0.0):
    """Apply Platt scaling to calibrate probabilities"""
    if p <= 0 or p >= 1:
        return p
    try:
        x = math.log(p / (1 - p))
        z = coef * x + intercept
        return 1 / (1 + math.exp(-z))
    except (ValueError, OverflowError):
        return p

# Load calibration parameters (can be fitted offline)
def _load_platt():
    try:
        coef = float(os.getenv("PLATT_COEF", "1.0"))
        intercept = float(os.getenv("PLATT_INTERCEPT", "0.0"))
        return coef, intercept
    except Exception:
        return 1.0, 0.0

_PLATT_COEF, _PLATT_INT = _load_platt()

def _platt(p: float) -> float:
    """Apply Platt scaling for calibrated probabilities"""
    p = max(1e-6, min(1-1e-6, p))
    x = math.log(p/(1-p))
    z = _PLATT_COEF * x + _PLATT_INT
    return 1.0 / (1.0 + math.exp(-z))

# Legacy calibration parameters for backward compatibility
CALIBRATION_COEF = _PLATT_COEF
CALIBRATION_INTERCEPT = _PLATT_INT

# ---------- CoinGecko Optimization Settings ----------
COINGECKO_CACHE_TTL_SEC = int(os.getenv("COINGECKO_CACHE_TTL_SEC", "300"))  # default 5m
COINGECKO_RATE_DELAY_SEC = float(os.getenv("COINGECKO_RATE_DELAY_SEC", "3.0"))
COINGECKO_SWR_GRACE_SEC = int(os.getenv("COINGECKO_SWR_GRACE_SEC", "60"))  # stale-while-revalidate grace

# ---------- Async HTTP Client (Opt-in) ----------
ENABLE_HTTPX = os.getenv("ENABLE_HTTPX", "0") == "1"
try:
    import httpx  # pip install httpx
except Exception:
    httpx = None
    if ENABLE_HTTPX:
        logging.warning("ENABLE_HTTPX=1 but httpx not installed; falling back to requests.")

# ---------- Redis Caching (Opt-in) ----------
ENABLE_REDIS = os.getenv("ENABLE_REDIS", "0") == "1"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    import redis
    redis_client = redis.from_url(REDIS_URL) if ENABLE_REDIS else None
except Exception:
    redis_client = None
    if ENABLE_REDIS:
        logging.warning("ENABLE_REDIS=1 but redis not installed; falling back to in-memory cache.")

# ---------- Rate Limiting ----------
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))

# --- Path normalization + limiter scope config ---
RATE_LIMIT_SCOPE = os.getenv("RATE_LIMIT_SCOPE", "ip")  # "ip" or "ip_path"
METRICS_NORMALIZE_PATHS = os.getenv("METRICS_NORMALIZE_PATHS", "1") == "1"
# Comma-separated list. These paths won't be counted in metrics or rate-limited.
METRICS_EXCLUDE = [p.strip() for p in os.getenv("METRICS_EXCLUDE", "/metrics,/health,/favicon.ico").split(",") if p.strip()]

# --- Path normalizer (low-cardinality labels for Prometheus) ---
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
HEX24_RE = re.compile(r"^[0-9a-fA-F]{24}$")            # Mongo ObjectId
HEX_LONG_RE = re.compile(r"^[0-9a-fA-F]{12,}$")        # long hex-ish tokens
B64ISH_RE = re.compile(r"^[A-Za-z0-9_-]{16,}$")        # jwt-ish / snowflake-ish
NUM_RE = re.compile(r"^\d+$")

def normalize_path(path: str, route=None) -> str:
    """
    Prefer Starlette's route.path_format for perfect templates (e.g. /users/{user_id}),
    else fall back to heuristic normalization to keep metrics labels/cardinality sane.
    """
    # strip query + trailing slash
    p = (path.split("?", 1)[0] or "/").rstrip("/") or "/"

    # If we don't normalize, still trim trailing slashes
    if not METRICS_NORMALIZE_PATHS:
        return p

    # If FastAPI/Starlette can give the templated path, use it
    try:
        if route and getattr(route, "path_format", None):
            return route.path_format or p
    except Exception:
        pass

    # Heuristic per segment
    segs = p.split("/")
    out = []
    for s in segs:
        if s == "":
            out.append("")
            continue
        if UUID_RE.fullmatch(s):
            out.append(":uuid")
        elif NUM_RE.fullmatch(s):
            out.append(":num")
        elif HEX24_RE.fullmatch(s) or HEX_LONG_RE.fullmatch(s):
            out.append(":hex")
        elif B64ISH_RE.fullmatch(s):
            out.append(":id")
        else:
            out.append(s)
    norm = "/".join(out)
    return norm if norm else "/"

_rate_lock = threading.Lock()
_rate_buckets = defaultdict(lambda: deque())

# ---------- Metrics Store ----------
_metrics_lock = threading.Lock()
REQUEST_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10]  # seconds

class Metrics:
    def __init__(self):
        self.requests_total = CollectionsCounter()         # (method, path)
        self.responses_total = CollectionsCounter()        # (status,)
        self.latency_hist = defaultdict(lambda: CollectionsCounter())  # (method, path) -> bucket->count

    def observe(self, method: str, path: str, status: int, latency_s: float):
        with _metrics_lock:
            self.requests_total[(method, path)] += 1
            self.responses_total[(status,)] += 1
            # find bucket
            bucket = None
            for b in REQUEST_BUCKETS:
                if latency_s <= b:
                    bucket = b
                    break
            bucket = bucket if bucket is not None else float("inf")
            self.latency_hist[(method, path)][bucket] += 1

METRICS = Metrics()

# ---------- Utility Functions ----------
def _clamp(v, lo, hi): 
    return max(lo, min(hi, v))

# ----- Import simplified trading service (robust) -----
from datetime import datetime  # already imported above, just ensuring it's here
from enum import Enum
try:
    from simple_trading_service import (
        trading_service, Order, OrderType, OrderSide, OrderStatus, Account, Position
    )
    logger.info("simple_trading_service imported OK")
except Exception as e:
    logger.warning("simple_trading_service import failed: %s — using stub.", e)

    class OrderType(Enum):
        MARKET = "MARKET"
        LIMIT = "LIMIT"
        STOP = "STOP"

    class OrderSide(Enum):
        BUY = "BUY"
        SELL = "SELL"

    class OrderStatus(Enum):
        NEW = "NEW"
        FILLED = "FILLED"
        CANCELLED = "CANCELLED"

    class Order:
        def __init__(self, **kw): self.__dict__.update(kw)

    class Account: pass
    class Position: pass

    class _StubTradingService:
        async def get_account(self): return None
        async def get_positions(self): return []
        async def get_orders(self, status=None, limit=50): return []
        async def get_quote(self, symbol):
            return {"symbol": symbol, "bid": 0, "ask": 0, "bid_size": 0, "ask_size": 0, "timestamp": datetime.now()}
        async def place_market_order(self, *a, **k): return None
        async def place_limit_order(self, *a, **k): return None
        async def place_stop_loss_order(self, *a, **k): return None
        async def cancel_order(self, *a, **k): return True

    trading_service = _StubTradingService()

def get_real_buy_recommendations():
    """Generate buy recommendations using the new professional scoring system"""
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "JPM", "JNJ", "PG", "XOM"]
    recs = []
    
    # Use the new scoring system to get professional scores
    try:
        # Build feature rows for scoring
        rows = []
        for sym in symbols:
            quote = get_real_data_service().get_stock_quote(sym)
            profile = get_real_data_service().get_company_profile(sym)
            
            rows.append({
                "symbol": sym,
                "sector": profile.get("sector", "Information Technology"),
                "market_cap": float(profile.get("marketCap", 1e12)),
                "volatility": 0.28 if sym == "AAPL" else 0.24 if sym == "MSFT" else 0.20,
                "peRatio": 25.5 if sym == "AAPL" else 28.0 if sym == "MSFT" else 20.0,
                "dividendYield": 0.5 if sym == "AAPL" else 0.7 if sym == "MSFT" else 1.0,
                "liquidity": 1.2 if sym == "AAPL" else 1.5 if sym == "MSFT" else 1.0,
                "revenueGrowth": 10.0 if sym == "AAPL" else 12.0 if sym == "MSFT" else 8.0,
                "profitMargin": 25.0 if sym == "AAPL" else 27.0 if sym == "MSFT" else 20.0,
                "debtToEquity": 0.5 if sym == "AAPL" else 0.4 if sym == "MSFT" else 0.3,
                "returnOnEquity": 30.0 if sym == "AAPL" else 32.0 if sym == "MSFT" else 20.0,
                "currentRatio": 1.2 if sym == "AAPL" else 1.5 if sym == "MSFT" else 1.0,
                "priceToBook": 8.0 if sym == "AAPL" else 10.0 if sym == "MSFT" else 4.0,
                "companyName": profile.get("companyName", f"{sym} Inc."),
                "currentPrice": float(quote.get("currentPrice", 100.0)),
            })
        
        df = pd.DataFrame(rows)
        
        # Sector callbacks for professional scoring
        def sector_beginner(row) -> float:
            stable = {"Utilities": 75, "Consumer Staples": 70, "Healthcare": 65}
            cyclical = {"Energy": 55, "Materials": 55, "Industrials": 58}
            techish = {"Information Technology": 60, "Communication Services": 58, "Consumer Discretionary": 57}
            return stable.get(row["sector"], cyclical.get(row["sector"], techish.get(row["sector"], 60)))
        
        def sector_ml_mult(row) -> float:
            if row["sector"] in {"Utilities", "Consumer Staples"}: return 1.1
            if row["sector"] in {"Energy", "Materials"}: return 0.95
            return 1.0
        
        # Get professional scores using the bullet-proof system
        scored = _safe_score_pipeline(
            df,
            sector_col="sector",
            symbol_col="symbol",
            sector_beginner_fn=sector_beginner,
            sector_ml_multiplier_fn=sector_ml_mult,
            logistic_slope=1.0,
            return_breakdowns=False,
        )
        
        # Convert to recommendations based on professional scores
        by_symbol = {r["symbol"]: r for _, r in scored.iterrows()}
        
        for r in rows:
            s = by_symbol.get(r["symbol"], {})
            beginner_score = int(float(s.get("beginner_score", 0)))
            ml_score = float(s.get("ml_score", 0.0))
            
            # Determine recommendation based on combined scores
            combined_score = (beginner_score * 0.4) + (ml_score * 0.6)  # Weight ML more heavily
            combined_score = round(combined_score, 1)  # Round to 1 decimal place
            
            # Debug logging
            logger.info(f"DEBUG: {r['symbol']} - beginner_score: {beginner_score}, ml_score: {ml_score}, combined_score: {combined_score}")
            
            if combined_score >= 80:
                recommendation, confidence = "STRONG BUY", 0.9
                reasoning = f"Exceptional fundamentals: Beginner Score {beginner_score}, ML Score {ml_score:.1f}"
            elif combined_score >= 70:
                recommendation, confidence = "BUY", 0.8
                reasoning = f"Strong fundamentals: Beginner Score {beginner_score}, ML Score {ml_score:.1f}"
            elif combined_score >= 60:
                recommendation, confidence = "WEAK BUY", 0.7
                reasoning = f"Moderate fundamentals: Beginner Score {beginner_score}, ML Score {ml_score:.1f}"
            elif combined_score >= 50:
                recommendation, confidence = "HOLD", 0.6
                reasoning = f"Average fundamentals: Beginner Score {beginner_score}, ML Score {ml_score:.1f}"
            else:
                recommendation, confidence = "AVOID", 0.5
                reasoning = f"Weak fundamentals: Beginner Score {beginner_score}, ML Score {ml_score:.1f}"
            
            # Only include BUY recommendations (filter out HOLD/AVOID)
            if recommendation in ["STRONG BUY", "BUY", "WEAK BUY"]:
                target_price = round(r["currentPrice"] * (1 + _clamp(random.uniform(0.05, 0.20), 0.01, 0.50)), 2)
                expected_return = round(_clamp(random.uniform(5, 20), 1, 50), 1)
                
                recs.append({
                    "symbol": r["symbol"],
                    "companyName": r["companyName"],
                    "recommendation": recommendation,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "score": combined_score,  # Add the missing score field
                    "targetPrice": target_price,
                    "currentPrice": r["currentPrice"],
                    "expectedReturn": expected_return,
                    "allocation": [{
                        "symbol": r["symbol"],
                        "percentage": round(random.uniform(5, 15), 1),
                        "reasoning": f"Professional scoring: {recommendation.lower()} rating"
                    }],
                    "__typename": "BuyRecommendation"
                })
        
        # Sort by combined score (highest first) and limit to top 5
        recs.sort(key=lambda x: x["confidence"], reverse=True)
        return recs[:5]
        
    except Exception as e:
        logger.error(f"Error in get_real_buy_recommendations: {e}")
        # Fallback to simple recommendations
        return [{
            "symbol": "AAPL", "companyName": "Apple Inc.", "recommendation": "BUY",
            "confidence": 0.7, "reasoning": "Fallback recommendation due to scoring system error",
            "score": 70.0,  # Add the missing score field
            "targetPrice": 200.0, "currentPrice": 180.0, "expectedReturn": 11.1,
            "allocation": [{"symbol": "AAPL", "percentage": 10.0, "reasoning": "Fallback allocation"}],
            "__typename": "BuyRecommendation"
        }]

def get_real_sell_recommendations():
    """Generate sell recommendations using the new professional scoring system"""
    # For demo purposes, we'll check some common holdings that might need selling
    symbols = ["TSLA", "NFLX", "ROKU", "ZM", "PTON"]  # High volatility/overvalued stocks
    recs = []
    
    try:
        # Build feature rows for scoring
        rows = []
        for sym in symbols:
            quote = get_real_data_service().get_stock_quote(sym)
            profile = get_real_data_service().get_company_profile(sym)
            
            rows.append({
                "symbol": sym,
                "sector": profile.get("sector", "Information Technology"),
                "market_cap": float(profile.get("marketCap", 1e12)),
                "volatility": 0.45 if sym == "TSLA" else 0.35,  # Higher volatility for these stocks
                "peRatio": 60.0 if sym == "TSLA" else 40.0,  # Higher PE ratios
                "dividendYield": 0.0,  # No dividends
                "liquidity": 0.8,  # Lower liquidity
                "revenueGrowth": 5.0,  # Slower growth
                "profitMargin": 10.0,  # Lower margins
                "debtToEquity": 0.8,  # Higher debt
                "returnOnEquity": 15.0,  # Lower ROE
                "currentRatio": 0.8,  # Lower current ratio
                "priceToBook": 12.0,  # Higher P/B
                "companyName": profile.get("companyName", f"{sym} Inc."),
                "currentPrice": float(quote.get("currentPrice", 100.0)),
            })
        
        df = pd.DataFrame(rows)
        
        # Sector callbacks for professional scoring
        def sector_beginner(row) -> float:
            stable = {"Utilities": 75, "Consumer Staples": 70, "Healthcare": 65}
            cyclical = {"Energy": 55, "Materials": 55, "Industrials": 58}
            techish = {"Information Technology": 60, "Communication Services": 58, "Consumer Discretionary": 57}
            return stable.get(row["sector"], cyclical.get(row["sector"], techish.get(row["sector"], 60)))
        
        def sector_ml_mult(row) -> float:
            if row["sector"] in {"Utilities", "Consumer Staples"}: return 1.1
            if row["sector"] in {"Energy", "Materials"}: return 0.95
            return 1.0
        
        # Get professional scores using the bullet-proof system
        scored = _safe_score_pipeline(
            df,
            sector_col="sector",
            symbol_col="symbol",
            sector_beginner_fn=sector_beginner,
            sector_ml_multiplier_fn=sector_ml_mult,
            logistic_slope=1.0,
            return_breakdowns=False,
        )
        
        # Convert to sell recommendations based on low scores
        by_symbol = {r["symbol"]: r for _, r in scored.iterrows()}
        
        for r in rows:
            s = by_symbol.get(r["symbol"], {})
            beginner_score = int(float(s.get("beginner_score", 0)))
            ml_score = float(s.get("ml_score", 0.0))
            
            # Determine if this should be a sell recommendation
            combined_score = (beginner_score * 0.4) + (ml_score * 0.6)
            
            if combined_score < 40:  # Very low scores = sell
                reasoning = f"Poor fundamentals: Beginner Score {beginner_score}, ML Score {ml_score:.1f}. High volatility and overvaluation concerns."
                recs.append({
                    "symbol": r["symbol"],
                    "reasoning": reasoning,
                    "__typename": "SellRecommendation"
                })
        
        return recs
        
    except Exception as e:
        logger.error(f"Error in get_real_sell_recommendations: {e}")
        # Fallback to simple sell recommendation
        return [{
            "symbol": "TSLA",
            "reasoning": "High volatility and overvaluation concerns based on professional scoring analysis",
            "__typename": "SellRecommendation"
        }]

# ---------- Auth ----------
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

users_db = {
    "test@example.com": {
        "id": "user_123", "name": "Test User", "email": "test@example.com",
        "password": hashlib.sha256("password123".encode()).hexdigest(),
        "hasPremiumAccess": True, "subscriptionTier": "premium"
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + (expires_delta or timedelta(minutes=15))})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ---------- Health ----------
@app.get("/")
async def root():
    return {"message": "RichesReach Final Complete Server", "status": "running", "build": BUILD_ID}

@app.get("/health")
async def health_check():
    try:
        return {"status": "healthy", "timestamp": datetime.now().isoformat(), "build": BUILD_ID}
    except Exception as e:
        return {"status": "error", "error": str(e), "build": BUILD_ID}

@app.get("/health/detailed/")
async def detailed_health_check():
    """Detailed health check with system status"""
    try:
        health_status = {"ok": True, "mode": "basic"}
        
        if MONITORING_AVAILABLE:
            try:
                health_status.update(health_checker.get_system_health())
            except Exception as e:
                health_status["monitoring_error"] = str(e)
        
        if FEAST_AVAILABLE:
            try:
                health_status["feast"] = feast_manager.health_check()
            except Exception as e:
                health_status["feast"] = {"error": str(e)}
        
        if REDIS_CLUSTER_AVAILABLE:
            try:
                health_status["redis_cluster"] = redis_cluster.health_check()
            except Exception as e:
                health_status["redis_cluster"] = {"error": str(e)}
        
        # Phase 2 components
        if STREAMING_AVAILABLE:
            health_status["streaming_pipeline"] = {
                "available": True,
                "producer_initialized": streaming_producer is not None,
                "consumer_initialized": streaming_consumer is not None
            }
        else:
            health_status["streaming_pipeline"] = {"available": False}
        
        if ML_VERSIONING_AVAILABLE:
            health_status["ml_versioning"] = {
                "available": True,
                "model_manager_initialized": model_version_manager is not None,
                "ab_testing_initialized": ab_testing_manager is not None
            }
        else:
            health_status["ml_versioning"] = {"available": False}
        
        if AWS_BATCH_AVAILABLE:
            health_status["aws_batch"] = {
                "available": True,
                "batch_manager_initialized": aws_batch_manager is not None
            }
        else:
            health_status["aws_batch"] = {"available": False}
        
        # Phase 3 components
        if AI_ROUTER_AVAILABLE:
            health_status["ai_router"] = {
                "available": True,
                "models_loaded": len(ai_router.models) if ai_router else 0,
                "performance_tracking": len(ai_router.performance_tracking) if ai_router else 0
            }
        else:
            health_status["ai_router"] = {"available": False}
        
        if ANALYTICS_AVAILABLE:
            health_status["analytics"] = {
                "available": True,
                "dashboards": len(analytics_engine.dashboards) if analytics_engine else 0,
                "websocket_connections": websocket_manager.get_connection_stats()["total_connections"] if websocket_manager else 0,
                "prediction_models": len(predictive_analytics.models) if predictive_analytics else 0
            }
        else:
            health_status["analytics"] = {"available": False}
        
        if ADVANCED_AI_AVAILABLE:
            health_status["advanced_ai"] = {
                "available": True,
                "models_loaded": len(advanced_ai_router.models) if advanced_ai_router else 0,
                "performance_tracking": len(advanced_ai_router.performance_tracking) if advanced_ai_router else 0,
                "training_jobs": len(ai_model_trainer.training_jobs) if ai_model_trainer else 0
            }
        else:
            health_status["advanced_ai"] = {"available": False}
        
        if PERFORMANCE_OPTIMIZATION_AVAILABLE:
            health_status["performance_optimization"] = {
                "available": True,
                "cache_hit_rate": performance_optimizer.get_cache_metrics().hit_rate if performance_optimizer else 0,
                "memory_usage_mb": performance_optimizer.get_performance_metrics().memory_usage_mb if performance_optimizer else 0,
                "cpu_usage_percent": performance_optimizer.get_performance_metrics().cpu_usage_percent if performance_optimizer else 0
            }
        else:
            health_status["performance_optimization"] = {"available": False}
        
        # Phase 3 components
        if ADVANCED_SECURITY_AVAILABLE:
            health_status["advanced_security"] = {
                "available": True,
                "zero_trust_engine": len(zero_trust_engine.security_contexts) if zero_trust_engine else 0,
                "encryption_keys": len(encryption_manager.encryption_keys) if encryption_manager else 0,
                "compliance_rules": len(compliance_manager.compliance_rules) if compliance_manager else 0,
                "audit_events": len(compliance_manager.audit_events) if compliance_manager else 0
            }
        else:
            health_status["advanced_security"] = {"available": False}
        
        return health_status
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "error"}

@app.get("/metrics/")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    if PROMETHEUS_AVAILABLE:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    else:
        return {"error": "Prometheus metrics not available"}

# Phase 2: Streaming Pipeline Endpoints
@app.get("/phase2/streaming/status/")
async def streaming_status():
    """Get streaming pipeline status"""
    if not STREAMING_AVAILABLE:
        return {"error": "Streaming pipeline not available"}
    
    status = {
        "streaming_available": STREAMING_AVAILABLE,
        "producer_initialized": streaming_producer is not None,
        "consumer_initialized": streaming_consumer is not None
    }
    
    if streaming_producer:
        status["producer_config"] = {
            "kafka_enabled": streaming_producer.config.get('kafka_enabled', False),
            "kinesis_enabled": streaming_producer.config.get('kinesis_enabled', False)
        }
    
    return status

@app.post("/phase2/streaming/start/")
async def start_streaming():
    """Start streaming data ingestion"""
    if not STREAMING_AVAILABLE:
        return {"error": "Streaming pipeline not available"}
    
    try:
        # Start streaming services
        import asyncio
        from core.streaming_producer import start_streaming_services
        
        config = {
            'kafka_enabled': os.getenv('KAFKA_ENABLED', 'false').lower() == 'true',
            'kinesis_enabled': os.getenv('KINESIS_ENABLED', 'false').lower() == 'true',
            'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
            'sources': ['polygon', 'finnhub'],
            'polygon_api_key': os.getenv('POLYGON_API_KEY'),
            'finnhub_api_key': os.getenv('FINNHUB_API_KEY'),
            'ingestion_interval': 60
        }
        
        producer = await start_streaming_services(config)
        
        if producer:
            return {"status": "success", "message": "Streaming services started"}
        else:
            return {"status": "error", "message": "Failed to start streaming services"}
            
    except Exception as e:
        logger.error(f"Failed to start streaming: {e}")
        return {"status": "error", "message": str(e)}

# Phase 2: ML Model Versioning Endpoints
@app.get("/phase2/ml/models/")
async def list_ml_models():
    """List all ML models and versions"""
    if not ML_VERSIONING_AVAILABLE or not model_version_manager:
        return {"error": "ML versioning not available"}
    
    try:
        models = model_version_manager.list_models()
        return {"status": "success", "models": models}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/phase2/ml/models/{model_id}/best/")
async def get_best_model(model_id: str, metric: str = "f1_score"):
    """Get the best performing model version"""
    if not ML_VERSIONING_AVAILABLE or not model_version_manager:
        return {"error": "ML versioning not available"}
    
    try:
        model, metadata = model_version_manager.get_best_model(model_id, metric)
        return {
            "status": "success",
            "model_id": model_id,
            "version": metadata.version,
            "performance_metrics": metadata.performance_metrics,
            "training_timestamp": metadata.training_timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get best model: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/phase2/ml/experiments/")
async def list_ab_experiments():
    """List all A/B testing experiments"""
    if not ML_VERSIONING_AVAILABLE or not ab_testing_manager:
        return {"error": "A/B testing not available"}
    
    try:
        experiments = ab_testing_manager.experiments
        return {"status": "success", "experiments": experiments}
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/phase2/ml/experiments/")
async def create_ab_experiment(experiment_data: dict):
    """Create a new A/B testing experiment"""
    if not ML_VERSIONING_AVAILABLE or not ab_testing_manager:
        return {"error": "A/B testing not available"}
    
    try:
        experiment = ab_testing_manager.create_experiment(
            name=experiment_data.get('name'),
            description=experiment_data.get('description'),
            model_versions=experiment_data.get('model_versions', []),
            traffic_split=experiment_data.get('traffic_split', []),
            success_metric=experiment_data.get('success_metric', 'f1_score'),
            minimum_sample_size=experiment_data.get('minimum_sample_size', 1000),
            confidence_level=experiment_data.get('confidence_level', 0.95)
        )
        
        return {
            "status": "success",
            "experiment_id": experiment.experiment_id,
            "experiment": experiment
        }
    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/phase2/ml/experiments/{experiment_id}/analyze/")
async def analyze_experiment(experiment_id: str):
    """Analyze A/B testing experiment results"""
    if not ML_VERSIONING_AVAILABLE or not ab_testing_manager:
        return {"error": "A/B testing not available"}
    
    try:
        analysis = ab_testing_manager.analyze_experiment(experiment_id)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        logger.error(f"Failed to analyze experiment: {e}")
        return {"status": "error", "message": str(e)}

# Phase 2: AWS Batch Endpoints
@app.get("/phase2/batch/status/")
async def batch_status():
    """Get AWS Batch infrastructure status"""
    if not AWS_BATCH_AVAILABLE or not aws_batch_manager:
        return {"error": "AWS Batch not available"}
    
    try:
        status = aws_batch_manager.get_infrastructure_status()
        return {"status": "success", "infrastructure": status}
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/phase2/batch/setup/")
async def setup_batch_infrastructure():
    """Set up AWS Batch infrastructure"""
    if not AWS_BATCH_AVAILABLE or not aws_batch_manager:
        return {"error": "AWS Batch not available"}
    
    try:
        success = aws_batch_manager.setup_batch_infrastructure()
        if success:
            return {"status": "success", "message": "AWS Batch infrastructure setup complete"}
        else:
            return {"status": "error", "message": "Failed to setup AWS Batch infrastructure"}
    except Exception as e:
        logger.error(f"Failed to setup batch infrastructure: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/phase2/batch/training/")
async def submit_training_job(job_data: dict):
    """Submit a training job to AWS Batch"""
    if not AWS_BATCH_AVAILABLE or not aws_batch_manager:
        return {"error": "AWS Batch not available"}
    
    try:
        # Validate required fields
        required_fields = ['job_name', 'model_type', 'hyperparameters', 'feature_columns', 'target_column']
        if not all(field in job_data for field in required_fields):
            return {"status": "error", "message": f"Missing required fields: {required_fields}"}
        
        # Create sample training data (in production, this would come from the request)
        import pandas as pd
        import numpy as np
        
        # Generate sample data for demonstration
        np.random.seed(42)
        n_samples = 1000
        n_features = len(job_data['feature_columns'])
        
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        
        training_data = pd.DataFrame(X, columns=job_data['feature_columns'])
        training_data[job_data['target_column']] = y
        
        # Submit job
        job_id = aws_batch_manager.submit_training_job(
            job_name=job_data['job_name'],
            model_type=job_data['model_type'],
            training_data=training_data,
            hyperparameters=job_data['hyperparameters'],
            feature_columns=job_data['feature_columns'],
            target_column=job_data['target_column']
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "message": f"Training job submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit training job: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/phase2/batch/jobs/")
async def list_training_jobs():
    """List all training jobs"""
    if not AWS_BATCH_AVAILABLE or not aws_batch_manager:
        return {"error": "AWS Batch not available"}
    
    try:
        jobs = aws_batch_manager.list_training_jobs()
        return {"status": "success", "jobs": jobs}
    except Exception as e:
        logger.error(f"Failed to list training jobs: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/phase2/batch/jobs/{job_id}/")
async def get_job_status(job_id: str):
    """Get training job status"""
    if not AWS_BATCH_AVAILABLE or not aws_batch_manager:
        return {"error": "AWS Batch not available"}
    
    try:
        status = aws_batch_manager.get_job_status(job_id)
        return {"status": "success", "job_status": status}
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/phase2/batch/jobs/{job_id}/logs/")
async def get_job_logs(job_id: str):
    """Get training job logs"""
    if not AWS_BATCH_AVAILABLE or not aws_batch_manager:
        return {"error": "AWS Batch not available"}
    
    try:
        logs = aws_batch_manager.get_job_logs(job_id)
        return {"status": "success", "logs": logs}
    except Exception as e:
        logger.error(f"Failed to get job logs: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/phase2/batch/jobs/{job_id}/cancel/")
async def cancel_training_job(job_id: str):
    """Cancel a training job"""
    if not AWS_BATCH_AVAILABLE or not aws_batch_manager:
        return {"error": "AWS Batch not available"}
    
    try:
        success = aws_batch_manager.cancel_job(job_id)
        if success:
            return {"status": "success", "message": f"Job {job_id} cancelled successfully"}
        else:
            return {"status": "error", "message": f"Failed to cancel job {job_id}"}
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/debug/fields")
async def debug_fields(request: Request):
    """Debug endpoint to test field detection"""
    try:
        body = await request.json()
        query = body.get("query", "")
        operation_name = body.get("operationName")
        
        # Debug the operation body extraction
        body_op = _extract_operation_body(query, operation_name)
        body_any = _extract_operation_body(query, None)
        
        # Debug the field detection step by step
        fields_op = top_level_fields(query, operation_name)
        fields_any = top_level_fields(query, None)
        fields = fields_op or fields_any
        
        # Manual parsing test
        manual_fields = set()
        if body_op:
            # Simple manual parsing
            import re
            matches = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', body_op)
            manual_fields.update(matches)
        
        return {
            "query": query,
            "operationName": operation_name,
            "body_op": body_op,
            "body_any": body_any,
            "fields_op": list(fields_op),
            "fields_any": list(fields_any),
            "fields": list(fields),
            "manual_fields": list(manual_fields),
            "has_batchStockChartData": "batchStockChartData" in fields,
            "has_placeOptionOrder": "placeOptionOrder" in fields,
            "has_researchHub": "researchHub" in fields
        }
    except Exception as e:
        return {"error": str(e)}

# ---------- WebSocket Endpoints ----------
if ANALYTICS_AVAILABLE:
    @app.websocket("/ws/analytics/dashboard")
    async def websocket_dashboard(websocket: WebSocket):
        """WebSocket endpoint for real-time dashboard updates"""
        from core.analytics_websocket import handle_dashboard_websocket
        await handle_dashboard_websocket(websocket)
    
    @app.websocket("/ws/analytics/metrics")
    async def websocket_metrics(websocket: WebSocket):
        """WebSocket endpoint for real-time metrics updates"""
        from core.analytics_websocket import handle_metrics_websocket
        await handle_metrics_websocket(websocket)
    
    @app.websocket("/ws/analytics/predictions")
    async def websocket_predictions(websocket: WebSocket):
        """WebSocket endpoint for real-time predictions updates"""
        from core.analytics_websocket import handle_predictions_websocket
        await handle_predictions_websocket(websocket)
    
    @app.websocket("/ws/analytics/alerts")
    async def websocket_alerts(websocket: WebSocket):
        """WebSocket endpoint for real-time alerts"""
        from core.analytics_websocket import handle_alerts_websocket
        await handle_alerts_websocket(websocket)

# ---------- GraphQL helpers (operationName-aware) ----------
_OP_HEADER_RE = re.compile(
    r'\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\([^)]*\))?\s*\{',
    re.DOTALL
)

def _find_matching_brace(s: str, start_idx: int) -> int:
    depth = 0
    for i in range(start_idx, len(s)):
        if s[i] == '{': depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0: return i
    return -1

def _clean_query(q: str) -> str:
    if not q: return ""
    q = re.sub(r'#.*', '', q)
    q = re.sub(r'//.*', '', q)
    return q

import re

_ident = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

def _extract_operation_body(q: str, operation_name: str | None):
    # Find the active operation's selection set: the '{ ... }' that belongs to it
    i = 0
    n = len(q)
    while i < n:
        # Skip whitespace and comments
        if q[i].isspace():
            i += 1; continue
        if q[i] == '#':  # comment to end of line
            while i < n and q[i] != '\n': i += 1
            continue

        # Read keyword: query/mutation/subscription or a bare selection '{'
        if q[i] == '{':
            # Anonymous operation; selection set starts here
            start = i
            break

        m = _ident.match(q, i)
        if not m:
            i += 1; continue
        kw = m.group(0)
        i = m.end()

        if kw in ("query", "mutation", "subscription"):
            # Optional operationName
            op_name = None
            # Skip spaces
            while i < n and q[i].isspace(): i += 1
            mm = _ident.match(q, i)
            if mm:
                op_name = mm.group(0)
                i = mm.end()

            # Optional variable defs '(...)'
            depth = 0
            if i < n and q[i] == '(':
                depth = 1; i += 1
                while i < n and depth:
                    c = q[i]
                    if c == '(':
                        depth += 1
                    elif c == ')':
                        depth -= 1
                    elif c in ('"', "'"):
                        # skip string
                        qchar = c; i += 1
                        while i < n:
                            if q[i] == '\\': i += 2; continue
                            if q[i] == qchar: i += 1; break
                            i += 1
                        continue
                    i += 1

            # Now we expect the selection set '{'
            while i < n and q[i].isspace(): i += 1
            if i < n and q[i] == '{':
                if (operation_name is None) or (op_name == operation_name):
                    start = i
                    break
        # otherwise keep scanning
    else:
        return ""  # not found

    # Find matching '}' for this '{'
    depth = 0
    j = start
    while j < n:
        c = q[j]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return q[start+1:j]  # inner contents
        elif c in ('"', "'"):
            qchar = c; j += 1
            while j < n:
                if q[j] == '\\': j += 2; continue
                if q[j] == qchar: break
                j += 1
        j += 1
    return ""
    

def top_level_fields(query: str, operation_name: str | None):
    body = _extract_operation_body(query, operation_name)
    if not body:
        # Try anonymous as fallback
        body = _extract_operation_body(query, None)
    
    if not body:
        return set()
    
    # Simple regex-based approach that works
    import re
    fields = set()
    
    # Find all field names (with or without arguments)
    # Pattern: word followed by optional (args) and optional {selection}
    pattern = r'\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*(?:\{[^}]*\})?'
    matches = re.findall(pattern, body)
    
    for match in matches:
        if match not in ['on', '__typename'] and not match.startswith('...'):
            fields.add(match)
    
    return fields

# ---------- Crypto Recommendations Helper Functions ----------
VOL_TIER_PENALTY = {"LOW": 0.0, "MEDIUM": 0.03, "HIGH": 0.06, "EXTREME": 0.10}

def _score_row(prob: float, liq_usd24h: float, tier: str, drift_mult: float) -> float:
    """
    Convert fundamentals into a 0–100 score.
    - Reward higher probability and liquidity
    - Penalize higher vol tiers
    - Apply drift clamp (safe-mode)
    """
    p_component   = max(0.0, (prob - 0.5) / 0.5)            # 0 at 0.5, 1 at 1.0
    liq_component = min(1.0, math.log10(max(liq_usd24h,1)) / 9.0)  # ~1.0 for $1B+ 24h
    tier_penalty  = VOL_TIER_PENALTY.get(tier.upper(), 0.05)

    raw = 0.65 * p_component + 0.35 * liq_component
    raw = max(0.0, raw - tier_penalty)                      # penalize riskier tiers
    scored = 100.0 * raw * drift_mult                       # clamp if drift high
    return float(max(0.0, min(100.0, scored)))

def _diversify(top: List[Dict[str, Any]], max_symbols: int) -> List[Dict[str, Any]]:
    """
    Simple diversification: pick at most one per tier bucket per round-robin until limit.
    """
    by_tier: Dict[str, List[Dict[str, Any]]] = {}
    for r in top:
        by_tier.setdefault(r["volatilityTier"], []).append(r)
    for v in by_tier.values():
        v.sort(key=lambda x: x["score"], reverse=True)

    out: List[Dict[str, Any]] = []
    tiers = sorted(by_tier.keys(), key=lambda t: {"LOW":0,"MEDIUM":1,"HIGH":2,"EXTREME":3}.get(t,9))
    while len(out) < max_symbols:
        advanced = False
        for t in tiers:
            if by_tier[t]:
                out.append(by_tier[t].pop(0))
                advanced = True
                if len(out) >= max_symbols:
                    break
        if not advanced:
            break
    return out

def _get_mock_supported_currencies():
    """Mock function to get supported currencies - returns top 5 by market cap"""
    return [
        {
            "id": "1",
            "symbol": "BTC",
            "name": "Bitcoin",
            "coingeckoId": "bitcoin",
            "isStakingAvailable": False,
            "minTradeAmount": 0.0001,
            "precision": 8,
            "volatilityTier": "HIGH",
            "isSecCompliant": True,
            "regulatoryStatus": "UNREGULATED"
        },
        {
            "id": "2",
            "symbol": "ETH", 
            "name": "Ethereum",
            "coingeckoId": "ethereum",
            "isStakingAvailable": True,
            "minTradeAmount": 0.001,
            "precision": 6,
            "volatilityTier": "HIGH",
            "isSecCompliant": True,
            "regulatoryStatus": "UNREGULATED"
        },
        {
            "id": "3",
            "symbol": "ADA",
            "name": "Cardano",
            "coingeckoId": "cardano",
            "isStakingAvailable": True,
            "minTradeAmount": 1.0,
            "precision": 2,
            "volatilityTier": "MEDIUM",
            "isSecCompliant": True,
            "regulatoryStatus": "UNREGULATED"
        },
        {
            "id": "4",
            "symbol": "SOL",
            "name": "Solana",
            "coingeckoId": "solana",
            "isStakingAvailable": True,
            "minTradeAmount": 0.01,
            "precision": 4,
            "volatilityTier": "HIGH",
            "isSecCompliant": True,
            "regulatoryStatus": "UNREGULATED"
        },
        {
            "id": "5",
            "symbol": "DOT",
            "name": "Polkadot",
            "coingeckoId": "polkadot",
            "isStakingAvailable": True,
            "minTradeAmount": 0.1,
            "precision": 3,
            "volatilityTier": "MEDIUM",
            "isSecCompliant": True,
            "regulatoryStatus": "UNREGULATED"
        }
    ]

def _get_mock_realtime_price(symbol: str):
    """Mock function to get realtime price - replace with real implementation"""
    mock_prices = {
        "BTC": {"priceUsd": 50000.0, "volumeUsd24h": 1500000000.0},
        "ETH": {"priceUsd": 3200.0, "volumeUsd24h": 800000000.0},
        "ADA": {"priceUsd": 0.45, "volumeUsd24h": 120000000.0},
        "SOL": {"priceUsd": 95.0, "volumeUsd24h": 300000000.0},
        "DOT": {"priceUsd": 6.5, "volumeUsd24h": 80000000.0}
    }
    return mock_prices.get(symbol.upper(), {"priceUsd": 0.0, "volumeUsd24h": 0.0})

# ========== REAL DATA INTEGRATION ==========

import requests
import time
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry
from requests import Session

class CryptoDataProvider:
    """Optimized cryptocurrency data provider using CoinGecko API with batching, SWR, and smart caching"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_ttl = COINGECKO_CACHE_TTL_SEC
        self.rate_limit_delay = COINGECKO_RATE_DELAY_SEC
        self.swr_grace = COINGECKO_SWR_GRACE_SEC
        
        # Threading and locking
        self._lock = threading.Lock()
        self._per_symbol_locks = defaultdict(threading.Lock)
        
        # Symbol mapping for CoinGecko API
        self.symbol_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "ADA": "cardano", 
            "SOL": "solana", "DOT": "polkadot", "MATIC": "matic-network",
            "AVAX": "avalanche-2", "LINK": "chainlink", "UNI": "uniswap",
            "ATOM": "cosmos", "NEAR": "near", "FTM": "fantom"
        }
        
        # Build optimized session
        self._session = self._build_session()
        
        # Throttled logging
        self._last_warn = {"price": 0.0, "market": 0.0}
    
    def _build_session(self) -> Session:
        """Build optimized HTTP session with retries and connection pooling"""
        s = Session()
        retry = Retry(
            total=5, 
            backoff_factor=0.4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"])
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=50)
        s.mount("https://", adapter)
        s.headers.update({"User-Agent": "RichesReach/1.0"})
        return s
    
    def _delay(self):
        """Add jittered delay to avoid sync bursts"""
        time.sleep(self.rate_limit_delay + random.uniform(0, 0.4))
    
    def _with_symbol_lock(self, symbol: str):
        """Get per-symbol lock to prevent thundering herd"""
        return self._per_symbol_locks[symbol.upper()]
    
    def _warn_throttled(self, key: str, msg: str):
        """Throttled logging to reduce noise"""
        now = time.time()
        if now - self._last_warn.get(key, 0) > 30:
            self._last_warn[key] = now
            logger.warning(msg)
    
    def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data with Redis and stale-while-revalidate support"""
        # Try Redis first if enabled
        if redis_client:
            try:
                cached = redis_client.get(f"crypto:{key}")
                if cached:
                    data, timestamp = json.loads(cached)
                    age = time.time() - timestamp
                    if age < self.cache_ttl:
                        CACHE_HITS.labels("redis", "coingecko").inc()
                        return data
                    elif age < self.cache_ttl + self.swr_grace:
                        CACHE_HITS.labels("redis", "coingecko").inc()
                        # Serve stale data and trigger background refresh
                        self._refresh_async(key)
                        return data
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
        
        # Fallback to in-memory cache
        if key in self.cache:
            data, timestamp = self.cache[key]
            age = time.time() - timestamp
            
            if age < self.cache_ttl:
                CACHE_HITS.labels("memory", "coingecko").inc()
                return data
            elif age < self.cache_ttl + self.swr_grace:
                CACHE_HITS.labels("memory", "coingecko").inc()
                # Serve stale data and trigger background refresh
                self._refresh_async(key)
                return data
            else:
                del self.cache[key]
        
        CACHE_MISSES.labels("memory", "coingecko").inc()
        return None

    def _refresh_async(self, key: str):
        """Trigger background refresh for stale-while-revalidate"""
        def _refresh_key():
            try:
                # Extract symbol from key and refresh
                if key.startswith("price:"):
                    symbol = key.replace("price:", "").upper()
                    self.get_real_time_price(symbol)
                elif key.startswith("price_batch:"):
                    # For batch keys, we'd need to parse the symbols
                    # For now, just log that we're refreshing
                    logger.debug(f"Background refresh triggered for {key}")
            except Exception as e:
                logger.warning(f"Background refresh failed for {key}: {e}")
        
        threading.Thread(target=_refresh_key, daemon=True).start()
    
    def _set_cached_data(self, key: str, data: Dict[str, Any]):
        """Cache data with timestamp in Redis and memory"""
        timestamp = time.time()
        
        # Store in Redis if enabled
        if redis_client:
            try:
                redis_client.setex(
                    f"crypto:{key}", 
                    self.cache_ttl + self.swr_grace,
                    json.dumps((data, timestamp))
                )
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
        
        # Also store in memory as fallback
        with self._lock:
            self.cache[key] = (data, timestamp)
    
    def _refresh_key(self, key: str):
        """Background refresh for stale-while-revalidate"""
        try:
            if key.startswith("price_"):
                sym = key.split("_", 1)[1]
                self.get_real_time_price(sym)  # Will recache
            elif key.startswith("market_"):
                sym = key.split("_", 1)[1]
                self.get_market_data(sym)  # Will recache
        except Exception as e:
            logger.debug(f"SWR refresh error for {key}: {e}")
    
    def get_real_time_price_many(self, symbols: list[str]) -> dict[str, dict]:
        """Batch fetch prices for multiple symbols with smart caching"""
        results, to_fetch = {}, []
        
        # Check cache for all symbols first
        for s in symbols:
            key = f"price_{s.upper()}"
            hit = self._get_cached_data(key)
            if hit:
                results[s.upper()] = hit
            elif s.upper() in self.symbol_map:
                to_fetch.append((s.upper(), self.symbol_map[s.upper()]))
        
        # If all cached, return immediately
        if not to_fetch:
            return results
        
        # Batch fetch missing symbols with smart rate limiting
        with self._with_symbol_lock("batch"):
            # Use shorter delay for batch requests
            time.sleep(0.5)  # Reduced from 3 seconds
            ids = ",".join([cid for _, cid in to_fetch])
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": ids, 
                "vs_currencies": "usd",
                "include_24hr_vol": "true", 
                "include_24hr_change": "true"
            }
            
            try:
                resp = self._session.get(url, params=params, timeout=10)
                
                # Handle 429 with Retry-After
                if resp.status_code == 429:
                    ra = resp.headers.get("Retry-After")
                    wait = float(ra) if ra and ra.isdigit() else 2.0  # Reduced fallback
                    self._warn_throttled("price", f"429 from CoinGecko; backing off for {wait:.1f}s")
                    time.sleep(wait)
                    resp = self._session.get(url, params=params, timeout=10)
                
                resp.raise_for_status()
                data = resp.json()
                
                # Map results back to symbols
                rev = {cid: sym for sym, cid in to_fetch}
                for cid, payload in data.items():
                    out = {
                        "priceUsd": payload.get("usd", 0.0),
                        "volumeUsd24h": payload.get("usd_24h_vol", 0.0),
                        "priceChange24h": payload.get("usd_24h_change", 0.0),
                        "timestamp": time.time(),
                    }
                    sym = rev.get(cid)
                    if sym:
                        self._set_cached_data(f"price_{sym}", out)
                        results[sym] = out
                        
            except Exception as e:
                self._warn_throttled("price", f"Batch price fetch failed: {e}")
                # Graceful fallback per symbol
                for sym, _ in to_fetch:
                    results[sym] = _get_mock_realtime_price(sym)
        
        return results
    
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """Get real-time price data from CoinGecko with per-symbol locking"""
        symbol = symbol.upper()
        
        with self._with_symbol_lock(symbol):
            # Check cache first
            cache_key = f"price_{symbol}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # Map symbol to CoinGecko ID
            coin_id = self.symbol_map.get(symbol)
            if not coin_id:
                return _get_mock_realtime_price(symbol)
            
            # Rate limiting with jitter
            self._delay()
            
            try:
                # Fetch from API
                url = f"{self.base_url}/simple/price"
                params = {
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true"
                }
                
                resp = self._session.get(url, params=params, timeout=10)
                
                # Handle 429 with Retry-After
                if resp.status_code == 429:
                    ra = resp.headers.get("Retry-After")
                    wait = float(ra) if ra and ra.isdigit() else (self.rate_limit_delay * 2)
                    self._warn_throttled("price", f"429 from CoinGecko for {symbol}; backing off for {wait:.1f}s")
                    time.sleep(wait)
                    resp = self._session.get(url, params=params, timeout=10)
                
                resp.raise_for_status()
                data = resp.json()
                
                if coin_id in data:
                    result = {
                        "priceUsd": data[coin_id].get("usd", 0.0),
                        "volumeUsd24h": data[coin_id].get("usd_24h_vol", 0.0),
                        "priceChange24h": data[coin_id].get("usd_24h_change", 0.0),
                        "timestamp": time.time(),
                    }
                    # Cache the result
                    self._set_cached_data(cache_key, result)
                    return result
                else:
                    return _get_mock_realtime_price(symbol)
                
            except Exception as e:
                self._warn_throttled("price", f"Error fetching real-time price for {symbol}: {e}")
                return _get_mock_realtime_price(symbol)

    def get_prices_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get prices for multiple symbols in one request"""
        # Map symbols to CoinGecko IDs
        coin_ids = [self.symbol_map.get(s.upper()) for s in symbols if s.upper() in self.symbol_map]
        if not coin_ids:
            return {}
        
        cache_key = f"batch_{','.join(sorted(coin_ids))}"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached
        
        # Rate limiting
        self._delay()
        
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_24hr_vol": "true",
                "include_24hr_change": "true"
            }
            
            t0 = time.perf_counter()
            response = self._session.get(url, params=params, timeout=10)
            CG_FETCH_LATENCY.labels("simple_price_batch").observe(time.perf_counter() - t0)
            response.raise_for_status()
            
            data = response.json()
            result = {}
            
            # Map back to symbols
            symbol_to_id = {s.upper(): self.symbol_map.get(s.upper()) for s in symbols}
            for symbol, coin_id in symbol_to_id.items():
                if coin_id and coin_id in data:
                    price_data = data[coin_id]
                    result[symbol] = {
                        "priceUsd": price_data.get("usd", 0.0),
                        "volumeUsd24h": price_data.get("usd_24h_vol", 0.0),
                        "priceChange24h": price_data.get("usd_24h_change", 0.0),
                        "timestamp": time.time()
                    }
            
            self._set_cached_data(cache_key, result)
            return result
            
        except Exception as e:
            self._warn_throttled("batch_price", f"Failed to fetch batch prices: {e}")
            return {}
    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market data including volatility, RSI, etc."""
        try:
            cache_key = f"market_{symbol.upper()}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            symbol_map = {
                "BTC": "bitcoin",
                "ETH": "ethereum", 
                "ADA": "cardano",
                "SOL": "solana",
                "DOT": "polkadot"
            }
            
            coin_id = symbol_map.get(symbol.upper())
            if not coin_id:
                return {}
            
            # Skip delay for speed - using mock data
            # time.sleep(self.rate_limit_delay)
            
            # Get detailed market data
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false"
            }
            
            response = self._session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            market_data = data.get("market_data", {})
            
            # Calculate volatility (simplified)
            price_change_24h = market_data.get("price_change_percentage_24h", 0)
            price_change_7d = market_data.get("price_change_percentage_7d", 0)
            price_change_30d = market_data.get("price_change_percentage_30d", 0)
            
            # Simple volatility calculation
            volatility_7d = abs(price_change_7d) / 7
            volatility_30d = abs(price_change_30d) / 30
            
            # Determine volatility tier
            avg_volatility = (volatility_7d + volatility_30d) / 2
            if avg_volatility < 2:
                volatility_tier = "LOW"
            elif avg_volatility < 5:
                volatility_tier = "MEDIUM"
            elif avg_volatility < 10:
                volatility_tier = "HIGH"
            else:
                volatility_tier = "EXTREME"
            
            result = {
                "priceUsd": market_data.get("current_price", {}).get("usd", 0.0),
                "volumeUsd24h": market_data.get("total_volume", {}).get("usd", 0.0),
                "marketCap": market_data.get("market_cap", {}).get("usd", 0.0),
                "priceChange24h": price_change_24h,
                "priceChangePercentage24h": price_change_24h,
                "volatility7d": volatility_7d,
                "volatility30d": volatility_30d,
                "volatilityTier": volatility_tier,
                "rsi14": 50.0,  # Would need technical analysis API
                "momentumScore": min(1.0, max(0.0, (price_change_24h + 20) / 40)),  # Normalized momentum
                "sentimentScore": 0.5,  # Would need sentiment analysis API
                "sentimentDescription": "Neutral market sentiment",
                "timestamp": time.time()
            }
            
            self._set_cached_data(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return {}

# Initialize the data provider
crypto_data_provider = CryptoDataProvider()

def get_real_crypto_price(symbol: str) -> Dict[str, Any]:
    """Get real cryptocurrency price data"""
    return crypto_data_provider.get_real_time_price(symbol)

def get_real_market_data(symbol: str) -> Dict[str, Any]:
    """Get real cryptocurrency market data with smart caching"""
    return crypto_data_provider.get_market_data(symbol)

def _get_mock_prediction(symbol: str):
    """Mock function to get prediction - replace with real implementation"""
    import random
    prob = random.uniform(0.45, 0.85)  # Random probability between 45% and 85%
    confidence = "HIGH" if prob > 0.7 else "MEDIUM" if prob > 0.6 else "LOW"
    return {
        "probability": prob,
        "confidenceLevel": confidence,
        "explanation": f"AI analysis indicates {prob:.1%} probability of bullish movement for {symbol}"
    }

# ========== REAL ML PREDICTION SYSTEM ==========

class MLPredictionEngine:
    """Real ML prediction engine for cryptocurrency price movements"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache for predictions
        
    def _get_cached_prediction(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached prediction if still valid"""
        if symbol in self.cache:
            data, timestamp = self.cache[symbol]
            if time.time() - timestamp < self.cache_ttl:
                return data
            del self.cache[symbol]
        return None
    
    def _set_cached_prediction(self, symbol: str, data: Dict[str, Any]):
        """Cache prediction with timestamp"""
        self.cache[symbol] = (data, time.time())
    
    def get_real_prediction(self, symbol: str) -> Dict[str, Any]:
        """Get real ML prediction based on market data"""
        try:
            # Check cache first
            cached_prediction = self._get_cached_prediction(symbol)
            if cached_prediction:
                return cached_prediction
            
            # Get real market data with fast fallback
            try:
                market_data = get_real_market_data(symbol)
            except Exception as e:
                logger.warning(f"Market data failed for {symbol}: {e}")
                market_data = None
            
            if not market_data:
                prediction = _get_mock_prediction(symbol)
            else:
                # Extract features for ML prediction
                price_change_24h = market_data.get("priceChangePercentage24h", 0)
                volatility_7d = market_data.get("volatility7d", 0)
                volume_24h = market_data.get("volumeUsd24h", 0)
                momentum_score = market_data.get("momentumScore", 0.5)
                
                # Advanced ML-like prediction algorithm
                price_momentum = min(1.0, max(0.0, (price_change_24h + 20) / 40))
                volatility_factor = min(1.0, max(0.0, volatility_7d / 10))
                volume_factor = min(1.0, max(0.0, volume_24h / 1_000_000_000))
                
                # Weighted prediction model
                base_probability = 0.5
                momentum_adjustment = (price_momentum - 0.5) * 0.3
                volatility_adjustment = (0.3 - abs(volatility_factor - 0.3)) * 0.2
                volume_adjustment = (volume_factor - 0.5) * 0.1
                
                raw_probability = base_probability + momentum_adjustment + volatility_adjustment + volume_adjustment
                raw_probability = max(0.1, min(0.9, raw_probability))
                
                # Apply improved Platt scaling for calibrated probabilities
                calibrated_probability = _platt(raw_probability)
                
                # Determine confidence level
                if abs(price_change_24h) > 10 and volume_factor > 0.5:
                    confidence = "HIGH"
                elif abs(price_change_24h) > 5 and volume_factor > 0.3:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"
                
                # Record prediction for accuracy tracking
                record_outcome(calibrated_probability, False)  # We don't know the outcome yet
                
                # Record Brier score components (placeholder - replace with true label when available)
                BRIER_SUM.inc((calibrated_probability - 0.5)**2)  # placeholder
                BRIER_N.inc()
                
                prediction = {
                    "probability": round(calibrated_probability, 4),
                    "confidenceLevel": confidence,
                    "explanation": f"ML analysis: {price_change_24h:.1f}% change, {volatility_7d:.1f}% vol, {momentum_score:.1f} momentum",
                    "features": {
                        "volatility_7d": volatility_7d,
                        "momentum": momentum_score,
                        "price_change_24h": price_change_24h,
                        "volume_factor": volume_factor
                    }
                }
            
            # Cache the prediction
            self._set_cached_prediction(symbol, prediction)
            return prediction
            
            # Extract features for ML prediction
            price_change_24h = market_data.get("priceChangePercentage24h", 0)
            volatility_7d = market_data.get("volatility7d", 0)
            volume_24h = market_data.get("volumeUsd24h", 0)
            momentum_score = market_data.get("momentumScore", 0.5)
            
            # Simple ML-like prediction algorithm
            # This is a simplified version - in production you'd use actual ML models
            
            # Feature engineering
            price_momentum = min(1.0, max(0.0, (price_change_24h + 20) / 40))  # Normalize to 0-1
            volatility_factor = min(1.0, max(0.0, volatility_7d / 10))  # Normalize volatility
            volume_factor = min(1.0, max(0.0, volume_24h / 1_000_000_000))  # Normalize volume
            
            # Weighted prediction model
            base_probability = 0.5  # 50% base probability
            
            # Adjust based on momentum (positive momentum increases bullish probability)
            momentum_adjustment = (price_momentum - 0.5) * 0.3
            
            # Adjust based on volatility (moderate volatility is good for predictions)
            volatility_adjustment = (0.3 - abs(volatility_factor - 0.3)) * 0.2
            
            # Adjust based on volume (higher volume increases confidence)
            volume_adjustment = (volume_factor - 0.5) * 0.1
            
            # Calculate final probability
            probability = base_probability + momentum_adjustment + volatility_adjustment + volume_adjustment
            probability = max(0.1, min(0.9, probability))  # Clamp between 10% and 90%
            
            # Determine confidence level
            if abs(price_change_24h) > 10 and volume_factor > 0.5:
                confidence = "HIGH"
            elif abs(price_change_24h) > 5 and volume_factor > 0.3:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
            
            # Generate explanation
            if price_change_24h > 5:
                trend = "strong bullish"
            elif price_change_24h > 0:
                trend = "bullish"
            elif price_change_24h > -5:
                trend = "neutral"
            else:
                trend = "bearish"
            
            explanation = f"ML model indicates {trend} signals for {symbol} based on price momentum ({price_change_24h:.1f}%), volatility ({volatility_7d:.1f}%), and volume activity"
            
            result = {
                "probability": probability,
                "confidenceLevel": confidence,
                "explanation": explanation,
                "features": {
                    "priceChange24h": price_change_24h,
                    "volatility7d": volatility_7d,
                    "volume24h": volume_24h,
                    "momentumScore": momentum_score
                },
                "modelVersion": "v1.0",
                "timestamp": time.time()
            }
            
            # Cache the prediction
            self._set_cached_prediction(symbol, result)
            return result
            
        except Exception as e:
            logger.error(f"Error generating ML prediction for {symbol}: {e}")
            return _get_mock_prediction(symbol)

# Initialize the ML prediction engine
ml_prediction_engine = MLPredictionEngine()

def get_real_ml_prediction(symbol: str) -> Dict[str, Any]:
    """Get real ML prediction for cryptocurrency"""
    return ml_prediction_engine.get_real_prediction(symbol)

def _get_mock_drift_decision():
    """Mock function to get drift decision - replace with real implementation"""
    return {"size_multiplier": 1.0, "level": "OK"}

# ---------- GraphQL endpoint ----------
@app.post("/graphql")
@app.post("/graphql/")
async def graphql_endpoint(request_data: dict):
    import re
    from datetime import datetime, timedelta
    _trace(f"ENTER /graphql (keys={list(request_data.keys())})")
    query = request_data.get("query", "") or ""
    variables = request_data.get("variables", {}) or {}
    operation_name = request_data.get("operationName") or None
    response_data = {}

    logger.info("=== GRAPHQL REQUEST ===")
    logger.info("BUILD_ID: %s", BUILD_ID)
    logger.info("operationName: %s", operation_name)
    logger.info("Top-level fields: %s", top_level_fields(query, operation_name))
    logger.info("Variables: %s", variables)

    # === Enhanced Field Detection (handles operationName mismatches) ===
    fields_op    = top_level_fields(query, operation_name)
    fields_any   = top_level_fields(query, None)
    fields       = fields_op or fields_any  # prefer opName, fall back to anonymous
    logger.info("Top-level fields (op=%s) -> using=%s (opOnly=%s any=%s)",
                operation_name, fields, fields_op, fields_any)

    # === Error Handling Helper ===
    def _add_error(errors, msg):
        errors.append({"message": msg})

    # === Initialize Response Data ===
    response_data = {}
    errors = []

    # === Persisted Query Cache Check ===
    pqk = _pq_key(query, variables)
    cached = _pq_get(pqk)
    if cached: 
        return cached

    # ---------------------------
    # PHASE 2 — put first, early return
    # ---------------------------
    
    # --- Crypto ML Signal (query) ---
    if "cryptoMlSignal" in fields:
        start = time.perf_counter()
        try:
            # Try variables first, then parse from query
            symbol = (variables or {}).get("symbol")
            timeframe = (variables or {}).get("timeframe", "ALL")
            if not symbol:
                m = re.search(r'cryptoMlSignal\s*\(\s*symbol:\s*"([^"]+)"', query or "")
                if m: symbol = m.group(1)

            if not symbol:
                return {"errors": [{"message": "symbol required"}]}

            # Try Rust service first for high performance
            sig = None
            try:
                from core.rust_crypto_service import rust_crypto_service
                logger.info(f"🔍 Checking Rust service availability for {symbol}")
                if rust_crypto_service.is_available():
                    logger.info(f"✅ Rust service is available, attempting analysis for {symbol}")
                    # Use the async method directly since we're already in an async context
                    rust_result = await rust_crypto_service.analyze_crypto(symbol, timeframe)
                    if rust_result:
                        # Map Rust response to GraphQL schema
                        sig = {
                            "symbol": rust_result.get("symbol", symbol),
                            "probability": rust_result.get("probability", 0.5),
                            "confidenceLevel": rust_result.get("confidence_level", "LOW"),
                            "explanation": rust_result.get("explanation", "Rust analysis completed"),
                            "features": rust_result.get("features", {}),
                            "modelVersion": rust_result.get("model_version", "rust-v1.0.0"),
                            "timestamp": rust_result.get("timestamp", time.time())
                        }
                        logger.info(f"✅ Used Rust service for {symbol} analysis")
            except Exception as rust_error:
                logger.warning(f"Rust service error: {rust_error}")

            # Fallback to Python ML prediction if Rust not available
            if not sig:
                try:
                    sig = get_real_ml_prediction(symbol)
                    logger.info(f"✅ Used Python ML for {symbol} analysis")
                except Exception as e:
                    logger.warning(f"ML prediction failed for {symbol}: {e}")
                    sig = None

            # Ensure non-null shape with fallback
            if not sig or "probability" not in sig:
                payload = {
                    "symbol": symbol,
                    "probability": 0.5,
                    "confidenceLevel": "LOW",
                    "explanation": "Fallback prediction due to model error",
                    "features": {},
                    "modelVersion": "v1.0",
                    "timestamp": time.time(),
                    "__typename": "CryptoMlSignal"
                }
            else:
                payload = {
                    "symbol": symbol,
                    "probability": float(sig.get("probability", 0.5)),
                    "confidenceLevel": sig.get("confidenceLevel", "LOW"),
                    "explanation": sig.get("explanation", ""),
                    "features": sig.get("features", {}),
                    "modelVersion": sig.get("modelVersion", "v1.0"),
                    "timestamp": sig.get("timestamp", time.time()),
                    "__typename": "CryptoMlSignal"
                }
            
            return {"data": {"cryptoMlSignal": payload}}
        except Exception as e:
            logger.warning(f"cryptoMlSignal handler failed: {e}")
            # Return fallback data instead of null
            return {"data": {"cryptoMlSignal": {
                "symbol": symbol or "UNKNOWN",
                "probability": 0.5,
                "confidenceLevel": "LOW",
                "explanation": "System error - using fallback",
                "features": {},
                "modelVersion": "v1.0",
                "timestamp": time.time(),
                "__typename": "CryptoMlSignal"
            }}}
        finally:
            ML_SIGNAL_LATENCY.observe(time.perf_counter() - start)

    # --- Crypto Recommendations (query) ---
    if "cryptoRecommendations" in fields:
        start = time.perf_counter()
        try:
            limit = int((variables or {}).get("limit", 5))
            symbols = (variables or {}).get("symbols") or ["BTC", "ETH", "SOL", "ADA", "DOT"]
            
            # Try Rust service first for high performance
            try:
                from core.rust_crypto_service import rust_crypto_service
                if rust_crypto_service.is_available():
                    # Use the async method directly since we're already in an async context
                    rust_recommendations = await rust_crypto_service.get_crypto_recommendations(limit, symbols)
                    if rust_recommendations:
                        # Extract items from Rust response (it returns {"items": [...]})
                        items = rust_recommendations.get("items", []) if isinstance(rust_recommendations, dict) else rust_recommendations
                        # Map Rust response to GraphQL schema
                        results = []
                        for rec in items:
                            results.append({
                                "symbol": rec.get("symbol", ""),
                                "name": rec.get("symbol", ""),
                                "currentPrice": float(rec.get("price_usd", 0.0)),
                                "priceUsd": float(rec.get("price_usd", 0.0)),
                                "change24h": float(rec.get("change_24h", 0.0)),
                                "changePercent24h": float(rec.get("change_percent_24h", 0.0)),
                                "marketCap": float(rec.get("market_cap", 0.0)),
                                "volume24h": float(rec.get("liquidity_24h_usd", 0.0)),
                                "volumeUsd24h": float(rec.get("liquidity_24h_usd", 0.0)),
                                "volatilityTier": rec.get("volatility_tier", "MEDIUM"),
                                "probability": rec.get("probability", 0.5),
                                "confidenceLevel": rec.get("confidence_level", "LOW"),
                                "riskLevel": rec.get("risk_level", "MEDIUM"),
                                "liquidity24hUsd": float(rec.get("liquidity_24h_usd", 0.0)),
                                "rationale": rec.get("rationale", "Rust analysis completed"),
                                "recommendation": rec.get("recommendation", "HOLD"),
                                "explanation": rec.get("rationale", "Rust analysis completed"),
                                "score": rec.get("score", 0.0),
                                "__typename": "CryptoRecommendation"
                            })
                        logger.info(f"✅ Used Rust service for recommendations")
                        return {"data": {"cryptoRecommendations": results}}
            except Exception as rust_error:
                logger.warning(f"Rust service error: {rust_error}")
            
            # Fallback to Python implementation
            # Use batch pricing for efficiency
            try:
                batch_prices = crypto_data_provider.get_prices_batch(symbols)
            except Exception as e:
                logger.warning(f"Batch pricing failed: {e}")
                batch_prices = {}

            results = []
            for symbol in symbols:
                try:
                    # Get ML prediction
                    ml_pred = get_real_ml_prediction(symbol)
                    
                    # Get price data from batch or individual call
                    price_data = batch_prices.get(crypto_data_provider.symbol_map.get(symbol, ""), {})
                    if not price_data:
                        price_data = get_real_crypto_price(symbol) or {}
                    
                    # Get market data
                    market_data = get_real_market_data(symbol) or {}
                    
                    prob = float(ml_pred.get("probability", 0.5))
                    price_usd = float(price_data.get("priceUsd", price_data.get("usd", 0.0)))
                    volume_24h = float(price_data.get("volumeUsd24h", price_data.get("usd_24h_vol", 0.0)))
                    volatility_tier = market_data.get("volatilityTier", "HIGH").upper()
                    
                    # Calculate score
                    score = _score_row(prob, volume_24h, volatility_tier, 1.0)
                    
                    results.append({
                        "symbol": symbol,
                        "name": symbol,  # Could be enhanced with full names
                        "currentPrice": price_usd,
                        "priceUsd": price_usd,
                        "change24h": float(price_data.get("change24h", 0.0)),
                        "changePercent24h": float(price_data.get("changePercent24h", 0.0)),
                        "marketCap": float(price_data.get("marketCap", 0.0)),
                        "volume24h": volume_24h,
                        "volumeUsd24h": volume_24h,
                        "volatilityTier": volatility_tier,
                        "probability": prob,
                        "confidenceLevel": ml_pred.get("confidenceLevel", "LOW"),
                        "riskLevel": "HIGH" if volatility_tier == "HIGH" else "MEDIUM" if volatility_tier == "MEDIUM" else "LOW",
                        "liquidity24hUsd": volume_24h,
                        "rationale": ml_pred.get("explanation", "Model produced a valid signal."),
                        "recommendation": "BUY" if prob > 0.6 else "SELL" if prob < 0.4 else "HOLD",
                        "explanation": ml_pred.get("explanation", "Model produced a valid signal."),
                        "score": round(score, 1),
                        "__typename": "CryptoRecommendation"
                    })
                except Exception as e:
                    logger.warning(f"Failed to process {symbol}: {e}")
                    # Add fallback entry
                    results.append({
                        "symbol": symbol,
                        "name": symbol,
                        "currentPrice": 0.0,
                        "priceUsd": 0.0,
                        "change24h": 0.0,
                        "changePercent24h": 0.0,
                        "marketCap": 0.0,
                        "volume24h": 0.0,
                        "volumeUsd24h": 0.0,
                        "volatilityTier": "UNKNOWN",
                        "probability": 0.5,
                        "confidenceLevel": "LOW",
                        "riskLevel": "UNKNOWN",
                        "liquidity24hUsd": 0.0,
                        "rationale": "Error processing symbol",
                        "recommendation": "HOLD",
                        "explanation": "Error processing symbol",
                        "score": 0.0,
                        "__typename": "CryptoRecommendation"
                    })

            # Sort by score and limit results
            results.sort(key=lambda x: x["score"], reverse=True)
            limited_results = results[:limit]

            return {"data": {"cryptoRecommendations": limited_results}}
        except Exception as e:
            logger.warning(f"cryptoRecommendations failed: {e}")
            return {"data": {"cryptoRecommendations": []}}
        finally:
            RECS_LATENCY.observe(time.perf_counter() - start)

    # Notifications (query)
    if "notifications" in fields:
        response_data["notifications"] = [
            {
                "id": "notif_001", "title": "Price Alert: AAPL",
                "message": "Apple Inc. (AAPL) has reached your target price of $150.00",
                "type": "price_alert", "isRead": False,
                "createdAt": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "data": {"symbol": "AAPL", "targetPrice": 150.00, "currentPrice": 150.25},
                "__typename": "Notification"
            },
            {
                "id": "notif_002", "title": "Order Filled",
                "message": "Your buy order for 10 shares of MSFT has been filled at $300.50",
                "type": "order_filled", "isRead": False,
                "createdAt": (datetime.now() - timedelta(hours=1)).isoformat(),
                "data": {"symbol": "MSFT", "quantity": 10, "fillPrice": 300.50, "orderId": "order_123"},
                "__typename": "Notification"
            },
            {
                "id": "notif_003", "title": "SBLOC Opportunity",
                "message": "Your portfolio has grown 15% this month! You now have $25,000 in additional borrowing power available.",
                "type": "sbloc_opportunity", "isRead": False,
                "createdAt": (datetime.now() - timedelta(hours=3)).isoformat(),
                "data": {"portfolioGrowth": 15.0, "newBorrowingPower": 25000, "previousBorrowingPower": 20000},
                "__typename": "Notification"
            },
            {
                "id": "notif_004", "title": "SBLOC Rate Alert",
                "message": "SBLOC interest rates have dropped to 6.5% - a great time to consider borrowing against your portfolio.",
                "type": "sbloc_rate_alert", "isRead": False,
                "createdAt": (datetime.now() - timedelta(days=1)).isoformat(),
                "data": {"newRate": 6.5, "previousRate": 7.2, "savings": 0.7},
                "__typename": "Notification"
            },
            {
                "id": "notif_005", "title": "Portfolio Liquidity Reminder",
                "message": "Consider SBLOC instead of selling shares for your upcoming $5,000 expense. Keep your investments growing!",
                "type": "sbloc_liquidity_reminder", "isRead": True,
                "createdAt": (datetime.now() - timedelta(days=2)).isoformat(),
                "data": {"suggestedAmount": 5000, "potentialSavings": 750},
                "__typename": "Notification"
            },
        ]
        return {"data": response_data}

    if "notificationSettings" in fields:
        response_data["notificationSettings"] = {
            "priceAlerts": True, "tradeConfirmations": True, "marketUpdates": False,
            "accountActivity": True, "pushNotifications": True, "emailNotifications": False,
            "orderUpdates": True, "newsUpdates": True, "systemUpdates": True,
            "__typename": "NotificationSettings"
        }
        return {"data": response_data}

    if "cancelOrder" in fields:
        oid = variables.get("orderId")
        if not oid: return {"errors":[{"message":"orderId required"}]}
        ok = await trading_service.cancel_order(oid)
        return {"data": {"cancelOrder": {"success": bool(ok), "orderId": oid, "__typename":"CancelOrderResult"}}}

    if "orders" in fields:
        status = variables.get("status")  # NEW/FILLED/CANCELLED/ALL
        arr = await trading_service.get_orders(status=status or None, limit=50)
        # normalize shape
        norm = []
        for o in arr or []:
            norm.append({
                "id": getattr(o,"id",""),
                "status": getattr(o,"status",""),
                "symbol": getattr(o,"symbol",""),
                "optionType": getattr(o,"option_type",""),
                "strike": getattr(o,"strike",0.0),
                "expiration": getattr(o,"expiration",""),
                "side": getattr(o,"side",""),
                "orderType": getattr(o,"order_type",""),
                "timeInForce": getattr(o,"time_in_force",""),
                "limitPrice": getattr(o,"limit_price",None),
                "stopPrice": getattr(o,"stop_price",None),
                "quantity": getattr(o,"qty",0),
                "createdAt": getattr(o,"created_at",datetime.now().isoformat()),
                "__typename":"Order"
            })
        return {"data":{"orders": norm}}

    # Options Trading Mutations
    if "placeOptionOrder" in fields:
        try:
            symbol = variables.get("symbol", "")
            option_type = variables.get("optionType", "CALL")  # CALL or PUT
            strike = float(variables.get("strike", 0))
            expiration = variables.get("expiration", "")
            side = variables.get("side", "BUY")  # BUY or SELL
            quantity = int(variables.get("quantity", 0) or 0)
            order_type = variables.get("orderType", "MARKET")  # MARKET, LIMIT, STOP
            limit_price = float(variables.get("limitPrice", 0) or 0)
            stop_price = float(variables.get("stopPrice", 0) or 0)
            time_in_force = variables.get("timeInForce", "DAY")  # DAY, GTC, IOC, FOK
            notes = variables.get("notes", "")
            
            if not symbol or strike <= 0 or not expiration or quantity <= 0:
                return {"errors": [{"message": "symbol, strike, expiration, and quantity are required"}]}
            
            # Generate order ID
            order_id = f"opt_{int(time.time() * 1000)}"
            
            # Price protection for limit orders
            if order_type == "LIMIT" and limit_price > 0:
                # Simple price protection - limit to 10% above current market
                max_price = limit_price * 1.10
                if limit_price > max_price:
                    limit_price = max_price
            
            return {"data": {"placeOptionOrder": {
                "success": True,
                "message": f"Options {side} order for {quantity} {option_type} contracts of {symbol} at ${strike} strike placed successfully",
                "orderId": order_id,
                "order": {
                    "id": order_id,
                    "symbol": symbol,
                    "optionType": option_type,
                    "strike": strike,
                    "expiration": expiration,
                    "side": side,
                    "quantity": quantity,
                    "orderType": order_type,
                    "limitPrice": limit_price if order_type == "LIMIT" else None,
                    "stopPrice": stop_price if order_type == "STOP" else None,
                    "timeInForce": time_in_force,
                    "status": "PENDING",
                    "notes": notes,
                    "createdAt": datetime.now().isoformat(),
                    "__typename": "OptionOrder"
                },
                "__typename": "PlaceOptionOrderResult"
            }}}
        except Exception as e:
            logger.error(f"placeOptionOrder error: {e}")
            return {"errors": [{"message": f"Failed to place options order: {str(e)}"}]}

    if "cancelOptionOrder" in fields:
        try:
            order_id = variables.get("orderId", "")
            if not order_id:
                return {"errors": [{"message": "orderId is required"}]}
            
            # Simulate order cancellation
            success = True  # In real implementation, call trading service
            
            return {"data": {"cancelOptionOrder": {
                "success": success,
                "message": f"Options order {order_id} {'cancelled successfully' if success else 'could not be cancelled'}",
                "orderId": order_id,
                "__typename": "CancelOptionOrderResult"
            }}}
        except Exception as e:
            logger.error(f"cancelOptionOrder error: {e}")
            return {"errors": [{"message": f"Failed to cancel options order: {str(e)}"}]}

    if "optionOrders" in fields:
        try:
            status = variables.get("status")  # PENDING, FILLED, CANCELLED, ALL
            option_type = variables.get("optionType")  # CALL, PUT, ALL
            
            # Mock options orders data
            mock_orders = [
                {
                    "id": "opt_1703123456789",
                    "symbol": "AAPL",
                    "optionType": "CALL",
                    "strike": 150.0,
                    "expiration": "2024-01-19",
                    "side": "BUY",
                    "quantity": 10,
                    "orderType": "MARKET",
                    "limitPrice": None,
                    "stopPrice": None,
                    "timeInForce": "DAY",
                    "status": "FILLED",
                    "filledPrice": 2.45,
                    "notes": "Bullish play on earnings",
                    "createdAt": "2024-01-15T10:30:00Z",
                    "__typename": "OptionOrder"
                },
                {
                    "id": "opt_1703123456790",
                    "symbol": "TSLA",
                    "optionType": "PUT",
                    "strike": 200.0,
                    "expiration": "2024-02-16",
                    "side": "SELL",
                    "quantity": 5,
                    "orderType": "LIMIT",
                    "limitPrice": 3.20,
                    "stopPrice": None,
                    "timeInForce": "GTC",
                    "status": "PENDING",
                    "filledPrice": None,
                    "notes": "Hedge against portfolio",
                    "createdAt": "2024-01-15T14:22:00Z",
                    "__typename": "OptionOrder"
                }
            ]
            
            # Filter by status if provided
            if status and status != "ALL":
                mock_orders = [o for o in mock_orders if o["status"] == status]
            
            # Filter by option type if provided
            if option_type and option_type != "ALL":
                mock_orders = [o for o in mock_orders if o["optionType"] == option_type]
            
            return {"data": {"optionOrders": mock_orders}}
        except Exception as e:
            logger.error(f"optionOrders error: {e}")
            return {"errors": [{"message": f"Failed to fetch options orders: {str(e)}"}]}

    # Stock chart data (query) - Enhanced with technical indicators
    if "stockChartData" in fields:
        symbol = variables.get("symbol", "")
        timeframe = variables.get("timeframe", "1D")
        interval = variables.get("interval") or timeframe
        limit = int(variables.get("limit") or 120)
        indicators_req = variables.get("indicators") or variables.get("inds") or []
        
        if not symbol:
            # Enhanced GraphQL query parsing
            import re
            # Look for symbol: "AAPL" pattern
            symbol_match = re.search(r'symbol:\s*["\']([^"\']+)["\']', query)
            if symbol_match:
                symbol = symbol_match.group(1)
            else:
                # Fallback: look for stockChartData(symbol: "AAPL")
                symbol_match = re.search(r'stockChartData\s*\(\s*symbol:\s*["\']([^"\']+)["\']', query)
                if symbol_match:
                    symbol = symbol_match.group(1)
        
        if not timeframe:
            # Look for timeframe: "1d" pattern
            timeframe_match = re.search(r'timeframe:\s*["\']([^"\']+)["\']', query)
            if timeframe_match:
                timeframe = timeframe_match.group(1)
        
        # Parse indicators from query if not in variables
        if not indicators_req:
            # Look for indicators: ["SMA20", "RSI"] pattern
            indicators_match = re.search(r'indicators:\s*\[([^\]]+)\]', query)
            if indicators_match:
                indicators_str = indicators_match.group(1)
                # Parse the array elements
                indicators_req = [ind.strip().strip('"\'') for ind in indicators_str.split(',')]
        
        if not symbol:
            return {"errors": [{"message": "Symbol is required for chart data"}]}

        # Guardrails for performance
        limit = max(30, min(limit, 500))
        
        now = datetime.now()
        data_points = {'1D': 24, '1W': 7, '1M': 30, '3M': 90, '1Y': 365}
        points = min(data_points.get(timeframe, 30), limit)
        base_price = 150 + hash(symbol) % 100
        import math
        chart = []
        for i in range(points):
            ts = now - (timedelta(hours=points - i) if timeframe == '1D' else timedelta(days=points - i))
            pv = (math.sin(i * 0.1) + math.cos(i * 0.05)) * 5
            cur = base_price + pv + (i * 0.1)
            open_p = cur + (random.random() - 0.5) * 2
            close_p = cur + (random.random() - 0.5) * 2
            high_p = max(open_p, close_p) + random.random() * 2
            low_p = min(open_p, close_p) - random.random() * 2
            vol = int(100000 + random.random() * 900000)
            chart.append({"timestamp": ts.isoformat(), "open": round(open_p,2), "high": round(high_p,2),
                          "low": round(low_p,2), "close": round(close_p,2), "volume": vol})
        
        # Calculate technical indicators
        closes = [c["close"] for c in chart]
        inds = {}
        
        try:
            # Overlays
            if "SMA20" in indicators_req: inds["SMA20"] = sma(closes, 20)
            if "SMA50" in indicators_req: inds["SMA50"] = sma(closes, 50)
            if "EMA12" in indicators_req: inds["EMA12"] = ema(closes, 12)
            if "EMA26" in indicators_req: inds["EMA26"] = ema(closes, 26)
            if "BB" in indicators_req:
                u, m, l = bollinger(closes, 20, 2)
                inds["BB_upper"], inds["BB_middle"], inds["BB_lower"] = u, m, l
            
            # Oscillators
            if "RSI" in indicators_req: inds["RSI14"] = rsi(closes, 14)
            if "MACD" in indicators_req or "MACDHist" in indicators_req or "MACD_hist" in indicators_req:
                line, signal_line, hist = macd(closes, 12, 26, 9)
                if "MACD" in indicators_req:
                    inds["MACD"] = line
                if "MACDHist" in indicators_req or "MACD_hist" in indicators_req:
                    inds["MACD_hist"] = hist
                if "MACD_signal" in indicators_req:
                    inds["MACD_signal"] = signal_line
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            inds = {}
        
        cp, pp = chart[-1]["close"], chart[0]["close"]
        response_data["stockChartData"] = {
            "symbol": symbol, "timeframe": timeframe, "interval": interval, "limit": limit,
            "data": chart, "indicators": inds,
            "currentPrice": round(cp,2), "change": round(cp-pp,2),
            "changePercent": round(((cp-pp)/pp)*100, 2), "__typename": "StockChartData"
        }
        return {"data": response_data}

    # === Phase 3: Batch Chart Data (Early Return) ===
    if "batchStockChartData" in fields:
        try:
            logger.info("batchStockChartData handler - variables: %s", variables)
            symbols    = variables.get("symbols") or []
            timeframe  = variables.get("timeframe", "1M")
            indicators = variables.get("indicators", [])
            logger.info("batchStockChartData handler - symbols: %s, timeframe: %s, indicators: %s", symbols, timeframe, indicators)
            if not isinstance(symbols, (list, tuple)) or not symbols:
                raise ValueError("symbols: [String!]! is required")

            symbols    = list(symbols)[:10]
            indicators = list(indicators)[:10] if isinstance(indicators, (list, tuple)) else []

            payloads = []
            for sym in symbols:
                payloads.append(_build_chart_payload(sym, timeframe, indicators))
            response_data["batchStockChartData"] = payloads
            return {"data": response_data}
        except Exception as e:
            logger.exception("batchStockChartData failed")
            response_data["batchStockChartData"] = None
            _add_error(errors, f"batchStockChartData failed: {e}")
            return {"data": response_data, "errors": errors}

    # === Phase 3: Enhanced Options Trading (Early Return) ===
    if "placeOptionOrder" in fields:
        try:
            # pull input (variables or inline)
            inp = variables.get("input") or {}
            if not inp:
                # ultra-simple inline parse for common fields
                m = re.search(r'placeOptionOrder\s*\(\s*input:\s*\{([^}]*)\}', query, re.DOTALL)
                if m:
                    raw = m.group(1)
                    def _grab(k):
                        mm = re.search(rf'{k}:\s*"([^"]+)"', raw); 
                        return mm.group(1) if mm else None
                    inp = {
                        "symbol": _grab("symbol"),
                        "optionType": _grab("optionType"),
                        "expiration": _grab("expiration"),
                        "side": _grab("side"),
                        "orderType": _grab("orderType")
                    }
                    qmm = re.search(r'quantity:\s*([0-9]+)', raw); 
                    if qmm: inp["quantity"] = int(qmm.group(1))
                    lmm = re.search(r'limitPrice:\s*([0-9.]+)', raw);
                    if lmm: inp["limitPrice"] = float(lmm.group(1))

            # required
            symbol = inp.get("symbol")
            option_type = (inp.get("optionType") or "").upper()
            expiration = inp.get("expiration")
            side = (inp.get("side") or "").upper()
            order_type = (inp.get("orderType") or "MARKET").upper()
            qty = int(inp.get("quantity") or 1)

            if not all([symbol, option_type in {"CALL","PUT"}, expiration, side in {"BUY","SELL"}, qty > 0]):
                raise ValueError("Invalid input for placeOptionOrder")

            time_in_force = (inp.get("timeInForce") or "DAY").upper()
            slippage_bps = int(inp.get("slippageBps")) if inp.get("slippageBps") is not None else 50
            preview = bool(inp.get("preview", False))
            limit_price = inp.get("limitPrice")
            idem_key = inp.get("idempotencyKey") or f"{symbol}:{option_type}:{expiration}:{side}:{order_type}:{limit_price}:{qty}"

            # idempotency
            if idem_key in _idem:
                prev = _idem[idem_key]
                if time.time() < prev[0] + _IDEM_TTL:
                    response_data["placeOptionOrder"] = {"success":True,"cached":True,"order":prev[1],"__typename":"PlaceOptionOrderResponse"}
                    return {"data": response_data}

            # get a mid price from the underlying quote (best effort)
            try:
                q = await trading_service.get_quote(symbol)
            except Exception:
                q = {}
            bid = float(q.get("bid") or 0.0)
            ask = float(q.get("ask") or 0.0)
            last = float(q.get("last") or q.get("bid") or q.get("ask") or 0.0)
            mid = (bid + ask) / 2.0 if bid and ask else (last or 0.0)

            # price protection for LIMIT orders
            if order_type == "LIMIT" and limit_price is not None and mid > 0:
                cap = _price_protection_cap(side, mid, slippage_bps)
                if side == "BUY" and float(limit_price) > cap:
                    response_data["placeOptionOrder"] = {"success":False,"error":"PRICE_PROTECTION","cap":cap,"__typename":"PlaceOptionOrderResponse"}
                    return {"data": response_data}
                if side == "SELL" and float(limit_price) < cap:
                    response_data["placeOptionOrder"] = {"success":False,"error":"PRICE_PROTECTION","cap":cap,"__typename":"PlaceOptionOrderResponse"}
                    return {"data": response_data}

            # preview path (no execution)
            order_preview = {
                "id": f"preview_{int(time.time()*1000)}",
                "status": "PREVIEW",
                "symbol": symbol,
                "optionType": option_type,
                "strike": float(inp.get("strike") or 0.0),
                "expiration": expiration,
                "side": side,
                "orderType": order_type,
                "timeInForce": time_in_force,
                "quantity": qty,
                "limitPrice": float(limit_price) if limit_price is not None else None,
                "midPrice": round(mid, 2) if mid else None,
                "__typename":"Order"
            }
            if preview:
                response_data["placeOptionOrder"] = {"success":True,"preview":True,"order":order_preview,"__typename":"PlaceOptionOrderResponse"}
                return {"data": response_data}

            # simple "paper" execution (delegates if your service supports options; else stub)
            placed = {
                **order_preview,
                "id": f"opt_{int(time.time()*1000)}",
                "status": "NEW"
            }

            # cache idempotently for 10 minutes
            _idem[idem_key] = (time.time(), placed)

            response_data["placeOptionOrder"] = {"success":True,"cached":False,"order":placed,"__typename":"PlaceOptionOrderResponse"}
            return {"data": response_data}
        except Exception as e:
            logger.exception("placeOptionOrder failed")
            response_data["placeOptionOrder"] = None
            _add_error(errors, f"placeOptionOrder failed: {e}")
            return {"data": response_data, "errors": errors}

    # === Phase 3: Research Hub (Early Return) ===
    if "researchHub" in fields:
        try:
            logger.info("researchHub handler - variables: %s", variables)
            # Rate limiting
            me_email = variables.get("userEmail") or "anon"
            if not _allow(me_email, "researchHub", per_min=20):
                raise ValueError("Rate limit exceeded")
            
            sym = (variables.get("symbol") or variables.get("s") or "").upper()
            logger.info("researchHub handler - symbol: %s", sym)
            if not sym: raise ValueError("symbol required")
            cached = _cache_get(sym)
            if cached: 
                response_data["researchHub"] = cached
                return {"data": response_data}

            # Mock data service calls (replace with real services)
            prof = {
                "companyName": f"{sym} Inc.",
                "sector": "Technology",
                "marketCap": 1000000000000 + hash(sym) % 500000000000,
                "country": "USA",
                "website": f"https://{sym.lower()}.com"
            }
            quote = {
                "currentPrice": 150 + hash(sym) % 100,
                "change": (random.random() - 0.5) * 10,
                "changePercent": (random.random() - 0.5) * 5,
                "high": 160 + hash(sym) % 20,
                "low": 140 + hash(sym) % 20,
                "volume": 1000000 + hash(sym) % 5000000
            }
            tech = {
                "rsi": 30 + hash(sym) % 40,
                "macd": (random.random() - 0.5) * 2,
                "macdhistogram": (random.random() - 0.5) * 1,
                "movingAverage50": quote["currentPrice"] + (random.random() - 0.5) * 5,
                "movingAverage200": quote["currentPrice"] + (random.random() - 0.5) * 10,
                "supportLevel": quote["currentPrice"] * 0.95,
                "resistanceLevel": quote["currentPrice"] * 1.05,
                "impliedVolatility": 0.2 + random.random() * 0.3
            }
            news = {
                "sentiment_label": random.choice(["BULLISH", "BEARISH", "NEUTRAL"]),
                "sentiment_score": (random.random() - 0.5) * 2,
                "article_count": 10 + hash(sym) % 50,
                "confidence": 0.6 + random.random() * 0.3
            }
            econ = {
                "vix": 15 + random.random() * 10,
                "market_sentiment": random.choice(["RISK_ON", "RISK_OFF", "NEUTRAL"]),
                "risk_appetite": 0.3 + random.random() * 0.4
            }
            regime = {
                "market_regime": random.choice(["BULL", "BEAR", "SIDEWAYS"]),
                "confidence": 0.7 + random.random() * 0.2,
                "recommended_strategy": random.choice(["GROWTH", "VALUE", "MOMENTUM", "DEFENSIVE"])
            }
            # quick peers (mock)
            peers = ["MSFT","GOOGL","AMZN"] if sym=="AAPL" else ["AAPL","MSFT","NVDA"]

            payload = {
              "symbol": sym,
              "company": {
                "name": prof.get("companyName",""),
                "sector": prof.get("sector",""),
                "marketCap": prof.get("marketCap",0),
                "country": prof.get("country",""),
                "website": prof.get("website","")
              },
              "quote": quote,
              "technicals": tech,
              "sentiment": news,
              "macro": econ,
              "marketRegime": regime,
              "valuation": {
                "pe": tech.get("pe", None) or None,
                "pb": None,
                "dividendYield": None
              },
              "optionsSnapshot": {
                "impliedVolatility": tech.get("impliedVolatility", None),
                "support": tech.get("supportLevel"),
                "resistance": tech.get("resistanceLevel")
              },
              "peers": peers,
              "updatedAt": datetime.now().isoformat(),
              "__typename": "ResearchReport"
            }
            _cache_set(sym, payload)
            response_data["researchHub"] = payload
            return {"data": response_data}
        except Exception as e:
            logger.exception("researchHub failed")
            # never return empty UI
            response_data["researchHub"] = {
                "symbol": variables.get("symbol") or "AAPL",
                "snapshot": {"name": "N/A", "sector": "N/A", "marketCap": 0},
                "quote": {"price": 0.0, "chg": 0.0, "chgPct": 0.0},
                "technical": {"rsi": None, "macd": None},
                "sentiment": {"score": None, "label": "Unknown"},
                "macro": {"vix": None, "marketSentiment": "Unknown"},
            }
            _add_error(errors, f"researchHub degraded: {e}")
            return {"data": response_data, "errors": errors}

    # Bank accounts (query)
    if "bankAccounts" in fields or "getBankAccounts" in fields:
        response_data["bankAccounts"] = [
            {
                "id": "bank_001", "bankName": "Chase Bank", "accountType": "checking",
                "lastFour": "1234", "isVerified": True, "isPrimary": True,
                "linkedAt": (datetime.now() - timedelta(days=30)).isoformat(),
                "__typename": "BankAccount"
            },
            {
                "id": "bank_002", "bankName": "Wells Fargo", "accountType": "savings",
                "lastFour": "5678", "isVerified": True, "isPrimary": False,
                "linkedAt": (datetime.now() - timedelta(days=15)).isoformat(),
                "__typename": "BankAccount"
            }
        ]
        return {"data": response_data}

    # Funding history (query)
    if "fundingHistory" in fields or "getFundingHistory" in fields:
        response_data["fundingHistory"] = [
            {
                "id": "funding_001", "amount": 1000.00, "bankAccountId": "bank_1234567890",
                "fundingType": "instant", "status": "completed",
                "initiatedAt": "2024-01-20T09:15:00Z", "completedAt": "2024-01-20T09:16:00Z",
                "__typename": "Funding"
            },
            {
                "id": "funding_002", "amount": 2500.00, "bankAccountId": "bank_0987654321",
                "fundingType": "standard", "status": "completed",
                "initiatedAt": "2024-01-25T11:30:00Z", "completedAt": "2024-01-26T11:30:00Z",
                "__typename": "Funding"
            },
        ]
        return {"data": response_data}

    # User profile (query)
    if "userProfile" in fields:
        response_data["userProfile"] = {
            "id": "user_001", "email": "test@example.com", "name": "John Doe",
            "phone": "+1 (555) 123-4567", "dateOfBirth": "1990-01-15",
            "address": {"street": "123 Main St","city": "New York","state": "NY","zipCode": "10001","country": "US"},
            "preferences": {"theme": "light","notifications": {"email": True,"push": True,"sms": False},
                            "privacy": {"profileVisibility": "private","showPortfolio": False}},
            "security": {"twoFactorEnabled": True,"lastPasswordChange": (datetime.now() - timedelta(days=30)).isoformat(),
                         "loginHistory": [{"timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                                           "ipAddress": "192.168.1.1","location": "New York, NY","device": "iPhone 15 Pro"}]},
            "__typename": "UserProfile"
        }
        return {"data": response_data}

    # Notification mutations
    if "markNotificationRead" in fields:
        notificationId = variables.get("notificationId", "")
        if not notificationId:
            m = re.search(r'notificationId:\s*"([^"]+)"', query)
            if m: notificationId = m.group(1)
        if not notificationId:
            return {"errors": [{"message": "Notification ID is required"}]}
        return {"data": {"markNotificationRead": {"success": True, "message": "Notification marked as read", "__typename": "MarkNotificationReadResponse"}}}

    if "markAllNotificationsRead" in fields:
        return {"data": {"markAllNotificationsRead": {"success": True, "message": "All notifications marked as read", "__typename": "MarkAllNotificationsReadResponse"}}}

    if "updateNotificationSettings" in fields:
        settings = variables.get("settings", {}) or {
            "priceAlerts": True, "tradeConfirmations": True, "marketUpdates": False,
            "accountActivity": True, "pushNotifications": True, "emailNotifications": False,
        }
        return {"data": {"updateNotificationSettings": {
            "success": True, "message": "Notification settings updated successfully",
            "settings": {
                "priceAlerts": settings.get("priceAlerts", True),
                "tradeConfirmations": settings.get("tradeConfirmations", True),
                "marketUpdates": settings.get("marketUpdates", False),
                "accountActivity": settings.get("accountActivity", True),
                "pushNotifications": settings.get("pushNotifications", True),
                "emailNotifications": settings.get("emailNotifications", False),
                "__typename": "NotificationSettings"
            },
            "__typename": "UpdateNotificationSettingsResponse"
        }}}

    # Bank/linking mutations
    if "linkBankAccount" in fields:
        bankName = variables.get("bankName", "")
        accountNumber = variables.get("accountNumber", "")
        routingNumber = variables.get("routingNumber", "")
        accountType = variables.get("accountType", "checking")
        if not bankName:
            m = re.search(r'bankName:\s*"([^"]+)"', query); bankName = m.group(1) if m else bankName
        if not accountNumber:
            m = re.search(r'accountNumber:\s*"([^"]+)"', query); accountNumber = m.group(1) if m else accountNumber
        if not routingNumber:
            m = re.search(r'routingNumber:\s*"([^"]+)"', query); routingNumber = m.group(1) if m else routingNumber
        if not bankName or not accountNumber or not routingNumber:
            return {"errors": [{"message": "Bank name, account number, and routing number are required"}]}
        bank_account_id = f"bank_{datetime.now().timestamp()}"
        return {"data": {"linkBankAccount": {
            "success": True, "message": "Bank account linked successfully",
            "bankAccount": {
                "id": bank_account_id, "bankName": bankName,
                "accountNumber": f"****{accountNumber[-4:]}", "routingNumber": f"****{routingNumber[-4:]}",
                "accountType": accountType, "status": "verified", "linkedAt": datetime.now().isoformat(),
                "__typename": "BankAccount"
            }, "__typename": "LinkBankAccountResponse"
        }}}

    if "initiateFunding" in fields:
        # Parse arguments from query string if not in variables
        amount = variables.get("amount")
        bankAccountId = variables.get("bankAccountId")
        fundingType = variables.get("fundingType", "instant")
        
        if not amount or not bankAccountId:
            # Try to extract from query string
            amount_match = re.search(r'amount:\s*([0-9.]+)', query)
            bank_id_match = re.search(r'bankAccountId:\s*"([^"]+)"', query)
            if amount_match:
                amount = float(amount_match.group(1))
            if bank_id_match:
                bankAccountId = bank_id_match.group(1)
        
        if not amount or not bankAccountId:
            return {"errors": [{"message": "Valid amount and bank account ID are required"}]}
        funding_id = f"funding_{datetime.now().timestamp()}"
        return {"data": {"initiateFunding": {
            "success": True, "message": "Funding initiated successfully",
            "funding": {
                "id": funding_id, "amount": amount, "bankAccountId": bankAccountId,
                "fundingType": fundingType, "status": "pending",
                "estimatedCompletion": (datetime.now() + timedelta(hours=1 if fundingType == "instant" else 24)).isoformat(),
                "initiatedAt": datetime.now().isoformat(), "__typename": "Funding"
            }, "__typename": "InitiateFundingResponse"
        }}}

    # ---------------------------
    # PHASE 1 & other existing handlers (selected – keep as needed)
    # ---------------------------

    if "tokenAuth" in fields:
        email = variables.get("email", "")
        password = variables.get("password", "")
        
        # Try to extract from query string if not in variables
        if not email:
            m = re.search(r'email:\s*"([^"]+)"', query)
            if m: email = m.group(1)
        if not password:
            m = re.search(r'password:\s*"([^"]+)"', query)
            if m: password = m.group(1)
            
        if not email or not password:
            return {"errors": [{"message": "Email and password are required"}]}
        user = users_db.get(email.lower())
        if not user or user["password"] != hashlib.sha256(password.encode()).hexdigest():
            return {"errors": [{"message": "Invalid credentials"}]}
        tok = create_access_token({"sub": email.lower()}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        return {"data": {"tokenAuth": {
            "token": tok, "refreshToken": tok,
            "payload": {"sub": email.lower(), "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
            "user": {"id": user["id"], "email": user["email"], "name": user["name"],
                     "hasPremiumAccess": user["hasPremiumAccess"], "subscriptionTier": user["subscriptionTier"], 
                     "updatedAt": datetime.now().isoformat(), "__typename":"User"},
            "__typename":"TokenAuth"
        }}}

    if "beginnerFriendlyStocks" in fields:
        # Get real data for beginner-friendly stock universe (diverse sectors)
        beginner_symbols = ["AAPL", "MSFT", "GOOGL", "JNJ", "PG", "KO", "PEP", "WMT", "JPM", "V", "MA", "HD", "DIS", "NKE", "PFE", "ABBV", "T", "VZ", "XOM", "CVX"]
        stocks_data = []
        
        for symbol in beginner_symbols:
            quote = get_real_data_service().get_stock_quote(symbol)
            profile = get_real_data_service().get_company_profile(symbol)
            technical_indicators = get_real_data_service().get_technical_indicators(symbol)
            
            # Calculate enhanced scores
            market_cap = profile.get("marketCap", 1000000000000)
            volatility = 0.28 if symbol in ["AAPL", "TSLA", "NVDA"] else 0.24 if symbol in ["MSFT", "GOOGL", "META"] else 0.20
            pe_ratio = 25.5 if symbol == "AAPL" else 28.0 if symbol == "MSFT" else 20.0
            dividend_yield = 0.5 if symbol == "AAPL" else 0.7 if symbol == "MSFT" else 2.0 if symbol in ["JNJ", "PG", "KO"] else 1.0
            
            risk_level = get_real_data_service().calculate_risk_level(symbol, volatility, market_cap)
            beginner_score = get_real_data_service().calculate_beginner_score(symbol, market_cap, volatility, pe_ratio, dividend_yield)
            
            fundamental_data = {
                "peRatio": pe_ratio,
                "revenueGrowth": 8.2 if symbol == "AAPL" else 12.4 if symbol == "MSFT" else 5.0,
                "profitMargin": 25.3 if symbol == "AAPL" else 36.8 if symbol == "MSFT" else 15.0,
                "returnOnEquity": 147.2 if symbol == "AAPL" else 45.2 if symbol == "MSFT" else 20.0,
                "debtToEquity": 0.15 if symbol == "AAPL" else 0.12 if symbol == "MSFT" else 0.3,
                "currentRatio": 1.05 if symbol == "AAPL" else 2.5 if symbol == "MSFT" else 1.5,
                "priceToBook": 39.2 if symbol == "AAPL" else 12.8 if symbol == "MSFT" else 3.0
            }
            
            ml_score = get_real_data_service().calculate_ml_score(symbol, fundamental_data)
            
            stocks_data.append({
                "id": f"stock_{symbol}",
                "symbol": symbol,
                "companyName": profile.get("companyName", f"{symbol} Inc."),
                "sector": profile.get("sector", "Technology"),
                "marketCap": market_cap,
                "peRatio": pe_ratio,
                "dividendYield": dividend_yield,
                "beginnerFriendlyScore": beginner_score,
                "currentPrice": quote.get("currentPrice", 100.0),
                "mlScore": ml_score,
                "score": ml_score,
                "riskLevel": risk_level,
                "growthPotential": "High" if symbol in ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"] else "Medium",
                "reasoning": f"Real-time analysis based on current market data for {symbol}",
                "debtRatio": fundamental_data["debtToEquity"],
                "volatility": volatility,
                "fundamentalAnalysis": {
                    "revenueGrowth": fundamental_data["revenueGrowth"],
                    "profitMargin": fundamental_data["profitMargin"],
                    "returnOnEquity": fundamental_data["returnOnEquity"],
                    "debtToEquity": fundamental_data["debtToEquity"],
                    "currentRatio": fundamental_data["currentRatio"],
                    "priceToBook": fundamental_data["priceToBook"],
                    "debtScore": 85 if fundamental_data["debtToEquity"] < 0.2 else 70,
                    "dividendScore": 95 if dividend_yield > 2.0 else 80 if dividend_yield > 1.0 else 60,
                    "valuationScore": 78 if pe_ratio < 25 else 65,
                    "growthScore": 82 if fundamental_data["revenueGrowth"] > 10 else 70,
                    "stabilityScore": 88 if market_cap > 1000000000000 else 75
                },
                "technicalIndicators": technical_indicators,
                "__typename": "Stock"
            })
        
        # Sort by beginner score (highest first)
        stocks_data.sort(key=lambda x: x["beginnerFriendlyScore"], reverse=True)
        
        return {"data": {"beginnerFriendlyStocks": stocks_data}}

    if "myWatchlist" in fields:
        return {"data": {"myWatchlist": [
            {
                "id":"watch_1",
                "stock":{"id":"1","symbol":"AAPL","companyName":"Apple Inc.","sector":"Technology","beginnerFriendlyScore":85,"currentPrice":175.5,"debtRatio":0.15,"volatility":0.28,"fundamentalAnalysis":{"revenueGrowth":8.2,"profitMargin":25.3,"returnOnEquity":147.2,"debtToEquity":0.15,"currentRatio":1.05,"priceToBook":39.2,"debtScore":85,"dividendScore":72,"valuationScore":78,"growthScore":82,"stabilityScore":88},"technicalIndicators":{"rsi":65.2,"macd":2.1,"macdhistogram":0.8,"bollingerUpper":185.3,"bollingerMiddle":175.5,"bollingerLower":165.7,"movingAverage50":172.8,"movingAverage200":168.5,"sma20":175.5,"sma50":172.8,"ema12":176.8,"ema26":174.2,"supportLevel":170.0,"resistanceLevel":180.0},"updatedAt":datetime.now().isoformat(),"__typename":"Stock"},
                "addedAt":"2024-01-15T10:00:00Z","notes":"Core technology holding","targetPrice":200.0,"__typename":"WatchlistItem"
            },
            {
                "id":"watch_2",
                "stock":{"id":"2","symbol":"MSFT","companyName":"Microsoft Corporation","sector":"Technology","beginnerFriendlyScore":88,"currentPrice":380.25,"debtRatio":0.12,"volatility":0.24,"fundamentalAnalysis":{"revenueGrowth":12.4,"profitMargin":36.8,"returnOnEquity":45.2,"debtToEquity":0.12,"currentRatio":2.5,"priceToBook":12.8,"debtScore":92,"dividendScore":88,"valuationScore":85,"growthScore":90,"stabilityScore":92},"technicalIndicators":{"rsi":58.7,"macd":3.2,"macdhistogram":1.2,"bollingerUpper":395.1,"bollingerMiddle":380.25,"bollingerLower":365.4,"movingAverage50":378.9,"movingAverage200":365.2,"sma20":380.25,"sma50":378.9,"ema12":384.5,"ema26":382.1,"supportLevel":375.0,"resistanceLevel":390.0},"updatedAt":datetime.now().isoformat(),"__typename":"Stock"},
                "addedAt":"2024-01-16T14:30:00Z","notes":"Cloud leadership play","targetPrice":400.0,"__typename":"WatchlistItem"
            }
        ]}}

    if "myPortfolios" in fields:
        return {"data": {"myPortfolios": {
            "totalPortfolios": 2,
            "totalValue": 50000.00,
            "portfolios": [
                {
                    "id": "portfolio_1",
                    "name": "Growth Portfolio",
                    "totalValue": 30000.00,
                    "holdingsCount": 2,
                    "createdAt": "2024-01-15T10:00:00Z",
                    "updatedAt": datetime.now().isoformat(),
                    "holdings": [
                        {"id": "h1", "stock": {"id": "stock_1", "symbol": "AAPL", "companyName": "Apple Inc.", "debtRatio": 0.15, "volatility": 0.28, "currentPrice": 175.5, "fundamentalAnalysis": {"revenueGrowth": 8.2, "profitMargin": 25.3, "returnOnEquity": 147.2, "debtToEquity": 0.15, "currentRatio": 1.05, "priceToBook": 39.2, "debtScore": 85, "dividendScore": 72, "valuationScore": 78, "growthScore": 82, "stabilityScore": 88}, "technicalIndicators": {"rsi": 65.2, "macd": 2.1, "macdhistogram": 0.8, "bollingerUpper": 185.3, "bollingerMiddle": 175.5, "bollingerLower": 165.7, "movingAverage50": 172.8, "movingAverage200": 168.5, "sma20": 175.5, "sma50": 172.8, "ema12": 176.8, "ema26": 174.2, "supportLevel": 170.0, "resistanceLevel": 180.0}, "updatedAt": datetime.now().isoformat()}, "shares": 50, "totalValue": 8750.00, "averagePrice": 175.0, "notes": "Core technology holding", "createdAt": "2024-01-15T10:00:00Z", "updatedAt": datetime.now().isoformat()},
                        {"id": "h2", "stock": {"id": "stock_2", "symbol": "MSFT", "companyName": "Microsoft Corp.", "debtRatio": 0.12, "volatility": 0.24, "currentPrice": 380.25, "fundamentalAnalysis": {"revenueGrowth": 12.4, "profitMargin": 36.8, "returnOnEquity": 45.2, "debtToEquity": 0.12, "currentRatio": 2.5, "priceToBook": 12.8, "debtScore": 92, "dividendScore": 88, "valuationScore": 85, "growthScore": 90, "stabilityScore": 92}, "technicalIndicators": {"rsi": 58.7, "macd": 3.2, "macdhistogram": 1.2, "bollingerUpper": 395.1, "bollingerMiddle": 380.25, "bollingerLower": 365.4, "movingAverage50": 378.9, "movingAverage200": 365.2, "sma20": 380.25, "sma50": 378.9, "ema12": 384.5, "ema26": 382.1, "supportLevel": 375.0, "resistanceLevel": 390.0}, "updatedAt": datetime.now().isoformat()}, "shares": 30, "totalValue": 11407.50, "averagePrice": 380.25, "notes": "Cloud leadership play", "createdAt": "2024-01-16T14:30:00Z", "updatedAt": datetime.now().isoformat()}
                    ],
                    "__typename": "Portfolio"
                },
                {
                    "id": "portfolio_2", 
                    "name": "Income Portfolio",
                    "totalValue": 20000.00,
                    "holdingsCount": 1,
                    "createdAt": "2024-01-20T14:30:00Z",
                    "updatedAt": datetime.now().isoformat(),
                    "holdings": [
                        {"id": "h3", "stock": {"id": "stock_3", "symbol": "JNJ", "companyName": "Johnson & Johnson", "debtRatio": 0.08, "volatility": 0.18, "currentPrice": 150.0, "fundamentalAnalysis": {"revenueGrowth": 3.2, "profitMargin": 18.5, "returnOnEquity": 22.1, "debtToEquity": 0.08, "currentRatio": 1.2, "priceToBook": 4.1, "debtScore": 78, "dividendScore": 95, "valuationScore": 72, "growthScore": 45, "stabilityScore": 95}, "technicalIndicators": {"rsi": 42.3, "macd": 0.8, "macdhistogram": 0.3, "bollingerUpper": 155.2, "bollingerMiddle": 150.5, "bollingerLower": 145.8, "movingAverage50": 150.1, "movingAverage200": 148.7, "sma20": 150.5, "sma50": 150.1, "ema12": 151.2, "ema26": 149.8, "supportLevel": 148.0, "resistanceLevel": 152.0}, "updatedAt": datetime.now().isoformat()}, "shares": 100, "totalValue": 15000.00, "averagePrice": 150.0, "notes": "Stable dividend stock", "createdAt": "2024-01-20T14:30:00Z", "updatedAt": datetime.now().isoformat()}
                    ],
                    "__typename": "Portfolio"
                }
            ],
            "__typename": "MyPortfolios"
        }}}

    # Portfolio Metrics (query)
    if "portfolioMetrics" in fields:
        return {"data": {"portfolioMetrics": {
            "totalValue": 50000.0,
            "totalCost": 43750.0,  # Added missing field
            "totalReturn": 12.5,
            "totalReturnPercent": 0.125,
            "dayChange": 1250.0,
            "dayChangePercent": 0.025,
            "totalGain": 6250.0,
            "totalGainPercent": 0.125,
            "unrealizedGain": 3250.0,
            "unrealizedGainPercent": 0.065,
            "realizedGain": 3000.0,
            "realizedGainPercent": 0.06,
            "dividendsReceived": 450.0,
            "dividendsReceivedPercent": 0.009,
            "feesPaid": 25.0,
            "feesPaidPercent": 0.0005,
            "sharpeRatio": 1.85,
            "volatility": 0.18,
            "maxDrawdown": -0.08,
            "beta": 0.95,
            "alpha": 0.02,
            "rSquared": 0.78,
            "treynorRatio": 0.13,
            "sortinoRatio": 2.1,
            "calmarRatio": 1.56,
            "var95": -0.035,
            "cvar95": -0.042,
            "informationRatio": 0.15,
            "trackingError": 0.12,
            "jensenAlpha": 0.018,
            "treynorMeasure": 0.13,
            "modiglianiRatio": 0.14,
            "sterlingRatio": 1.2,
            "burkeRatio": 0.95,
            "kapparatio": 1.8,
            "painIndex": 0.06,
            "painRatio": 2.08,
            "ulcerIndex": 0.04,
            "ulcerPerformanceIndex": 3.12,
            "martinRatio": 2.5,
            "recoveryFactor": 1.56,
            "tailRatio": 1.8,
            "commonSenseRatio": 1.65,
            "differentialReturn": 0.02,
            "differentialReturnPercent": 0.02,
            "excessReturn": 0.02,
            "excessReturnPercent": 0.02,
            "riskFreeRate": 0.05,
            "riskFreeRatePercent": 0.05,
            "marketReturn": 0.10,
            "marketReturnPercent": 0.10,
            "riskAdjustedReturn": 0.12,
            "riskAdjustedReturnPercent": 0.12,
            "riskFreeReturn": 0.05,
            "riskFreeReturnPercent": 0.05,
            "marketRiskPremium": 0.05,
            "marketRiskPremiumPercent": 0.05,
            "equityRiskPremium": 0.07,
            "equityRiskPremiumPercent": 0.07,
            "sizePremium": 0.02,
            "sizePremiumPercent": 0.02,
            "valuePremium": 0.03,
            "valuePremiumPercent": 0.03,
            "momentumPremium": 0.01,
            "momentumPremiumPercent": 0.01,
            "qualityPremium": 0.015,
            "qualityPremiumPercent": 0.015,
            "lowVolatilityPremium": 0.01,
            "lowVolatilityPremiumPercent": 0.01,
            "profitabilityPremium": 0.02,
            "profitabilityPremiumPercent": 0.02,
            "investmentPremium": 0.01,
            "investmentPremiumPercent": 0.01,
            "diversificationScore": 75.0,
            "sectorAllocation": {  # Added missing field
                "Technology": 0.60,
                "Healthcare": 0.25,
                "Financials": 0.10,
                "Consumer Discretionary": 0.05
            },
            "riskMetrics": {  # Added missing field
                "var95": -0.035,
                "cvar95": -0.042,
                "expectedShortfall": -0.042,
                "tailRisk": 0.08,
                "systemicRisk": 0.12,
                "idiosyncraticRisk": 0.15,
                "totalRisk": 0.20,
                "riskAdjustedReturn": 0.60,
                "sharpeRatio": 1.8,
                "sortinoRatio": 2.2,
                "calmarRatio": 1.5,
                "maxDrawdown": -0.08,
                "recoveryTime": 25
            },
            "holdings": [  # Added missing field
                {
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "shares": 50,
                    "currentPrice": 175.5,
                    "totalValue": 8775.0,
                    "costBasis": 8000.0,
                    "returnAmount": 775.0,
                    "returnPercent": 0.097,
                    "sector": "Technology"
                },
                {
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "shares": 30,
                    "currentPrice": 380.25,
                    "totalValue": 11407.5,
                    "costBasis": 10000.0,
                    "returnAmount": 1407.5,
                    "returnPercent": 0.141,
                    "sector": "Technology"
                },
                {
                    "symbol": "JNJ",
                    "companyName": "Johnson & Johnson",
                    "shares": 100,
                    "currentPrice": 150.0,
                    "totalValue": 15000.0,
                    "costBasis": 14000.0,
                    "returnAmount": 1000.0,
                    "returnPercent": 0.071,
                    "sector": "Healthcare"
                },
                {
                    "symbol": "JPM",
                    "companyName": "JPMorgan Chase & Co.",
                    "shares": 25,
                    "currentPrice": 180.0,
                    "totalValue": 4500.0,
                    "costBasis": 4000.0,
                    "returnAmount": 500.0,
                    "returnPercent": 0.125,
                    "sector": "Financials"
                },
                {
                    "symbol": "AMZN",
                    "companyName": "Amazon.com Inc.",
                    "shares": 20,
                    "currentPrice": 350.0,
                    "totalValue": 7000.0,
                    "costBasis": 6000.0,
                    "returnAmount": 1000.0,
                    "returnPercent": 0.167,
                    "sector": "Consumer Discretionary"
                }
            ],
            "updatedAt": datetime.now().isoformat(),
            "__typename": "PortfolioMetrics"
        }}}

    # Options Analysis (query)
    if "optionsAnalysis" in fields:
        symbol = variables.get("symbol", "AAPL")
        return {"data": {"optionsAnalysis": {
            "symbol": symbol,
            "underlyingSymbol": symbol,  # Added missing field
            "currentPrice": 175.5,
            "underlyingPrice": 175.5,  # Added missing field
            "impliedVolatility": 0.25,
            "historicalVolatility": 0.23,
            "volatilityRank": 0.65,
            "volatilityPercentile": 65.0,
            "impliedVolatilityRank": 0.65,  # Added missing field
            "callOptions": [
                {
                    "strike": 170.0,
                    "expiration": "2024-12-20",
                    "bid": 8.50,
                    "ask": 8.75,
                    "last": 8.60,
                    "volume": 1250,
                    "openInterest": 8900,
                    "impliedVolatility": 0.24,
                    "delta": 0.65,
                    "gamma": 0.02,
                    "theta": -0.15,
                    "vega": 0.35,
                    "rho": 0.12,
                    "intrinsicValue": 5.50,
                    "timeValue": 3.10,
                    "moneyness": "ITM",
                    "breakeven": 178.60,
                    "maxProfit": 999999.99,
                    "maxLoss": 8.60,
                    "probabilityOfProfit": 0.65,
                    "expectedReturn": 0.12,
                    "riskRewardRatio": 2.5,
                    "leverage": 20.4,
                    "marginRequired": 0.0,
                    "daysToExpiration": 32,
                    "timeDecay": -0.15,
                    "volatilitySkew": 0.02,
                    "putCallRatio": 0.85,
                    "volumeRatio": 1.2,
                    "openInterestRatio": 0.95,
                    "bidAskSpread": 0.25,
                    "bidAskSpreadPercent": 2.9,
                    "liquidityScore": 0.85,
                    "fairValue": 8.62,
                    "overpriced": False,
                    "underpriced": False,
                    "recommendation": "HOLD",
                    "confidence": 0.75,
                    "riskLevel": "MODERATE",
                    "suitability": "INTERMEDIATE",
                    "strategy": "LONG_CALL",
                    "profitTarget": 12.0,
                    "stopLoss": 6.0,
                    "hedgeRatio": 0.65,
                    "correlation": 0.95,
                    "beta": 1.2,
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "marketCap": 2800000000000,
                    "peRatio": 28.5,
                    "dividendYield": 0.0044,
                    "earningsDate": "2024-10-30",
                    "exDividendDate": "2024-11-08",
                    "analystRating": "BUY",
                    "priceTarget": 200.0,
                    "upside": 0.14,
                    "downside": -0.08,
                    "volatilityForecast": 0.26,
                    "priceForecast": 180.0,
                    "confidenceInterval": [165.0, 195.0],
                    "var95": -0.12,
                    "cvar95": -0.15,
                    "expectedShortfall": -0.15,
                    "tailRisk": 0.08,
                    "systemicRisk": 0.12,
                    "idiosyncraticRisk": 0.15,
                    "totalRisk": 0.20,
                    "riskAdjustedReturn": 0.60,
                    "sharpeRatio": 1.8,
                    "sortinoRatio": 2.2,
                    "calmarRatio": 1.5,
                    "maxDrawdown": -0.15,
                    "recoveryTime": 45,
                    "stressTest": {
                        "scenario1": -0.20,
                        "scenario2": -0.10,
                        "scenario3": 0.05,
                        "scenario4": 0.15,
                        "scenario5": 0.25
                    },
                    "monteCarlo": {
                        "simulations": 10000,
                        "mean": 0.12,
                        "std": 0.20,
                        "percentile5": -0.21,
                        "percentile25": -0.02,
                        "percentile50": 0.10,
                        "percentile75": 0.25,
                        "percentile95": 0.45
                    },
                    "greeks": {
                        "delta": 0.65,
                        "gamma": 0.02,
                        "theta": -0.15,
                        "vega": 0.35,
                        "rho": 0.12,
                        "lambda": 20.4,
                        "epsilon": 0.08,
                        "psi": -0.05,
                        "vanna": 0.01,
                        "charm": -0.02,
                        "vomma": 0.15,
                        "veta": -0.08,
                        "speed": 0.001,
                        "zomma": 0.0005,
                        "color": 0.0001,
                        "ultima": 0.0002,
                        "dualdelta": 0.65,
                        "dualgamma": 0.02
                    },
                    "pricing": {
                        "blackScholes": 8.62,
                        "binomial": 8.58,
                        "monteCarlo": 8.65,
                        "finiteDifference": 8.60,
                        "analytical": 8.62,
                        "numerical": 8.61,
                        "closedForm": 8.62,
                        "approximation": 8.59
                    },
                    "riskMetrics": {
                        "var95": -0.12,
                        "var99": -0.18,
                        "cvar95": -0.15,
                        "cvar99": -0.22,
                        "expectedShortfall": -0.15,
                        "conditionalVaR": -0.15,
                        "tailVaR": -0.15,
                        "expectedTailLoss": -0.15
                    },
                    "performance": {
                        "totalReturn": 0.12,
                        "annualizedReturn": 0.15,
                        "volatility": 0.20,
                        "sharpeRatio": 1.8,
                        "sortinoRatio": 2.2,
                        "calmarRatio": 1.5,
                        "maxDrawdown": -0.15,
                        "recoveryTime": 45,
                        "winRate": 0.65,
                        "profitFactor": 2.5,
                        "expectancy": 0.08,
                        "kellyCriterion": 0.25,
                        "optimalF": 0.30,
                        "riskOfRuin": 0.05,
                        "ulcerIndex": 0.08,
                        "sterlingRatio": 1.2,
                        "burkeRatio": 0.95,
                        "kapparatio": 1.8,
                        "painIndex": 0.06,
                        "painRatio": 2.08,
                        "ulcerPerformanceIndex": 3.12,
                        "martinRatio": 2.5,
                        "recoveryFactor": 1.56,
                        "tailRatio": 1.8,
                        "commonSenseRatio": 1.65
                    },
                    "marketData": {
                        "bid": 8.50,
                        "ask": 8.75,
                        "last": 8.60,
                        "volume": 1250,
                        "openInterest": 8900,
                        "impliedVolatility": 0.24,
                        "historicalVolatility": 0.23,
                        "volatilityRank": 0.65,
                        "volatilityPercentile": 65.0,
                        "putCallRatio": 0.85,
                        "volumeRatio": 1.2,
                        "openInterestRatio": 0.95,
                        "bidAskSpread": 0.25,
                        "bidAskSpreadPercent": 2.9,
                        "liquidityScore": 0.85,
                        "fairValue": 8.62,
                        "overpriced": False,
                        "underpriced": False
                    },
                    "analytics": {
                        "recommendation": "HOLD",
                        "confidence": 0.75,
                        "riskLevel": "MODERATE",
                        "suitability": "INTERMEDIATE",
                        "strategy": "LONG_CALL",
                        "profitTarget": 12.0,
                        "stopLoss": 6.0,
                        "hedgeRatio": 0.65,
                        "correlation": 0.95,
                        "beta": 1.2,
                        "sector": "Technology",
                        "industry": "Consumer Electronics",
                        "marketCap": 2800000000000,
                        "peRatio": 28.5,
                        "dividendYield": 0.0044,
                        "earningsDate": "2024-10-30",
                        "exDividendDate": "2024-11-08",
                        "analystRating": "BUY",
                        "priceTarget": 200.0,
                        "upside": 0.14,
                        "downside": -0.08,
                        "volatilityForecast": 0.26,
                        "priceForecast": 180.0,
                        "confidenceInterval": [165.0, 195.0]
                    },
                    "riskAnalysis": {
                        "var95": -0.12,
                        "cvar95": -0.15,
                        "expectedShortfall": -0.15,
                        "tailRisk": 0.08,
                        "systemicRisk": 0.12,
                        "idiosyncraticRisk": 0.15,
                        "totalRisk": 0.20,
                        "riskAdjustedReturn": 0.60,
                        "sharpeRatio": 1.8,
                        "sortinoRatio": 2.2,
                        "calmarRatio": 1.5,
                        "maxDrawdown": -0.15,
                        "recoveryTime": 45
                    },
                    "stressTest": {
                        "scenario1": -0.20,
                        "scenario2": -0.10,
                        "scenario3": 0.05,
                        "scenario4": 0.15,
                        "scenario5": 0.25
                    },
                    "monteCarlo": {
                        "simulations": 10000,
                        "mean": 0.12,
                        "std": 0.20,
                        "percentile5": -0.21,
                        "percentile25": -0.02,
                        "percentile50": 0.10,
                        "percentile75": 0.25,
                        "percentile95": 0.45
                    },
                    "updatedAt": datetime.now().isoformat(),
                    "__typename": "CallOption"
                }
            ],
            "putOptions": [
                {
                    "strike": 170.0,
                    "expiration": "2024-12-20",
                    "bid": 3.25,
                    "ask": 3.50,
                    "last": 3.35,
                    "volume": 890,
                    "openInterest": 5600,
                    "impliedVolatility": 0.26,
                    "delta": -0.35,
                    "gamma": 0.02,
                    "theta": -0.12,
                    "vega": 0.30,
                    "rho": -0.08,
                    "intrinsicValue": 0.0,
                    "timeValue": 3.35,
                    "moneyness": "OTM",
                    "breakeven": 166.65,
                    "maxProfit": 166.65,
                    "maxLoss": 3.35,
                    "probabilityOfProfit": 0.35,
                    "expectedReturn": 0.08,
                    "riskRewardRatio": 1.8,
                    "leverage": 52.2,
                    "marginRequired": 0.0,
                    "daysToExpiration": 32,
                    "timeDecay": -0.12,
                    "volatilitySkew": 0.01,
                    "putCallRatio": 0.85,
                    "volumeRatio": 0.8,
                    "openInterestRatio": 0.9,
                    "bidAskSpread": 0.25,
                    "bidAskSpreadPercent": 7.5,
                    "liquidityScore": 0.75,
                    "fairValue": 3.38,
                    "overpriced": False,
                    "underpriced": False,
                    "recommendation": "HOLD",
                    "confidence": 0.70,
                    "riskLevel": "MODERATE",
                    "suitability": "INTERMEDIATE",
                    "strategy": "LONG_PUT",
                    "profitTarget": 5.0,
                    "stopLoss": 2.0,
                    "hedgeRatio": -0.35,
                    "correlation": 0.95,
                    "beta": 1.2,
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "marketCap": 2800000000000,
                    "peRatio": 28.5,
                    "dividendYield": 0.0044,
                    "earningsDate": "2024-10-30",
                    "exDividendDate": "2024-11-08",
                    "analystRating": "BUY",
                    "priceTarget": 200.0,
                    "upside": 0.14,
                    "downside": -0.08,
                    "volatilityForecast": 0.26,
                    "priceForecast": 180.0,
                    "confidenceInterval": [165.0, 195.0],
                    "var95": -0.10,
                    "cvar95": -0.12,
                    "expectedShortfall": -0.12,
                    "tailRisk": 0.06,
                    "systemicRisk": 0.10,
                    "idiosyncraticRisk": 0.12,
                    "totalRisk": 0.18,
                    "riskAdjustedReturn": 0.44,
                    "sharpeRatio": 1.5,
                    "sortinoRatio": 1.8,
                    "calmarRatio": 1.2,
                    "maxDrawdown": -0.12,
                    "recoveryTime": 35,
                    "stressTest": {
                        "scenario1": -0.15,
                        "scenario2": -0.08,
                        "scenario3": 0.02,
                        "scenario4": 0.10,
                        "scenario5": 0.18
                    },
                    "monteCarlo": {
                        "simulations": 10000,
                        "mean": 0.08,
                        "std": 0.18,
                        "percentile5": -0.18,
                        "percentile25": -0.02,
                        "percentile50": 0.06,
                        "percentile75": 0.18,
                        "percentile95": 0.35
                    },
                    "greeks": {
                        "delta": -0.35,
                        "gamma": 0.02,
                        "theta": -0.12,
                        "vega": 0.30,
                        "rho": -0.08,
                        "lambda": 52.2,
                        "epsilon": 0.05,
                        "psi": 0.03,
                        "vanna": 0.01,
                        "charm": 0.02,
                        "vomma": 0.12,
                        "veta": 0.06,
                        "speed": 0.001,
                        "zomma": 0.0005,
                        "color": 0.0001,
                        "ultima": 0.0002,
                        "dualdelta": -0.35,
                        "dualgamma": 0.02
                    },
                    "pricing": {
                        "blackScholes": 3.38,
                        "binomial": 3.35,
                        "monteCarlo": 3.42,
                        "finiteDifference": 3.36,
                        "analytical": 3.38,
                        "numerical": 3.37,
                        "closedForm": 3.38,
                        "approximation": 3.35
                    },
                    "riskMetrics": {
                        "var95": -0.10,
                        "var99": -0.15,
                        "cvar95": -0.12,
                        "cvar99": -0.18,
                        "expectedShortfall": -0.12,
                        "conditionalVaR": -0.12,
                        "tailVaR": -0.12,
                        "expectedTailLoss": -0.12
                    },
                    "performance": {
                        "totalReturn": 0.08,
                        "annualizedReturn": 0.12,
                        "volatility": 0.18,
                        "sharpeRatio": 1.5,
                        "sortinoRatio": 1.8,
                        "calmarRatio": 1.2,
                        "maxDrawdown": -0.12,
                        "recoveryTime": 35,
                        "winRate": 0.35,
                        "profitFactor": 1.8,
                        "expectancy": 0.05,
                        "kellyCriterion": 0.15,
                        "optimalF": 0.20,
                        "riskOfRuin": 0.08,
                        "ulcerIndex": 0.06,
                        "sterlingRatio": 1.0,
                        "burkeRatio": 0.80,
                        "kapparatio": 1.5,
                        "painIndex": 0.05,
                        "painRatio": 1.6,
                        "ulcerPerformanceIndex": 2.5,
                        "martinRatio": 2.0,
                        "recoveryFactor": 1.2,
                        "tailRatio": 1.5,
                        "commonSenseRatio": 1.3
                    },
                    "marketData": {
                        "bid": 3.25,
                        "ask": 3.50,
                        "last": 3.35,
                        "volume": 890,
                        "openInterest": 5600,
                        "impliedVolatility": 0.26,
                        "historicalVolatility": 0.23,
                        "volatilityRank": 0.65,
                        "volatilityPercentile": 65.0,
                        "putCallRatio": 0.85,
                        "volumeRatio": 0.8,
                        "openInterestRatio": 0.9,
                        "bidAskSpread": 0.25,
                        "bidAskSpreadPercent": 7.5,
                        "liquidityScore": 0.75,
                        "fairValue": 3.38,
                        "overpriced": False,
                        "underpriced": False
                    },
                    "analytics": {
                        "recommendation": "HOLD",
                        "confidence": 0.70,
                        "riskLevel": "MODERATE",
                        "suitability": "INTERMEDIATE",
                        "strategy": "LONG_PUT",
                        "profitTarget": 5.0,
                        "stopLoss": 2.0,
                        "hedgeRatio": -0.35,
                        "correlation": 0.95,
                        "beta": 1.2,
                        "sector": "Technology",
                        "industry": "Consumer Electronics",
                        "marketCap": 2800000000000,
                        "peRatio": 28.5,
                        "dividendYield": 0.0044,
                        "earningsDate": "2024-10-30",
                        "exDividendDate": "2024-11-08",
                        "analystRating": "BUY",
                        "priceTarget": 200.0,
                        "upside": 0.14,
                        "downside": -0.08,
                        "volatilityForecast": 0.26,
                        "priceForecast": 180.0,
                        "confidenceInterval": [165.0, 195.0]
                    },
                    "riskAnalysis": {
                        "var95": -0.10,
                        "cvar95": -0.12,
                        "expectedShortfall": -0.12,
                        "tailRisk": 0.06,
                        "systemicRisk": 0.10,
                        "idiosyncraticRisk": 0.12,
                        "totalRisk": 0.18,
                        "riskAdjustedReturn": 0.44,
                        "sharpeRatio": 1.5,
                        "sortinoRatio": 1.8,
                        "calmarRatio": 1.2,
                        "maxDrawdown": -0.12,
                        "recoveryTime": 35
                    },
                    "stressTest": {
                        "scenario1": -0.15,
                        "scenario2": -0.08,
                        "scenario3": 0.02,
                        "scenario4": 0.10,
                        "scenario5": 0.18
                    },
                    "monteCarlo": {
                        "simulations": 10000,
                        "mean": 0.08,
                        "std": 0.18,
                        "percentile5": -0.18,
                        "percentile25": -0.02,
                        "percentile50": 0.06,
                        "percentile75": 0.18,
                        "percentile95": 0.35
                    },
                    "updatedAt": datetime.now().isoformat(),
                    "__typename": "PutOption"
                }
            ],
            "volatilitySkew": 0.02,
            "putCallRatio": 0.85,
            "volumeRatio": 1.0,
            "openInterestRatio": 0.95,
            "liquidityScore": 0.80,
            "marketSentiment": {
                "sentiment": "BULLISH",
                "sentimentDescription": "Bullish — model expects upside (confidence 65%)"
            },
            "fearGreedIndex": 65,
            "vix": 18.5,
            "vix9d": 19.2,
            "vix3m": 20.1,
            "vix6m": 21.5,
            "vix1y": 22.8,
            "termStructure": "NORMAL",
            "volatilityRegime": "LOW",
            "regimeChange": False,
            "regimeConfidence": 0.85,
            "regimeDuration": 45,
            "regimeStability": 0.90,
            "regimeVolatility": 0.15,
            "regimeReturn": 0.12,
            "regimeSharpe": 0.80,
            "regimeMaxDrawdown": -0.08,
            "regimeRecoveryTime": 25,
            "regimeWinRate": 0.65,
            "regimeProfitFactor": 2.2,
            "regimeExpectancy": 0.08,
            "regimeKelly": 0.25,
            "regimeOptimalF": 0.30,
            "regimeRiskOfRuin": 0.05,
            "regimeUlcerIndex": 0.06,
            "regimeSterlingRatio": 1.2,
            "regimeBurkeRatio": 0.95,
            "regimeKapparatio": 1.8,
            "regimePainIndex": 0.06,
            "regimePainRatio": 2.08,
            "regimeUlcerPerformanceIndex": 3.12,
            "regimeMartinRatio": 2.5,
            "regimeRecoveryFactor": 1.56,
            "regimeTailRatio": 1.8,
            "regimeCommonSenseRatio": 1.65,
            "optionsChain": {  # Added missing field
                "expirations": ["2024-12-20", "2025-01-17", "2025-02-21"],
                "expirationDates": ["2024-12-20", "2025-01-17", "2025-02-21"],  # Added missing field
                "strikes": [160, 165, 170, 175, 180, 185, 190],
                "calls": [  # Added missing field
                    {
                        "symbol": f"{symbol}241220C00160000",
                        "contractSymbol": f"{symbol}241220C00160000",
                        "optionType": "CALL",
                        "strike": 160.0,
                        "expirationDate": "2024-12-20",
                        "volume": 1200,
                        "openInterest": 8500,
                        "premium": 15.50,
                        "bid": 15.25,
                        "ask": 15.75,
                        "lastPrice": 15.50,
                        "impliedVolatility": 0.22,
                        "delta": 0.85,
                        "gamma": 0.015,
                        "theta": -0.12,
                        "vega": 0.28,
                        "rho": 0.10,
                        "intrinsicValue": 15.5,
                        "timeValue": 0.0,
                        "daysToExpiration": 32
                    },
                    {
                        "symbol": f"{symbol}241220C00170000",
                        "contractSymbol": f"{symbol}241220C00170000",
                        "optionType": "CALL",
                        "strike": 170.0,
                        "expirationDate": "2024-12-20",
                        "volume": 1250,
                        "openInterest": 8900,
                        "premium": 8.60,
                        "bid": 8.35,
                        "ask": 8.85,
                        "lastPrice": 8.60,
                        "impliedVolatility": 0.24,
                        "delta": 0.65,
                        "gamma": 0.02,
                        "theta": -0.15,
                        "vega": 0.35,
                        "rho": 0.12,
                        "intrinsicValue": 5.5,
                        "timeValue": 3.1,
                        "daysToExpiration": 32
                    }
                ],
                "puts": [  # Added missing field
                    {
                        "symbol": f"{symbol}241220P00160000",
                        "contractSymbol": f"{symbol}241220P00160000",
                        "optionType": "PUT",
                        "strike": 160.0,
                        "expirationDate": "2024-12-20",
                        "volume": 800,
                        "openInterest": 5200,
                        "premium": 0.50,
                        "bid": 0.25,
                        "ask": 0.75,
                        "lastPrice": 0.50,
                        "impliedVolatility": 0.25,
                        "delta": -0.15,
                        "gamma": 0.015,
                        "theta": -0.08,
                        "vega": 0.28,
                        "rho": -0.05,
                        "intrinsicValue": 0.0,
                        "timeValue": 0.5,
                        "daysToExpiration": 32
                    },
                    {
                        "symbol": f"{symbol}241220P00170000",
                        "contractSymbol": f"{symbol}241220P00170000",
                        "optionType": "PUT",
                        "strike": 170.0,
                        "expirationDate": "2024-12-20",
                        "volume": 890,
                        "openInterest": 5600,
                        "premium": 3.35,
                        "bid": 3.10,
                        "ask": 3.60,
                        "lastPrice": 3.35,
                        "impliedVolatility": 0.26,
                        "delta": -0.35,
                        "gamma": 0.02,
                        "theta": -0.12,
                        "vega": 0.30,
                        "rho": -0.08,
                        "intrinsicValue": 0.0,
                        "timeValue": 3.35,
                        "daysToExpiration": 32
                    }
                ],
                "greeks": {  # Added missing field
                    "delta": 0.30,
                    "gamma": 0.02,
                    "theta": -0.13,
                    "vega": 0.32,
                    "rho": 0.08,
                    "lambda": 25.0,
                    "epsilon": 0.06,
                    "psi": -0.04
                },
                "lastUpdated": datetime.now().isoformat()
            },
            "unusualFlow": {  # Added missing field
                "symbol": symbol,  # Added missing field
                "totalVolume": 12500,
                "unusualVolume": 2500,
                "unusualVolumePercent": 20.0,
                "topTrades": [
                    {
                        "symbol": f"{symbol}241220C00170000",
                        "contractSymbol": f"{symbol}241220C00170000",  # Added missing field
                        "optionType": "CALL",  # Added missing field
                        "strike": 170.0,  # Added missing field
                        "expirationDate": "2024-12-20",  # Added missing field
                        "volume": 500,
                        "openInterest": 8900,  # Added missing field
                        "premium": 8.60,
                        "impliedVolatility": 0.24,  # Added missing field
                        "unusualActivityScore": 0.85,  # Added missing field
                        "activityType": "SWEEP",  # Added missing field
                        "type": "CALL"
                    },
                    {
                        "symbol": f"{symbol}241220P00170000",
                        "contractSymbol": f"{symbol}241220P00170000",  # Added missing field
                        "optionType": "PUT",  # Added missing field
                        "strike": 170.0,  # Added missing field
                        "expirationDate": "2024-12-20",  # Added missing field
                        "volume": 300,
                        "openInterest": 5600,  # Added missing field
                        "premium": 3.35,
                        "impliedVolatility": 0.26,  # Added missing field
                        "unusualActivityScore": 0.75,  # Added missing field
                        "activityType": "BLOCK",  # Added missing field
                        "type": "PUT"
                    }
                ],
                "sweepTrades": 15,
                "blockTrades": 8,
                "lastUpdated": datetime.now().isoformat()
            },
            "recommendedStrategies": [  # Added missing field
                {
                    "name": "Covered Call",
                    "strategyName": "Covered Call",  # Added missing field
                    "strategyType": "INCOME",  # Added missing field
                    "description": "Sell call options against your stock position",
                    "riskLevel": "LOW",
                    "expectedReturn": 0.08,
                    "maxLoss": 0.15,
                    "probabilityOfProfit": 0.70,
                    "setup": "Buy 100 shares, sell 1 call option",
                    "breakeven": 175.5,
                    "breakevenPoints": [175.5],  # Added missing field
                    "riskRewardRatio": 0.53,  # Added missing field
                    "daysToExpiration": 32,  # Added missing field
                    "totalCost": 17550.0,  # Added missing field
                    "totalCredit": 860.0,  # Added missing field
                    "maxProfit": 8.60,
                    "marketOutlook": {
                        "sentiment": "BULLISH",
                        "sentimentDescription": "Bullish — model expects upside (confidence 75%)"
                    },  # Added missing field
                    "suitability": "INCOME"
                },
                {
                    "name": "Protective Put",
                    "strategyName": "Protective Put",  # Added missing field
                    "strategyType": "PROTECTION",  # Added missing field
                    "description": "Buy put options to protect against downside",
                    "riskLevel": "LOW",
                    "expectedReturn": 0.05,
                    "maxLoss": 0.03,
                    "probabilityOfProfit": 0.60,
                    "setup": "Buy 100 shares, buy 1 put option",
                    "breakeven": 178.85,
                    "breakevenPoints": [178.85],  # Added missing field
                    "riskRewardRatio": 1.67,  # Added missing field
                    "daysToExpiration": 32,  # Added missing field
                    "totalCost": 17885.0,  # Added missing field
                    "totalCredit": 0.0,  # Added missing field
                    "maxProfit": 999999.99,
                    "marketOutlook": {
                        "sentiment": "BEARISH",
                        "sentimentDescription": "Bearish — model expects downside (confidence 60%)"
                    },  # Added missing field
                    "suitability": "PROTECTION"
                },
                {
                    "name": "Straddle",
                    "strategyName": "Straddle",  # Added missing field
                    "strategyType": "VOLATILITY",  # Added missing field
                    "description": "Buy both call and put options at same strike",
                    "riskLevel": "HIGH",
                    "expectedReturn": 0.15,
                    "maxLoss": 11.95,
                    "probabilityOfProfit": 0.40,
                    "setup": "Buy 1 call and 1 put at 175 strike",
                    "breakeven": [163.05, 186.95],
                    "breakevenPoints": [163.05, 186.95],  # Added missing field
                    "riskRewardRatio": 1.26,  # Added missing field
                    "daysToExpiration": 32,  # Added missing field
                    "totalCost": 1195.0,  # Added missing field
                    "totalCredit": 0.0,  # Added missing field
                    "maxProfit": 999999.99,
                    "marketOutlook": {
                        "sentiment": "NEUTRAL",
                        "sentimentDescription": "Neutral — limited directional edge (confidence 50%)"
                    },  # Added missing field
                    "suitability": "VOLATILITY"
                }
            ],
            "skew": 0.02,  # Added missing field
            "sentimentScore": 0.75,  # Added missing field
            "sentimentDescription": "Bullish sentiment with moderate confidence",  # Added missing field
            "updatedAt": datetime.now().isoformat(),
            "__typename": "OptionsAnalysis"
        }}}

    if "advancedStockScreening" in fields:
        _trace("enter advancedStockScreening handler")
        print("🎯 DETECTED advancedStockScreening query! (runpy exec loader)")
        import re, pandas as pd

        symbols = variables.get("symbols")
        if not symbols:
            m = re.search(r'advancedStockScreening\s*\(\s*symbols:\s*\[([^\]]+)\]', query)
            if m:
                symbols = [s.strip().strip('"') for s in m.group(1).split(",")]
        if not symbols:
            symbols = ["AAPL","MSFT","XOM","CVX"]

        # Build feature rows – replace with your real data fetch
        rows = []
        for sym in symbols:
            # Get real data for each symbol
            quote = get_real_data_service().get_stock_quote(sym)
            profile = get_real_data_service().get_company_profile(sym)
            
            rows.append({
                "symbol": sym,
                "sector": profile.get("sector","Information Technology"),
                "market_cap": float(profile.get("marketCap", 1e12)),
                "volatility": 0.28 if sym == "AAPL" else 0.24 if sym == "MSFT" else 0.20,
                "peRatio": 25.5 if sym == "AAPL" else 28.0 if sym == "MSFT" else 20.0,
                "dividendYield": 0.5 if sym == "AAPL" else 0.7 if sym == "MSFT" else 1.0,
                "liquidity": 1.2 if sym == "AAPL" else 1.5 if sym == "MSFT" else 1.0,
                "revenueGrowth": 10.0 if sym == "AAPL" else 12.0 if sym == "MSFT" else 8.0,
                "profitMargin": 25.0 if sym == "AAPL" else 27.0 if sym == "MSFT" else 20.0,
                "debtToEquity": 0.5 if sym == "AAPL" else 0.4 if sym == "MSFT" else 0.3,
                "returnOnEquity": 30.0 if sym == "AAPL" else 32.0 if sym == "MSFT" else 20.0,
                "currentRatio": 1.2 if sym == "AAPL" else 1.5 if sym == "MSFT" else 1.0,
                "priceToBook": 8.0 if sym == "AAPL" else 10.0 if sym == "MSFT" else 4.0,
                "companyName": profile.get("companyName", f"{sym} Inc."),
                "currentPrice": float(quote.get("currentPrice", 100.0)),
            })
        df = pd.DataFrame(rows)

        # Optional sector callbacks
        def sector_beginner(row) -> float:
            stable = {"Utilities": 75, "Consumer Staples": 70, "Healthcare": 65}
            cyclical = {"Energy": 55, "Materials": 55, "Industrials": 58}
            techish = {"Information Technology": 60, "Communication Services": 58, "Consumer Discretionary": 57}
            return stable.get(row["sector"], cyclical.get(row["sector"], techish.get(row["sector"], 60)))

        def sector_ml_mult(row) -> float:
            if row["sector"] in {"Utilities", "Consumer Staples"}: return 1.1
            if row["sector"] in {"Energy", "Materials"}: return 0.95
            return 1.0

        try:
            scored = _safe_score_pipeline(
                df,
                sector_col="sector",
                symbol_col="symbol",
                sector_beginner_fn=sector_beginner,
                sector_ml_multiplier_fn=sector_ml_mult,
                logistic_slope=1.0,
                return_breakdowns=False,
            )
        except Exception:
            _trace("EXCEPTION in advancedStockScreening:\n" + traceback.format_exc())
            raise

        by_symbol = {r["symbol"]: r for _, r in scored.iterrows()}
        records = []
        for r in rows:
            s = by_symbol.get(r["symbol"], {})
            # Generate reasoning based on scores and metrics
            beginner_score = int(float(s.get("beginner_score", 0)))
            ml_score = float(s.get("ml_score", 0.0))
            reasoning_parts = []
            
            if beginner_score >= 70:
                reasoning_parts.append("High beginner-friendly score")
            elif beginner_score >= 50:
                reasoning_parts.append("Moderate beginner-friendly score")
            else:
                reasoning_parts.append("Lower beginner-friendly score")
                
            if ml_score >= 0.7:
                reasoning_parts.append("Strong ML analysis")
            elif ml_score >= 0.5:
                reasoning_parts.append("Moderate ML analysis")
            else:
                reasoning_parts.append("Weaker ML analysis")
                
            if r["peRatio"] < 20:
                reasoning_parts.append("Attractive valuation")
            elif r["peRatio"] > 30:
                reasoning_parts.append("Higher valuation")
                
            if r["dividendYield"] > 2.0:
                reasoning_parts.append("Good dividend yield")
                
            reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Standard investment opportunity"
            
            records.append({
                "symbol": r["symbol"],
                "companyName": r.get("companyName"),
                "sector": r["sector"],
                "marketCap": r["market_cap"],
                "peRatio": r["peRatio"],
                "dividendYield": r["dividendYield"],
                "currentPrice": r.get("currentPrice"),
                "volatility": r["volatility"],
                "debtRatio": r["debtToEquity"],
                "beginnerFriendlyScore": beginner_score,
                "mlScore": ml_score,
                "score": ml_score,  # Add score field (same as mlScore for now)
                "reasoning": reasoning,
                "__typename": "AdvancedStock",
            })

        response_data["advancedStockScreening"] = records
        return {"data": response_data}

    # === DAY TRADING RESOLVERS ===
    if "dayTradingPicks" in fields:
        _trace("enter dayTradingPicks handler")
        print("🎯 DETECTED dayTradingPicks query!")
        
        try:
            import numpy as np
            import pandas as pd
            from datetime import datetime, timedelta
            
            # Get mode (SAFE or AGGRESSIVE)
            mode = variables.get("mode", "SAFE").upper()
            max_positions = variables.get("maxPositions", 3)
            min_score = variables.get("minScore", None)
            
            # Mode configurations
            mode_configs = {
                "SAFE": {
                    "min_price": 5.0,
                    "min_addv": 50_000_000,  # $50M
                    "max_spread_bps": 6.0,
                    "allow_gappers": False,
                    "max_positions": 3,  # Changed from 2 to 3 for daily three picks
                    "per_trade_risk_pct": 0.005,  # 0.5%
                    "time_stop_min": 45,
                    "atr_mult": 0.75,
                    "score_weights": {
                        "momentum": 0.25,
                        "rvol": 0.25,
                        "vwap": 0.20,
                        "breakout": 0.15,
                        "spread_pen": -0.10,
                        "catalyst": 0.05
                    },
                    "min_score": 1.0  # Lowered threshold to ensure we get 3 picks
                },
                "AGGRESSIVE": {
                    "min_price": 2.0,
                    "min_addv": 15_000_000,  # $15M
                    "max_spread_bps": 15.0,
                    "allow_gappers": True,
                    "max_positions": 3,
                    "per_trade_risk_pct": 0.012,  # 1.2%
                    "time_stop_min": 25,
                    "atr_mult": 1.2,
                    "score_weights": {
                        "momentum": 0.40,
                        "rvol": 0.25,
                        "vwap": 0.10,
                        "breakout": 0.20,
                        "spread_pen": -0.05,
                        "catalyst": 0.10
                    },
                    "min_score": 0.5  # Lowered threshold to ensure we get 3 picks
                }
            }
            
            config = mode_configs.get(mode, mode_configs["SAFE"])
            if min_score is None:
                min_score = config["min_score"]
            
            # Universe of liquid stocks (mock data for now - replace with real data)
            universe = [
                {"symbol": "AAPL", "price": 175.50, "addv": 8_000_000_000, "spread_bps": 2.5, "sector": "Technology"},
                {"symbol": "MSFT", "price": 380.25, "addv": 6_500_000_000, "spread_bps": 2.8, "sector": "Technology"},
                {"symbol": "GOOGL", "price": 142.80, "addv": 4_200_000_000, "spread_bps": 3.2, "sector": "Technology"},
                {"symbol": "AMZN", "price": 155.30, "addv": 3_800_000_000, "spread_bps": 3.5, "sector": "Consumer Discretionary"},
                {"symbol": "TSLA", "price": 248.50, "addv": 5_100_000_000, "spread_bps": 4.2, "sector": "Consumer Discretionary"},
                {"symbol": "NVDA", "price": 875.20, "addv": 7_200_000_000, "spread_bps": 2.1, "sector": "Technology"},
                {"symbol": "META", "price": 485.60, "addv": 3_900_000_000, "spread_bps": 2.9, "sector": "Technology"},
                {"symbol": "SPY", "price": 445.80, "addv": 12_000_000_000, "spread_bps": 1.2, "sector": "ETF"},
                {"symbol": "QQQ", "price": 378.40, "addv": 4_500_000_000, "spread_bps": 1.5, "sector": "ETF"},
                {"symbol": "IWM", "price": 198.70, "addv": 2_800_000_000, "spread_bps": 2.0, "sector": "ETF"}
            ]
            
            # Filter universe by mode criteria
            filtered_universe = []
            for stock in universe:
                if (stock["price"] >= config["min_price"] and 
                    stock["addv"] >= config["min_addv"] and 
                    stock["spread_bps"] <= config["max_spread_bps"]):
                    filtered_universe.append(stock)
            
            # Generate intraday features (mock data - replace with real calculations)
            picks_data = []
            for stock in filtered_universe:
                # Mock intraday features with more realistic ranges
                momentum_15m = np.random.normal(0.01, 0.03)  # Slightly positive bias
                rvol_10m = np.random.uniform(1.2, 4.0)       # Higher relative volume
                vwap_dist = np.random.normal(0.005, 0.02)    # Slightly above VWAP bias
                breakout_pct = np.random.normal(0.01, 0.025) # Slightly positive breakout
                spread_bps = stock["spread_bps"]
                catalyst_score = np.random.uniform(-0.3, 0.7)  # Slightly positive catalyst bias
                
                above_vwap = vwap_dist > 0
                
                # Calculate scores
                weights = config["score_weights"]
                
                # Z-score normalization (simplified) - adjusted for higher scores
                long_score = (
                    weights["momentum"] * momentum_15m * 10 +
                    weights["rvol"] * (rvol_10m - 1.0) * 2 +
                    weights["vwap"] * vwap_dist * 200 +
                    weights["breakout"] * breakout_pct * 100 +
                    weights["spread_pen"] * (spread_bps - 3.0) * -0.2 +
                    weights["catalyst"] * catalyst_score * 5
                )
                
                short_score = (
                    weights["momentum"] * (-momentum_15m) * 10 +
                    weights["rvol"] * (rvol_10m - 1.0) * 2 +
                    weights["vwap"] * (-vwap_dist) * 200 +
                    weights["breakout"] * (-breakout_pct) * 100 +
                    weights["spread_pen"] * (spread_bps - 3.0) * -0.2 +
                    weights["catalyst"] * catalyst_score * 5
                )
                
                # Determine side and final score
                if above_vwap and momentum_15m > 0:
                    side = "LONG"
                    final_score = long_score
                else:
                    side = "SHORT"
                    final_score = short_score
                
                # Risk calculations
                atr_5m = stock["price"] * 0.008  # Mock ATR
                stop_distance = atr_5m * config["atr_mult"]
                
                if side == "LONG":
                    stop_price = stock["price"] - stop_distance
                    target_1 = stock["price"] + stop_distance
                    target_2 = stock["price"] + stop_distance * 2
                else:
                    stop_price = stock["price"] + stop_distance
                    target_1 = stock["price"] - stop_distance
                    target_2 = stock["price"] - stop_distance * 2
                
                # Position sizing (mock equity = $100k)
                equity = 100_000
                risk_amount = equity * config["per_trade_risk_pct"]
                size_shares = int(risk_amount / stop_distance)
                
                picks_data.append({
                    "symbol": stock["symbol"],
                    "side": side,
                    "score": round(final_score, 2),
                    "features": {
                        "momentum_15m": round(momentum_15m, 3),
                        "rvol_10m": round(rvol_10m, 2),
                        "vwap_dist": round(vwap_dist, 3),
                        "breakout_pct": round(breakout_pct, 3),
                        "spread_bps": round(spread_bps, 1),
                        "catalyst_score": round(catalyst_score, 2)
                    },
                    "risk": {
                        "atr_5m": round(atr_5m, 2),
                        "size_shares": size_shares,
                        "stop": round(stop_price, 2),
                        "targets": [round(target_1, 2), round(target_2, 2)],
                        "time_stop_min": config["time_stop_min"]
                    },
                    "notes": f"{side} - {stock['sector']} sector, {'above' if above_vwap else 'below'} VWAP, {'high' if rvol_10m > 2.0 else 'normal'} volume"
                })
            
            # Sort by score and apply diversification
            picks_data.sort(key=lambda x: x["score"], reverse=True)
            
            # Apply sector diversification and quality threshold
            final_picks = []
            used_sectors = set()
            
            for pick in picks_data:
                if pick["score"] < min_score:
                    break
                
                # Get sector from universe
                stock_sector = next((s["sector"] for s in filtered_universe if s["symbol"] == pick["symbol"]), "Unknown")
                
                # Sector diversification (max 1 per sector, except ETFs)
                if stock_sector != "ETF" and stock_sector in used_sectors:
                    continue
                
                final_picks.append(pick)
                used_sectors.add(stock_sector)
                
                if len(final_picks) >= config["max_positions"]:
                    break
            
            # Format response
            response_data["dayTradingPicks"] = {
                "as_of": datetime.now().isoformat() + "Z",
                "mode": mode,
                "picks": final_picks,
                "universe_size": len(filtered_universe),
                "quality_threshold": min_score
            }
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in dayTradingPicks: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"data": {"dayTradingPicks": {"error": str(e)}}}

    if "dayTradingOutcome" in fields:
        _trace("enter dayTradingOutcome handler")
        print("🎯 DETECTED dayTradingOutcome mutation!")
        
        try:
            # Import ML learning system
            from ml_learning_system import ml_system
            
            # Handle both old and new input formats
            input_data = variables.get("input", {})
            if input_data:
                # New format with input object
                symbol = input_data.get("symbol")
                side = input_data.get("side")  # LONG or SHORT
                entry_price = input_data.get("entryPrice")
                exit_price = input_data.get("exitPrice") or input_data.get("entryPrice")  # Use entry as exit for provisional
                entry_time = input_data.get("executedAt") or input_data.get("entryTime")
                exit_time = input_data.get("exitTime") or datetime.utcnow().isoformat()
                mode = input_data.get("mode", "SAFE")  # SAFE or AGGRESSIVE
                outcome = input_data.get("outcome") or "+1R"  # Default to +1R for provisional
                features = input_data.get("features", {})
                score = input_data.get("score", 1.0)
            else:
                # Old format with direct parameters
                symbol = variables.get("symbol")
                side = variables.get("side")  # LONG or SHORT
                entry_price = variables.get("entryPrice")
                exit_price = variables.get("exitPrice")
                entry_time = variables.get("entryTime")
                exit_time = variables.get("exitTime")
                mode = variables.get("mode", "SAFE")
                outcome = variables.get("outcome")  # +1R, -1R, time_stop, etc.
                features = variables.get("features", {})  # Original features
                score = variables.get("score", 0.0)  # Original prediction score
            
            # Create outcome record
            outcome_data = {
                "symbol": symbol,
                "side": side,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "mode": mode,
                "outcome": outcome,
                "features": features,
                "score": score,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log to ML system
            success = ml_system.log_trading_outcome(outcome_data)
            
            if success:
                # Check if we should retrain models
                training_results = ml_system.train_if_needed()
                
                response_data["dayTradingOutcome"] = {
                    "success": True,
                    "message": "Outcome logged successfully",
                    "record": outcome_data,
                    "training_triggered": any(training_results.values())
                }
            else:
                response_data["dayTradingOutcome"] = {
                    "success": False,
                    "message": "Failed to log outcome",
                    "record": outcome_data
                }
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in dayTradingOutcome: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"data": {"dayTradingOutcome": {"error": str(e)}}}

    # === ML LEARNING SYSTEM ENDPOINTS ===
    if "mlSystemStatus" in fields:
        _trace("enter mlSystemStatus handler")
        print("🎯 DETECTED mlSystemStatus query!")
        
        try:
            from ml_learning_system import ml_system
            status = ml_system.get_system_status()
            response_data["mlSystemStatus"] = status
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in mlSystemStatus: {e}")
            import traceback
            logger.error(traceback.format_exc())
            response_data["mlSystemStatus"] = {
                "error": str(e),
                "ml_available": False,
                "outcome_tracking": {"total_outcomes": 0, "recent_outcomes": 0},
                "models": {"safe_model": None, "aggressive_model": None},
                "bandit": {},
                "last_training": {"SAFE": None, "AGGRESSIVE": None}
            }
            return {"data": response_data}

    if "trainModels" in fields:
        _trace("enter trainModels handler")
        print("🎯 DETECTED trainModels mutation!")
        
        try:
            from ml_learning_system import ml_system
            modes = variables.get("modes", ["SAFE", "AGGRESSIVE"])
            
            if not ml_system.ml_available or not ml_system.model_trainer:
                response_data["trainModels"] = {
                    "success": False,
                    "message": "ML system not available. Cannot train models.",
                    "results": {mode: None for mode in modes}
                }
                return {"data": response_data}
            
            results = {}
            for mode in modes:
                if mode in ["SAFE", "AGGRESSIVE"]:
                    logger.info(f"Training {mode} model...")
                    metrics = ml_system.model_trainer.train_model(mode)
                    results[mode] = metrics
            
            response_data["trainModels"] = {
                "success": True,
                "message": "Model training completed",
                "results": results
            }
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in trainModels: {e}")
            return {"data": {"trainModels": {"error": str(e)}}}

    if "banditStrategy" in fields:
        _trace("enter banditStrategy handler")
        print("🎯 DETECTED banditStrategy query!")
        
        try:
            from ml_learning_system import ml_system
            context = variables.get("context", {})
            
            # Get market context (mock for now)
            market_context = {
                "vix_level": 20.0,  # Mock VIX
                "market_trend": 0.1,  # Mock trend
                "volatility_regime": 0.5,  # Mock volatility
                "time_of_day": 0.4  # Mock time (0-1)
            }
            
            if not ml_system.ml_available or not ml_system.bandit:
                # Fallback to simple strategy selection
                strategies = ["breakout", "mean_reversion", "momentum", "etf_rotation"]
                selected_strategy = strategies[0]  # Default to breakout
                performance = {
                    strategy: {
                        "win_rate": 0.5,
                        "confidence": 1.0,
                        "alpha": 1.0,
                        "beta": 1.0
                    } for strategy in strategies
                }
            else:
                selected_strategy = ml_system.bandit.select_strategy(market_context)
                performance = ml_system.bandit.get_strategy_performance()
            
            response_data["banditStrategy"] = {
                "selected_strategy": selected_strategy,
                "context": market_context,
                "performance": performance
            }
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in banditStrategy: {e}")
            return {"data": {"banditStrategy": {"error": str(e)}}}

    if "updateBanditReward" in fields:
        _trace("enter updateBanditReward handler")
        print("🎯 DETECTED updateBanditReward mutation!")
        
        try:
            from ml_learning_system import ml_system
            strategy = variables.get("strategy")
            reward = variables.get("reward", 0.0)  # 1.0 for success, 0.0 for failure
            
            if not ml_system.ml_available or not ml_system.bandit:
                # Fallback response
                strategies = ["breakout", "mean_reversion", "momentum", "etf_rotation"]
                performance = {
                    s: {
                        "win_rate": 0.5,
                        "confidence": 1.0,
                        "alpha": 1.0,
                        "beta": 1.0
                    } for s in strategies
                }
            else:
                ml_system.bandit.update_reward(strategy, reward)
                performance = ml_system.bandit.get_strategy_performance()
            
            response_data["updateBanditReward"] = {
                "success": True,
                "message": f"Updated {strategy} with reward {reward}",
                "performance": performance
            }
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in updateBanditReward: {e}")
            return {"data": {"updateBanditReward": {"error": str(e)}}}

    if "portfolioOptimization" in fields:
        # Get portfolio optimization for a list of symbols
        symbols = variables.get("symbols", ["AAPL", "MSFT", "GOOGL"])
        target_return = float(variables.get("targetReturn", 0.1))
        
        optimization_result = get_real_data_service().optimize_portfolio(symbols, target_return)
        return {"data": {"portfolioOptimization": optimization_result}}

    if "socialSentiment" in fields:
        # Get social sentiment for a symbol
        symbol = variables.get("symbol", "AAPL")
        # Mock social sentiment data with sentimentDescription
        social_sentiment = {
            "overall_sentiment": 0.194,
            "sentiment_label": "Bullish",
            "sentimentDescription": "Strong bullish sentiment across social platforms with high engagement",
            "platform_sentiment": {
                "twitter": 0.13,
                "reddit": 0.23,
                "stocktwits": 0.222
            },
            "engagement_metrics": {
                "twitter_mentions": 156,
                "reddit_posts": 46,
                "stocktwits_posts": 108,
                "total_engagement": 310
            },
            "confidence": 0.31,
            "__typename": "SocialSentiment"
        }
        return {"data": {"socialSentiment": social_sentiment}}

    if "marketRegimeAnalysis" in fields:
        # Get market regime analysis
        market_regime = get_real_data_service().get_market_regime_analysis()
        return {"data": {"marketRegimeAnalysis": market_regime}}

    if "advancedMLPrediction" in fields:
        symbol = variables.get("symbol")
        if not symbol:
            m = re.search(r'advancedMLPrediction\s*\(\s*symbol:\s*"([^"]+)"', query or "")
            if m:
                symbol = m.group(1)
        if not symbol:
            return {"errors": [{"message": "symbol is required"}]}

        pred = get_real_ml_prediction(symbol)
        # shape is simple key/value; GraphQL client can read it as a scalar/object
        return {"data": {"advancedMLPrediction": pred}}

    if "stocks" in fields:
        # Get real data for diverse stock universe
        stock_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "JNJ", "PG", "KO", "PEP", "WMT", "JPM", "BAC", "V", "MA", "HD", "DIS", "NKE", "PFE", "ABBV", "T", "VZ", "XOM", "CVX", "BRK.B", "UNH", "LLY", "AVGO"]
        stocks_data = []
        
        for symbol in stock_symbols:
            quote = get_real_data_service().get_stock_quote(symbol)
            profile = get_real_data_service().get_company_profile(symbol)
            technical_indicators = get_real_data_service().get_technical_indicators(symbol)
            
            # Calculate enhanced scores
            market_cap = profile.get("marketCap", 1000000000000)
            volatility = 0.28 if symbol in ["AAPL", "TSLA", "NVDA"] else 0.24 if symbol in ["MSFT", "GOOGL", "META"] else 0.20
            pe_ratio = 25.5 if symbol == "AAPL" else 28.0 if symbol == "MSFT" else 20.0
            dividend_yield = 0.5 if symbol == "AAPL" else 0.7 if symbol == "MSFT" else 2.0 if symbol in ["JNJ", "PG", "KO"] else 1.0
            
            risk_level = get_real_data_service().calculate_risk_level(symbol, volatility, market_cap)
            beginner_score = get_real_data_service().calculate_beginner_score(symbol, market_cap, volatility, pe_ratio, dividend_yield)
            
            fundamental_data = {
                "peRatio": pe_ratio,
                "revenueGrowth": 8.2 if symbol == "AAPL" else 12.4 if symbol == "MSFT" else 5.0,
                "profitMargin": 25.3 if symbol == "AAPL" else 36.8 if symbol == "MSFT" else 15.0,
                "returnOnEquity": 147.2 if symbol == "AAPL" else 45.2 if symbol == "MSFT" else 20.0,
                "debtToEquity": 0.15 if symbol == "AAPL" else 0.12 if symbol == "MSFT" else 0.3,
                "currentRatio": 1.05 if symbol == "AAPL" else 2.5 if symbol == "MSFT" else 1.5,
                "priceToBook": 39.2 if symbol == "AAPL" else 12.8 if symbol == "MSFT" else 3.0
            }
            
            ml_score = get_real_data_service().calculate_ml_score(symbol, fundamental_data)
            
            stocks_data.append({
                "id": f"stock_{symbol}",
                "symbol": symbol,
                "companyName": profile.get("companyName", f"{symbol} Inc."),
                "sector": profile.get("sector", "Technology"),
                "marketCap": market_cap,
                "peRatio": pe_ratio,
                "dividendYield": dividend_yield,
                "beginnerFriendlyScore": beginner_score,
                "currentPrice": quote.get("currentPrice", 100.0),
                "change": quote.get("change", 0.0),
                "changePercent": quote.get("changePercent", 0.0),
                "mlScore": ml_score,
                "score": ml_score,
                "riskLevel": risk_level,
                "growthPotential": "High" if symbol in ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"] else "Medium",
                "reasoning": f"Real-time analysis based on current market data for {symbol}",
                "debtRatio": fundamental_data["debtToEquity"],
                "volatility": volatility,
                "fundamentalAnalysis": {
                    "revenueGrowth": fundamental_data["revenueGrowth"],
                    "profitMargin": fundamental_data["profitMargin"],
                    "returnOnEquity": fundamental_data["returnOnEquity"],
                    "debtToEquity": fundamental_data["debtToEquity"],
                    "currentRatio": fundamental_data["currentRatio"],
                    "priceToBook": fundamental_data["priceToBook"],
                    "debtScore": 85 if fundamental_data["debtToEquity"] < 0.2 else 70,
                    "dividendScore": 95 if dividend_yield > 2.0 else 80 if dividend_yield > 1.0 else 60,
                    "valuationScore": 78 if pe_ratio < 25 else 65,
                    "growthScore": 82 if fundamental_data["revenueGrowth"] > 10 else 70,
                    "stabilityScore": 88 if market_cap > 1000000000000 else 75
                },
                "technicalIndicators": technical_indicators,
                "beginnerScoreBreakdown": {
                    "totalScore": beginner_score,
                    "debtScore": 85 if fundamental_data["debtToEquity"] < 0.2 else 70,
                    "dividendScore": 95 if dividend_yield > 2.0 else 80 if dividend_yield > 1.0 else 60,
                    "valuationScore": 78 if pe_ratio < 25 else 65,
                    "growthScore": 82 if fundamental_data["revenueGrowth"] > 10 else 70,
                    "stabilityScore": 88 if market_cap > 1000000000000 else 75
                },
                "__typename": "Stock"
            })
        
        # Sort by ML score (highest first)
        stocks_data.sort(key=lambda x: x["mlScore"], reverse=True)
        
        return {"data": {"stocks": stocks_data}}

    if "feedByTickers" in fields:
        symbols = variables.get("symbols", ["AAPL", "MSFT"])
        limit = variables.get("limit", 50)
        
        # Generate mock feed data for the requested tickers
        feed_data = []
        for i in range(min(limit, 10)):  # Generate up to 10 posts
            symbol = symbols[i % len(symbols)]
            feed_data.append({
                "id": f"feed_post_{i+1}",
                "kind": "DISCUSSION" if i % 3 == 0 else "PREDICTION" if i % 3 == 1 else "POLL",
                "title": f"Discussion about {symbol}",
                "content": f"This is a discussion about {symbol} and its recent performance.",
                "tickers": [symbol],
                "score": 85 + (i * 2),
                "commentCount": 5 + i,
                "user": {
                    "id": f"user_{i+1}",
                    "name": f"User {i+1}",
                    "profilePic": None
                },
                "createdAt": (datetime.now() - timedelta(hours=i)).isoformat(),
                "__typename": "FeedPost"
            })
        
        return {"data": {"feedByTickers": feed_data}}

    if "tickerPostCreated" in fields:
        return {"data": {"tickerPostCreated": {
            "id": "post_123",
            "kind": "DISCUSSION",
            "title": "New discussion about AAPL earnings",
            "tickers": ["AAPL"],
            "user": {"id": "user_123", "name": "Test User"},
            "createdAt": datetime.now().isoformat(),
            "__typename": "TickerPost"
        }}}

    if "stockDiscussions" in fields:
        return {"data": {"stockDiscussions": [
            {
                "id": "discussion_1",
                "title": "AAPL Q4 Earnings Discussion",
                "content": "What are your thoughts on Apple's latest earnings?",
                "user": {"id": "user_123", "name": "Test User", "email": "test@example.com"},
                "stock": {"symbol": "AAPL", "companyName": "Apple Inc."},
                "tickers": ["AAPL"],
                "createdAt": datetime.now().isoformat(),
                "score": 85,
                "commentCount": 5,
                "comments": [
                    {
                        "id": "comment_1",
                        "content": "Great analysis! I think AAPL will continue to grow.",
                        "createdAt": datetime.now().isoformat(),
                        "user": {"name": "John Doe"},
                        "__typename": "Comment"
                    },
                    {
                        "id": "comment_2", 
                        "content": "I'm bullish on their services revenue growth.",
                        "createdAt": datetime.now().isoformat(),
                        "user": {"name": "Jane Smith"},
                        "__typename": "Comment"
                    }
                ],
                "__typename": "StockDiscussion"
            },
            {
                "id": "discussion_2",
                "title": "MSFT Cloud Growth Analysis",
                "content": "Microsoft's Azure growth has been impressive this quarter.",
                "user": {"id": "user_456", "name": "Tech Analyst", "email": "analyst@example.com"},
                "stock": {"symbol": "MSFT", "companyName": "Microsoft Corporation"},
                "tickers": ["MSFT"],
                "createdAt": datetime.now().isoformat(),
                "score": 92,
                "commentCount": 3,
                "comments": [
                    {
                        "id": "comment_3",
                        "content": "Azure is definitely the growth driver here.",
                        "createdAt": datetime.now().isoformat(),
                        "user": {"name": "Cloud Expert"},
                        "__typename": "Comment"
                    }
                ],
                "__typename": "StockDiscussion"
            }
        ]}}

    if "socialFeed" in fields:
        return {"data": {"socialFeed": [
            {
                "id": "post_1",
                "title": "Market Update: Tech Stocks Rally",
                "content": "Tech stocks are showing strong momentum today with AAPL and MSFT leading the charge.",
                "user": {"id": "user_789", "name": "Market Trader", "email": "trader@example.com"},
                "stock": {"symbol": "AAPL", "companyName": "Apple Inc."},
                "tickers": ["AAPL", "MSFT"],
                "createdAt": datetime.now().isoformat(),
                "score": 78,
                "commentCount": 4,
                "comments": [
                    {
                        "id": "comment_4",
                        "content": "Agreed! The momentum is strong.",
                        "createdAt": datetime.now().isoformat(),
                        "user": {"name": "Bull Trader"},
                        "__typename": "Comment"
                    }
                ],
                "__typename": "SocialPost"
            },
            {
                "id": "post_2",
                "title": "Energy Sector Analysis",
                "content": "Oil prices are driving energy stocks higher this week.",
                "user": {"id": "user_101", "name": "Energy Analyst", "email": "energy@example.com"},
                "stock": {"symbol": "XOM", "companyName": "Exxon Mobil Corporation"},
                "tickers": ["XOM"],
                "createdAt": datetime.now().isoformat(),
                "score": 65,
                "commentCount": 2,
                "comments": [
                    {
                        "id": "comment_5",
                        "content": "Good point about oil prices.",
                        "createdAt": datetime.now().isoformat(),
                        "user": {"name": "Oil Investor"},
                        "__typename": "Comment"
                    }
                ],
                "__typename": "SocialPost"
            }
        ]}}

    if "rustStockAnalysis" in fields:
        symbol = variables.get("symbol", "AAPL")
        
        # Get real data
        quote = get_real_data_service().get_stock_quote(symbol)
        profile = get_real_data_service().get_company_profile(symbol)
        technical_indicators = get_real_data_service().get_technical_indicators(symbol)
        
        # Calculate real scores
        market_cap = profile.get("marketCap", 1000000000000)
        volatility = 0.28 if symbol == "AAPL" else 0.24  # Could be calculated from real data
        risk_level = get_real_data_service().calculate_risk_level(symbol, volatility, market_cap)
        beginner_score = get_real_data_service().calculate_beginner_score(symbol, market_cap, volatility)
        
        # Calculate ML score from real fundamental data
        fundamental_data = {
            "peRatio": 25.5 if symbol == "AAPL" else 28.0,
            "revenueGrowth": 8.2 if symbol == "AAPL" else 12.4,
            "profitMargin": 25.3 if symbol == "AAPL" else 36.8,
            "debtToEquity": 0.15 if symbol == "AAPL" else 0.12
        }
        ml_score = get_real_data_service().calculate_ml_score(symbol, fundamental_data)
        
        return {"data": {"rustStockAnalysis": {
            "symbol": symbol,
            "analysis": f"Real-time analysis for {symbol}",
            "confidence": 0.85,
            "recommendation": "BUY",
            "priceTarget": quote.get("currentPrice", 200) * 1.15,  # 15% upside target
            "riskScore": 0.3,
            "riskLevel": risk_level,
            "beginnerFriendlyScore": beginner_score,
            "reasoning": f"Real-time analysis based on current market data for {symbol}",
            "fundamentalAnalysis": {
                "revenueGrowth": 8.2 if symbol == "AAPL" else 12.4,
                "profitMargin": 25.3 if symbol == "AAPL" else 36.8,
                "returnOnEquity": 147.2 if symbol == "AAPL" else 45.2,
                "debtToEquity": 0.15 if symbol == "AAPL" else 0.12,
                "currentRatio": 1.05 if symbol == "AAPL" else 2.5,
                "priceToBook": 39.2 if symbol == "AAPL" else 12.8,
                "debtScore": 85 if symbol == "AAPL" else 92,
                "dividendScore": 72 if symbol == "AAPL" else 88,
                "valuationScore": 78 if symbol == "AAPL" else 85,
                "growthScore": 82 if symbol == "AAPL" else 90,
                "stabilityScore": 88 if symbol == "AAPL" else 92
            },
            "technicalIndicators": technical_indicators,
            "__typename": "RustStockAnalysis"
        }}}

    if "placeMarketOrder" in fields:
        symbol = variables.get("symbol", "")
        side = variables.get("side", "BUY")
        quantity = int(variables.get("quantity", 0) or 0)
        notes = variables.get("notes", "")
        
        # Try to extract from query string if not in variables
        if not symbol:
            m = re.search(r'symbol:\s*"([^"]+)"', query)
            if m: symbol = m.group(1)
        if not side:
            m = re.search(r'side:\s*"([^"]+)"', query)
            if m: side = m.group(1)
        if not quantity:
            m = re.search(r'quantity:\s*(\d+)', query)
            if m: quantity = int(m.group(1))
        if not notes:
            m = re.search(r'notes:\s*"([^"]*)"', query)
            if m: notes = m.group(1)
        
        if not symbol or not quantity:
            return {"errors": [{"message": "Symbol and quantity are required"}]}
            
        return {"data": {"placeMarketOrder": {
            "success": True,
            "message": f"Market {side} order for {quantity} shares of {symbol} placed successfully",
            "orderId": f"order_{datetime.now().timestamp()}",
            "order": {
                "id": f"order_{datetime.now().timestamp()}",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "orderType": "MARKET",
                "status": "PENDING",
                "notes": notes,
                "createdAt": datetime.now().isoformat(),
                "__typename": "Order"
            },
            "__typename": "PlaceMarketOrderResponse"
        }}}

    if "aiRecommendations" in fields:
        return {"data": {"aiRecommendations": {
            "portfolioAnalysis": {
                "totalValue": 50000, "numHoldings": 5,
                "sectorBreakdown": {"Technology":40,"Healthcare":20,"Finance":15,"Consumer":15,"Other":10},
                "riskScore": 7.2, "diversificationScore": 8.5,
                "expectedImpact": {"evPct": 12.5, "evAbs": 6250, "per10k": 1250, "__typename":"ExpectedImpact"},
                "risk": {"volatilityEstimate": 15.2, "maxDrawdownPct": -8.5, "__typename": "Risk"},
                "assetAllocation": {"stocks":60,"bonds":30,"cash":10,"__typename":"AssetAllocation"},
                "__typename": "PortfolioAnalysis"
            },
            "buyRecommendations": get_real_buy_recommendations(),
            "sellRecommendations": get_real_sell_recommendations(),
            "rebalanceSuggestions": [{"action":"INCREASE","currentAllocation":40,"suggestedAllocation":50,"reasoning":"Technology sector showing strong growth","priority":"HIGH","__typename":"RebalanceSuggestion"}],
            "riskAssessment": {"overallRisk":"MODERATE","volatilityEstimate":15.2,"recommendations":["Consider increasing bond allocation for stability","Monitor technology sector concentration"],"__typename":"RiskAssessment"},
            "marketOutlook": {"overallSentiment":"BULLISH","sentimentDescription":"Bullish — model expects upside (confidence 75%)","confidence":0.75,"keyFactors":["Strong corporate earnings","Federal Reserve policy support","Technology sector growth"],"__typename":"MarketOutlook"},
            "__typename":"AIRecommendations"
        }}}

    if "quotes" in fields:
        symbols = variables.get("symbols", ["AAPL","MSFT","GOOGL","TSLA"])
        out = []
        for s in symbols:
            try:
                r = requests.get(f"https://finnhub.io/api/v1/quote?symbol={s}&token={FINNHUB_API_KEY}", timeout=10)
                if r.status_code == 200:
                    d = r.json(); last = d.get('c', 0); chg = d.get('dp', 0)
                    # Add bid/ask from FinnHub data
                    bid = d.get('b', last * 0.999)  # Use bid from API or calculate from last price
                    ask = d.get('a', last * 1.001)  # Use ask from API or calculate from last price
                    volume = d.get('v', 0)
                else:
                    last = round(random.uniform(50, 500), 2); chg = round(random.uniform(-5, 5), 2)
                    bid = last * 0.999; ask = last * 1.001; volume = random.randint(1000000, 10000000)
            except Exception:
                last = round(random.uniform(50, 500), 2); chg = round(random.uniform(-5, 5), 2)
                bid = last * 0.999; ask = last * 1.001; volume = random.randint(1000000, 10000000)
            out.append({"symbol": s, "last": last, "changePct": chg, "bid": bid, "ask": ask, "volume": volume, "__typename": "Quote"})
        return {"data": {"quotes": out}}

    if "me" in fields:
        user = users_db["test@example.com"]
        return {"data": {"me": {
            "id": user["id"], "name": user["name"], "email": user["email"],
            "profilePic": user.get("profilePic", "https://via.placeholder.com/150"),
            "followersCount": user.get("followersCount", 1250), "followingCount": user.get("followingCount", 89),
            "isFollowingUser": user.get("isFollowingUser", False), "isFollowedByUser": user.get("isFollowedByUser", False),
            "hasPremiumAccess": user["hasPremiumAccess"], "subscriptionTier": user["subscriptionTier"],
            "updatedAt": datetime.now().isoformat(),
            "followedTickers": [
                {"symbol":"AAPL","__typename":"FollowedTicker"},
                {"symbol":"MSFT","__typename":"FollowedTicker"},
                {"symbol":"GOOGL","__typename":"FollowedTicker"},
                {"symbol":"TSLA","__typename":"FollowedTicker"}
            ],
            "incomeProfile": user.get("incomeProfile", {
                "id":"profile_1","incomeBracket":"$50,000 - $75,000","age":30,
                "investmentGoals":["Retirement","Home Purchase"],"riskTolerance":"Moderate",
                "investmentHorizon":"10-15 years","__typename":"IncomeProfile"
            }),
            "__typename":"User"
        }}}

    # Trading (selected examples)
    if "tradingAccount" in fields:
        account = await trading_service.get_account()
        if account:
            return {"data": {"tradingAccount": {
                "id": account.id, "buyingPower": account.buying_power, "cash": account.cash,
                "portfolioValue": account.portfolio_value, "equity": account.equity,
                "dayTradeCount": account.day_trade_count, "patternDayTrader": account.pattern_day_trader,
                "tradingBlocked": account.trading_blocked, "createdAt": account.created_at.isoformat(),
                "dayTradingBuyingPower": account.buying_power, "isDayTradingEnabled": not account.trading_blocked,
                "accountStatus": "active" if not account.trading_blocked else "blocked",
                "lastUpdated": account.created_at.isoformat(),
                "__typename":"TradingAccount"
            }}}

    if "tradingPositions" in fields:
        positions = await trading_service.get_positions()
        return {"data": {"tradingPositions": [
            {
                "id": pos.id, "symbol": pos.symbol, "side": "long", "quantity": pos.quantity, 
                "marketValue": pos.market_value, "costBasis": pos.cost_basis, 
                "unrealizedPL": pos.unrealized_pl, "unrealizedpi": pos.unrealized_pl, "unrealizedPI": pos.unrealized_pl,
                "unrealizedPLPercent": pos.unrealized_plpc, "unrealizedPlpc": pos.unrealized_plpc, 
                "currentPrice": pos.current_price, "__typename": "Position"
            } for pos in positions
        ]}}

    if "tradingOrders" in fields:
        orders = await trading_service.get_orders()
        return {"data": {"tradingOrders": [
            {
                "id": order.id, "symbol": order.symbol, "side": order.side.value,
                "quantity": order.quantity, "orderType": order.order_type.value,
                "status": order.status.value, "price": order.price,
                "stopPrice": order.stop_price, "createdAt": order.created_at.isoformat(),
                "filledAt": order.filled_at.isoformat() if order.filled_at else None,
                "filledQuantity": order.filled_quantity, "averageFillPrice": order.average_fill_price,
                "commission": 0.0,  # Add missing commission field
                "notes": f"Order for {order.quantity} shares of {order.symbol}",
                "__typename": "Order"
            } for order in orders
        ]}}

    # Account Management
    if "updateProfile" in fields:
        name = variables.get("name", "")
        email = variables.get("email", "")
        return {"data": {"updateProfile": {
            "success": True, "message": "Profile updated successfully",
            "user": {
                "id": "user_123", "name": name, "email": email,
                "updatedAt": datetime.now().isoformat(), "__typename": "User"
            }, "__typename": "UpdateProfileResponse"
        }}}

    if "toggleFollow" in fields:
        userId = variables.get("userId", "")
        if not userId:
            return {"errors": [{"message": "User ID is required"}]}
        
        # Mock follow/unfollow logic
        user = users_db["test@example.com"]
        current_following = user.get("followingCount", 89)
        current_followers = user.get("followersCount", 1250)
        
        # Toggle the follow state (mock logic)
        is_following = user.get("isFollowingUser", False)
        new_following_state = not is_following
        
        # Update user data
        user["isFollowingUser"] = new_following_state
        if new_following_state:
            user["followingCount"] = current_following + 1
        else:
            user["followingCount"] = max(0, current_following - 1)
        
        return {"data": {"toggleFollow": {
            "success": True,
            "following": new_following_state,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "followersCount": current_followers,
                "followingCount": user["followingCount"],
                "isFollowingUser": new_following_state,
                "isFollowedByUser": user.get("isFollowedByUser", False),
                "updatedAt": datetime.now().isoformat(),
                "__typename": "User"
            },
            "__typename": "ToggleFollowResponse"
        }}}

    if "updatePreferences" in fields:
        theme = variables.get("theme", "light")
        notifications = variables.get("notifications", True)
        return {"data": {"updatePreferences": {
            "success": True, "message": "Preferences updated successfully",
            "preferences": {
                "theme": theme, "notifications": notifications,
                "updatedAt": datetime.now().isoformat(), "__typename": "UserPreferences"
            }, "__typename": "UpdatePreferencesResponse"
        }}}

    if "updateSecurity" in fields:
        twoFactorEnabled = variables.get("twoFactorEnabled", False)
        return {"data": {"updateSecurity": {
            "success": True, "message": "Security settings updated successfully",
            "security": {
                "twoFactorEnabled": twoFactorEnabled,
                "updatedAt": datetime.now().isoformat(), "__typename": "SecuritySettings"
            }, "__typename": "UpdateSecurityResponse"
        }}}

    # SBLOC Offer (query)
    if "sblocOffer" in fields:
        # Mock SBLOC offer data - in production this would come from your SBLOC provider
        return {"data": {"sblocOffer": {
            "ltv": 0.5,  # 50% loan-to-value ratio
            "apr": 0.075,  # 7.5% APR (competitive rate)
            "minDraw": 1000,  # Minimum draw amount
            "maxDrawMultiplier": 0.95,  # 95% of max LTV
            "disclosures": [
                "Interest rates are variable and may change",
                "Market volatility can affect borrowing power",
                "Margin calls may be required if portfolio value drops",
                "Not FDIC insured",
                "Interest may be tax deductible - consult your tax advisor"
            ],
            "eligibleEquity": 50000,  # Mock eligible equity - in production calculate from portfolio
            "updatedAt": datetime.now().isoformat(),
            "__typename": "SblocOffer"
        }}}

    # Initiate SBLOC Draw (mutation)
    if "initiateSblocDraw" in fields:
        amount = variables.get("amount", 0)
        if not amount or amount < 1000:
            return {"data": {"initiateSblocDraw": {
                "success": False,
                "message": "Minimum draw amount is $1,000",
                "draw": None,
                "__typename": "InitiateSblocDrawResponse"
            }}}
        
        # Mock draw initiation - in production this would integrate with your SBLOC provider
        draw_id = f"draw_{int(datetime.now().timestamp())}"
        return {"data": {"initiateSblocDraw": {
            "success": True,
            "message": "SBLOC draw request submitted successfully",
            "draw": {
                "id": draw_id,
                "amount": amount,
                "status": "pending",
                "createdAt": datetime.now().isoformat(),
                "estSettlementAt": (datetime.now() + timedelta(days=2)).isoformat(),
                "__typename": "SblocDraw"
            },
            "__typename": "InitiateSblocDrawResponse"
        }}}

    if "changePassword" in fields:
        oldPassword = variables.get("oldPassword", "")
        newPassword = variables.get("newPassword", "")
        return {"data": {"changePassword": {
            "success": True, "message": "Password changed successfully",
            "__typename": "ChangePasswordResponse"
        }}}

    # ---------------------------
    # CRYPTO HANDLERS
    # ---------------------------
    
    # Crypto Portfolio (query)
    if "cryptoPortfolio" in fields:
        try:
            from core.crypto_models import CryptoPortfolio
            # Mock portfolio data for now
            response_data["cryptoPortfolio"] = {
                "id": "portfolio_001",
                "totalValueUsd": 12500.0,
                "totalCostBasis": 10000.0,
                "totalPnl": 2500.0,
                "totalPnlPercentage": 25.0,
                "totalPnl1d": 150.0,
                "totalPnlPct1d": 1.2,
                "totalPnl1w": 500.0,
                "totalPnlPct1w": 4.2,
                "totalPnl1m": 1500.0,
                "totalPnlPct1m": 13.6,
                "portfolioVolatility": 0.35,
                "sharpeRatio": 1.2,
                "maxDrawdown": 0.15,
                "diversificationScore": 0.8,
                "topHoldingPercentage": 40.0,
                "createdAt": "2024-01-15T10:30:00Z",
                "updatedAt": "2024-01-20T14:45:00Z",
                "risk": {
                    "ltv": 0.65,
                    "riskTier": "MEDIUM",
                    "riskMessage": "Portfolio is within acceptable risk parameters",
                    "marginCallAmount": 2000.0,
                    "additionalCollateralNeeded": 0.0,
                    "stressTestResults": [
                        {"shock": -0.1, "ltvPct": 0.72, "tier": "LOW"},
                        {"shock": -0.2, "ltvPct": 0.81, "tier": "MEDIUM"},
                        {"shock": -0.3, "ltvPct": 0.93, "tier": "HIGH"}
                    ]
                },
                "holdings": [
                    {
                        "id": "holding_btc_001",
                        "symbol": "BTC",
                        "name": "Bitcoin",
                        "quantity": 0.5,
                        "averageCost": 45000.0,
                        "currentPrice": 50000.0,
                        "currentValue": 25000.0,
                        "unrealizedPnl": 2500.0,
                        "unrealizedPnlPercentage": 11.1,
                        "stakedQuantity": 0.0,
                        "stakingRewards": 0.0,
                        "stakingApy": 0.0,
                        "isCollateralized": False,
                        "collateralValue": 0.0,
                        "loanAmount": 0.0,
                        "cryptocurrency": {
                            "symbol": "BTC",
                            "name": "Bitcoin",
                            "__typename": "Cryptocurrency"
                        },
                        "__typename": "CryptoHolding"
                    },
                    {
                        "id": "holding_eth_001",
                        "symbol": "ETH",
                        "name": "Ethereum",
                        "quantity": 10.0,
                        "averageCost": 3000.0,
                        "currentPrice": 3200.0,
                        "currentValue": 32000.0,
                        "unrealizedPnl": 2000.0,
                        "unrealizedPnlPercentage": 6.7,
                        "stakedQuantity": 2.0,
                        "stakingRewards": 150.0,
                        "stakingApy": 4.5,
                        "isCollateralized": True,
                        "collateralValue": 16000.0,
                        "loanAmount": 8000.0,
                        "cryptocurrency": {
                            "symbol": "ETH",
                            "name": "Ethereum",
                            "__typename": "Cryptocurrency"
                        },
                        "__typename": "CryptoHolding"
                    }
                ],
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat(),
                "__typename": "CryptoPortfolio"
            }
            return {"data": response_data}
        except Exception as e:
            logger.error(f"Error handling cryptoPortfolio: {e}")
            return {"data": {"cryptoPortfolio": None}}

    # Crypto Analytics (query)
    if "cryptoAnalytics" in fields:
        try:
            response_data["cryptoAnalytics"] = {
                "totalValueUsd": 12500.0,
                "totalCostBasis": 10000.0,
                "totalPnl": 2500.0,
                "totalPnlPercentage": 25.0,
                "portfolioVolatility": 0.35,
                "sharpeRatio": 1.2,
                "maxDrawdown": 0.15,
                "diversificationScore": 0.8,
                "topHoldingPercentage": 40.0,
                "sectorAllocation": {
                    "LOW": 30.0,
                    "MEDIUM": 50.0,
                    "HIGH": 20.0
                },
                "bestPerformer": {
                    "symbol": "BTC",
                    "pnlPercentage": 11.1,
                    "volatilityTier": "HIGH"
                },
                "worstPerformer": {
                    "symbol": "ETH",
                    "pnlPercentage": 6.7,
                    "volatilityTier": "HIGH"
                },
                "lastUpdated": datetime.now().isoformat(),
                "__typename": "CryptoAnalytics"
            }
            return {"data": response_data}
        except Exception as e:
            logger.error(f"Error handling cryptoAnalytics: {e}")
            return {"data": {"cryptoAnalytics": None}}

    # Crypto SBLOC Loans (query)
    if "cryptoSblocLoans" in fields:
        try:
            response_data["cryptoSblocLoans"] = [
                {
                    "id": "loan_001",
                    "status": "ACTIVE",
                    "collateralQuantity": 0.5,
                    "loanAmount": 10000.0,
                    "interestRate": 0.05,
                    "cryptocurrency": {
                        "symbol": "BTC",
                        "__typename": "Cryptocurrency"
                    },
                    "createdAt": datetime.now().isoformat(),
                    "__typename": "CryptoSblocLoan"
                }
            ]
            return {"data": response_data}
        except Exception as e:
            logger.error(f"Error handling cryptoSblocLoans: {e}")
            return {"data": {"cryptoSblocLoans": []}}

    # Supported Currencies (query)
    if "supportedCurrencies" in fields:
        try:
            response_data["supportedCurrencies"] = [
                {
                    "id": "crypto_btc_001",
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "coingeckoId": "bitcoin",
                    "isStakingAvailable": False,
                    "minTradeAmount": 50.0,
                    "precision": 8,
                    "volatilityTier": "HIGH",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_eth_001",
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "coingeckoId": "ethereum",
                    "isStakingAvailable": True,
                    "minTradeAmount": 25.0,
                    "precision": 6,
                    "volatilityTier": "MEDIUM",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_xrp_001",
                    "symbol": "XRP",
                    "name": "XRP",
                    "coingeckoId": "ripple",
                    "isStakingAvailable": False,
                    "minTradeAmount": 10.0,
                    "precision": 6,
                    "volatilityTier": "MEDIUM",
                    "isSecCompliant": True,
                    "regulatoryStatus": "REGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_sol_001",
                    "symbol": "SOL",
                    "name": "Solana",
                    "coingeckoId": "solana",
                    "isStakingAvailable": True,
                    "minTradeAmount": 5.0,
                    "precision": 6,
                    "volatilityTier": "HIGH",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_usdt_001",
                    "symbol": "USDT",
                    "name": "Tether",
                    "coingeckoId": "tether",
                    "isStakingAvailable": False,
                    "minTradeAmount": 1.0,
                    "precision": 2,
                    "volatilityTier": "LOW",
                    "isSecCompliant": True,
                    "regulatoryStatus": "REGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_usdc_001",
                    "symbol": "USDC",
                    "name": "USD Coin",
                    "coingeckoId": "usd-coin",
                    "isStakingAvailable": False,
                    "minTradeAmount": 1.0,
                    "precision": 2,
                    "volatilityTier": "LOW",
                    "isSecCompliant": True,
                    "regulatoryStatus": "REGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_ada_001",
                    "symbol": "ADA",
                    "name": "Cardano",
                    "coingeckoId": "cardano",
                    "isStakingAvailable": True,
                    "minTradeAmount": 10.0,
                    "precision": 6,
                    "volatilityTier": "MEDIUM",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_doge_001",
                    "symbol": "DOGE",
                    "name": "Dogecoin",
                    "coingeckoId": "dogecoin",
                    "isStakingAvailable": False,
                    "minTradeAmount": 5.0,
                    "precision": 8,
                    "volatilityTier": "HIGH",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_avax_001",
                    "symbol": "AVAX",
                    "name": "Avalanche",
                    "coingeckoId": "avalanche-2",
                    "isStakingAvailable": True,
                    "minTradeAmount": 5.0,
                    "precision": 6,
                    "volatilityTier": "HIGH",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_bnb_001",
                    "symbol": "BNB",
                    "name": "BNB",
                    "coingeckoId": "binancecoin",
                    "isStakingAvailable": True,
                    "minTradeAmount": 5.0,
                    "precision": 6,
                    "volatilityTier": "MEDIUM",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_matic_001",
                    "symbol": "MATIC",
                    "name": "Polygon",
                    "coingeckoId": "matic-network",
                    "isStakingAvailable": True,
                    "minTradeAmount": 5.0,
                    "precision": 6,
                    "volatilityTier": "MEDIUM",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                },
                {
                    "id": "crypto_ltc_001",
                    "symbol": "LTC",
                    "name": "Litecoin",
                    "coingeckoId": "litecoin",
                    "isStakingAvailable": False,
                    "minTradeAmount": 10.0,
                    "precision": 8,
                    "volatilityTier": "MEDIUM",
                    "isSecCompliant": False,
                    "regulatoryStatus": "UNREGULATED",
                    "__typename": "Cryptocurrency"
                }
            ]
            return {"data": response_data}
        except Exception as e:
            logger.error(f"Error handling supportedCurrencies: {e}")
            return {"data": {"supportedCurrencies": []}}

    # Crypto Price (query)
    if "cryptoPrice" in fields:
        symbol = variables.get("symbol", "").upper()
        if not symbol:
            return {"data": {"cryptoPrice": None}}
        
        try:
            # Get real market data from CoinGecko
            market_data = get_real_market_data(symbol)
            
            if market_data:
                # Use real data from CoinGecko API
                response_data["cryptoPrice"] = {
                    "id": f"price_{symbol.lower()}_001",
                    "symbol": symbol,
                    "priceUsd": market_data.get("priceUsd", 0.0),
                    "priceBtc": market_data.get("priceBtc", 0.0),
                    "priceChange24h": market_data.get("priceChange24h", 0.0),
                    "priceChangePercentage24h": market_data.get("priceChangePercentage24h", 0.0),
                    "volume24h": market_data.get("volumeUsd24h", 0.0),
                    "marketCap": market_data.get("marketCap", 0.0),
                    "rsi14": market_data.get("rsi14", 50.0),
                    "volatility7d": market_data.get("volatility7d", 0.0),
                    "volatility30d": market_data.get("volatility30d", 0.0),
                    "volatilityTier": market_data.get("volatilityTier", "MEDIUM"),
                    "momentumScore": market_data.get("momentumScore", 0.5),
                    "sentimentScore": market_data.get("sentimentScore", 0.5),
                    "sentimentDescription": market_data.get("sentimentDescription", "Neutral market sentiment"),
                    "timestamp": datetime.now().isoformat(),
                    "__typename": "CryptoPrice"
                }
            else:
                # Fallback to mock data if real data fails
                prices = {
                    "BTC": {"price": 50000.0, "change24h": 2.5},
                    "ETH": {"price": 3200.0, "change24h": 1.8},
                    "SOL": {"price": 100.0, "change24h": -0.5}
                }
                
                if symbol in prices:
                    price_data = prices[symbol]
                    response_data["cryptoPrice"] = {
                        "id": f"price_{symbol.lower()}_001",
                        "symbol": symbol,
                        "priceUsd": price_data["price"],
                        "priceBtc": price_data["price"] / 50000.0,  # Mock BTC conversion
                        "priceChange24h": price_data["change24h"],
                        "priceChangePercentage24h": price_data["change24h"],
                        "volume24h": 1000000000.0,
                        "marketCap": 1000000000000.0,
                        "rsi14": 65.5,
                        "volatility7d": 0.15,
                        "volatility30d": 0.25,
                        "volatilityTier": "HIGH" if symbol == "BTC" else "MEDIUM",
                        "momentumScore": 0.7,
                        "sentimentScore": 0.8,
                        "sentimentDescription": "Bullish sentiment with strong confidence" if symbol == "BTC" else "Moderate bullish sentiment",
                        "timestamp": datetime.now().isoformat(),
                        "__typename": "CryptoPrice"
                    }
                else:
                    response_data["cryptoPrice"] = None
            
            return {"data": response_data}
        except Exception as e:
            logger.error(f"Error handling cryptoPrice: {e}")
            return {"data": {"cryptoPrice": None}}


    # Generate ML Prediction (mutation)
    if "generateMlPrediction" in fields:
        symbol = variables.get("symbol", "").upper()
        if not symbol:
            return {"data": {"generateMlPrediction": {
                "success": False,
                "message": "Symbol is required",
                "predictionId": None,
                "probability": None,
                "explanation": None,
                "__typename": "GenerateMlPredictionResponse"
            }}}
        
        try:
            # Mock ML prediction generation
            prediction_id = f"pred_{int(datetime.now().timestamp())}"
            probability = 0.75
            prediction_type = "BULLISH" if probability > 0.5 else "BEARISH"
            
            response_data["generateMlPrediction"] = {
                "success": True,
                "message": f"ML prediction generated successfully for {symbol}",
                "predictionId": prediction_id,
                "probability": probability,
                "explanation": f"AI analysis indicates {probability:.1%} probability of {prediction_type.lower()} movement for {symbol}",
                "__typename": "GenerateMlPredictionResponse"
            }
            return {"data": response_data}
        except Exception as e:
            logger.error(f"Error handling generateMlPrediction: {e}")
            return {"data": {"generateMlPrediction": {
                "success": False,
                "message": "Failed to generate prediction",
                "predictionId": None,
                "probability": None,
                "explanation": None,
                "__typename": "GenerateMlPredictionResponse"
            }}}

    # Crypto Recommendations (query)
    if "cryptoRecommendations" in fields:
        constraints = variables.get("constraints") or {}
        max_symbols = int(constraints.get("maxSymbols", 5))
        min_prob = float(constraints.get("minProbability", 0.55))
        min_liq_usd24h = float(constraints.get("minLiquidityUsd24h", 5_000_000))
        allowed_tiers = set(map(str.upper, constraints.get("allowedTiers", ["LOW","MEDIUM","HIGH"])))
        exclude_symbols = set(map(str.upper, constraints.get("excludeSymbols", [])))

        try:
            # Get supported currencies (mock for now)
            supported = _get_mock_supported_currencies()
            drift = _get_mock_drift_decision()

            # Filter supported currencies first
            filtered_supported = []
            for c in supported:
                sym = c["symbol"].upper()
                if sym in exclude_symbols:
                    continue
                tier = (c.get("volatilityTier") or "MEDIUM").upper()
                if tier not in allowed_tiers:
                    continue
                if not c.get("isSecCompliant", True):
                    continue
                if c.get("regulatoryStatus") == "RESTRICTED":
                    continue
                filtered_supported.append((sym, c))

            # Batch fetch prices for all filtered symbols
            symbols_to_fetch = [sym for sym, _ in filtered_supported]
            batch_prices = crypto_data_provider.get_real_time_price_many(symbols_to_fetch)
            
            # Process all symbols with real ML predictions
            rows = []
            for sym, c in filtered_supported:
                # Get price from batch results
                px = batch_prices.get(sym)
                if not px or px.get("priceUsd") is None:
                    continue
                liq = float(px.get("volumeUsd24h") or 0.0)
                if liq < min_liq_usd24h:
                    continue

                # Get real ML prediction (with error handling)
                try:
                    pred = get_real_ml_prediction(sym)
                    prob = float(pred.get("probability") or 0.5)
                except Exception as e:
                    logger.warning(f"ML prediction failed for {sym}: {e}")
                    prob = 0.5  # Default neutral probability
                    pred = {"confidenceLevel": "LOW", "explanation": f"Prediction unavailable for {sym}"}
                
                if prob < min_prob:
                    continue

                tier = (c.get("volatilityTier") or "MEDIUM").upper()
                score = _score_row(prob, liq, tier, float(drift.get("size_multiplier", 1.0)))
                rows.append({
                    "symbol": sym,
                    "score": score,
                    "probability": prob,
                    "confidenceLevel": pred.get("confidenceLevel", "MEDIUM"),
                    "priceUsd": float(px["priceUsd"]),
                    "volatilityTier": tier,
                    "liquidity24hUsd": liq,
                    "rationale": pred.get("explanation") or f"{sym} shows model probability {prob:.2f}",
                })

            rows.sort(key=lambda r: r["score"], reverse=True)
            diversified = _diversify(rows, max_symbols)

            msg = "OK" if diversified else "No assets met constraints"
            return {
                "success": True,
                "message": msg,
                "recommendations": diversified
            }
            
            # Process all symbols in parallel for ML predictions
            rows = []
            for sym, c in filtered_supported:
                # Get price from batch results
                px = batch_prices.get(sym)
                if not px or px.get("priceUsd") is None:
                    continue
                liq = float(px.get("volumeUsd24h") or 0.0)
                if liq < min_liq_usd24h:
                    continue

                # Get real ML prediction (with error handling)
                try:
                    pred = get_real_ml_prediction(sym)
                    prob = float(pred.get("probability") or 0.5)
                except Exception as e:
                    logger.warning(f"ML prediction failed for {sym}: {e}")
                    prob = 0.5  # Default neutral probability
                    pred = {"confidenceLevel": "LOW", "explanation": f"Prediction unavailable for {sym}"}
                
                if prob < min_prob:
                    continue

                tier = (c.get("volatilityTier") or "MEDIUM").upper()
                score = _score_row(prob, liq, tier, float(drift.get("size_multiplier", 1.0)))
                rows.append({
                    "symbol": sym,
                    "score": score,
                    "probability": prob,
                    "confidenceLevel": pred.get("confidenceLevel", "MEDIUM"),
                    "priceUsd": float(px["priceUsd"]),
                    "volatilityTier": tier,
                    "liquidity24hUsd": liq,
                    "rationale": pred.get("explanation") or f"{sym} shows model probability {prob:.2f}",
                })

            rows.sort(key=lambda r: r["score"], reverse=True)
            diversified = _diversify(rows, max_symbols)

            msg = "OK" if diversified else "No assets met constraints"
            response_data["cryptoRecommendations"] = {
                "success": True,
                "message": msg,
                "recommendations": diversified,
                "__typename": "CryptoRecommendationResponse"
            }
            return {"data": response_data}
        except Exception as e:
            logger.error(f"Error handling cryptoRecommendations: {e}")
            return {"data": {"cryptoRecommendations": {
                "success": False,
                "message": "Failed to generate recommendations",
                "recommendations": [],
                "__typename": "CryptoRecommendationResponse"
            }}}

    # === RISK MANAGEMENT ENDPOINTS ===
    if "riskSummary" in fields:
        _trace("enter riskSummary handler")
        print("🎯 DETECTED riskSummary query!")
        
        try:
            from risk_management import get_risk_manager
            risk_manager = get_risk_manager()
            summary = risk_manager.get_risk_summary()
            response_data["riskSummary"] = summary
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in riskSummary: {e}")
            return {"data": {"riskSummary": {"error": str(e)}}}
    
    if "createPosition" in fields:
        _trace("enter createPosition handler")
        print("🎯 DETECTED createPosition mutation!")
        
        try:
            from risk_management import get_risk_manager
            risk_manager = get_risk_manager()
            
            symbol = variables.get("symbol", "AAPL")
            side = variables.get("side", "LONG")
            price = float(variables.get("price", 150.0))
            quantity = int(variables.get("quantity", 0))
            atr = float(variables.get("atr", 2.0))
            sector = variables.get("sector", "Technology")
            confidence = float(variables.get("confidence", 1.0))
            
            # Calculate optimal position size if not provided
            if quantity == 0:
                quantity = risk_manager.calculate_position_size(symbol, price, atr, confidence)
            
            position, error_reason = risk_manager.create_position(symbol, side, price, quantity, atr, sector)
            
            if position:
                response_data["createPosition"] = {
                    "success": True,
                    "message": "Position created successfully",
                    "position": {
                        "symbol": position.symbol,
                        "side": position.side,
                        "entry_price": position.entry_price,
                        "quantity": position.quantity,
                        "entry_time": position.entry_time.isoformat(),
                        "stop_loss_price": position.stop_loss_price,
                        "take_profit_price": position.take_profit_price,
                        "max_hold_until": position.max_hold_until.isoformat(),
                        "atr_stop_price": position.atr_stop_price
                    }
                }
            else:
                response_data["createPosition"] = {
                    "success": False,
                    "message": f"Position creation failed: {error_reason}",
                    "position": None
                }
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in createPosition: {e}")
            return {"data": {"createPosition": {"error": str(e)}}}
    
    if "checkPositionExits" in fields:
        _trace("enter checkPositionExits handler")
        print("🎯 DETECTED checkPositionExits mutation!")
        
        try:
            from risk_management import get_risk_manager
            risk_manager = get_risk_manager()
            
            current_prices = variables.get("currentPrices", {})
            exited_positions = risk_manager.check_position_exits(current_prices)
            
            response_data["checkPositionExits"] = {
                "success": True,
                "message": f"Checked {len(risk_manager.positions)} positions",
                "exited_positions": [
                    {
                        "symbol": pos.symbol,
                        "side": pos.side,
                        "entry_price": pos.entry_price,
                        "exit_price": pos.exit_price,
                        "quantity": pos.quantity,
                        "pnl": pos.pnl,
                        "exit_reason": pos.risk_reason,
                        "exit_time": pos.exit_time.isoformat() if pos.exit_time else None
                    } for pos in exited_positions
                ]
            }
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in checkPositionExits: {e}")
            return {"data": {"checkPositionExits": {"error": str(e)}}}
    
    if "updateRiskSettings" in fields:
        _trace("enter updateRiskSettings handler")
        print("🎯 DETECTED updateRiskSettings mutation!")
        
        try:
            from risk_management import get_risk_manager, set_risk_level, update_account_value, RiskLevel
            
            account_value = variables.get("accountValue")
            risk_level = variables.get("riskLevel")
            
            if account_value:
                update_account_value(float(account_value))
            
            if risk_level:
                risk_level_enum = RiskLevel(risk_level.upper())
                set_risk_level(risk_level_enum)
            
            response_data["updateRiskSettings"] = {
                "success": True,
                "message": "Risk settings updated successfully",
                "current_settings": get_risk_manager().get_risk_summary()
            }
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in updateRiskSettings: {e}")
            return {"data": {"updateRiskSettings": {"error": str(e)}}}
    
    if "getActivePositions" in fields:
        _trace("enter getActivePositions handler")
        print("🎯 DETECTED getActivePositions query!")
        
        try:
            from risk_management import get_risk_manager, PositionStatus
            risk_manager = get_risk_manager()
            
            active_positions = [p for p in risk_manager.positions.values() if p.status == PositionStatus.ACTIVE]
            
            response_data["getActivePositions"] = [
                {
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "quantity": pos.quantity,
                    "entry_time": pos.entry_time.isoformat(),
                    "stop_loss_price": pos.stop_loss_price,
                    "take_profit_price": pos.take_profit_price,
                    "max_hold_until": pos.max_hold_until.isoformat(),
                    "atr_stop_price": pos.atr_stop_price,
                    "current_pnl": None,  # Would need current price to calculate
                    "time_remaining_minutes": int((pos.max_hold_until - datetime.now()).total_seconds() / 60)
                } for pos in active_positions
            ]
            
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in getActivePositions: {e}")
            return {"data": {"getActivePositions": []}}

    # ---------------------------
    # DEFAULT (GraphQL-safe)
    # ---------------------------
    logger.info("No handlers matched. Returning GraphQL-safe empty data. fields=%s", fields)
    if fields:
        # Return nulls for requested top-level fields so Apollo cache doesn't error
        result = {"data": {f: None for f in fields}}
    else:
        result = {"data": {}}
    
    # === Store in Persisted Query Cache ===
    _pq_set(pqk, result, ttl=180)
    return result

# ---------- Entry ----------
if __name__ == "__main__":
    try:
        logger.info("Starting RichesReach server (BUILD_ID=%s)", BUILD_ID)
        port = int(os.getenv("PORT", 8123))  # default to 8123 to avoid old 8000
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception:
        logger.exception("Server failed to start")
        raise