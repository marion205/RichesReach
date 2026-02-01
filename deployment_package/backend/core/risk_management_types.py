"""
GraphQL types and resolvers for risk management calculations
"""
import graphene
from .graphql_utils import get_user_from_context


class PositionSizeType(graphene.ObjectType):
    """Position size calculation result"""
    positionSize = graphene.Int()
    dollarRisk = graphene.Float()
    positionValue = graphene.Float()
    positionPct = graphene.Float()
    riskPerTradePct = graphene.Float()
    method = graphene.String()
    riskPerShare = graphene.Float()
    maxSharesFixedRisk = graphene.Int()
    maxSharesPosition = graphene.Int()
    # Kelly-specific fields
    kellyFraction = graphene.Float(description="Optimal Kelly fraction (0-1)")
    recommendedFraction = graphene.Float(description="Conservative Kelly recommendation (usually Kelly * 0.25)")
    maxDrawdownRisk = graphene.Float(description="Expected max drawdown with this position size")
    winRate = graphene.Float(description="Historical win rate (0-1)")
    avgWin = graphene.Float(description="Average win percentage")
    avgLoss = graphene.Float(description="Average loss percentage")


class DynamicStopType(graphene.ObjectType):
    """Dynamic stop loss calculation result"""
    stopPrice = graphene.Float()
    stopDistance = graphene.Float()
    riskPercentage = graphene.Float()
    method = graphene.String()
    atrStop = graphene.Float()
    srStop = graphene.Float()
    pctStop = graphene.Float()


class TargetPriceType(graphene.ObjectType):
    """Target price calculation result"""
    targetPrice = graphene.Float()
    rewardDistance = graphene.Float()
    riskRewardRatio = graphene.Float()
    method = graphene.String()
    rrTarget = graphene.Float()
    atrTarget = graphene.Float()
    srTarget = graphene.Float()


class PortfolioKellyMetricsType(graphene.ObjectType):
    """Portfolio-level Kelly Criterion metrics"""
    totalPortfolioValue = graphene.Float(description="Total portfolio value")
    aggregateKellyFraction = graphene.Float(description="Weighted average Kelly fraction across all positions")
    aggregateRecommendedFraction = graphene.Float(description="Weighted average recommended (conservative) Kelly fraction")
    portfolioMaxDrawdownRisk = graphene.Float(description="Expected max drawdown for entire portfolio")
    weightedWinRate = graphene.Float(description="Weighted average win rate across positions")
    positionCount = graphene.Int(description="Number of positions with Kelly data")
    totalPositions = graphene.Int(description="Total number of positions in portfolio")


class RiskManagementQueries(graphene.ObjectType):
    """Risk management calculation queries"""
    
    portfolioKellyMetrics = graphene.Field(
        PortfolioKellyMetricsType,
        description="Calculate portfolio-level Kelly Criterion metrics across all positions"
    )
    
    calculatePositionSize = graphene.Field(
        PositionSizeType,
        accountEquity=graphene.Float(required=True),
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskPerTrade=graphene.Float(),
        maxPositionPct=graphene.Float(),
        confidence=graphene.Float(),
        method=graphene.String(description="Position sizing method: 'FIXED_RISK', 'PERCENTAGE', or 'KELLY'"),
        symbol=graphene.String(description="Stock symbol (required for KELLY method)"),
        description="Calculate optimal position size based on risk parameters"
    )
    
    calculateDynamicStop = graphene.Field(
        DynamicStopType,
        entryPrice=graphene.Float(required=True),
        atr=graphene.Float(required=True),
        atrMultiplier=graphene.Float(),
        supportLevel=graphene.Float(),
        resistanceLevel=graphene.Float(),
        signalType=graphene.String(),
        description="Calculate dynamic stop loss based on ATR and support/resistance"
    )
    
    calculateTargetPrice = graphene.Field(
        TargetPriceType,
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskRewardRatio=graphene.Float(),
        atr=graphene.Float(),
        resistanceLevel=graphene.Float(),
        supportLevel=graphene.Float(),
        signalType=graphene.String(),
        description="Calculate target price based on risk/reward ratio and technical levels"
    )
    
    def resolve_portfolioKellyMetrics(self, info):
        """Calculate portfolio-level Kelly Criterion metrics"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            user = get_user_from_context(info.context)
            if not user or getattr(user, "is_anonymous", True):
                logger.warning("Portfolio Kelly metrics: User not authenticated")
                return PortfolioKellyMetricsType(
                    totalPortfolioValue=0.0,
                    aggregateKellyFraction=0.0,
                    aggregateRecommendedFraction=0.0,
                    portfolioMaxDrawdownRisk=0.0,
                    weightedWinRate=0.0,
                    positionCount=0,
                    totalPositions=0
                )
        except Exception as e:
            logger.error(f"Error getting user from context: {e}", exc_info=True)
            return PortfolioKellyMetricsType(
                totalPortfolioValue=0.0,
                aggregateKellyFraction=0.0,
                aggregateRecommendedFraction=0.0,
                portfolioMaxDrawdownRisk=0.0,
                weightedWinRate=0.0,
                positionCount=0,
                totalPositions=0
            )
        
        try:
            from .portfolio_service import PortfolioService
            from .chan_quant_signal_engine import ChanQuantSignalEngine
            from .fss_data_pipeline import FSSDataPipeline, FSSDataRequest
            import pandas as pd
            import asyncio
            
            # Get user's portfolio holdings
            portfolios_data = PortfolioService.get_user_portfolios(user)
            if not portfolios_data or not portfolios_data.get('portfolios'):
                return PortfolioKellyMetricsType(
                    totalPortfolioValue=0.0,
                    aggregateKellyFraction=0.0,
                    aggregateRecommendedFraction=0.0,
                    portfolioMaxDrawdownRisk=0.0,
                    weightedWinRate=0.0,
                    positionCount=0,
                    totalPositions=0
                )
            
            # Collect all holdings across all portfolios
            all_holdings = []
            total_portfolio_value = 0.0
            total_positions = 0
            
            for portfolio in portfolios_data.get('portfolios', []):
                for holding in portfolio.get('holdings', []):
                    total_positions += 1  # Count all positions
                    stock = holding.get('stock')
                    if not stock:
                        continue
                    
                    # Handle both model objects and dicts
                    if hasattr(stock, 'symbol'):
                        symbol = stock.symbol
                    elif isinstance(stock, dict):
                        symbol = stock.get('symbol')
                    else:
                        continue
                    
                    if not symbol:
                        continue
                    
                    shares = float(holding.get('shares', 0) or 0)
                    # Use current_price, fallback to average_price, fallback to 0
                    current_price = float(
                        holding.get('current_price') or 
                        holding.get('average_price') or 
                        0
                    )
                    position_value = shares * current_price
                    
                    if position_value > 0:
                        all_holdings.append({
                            'symbol': symbol,
                            'shares': shares,
                            'current_price': current_price,
                            'position_value': position_value
                        })
                        total_portfolio_value += position_value
            
            if not all_holdings:
                logger.info(f"Portfolio Kelly: Found {total_positions} positions but none with valid price data")
                return PortfolioKellyMetricsType(
                    totalPortfolioValue=float(total_portfolio_value),
                    aggregateKellyFraction=0.0,
                    aggregateRecommendedFraction=0.0,
                    portfolioMaxDrawdownRisk=0.0,
                    weightedWinRate=0.0,
                    positionCount=0,
                    totalPositions=total_positions
                )
                return PortfolioKellyMetricsType(
                    totalPortfolioValue=0.0,
                    aggregateKellyFraction=0.0,
                    aggregateRecommendedFraction=0.0,
                    portfolioMaxDrawdownRisk=0.0,
                    weightedWinRate=0.0,
                    positionCount=0,
                    totalPositions=0
                )
            
            # Calculate Kelly metrics for each position
            engine = ChanQuantSignalEngine()
            pipeline = FSSDataPipeline()
            
            kelly_data = []
            positions_with_kelly = 0
            
            for holding in all_holdings:
                symbol = holding['symbol']
                position_value = holding['position_value']
                
                try:
                    # Fetch historical data - use yfinance directly to avoid async issues
                    # This is simpler and more reliable for this use case
                    try:
                        import yfinance as yf
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period="1y")
                        if hist.empty:
                            logger.debug(f"No data for {symbol}, skipping")
                            continue
                        prices = hist['Close']
                    except Exception as yf_error:
                        logger.debug(f"yfinance failed for {symbol}: {yf_error}, trying FSSDataPipeline")
                        # Fallback to FSSDataPipeline if yfinance fails
                        try:
                            # Try to get event loop safely
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # Can't use asyncio.run() if loop is running
                                    logger.warning(f"Event loop running for {symbol}, skipping FSSDataPipeline")
                                    continue
                            except RuntimeError:
                                # No event loop, safe to use asyncio.run()
                                pass
                            
                            data_result = asyncio.run(pipeline.fetch_data(
                                tickers=[symbol],
                                request=FSSDataRequest(lookback_days=252, include_fundamentals=False)
                            ))
                            
                            if not data_result or data_result.prices.empty or symbol not in data_result.prices.columns:
                                continue
                            prices = data_result.prices[symbol]
                        except Exception as fss_error:
                            logger.debug(f"FSSDataPipeline also failed for {symbol}: {fss_error}")
                            continue
                    
                    if not data_result or data_result.prices.empty or symbol not in data_result.prices.columns:
                        # Fallback to yfinance
                        try:
                            import yfinance as yf
                            ticker = yf.Ticker(symbol)
                            hist = ticker.history(period="1y")
                            if hist.empty:
                                continue
                            prices = hist['Close']
                        except Exception:
                            continue
                    else:
                        prices = data_result.prices[symbol]
                    
                    if len(prices) < 20:
                        continue
                    
                    # Calculate Kelly
                    returns = prices.pct_change().dropna()
                    kelly_result = engine.calculate_kelly_position_size(symbol, returns)
                    
                    # Weight by position value
                    weight = position_value / total_portfolio_value if total_portfolio_value > 0 else 0
                    
                    kelly_data.append({
                        'kelly_fraction': kelly_result.kelly_fraction,
                        'recommended_fraction': kelly_result.recommended_fraction,
                        'max_drawdown_risk': kelly_result.max_drawdown_risk,
                        'win_rate': kelly_result.win_rate,
                        'weight': weight,
                        'position_value': position_value
                    })
                    positions_with_kelly += 1
                    
                except Exception as e:
                    logger.warning(f"Error calculating Kelly for {symbol}: {e}")
                    continue
            
            if not kelly_data:
                return PortfolioKellyMetricsType(
                    totalPortfolioValue=float(total_portfolio_value),
                    aggregateKellyFraction=0.0,
                    aggregateRecommendedFraction=0.0,
                    portfolioMaxDrawdownRisk=0.0,
                    weightedWinRate=0.0,
                    positionCount=0,
                    totalPositions=len(all_holdings)
                )
            
            # Calculate weighted averages
            aggregate_kelly = sum(d['kelly_fraction'] * d['weight'] for d in kelly_data)
            aggregate_recommended = sum(d['recommended_fraction'] * d['weight'] for d in kelly_data)
            weighted_win_rate = sum(d['win_rate'] * d['weight'] for d in kelly_data)
            
            # Portfolio max drawdown is the maximum individual drawdown (conservative)
            portfolio_max_drawdown = max(d['max_drawdown_risk'] for d in kelly_data) if kelly_data else 0.0
            
            logger.info(f"Portfolio Kelly: Calculated metrics for {positions_with_kelly}/{total_positions} positions")
            return PortfolioKellyMetricsType(
                totalPortfolioValue=float(total_portfolio_value),
                aggregateKellyFraction=float(aggregate_kelly),
                aggregateRecommendedFraction=float(aggregate_recommended),
                portfolioMaxDrawdownRisk=float(portfolio_max_drawdown),
                weightedWinRate=float(weighted_win_rate),
                positionCount=positions_with_kelly,
                totalPositions=total_positions
            )
            
        except Exception as e:
            logger.error(f"Error calculating portfolio Kelly metrics: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return empty metrics instead of None to avoid GraphQL errors
            return PortfolioKellyMetricsType(
                totalPortfolioValue=0.0,
                aggregateKellyFraction=0.0,
                aggregateRecommendedFraction=0.0,
                portfolioMaxDrawdownRisk=0.0,
                weightedWinRate=0.0,
                positionCount=0,
                totalPositions=0
            )
    
    def resolve_calculatePositionSize(
        self, info,
        accountEquity: float,
        entryPrice: float,
        stopPrice: float,
        riskPerTrade: float = None,
        maxPositionPct: float = None,
        confidence: float = None,
        method: str = None,
        symbol: str = None
    ):
        """Calculate position size"""
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Default method: FIXED_RISK
        sizing_method = (method or "FIXED_RISK").upper()
        
        # KELLY method requires symbol
        if sizing_method == "KELLY":
            if not symbol:
                logger.warning("KELLY method requires symbol parameter")
                return PositionSizeType(
                    positionSize=0,
                    dollarRisk=0.0,
                    positionValue=0.0,
                    positionPct=0.0,
                    riskPerTradePct=0.0,
                    method="error",
                    riskPerShare=0.0,
                    maxSharesFixedRisk=0,
                    maxSharesPosition=0,
                    kellyFraction=None,
                    recommendedFraction=None,
                    maxDrawdownRisk=None,
                    winRate=None,
                    avgWin=None,
                    avgLoss=None
                )
            
            # Calculate Kelly-based position size
            try:
                from .chan_quant_signal_engine import ChanQuantSignalEngine
                from .fss_data_pipeline import FSSDataPipeline, FSSDataRequest
                import pandas as pd
                import asyncio
                
                engine = ChanQuantSignalEngine()
                
                # Fetch historical price data
                try:
                    pipeline = FSSDataPipeline()
                    data_result = asyncio.run(pipeline.fetch_data(
                        tickers=[symbol],
                        request=FSSDataRequest(lookback_days=252, include_fundamentals=False)
                    ))
                    
                    if not data_result or data_result.prices.empty or symbol not in data_result.prices.columns:
                        # Fallback to yfinance
                        try:
                            import yfinance as yf
                            ticker = yf.Ticker(symbol)
                            hist = ticker.history(period="1y")
                            if hist.empty:
                                raise ValueError(f"No data for {symbol}")
                            prices = hist['Close']
                        except Exception as yf_error:
                            logger.error(f"Failed to fetch data for {symbol}: {yf_error}")
                            raise ValueError(f"Cannot fetch historical data for {symbol}")
                    else:
                        prices = data_result.prices[symbol]
                    
                    if len(prices) < 20:
                        raise ValueError(f"Insufficient data for {symbol}: {len(prices)} days")
                    
                    # Calculate Kelly
                    returns = prices.pct_change().dropna()
                    kelly_result = engine.calculate_kelly_position_size(symbol, returns)
                    
                    # Use recommended fraction (conservative Kelly)
                    recommended_fraction = float(kelly_result.recommended_fraction)
                    account_equity = float(accountEquity)
                    
                    # Calculate position value based on Kelly
                    position_value = account_equity * recommended_fraction
                    position_size = int(position_value / entryPrice) if entryPrice > 0 else 0
                    
                    # Calculate risk metrics
                    risk_per_share = abs(entryPrice - stopPrice) if stopPrice else entryPrice * 0.02  # 2% default
                    dollar_risk = float(position_size * risk_per_share)
                    position_pct = float((position_value / account_equity) * 100) if account_equity > 0 else 0.0
                    
                    # Apply max position cap if provided
                    if maxPositionPct:
                        max_position_value = account_equity * float(maxPositionPct)
                        max_shares_position = int(max_position_value / entryPrice) if entryPrice > 0 else 0
                        if position_size > max_shares_position:
                            position_size = max_shares_position
                            position_value = float(position_size * entryPrice)
                            dollar_risk = float(position_size * risk_per_share)
                            position_pct = float((position_value / account_equity) * 100) if account_equity > 0 else 0.0
                    
                    return PositionSizeType(
                        positionSize=position_size,
                        dollarRisk=dollar_risk,
                        positionValue=position_value,
                        positionPct=position_pct,
                        riskPerTradePct=float(recommended_fraction * 100),
                        method="kelly",
                        riskPerShare=float(risk_per_share),
                        maxSharesFixedRisk=position_size,
                        maxSharesPosition=position_size,
                        kellyFraction=float(kelly_result.kelly_fraction),
                        recommendedFraction=float(recommended_fraction),
                        maxDrawdownRisk=float(kelly_result.max_drawdown_risk),
                        winRate=float(kelly_result.win_rate),
                        avgWin=float(kelly_result.avg_win),
                        avgLoss=float(kelly_result.avg_loss)
                    )
                    
                except Exception as e:
                    logger.error(f"Error calculating Kelly position size for {symbol}: {e}", exc_info=True)
                    # Fall back to fixed risk method
                    sizing_method = "FIXED_RISK"
            except Exception as e:
                logger.error(f"Error in Kelly calculation setup for {symbol}: {e}", exc_info=True)
                # Fall back to fixed risk method
                sizing_method = "FIXED_RISK"
        
        # Default risk per trade: 1% if not specified
        risk_per_trade_pct = float(riskPerTrade) if riskPerTrade else 0.01
        max_position_pct = float(maxPositionPct) if maxPositionPct else 0.10  # 10% max
        
        # Calculate risk per share
        risk_per_share = abs(entryPrice - stopPrice)
        if risk_per_share == 0:
            return PositionSizeType(
                positionSize=0,
                dollarRisk=0.0,
                positionValue=0.0,
                positionPct=0.0,
                riskPerTradePct=risk_per_trade_pct * 100,
                method="invalid",
                riskPerShare=0.0,
                maxSharesFixedRisk=0,
                maxSharesPosition=0,
                kellyFraction=None,
                recommendedFraction=None,
                maxDrawdownRisk=None,
                winRate=None,
                avgWin=None,
                avgLoss=None
            )
        
        # Calculate max dollars at risk
        account_equity = float(accountEquity)
        max_dollars_at_risk = account_equity * risk_per_trade_pct
        
        # Calculate shares based on fixed risk
        max_shares_fixed_risk = int(max_dollars_at_risk / risk_per_share)
        
        # Calculate shares based on max position size
        max_position_value = account_equity * max_position_pct
        max_shares_position = int(max_position_value / entryPrice)
        
        # Use the smaller of the two
        position_size = min(max_shares_fixed_risk, max_shares_position)
        
        # Calculate actual values
        dollar_risk = float(position_size * risk_per_share)
        position_value = float(position_size * entryPrice)
        position_pct = float((position_value / account_equity) * 100) if account_equity > 0 else 0.0
        
        # Adjust for confidence if provided
        if confidence and 0 < confidence < 1:
            position_size = int(position_size * confidence)
            dollar_risk = float(position_size * risk_per_share)
            position_value = float(position_size * entryPrice)
            position_pct = float((position_value / account_equity) * 100) if account_equity > 0 else 0.0
        
        method_name = "fixed_risk" if max_shares_fixed_risk <= max_shares_position else "max_position"
        
        return PositionSizeType(
            positionSize=position_size,
            dollarRisk=dollar_risk,
            positionValue=position_value,
            positionPct=position_pct,
            riskPerTradePct=risk_per_trade_pct * 100,  # Convert to percentage
            method=method_name,
            riskPerShare=float(risk_per_share),
            maxSharesFixedRisk=max_shares_fixed_risk,
            maxSharesPosition=max_shares_position,
            kellyFraction=None,
            recommendedFraction=None,
            maxDrawdownRisk=None,
            winRate=None,
            avgWin=None,
            avgLoss=None
        )
    
    def resolve_calculateDynamicStop(
        self, info,
        entryPrice: float,
        atr: float,
        atrMultiplier: float = None,
        supportLevel: float = None,
        resistanceLevel: float = None,
        signalType: str = None
    ):
        """Calculate dynamic stop loss"""
        # Default ATR multiplier: 2.0
        atr_multiplier = atrMultiplier if atrMultiplier else 2.0
        
        # Determine if long or short based on signal type
        is_long = signalType != "SHORT" if signalType else True
        
        # Calculate ATR-based stop
        atr_stop_distance = atr * atr_multiplier
        if is_long:
            atr_stop = entryPrice - atr_stop_distance
        else:
            atr_stop = entryPrice + atr_stop_distance
        
        # Calculate support/resistance stop
        sr_stop = None
        if is_long and supportLevel:
            sr_stop = supportLevel * 0.995  # 0.5% below support
        elif not is_long and resistanceLevel:
            sr_stop = resistanceLevel * 1.005  # 0.5% above resistance
        
        # Calculate percentage-based stop (2% default)
        pct_stop_distance = entryPrice * 0.02
        if is_long:
            pct_stop = entryPrice - pct_stop_distance
        else:
            pct_stop = entryPrice + pct_stop_distance
        
        # Choose the best stop (closest to entry for long, farthest for short)
        stops = [s for s in [atr_stop, sr_stop, pct_stop] if s is not None]
        if is_long:
            stop_price = max(stops)  # Highest stop (closest to entry)
        else:
            stop_price = min(stops)  # Lowest stop (closest to entry)
        
        stop_distance = abs(entryPrice - stop_price)
        risk_percentage = (stop_distance / entryPrice) * 100 if entryPrice > 0 else 0.0
        
        # Determine method
        if sr_stop and abs(stop_price - sr_stop) < abs(stop_price - atr_stop):
            method = "support_resistance"
        elif abs(stop_price - atr_stop) < abs(stop_price - pct_stop):
            method = "atr"
        else:
            method = "percentage"
        
        return DynamicStopType(
            stopPrice=stop_price,
            stopDistance=stop_distance,
            riskPercentage=risk_percentage,
            method=method,
            atrStop=atr_stop,
            srStop=sr_stop if sr_stop else None,
            pctStop=pct_stop
        )
    
    def resolve_calculateTargetPrice(
        self, info,
        entryPrice: float,
        stopPrice: float,
        riskRewardRatio: float = None,
        atr: float = None,
        resistanceLevel: float = None,
        supportLevel: float = None,
        signalType: str = None
    ):
        """Calculate target price"""
        # Calculate risk distance
        risk_distance = abs(entryPrice - stopPrice)
        
        # Default risk/reward ratio: 2:1
        rr_ratio = riskRewardRatio if riskRewardRatio else 2.0
        
        # Determine if long or short
        is_long = signalType != "SHORT" if signalType else entryPrice > stopPrice
        
        # Calculate R:R-based target
        reward_distance = risk_distance * rr_ratio
        if is_long:
            rr_target = entryPrice + reward_distance
        else:
            rr_target = entryPrice - reward_distance
        
        # Calculate ATR-based target (if ATR provided)
        atr_target = None
        if atr:
            atr_target_distance = atr * 2.0  # 2x ATR
            if is_long:
                atr_target = entryPrice + atr_target_distance
            else:
                atr_target = entryPrice - atr_target_distance
        
        # Calculate support/resistance target
        sr_target = None
        if is_long and resistanceLevel:
            sr_target = resistanceLevel * 0.995  # Just below resistance
        elif not is_long and supportLevel:
            sr_target = supportLevel * 1.005  # Just above support
        
        # Choose the best target
        targets = [t for t in [rr_target, atr_target, sr_target] if t is not None]
        if is_long:
            target_price = min(targets)  # Lowest target (most conservative)
        else:
            target_price = max(targets)  # Highest target (most conservative)
        
        # Calculate final reward distance
        final_reward_distance = abs(target_price - entryPrice)
        final_rr_ratio = final_reward_distance / risk_distance if risk_distance > 0 else 0.0
        
        # Determine method
        if sr_target and abs(target_price - sr_target) < abs(target_price - rr_target):
            method = "support_resistance"
        elif atr_target and abs(target_price - atr_target) < abs(target_price - rr_target):
            method = "atr"
        else:
            method = "risk_reward"
        
        return TargetPriceType(
            targetPrice=target_price,
            rewardDistance=final_reward_distance,
            riskRewardRatio=final_rr_ratio,
            method=method,
            rrTarget=rr_target,
            atrTarget=atr_target if atr_target else None,
            srTarget=sr_target if sr_target else None
        )

