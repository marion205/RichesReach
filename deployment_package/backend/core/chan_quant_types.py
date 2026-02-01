# core/chan_quant_types.py
"""
GraphQL types for Chan Quantitative Signal Engine
"""

import graphene
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MeanReversionSignalType(graphene.ObjectType):
    """GraphQL type for mean reversion signal"""
    symbol = graphene.String(required=True)
    currentPrice = graphene.Float(required=True)
    meanPrice = graphene.Float(required=True)
    deviationSigma = graphene.Float(required=True, description="Standard deviations from mean")
    reversionProbability = graphene.Float(required=True, description="Probability of reversion (0-1)")
    expectedDrawdown = graphene.Float(required=True, description="Expected max drawdown before reversion")
    timeframeDays = graphene.Int(required=True, description="Expected reversion timeframe")
    confidence = graphene.String(required=True, description="high, medium, or low")
    explanation = graphene.String(required=True, description="Human-readable explanation")


class MomentumAlignmentType(graphene.ObjectType):
    """GraphQL type for momentum alignment across timeframes"""
    daily = graphene.Boolean(required=True)
    weekly = graphene.Boolean(required=True)
    monthly = graphene.Boolean(required=True)


class MomentumSignalType(graphene.ObjectType):
    """GraphQL type for momentum signal"""
    symbol = graphene.String(required=True)
    currentPrice = graphene.Float(required=True)
    momentumAlignment = graphene.Field(MomentumAlignmentType, required=True)
    trendPersistenceHalfLife = graphene.Float(required=True, description="Days until momentum decays by 50%")
    momentumDecayProbability = graphene.Float(required=True, description="Probability momentum decays in next 7 days")
    timingConfidence = graphene.Float(required=True, description="Overall timing confidence (0-1)")
    confidence = graphene.String(required=True, description="high, medium, or low")
    explanation = graphene.String(required=True, description="Human-readable explanation")


class KellyPositionSizeType(graphene.ObjectType):
    """GraphQL type for Kelly Criterion position sizing"""
    symbol = graphene.String(required=True)
    winRate = graphene.Float(required=True, description="Historical win rate (0-1)")
    avgWin = graphene.Float(required=True, description="Average win percentage")
    avgLoss = graphene.Float(required=True, description="Average loss percentage")
    kellyFraction = graphene.Float(required=True, description="Optimal Kelly fraction (0-1)")
    recommendedFraction = graphene.Float(required=True, description="Conservative Kelly (usually Kelly * 0.25)")
    maxDrawdownRisk = graphene.Float(required=True, description="Expected max drawdown with this position size")
    explanation = graphene.String(required=True, description="Human-readable explanation")


class RegimeRobustnessScoreType(graphene.ObjectType):
    """GraphQL type for regime robustness score"""
    symbol = graphene.String(required=True)
    signalType = graphene.String(required=True, description="mean_reversion or momentum")
    regimesTested = graphene.List(graphene.String, required=True, description="List of regimes tested")
    robustnessScore = graphene.Float(required=True, description="Robustness score (0-1)")
    worstRegimePerformance = graphene.Float(required=True, description="Worst Sharpe/return in any regime")
    bestRegimePerformance = graphene.Float(required=True, description="Best Sharpe/return in any regime")
    explanation = graphene.String(required=True, description="Human-readable explanation")


class ChanQuantSignalsType(graphene.ObjectType):
    """Combined Chan quantitative signals for a symbol"""
    symbol = graphene.String(required=True)
    meanReversion = graphene.Field(MeanReversionSignalType, description="Mean reversion signal")
    momentum = graphene.Field(MomentumSignalType, description="Momentum signal")
    kellyPositionSize = graphene.Field(KellyPositionSizeType, description="Kelly Criterion position sizing")
    regimeRobustness = graphene.Field(RegimeRobustnessScoreType, description="Regime robustness score")


class ChanQuantQueries(graphene.ObjectType):
    """GraphQL queries for Chan quantitative signals"""
    
    chanQuantSignals = graphene.Field(
        ChanQuantSignalsType,
        symbol=graphene.String(required=True),
        description="Get Chan quantitative signals (mean reversion, momentum, Kelly, regime robustness) for a symbol"
    )
    
    def resolve_chanQuantSignals(self, info, symbol: str):
        """Resolve Chan quantitative signals"""
        from .chan_quant_signal_engine import (
            ChanQuantSignalEngine, MeanReversionSignal, MomentumSignal,
            KellyPositionSize, RegimeRobustnessScore
        )
        from .fss_data_pipeline import FSSDataPipeline, FSSDataRequest
        import pandas as pd
        import asyncio
        
        try:
            engine = ChanQuantSignalEngine()
            
            # Use FSSDataPipeline to fetch data synchronously
            # This is a simpler approach that avoids async complexity
            try:
                pipeline = FSSDataPipeline()
                data_result = asyncio.run(pipeline.fetch_data(
                    tickers=[symbol],
                    request=FSSDataRequest(lookback_days=252, include_fundamentals=False)
                ))
                
                if not data_result or data_result.prices.empty or symbol not in data_result.prices.columns:
                    logger.warning(f"No price data available for {symbol}")
                    return None
                
                prices = data_result.prices[symbol]
                spy_prices = data_result.spy if data_result.spy is not None else None
                regime_series = data_result.regime_series if hasattr(data_result, 'regime_series') else None
                
            except Exception as pipeline_error:
                logger.warning(f"FSSDataPipeline failed for {symbol}, trying fallback: {pipeline_error}")
                # Fallback: try to use yfinance directly
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1y")
                    if hist.empty:
                        logger.warning(f"No yfinance data for {symbol}")
                        return None
                    prices = hist['Close']
                    # Get SPY for relative strength
                    spy_ticker = yf.Ticker("SPY")
                    spy_hist = spy_ticker.history(period="1y")
                    spy_prices = spy_hist['Close'] if not spy_hist.empty else None
                    regime_series = None
                except Exception as yf_error:
                    logger.error(f"Both FSSDataPipeline and yfinance failed for {symbol}: {yf_error}")
                    return None
            
            if prices is None or len(prices) < 20:
                logger.warning(f"Insufficient price data for {symbol}: {len(prices) if prices is not None else 0} days")
                return None
            
            # Ensure prices is a Series with datetime index
            if not isinstance(prices, pd.Series):
                prices = pd.Series(prices)
            if not isinstance(prices.index, pd.DatetimeIndex):
                prices.index = pd.to_datetime(prices.index)
            
            # Calculate mean reversion signal (Bollinger Bands method)
            mean_rev = engine.calculate_mean_reversion_signal(symbol, prices)
            
            # Calculate momentum signal
            momentum = engine.calculate_momentum_signal(symbol, prices, spy_prices)
            
            # Calculate Kelly position size
            returns = prices.pct_change().dropna()
            kelly = engine.calculate_kelly_position_size(symbol, returns)
            
            # Calculate regime robustness (if regime data available)
            regime_robustness = None
            if regime_series is not None:
                try:
                    regime_robustness = engine.calculate_regime_robustness(
                        symbol, "mean_reversion", prices, regime_series
                    )
                except Exception as reg_error:
                    logger.warning(f"Failed to calculate regime robustness for {symbol}: {reg_error}")
                    regime_robustness = None
            
            # Convert to GraphQL types
            return ChanQuantSignalsType(
                symbol=symbol,
                meanReversion=MeanReversionSignalType(
                    symbol=mean_rev.symbol,
                    currentPrice=mean_rev.current_price,
                    meanPrice=mean_rev.mean_price,
                    deviationSigma=mean_rev.deviation_sigma,
                    reversionProbability=mean_rev.reversion_probability,
                    expectedDrawdown=mean_rev.expected_drawdown,
                    timeframeDays=mean_rev.timeframe_days,
                    confidence=mean_rev.confidence,
                    explanation=mean_rev.explanation
                ),
                momentum=MomentumSignalType(
                    symbol=momentum.symbol,
                    currentPrice=momentum.current_price,
                    momentumAlignment=MomentumAlignmentType(
                        daily=momentum.momentum_alignment["daily"],
                        weekly=momentum.momentum_alignment["weekly"],
                        monthly=momentum.momentum_alignment["monthly"]
                    ),
                    trendPersistenceHalfLife=momentum.trend_persistence_half_life,
                    momentumDecayProbability=momentum.momentum_decay_probability,
                    timingConfidence=momentum.timing_confidence,
                    confidence=momentum.confidence,
                    explanation=momentum.explanation
                ),
                kellyPositionSize=KellyPositionSizeType(
                    symbol=kelly.symbol,
                    winRate=kelly.win_rate,
                    avgWin=kelly.avg_win,
                    avgLoss=kelly.avg_loss,
                    kellyFraction=kelly.kelly_fraction,
                    recommendedFraction=kelly.recommended_fraction,
                    maxDrawdownRisk=kelly.max_drawdown_risk,
                    explanation=kelly.explanation
                ),
                regimeRobustness=RegimeRobustnessScoreType(
                    symbol=regime_robustness.symbol,
                    signalType=regime_robustness.signal_type,
                    regimesTested=regime_robustness.regimes_tested,
                    robustnessScore=regime_robustness.robustness_score,
                    worstRegimePerformance=regime_robustness.worst_regime_performance,
                    bestRegimePerformance=regime_robustness.best_regime_performance,
                    explanation=regime_robustness.explanation
                ) if regime_robustness else None
            )
            
        except Exception as e:
            logger.error(f"Error resolving Chan quant signals for {symbol}: {e}", exc_info=True)
            return None

