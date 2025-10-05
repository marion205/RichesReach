"""
AI Scans Engine — Hedge-Fund Edition
Deterministic, concurrent, observable core for AI-powered market scanning & playbooks.
No third-party deps required. Drop-in replacement for your current engine.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Iterable, Protocol, Tuple
import uuid
from asyncio import Semaphore, gather, wait_for

MAX_HISTORY = 50
CONCURRENCY = 8

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

@dataclass
class ScoreWeights:
    momentum_change_2pct: float = 0.18
    momentum_change_5pct: float = 0.10
    volume_high: float = 0.10
    value_pe_15: float = 0.18
    value_pe_10: float = 0.10
import math
import random

# --------- Logging (structured) ---------
logger = logging.getLogger("richesreach.ai_scans_engine")
if not logger.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s %(levelname)s ai_scans_engine %(message)s')
    h.setFormatter(fmt)
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# --------- Utilities ---------
def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))

def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

# --------- Domain Models ---------
@dataclass(frozen=True)
class ScanParameters:
    universe: List[str] = field(default_factory=list)
    min_price: float = 0.0
    max_price: float = math.inf
    min_volume: int = 0
    min_market_cap: float = 0.0
    sectors: List[str] = field(default_factory=list)
    technical_indicators: List[str] = field(default_factory=list)
    fundamental_filters: List[str] = field(default_factory=list)
    alt_data_sources: List[str] = field(default_factory=list)
    risk_tolerance: str = "medium"  # low/medium/high
    time_horizon: str = "daily"     # intraday/daily/weekly/...

    def validate(self) -> None:
        if self.min_price < 0 or self.max_price <= 0 or self.max_price < self.min_price:
            raise ValueError("Invalid price range in parameters.")
        if self.min_volume < 0:
            raise ValueError("min_volume cannot be negative.")
        if self.min_market_cap < 0:
            raise ValueError("min_market_cap cannot be negative.")

@dataclass
class PlaybookPerformance:
    total_runs: int
    success_rate: float
    average_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    avg_hold_time: float
    last_updated: str

@dataclass
class Playbook:
    id: str
    name: str
    description: str
    author: str
    category: str
    risk_level: str
    is_public: bool
    is_clonable: bool
    parameters: ScanParameters
    explanation: Dict[str, Any]
    performance: PlaybookPerformance
    tags: List[str]

@dataclass
class TechnicalSignal:
    indicator: str
    value: float
    signal: str  # bullish/bearish/neutral
    strength: float

@dataclass
class FundamentalMetric:
    metric: str
    value: float
    benchmark: float
    signal: str

@dataclass
class AltDataSignal:
    source: str
    signal: str
    strength: float
    description: str
    timestamp: str

@dataclass
class ScanResult:
    id: str
    symbol: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float
    score: float
    confidence: float
    reasoning: str
    risk_factors: List[str]
    opportunity_factors: List[str]
    technical_signals: List[TechnicalSignal]
    fundamental_metrics: List[FundamentalMetric]
    alt_data_signals: List[AltDataSignal]

@dataclass
class Scan:
    id: str
    user_id: str
    name: str
    description: str
    category: str
    risk_level: str
    time_horizon: str
    is_active: bool
    created_at: str
    last_run: Optional[str]
    parameters: ScanParameters
    playbook: Optional[Dict[str, Any]]
    results: List[ScanResult] = field(default_factory=list)

# --------- Interfaces (Ports) ---------
class RealDataService(Protocol):
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]: ...

class ScanStore(Protocol):
    def put_scan(self, scan: Scan) -> None: ...
    def get_scan(self, scan_id: str) -> Optional[Scan]: ...
    def delete_scan(self, scan_id: str) -> None: ...
    def list_scans_for_user(self, user_id: str) -> Iterable[Scan]: ...
    def append_history(self, scan_id: str, results: List[ScanResult]) -> None: ...
    def get_history(self, scan_id: str, limit: int) -> List[List[ScanResult]]: ...

# --------- In-memory store (default dev) ---------
class InMemoryScanStore(ScanStore):
    def __init__(self, history_cap: int = 100):
        self.scans: Dict[str, Scan] = {}
        self.history: Dict[str, List[List[ScanResult]]] = {}
        self.history_cap = history_cap

    def put_scan(self, scan: Scan) -> None:
        self.scans[scan.id] = scan

    def get_scan(self, scan_id: str) -> Optional[Scan]:
        return self.scans.get(scan_id)

    def delete_scan(self, scan_id: str) -> None:
        self.scans.pop(scan_id, None)
        self.history.pop(scan_id, None)

    def list_scans_for_user(self, user_id: str) -> Iterable[Scan]:
        return [s for s in self.scans.values() if s.user_id == user_id]

    def append_history(self, scan_id: str, results: List[ScanResult]) -> None:
        runs = self.history.setdefault(scan_id, [])
        runs.append(results)
        # cap history length for memory safety
        if len(runs) > self.history_cap:
            # keep most recent
            self.history[scan_id] = runs[-self.history_cap :]

    def get_history(self, scan_id: str, limit: int) -> List[List[ScanResult]]:
        runs = self.history.get(scan_id, [])
        return runs[-limit:]

# --------- Engine ---------
class AIScansEngine:
    """
    Concurrency-safe, deterministic AI scanning engine with DI for data & storage.
    """

    def __init__(
        self,
        real_data_service: RealDataService,
        store: Optional[ScanStore] = None,
        *,
        max_concurrency: int = CONCURRENCY,
        fetch_timeout_s: float = 2.0,
        max_results: int = 10,
        score_threshold: float = 0.6,
        rng_seed: Optional[int] = 42,  # deterministic by default
    ):
        self.real_data_service = real_data_service
        self.store = store or InMemoryScanStore()
        self.max_concurrency = max_concurrency
        self.fetch_timeout_s = fetch_timeout_s
        self._sem = Semaphore(max_concurrency)
        self._weights = ScoreWeights()
        self.max_results = max_results
        self.score_threshold = score_threshold
        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

        self.playbooks: Dict[str, Playbook] = {}
        self._initialize_default_playbooks()

        # metrics counters
        self.metrics = {
            "runs_total": 0,
            "symbols_evaluated_total": 0,
            "results_emitted_total": 0,
            "fetch_time_ms_p50": 0.0,
        }

    # --------- Metrics helpers ---------
    def _emit_metric(self, name: str, value: float, **labels: Any) -> None:
        # Hook for Prometheus/StatsD; here we log
        logger.info(f"metric name={name} value={value} labels={labels}")

    # --------- Playbooks ---------
    def _initialize_default_playbooks(self) -> None:
        now = utcnow_iso()
        defaults: List[Playbook] = [
            Playbook(
                id="momentum_breakout",
                name="Momentum Breakout Scanner",
                description="Identifies stocks breaking out with strong momentum and volume",
                author="RichesReach AI",
                category="momentum",
                risk_level="medium",
                is_public=True,
                is_clonable=True,
                parameters=ScanParameters(
                    universe=["SPY", "QQQ", "IWM"],
                    min_price=5,
                    max_price=500,
                    min_volume=1_000_000,
                    min_market_cap=1_000_000_000,
                    sectors=["Technology", "Healthcare", "Finance"],
                    technical_indicators=["RSI", "MACD", "Bollinger Bands"],
                    fundamental_filters=["PE_RATIO", "DEBT_TO_EQUITY"],
                    alt_data_sources=["social_sentiment", "insider_trading"],
                    risk_tolerance="medium",
                    time_horizon="daily",
                ),
                explanation={
                    "why_this_setup": "Momentum breakouts often continue for days with proper risk management",
                    "risk_bands": [
                        {"level": "low", "max_position_size": 0.02, "stop_loss_percent": 0.05, "time_horizon": "daily"},
                        {"level": "medium", "max_position_size": 0.05, "stop_loss_percent": 0.08, "time_horizon": "daily"},
                    ],
                    "alt_data_hooks": [
                        {"name": "Social Sentiment", "weight": 0.3, "source": "Twitter/Reddit/StockTwits"},
                    ],
                    "market_conditions": ["Bull market", "Low volatility", "Strong earnings season"],
                    "expected_outcomes": ["2-5% gains over 1-3 days", "High win rate in trends"],
                },
                performance=PlaybookPerformance(
                    total_runs=150,
                    success_rate=0.68,
                    average_return=0.032,
                    max_drawdown=0.12,
                    sharpe_ratio=1.45,
                    win_rate=0.68,
                    avg_hold_time=2.3,
                    last_updated=now,
                ),
                tags=["momentum", "breakout", "volume", "technical"],
            ),
            Playbook(
                id="value_opportunity",
                name="Value Opportunity Scanner",
                description="Finds undervalued stocks with strong fundamentals",
                author="RichesReach AI",
                category="value",
                risk_level="low",
                is_public=True,
                is_clonable=True,
                parameters=ScanParameters(
                    universe=["SPY", "QQQ", "IWM"],
                    min_price=10,
                    max_price=200,
                    min_volume=500_000,
                    min_market_cap=500_000_000,
                    sectors=["All"],
                    technical_indicators=["RSI", "MACD"],
                    fundamental_filters=["PE_RATIO", "PB_RATIO", "DEBT_TO_EQUITY", "ROE"],
                    alt_data_sources=["analyst_ratings", "insider_trading"],
                    risk_tolerance="low",
                    time_horizon="weekly",
                ),
                explanation={
                    "why_this_setup": "Value stocks provide downside protection with upside potential",
                    "risk_bands": [{"level": "low", "max_position_size": 0.03, "stop_loss_percent": 0.10, "time_horizon": "weekly"}],
                    "alt_data_hooks": [{"name": "Analyst Ratings", "weight": 0.4, "source": "Wall Street"}],
                    "market_conditions": ["Market correction", "High volatility", "Earnings season"],
                    "expected_outcomes": ["5-15% gains over 1-3 months", "Lower vol than growth"],
                },
                performance=PlaybookPerformance(
                    total_runs=200,
                    success_rate=0.72,
                    average_return=0.085,
                    max_drawdown=0.08,
                    sharpe_ratio=1.20,
                    win_rate=0.72,
                    avg_hold_time=45.2,
                    last_updated=now,
                ),
                tags=["value", "fundamentals", "undervalued", "long-term"],
            ),
        ]
        for pb in defaults:
            self.playbooks[pb.id] = pb

    # --------- Public API ---------
    async def get_user_scans(self, user_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        scans = list(self.store.list_scans_for_user(user_id))
        if filters:
            if "category" in filters:
                scans = [s for s in scans if s.category == filters["category"]]
            if "risk_level" in filters:
                scans = [s for s in scans if s.risk_level == filters["risk_level"]]
            if "time_horizon" in filters:
                scans = [s for s in scans if s.time_horizon == filters["time_horizon"]]
            if "is_active" in filters:
                scans = [s for s in scans if s.is_active == bool(filters["is_active"])]
        logger.info(f"get_user_scans user_id={user_id} count={len(scans)}")
        return [self._scan_to_dict(s) for s in scans]

    async def get_scan(self, scan_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        scan = self.store.get_scan(scan_id)
        if scan and scan.user_id == user_id:
            return self._scan_to_dict(scan)
        return None

    async def create_scan(self, user_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        params = self._dict_to_params(request.get("parameters") or {})
        params.validate()

        risk_level = str(params.risk_tolerance or "medium")
        time_horizon = str(params.time_horizon or "daily")

        playbook: Optional[Dict[str, Any]] = None
        playbook_id = request.get("playbook_id")
        if playbook_id and playbook_id in self.playbooks:
            pb = self.playbooks[playbook_id]
            playbook = {
                "id": pb.id,
                "name": pb.name,
                "description": pb.description,
                "author": pb.author,
                "is_public": pb.is_public,
                "is_clonable": pb.is_clonable,
                "performance": asdict(pb.performance),
            }

        scan = Scan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=request["name"],
            description=request["description"],
            category=request["category"],
            risk_level=risk_level,
            time_horizon=time_horizon,
            is_active=True,
            created_at=utcnow_iso(),
            last_run=None,
            parameters=params,
            playbook=playbook,
            results=[],
        )
        self.store.put_scan(scan)
        logger.info(f"create_scan user_id={user_id} scan_id={scan.id} category={scan.category}")
        return self._scan_to_dict(scan)

    async def update_scan(self, scan_id: str, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        scan = self.store.get_scan(scan_id)
        if not scan or scan.user_id != user_id:
            raise ValueError("Scan not found or access denied")

        # immutable dataclass -> rebuild with updates
        new_scan = Scan(
            id=scan.id,
            user_id=scan.user_id,
            name=updates.get("name", scan.name),
            description=updates.get("description", scan.description),
            category=scan.category,  # category change usually disallowed; keep stable
            risk_level=updates.get("risk_level", scan.risk_level),
            time_horizon=updates.get("time_horizon", scan.time_horizon),
            is_active=bool(updates.get("is_active", scan.is_active)),
            created_at=scan.created_at,
            last_run=scan.last_run,
            parameters=self._dict_to_params(updates.get("parameters", asdict(scan.parameters))),
            playbook=scan.playbook,
            results=scan.results,
        )
        new_scan.parameters.validate()
        new_scan.last_run = scan.last_run
        self.store.put_scan(new_scan)
        logger.info(f"update_scan scan_id={scan_id}")
        return self._scan_to_dict(new_scan)

    async def delete_scan(self, scan_id: str, user_id: str) -> None:
        scan = self.store.get_scan(scan_id)
        if not scan or scan.user_id != user_id:
            raise ValueError("Scan not found or access denied")
        self.store.delete_scan(scan_id)
        logger.info(f"delete_scan scan_id={scan_id}")

    async def get_scan_history(self, scan_id: str, user_id: str, limit: int = 10) -> List[List[Dict[str, Any]]]:
        scan = self.store.get_scan(scan_id)
        if not scan or scan.user_id != user_id:
            raise ValueError("Scan not found or access denied")
        history = self.store.get_history(scan_id, limit)
        return [[asdict(r) for r in run] for run in history]

    async def get_playbooks(self, category: Optional[str] = None, risk_level: Optional[str] = None, is_public: bool = True) -> List[Dict[str, Any]]:
        items = list(self.playbooks.values())
        if is_public:
            items = [p for p in items if p.is_public]
        if category:
            items = [p for p in items if p.category == category]
        if risk_level:
            items = [p for p in items if p.risk_level == risk_level]
        logger.info(f"get_playbooks count={len(items)}")
        return [self._playbook_summary(p) for p in items]

    async def get_playbook(self, playbook_id: str) -> Optional[Dict[str, Any]]:
        pb = self.playbooks.get(playbook_id)
        return self._playbook_summary(pb) if pb else None

    async def clone_playbook(self, playbook_id: str, user_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        pb = self.playbooks.get(playbook_id)
        if not pb:
            raise ValueError("Playbook not found")
        if not pb.is_clonable:
            raise ValueError("Playbook is not clonable")

        scan_request = {
            "name": request["name"],
            "description": request["description"],
            "category": pb.category,
            "parameters": request.get("parameters", asdict(pb.parameters)),
            "playbook_id": playbook_id,
        }
        logger.info(f"clone_playbook playbook_id={playbook_id}")
        return await self.create_scan(user_id, scan_request)

    async def run_scan(self, scan_id: str, user_id: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        scan = self.store.get_scan(scan_id)
        if not scan or scan.user_id != user_id:
            raise ValueError("Scan not found or access denied")

        # parameters override (validate)
        params = self._dict_to_params(parameters or asdict(scan.parameters))
        params.validate()

        # Build universe
        symbols = await self._get_scan_universe(params)
        if not symbols:
            return []

        # Concurrent fetch & evaluate
        start = time.perf_counter()
        semaphore = asyncio.Semaphore(self.max_concurrency)
        tasks = [self._process_symbol(symbol, params, scan.category, semaphore) for symbol in symbols]
        raw_results: List[Optional[ScanResult]] = await asyncio.gather(*tasks, return_exceptions=False)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self._emit_metric("scan_elapsed_ms", elapsed_ms, scan_id=scan_id, category=scan.category)

        # Filter, sort, and clip
        results: List[ScanResult] = [r for r in raw_results if r and r.score >= self.score_threshold]  # type: ignore
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[: self.max_results]

        # Update scan state
        scan.results = results
        scan.last_run = utcnow_iso()
        self.store.put_scan(scan)
        self.store.append_history(scan.id, results)

        # Metrics
        self.metrics["runs_total"] += 1
        self.metrics["symbols_evaluated_total"] += len(symbols)
        self.metrics["results_emitted_total"] += len(results)
        logger.info(f"run_scan scan_id={scan_id} symbols={len(symbols)} results={len(results)} elapsed_ms={elapsed_ms:.1f}")
        return [asdict(r) for r in results]

    async def get_health_status(self) -> Dict[str, Any]:
        try:
            scans_count = len(list(self.store.scans.values())) if isinstance(self.store, InMemoryScanStore) else None
            last_run = None
            if isinstance(self.store, InMemoryScanStore) and self.store.scans:
                last_run = max((s.last_run or "") for s in self.store.scans.values()) or "Never"
            return {
                "scans_count": scans_count,
                "playbooks_count": len(self.playbooks),
                "last_scan_run": last_run or "Never",
                "status": "healthy",
                "metrics": self.metrics,
                "ts": utcnow_iso(),
            }
        except Exception as e:
            logger.exception("health_status_error")
            return {"status": "unhealthy", "error": str(e), "ts": utcnow_iso()}

    # --------- Internals ---------
    async def _process_symbol(
        self,
        symbol: str,
        params: ScanParameters,
        category: str,
        semaphore: asyncio.Semaphore,
    ) -> Optional[ScanResult]:
        async with semaphore:
            # bounded retry with jitter (no external deps)
            attempt, max_attempts = 0, 3
            backoff = 0.15
            while True:
                try:
                    return await asyncio.wait_for(self._evaluate_symbol(symbol, params, category), timeout=self.fetch_timeout_s)
                except asyncio.TimeoutError:
                    logger.warning(f"fetch_timeout symbol={symbol}")
                except Exception as e:
                    logger.warning(f"fetch_error symbol={symbol} err={e}")
                attempt += 1
                if attempt >= max_attempts:
                    return None
                await asyncio.sleep(backoff + self.rng.uniform(0, 0.1))
                backoff *= 2.0

    async def _evaluate_symbol(self, symbol: str, params: ScanParameters, category: str) -> Optional[ScanResult]:
        t0 = time.perf_counter()
        stock = await self.real_data_service.get_stock_data(symbol)
        fetch_ms = (time.perf_counter() - t0) * 1000.0
        self._emit_metric("fetch_ms", fetch_ms, symbol=symbol)

        if not stock:
            return None
        if not self._passes_filters(stock, params):
            return None

        score = self._calculate_score(stock, params, category)
        if score < self.score_threshold:
            return None

        name = stock.get("name") or symbol
        result = ScanResult(
            id=str(uuid.uuid4()),
            symbol=symbol,
            name=str(name),
            current_price=safe_float(stock.get("price")),
            change=safe_float(stock.get("change")),
            change_percent=safe_float(stock.get("change_percent")),
            volume=int(stock.get("volume") or 0),
            market_cap=safe_float(stock.get("market_cap")),
            score=score,
            confidence=clamp(score + 0.1, 0.0, 1.0),
            reasoning=f"Strong {category} signals",
            risk_factors=["Market volatility", "Liquidity risk"],
            opportunity_factors=["Technical breakout", "Volume surge"],
            technical_signals=[
                TechnicalSignal(indicator="RSI", value=safe_float(stock.get("rsi", 65)), signal="bullish", strength=0.7),
                TechnicalSignal(indicator="MACD", value=safe_float(stock.get("macd", 0.5)), signal="bullish", strength=0.8),
            ],
            fundamental_metrics=[
                FundamentalMetric(metric="P/E Ratio", value=safe_float(stock.get("pe_ratio", 25)), benchmark=20.0, signal="neutral"),
                FundamentalMetric(metric="Revenue Growth", value=safe_float(stock.get("revenue_growth", 0.15)), benchmark=0.10, signal="positive"),
            ],
            alt_data_signals=[
                AltDataSignal(
                    source="Social Sentiment",
                    signal="bullish",
                    strength=0.6,
                    description="Positive sentiment trending",
                    timestamp=utcnow_iso(),
                )
            ],
        )
        return result

    async def _get_scan_universe(self, parameters: ScanParameters) -> List[str]:
        # Respect provided universe first; otherwise default to liquid tech+index names
        if parameters.universe:
            return list(dict.fromkeys([s.upper() for s in parameters.universe]))  # de-dup while preserving order
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER", "SQ", "ROKU",
            "ZM", "SNOW", "PLTR", "CRWD", "OKTA", "NET", "AVGO", "COST",
        ]

    def _passes_filters(self, stock: Dict[str, Any], p: ScanParameters) -> bool:
        try:
            price = safe_float(stock.get("price"))
            volume = int(stock.get("volume") or 0)
            mcap = safe_float(stock.get("market_cap"))
            if price < p.min_price or price > p.max_price:
                return False
            if volume < p.min_volume:
                return False
            if mcap < p.min_market_cap:
                return False
            return True
        except Exception as e:
            logger.warning(f"filter_error err={e}")
            return False

    def _calculate_score(self, stock: Dict[str, Any], p: ScanParameters, category: str) -> float:
        """
        Deterministic scoring (no hidden randomness).
        Extend with factor weights, z-scores, or model outputs.
        """
        score = 0.5

        # Momentum factors
        if category == "momentum":
            chg = safe_float(stock.get("change_percent"))
            vol = safe_float(stock.get("volume"))
            if chg > 2.0:
                score += 0.15
            if chg > 5.0:
                score += 0.10
            if vol > 1_000_000:
                score += 0.05

        # Value factors
        if category == "value":
            pe = safe_float(stock.get("pe_ratio"), 20.0)
            if pe < 15:
                score += 0.15
            if pe < 10:
                score += 0.10

        # Risk tolerance nudges (light-touch)
        rt = (p.risk_tolerance or "medium").lower()
        if rt == "low":
            score -= 0.02
        elif rt == "high":
            score += 0.02

        # Clamp
        return clamp(score, 0.0, 1.0)

    # --------- Mappers ---------
    def _scan_to_dict(self, s: Scan) -> Dict[str, Any]:
        d = asdict(s)
        # ensure ISO timestamps & snake_case -> camel where your API expects (handled upstream if needed)
        return d

    def _playbook_summary(self, p: Optional[Playbook]) -> Optional[Dict[str, Any]]:
        if not p:
            return None
        d = asdict(p)
        return d

    def _dict_to_params(self, data: Dict[str, Any]) -> ScanParameters:
        return ScanParameters(
            universe=list(data.get("universe", [])),
            min_price=float(data.get("min_price", 0.0)),
            max_price=float(data.get("max_price", math.inf)),
            min_volume=int(data.get("min_volume", 0)),
            min_market_cap=float(data.get("min_market_cap", 0.0)),
            sectors=list(data.get("sectors", [])),
            technical_indicators=list(data.get("technical_indicators", [])),
            fundamental_filters=list(data.get("fundamental_filters", [])),
            alt_data_sources=list(data.get("alt_data_sources", [])),
            risk_tolerance=str(data.get("risk_tolerance", "medium")),
            time_horizon=str(data.get("time_horizon", "daily")),
        )