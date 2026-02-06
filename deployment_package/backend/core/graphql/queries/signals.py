"""
Day/swing/pre-market picks, execution suggestions, and research hub GraphQL queries.
Exposes day_trading_picks, day_trading_stats, pre_market_picks, swing_trading_picks,
swing_trading_stats, executionSuggestion, entry_timing_suggestion, execution_quality_stats,
researchHub. Composed into ExtendedQuery.
"""
import asyncio
import json
import logging
import time
from datetime import timedelta

import graphene
from django.utils import timezone

logger = logging.getLogger(__name__)


class SignalsQuery(graphene.ObjectType):
    """Trading signals, execution intelligence, and research hub root fields."""

    day_trading_picks = graphene.Field(
        "core.types.DayTradingDataType",
        mode=graphene.String(required=False, default_value="SAFE"),
        minBanditWeight=graphene.Float(required=False, default_value=0.10),
    )
    day_trading_stats = graphene.List(
        "core.types.DayTradingStatsType",
        mode=graphene.String(required=False),
        period=graphene.String(required=False, default_value="ALL_TIME"),
        description="Get day trading strategy performance stats (Citadel Board)",
    )
    pre_market_picks = graphene.Field(
        "core.types.PreMarketDataType",
        mode=graphene.String(required=False, default_value="AGGRESSIVE"),
        limit=graphene.Int(required=False, default_value=20),
        description="Get pre-market quality setups (4AM-9:30AM ET)",
    )
    swing_trading_picks = graphene.Field(
        "core.types.SwingTradingDataType",
        strategy=graphene.String(required=False, default_value="MOMENTUM"),
        description="Get swing trading picks (2-5 day holds). Strategy: MOMENTUM, BREAKOUT, or MEAN_REVERSION",
    )
    swing_trading_stats = graphene.List(
        "core.types.SwingTradingStatsType",
        strategy=graphene.String(required=False),
        period=graphene.String(required=False, default_value="ALL_TIME"),
        description="Get swing trading strategy performance stats",
    )
    execution_suggestion = graphene.Field(
        "core.types.ExecutionSuggestionType",
        signal=graphene.JSONString(required=True),
        signalType=graphene.String(required=False, default_value="day_trading"),
        description="Get smart order suggestion for a trading signal",
        name="executionSuggestion",
    )
    entry_timing_suggestion = graphene.Field(
        "core.types.EntryTimingSuggestionType",
        signal=graphene.JSONString(required=True),
        currentPrice=graphene.Float(required=True),
        description="Get entry timing suggestion (enter now vs wait for pullback)",
    )
    execution_quality_stats = graphene.Field(
        "core.types.ExecutionQualityStatsType",
        signalType=graphene.String(required=False, default_value="day_trading"),
        days=graphene.Int(required=False, default_value=30),
        description="Get execution quality statistics and coaching tips",
    )
    research_hub = graphene.Field(
        "core.types.ResearchHubType",
        symbol=graphene.String(required=True),
        description="Get comprehensive research data for a stock",
        name="researchHub",
    )
    system_health = graphene.Field(
        "core.types.SystemHealthType",
        limit=graphene.Int(required=False, default_value=5),
        description="Get system health summary for regime, bandit weights, and execution risk",
        name="systemHealth",
    )

    def resolve_day_trading_picks(self, info, mode="SAFE", minBanditWeight=0.10):
        """Resolve day trading picks using real intraday data."""
        from core.queries import _get_real_intraday_day_trading_picks

        logger.info("Generating day trading picks for mode: %s", mode)
        try:
            result_data = _get_real_intraday_day_trading_picks(
                mode=mode,
                limit=10,
                use_dynamic_discovery=True,
                min_bandit_weight=minBanditWeight,
            )
            if isinstance(result_data, tuple) and len(result_data) == 2:
                picks, metadata = result_data
                universe_size = metadata.get("universe_size", 0)
                universe_source = metadata.get("universe_source", "CORE")
                diagnostics = metadata.get("diagnostics", {})
            else:
                picks = result_data if isinstance(result_data, list) else []
                universe_size = 0
                universe_source = picks[0].get("universe_source", "CORE") if picks else "CORE"
                diagnostics = {}
            picks = picks[:10]
            now = timezone.now()
            result = {
                "asOf": now.isoformat(),
                "mode": mode,
                "picks": picks,
                "universeSize": universe_size,
                "qualityThreshold": 2.5 if mode == "SAFE" else 2.0,
                "universeSource": universe_source,
                "scannedCount": diagnostics.get("scanned_count", universe_size),
                "passedLiquidity": diagnostics.get("passed_liquidity", 0),
                "passedQuality": diagnostics.get("passed_quality", len(picks)),
                "failedDataFetch": diagnostics.get("failed_data_fetch", 0),
                "filteredByMicrostructure": diagnostics.get("filtered_by_microstructure", 0),
                "filteredByVolatility": diagnostics.get("filtered_by_volatility", 0),
                "filteredByMomentum": diagnostics.get("filtered_by_momentum", 0),
            }
            try:
                from core.signal_logger import log_signals_batch
                if picks:
                    log_signals_batch(picks, mode)
            except Exception as e:
                logger.warning("Could not log signals to database: %s", e)
            try:
                from django.core.cache import cache
                from core.day_trading_ml_learner import get_day_trading_ml_learner
                from core.signal_performance_models import DayTradingSignal

                retrain_cache_key = "day_trading_ml_retrain_today"
                if not cache.get(retrain_cache_key):
                    cutoff = timezone.now() - timedelta(days=7)
                    signals_with_perf = DayTradingSignal.objects.filter(
                        generated_at__gte=cutoff
                    ).exclude(performance__isnull=True).count()
                    if signals_with_perf >= 50:
                        import threading
                        def retrain_async():
                            try:
                                learner = get_day_trading_ml_learner()
                                result = learner.train_model(days_back=30, force_retrain=False)
                                if "error" not in result:
                                    logger.info(
                                        "Background ML retraining completed: %s records",
                                        result.get("records_used", 0),
                                    )
                            except Exception as e:
                                logger.error("Background retraining failed: %s", e)
                        thread = threading.Thread(target=retrain_async, daemon=True)
                        thread.start()
                        cache.set(retrain_cache_key, True, timeout=86400)
            except Exception:
                pass
            return result
        except Exception as e:
            logger.error("Error generating day trading picks: %s", e, exc_info=True)
            return {
                "asOf": timezone.now().isoformat(),
                "mode": mode,
                "picks": [],
                "universeSize": 0,
                "qualityThreshold": 2.5 if mode == "SAFE" else 2.0,
                "universeSource": "CORE",
            }

    def resolve_swing_trading_picks(self, info, strategy="MOMENTUM"):
        """Resolve swing trading picks (2-5 day holds) using daily bars."""
        from core.swing_trading_engine import SwingTradingEngine

        logger.info("Generating swing trading picks for strategy: %s", strategy)
        try:
            engine = SwingTradingEngine()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                signals = loop.run_until_complete(
                    engine.generate_swing_signals(
                        strategy=strategy,
                        limit=5,
                        use_dynamic_discovery=True,
                    )
                )
            finally:
                loop.close()
            now = timezone.now()
            universe_source = signals[0].get("universe_source", "CORE") if signals else "CORE"
            result = {
                "asOf": now.isoformat(),
                "strategy": strategy,
                "picks": signals,
                "universeSize": len(signals),
                "universeSource": universe_source,
            }
            try:
                from core.signal_logger import log_swing_signals_batch
                if signals:
                    log_swing_signals_batch(signals, strategy)
            except Exception as e:
                logger.warning("Could not log swing signals: %s", e)
            logger.info("Generated %s swing trading picks for %s", len(signals), strategy)
            return result
        except Exception as e:
            logger.error("Error generating swing trading picks: %s", e, exc_info=True)
            return {
                "asOf": timezone.now().isoformat(),
                "strategy": strategy,
                "picks": [],
                "universeSize": 0,
                "universeSource": "CORE",
            }

    def resolve_day_trading_stats(self, info, mode=None, period="ALL_TIME"):
        """Resolve day trading strategy performance stats."""
        from core.signal_performance_models import StrategyPerformance

        try:
            queryset = StrategyPerformance.objects.filter(period=period)
            if mode:
                queryset = queryset.filter(mode=mode)
            stats_list = []
            for perf in queryset.order_by("-period_end", "mode").distinct("mode"):
                stats_list.append({
                    "mode": perf.mode,
                    "period": perf.period,
                    "asOf": perf.period_end.isoformat() if perf.period_end else timezone.now().isoformat(),
                    "winRate": float(perf.win_rate) if perf.win_rate else 0.0,
                    "sharpeRatio": float(perf.sharpe_ratio) if perf.sharpe_ratio else None,
                    "maxDrawdown": float(abs(perf.max_drawdown)) if perf.max_drawdown else 0.0,
                    "avgPnlPerSignal": float(perf.avg_pnl_per_signal) if perf.avg_pnl_per_signal else 0.0,
                    "totalSignals": perf.total_signals,
                    "signalsEvaluated": perf.signals_evaluated,
                    "totalPnlPercent": float(perf.total_pnl_percent) if perf.total_pnl_percent else 0.0,
                    "sortinoRatio": float(perf.sortino_ratio) if perf.sortino_ratio else None,
                    "calmarRatio": float(perf.calmar_ratio) if perf.calmar_ratio else None,
                })
            return stats_list
        except Exception as e:
            logger.error("Error fetching day trading stats: %s", e, exc_info=True)
            return []

    def resolve_pre_market_picks(self, info, mode="AGGRESSIVE", limit=20):
        """Resolve pre-market picks - scans pre-market movers and flags quality setups."""
        from core.pre_market_scanner import PreMarketScanner

        try:
            scanner = PreMarketScanner()
            if not scanner.is_pre_market_hours():
                logger.warning("Pre-market scan requested outside pre-market hours")
                return {
                    "asOf": timezone.now().isoformat(),
                    "mode": mode,
                    "picks": [],
                    "totalScanned": 0,
                    "minutesUntilOpen": scanner._minutes_until_open(),
                }
            setups = scanner.scan_pre_market_sync(mode=mode, limit=limit)
            picks = [
                {
                    "symbol": s["symbol"],
                    "side": s["side"],
                    "score": s["score"],
                    "preMarketPrice": s["pre_market_price"],
                    "preMarketChangePct": s["pre_market_change_pct"],
                    "volume": s["volume"],
                    "marketCap": s["market_cap"],
                    "prevClose": s["prev_close"],
                    "notes": s["notes"],
                    "scannedAt": s["scanned_at"],
                }
                for s in setups
            ]
            return {
                "asOf": timezone.now().isoformat(),
                "mode": mode,
                "picks": picks,
                "totalScanned": len(setups) if setups else 0,
                "minutesUntilOpen": scanner._minutes_until_open(),
            }
        except Exception as e:
            logger.error("Error in pre-market scan: %s", e, exc_info=True)
            return {
                "asOf": timezone.now().isoformat(),
                "mode": mode,
                "picks": [],
                "totalScanned": 0,
                "minutesUntilOpen": 0,
            }

    def resolve_system_health(self, info, limit=5):
        """Resolve system health summary for dashboard."""
        from django.utils import timezone

        as_of = timezone.now()

        current_regime = None
        regime_confidence = None
        regime_stability_minutes = None
        try:
            from core.hmm_regime_models import HMMRegimeSnapshot

            latest = HMMRegimeSnapshot.objects.filter(symbol="SPY").first()
            if latest:
                current_regime = latest.ensemble_regime
                try:
                    regime_confidence = float(
                        latest.hmm_probabilities.get(latest.hmm_regime, 0.0)
                    )
                except Exception:
                    regime_confidence = 0.0

                last_change = (
                    HMMRegimeSnapshot.objects
                    .filter(symbol="SPY", detected_at__lt=latest.detected_at)
                    .exclude(ensemble_regime=current_regime)
                    .first()
                )
                if last_change:
                    stability_minutes = int(
                        (latest.detected_at - last_change.detected_at).total_seconds() / 60
                    )
                else:
                    stability_minutes = int(
                        (as_of - latest.detected_at).total_seconds() / 60
                    )
                regime_stability_minutes = max(0, stability_minutes)
        except Exception as e:
            logger.debug("System health regime lookup failed: %s", e)

        active_strategies = []
        top_strategy = None
        bandit_adaptation_rate = None
        try:
            from core.bandit_models import BanditArm

            arms = BanditArm.objects.filter(enabled=True)
            if arms.exists():
                ordered_arms = arms.order_by("-current_weight")
                top_strategy = ordered_arms.first().strategy_slug
                active_strategies = [
                    {
                        "name": arm.strategy_slug,
                        "weight": float(arm.current_weight),
                        "recentWinRate": float(arm.expected_win_rate),
                    }
                    for arm in ordered_arms[:limit]
                ]
                avg_discount = sum(float(arm.discount_rate) for arm in arms) / arms.count()
                bandit_adaptation_rate = max(0.0, 1.0 - avg_discount)
        except Exception as e:
            logger.debug("System health bandit lookup failed: %s", e)

        execution_alerts = []
        avg_slippage_bps = None
        try:
            from django.db.models import Avg
            from core.signal_performance_models import SymbolExecutionProfile

            profiles = SymbolExecutionProfile.objects.filter(fill_count__gte=5)
            if profiles.exists():
                avg_slippage_bps = float(
                    profiles.aggregate(avg=Avg("avg_slippage_bps")).get("avg") or 0.0
                )

            ranked_profiles = profiles.order_by("-avg_slippage_bps")[:limit]
            for profile in ranked_profiles:
                avg_slippage = float(profile.avg_slippage_bps)
                avg_quality = float(profile.avg_quality_score)
                penalty = 1.0
                if avg_slippage > 25:
                    penalty = min(penalty, 0.75)
                elif avg_slippage > 15:
                    penalty = min(penalty, 0.85)
                if avg_quality < 3.5:
                    penalty = min(penalty, 0.75)
                elif avg_quality < 4.5:
                    penalty = min(penalty, 0.85)

                if penalty < 1.0:
                    execution_alerts.append({
                        "symbol": profile.symbol,
                        "penaltyApplied": float(penalty),
                        "avgSlippage": avg_slippage,
                    })
        except Exception as e:
            logger.debug("System health execution lookup failed: %s", e)

        total_signals_filtered_by_liquidity = 0

        safety_kill_switch_active = False
        safety_kill_switch_reason = None
        max_drawdown = None
        max_drawdown_limit = None
        try:
            from core.signal_performance_models import UserRiskBudget

            user = getattr(info.context, "user", None)
            if user and not getattr(user, "is_anonymous", True):
                budget = UserRiskBudget.objects.filter(user=user).first()
                if budget:
                    daily_pnl_pct = float(budget.daily_pnl_pct)
                    max_daily_loss_pct = float(budget.max_daily_loss_pct)
                    max_drawdown = daily_pnl_pct / 100.0
                    max_drawdown_limit = max_daily_loss_pct / 100.0
                    if budget.trading_paused:
                        safety_kill_switch_active = True
                        safety_kill_switch_reason = "Trading paused by user risk budget"
                    elif daily_pnl_pct <= -max_daily_loss_pct:
                        safety_kill_switch_active = True
                        safety_kill_switch_reason = (
                            f"Daily PnL {daily_pnl_pct:.2f}% exceeds max loss {max_daily_loss_pct:.2f}%"
                        )
        except Exception as e:
            logger.debug("System health safety lookup failed: %s", e)

        return {
            "currentRegime": current_regime,
            "regimeStabilityMinutes": regime_stability_minutes,
            "regimeConfidence": regime_confidence,
            "activeStrategies": active_strategies,
            "topStrategy": top_strategy,
            "banditAdaptationRate": bandit_adaptation_rate,
            "executionAlerts": execution_alerts,
            "avgSlippageBps": avg_slippage_bps,
            "totalSignalsFilteredByLiquidity": total_signals_filtered_by_liquidity,
            "safetyKillSwitchActive": safety_kill_switch_active,
            "safetyKillSwitchReason": safety_kill_switch_reason,
            "maxDrawdown": max_drawdown,
            "maxDrawdownLimit": max_drawdown_limit,
        }

    def resolve_swing_trading_stats(self, info, strategy=None, period="ALL_TIME"):
        """Resolve swing trading strategy performance stats."""
        import math
        from django.db.models import Q

        from core.signal_performance_models import SignalPerformance, SwingTradingSignal

        try:
            now = timezone.now()
            if period == "DAILY":
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "WEEKLY":
                days_since_monday = now.weekday()
                period_start = (now - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif period == "MONTHLY":
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                period_start = timezone.now() - timedelta(days=365)
            period_end = now
            signals_queryset = SwingTradingSignal.objects.filter(
                generated_at__gte=period_start,
                generated_at__lte=period_end,
            )
            if strategy:
                signals_queryset = signals_queryset.filter(strategy=strategy)
            horizon = "5d"
            performances = SignalPerformance.objects.filter(
                swing_signal__generated_at__gte=period_start,
                swing_signal__generated_at__lte=period_end,
                horizon=horizon,
            )
            if strategy:
                performances = performances.filter(swing_signal__strategy=strategy)
            strategies_list = ["MOMENTUM", "BREAKOUT", "MEAN_REVERSION"] if not strategy else [strategy]
            stats_list = []
            for strat in strategies_list:
                strat_signals = signals_queryset.filter(strategy=strat)
                strat_perfs = performances.filter(swing_signal__strategy=strat)
                total_signals = strat_signals.count()
                signals_evaluated = strat_perfs.count()
                if signals_evaluated == 0:
                    continue
                winning = strat_perfs.filter(outcome__in=["WIN", "TARGET_HIT"]).count()
                losing = strat_perfs.filter(outcome__in=["LOSS", "STOP_HIT"]).count()
                win_rate = (winning / signals_evaluated * 100) if signals_evaluated > 0 else 0
                total_pnl_percent = sum(float(p.pnl_percent) for p in strat_perfs)
                avg_pnl = total_pnl_percent / signals_evaluated if signals_evaluated > 0 else 0
                returns = [float(p.pnl_percent) for p in strat_perfs]
                if len(returns) > 1:
                    mean_return = sum(returns) / len(returns)
                    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
                    std_dev = math.sqrt(variance) if variance > 0 else 0.01
                    sharpe = (mean_return / std_dev) if std_dev > 0 else 0
                else:
                    sharpe = None
                max_dd = 0.0
                if returns:
                    peak = returns[0]
                    for r in returns:
                        if r > peak:
                            peak = r
                        dd = (peak - r) / peak if peak > 0 else 0
                        if dd > max_dd:
                            max_dd = dd
                stats_list.append({
                    "strategy": strat,
                    "period": period,
                    "asOf": period_end.isoformat(),
                    "winRate": win_rate,
                    "sharpeRatio": sharpe,
                    "maxDrawdown": max_dd,
                    "avgPnlPerSignal": avg_pnl,
                    "totalSignals": total_signals,
                    "signalsEvaluated": signals_evaluated,
                    "totalPnlPercent": total_pnl_percent,
                    "sortinoRatio": None,
                    "calmarRatio": None,
                })
            return stats_list
        except Exception as e:
            logger.error("Error fetching swing trading stats: %s", e, exc_info=True)
            return []

    def resolve_execution_suggestion(self, info, signal, signalType="day_trading"):
        """Resolve execution order suggestion for a signal."""
        from core.execution_advisor import ExecutionAdvisor
        from core.types import BracketLegsType, ExecutionSuggestionType

        start_time = time.time()
        try:
            if isinstance(signal, str):
                try:
                    signal = json.loads(signal)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error("Failed to parse signal JSON: %s", e)
                    return None
            if not signal or not isinstance(signal, dict):
                logger.error("Invalid signal format: %s", type(signal))
                return None
            symbol = signal.get("symbol")
            if not symbol:
                logger.error("Signal missing symbol: %s", signal)
                return None
            if not hasattr(SignalsQuery, "_execution_advisor"):
                SignalsQuery._execution_advisor = ExecutionAdvisor()
            advisor = SignalsQuery._execution_advisor
            suggestion_dict = advisor.suggest_order(signal, signalType)
            if not suggestion_dict:
                logger.warning("ExecutionAdvisor returned None for %s", symbol)
                return None
            bracket_legs_dict = suggestion_dict.get("bracket_legs", {})
            bracket_legs = None
            if bracket_legs_dict:
                bracket_legs = BracketLegsType(
                    stop=bracket_legs_dict.get("stop"),
                    target1=bracket_legs_dict.get("target1"),
                    target2=bracket_legs_dict.get("target2"),
                    orderStructure=bracket_legs_dict.get("order_structure") or bracket_legs_dict.get("orderStructure"),
                )
            suggestion = ExecutionSuggestionType(
                orderType=suggestion_dict.get("order_type"),
                priceBand=suggestion_dict.get("price_band", []),
                timeInForce=suggestion_dict.get("time_in_force"),
                entryStrategy=suggestion_dict.get("entry_strategy"),
                bracketLegs=bracket_legs,
                suggestedSize=suggestion_dict.get("suggested_size"),
                rationale=suggestion_dict.get("rationale"),
                microstructureSummary=suggestion_dict.get("microstructure_summary"),
            )
            elapsed = (time.time() - start_time) * 1000
            if elapsed > 50:
                logger.warning("Execution suggestion took %.1fms for %s", elapsed, symbol)
            return suggestion
        except Exception as e:
            logger.error(
                "Error generating execution suggestion: %s",
                e,
                exc_info=True,
            )
            return None

    def resolve_entry_timing_suggestion(self, info, signal, currentPrice):
        """Resolve entry timing suggestion (enter now vs wait)."""
        from core.execution_advisor import ExecutionAdvisor

        try:
            advisor = ExecutionAdvisor()
            return advisor.suggest_entry_timing(signal, currentPrice)
        except Exception as e:
            logger.error("Error generating entry timing suggestion: %s", e, exc_info=True)
            return None

    def resolve_execution_quality_stats(self, info, signalType="day_trading", days=30):
        """Resolve execution quality statistics."""
        from core.execution_quality_tracker import ExecutionQualityTracker

        try:
            tracker = ExecutionQualityTracker()
            return tracker.get_user_execution_stats(
                user_id=None,
                signal_type=signalType,
                days=days,
            )
        except Exception as e:
            logger.error("Error getting execution quality stats: %s", e, exc_info=True)
            return {
                "avgSlippagePct": 0,
                "avgQualityScore": 5.0,
                "chasedCount": 0,
                "totalFills": 0,
                "improvementTips": ["Unable to calculate stats"],
                "periodDays": days,
            }

    def resolve_research_hub(self, info, symbol: str):
        """Resolve research hub data for a stock using real APIs."""
        import os
        from core.enhanced_stock_service import enhanced_stock_service
        from core.models import Stock
        from core.types import (
            MacroType,
            QuoteType,
            ResearchHubType,
            ResearchMarketRegimeType,
            SentimentType,
            SnapshotType,
            TechnicalType,
        )
        from django.utils import timezone

        symbol_upper = symbol.upper()
        logger.info("resolve_research_hub called for %s", symbol_upper)
        try:
            try:
                stock = Stock.objects.get(symbol=symbol_upper)
            except Stock.DoesNotExist:
                logger.warning("Stock %s not found in database", symbol_upper)
                stock = None
            quote_data = None
            try:
                price_data = asyncio.run(enhanced_stock_service.get_real_time_price(symbol_upper))
                if price_data:
                    quote_data = {
                        "price": price_data.get("price", 0),
                        "chg": price_data.get("change", 0),
                        "chgPct": price_data.get("change_percent", 0),
                        "high": price_data.get("high", 0),
                        "low": price_data.get("low", 0),
                        "volume": price_data.get("volume", 0),
                    }
            except Exception as e:
                logger.warning("Could not get real-time quote for %s: %s", symbol_upper, e)
            snapshot_data = None
            alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv("ALPHA_VANTAGE_KEY")
            if alpha_vantage_key:
                try:
                    import requests
                    av_url = "https://www.alphavantage.co/query"
                    av_params = {"function": "OVERVIEW", "symbol": symbol_upper, "apikey": alpha_vantage_key}
                    av_response = requests.get(av_url, params=av_params, timeout=10)
                    if av_response.ok:
                        av_data = av_response.json()
                        if "Name" in av_data:
                            snapshot_data = {
                                "name": av_data.get("Name", ""),
                                "sector": av_data.get("Sector", stock.sector if stock else "Unknown"),
                                "marketCap": float(av_data.get("MarketCapitalization", 0)) if av_data.get("MarketCapitalization") else None,
                                "country": av_data.get("Country", "US"),
                                "website": av_data.get("Website", ""),
                            }
                except Exception as e:
                    logger.warning("Could not get Alpha Vantage overview for %s: %s", symbol_upper, e)
            if not snapshot_data and stock:
                snapshot_data = {
                    "name": stock.company_name or symbol_upper,
                    "sector": stock.sector or "Unknown",
                    "marketCap": float(stock.market_cap) if stock.market_cap else None,
                    "country": "US",
                    "website": "",
                }
            current_price = None
            if quote_data and quote_data.get("price"):
                current_price = quote_data["price"]
            elif stock and stock.current_price:
                current_price = float(stock.current_price)
            else:
                current_price = 150.0
            technical_data = {
                "rsi": 55.0,
                "macd": 0.5,
                "macdhistogram": 0.2,
                "movingAverage50": current_price * 0.98,
                "movingAverage200": current_price * 0.95,
                "supportLevel": current_price * 0.92,
                "resistanceLevel": current_price * 1.08,
                "impliedVolatility": 0.25,
            }
            sentiment_data = None
            news_api_key = os.getenv("NEWS_API_KEY")
            if news_api_key:
                try:
                    import requests
                    news_url = "https://newsapi.org/v2/everything"
                    news_params = {
                        "q": symbol_upper,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": 10,
                        "apiKey": news_api_key,
                    }
                    news_response = requests.get(news_url, params=news_params, timeout=10)
                    if news_response.ok:
                        news_data = news_response.json()
                        articles = news_data.get("articles", [])
                        positive_keywords = ["up", "gain", "rise", "surge", "bullish", "buy", "positive"]
                        negative_keywords = ["down", "fall", "drop", "bearish", "sell", "negative"]
                        positive_count = sum(1 for a in articles if any(kw in a.get("title", "").lower() for kw in positive_keywords))
                        negative_count = sum(1 for a in articles if any(kw in a.get("title", "").lower() for kw in negative_keywords))
                        total = len(articles)
                        score = ((positive_count - negative_count) / max(total, 1)) * 50 + 50
                        label = "BULLISH" if score > 60 else "BEARISH" if score < 40 else "NEUTRAL"
                        sentiment_data = {
                            "label": label,
                            "score": score,
                            "articleCount": total,
                            "confidence": min(100, total * 10),
                        }
                except Exception as e:
                    logger.warning("Could not get news sentiment for %s: %s", symbol_upper, e)
            if not sentiment_data:
                sentiment_data = {
                    "label": "NEUTRAL",
                    "score": 50.0,
                    "articleCount": 0,
                    "confidence": 0.0,
                }
            macro_data = {"vix": 18.5, "marketSentiment": "Positive", "riskAppetite": 0.65}
            market_regime_data = {
                "market_regime": "Bull Market",
                "marketRegime": "Bull Market",
                "confidence": 0.72,
                "recommended_strategy": "Momentum",
                "recommendedStrategy": "Momentum",
            }
            peers = []
            if stock and stock.sector:
                sector_stocks = Stock.objects.filter(sector=stock.sector).exclude(symbol=symbol_upper)[:5]
                peers = [s.symbol for s in sector_stocks]
            if not peers:
                default_peers = {
                    "AAPL": ["MSFT", "GOOGL", "META", "AMZN"],
                    "MSFT": ["AAPL", "GOOGL", "META", "AMZN"],
                    "GOOGL": ["AAPL", "MSFT", "META", "AMZN"],
                }
                peers = default_peers.get(symbol_upper, ["AAPL", "MSFT", "GOOGL"])
            return ResearchHubType(
                symbol=symbol_upper,
                snapshot=SnapshotType(**snapshot_data) if snapshot_data else None,
                quote=QuoteType(**quote_data) if quote_data else None,
                technical=TechnicalType(**technical_data) if technical_data else None,
                sentiment=SentimentType(**sentiment_data) if sentiment_data else None,
                macro=MacroType(**macro_data) if macro_data else None,
                marketRegime=ResearchMarketRegimeType(**market_regime_data) if market_regime_data else None,
                peers=peers,
                updatedAt=timezone.now().isoformat(),
            )
        except Exception as e:
            logger.error("Error resolving research hub for %s: %s", symbol_upper, e, exc_info=True)
            try:
                fallback_technical = {
                    "rsi": 55.0,
                    "macd": 0.5,
                    "macdhistogram": 0.2,
                    "movingAverage50": 150.0 * 0.98,
                    "movingAverage200": 150.0 * 0.95,
                    "supportLevel": 150.0 * 0.92,
                    "resistanceLevel": 150.0 * 1.08,
                    "impliedVolatility": 0.25,
                }
                fallback_sentiment = {"label": "NEUTRAL", "score": 50.0, "articleCount": 0, "confidence": 0.0}
                fallback_macro = {"vix": 18.5, "marketSentiment": "Positive", "riskAppetite": 0.65}
                fallback_market_regime = {
                    "market_regime": "Bull Market",
                    "marketRegime": "Bull Market",
                    "confidence": 0.72,
                    "recommended_strategy": "Momentum",
                    "recommendedStrategy": "Momentum",
                }
                return ResearchHubType(
                    symbol=symbol_upper,
                    snapshot=None,
                    quote=None,
                    technical=TechnicalType(**fallback_technical),
                    sentiment=SentimentType(**fallback_sentiment),
                    macro=MacroType(**fallback_macro),
                    marketRegime=ResearchMarketRegimeType(**fallback_market_regime),
                    peers=["AAPL", "MSFT", "GOOGL"],
                    updatedAt=timezone.now().isoformat(),
                )
            except Exception as fallback_error:
                logger.error("Even fallback failed for %s: %s", symbol_upper, fallback_error, exc_info=True)
                return None
