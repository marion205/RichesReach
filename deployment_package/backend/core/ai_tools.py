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

