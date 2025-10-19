"""
Options Copilot Engine
Core logic for AI-powered options strategy recommendations with risk rails
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import math

def _safe_int(x, default=0):
    try: return int(x)
    except: return default

def _safe_float(x, default=0.0):
    try: return float(x)
    except: return default

from .monitoring import logger
from .real_data_service import get_real_data_service

class OptionsCopilotEngine:
    """AI-powered options strategy recommendation engine"""
    
    def __init__(self):
        self.real_data_service = get_real_data_service()
        self.strategies_db = {}  # In-memory storage for development
        self.market_data_cache = {}  # Cache for market data
        
        # Initialize with default strategies
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize with default options strategies"""
        default_strategies = [
            {
                "id": "bull_call_spread",
                "name": "Bull Call Spread",
                "type": "bull_call_spread",
                "description": "Limited risk, limited reward bullish strategy",
                "risk_level": "medium",
                "time_horizon": "short",
                "market_conditions": ["bullish", "neutral"],
                "max_profit": "strike_spread - net_debit",
                "max_loss": "net_debit",
                "breakeven": "lower_strike + net_debit"
            },
            {
                "id": "bear_put_spread",
                "name": "Bear Put Spread",
                "type": "bear_put_spread",
                "description": "Limited risk, limited reward bearish strategy",
                "risk_level": "medium",
                "time_horizon": "short",
                "market_conditions": ["bearish", "neutral"],
                "max_profit": "strike_spread - net_debit",
                "max_loss": "net_debit",
                "breakeven": "higher_strike - net_debit"
            },
            {
                "id": "iron_condor",
                "name": "Iron Condor",
                "type": "iron_condor",
                "description": "Neutral strategy with limited risk and reward",
                "risk_level": "low",
                "time_horizon": "medium",
                "market_conditions": ["neutral", "low_volatility"],
                "max_profit": "net_credit",
                "max_loss": "strike_spread - net_credit",
                "breakeven": "two_breakeven_points"
            },
            {
                "id": "straddle",
                "name": "Long Straddle",
                "type": "straddle",
                "description": "Profits from large moves in either direction",
                "risk_level": "high",
                "time_horizon": "short",
                "market_conditions": ["high_volatility", "earnings"],
                "max_profit": "unlimited",
                "max_loss": "total_premium",
                "breakeven": "strike ± total_premium"
            }
        ]
        
        for strategy in default_strategies:
            self.strategies_db[strategy["id"]] = strategy
    
    async def get_recommendations(self, request) -> Dict:
        """Get AI-powered options strategy recommendations"""
        try:
            symbol = request.symbol
            current_price = request.current_price
            risk_tolerance = request.risk_tolerance
            time_horizon = request.time_horizon
            max_risk = request.max_risk
            account_value = request.account_value
            market_outlook = request.market_outlook
            
            # Get market data
            market_data = await self._get_market_data(symbol)
            
            # Get options chain
            options_chain = await self._get_options_chain(symbol)
            
            # Analyze market conditions
            market_analysis = await self._analyze_market_conditions(symbol, market_data, options_chain)
            
            # Generate strategy recommendations
            recommended_strategies = await self._generate_strategy_recommendations(
                symbol, current_price, risk_tolerance, time_horizon, 
                max_risk, account_value, market_outlook, market_analysis, options_chain
            )
            
            # Calculate risk assessment
            risk_assessment = await self._calculate_risk_assessment(
                recommended_strategies, risk_tolerance, account_value
            )
            
            response = {
                "symbol": symbol,
                "current_price": current_price,
                "market_outlook": market_outlook,
                "recommended_strategies": recommended_strategies,
                "risk_assessment": risk_assessment,
                "market_analysis": market_analysis
            }
            
            logger.info(f"Generated {len(recommended_strategies)} recommendations for {symbol}")
            return response
            
        except Exception as e:
            logger.error(f"Error getting recommendations for {request.symbol}: {e}")
            raise
    
    async def get_options_chain(self, symbol: str, expiration_date: Optional[str] = None) -> Dict:
        """Get options chain data for a symbol"""
        try:
            # In production, this would call your options data provider
            # For now, return mock data
            mock_chain = {
                "symbol": symbol,
                "underlying_price": 150.0,
                "expiration_dates": ["2024-01-19", "2024-02-16", "2024-03-15"],
                "calls": [
                    {
                        "strike": 145,
                        "bid": 8.50,
                        "ask": 8.75,
                        "volume": 1500,
                        "open_interest": 5000,
                        "implied_volatility": 0.25,
                        "delta": 0.65,
                        "gamma": 0.02,
                        "theta": -0.15,
                        "vega": 0.30
                    },
                    {
                        "strike": 150,
                        "bid": 5.25,
                        "ask": 5.50,
                        "volume": 2000,
                        "open_interest": 8000,
                        "implied_volatility": 0.24,
                        "delta": 0.50,
                        "gamma": 0.02,
                        "theta": -0.20,
                        "vega": 0.35
                    },
                    {
                        "strike": 155,
                        "bid": 2.75,
                        "ask": 3.00,
                        "volume": 1200,
                        "open_interest": 3000,
                        "implied_volatility": 0.23,
                        "delta": 0.35,
                        "gamma": 0.02,
                        "theta": -0.15,
                        "vega": 0.30
                    }
                ],
                "puts": [
                    {
                        "strike": 145,
                        "bid": 2.25,
                        "ask": 2.50,
                        "volume": 800,
                        "open_interest": 2000,
                        "implied_volatility": 0.26,
                        "delta": -0.35,
                        "gamma": 0.02,
                        "theta": -0.15,
                        "vega": 0.30
                    },
                    {
                        "strike": 150,
                        "bid": 4.75,
                        "ask": 5.00,
                        "volume": 1500,
                        "open_interest": 4000,
                        "implied_volatility": 0.25,
                        "delta": -0.50,
                        "gamma": 0.02,
                        "theta": -0.20,
                        "vega": 0.35
                    },
                    {
                        "strike": 155,
                        "bid": 8.25,
                        "ask": 8.50,
                        "volume": 1000,
                        "open_interest": 2500,
                        "implied_volatility": 0.24,
                        "delta": -0.65,
                        "gamma": 0.02,
                        "theta": -0.15,
                        "vega": 0.30
                    }
                ]
            }
            
            logger.info(f"Retrieved options chain for {symbol}")
            return mock_chain
            
        except Exception as e:
            logger.error(f"Error getting options chain for {symbol}: {e}")
            raise
    
    async def calculate_strategy_pnl(self, strategy: Dict, price_scenarios: List[float]) -> Dict:
        """Calculate strategy P&L for different price scenarios"""
        try:
            pnl_results = []
            
            for price in price_scenarios:
                pnl = await self._calculate_strategy_pnl_at_price(strategy, price)
                pnl_results.append({
                    "price": price,
                    "pnl": pnl,
                    "return_percent": (pnl / strategy["setup"]["total_cost"]) * 100 if strategy["setup"]["total_cost"] > 0 else 0
                })
            
            logger.info(f"Calculated P&L for {len(price_scenarios)} scenarios")
            return {"scenarios": pnl_results}
            
        except Exception as e:
            logger.error(f"Error calculating strategy P&L: {e}")
            raise
    
    async def get_risk_analysis(self, strategy: Dict) -> Dict:
        """Get detailed risk analysis for a strategy"""
        try:
            risk_factors = []
            mitigation_strategies = []
            
            # Analyze different risk factors
            if strategy["type"] in ["straddle", "strangle"]:
                risk_factors.append({
                    "factor": "Time Decay",
                    "impact": "high",
                    "description": "Options lose value as expiration approaches",
                    "mitigation": "Close position before last week of expiration"
                })
            
            if strategy["greeks"]["vega"] > 0.5:
                risk_factors.append({
                    "factor": "Volatility Risk",
                    "impact": "high",
                    "description": "High sensitivity to volatility changes",
                    "mitigation": "Monitor IV and close if it drops significantly"
                })
            
            if strategy["setup"]["total_cost"] > 1000:
                risk_factors.append({
                    "factor": "Capital Risk",
                    "impact": "medium",
                    "description": "Large capital commitment",
                    "mitigation": "Ensure position size is appropriate for account"
                })
            
            # Calculate overall risk score
            risk_score = 0.5  # Base score
            for factor in risk_factors:
                if factor["impact"] == "high":
                    risk_score += 0.2
                elif factor["impact"] == "medium":
                    risk_score += 0.1
            
            risk_score = min(1.0, risk_score)
            
            overall_risk = "low" if risk_score < 0.4 else "medium" if risk_score < 0.7 else "high"
            
            risk_analysis = {
                "overall_risk": overall_risk,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "recommendations": [
                    "Start with small position size",
                    "Set stop loss at 50% of max loss",
                    "Monitor position daily",
                    "Close before expiration if profitable"
                ]
            }
            
            logger.info(f"Generated risk analysis for strategy {strategy['id']}")
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Error getting risk analysis: {e}")
            raise
    
    async def get_available_strategies(self) -> List[Dict]:
        """Get list of available options strategies"""
        try:
            strategies = list(self.strategies_db.values())
            logger.info(f"Retrieved {len(strategies)} available strategies")
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting available strategies: {e}")
            raise
    
    async def get_market_data(self, symbol: str) -> Dict:
        """Get comprehensive market data for options analysis"""
        try:
            # Get stock data
            stock_data = await self.real_data_service.get_stock_data(symbol)
            
            # Get additional market data
            market_data = {
                "symbol": symbol,
                "current_price": stock_data.get("price", 0),
                "change": stock_data.get("change", 0),
                "change_percent": stock_data.get("change_percent", 0),
                "volume": stock_data.get("volume", 0),
                "market_cap": stock_data.get("market_cap", 0),
                "pe_ratio": stock_data.get("pe_ratio", 0),
                "beta": stock_data.get("beta", 1.0),
                "volatility": 0.25,  # Mock volatility
                "dividend_yield": stock_data.get("dividend_yield", 0),
                "earnings_date": stock_data.get("earnings_date"),
                "analyst_rating": stock_data.get("analyst_rating", "hold"),
                "price_target": stock_data.get("price_target", 0)
            }
            
            logger.info(f"Retrieved market data for {symbol}")
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            raise
    
    async def backtest_strategy(self, strategy: Dict, symbol: str, start_date: str, end_date: str) -> Dict:
        """Backtest a strategy against historical data"""
        try:
            # Mock backtest results
            backtest_results = {
                "strategy_id": strategy["id"],
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "total_trades": 25,
                "winning_trades": 18,
                "losing_trades": 7,
                "win_rate": 0.72,
                "total_return": 0.15,
                "max_drawdown": 0.08,
                "sharpe_ratio": 1.2,
                "average_hold_time": 5.2,
                "best_trade": 0.12,
                "worst_trade": -0.06,
                "monthly_returns": [0.02, 0.03, -0.01, 0.04, 0.02, 0.01, 0.03, 0.01]
            }
            
            logger.info(f"Backtested strategy {strategy['id']} for {symbol}")
            return backtest_results
            
        except Exception as e:
            logger.error(f"Error backtesting strategy: {e}")
            raise
    
    async def calculate_greeks(self, symbol: str, strike: float, expiration: str, 
                             option_type: str, current_price: float, 
                             volatility: float, risk_free_rate: float = 0.05) -> Dict:
        """Calculate Greeks for a specific option"""
        try:
            # Mock Greeks calculation
            # In production, this would use Black-Scholes or similar model
            greeks = {
                "symbol": symbol,
                "strike": strike,
                "expiration": expiration,
                "option_type": option_type,
                "current_price": current_price,
                "volatility": volatility,
                "risk_free_rate": risk_free_rate,
                "delta": 0.5 if option_type == "call" else -0.5,
                "gamma": 0.02,
                "theta": -0.15,
                "vega": 0.30,
                "rho": 0.05
            }
            
            logger.info(f"Calculated Greeks for {symbol} {option_type} {strike}")
            return greeks
            
        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            raise
    
    async def get_volatility_analysis(self, symbol: str) -> Dict:
        """Get comprehensive volatility analysis for a symbol"""
        try:
            # Mock volatility analysis
            vol_analysis = {
                "symbol": symbol,
                "current_iv": 0.25,
                "historical_iv": 0.20,
                "iv_percentile": 0.75,
                "iv_rank": 0.8,
                "trend": "increasing",
                "volatility_forecast": {
                    "next_week": 0.26,
                    "next_month": 0.24,
                    "next_quarter": 0.22
                },
                "volatility_events": [
                    {"date": "2024-01-15", "event": "Earnings", "impact": "high"},
                    {"date": "2024-02-01", "event": "Fed Meeting", "impact": "medium"}
                ]
            }
            
            logger.info(f"Retrieved volatility analysis for {symbol}")
            return vol_analysis
            
        except Exception as e:
            logger.error(f"Error getting volatility analysis for {symbol}: {e}")
            raise
    
    async def _get_market_data(self, symbol: str) -> Dict:
        """Get market data for analysis"""
        try:
            if symbol in self.market_data_cache:
                return self.market_data_cache[symbol]
            
            market_data = await self.get_market_data(symbol)
            self.market_data_cache[symbol] = market_data
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return {}
    
    async def _analyze_market_conditions(self, symbol: str, market_data: Dict, options_chain: Dict) -> Dict:
        """Analyze market conditions for strategy selection"""
        try:
            # Volatility analysis
            volatility_analysis = {
                "current_iv": 0.25,
                "historical_iv": 0.20,
                "iv_percentile": 0.75,
                "iv_rank": 0.8,
                "trend": "increasing"
            }
            
            # Sentiment analysis
            sentiment_analysis = {
                "overall": "bullish",
                "score": 0.7,
                "sources": [
                    {"source": "Analyst Ratings", "sentiment": "bullish", "confidence": 0.8},
                    {"source": "Social Media", "sentiment": "bullish", "confidence": 0.6},
                    {"source": "Options Flow", "sentiment": "bullish", "confidence": 0.75}
                ]
            }
            
            # Technical analysis
            technical_analysis = {
                "trend": "bullish",
                "support": market_data.get("current_price", 0) * 0.95,
                "resistance": market_data.get("current_price", 0) * 1.05,
                "key_levels": [market_data.get("current_price", 0) * 0.95, market_data.get("current_price", 0) * 1.05],
                "indicators": [
                    {"name": "RSI", "value": 65, "signal": "bullish", "strength": 0.7},
                    {"name": "MACD", "value": 0.5, "signal": "bullish", "strength": 0.8}
                ]
            }
            
            # Fundamental analysis
            fundamental_analysis = {
                "rating": "buy",
                "price_target": market_data.get("price_target", 0),
                "upside": 0.1,
                "key_metrics": [
                    {"metric": "P/E Ratio", "value": 25, "benchmark": 20, "signal": "neutral"},
                    {"metric": "Revenue Growth", "value": 0.15, "benchmark": 0.10, "signal": "positive"}
                ]
            }
            
            return {
                "volatility": volatility_analysis,
                "sentiment": sentiment_analysis,
                "technical": technical_analysis,
                "fundamental": fundamental_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {}
    
    async def _generate_strategy_recommendations(self, symbol: str, current_price: float, 
                                               risk_tolerance: str, time_horizon: str,
                                               max_risk: float, account_value: float,
                                               market_outlook: str, market_analysis: Dict,
                                               options_chain: Dict) -> List[Dict]:
        """Generate strategy recommendations based on parameters"""
        try:
            recommendations = []
            
            # Select appropriate strategies based on market outlook and risk tolerance
            if market_outlook == "bullish" and risk_tolerance in ["medium", "high"]:
                # Bull Call Spread
                recommendation = await self._create_bull_call_spread(
                    symbol, current_price, max_risk, options_chain
                )
                recommendations.append(recommendation)
            
            if market_outlook == "bearish" and risk_tolerance in ["medium", "high"]:
                # Bear Put Spread
                recommendation = await self._create_bear_put_spread(
                    symbol, current_price, max_risk, options_chain
                )
                recommendations.append(recommendation)
            
            if market_outlook == "neutral" and risk_tolerance == "low":
                # Iron Condor
                recommendation = await self._create_iron_condor(
                    symbol, current_price, max_risk, options_chain
                )
                recommendations.append(recommendation)
            
            if market_analysis.get("volatility", {}).get("iv_percentile", 0) > 0.7 and risk_tolerance == "high":
                # Long Straddle
                recommendation = await self._create_long_straddle(
                    symbol, current_price, max_risk, options_chain
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating strategy recommendations: {e}")
            return []
    
    async def _create_bull_call_spread(self, symbol: str, current_price: float, 
                                     max_risk: float, options_chain: Dict) -> Dict:
        """Create a bull call spread recommendation"""
        try:
            # Find appropriate strikes
            lower_strike = current_price * 0.98
            upper_strike = current_price * 1.02
            
            # Calculate premiums (mock)
            lower_call_premium = 5.50
            upper_call_premium = 3.00
            net_debit = lower_call_premium - upper_call_premium
            
            # Calculate position size
            max_contracts = int(max_risk / (net_debit * 100))
            position_size = min(max_contracts, 10)  # Cap at 10 contracts
            
            strategy = {
                "id": str(uuid.uuid4()),
                "name": "Bull Call Spread",
                "type": "bull_call_spread",
                "description": "Limited risk, limited reward bullish strategy",
                "expected_payoff": {
                    "max_profit": (upper_strike - lower_strike - net_debit) * 100 * position_size,
                    "max_loss": net_debit * 100 * position_size,
                    "breakeven_points": [lower_strike + net_debit],
                    "profit_probability": 0.65,
                    "expected_value": 45 * position_size,
                    "time_decay": -0.5 * position_size
                },
                "greeks": {
                    "delta": 0.35,
                    "gamma": 0.02,
                    "theta": -0.5,
                    "vega": 0.8,
                    "rho": 0.1
                },
                "slippage_estimate": {
                    "bid_ask_spread": 0.05,
                    "market_impact": 0.02,
                    "total_slippage": 0.07,
                    "liquidity_score": 0.85
                },
                "risk_explanation": {
                    "plain_english": "This strategy profits if the stock goes up moderately. Maximum loss is limited to the net premium paid.",
                    "risk_factors": ["Time decay", "Volatility crush", "Early assignment risk"],
                    "mitigation_strategies": ["Close before expiration", "Monitor volatility", "Set stop losses"],
                    "worst_case_scenario": "Stock drops below lower strike, lose full premium",
                    "probability_of_loss": 0.35
                },
                "setup": {
                    "legs": [
                        {
                            "action": "buy",
                            "option_type": "call",
                            "quantity": position_size,
                            "strike_price": lower_strike,
                            "expiration_date": "2024-01-19",
                            "premium": lower_call_premium,
                            "greeks": {"delta": 0.5, "gamma": 0.02, "theta": -0.3, "vega": 0.4, "rho": 0.05}
                        },
                        {
                            "action": "sell",
                            "option_type": "call",
                            "quantity": position_size,
                            "strike_price": upper_strike,
                            "expiration_date": "2024-01-19",
                            "premium": upper_call_premium,
                            "greeks": {"delta": -0.15, "gamma": -0.01, "theta": 0.2, "vega": -0.2, "rho": -0.05}
                        }
                    ],
                    "total_cost": net_debit * 100 * position_size,
                    "margin_requirement": 0,
                    "expiration_date": "2024-01-19",
                    "strike_prices": [lower_strike, upper_strike]
                },
                "risk_rails": {
                    "max_position_size": 0.05,
                    "stop_loss": 0.5,
                    "take_profit": 0.75,
                    "time_stop": 7,
                    "volatility_stop": 0.3,
                    "max_drawdown": 0.2
                },
                "confidence": 0.75,
                "reasoning": "Strong bullish momentum with good risk/reward ratio. Volatility is elevated, making this spread attractive."
            }
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error creating bull call spread: {e}")
            return {}
    
    async def _create_bear_put_spread(self, symbol: str, current_price: float, 
                                    max_risk: float, options_chain: Dict) -> Dict:
        """Create a bear put spread recommendation"""
        # Similar implementation to bull call spread but with puts
        return {}
    
    async def _create_iron_condor(self, symbol: str, current_price: float, 
                                max_risk: float, options_chain: Dict) -> Dict:
        """Create an iron condor recommendation"""
        # Implementation for iron condor strategy
        return {}
    
    async def _create_long_straddle(self, symbol: str, current_price: float, 
                                  max_risk: float, options_chain: Dict) -> Dict:
        """Create a long straddle recommendation"""
        # Implementation for long straddle strategy
        return {}
    
    async def _calculate_risk_assessment(self, strategies: List[Dict], 
                                       risk_tolerance: str, account_value: float) -> Dict:
        """Calculate overall risk assessment"""
        try:
            if not strategies:
                return {
                    "overall_risk": "low",
                    "risk_score": 0.0,
                    "risk_factors": [],
                    "recommendations": ["No strategies recommended"]
                }
            
            # Calculate weighted risk score
            total_risk = 0
            risk_factors = []
            
            for strategy in strategies:
                if strategy.get("type") in ["straddle", "strangle"]:
                    total_risk += 0.8
                    risk_factors.append({
                        "factor": "High Volatility Strategy",
                        "impact": "high",
                        "description": "Strategy profits from large price moves",
                        "mitigation": "Monitor position closely and set stop losses"
                    })
                elif strategy.get("type") in ["bull_call_spread", "bear_put_spread"]:
                    total_risk += 0.5
                else:
                    total_risk += 0.3
            
            avg_risk = total_risk / len(strategies)
            
            overall_risk = "low" if avg_risk < 0.4 else "medium" if avg_risk < 0.7 else "high"
            
            recommendations = [
                "Start with small position sizes",
                "Set stop losses for all positions",
                "Monitor positions daily",
                "Close profitable positions early"
            ]
            
            return {
                "overall_risk": overall_risk,
                "risk_score": avg_risk,
                "risk_factors": risk_factors,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk assessment: {e}")
            return {}
    
    async def _calculate_strategy_pnl_at_price(self, strategy: Dict, price: float) -> float:
        """Calculate P&L for a strategy at a specific price"""
        try:
            # Simplified P&L calculation
            # In production, this would be much more sophisticated
            if strategy["type"] == "bull_call_spread":
                setup = strategy["setup"]
                lower_strike = setup["strike_prices"][0]
                upper_strike = setup["strike_prices"][1]
                net_debit = setup["total_cost"] / (setup["legs"][0]["quantity"] * 100)
                
                if price <= lower_strike:
                    return -setup["total_cost"]  # Max loss
                elif price >= upper_strike:
                    return (upper_strike - lower_strike - net_debit) * setup["legs"][0]["quantity"] * 100  # Max profit
                else:
                    return (price - lower_strike - net_debit) * setup["legs"][0]["quantity"] * 100  # Partial profit
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating strategy P&L: {e}")
            return 0.0
    
    async def get_health_status(self) -> Dict:
        """Get health status of the Options Copilot engine"""
        try:
            return {
                "strategies_available": len(self.strategies_db),
                "market_data_cache_size": len(self.market_data_cache),
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"status": "unhealthy", "error": str(e)}
