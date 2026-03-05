"""
trade_debrief_service.py
========================
Analyses a user's real and paper trade history to surface behavioural patterns.

This is the analytics engine behind the AI Trade Debrief feature.  It sits on
top of existing models (BrokerOrder, UserFill, SignalPerformance, PaperTradingTrade)
and produces a structured TradeDebriefReport that the LLM formatter can narrate.

Key outputs
-----------
- Realised P&L via FIFO buy/sell matching on BrokerOrder fills
- Hold-time analysis: winners vs losers (early-exit / overstaying bias)
- Win rate sliced by sector, mode, and signal side
- Early-exit score: how often the user exits before the signal's first target
- Pattern flags: early_exit_bias, late_exit_bias, momentum_spike_buying,
                 sector_concentration_risk
- Counterfactual P&L: "if you had held to target, extra profit would be $X"

Usage
-----
    from .trade_debrief_service import TradeDebriefService
    service = TradeDebriefService()
    report  = service.build_report(user, lookback_days=90)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SectorStats:
    sector: str
    trades: int
    wins: int
    losses: int
    total_pnl: float
    win_rate: float          # 0–1


@dataclass
class HoldTimeStats:
    avg_winner_hold_hours: float
    avg_loser_hold_hours: float
    early_exit_rate: float   # fraction of winners closed before target_1
    overstay_rate: float     # fraction of losers held past time_stop


@dataclass
class PatternFlag:
    code: str                # e.g. "EARLY_EXIT_BIAS"
    severity: str            # "high" | "medium" | "low"
    description: str         # plain English
    impact_dollars: float    # estimated dollar impact (positive = lost opportunity)


@dataclass
class TradeDebriefReport:
    """
    Full structured output of TradeDebriefService.build_report().
    The LLM formatter converts this to a narrative paragraph.
    """
    # ---- meta ----
    user_id: int
    lookback_days: int
    generated_at: str        # ISO-8601

    # ---- summary ----
    total_trades: int
    total_realised_pnl: float
    total_pnl_percent: float  # relative to cost basis
    win_rate: float           # 0–1
    avg_win_dollars: float
    avg_loss_dollars: float
    profit_factor: float      # abs(total_wins) / abs(total_losses)
    largest_win: float
    largest_loss: float

    # ---- hold-time ----
    hold_time: Optional[HoldTimeStats]

    # ---- sector breakdown ----
    sector_stats: List[SectorStats]
    best_sector: Optional[str]    # highest win_rate with ≥3 trades
    worst_sector: Optional[str]   # lowest win_rate with ≥3 trades

    # ---- counterfactual ----
    # If the user had held winners to target_1, extra P&L
    counterfactual_extra_pnl: float

    # ---- pattern flags ----
    pattern_flags: List[PatternFlag]

    # ---- data provenance ----
    broker_trades_count: int     # from BrokerOrder FILL pairs
    paper_trades_count: int      # from PaperTradingTrade
    signal_linked_count: int     # trades matched back to DayTradingSignal / SwingTradingSignal
    data_source: str             # "broker" | "paper" | "mixed" | "none"
    has_enough_data: bool        # False if total_trades < MIN_TRADES_FOR_PATTERNS


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_TRADES_FOR_PATTERNS = 5     # need at least this many to surface patterns
MIN_TRADES_FOR_SECTOR   = 3     # need this many per sector for sector stats


# ---------------------------------------------------------------------------
# FIFO buy/sell matcher
# ---------------------------------------------------------------------------

def _match_broker_fills_fifo(
    orders: List[Any],
) -> List[Dict[str, Any]]:
    """
    Match BUY and SELL BrokerOrder records for the same symbol using FIFO.

    Parameters
    ----------
    orders : list of BrokerOrder
        All FILLED orders for one user, sorted ascending by filled_at / created_at.

    Returns
    -------
    list of dicts with keys:
        symbol, buy_price, sell_price, shares, pnl, pnl_pct,
        entry_time, exit_time, hold_hours, sector
    """
    # Build per-symbol queues of open long lots: {symbol: [(price, shares, time)]}
    open_lots: Dict[str, List[Tuple[Decimal, int, datetime]]] = defaultdict(list)
    matched: List[Dict[str, Any]] = []

    for order in orders:
        if not order.filled_avg_price or not order.filled_qty:
            continue

        symbol   = order.symbol
        price    = Decimal(str(order.filled_avg_price))
        qty      = int(order.filled_qty)
        ts       = order.filled_at or order.created_at
        sector   = _get_sector(symbol)

        if order.side == "BUY":
            open_lots[symbol].append((price, qty, ts))

        elif order.side == "SELL" and open_lots[symbol]:
            shares_to_close = qty
            while shares_to_close > 0 and open_lots[symbol]:
                buy_price, lot_qty, buy_ts = open_lots[symbol][0]

                closed = min(lot_qty, shares_to_close)
                pnl    = float((price - buy_price) * closed)
                cost   = float(buy_price * closed)
                hold_h = (ts - buy_ts).total_seconds() / 3600 if ts and buy_ts else 0.0

                matched.append({
                    "symbol":      symbol,
                    "buy_price":   float(buy_price),
                    "sell_price":  float(price),
                    "shares":      closed,
                    "pnl":         pnl,
                    "pnl_pct":     pnl / cost if cost else 0.0,
                    "entry_time":  buy_ts,
                    "exit_time":   ts,
                    "hold_hours":  hold_h,
                    "sector":      sector,
                })

                if lot_qty <= shares_to_close:
                    open_lots[symbol].pop(0)
                    shares_to_close -= lot_qty
                else:
                    open_lots[symbol][0] = (buy_price, lot_qty - shares_to_close, buy_ts)
                    shares_to_close = 0

    return matched


# ---------------------------------------------------------------------------
# Sector lookup
# ---------------------------------------------------------------------------

# Static sector map for common tickers. Falls back to "Unknown".
_SECTOR_MAP: Dict[str, str] = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "GOOG": "Technology",  "META": "Technology",  "NVDA": "Technology",
    "AMD":  "Technology",  "INTC": "Technology",  "CRM":  "Technology",
    "ORCL": "Technology",  "ADBE": "Technology",  "SNOW": "Technology",
    "AMZN": "Consumer Discretionary", "TSLA": "Consumer Discretionary",
    "HD":   "Consumer Discretionary", "NKE": "Consumer Discretionary",
    "MCD":  "Consumer Discretionary", "SBUX": "Consumer Discretionary",
    "JPM":  "Financials", "BAC": "Financials", "GS": "Financials",
    "MS":   "Financials", "V": "Financials", "MA": "Financials",
    "BRK.B": "Financials",
    "JNJ":  "Healthcare", "UNH": "Healthcare", "PFE": "Healthcare",
    "ABBV": "Healthcare", "MRK": "Healthcare",  "LLY": "Healthcare",
    "XOM":  "Energy", "CVX": "Energy", "COP": "Energy",
    "SPY":  "ETF", "QQQ": "ETF", "IWM": "ETF", "DIA": "ETF",
}


def _get_sector(symbol: str) -> str:
    return _SECTOR_MAP.get(symbol.upper(), "Unknown")


# ---------------------------------------------------------------------------
# Paper trade adapter
# ---------------------------------------------------------------------------

def _paper_trades_to_matched(paper_trades: List[Any]) -> List[Dict[str, Any]]:
    """Convert PaperTradingTrade records to the same dict shape as FIFO output."""
    result = []
    for t in paper_trades:
        if t.side != "SELL":
            continue
        symbol = t.stock.symbol if hasattr(t.stock, "symbol") else str(t.stock)
        entry  = getattr(t, "buy_order", None)
        entry_price = float(entry.filled_price) if entry and entry.filled_price else float(t.price)
        sell_price  = float(t.price)
        shares      = int(t.quantity)
        pnl         = float(t.realized_pnl)
        cost        = entry_price * shares
        hold_h      = 0.0
        if entry and getattr(entry, "filled_at", None) and getattr(t, "created_at", None):
            hold_h = (t.created_at - entry.filled_at).total_seconds() / 3600

        result.append({
            "symbol":     symbol,
            "buy_price":  entry_price,
            "sell_price": sell_price,
            "shares":     shares,
            "pnl":        pnl,
            "pnl_pct":    pnl / cost if cost else 0.0,
            "entry_time": getattr(entry, "filled_at", None),
            "exit_time":  getattr(t, "created_at", None),
            "hold_hours": hold_h,
            "sector":     _get_sector(symbol),
        })
    return result


# ---------------------------------------------------------------------------
# Pattern detection helpers
# ---------------------------------------------------------------------------

def _detect_hold_time(trades: List[Dict]) -> HoldTimeStats:
    winners = [t for t in trades if t["pnl"] > 0]
    losers  = [t for t in trades if t["pnl"] < 0]

    avg_win_h  = sum(t["hold_hours"] for t in winners) / len(winners) if winners else 0.0
    avg_loss_h = sum(t["hold_hours"] for t in losers)  / len(losers)  if losers  else 0.0

    # Early-exit + overstay rates require signal linkage — set to 0 if unavailable
    return HoldTimeStats(
        avg_winner_hold_hours=round(avg_win_h, 1),
        avg_loser_hold_hours=round(avg_loss_h, 1),
        early_exit_rate=0.0,   # enriched later if signal data available
        overstay_rate=0.0,
    )


def _detect_sector_stats(trades: List[Dict]) -> List[SectorStats]:
    by_sector: Dict[str, List[Dict]] = defaultdict(list)
    for t in trades:
        by_sector[t["sector"]].append(t)

    stats = []
    for sector, ts in by_sector.items():
        wins   = [t for t in ts if t["pnl"] > 0]
        losses = [t for t in ts if t["pnl"] < 0]
        stats.append(SectorStats(
            sector=sector,
            trades=len(ts),
            wins=len(wins),
            losses=len(losses),
            total_pnl=round(sum(t["pnl"] for t in ts), 2),
            win_rate=len(wins) / len(ts),
        ))

    return sorted(stats, key=lambda s: s.trades, reverse=True)


def _build_pattern_flags(
    trades: List[Dict],
    hold_time: HoldTimeStats,
    sector_stats: List[SectorStats],
    signal_linked: List[Dict],
) -> Tuple[List[PatternFlag], float]:
    """
    Returns (list_of_flags, counterfactual_extra_pnl).
    """
    flags: List[PatternFlag] = []
    counterfactual = 0.0

    if len(trades) < MIN_TRADES_FOR_PATTERNS:
        return flags, counterfactual

    winners = [t for t in trades if t["pnl"] > 0]
    losers  = [t for t in trades if t["pnl"] < 0]

    # --- Early-exit bias ---
    # Winners held notably shorter than losers → cutting profits early
    if winners and losers:
        if hold_time.avg_winner_hold_hours < hold_time.avg_loser_hold_hours * 0.7:
            avg_missed = sum(t["pnl"] for t in winners) * 0.30  # rough: 30% more if held longer
            flags.append(PatternFlag(
                code="EARLY_EXIT_BIAS",
                severity="high" if avg_missed > 500 else "medium",
                description=(
                    f"You tend to close winners after "
                    f"{hold_time.avg_winner_hold_hours:.0f}h but hold losers for "
                    f"{hold_time.avg_loser_hold_hours:.0f}h. "
                    "Cutting profits too early is a common behavioural bias."
                ),
                impact_dollars=round(avg_missed, 0),
            ))
            counterfactual += avg_missed

    # --- Signal-target early exit (requires signal linkage) ---
    if signal_linked:
        early_exits = [
            t for t in signal_linked
            if t.get("exited_before_target") and t["pnl"] > 0
        ]
        if len(early_exits) >= 2:
            missed = sum(
                t.get("target_1_price", t["sell_price"]) * t["shares"]
                - t["sell_price"] * t["shares"]
                for t in early_exits
            )
            flags.append(PatternFlag(
                code="TARGET_EXIT_MISS",
                severity="medium",
                description=(
                    f"In {len(early_exits)} of your winning trades you exited before "
                    "the signal's first price target. Estimated missed upside: "
                    f"${missed:,.0f}."
                ),
                impact_dollars=round(missed, 0),
            ))
            counterfactual += missed

    # --- Sector concentration risk ---
    large_sectors = [
        s for s in sector_stats
        if s.trades >= MIN_TRADES_FOR_SECTOR and s.trades / len(trades) > 0.50
    ]
    if large_sectors:
        s = large_sectors[0]
        flags.append(PatternFlag(
            code="SECTOR_CONCENTRATION",
            severity="medium",
            description=(
                f"Over {s.trades / len(trades):.0%} of your trades are in "
                f"{s.sector} stocks. Concentrated exposure increases volatility."
            ),
            impact_dollars=0.0,
        ))

    # --- Momentum spike buying ---
    # Detect if winning signals were entered after large momentum features
    if signal_linked:
        spike_entries = [
            t for t in signal_linked
            if t.get("entry_momentum_15m", 0) > 0.03   # >3% momentum in 15m
        ]
        if len(spike_entries) >= 3:
            spike_losses = [t for t in spike_entries if t["pnl"] < 0]
            if len(spike_losses) / len(spike_entries) > 0.55:
                flags.append(PatternFlag(
                    code="MOMENTUM_SPIKE_BUYING",
                    severity="high",
                    description=(
                        "You frequently enter trades after a large short-term "
                        "momentum spike (>3% in 15 minutes). These trades lose "
                        f"{len(spike_losses)/len(spike_entries):.0%} of the time — "
                        "chasing breakouts tends to result in buying at local tops."
                    ),
                    impact_dollars=round(abs(sum(t["pnl"] for t in spike_losses)), 0),
                ))

    # --- Late-exit / overstaying losers ---
    if losers:
        # Find losers held >2× longer than winners on average
        long_losers = [
            t for t in losers
            if t["hold_hours"] > hold_time.avg_winner_hold_hours * 2
        ]
        if len(long_losers) >= 2:
            flags.append(PatternFlag(
                code="LATE_EXIT_LOSERS",
                severity="medium",
                description=(
                    f"{len(long_losers)} of your losing trades were held for "
                    f"more than 2× your average winner hold time. "
                    "Letting losers run while cutting winners is the classic "
                    "disposition effect."
                ),
                impact_dollars=round(abs(sum(t["pnl"] for t in long_losers)) * 0.20, 0),
            ))

    return flags, round(counterfactual, 2)


def _enrich_with_signal_data(
    trades: List[Dict],
    user,
    cutoff: datetime,
) -> List[Dict]:
    """
    Attempt to match each trade dict back to a DayTradingSignal or SwingTradingSignal
    and annotate it with signal features (entry_momentum_15m, target_1_price, etc.).
    Falls back gracefully if signal models are not available.
    """
    try:
        from .signal_performance_models import DayTradingSignal, SwingTradingSignal
    except ImportError:
        return trades

    # Build symbol → signals lookup for the lookback window
    day_signals: Dict[str, List[Any]] = defaultdict(list)
    swing_signals: Dict[str, List[Any]] = defaultdict(list)

    try:
        for sig in DayTradingSignal.objects.filter(generated_at__gte=cutoff):
            day_signals[sig.symbol].append(sig)
        for sig in SwingTradingSignal.objects.filter(generated_at__gte=cutoff):
            swing_signals[sig.symbol].append(sig)
    except Exception as exc:
        logger.debug("Could not query signals for debrief enrichment: %s", exc)
        return trades

    enriched = []
    for t in trades:
        symbol = t["symbol"]
        entry_time = t.get("entry_time")
        matched_sig = None

        # Try to find a signal close in time to entry (within ±4 hours)
        for sig in day_signals.get(symbol, []) + swing_signals.get(symbol, []):
            sig_ts = sig.generated_at
            if entry_time and abs((sig_ts - entry_time).total_seconds()) < 4 * 3600:
                matched_sig = sig
                break

        if matched_sig:
            features       = matched_sig.features or {}
            target_prices  = matched_sig.target_prices or []
            target_1       = float(target_prices[0]) if target_prices else None

            t = {
                **t,
                "entry_momentum_15m":   float(features.get("momentum15m", 0)),
                "entry_rvol":           float(features.get("rvol10m", 1)),
                "target_1_price":       target_1,
                "signal_stop":          float(matched_sig.stop_price) if matched_sig.stop_price else None,
                "exited_before_target": (
                    target_1 is not None
                    and t["sell_price"] < target_1
                    and t["pnl"] > 0
                ),
            }
        enriched.append(t)

    return enriched


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

class TradeDebriefService:
    """
    Builds a TradeDebriefReport for a user from their real and paper trade history.

    Data sources (in priority order):
    1. BrokerOrder FILL records (real money, Alpaca) — FIFO P&L matched
    2. PaperTradingTrade records (simulated)
    3. UserFill + SignalPerformance (signal-linked enrichment)
    """

    def build_report(
        self,
        user,
        lookback_days: int = 90,
    ) -> TradeDebriefReport:
        """
        Build and return a TradeDebriefReport.

        Parameters
        ----------
        user : Django User
        lookback_days : int
            How many calendar days to look back (default 90).
        """
        cutoff = timezone.now() - timedelta(days=lookback_days)
        broker_trades: List[Dict] = []
        paper_trades:  List[Dict] = []

        # --- 1. Real broker trades ---
        broker_count = 0
        try:
            from .broker_models import BrokerAccount, BrokerOrder
            broker_account = BrokerAccount.objects.get(user=user)
            raw_orders = list(
                BrokerOrder.objects
                .filter(
                    broker_account=broker_account,
                    status="FILLED",
                    created_at__gte=cutoff,
                )
                .order_by("filled_at", "created_at")
            )
            broker_trades = _match_broker_fills_fifo(raw_orders)
            broker_count  = len(broker_trades)
            logger.debug("Debrief: %d broker filled trades for user %s", broker_count, user.id)
        except Exception as exc:
            logger.debug("Debrief: could not load broker trades — %s", exc)

        # --- 2. Paper trades ---
        paper_count = 0
        try:
            from .paper_trading_models import PaperTradingTrade, PaperTradingAccount
            paper_account = PaperTradingAccount.objects.get(user=user)
            raw_paper = list(
                PaperTradingTrade.objects
                .filter(account=paper_account, created_at__gte=cutoff)
                .select_related("stock", "buy_order")
                .order_by("created_at")
            )
            paper_trades = _paper_trades_to_matched(raw_paper)
            paper_count  = len(paper_trades)
            logger.debug("Debrief: %d paper trades for user %s", paper_count, user.id)
        except Exception as exc:
            logger.debug("Debrief: could not load paper trades — %s", exc)

        # Merge; prefer broker if both present
        all_trades = broker_trades + paper_trades

        # Data source label
        if broker_count > 0 and paper_count > 0:
            data_source = "mixed"
        elif broker_count > 0:
            data_source = "broker"
        elif paper_count > 0:
            data_source = "paper"
        else:
            data_source = "none"

        # --- 3. Signal enrichment (best-effort) ---
        signal_linked_count = 0
        if all_trades:
            enriched = _enrich_with_signal_data(all_trades, user, cutoff)
            signal_linked_count = sum(1 for t in enriched if "entry_momentum_15m" in t)
            all_trades = enriched

        # --- 4. Compute summary stats ---
        total_trades = len(all_trades)
        has_enough   = total_trades >= MIN_TRADES_FOR_PATTERNS

        wins   = [t for t in all_trades if t["pnl"] > 0]
        losses = [t for t in all_trades if t["pnl"] < 0]

        total_pnl     = sum(t["pnl"] for t in all_trades)
        total_cost    = sum(t["buy_price"] * t["shares"] for t in all_trades)
        total_pnl_pct = total_pnl / total_cost if total_cost else 0.0

        win_rate      = len(wins) / total_trades if total_trades else 0.0
        avg_win       = sum(t["pnl"] for t in wins)   / len(wins)   if wins   else 0.0
        avg_loss      = sum(t["pnl"] for t in losses) / len(losses) if losses else 0.0
        largest_win   = max((t["pnl"] for t in wins),   default=0.0)
        largest_loss  = min((t["pnl"] for t in losses), default=0.0)

        total_wins_abs   = sum(t["pnl"] for t in wins)
        total_losses_abs = abs(sum(t["pnl"] for t in losses))
        profit_factor = total_wins_abs / total_losses_abs if total_losses_abs else 0.0

        # --- 5. Behavioural analytics ---
        hold_time    = _detect_hold_time(all_trades) if has_enough else None
        sector_stats = _detect_sector_stats(all_trades)

        # Best / worst sector (≥ MIN_TRADES_FOR_SECTOR)
        qualified_sectors = [s for s in sector_stats if s.trades >= MIN_TRADES_FOR_SECTOR]
        best_sector  = max(qualified_sectors, key=lambda s: s.win_rate).sector if qualified_sectors else None
        worst_sector = min(qualified_sectors, key=lambda s: s.win_rate).sector if qualified_sectors else None

        signal_linked_trades = [t for t in all_trades if "entry_momentum_15m" in t]
        pattern_flags, counterfactual = _build_pattern_flags(
            all_trades, hold_time or HoldTimeStats(0, 0, 0, 0),
            sector_stats, signal_linked_trades,
        )

        return TradeDebriefReport(
            user_id=user.id,
            lookback_days=lookback_days,
            generated_at=timezone.now().isoformat(),

            total_trades=total_trades,
            total_realised_pnl=round(total_pnl, 2),
            total_pnl_percent=round(total_pnl_pct * 100, 2),
            win_rate=round(win_rate, 4),
            avg_win_dollars=round(avg_win, 2),
            avg_loss_dollars=round(avg_loss, 2),
            profit_factor=round(profit_factor, 3),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),

            hold_time=hold_time,

            sector_stats=sector_stats,
            best_sector=best_sector,
            worst_sector=worst_sector,

            counterfactual_extra_pnl=counterfactual,

            pattern_flags=pattern_flags,

            broker_trades_count=broker_count,
            paper_trades_count=paper_count,
            signal_linked_count=signal_linked_count,
            data_source=data_source,
            has_enough_data=has_enough,
        )
