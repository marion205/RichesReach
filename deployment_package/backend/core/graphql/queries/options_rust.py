"""
Rust engine and options flow GraphQL queries.
Exposes rust_stock_analysis, rust_options_analysis, options_flow, scan_options,
edge_predictions, one_tap_trades, iv_surface_forecast, rust_forex_analysis,
rust_sentiment_analysis, rust_correlation_analysis. Composed into ExtendedQuery.
"""
import json
import logging
import time
from datetime import datetime, timedelta

import graphene
from django.utils import timezone

logger = logging.getLogger(__name__)


def _calculate_fundamental_scores(features: dict, has_rust_data: bool):
    """Calculate fundamental analysis scores from Rust features or use defaults."""
    from core.types import FundamentalAnalysisType

    if not has_rust_data or not features:
        return FundamentalAnalysisType(
            valuationScore=70.0, growthScore=65.0, stabilityScore=80.0,
            dividendScore=60.0, debtScore=75.0,
        )
    pe_ratio = features.get("pe_ratio", 0.0) or 0.0
    dividend_yield = features.get("dividend_yield", 0.0) or 0.0
    volatility = features.get("volatility", 0.0) or 0.0
    risk_score = features.get("risk_score", 0.0) or 0.0
    if pe_ratio > 0:
        if pe_ratio < 15:
            valuation_score = 90.0 + (15 - pe_ratio) * 0.67
        elif pe_ratio < 25:
            valuation_score = 70.0 + (25 - pe_ratio) * 1.9
        elif pe_ratio < 35:
            valuation_score = 50.0 + (35 - pe_ratio) * 1.9
        else:
            valuation_score = max(0.0, 50.0 - (pe_ratio - 35) * 2.0)
    else:
        valuation_score = 70.0
    if volatility > 0:
        if 0.015 <= volatility <= 0.025:
            growth_score = 75.0 + (0.025 - volatility) * 1000
        elif volatility < 0.015:
            growth_score = 60.0 + volatility * 1000
        elif volatility <= 0.035:
            growth_score = 70.0 - (volatility - 0.025) * 1000
        else:
            growth_score = max(30.0, 50.0 - (volatility - 0.035) * 500)
    else:
        growth_score = 65.0
    if volatility > 0 and risk_score > 0:
        stability_score = max(0.0, min(100.0, 100.0 - (volatility * 2000 + risk_score * 20)))
    else:
        stability_score = 80.0
    if dividend_yield > 0:
        if dividend_yield >= 0.03:
            dividend_score = 80.0 + min(20.0, (dividend_yield - 0.03) * 1000)
        elif dividend_yield >= 0.01:
            dividend_score = 60.0 + (dividend_yield - 0.01) * 1000
        elif dividend_yield >= 0.005:
            dividend_score = 40.0 + (dividend_yield - 0.005) * 4000
        else:
            dividend_score = dividend_yield * 8000
    else:
        dividend_score = 0.0
    debt_score = max(50.0, min(100.0, 100.0 - (risk_score - 0.1) * 125)) if risk_score > 0 else 75.0
    return FundamentalAnalysisType(
        valuationScore=round(valuation_score, 1),
        growthScore=round(growth_score, 1),
        stabilityScore=round(stability_score, 1),
        dividendScore=round(dividend_score, 1),
        debtScore=round(debt_score, 1),
    )


class OptionsRustQuery(graphene.ObjectType):
    """Rust engine and options flow root fields."""

    rust_stock_analysis = graphene.Field(
        "core.types.RustStockAnalysisType",
        symbol=graphene.String(required=True),
    )
    rust_options_analysis = graphene.Field(
        "core.types.RustOptionsAnalysisType",
        symbol=graphene.String(required=True),
    )
    options_flow = graphene.Field(
        "core.options_flow_types.OptionsFlowType",
        symbol=graphene.String(required=True),
    )
    scan_options = graphene.List(
        "core.options_flow_types.ScannedOptionType",
        filters=graphene.String(required=False),
    )
    edge_predictions = graphene.List(
        "core.edge_prediction_types.EdgePredictionType",
        symbol=graphene.String(required=True),
    )
    one_tap_trades = graphene.List(
        "core.one_tap_trade_types.OneTapTradeType",
        symbol=graphene.String(required=True),
        account_size=graphene.Float(required=False),
        risk_tolerance=graphene.Float(required=False),
    )
    iv_surface_forecast = graphene.Field(
        "core.iv_forecast_types.IVSurfaceForecastType",
        symbol=graphene.String(required=True),
    )
    rust_forex_analysis = graphene.Field(
        "core.types.ForexAnalysisType",
        pair=graphene.String(required=True),
    )
    rust_sentiment_analysis = graphene.Field(
        "core.types.SentimentAnalysisType",
        symbol=graphene.String(required=True),
    )
    rust_correlation_analysis = graphene.Field(
        "core.types.CorrelationAnalysisType",
        primary=graphene.String(required=True),
        secondary=graphene.String(),
    )

    def resolve_rust_stock_analysis(self, info, symbol):
        """Get Rust engine stock analysis."""
        from core.types import (
            FundamentalAnalysisType,
            OptionsFlowDataPointType,
            RustStockAnalysisType,
            SpendingDataPointType,
            TechnicalIndicatorsType,
        )
        from core.rust_stock_service import rust_stock_service

        symbol_upper = symbol.upper()
        start_time = time.time()
        logger.info("rustStockAnalysis START for symbol: %s", symbol_upper)
        try:
            rust_response = rust_stock_service.analyze_stock(symbol_upper)
        except Exception as e:
            logger.warning("Rust service unavailable: %s. Using fallback.", e)
            rust_response = None
        end_date = timezone.now().date()
        base_price = 100.0
        fallback_spending_data = [
            SpendingDataPointType(
                date=(end_date - timedelta(weeks=w)).isoformat(),
                spending=1000.0 + (w * 50),
                spendingChange=0.05,
                price=base_price * (1 + 0.01 * (12 - w) / 12),
                priceChange=0.01,
            )
            for w in range(12, -1, -1)
        ]
        fallback_options_flow_data = [
            OptionsFlowDataPointType(
                date=(end_date - timedelta(days=d)).isoformat(),
                price=base_price * (1 + 0.005 * (20 - d) / 20),
                unusualVolumePercent=15.0,
                sweepCount=0,
                putCallRatio=0.8,
            )
            for d in range(20, -1, -1)
        ]
        features = rust_response.get("features", {}) if rust_response else {}
        price_usd = rust_response.get("price_usd") if rust_response else None
        if price_usd:
            if isinstance(price_usd, dict):
                price_value = price_usd.get("value", 100.0)
            elif isinstance(price_usd, str):
                try:
                    price_value = float(price_usd)
                except (ValueError, TypeError):
                    price_value = 100.0
            else:
                price_value = float(price_usd)
        else:
            price_value = float(features.get("price_usd", 100.0))
        sma20_val = features.get("sma_20", 0.0) or features.get("sma20", 0.0)
        sma50_val = features.get("sma_50", 0.0) or features.get("sma50", 0.0)
        rsi_val = features.get("rsi", 50.0) or 50.0
        macd_val = features.get("macd", 0.0) or 0.0
        if sma20_val > 0:
            bollinger_middle, bollinger_upper = sma20_val, sma20_val * 1.04
            bollinger_lower = sma20_val * 0.96
        else:
            bollinger_middle = price_value
            bollinger_upper, bollinger_lower = price_value * 1.04, price_value * 0.96
        has_rust_data = bool(rust_response and rust_response.get("features") and len(features) > 0)
        if has_rust_data:
            prediction_type = rust_response.get("prediction_type", "NEUTRAL")
            confidence = rust_response.get("confidence_level", "MEDIUM")
            probability = rust_response.get("probability", 0.5)
            recommendation = "BUY" if prediction_type == "BULLISH" and probability > 0.6 else "SELL" if prediction_type == "BEARISH" and probability > 0.6 else "HOLD"
            risk_level = "Low" if confidence == "HIGH" and probability > 0.6 else "Medium" if confidence == "MEDIUM" else "High"
            reasoning = [rust_response.get("explanation", "") or f"Rust analysis for {symbol_upper}"]
        else:
            recommendation, risk_level = "HOLD", "Medium"
            reasoning = [f"Fallback analysis for {symbol_upper}"]
        result = RustStockAnalysisType(
            symbol=symbol_upper,
            beginnerFriendlyScore=75.0,
            riskLevel=risk_level,
            recommendation=recommendation,
            technicalIndicators=TechnicalIndicatorsType(
                rsi=rsi_val,
                macd=macd_val,
                macdSignal=0.0,
                macdHistogram=0.0,
                sma20=sma20_val if sma20_val > 0 else price_value * 0.98,
                sma50=sma50_val if sma50_val > 0 else price_value * 0.95,
                ema12=0.0,
                ema26=0.0,
                bollingerUpper=bollinger_upper if sma20_val > 0 else 0.0,
                bollingerLower=bollinger_lower if sma20_val > 0 else 0.0,
                bollingerMiddle=bollinger_middle if sma20_val > 0 else 0.0,
            ),
            fundamentalAnalysis=_calculate_fundamental_scores(features, has_rust_data),
            reasoning=reasoning,
            spendingData=fallback_spending_data,
            optionsFlowData=fallback_options_flow_data,
            signalContributions=[],
            shapValues=[],
            shapExplanation=f"Fallback analysis for {symbol_upper}",
        )
        logger.info("rustStockAnalysis COMPLETE for %s in %.3fs", symbol_upper, time.time() - start_time)
        return result

    def resolve_options_flow(self, info, symbol):
        """
        Resolve options flow and unusual activity data using REAL Polygon data.

        Uses PolygonOptionsFlowService to detect unusual activity based on:
        - Volume vs Open Interest ratios
        - Large trades (blocks)
        - High volume relative to average
        - Unusual IV levels
        """
        from core.options_flow_types import LargestTradeType, OptionsFlowType, UnusualActivityType
        from core.polygon_options_flow_service import get_polygon_flow_service

        try:
            symbol_upper = symbol.upper()
            logger.info(f"Fetching real options flow for {symbol_upper}")

            # Use the new Polygon-based flow service
            flow_service = get_polygon_flow_service()
            flow_data = flow_service.get_unusual_options_flow(symbol_upper, limit=20)

            # Convert to GraphQL types
            unusual_activity = []
            for item in flow_data.get('unusual_activity', []):
                vol = item.get('volume', 0)
                oi = item.get('open_interest', 1)
                vol_oi_ratio = item.get('volume_oi_ratio', 0)

                unusual_activity.append(UnusualActivityType(
                    contractSymbol=item.get('contract_symbol', ''),
                    strike=float(item.get('strike', 0)),
                    expiration=item.get('expiration_date', ''),
                    optionType=item.get('option_type', 'call'),
                    volume=int(vol),
                    openInterest=int(oi),
                    volumeVsOI=float(vol_oi_ratio),
                    lastPrice=float(item.get('last_price', 0)),
                    bid=float(item.get('bid', 0)),
                    ask=float(item.get('ask', 0)),
                    impliedVolatility=float(item.get('implied_volatility', 0.25)),
                    unusualVolumePercent=float(item.get('unusual_score', 0)),
                    sweepCount=int(item.get('sweep_count', 0)),
                    blockSize=int(item.get('block_size', 0)),
                    isDarkPool=bool(item.get('is_dark_pool', False)),
                ))

            # Convert largest trades
            largest_trades = [
                LargestTradeType(
                    contractSymbol=trade.get('contract_symbol', ''),
                    size=int(trade.get('size', 0)),
                    price=float(trade.get('price', 0)),
                    time=trade.get('time', datetime.now().isoformat()),
                    isCall=bool(trade.get('is_call', True)),
                    isSweep=bool(trade.get('is_sweep', False)),
                    isBlock=bool(trade.get('is_block', False)),
                )
                for trade in flow_data.get('largest_trades', [])
            ]

            is_real = flow_data.get('is_real_data', False)
            logger.info(f"Options flow for {symbol_upper}: {len(unusual_activity)} unusual activities, real_data={is_real}")

            return OptionsFlowType(
                symbol=symbol_upper,
                timestamp=flow_data.get('timestamp', datetime.now().isoformat()),
                unusualActivity=unusual_activity,
                putCallRatio=float(flow_data.get('put_call_ratio', 0)),
                totalCallVolume=int(flow_data.get('total_call_volume', 0)),
                totalPutVolume=int(flow_data.get('total_put_volume', 0)),
                largestTrades=largest_trades,
            )

        except Exception as e:
            logger.error("Error resolving options flow: %s", e, exc_info=True)
            return OptionsFlowType(
                symbol=symbol.upper(),
                timestamp=datetime.now().isoformat(),
                unusualActivity=[],
                putCallRatio=0.0,
                totalCallVolume=0,
                totalPutVolume=0,
                largestTrades=[],
            )

    def resolve_scan_options(self, info, filters=None):
        """Resolve options scanner results."""
        from core.real_options_service import RealOptionsService

        try:
            filter_dict = json.loads(filters) if filters else {}
            options_service = RealOptionsService()
            options_data = options_service.get_real_options_chain("AAPL")
            all_options = []
            for call in (options_data.get("options_chain", {}).get("calls", []))[:20]:
                score = 75
                if filter_dict.get("minIV") and call.get("implied_volatility", 0) < filter_dict["minIV"]:
                    continue
                if filter_dict.get("maxIV") and call.get("implied_volatility", 0) > filter_dict["maxIV"]:
                    continue
                if filter_dict.get("minDelta") and call.get("delta", 0) < filter_dict["minDelta"]:
                    continue
                if call.get("volume", 0) < filter_dict.get("minVolume", 100):
                    continue
                opportunity = "High volatility play" if call.get("implied_volatility", 0) > 0.3 else "Strong directional move" if call.get("delta", 0) > 0.6 else "High liquidity trade"
                all_options.append({
                    "symbol": call.get("symbol", "AAPL"),
                    "contractSymbol": call.get("contract_symbol", ""),
                    "strike": call.get("strike", 0),
                    "expiration": call.get("expiration_date", ""),
                    "optionType": "call",
                    "bid": call.get("bid", 0),
                    "ask": call.get("ask", 0),
                    "volume": call.get("volume", 0),
                    "impliedVolatility": call.get("implied_volatility", 0),
                    "delta": call.get("delta", 0),
                    "theta": call.get("theta", 0),
                    "score": score,
                    "opportunity": opportunity,
                })
            all_options.sort(key=lambda x: x["score"], reverse=True)
            return all_options[:10]
        except Exception as e:
            logger.error("Error scanning options: %s", e, exc_info=True)
            return []

    def resolve_edge_predictions(self, info, symbol):
        """Get edge predictions for options chain."""
        from core.edge_prediction_types import EdgePredictionType
        from core.rust_stock_service import rust_stock_service

        symbol_upper = symbol.upper()
        try:
            rust_response = rust_stock_service.predict_edge(symbol_upper)
            predictions = rust_response if isinstance(rust_response, list) else []
            return [
                EdgePredictionType(
                    strike=float(p.get("strike", 0.0)),
                    expiration=str(p.get("expiration", "")),
                    option_type=str(p.get("option_type", "call")),
                    current_edge=float(p.get("current_edge", 0.0)),
                    predicted_edge_15min=float(p.get("predicted_edge_15min", 0.0)),
                    predicted_edge_1hr=float(p.get("predicted_edge_1hr", 0.0)),
                    predicted_edge_1day=float(p.get("predicted_edge_1day", 0.0)),
                    confidence=float(p.get("confidence", 0.0)),
                    explanation=str(p.get("explanation", "")),
                    edge_change_dollars=float(p.get("edge_change_dollars", 0.0)),
                    current_premium=float(p.get("current_premium", 0.0)),
                    predicted_premium_15min=float(p.get("predicted_premium_15min", 0.0)),
                    predicted_premium_1hr=float(p.get("predicted_premium_1hr", 0.0)),
                )
                for p in predictions
            ]
        except Exception as e:
            logger.warning("Error getting edge predictions for %s: %s", symbol_upper, e)
            return []

    def resolve_one_tap_trades(self, info, symbol, account_size=None, risk_tolerance=None):
        """Get one-tap trade recommendations."""
        from core.one_tap_trade_types import OneTapLegType, OneTapTradeType
        from core.rust_stock_service import rust_stock_service

        symbol_upper = symbol.upper()
        account_size_val = account_size if account_size is not None else 10000.0
        risk_tolerance_val = risk_tolerance if risk_tolerance is not None else 0.1
        try:
            rust_response = rust_stock_service.get_one_tap_trades(symbol_upper, account_size_val, risk_tolerance_val)
            trades = rust_response if isinstance(rust_response, list) else []
            result = []
            for trade in trades:
                legs = [
                    OneTapLegType(
                        action=str(leg.get("action", "buy")),
                        option_type=str(leg.get("option_type", "call")),
                        strike=float(leg.get("strike", 0.0)),
                        expiration=str(leg.get("expiration", "")),
                        quantity=int(leg.get("quantity", 1)),
                        premium=float(leg.get("premium", 0.0)),
                    )
                    for leg in trade.get("legs", [])
                ]
                result.append(OneTapTradeType(
                    strategy=str(trade.get("strategy", "")),
                    entry_price=float(trade.get("entry_price", 0.0)),
                    expected_edge=float(trade.get("expected_edge", 0.0)),
                    confidence=float(trade.get("confidence", 0.0)),
                    take_profit=float(trade.get("take_profit", 0.0)),
                    stop_loss=float(trade.get("stop_loss", 0.0)),
                    reasoning=str(trade.get("reasoning", "")),
                    max_loss=float(trade.get("max_loss", 0.0)),
                    max_profit=float(trade.get("max_profit", 0.0)),
                    probability_of_profit=float(trade.get("probability_of_profit", 0.0)),
                    symbol=str(trade.get("symbol", symbol_upper)),
                    legs=legs,
                    strategy_type=str(trade.get("strategy_type", "")),
                    days_to_expiration=int(trade.get("days_to_expiration", 30)),
                    total_cost=float(trade.get("total_cost", 0.0)),
                    total_credit=float(trade.get("total_credit", 0.0)),
                ))
            return result
        except Exception as e:
            logger.warning("Error getting one-tap trades for %s: %s", symbol_upper, e)
            return []

    def resolve_iv_surface_forecast(self, info, symbol):
        """Get IV surface forecast."""
        from core.iv_forecast_types import IVChangePointType, IVSurfaceForecastType
        from core.rust_stock_service import rust_stock_service

        symbol_upper = symbol.upper()
        try:
            rust_response = rust_stock_service.forecast_iv_surface(symbol_upper)
            if not rust_response:
                return None
            current_iv = rust_response.get("current_iv", {})
            predicted_iv_1hr = rust_response.get("predicted_iv_1hr", {})
            predicted_iv_24hr = rust_response.get("predicted_iv_24hr", {})
            current_iv_json = json.dumps({k: float(v) for k, v in current_iv.items()})
            predicted_iv_1hr_json = json.dumps({k: float(v) for k, v in predicted_iv_1hr.items()})
            predicted_iv_24hr_json = json.dumps({k: float(v) for k, v in predicted_iv_24hr.items()})
            heatmap = [
                IVChangePointType(
                    strike=float(pt.get("strike", 0.0)),
                    expiration=str(pt.get("expiration", "")),
                    current_iv=float(pt.get("current_iv", 0.0)),
                    predicted_iv_1hr=float(pt.get("predicted_iv_1hr", 0.0)),
                    predicted_iv_24hr=float(pt.get("predicted_iv_24hr", 0.0)),
                    iv_change_1hr_pct=float(pt.get("iv_change_1hr_pct", 0.0)),
                    iv_change_24hr_pct=float(pt.get("iv_change_24hr_pct", 0.0)),
                    confidence=float(pt.get("confidence", 0.0)),
                )
                for pt in rust_response.get("iv_change_heatmap", [])
            ]
            timestamp = rust_response.get("timestamp", "")
            if isinstance(timestamp, dict):
                timestamp = timestamp.get("$date", "") or str(timestamp)
            return IVSurfaceForecastType(
                symbol=str(rust_response.get("symbol", symbol_upper)),
                current_iv=current_iv_json,
                predicted_iv_1hr=predicted_iv_1hr_json,
                predicted_iv_24hr=predicted_iv_24hr_json,
                confidence=float(rust_response.get("confidence", 0.0)),
                regime=str(rust_response.get("regime", "normal")),
                iv_change_heatmap=heatmap,
                timestamp=str(timestamp),
            )
        except Exception as e:
            logger.warning("Error getting IV surface forecast for %s: %s", symbol_upper, e)
            return None

    def resolve_rust_options_analysis(self, info, symbol):
        """Get Rust engine options analysis."""
        from core.types import GreeksType, RustOptionsAnalysisType, StrikeRecommendationType, VolatilitySurfaceType
        from core.rust_stock_service import rust_stock_service

        symbol_upper = symbol.upper()
        try:
            rust_response = rust_stock_service.analyze_options(symbol_upper)
            vol_surface = rust_response.get("volatility_surface", {})
            greeks_data = rust_response.get("greeks", {})
            recommended_strikes = rust_response.get("recommended_strikes", [])
            return RustOptionsAnalysisType(
                symbol=rust_response.get("symbol", symbol_upper),
                underlyingPrice=float(rust_response.get("underlying_price", 0)),
                volatilitySurface=VolatilitySurfaceType(
                    atmVol=vol_surface.get("atm_vol", 0.0),
                    skew=vol_surface.get("skew", 0.0),
                    termStructure=vol_surface.get("term_structure", {}),
                ),
                greeks=GreeksType(
                    delta=greeks_data.get("delta", 0.0),
                    gamma=greeks_data.get("gamma", 0.0),
                    theta=greeks_data.get("theta", 0.0),
                    vega=greeks_data.get("vega", 0.0),
                    rho=greeks_data.get("rho", 0.0),
                ),
                recommendedStrikes=[
                    StrikeRecommendationType(
                        strike=s.get("strike", 0.0),
                        expiration=s.get("expiration", ""),
                        optionType=s.get("option_type", "call"),
                        greeks=GreeksType(
                            delta=s.get("greeks", {}).get("delta", 0.0),
                            gamma=s.get("greeks", {}).get("gamma", 0.0),
                            theta=s.get("greeks", {}).get("theta", 0.0),
                            vega=s.get("greeks", {}).get("vega", 0.0),
                            rho=s.get("greeks", {}).get("rho", 0.0),
                        ),
                        expectedReturn=s.get("expected_return", 0.0),
                        riskScore=s.get("risk_score", 0.0),
                    )
                    for s in recommended_strikes
                ],
                putCallRatio=rust_response.get("put_call_ratio", 0.0),
                impliedVolatilityRank=rust_response.get("implied_volatility_rank", 0.0),
                timestamp=rust_response.get("timestamp", ""),
            )
        except Exception as e:
            logger.error("Error getting Rust options analysis: %s", e)
            return RustOptionsAnalysisType(
                symbol=symbol_upper,
                underlyingPrice=0.0,
                volatilitySurface=VolatilitySurfaceType(atmVol=0.0, skew=0.0, termStructure={}),
                greeks=GreeksType(delta=0.0, gamma=0.0, theta=0.0, vega=0.0, rho=0.0),
                recommendedStrikes=[],
                putCallRatio=0.0,
                impliedVolatilityRank=0.0,
                timestamp="",
            )

    def resolve_rust_forex_analysis(self, info, pair):
        """Get Rust engine forex analysis."""
        from core.types import ForexAnalysisType
        from core.rust_stock_service import rust_stock_service

        pair_upper = pair.upper()
        try:
            rust_response = rust_stock_service.analyze_forex(pair_upper)
            return ForexAnalysisType(
                pair=rust_response.get("pair", pair_upper),
                bid=float(rust_response.get("bid", 0)),
                ask=float(rust_response.get("ask", 0)),
                spread=rust_response.get("spread", 0.0),
                pipValue=rust_response.get("pip_value", 0.0),
                volatility=rust_response.get("volatility", 0.0),
                trend=rust_response.get("trend", "NEUTRAL"),
                supportLevel=float(rust_response.get("support_level", 0)),
                resistanceLevel=float(rust_response.get("resistance_level", 0)),
                correlation24h=rust_response.get("correlation_24h", 0.0),
                timestamp=rust_response.get("timestamp", ""),
            )
        except Exception as e:
            logger.error("Error getting Rust forex analysis: %s", e)
            return ForexAnalysisType(
                pair=pair_upper,
                bid=0.0, ask=0.0, spread=0.0, pipValue=0.0, volatility=0.0,
                trend="NEUTRAL", supportLevel=0.0, resistanceLevel=0.0,
                correlation24h=0.0, timestamp="",
            )

    def resolve_rust_sentiment_analysis(self, info, symbol):
        """Get Rust engine sentiment analysis."""
        from core.types import NewsSentimentType, SentimentAnalysisType, SocialSentimentType
        from core.rust_stock_service import rust_stock_service

        symbol_upper = symbol.upper()
        try:
            rust_response = rust_stock_service.analyze_sentiment(symbol_upper)
            news_sentiment = rust_response.get("news_sentiment", {})
            social_sentiment = rust_response.get("social_sentiment", {})
            return SentimentAnalysisType(
                symbol=rust_response.get("symbol", symbol_upper),
                overallSentiment=rust_response.get("overall_sentiment", "NEUTRAL"),
                sentimentScore=rust_response.get("sentiment_score", 0.0),
                newsSentiment=NewsSentimentType(
                    score=news_sentiment.get("score", 0.0),
                    articleCount=news_sentiment.get("article_count", 0),
                    positiveArticles=news_sentiment.get("positive_articles", 0),
                    negativeArticles=news_sentiment.get("negative_articles", 0),
                    neutralArticles=news_sentiment.get("neutral_articles", 0),
                    topHeadlines=news_sentiment.get("top_headlines", []),
                ),
                socialSentiment=SocialSentimentType(
                    score=social_sentiment.get("score", 0.0),
                    mentions24h=social_sentiment.get("mentions_24h", 0),
                    positiveMentions=social_sentiment.get("positive_mentions", 0),
                    negativeMentions=social_sentiment.get("negative_mentions", 0),
                    engagementScore=social_sentiment.get("engagement_score", 0.0),
                    trending=social_sentiment.get("trending", False),
                ),
                confidence=rust_response.get("confidence", 0.0),
                timestamp=rust_response.get("timestamp", ""),
            )
        except Exception as e:
            logger.error("Error getting Rust sentiment analysis: %s", e)
            return SentimentAnalysisType(
                symbol=symbol_upper,
                overallSentiment="NEUTRAL",
                sentimentScore=0.0,
                newsSentiment=NewsSentimentType(score=0.0, articleCount=0, positiveArticles=0, negativeArticles=0, neutralArticles=0, topHeadlines=[]),
                socialSentiment=SocialSentimentType(score=0.0, mentions24h=0, positiveMentions=0, negativeMentions=0, engagementScore=0.0, trending=False),
                confidence=0.0,
                timestamp="",
            )

    def resolve_rust_correlation_analysis(self, info, primary, secondary=None):
        """Get Rust engine correlation analysis."""
        from core.types import CorrelationAnalysisType
        from core.rust_stock_service import rust_stock_service

        primary_upper = primary.upper()
        try:
            rust_response = rust_stock_service.analyze_correlation(primary_upper, secondary)
            return CorrelationAnalysisType(
                primarySymbol=rust_response.get("primary_symbol", primary_upper),
                secondarySymbol=rust_response.get("secondary_symbol", secondary or "SPY"),
                correlation1d=rust_response.get("correlation_1d", 0.0),
                correlation7d=rust_response.get("correlation_7d", 0.0),
                correlation30d=rust_response.get("correlation_30d", 0.0),
                btcDominance=rust_response.get("btc_dominance"),
                spyCorrelation=rust_response.get("spy_correlation"),
                globalRegime=rust_response.get("global_regime", "NEUTRAL"),
                localContext=rust_response.get("local_context", "NORMAL"),
                timestamp=rust_response.get("timestamp", ""),
            )
        except Exception as e:
            logger.error("Error getting Rust correlation analysis: %s", e)
            return CorrelationAnalysisType(
                primarySymbol=primary_upper,
                secondarySymbol=secondary or "SPY",
                correlation1d=0.0,
                correlation7d=0.0,
                correlation30d=0.0,
                btcDominance=None,
                spyCorrelation=None,
                globalRegime="NEUTRAL",
                localContext="NORMAL",
                timestamp="",
            )
