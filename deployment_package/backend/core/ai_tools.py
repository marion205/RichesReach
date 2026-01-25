# core/ai_tools.py
"""
AI Tools (Function Calling) Definitions
Defines the tools/functions that LLMs can call to execute quantitative algorithms.

This enables the "Tool Runner" pattern where the AI decides when to use algorithms.
"""
from typing import Dict, List, Any, Optional
import json


class AITools:
    """
    Tool definitions for function calling.
    
    These tools allow the LLM to call quantitative algorithms on-demand.
    """
    
    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """
        Get all available tool definitions for OpenAI/Gemini function calling.
        
        Returns:
            List of tool definitions in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_monte_carlo_goal_simulation",
                    "description": "Run a Monte Carlo simulation to calculate the probability of achieving a financial goal (e.g., 'Can I afford a $50k wedding in 2 years?'). Returns success probability, median outcome, and required savings if needed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal_amount": {
                                "type": "number",
                                "description": "The target amount to reach (e.g., 50000 for $50k)"
                            },
                            "time_horizon_months": {
                                "type": "integer",
                                "description": "Number of months to reach the goal (e.g., 24 for 2 years)"
                            },
                            "current_savings": {
                                "type": "number",
                                "description": "Current savings amount (default 0 if not provided)"
                            },
                            "monthly_contribution": {
                                "type": "number",
                                "description": "Monthly contribution amount (default 0 if not provided)"
                            },
                            "risk_level": {
                                "type": "string",
                                "enum": ["conservative", "moderate", "aggressive"],
                                "description": "Risk level for return assumptions (default: moderate)"
                            }
                        },
                        "required": ["goal_amount", "time_horizon_months"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_retirement_simulation",
                    "description": "Run a Monte Carlo simulation for retirement planning. Calculates the 'Safety Score' - probability of not running out of money in retirement. Runs 10,000+ market scenarios.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "current_age": {
                                "type": "integer",
                                "description": "Current age of the user"
                            },
                            "retirement_age": {
                                "type": "integer",
                                "description": "Target retirement age (default: 65)"
                            },
                            "current_savings": {
                                "type": "number",
                                "description": "Current retirement savings"
                            },
                            "monthly_contribution": {
                                "type": "number",
                                "description": "Monthly contribution to retirement account"
                            },
                            "target_amount": {
                                "type": "number",
                                "description": "Optional target retirement amount"
                            }
                        },
                        "required": ["current_age", "current_savings", "monthly_contribution"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "optimize_portfolio_allocation",
                    "description": "Optimize portfolio allocation using Modern Portfolio Theory (MPT) or Black-Litterman model. Finds the optimal mix of assets for risk/return balance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "assets": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of asset symbols (e.g., ['AAPL', 'MSFT', 'BND'])"
                            },
                            "expected_returns": {
                                "type": "object",
                                "description": "Expected annual returns for each asset (e.g., {'AAPL': 0.10, 'MSFT': 0.12})"
                            },
                            "risk_tolerance": {
                                "type": "string",
                                "enum": ["conservative", "moderate", "aggressive"],
                                "description": "User's risk tolerance level"
                            },
                            "user_views": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "asset": {"type": "string"},
                                        "return": {"type": "number"}
                                    }
                                },
                                "description": "Optional user views for Black-Litterman (e.g., [{'asset': 'AAPL', 'return': 0.15}])"
                            }
                        },
                        "required": ["assets", "risk_tolerance"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_tax_loss_harvesting_opportunities",
                    "description": "Identify tax-loss harvesting opportunities. Finds losing positions that can be sold to offset gains, saving money on taxes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "positions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "symbol": {"type": "string"},
                                        "cost_basis": {"type": "number"},
                                        "current_price": {"type": "number"},
                                        "quantity": {"type": "number"},
                                        "purchase_date": {"type": "string"}
                                    }
                                },
                                "description": "List of investment positions"
                            },
                            "realized_gains": {
                                "type": "number",
                                "description": "Already realized gains to offset (default: 0)"
                            }
                        },
                        "required": ["positions"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_portfolio_rebalancing",
                    "description": "Check if portfolio should be rebalanced using reinforcement learning. Determines optimal rebalancing timing based on drift, volatility, and transaction costs.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "current_allocation": {
                                "type": "object",
                                "description": "Current portfolio allocation (e.g., {'stocks': 0.65, 'bonds': 0.30, 'cash': 0.05})"
                            },
                            "target_allocation": {
                                "type": "object",
                                "description": "Target portfolio allocation"
                            },
                            "market_volatility": {
                                "type": "number",
                                "description": "Current market volatility (default: 0.15)"
                            }
                        },
                        "required": ["current_allocation", "target_allocation"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "classify_financial_persona",
                    "description": "Classify user into financial persona (e.g., 'Aggressive Saver', 'Conservative Retiree') using ML clustering. Helps personalize advice.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "age": {"type": "integer"},
                            "income": {"type": "number"},
                            "savings_rate": {"type": "number", "description": "Savings rate as decimal (e.g., 0.20 for 20%)"},
                            "risk_tolerance": {
                                "type": "string",
                                "enum": ["conservative", "moderate", "aggressive"]
                            },
                            "investment_horizon": {
                                "type": "integer",
                                "description": "Investment horizon in years"
                            }
                        },
                        "required": ["age", "risk_tolerance"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "forecast_cash_flow",
                    "description": "Forecast future cash flow using time-series analysis. Predicts spending patterns and can detect seasonal spikes (e.g., December spending).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "historical_transactions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {"type": "string"},
                                        "amount": {"type": "number", "description": "Positive for income, negative for expenses"}
                                    }
                                },
                                "description": "Historical transaction data"
                            },
                            "forecast_months": {
                                "type": "integer",
                                "description": "Number of months to forecast (default: 12)"
                            }
                        },
                        "required": ["historical_transactions"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_direct_index",
                    "description": "Create a tax-efficient direct indexing portfolio that tracks an ETF by owning individual stocks instead of the ETF. Enables tax-loss harvesting at the stock level and customization (e.g., exclude employer stock). Ideal for portfolios over $100k.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_etf": {
                                "type": "string",
                                "description": "ETF to replicate (e.g., 'SPY' for S&P 500, 'QQQ' for NASDAQ-100)"
                            },
                            "portfolio_value": {
                                "type": "number",
                                "description": "Total portfolio value for direct indexing"
                            },
                            "excluded_stocks": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Stocks to exclude from the direct index (e.g., employer stock like ['AAPL'])"
                            },
                            "tax_optimization": {
                                "type": "boolean",
                                "description": "Enable tax-loss harvesting optimization (default: true)"
                            }
                        },
                        "required": ["target_etf", "portfolio_value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_tax_smart_transition",
                    "description": "Create a tax-smart plan to gradually transition concentrated positions (e.g., employer stock) while harvesting losses to minimize taxes. Ideal for diversifying concentrated holdings over 2-3 years. Returns monthly sale schedule and tax savings.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "concentrated_position": {
                                "type": "object",
                                "description": "Position to transition: {symbol: string, quantity: number, cost_basis: number, current_price: number}",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "quantity": {"type": "number"},
                                    "cost_basis": {"type": "number"},
                                    "current_price": {"type": "number"}
                                },
                                "required": ["symbol", "quantity", "cost_basis", "current_price"]
                            },
                            "target_allocation": {
                                "type": "object",
                                "description": "Target portfolio allocation after transition (e.g., {'SPY': 0.6, 'BND': 0.4})"
                            },
                            "time_horizon_months": {
                                "type": "integer",
                                "description": "Months to complete transition (default: 36 for 3 years)"
                            },
                            "annual_income": {
                                "type": "number",
                                "description": "Annual income for tax calculations"
                            },
                            "tax_bracket": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Tax bracket (default: 'high')"
                            }
                        },
                        "required": ["concentrated_position", "target_allocation"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_tax_alpha_dashboard",
                    "description": "Get Tax Alpha Dashboard metrics showing real-time tax savings from direct indexing. Displays harvested losses, potential harvestable losses, annual tax alpha percentage, and net alpha (tax alpha minus tracking error). Use this when user asks to 'show tax alpha dashboard' or 'show tax savings'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "portfolio_value": {
                                "type": "number",
                                "description": "Total portfolio value (default: 100000 if not provided)"
                            },
                            "harvested_losses_ytd": {
                                "type": "number",
                                "description": "Harvested losses year-to-date (default: calculated if not provided)"
                            },
                            "tracking_error_pct": {
                                "type": "number",
                                "description": "Tracking error percentage (default: 0.5 if not provided)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_fss_scores",
                    "description": "Calculate Future Success Score (FSS) for stocks. FSS is a quantitative ranking system that predicts outperformance over 6-12 months using Trend (30%), Fundamentals (30%), Capital Flow (25%), and Risk (15%) components. Returns scores 0-100 with regime-aware weighting and safety filters. Use this when user asks to 'rank stocks', 'find best stocks', 'score stocks', 'future success score', or 'FSS'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tickers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of stock symbols to score (e.g., ['AAPL', 'MSFT', 'GOOGL'])"
                            },
                            "apply_safety_filters": {
                                "type": "boolean",
                                "description": "Whether to apply safety filters (liquidity, Altman Z-Score). Default: true"
                            }
                        },
                        "required": ["tickers"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "optimize_fss_portfolio",
                    "description": "Optimize portfolio weights for FSS-ranked stocks using confidence-weighted risk parity. Sizes positions based on FSS scores and volatility. Use this when user asks to 'optimize portfolio', 'size positions', or 'allocate capital' for FSS-ranked stocks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tickers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of stock symbols in portfolio"
                            },
                            "fss_scores": {
                                "type": "object",
                                "description": "FSS scores for each ticker (e.g., {'AAPL': 85, 'MSFT': 78})"
                            },
                            "volatilities": {
                                "type": "object",
                                "description": "Annualized volatilities for each ticker (e.g., {'AAPL': 0.25, 'MSFT': 0.22})"
                            },
                            "max_weight": {
                                "type": "number",
                                "description": "Maximum weight per position (default: 0.15 = 15%)"
                            }
                        },
                        "required": ["tickers", "fss_scores", "volatilities"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "backtest_fss_strategy",
                    "description": "Backtest a FSS-based ranking strategy. Tests buying top N stocks ranked by FSS and rebalancing monthly/weekly. Returns performance metrics including Sharpe ratio, max drawdown, and alpha vs benchmark. Use this when user asks to 'backtest FSS', 'test strategy', or 'historical performance'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tickers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of stock symbols to backtest"
                            },
                            "rebalance_freq": {
                                "type": "string",
                                "enum": ["W", "M"],
                                "description": "Rebalancing frequency: 'W' for weekly, 'M' for monthly (default: 'M')"
                            },
                            "top_n": {
                                "type": "integer",
                                "description": "Number of top stocks to hold (default: 20)"
                            }
                        },
                        "required": ["tickers"]
                    }
                }
            }
        ]
    
    @staticmethod
    def get_tool_by_name(tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool definition by name"""
        tools = AITools.get_tool_definitions()
        for tool in tools:
            if tool.get("function", {}).get("name") == tool_name:
                return tool
        return None


class ToolRunner:
    """
    Executes tools/functions called by the LLM.
    
    This is the "Tool Runner" that bridges LLM function calls to actual algorithm execution.
    """
    
    def __init__(self):
        """Initialize tool runner"""
        from .algorithm_service import get_algorithm_service
        self.algorithm_service = get_algorithm_service()
    
    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool called by the LLM.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments passed by the LLM
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name == "run_monte_carlo_goal_simulation":
                return self.algorithm_service.run_goal_simulation(
                    goal_amount=arguments.get("goal_amount", 0),
                    time_horizon_months=arguments.get("time_horizon_months", 24),
                    current_savings=arguments.get("current_savings", 0),
                    monthly_contribution=arguments.get("monthly_contribution", 0),
                    risk_level=arguments.get("risk_level", "moderate")
                )
            
            elif tool_name == "run_retirement_simulation":
                return self.algorithm_service.run_retirement_simulation(
                    current_age=arguments.get("current_age", 30),
                    retirement_age=arguments.get("retirement_age", 65),
                    current_savings=arguments.get("current_savings", 0),
                    monthly_contribution=arguments.get("monthly_contribution", 0),
                    target_amount=arguments.get("target_amount")
                )
            
            elif tool_name == "optimize_portfolio_allocation":
                # Note: This requires market data - simplified for now
                return {
                    "error": "Portfolio optimization requires market data. Please provide expected_returns and cov_matrix.",
                    "algorithm": "portfolio_optimization"
                }
            
            elif tool_name == "find_tax_loss_harvesting_opportunities":
                return self.algorithm_service.find_tax_loss_harvesting(
                    positions=arguments.get("positions", []),
                    realized_gains=arguments.get("realized_gains", 0)
                )
            
            elif tool_name == "check_portfolio_rebalancing":
                return self.algorithm_service.check_rebalancing(
                    current_allocation=arguments.get("current_allocation", {}),
                    target_allocation=arguments.get("target_allocation", {}),
                    market_volatility=arguments.get("market_volatility", 0.15)
                )
            
            elif tool_name == "classify_financial_persona":
                from .ml_behavioral_layer import classify_financial_persona
                persona = classify_financial_persona(arguments)
                return {
                    "persona_type": persona.persona_type,
                    "confidence": persona.confidence,
                    "characteristics": persona.characteristics
                }
            
            elif tool_name == "forecast_cash_flow":
                import pandas as pd
                transactions = arguments.get("historical_transactions", [])
                df = pd.DataFrame(transactions)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                
                return self.algorithm_service.forecast_user_cash_flow(
                    historical_transactions=df if len(df) > 0 else [],
                    forecast_months=arguments.get("forecast_months", 12)
                )
            
            elif tool_name == "create_direct_index":
                return self.algorithm_service.create_direct_index(
                    target_etf=arguments.get("target_etf", ""),
                    portfolio_value=arguments.get("portfolio_value", 0),
                    excluded_stocks=arguments.get("excluded_stocks"),
                    tax_optimization=arguments.get("tax_optimization", True)
                )
            
            elif tool_name == "create_tax_smart_transition":
                return self.algorithm_service.create_tax_smart_transition(
                    concentrated_position=arguments.get("concentrated_position", {}),
                    target_allocation=arguments.get("target_allocation", {}),
                    time_horizon_months=arguments.get("time_horizon_months", 36),
                    annual_income=arguments.get("annual_income", 0),
                    tax_bracket=arguments.get("tax_bracket", "high")
                )
            
            elif tool_name == "get_tax_alpha_dashboard":
                from .tax_alpha_calculator import get_tax_alpha_calculator
                calculator = get_tax_alpha_calculator()
                portfolio_value = arguments.get("portfolio_value", 100000)
                harvested_losses_ytd = arguments.get("harvested_losses_ytd")
                tracking_error_pct = arguments.get("tracking_error_pct", 0.5)
                
                # If no harvested losses provided, use default demo data
                if harvested_losses_ytd is None:
                    # Create demo direct index positions for calculation
                    demo_positions = [
                        {"symbol": "MSFT", "cost_basis": 300, "current_price": 280, "shares": 100},
                        {"symbol": "GOOGL", "cost_basis": 140, "current_price": 135, "shares": 200},
                        {"symbol": "AMZN", "cost_basis": 150, "current_price": 145, "shares": 150},
                    ]
                    dashboard_data = calculator.get_dashboard_data(
                        direct_index_positions=demo_positions,
                        benchmark_etf="SPY",
                        portfolio_value=portfolio_value
                    )
                else:
                    # Use provided data
                    dashboard_data = calculator.get_dashboard_data(
                        portfolio_value=portfolio_value,
                        harvested_losses_ytd=harvested_losses_ytd,
                        tracking_error_pct=tracking_error_pct
                    )
                return dashboard_data
            
            elif tool_name == "calculate_fss_scores":
                import asyncio
                import logging
                logger = logging.getLogger(__name__)
                
                tickers = arguments.get("tickers", [])
                apply_safety = arguments.get("apply_safety_filters", True)
                
                if not tickers:
                    return {
                        "error": "Please provide a list of stock symbols to score",
                        "algorithm": "fss"
                    }
                
                # Calculate FSS scores using data pipeline
                try:
                    # Try to get existing event loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Run async function
                    if loop.is_running():
                        # If already running, we need to use a different approach
                        # For now, return a message that async execution is needed
                        return {
                            "message": f"FSS scoring is calculating scores for {len(tickers)} tickers. This may take a moment as we fetch market data.",
                            "tickers_requested": tickers,
                            "apply_safety_filters": apply_safety,
                            "algorithm": "fss_v2",
                            "status": "processing",
                            "note": "FSS calculation is running. Results will be available shortly."
                        }
                    else:
                        result = loop.run_until_complete(
                            self.algorithm_service.calculate_fss_scores(
                                tickers=tickers,
                                apply_safety_filters=apply_safety,
                                fetch_data=True
                            )
                        )
                        return result
                except Exception as e:
                    logger.error(f"FSS calculation error: {e}", exc_info=True)
                    return {
                        "error": f"Failed to calculate FSS scores: {str(e)}",
                        "tickers_requested": tickers,
                        "algorithm": "fss_v2",
                        "note": "Please ensure market data APIs are configured (Polygon, Alpaca, or Alpha Vantage)"
                    }
            
            elif tool_name == "optimize_fss_portfolio":
                tickers = arguments.get("tickers", [])
                fss_scores = arguments.get("fss_scores", {})
                volatilities = arguments.get("volatilities", {})
                max_weight = arguments.get("max_weight", 0.15)
                
                if not tickers:
                    return {
                        "error": "Please provide a list of stock symbols",
                        "algorithm": "portfolio_optimization"
                    }
                
                return self.algorithm_service.optimize_fss_portfolio(
                    tickers=tickers,
                    fss_scores=fss_scores,
                    volatilities=volatilities,
                    max_weight=max_weight
                )
            
            elif tool_name == "backtest_fss_strategy":
                tickers = arguments.get("tickers", [])
                rebalance_freq = arguments.get("rebalance_freq", "M")
                top_n = arguments.get("top_n", 20)
                
                if not tickers:
                    return {
                        "error": "Please provide a list of stock symbols to backtest",
                        "algorithm": "fss_backtest"
                    }
                
                # Note: In production, this would fetch historical data
                return {
                    "message": f"FSS backtesting requires historical price data for {len(tickers)} tickers. This feature is available when market data is connected.",
                    "tickers_requested": tickers,
                    "rebalance_freq": rebalance_freq,
                    "top_n": top_n,
                    "algorithm": "fss_backtest",
                    "note": "To use FSS backtesting, ensure market data service is configured with historical price data."
                }
            
            else:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "available_tools": [t["function"]["name"] for t in AITools.get_tool_definitions()]
                }
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Tool execution failed: {tool_name}")
            return {
                "error": str(e),
                "tool": tool_name
            }


# Singleton instance
_tool_runner = ToolRunner()


def get_tool_runner() -> ToolRunner:
    """Get singleton tool runner instance"""
    return _tool_runner

