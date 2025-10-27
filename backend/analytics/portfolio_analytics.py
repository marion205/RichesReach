"""
Advanced Portfolio Analytics System for RichesReach
Provides comprehensive portfolio analysis, risk metrics, performance attribution,
and advanced reporting features.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import random
import math
import numpy as np

class PortfolioAnalytics:
    """Advanced portfolio analytics engine"""
    
    def __init__(self):
        self.portfolios_db = {}
        self.positions_db = {}
        self.trades_db = {}
        self.market_data_db = {}
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock portfolio data"""
        # Mock portfolio
        portfolio_id = "portfolio_001"
        self.portfolios_db[portfolio_id] = {
            "id": portfolio_id,
            "name": "Main Trading Portfolio",
            "user_id": "user_001",
            "total_value": 50000.0,
            "cash_balance": 10000.0,
            "invested_value": 40000.0,
            "created_at": "2023-01-01T00:00:00",
            "last_updated": datetime.now().isoformat(),
            "currency": "USD",
            "risk_tolerance": "moderate",
            "investment_goal": "growth"
        }
        
        # Mock positions
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
        for i, symbol in enumerate(symbols):
            position = {
                "id": f"pos_{i:03d}",
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "quantity": random.randint(10, 100),
                "avg_cost": random.uniform(100, 500),
                "current_price": random.uniform(100, 500),
                "market_value": 0,  # Will be calculated
                "unrealized_pnl": 0,  # Will be calculated
                "unrealized_pnl_percent": 0,  # Will be calculated
                "weight": 0,  # Will be calculated
                "sector": random.choice(["Technology", "Healthcare", "Finance", "Consumer", "Energy"]),
                "purchase_date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
            }
            position["market_value"] = position["quantity"] * position["current_price"]
            position["unrealized_pnl"] = position["market_value"] - (position["quantity"] * position["avg_cost"])
            position["unrealized_pnl_percent"] = (position["unrealized_pnl"] / (position["quantity"] * position["avg_cost"])) * 100
            self.positions_db[position["id"]] = position
        
        # Mock trades
        for i in range(100):
            trade = {
                "id": f"trade_{i:03d}",
                "portfolio_id": portfolio_id,
                "symbol": random.choice(symbols),
                "side": random.choice(["BUY", "SELL"]),
                "quantity": random.randint(1, 50),
                "price": random.uniform(100, 500),
                "timestamp": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "commission": random.uniform(1, 10),
                "pnl": random.uniform(-500, 1000),
                "status": "filled"
            }
            self.trades_db[trade["id"]] = trade
    
    def get_portfolio_overview(self, portfolio_id: str) -> Dict[str, Any]:
        """Get comprehensive portfolio overview"""
        if portfolio_id not in self.portfolios_db:
            return {"error": "Portfolio not found"}
        
        portfolio = self.portfolios_db[portfolio_id]
        positions = [pos for pos in self.positions_db.values() if pos["portfolio_id"] == portfolio_id]
        
        # Calculate portfolio metrics
        total_market_value = sum(pos["market_value"] for pos in positions)
        total_cost_basis = sum(pos["quantity"] * pos["avg_cost"] for pos in positions)
        total_unrealized_pnl = sum(pos["unrealized_pnl"] for pos in positions)
        total_unrealized_pnl_percent = (total_unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        # Calculate weights
        for position in positions:
            position["weight"] = (position["market_value"] / total_market_value * 100) if total_market_value > 0 else 0
        
        # Calculate sector allocation
        sector_allocation = {}
        for position in positions:
            sector = position["sector"]
            if sector not in sector_allocation:
                sector_allocation[sector] = {"value": 0, "weight": 0}
            sector_allocation[sector]["value"] += position["market_value"]
            sector_allocation[sector]["weight"] += position["weight"]
        
        return {
            "portfolio": portfolio,
            "positions": positions,
            "metrics": {
                "total_market_value": round(total_market_value, 2),
                "total_cost_basis": round(total_cost_basis, 2),
                "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                "total_unrealized_pnl_percent": round(total_unrealized_pnl_percent, 2),
                "cash_balance": portfolio["cash_balance"],
                "total_value": round(total_market_value + portfolio["cash_balance"], 2),
                "invested_percentage": round((total_market_value / (total_market_value + portfolio["cash_balance"]) * 100), 2),
                "cash_percentage": round((portfolio["cash_balance"] / (total_market_value + portfolio["cash_balance"]) * 100), 2)
            },
            "sector_allocation": sector_allocation,
            "position_count": len(positions),
            "last_updated": datetime.now().isoformat()
        }
    
    def get_performance_metrics(self, portfolio_id: str, period: str = "1Y") -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        if portfolio_id not in self.portfolios_db:
            return {"error": "Portfolio not found"}
        
        # Calculate period dates
        end_date = datetime.now()
        if period == "1D":
            start_date = end_date - timedelta(days=1)
        elif period == "1W":
            start_date = end_date - timedelta(weeks=1)
        elif period == "1M":
            start_date = end_date - timedelta(days=30)
        elif period == "3M":
            start_date = end_date - timedelta(days=90)
        elif period == "6M":
            start_date = end_date - timedelta(days=180)
        elif period == "1Y":
            start_date = end_date - timedelta(days=365)
        else:  # All time
            start_date = datetime(2023, 1, 1)
        
        # Get trades in period
        period_trades = [
            trade for trade in self.trades_db.values()
            if trade["portfolio_id"] == portfolio_id and
            datetime.fromisoformat(trade["timestamp"]) >= start_date
        ]
        
        # Calculate performance metrics
        total_pnl = sum(trade["pnl"] for trade in period_trades)
        total_commission = sum(trade["commission"] for trade in period_trades)
        net_pnl = total_pnl - total_commission
        
        # Calculate returns
        portfolio_value = self.portfolios_db[portfolio_id]["total_value"]
        period_return = (net_pnl / portfolio_value * 100) if portfolio_value > 0 else 0
        
        # Calculate volatility (mock)
        daily_returns = [random.uniform(-0.05, 0.05) for _ in range(252)]
        volatility = np.std(daily_returns) * math.sqrt(252) * 100
        
        # Calculate Sharpe ratio (mock)
        risk_free_rate = 0.02  # 2% annual
        excess_return = (period_return / 100) - risk_free_rate
        sharpe_ratio = excess_return / (volatility / 100) if volatility > 0 else 0.0
        sharpe_ratio = max(-10.0, min(10.0, sharpe_ratio))  # Cap between -10 and 10
        
        # Calculate max drawdown (mock)
        max_drawdown = random.uniform(5, 15)
        
        # Calculate win rate
        winning_trades = [trade for trade in period_trades if trade["pnl"] > 0]
        win_rate = len(winning_trades) / len(period_trades) if period_trades else 0
        
        # Calculate average win/loss
        avg_win = sum(trade["pnl"] for trade in winning_trades) / len(winning_trades) if winning_trades else 0
        losing_trades = [trade for trade in period_trades if trade["pnl"] < 0]
        avg_loss = sum(trade["pnl"] for trade in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Calculate profit factor
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 100.0  # Cap at 100 instead of infinity
        
        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "performance": {
                "total_return": round(period_return, 2),
                "total_pnl": round(total_pnl, 2),
                "net_pnl": round(net_pnl, 2),
                "total_commission": round(total_commission, 2),
                "volatility": round(volatility, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 2),
                "win_rate": round(win_rate * 100, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2)
            },
            "trade_stats": {
                "total_trades": len(period_trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "avg_trade_size": round(sum(trade["quantity"] * trade["price"] for trade in period_trades) / len(period_trades), 2) if period_trades else 0
            }
        }
    
    def get_risk_metrics(self, portfolio_id: str) -> Dict[str, Any]:
        """Get comprehensive risk metrics"""
        if portfolio_id not in self.portfolios_db:
            return {"error": "Portfolio not found"}
        
        positions = [pos for pos in self.positions_db.values() if pos["portfolio_id"] == portfolio_id]
        
        # Calculate position-level risk metrics
        position_risks = []
        for position in positions:
            # Mock beta calculation
            beta = random.uniform(0.5, 2.0)
            
            # Mock VaR calculation (95% confidence)
            var_95 = position["market_value"] * random.uniform(0.02, 0.08)
            
            # Mock expected shortfall
            expected_shortfall = var_95 * random.uniform(1.2, 1.5)
            
            position_risks.append({
                "symbol": position["symbol"],
                "market_value": position["market_value"],
                "weight": position["weight"],
                "beta": round(beta, 2),
                "var_95": round(var_95, 2),
                "expected_shortfall": round(expected_shortfall, 2),
                "sector": position["sector"]
            })
        
        # Calculate portfolio-level risk metrics
        portfolio_beta = sum(pos["beta"] * pos["weight"] / 100 for pos in position_risks)
        portfolio_var_95 = sum(pos["var_95"] for pos in position_risks)
        portfolio_expected_shortfall = sum(pos["expected_shortfall"] for pos in position_risks)
        
        # Calculate concentration risk
        top_5_positions = sorted(positions, key=lambda x: x["market_value"], reverse=True)[:5]
        concentration_risk = sum(pos["weight"] for pos in top_5_positions)
        
        # Calculate sector concentration
        sector_weights = {}
        for position in positions:
            sector = position["sector"]
            sector_weights[sector] = sector_weights.get(sector, 0) + position["weight"]
        
        max_sector_weight = max(sector_weights.values()) if sector_weights else 0
        
        return {
            "portfolio_id": portfolio_id,
            "portfolio_risk": {
                "portfolio_beta": round(portfolio_beta, 2),
                "portfolio_var_95": round(portfolio_var_95, 2),
                "portfolio_expected_shortfall": round(portfolio_expected_shortfall, 2),
                "concentration_risk": round(concentration_risk, 2),
                "max_sector_weight": round(max_sector_weight, 2),
                "position_count": len(positions)
            },
            "position_risks": position_risks,
            "sector_weights": sector_weights,
            "risk_assessment": {
                "overall_risk": "moderate" if portfolio_beta < 1.2 else "high",
                "concentration_risk": "low" if concentration_risk < 60 else "moderate" if concentration_risk < 80 else "high",
                "sector_risk": "low" if max_sector_weight < 30 else "moderate" if max_sector_weight < 50 else "high"
            }
        }
    
    def get_attribution_analysis(self, portfolio_id: str, period: str = "1M") -> Dict[str, Any]:
        """Get performance attribution analysis"""
        if portfolio_id not in self.portfolios_db:
            return {"error": "Portfolio not found"}
        
        positions = [pos for pos in self.positions_db.values() if pos["portfolio_id"] == portfolio_id]
        
        # Calculate attribution by position
        position_attribution = []
        total_contribution = 0
        
        for position in positions:
            # Mock contribution calculation
            contribution = position["unrealized_pnl"]
            contribution_percent = (contribution / self.portfolios_db[portfolio_id]["total_value"] * 100) if self.portfolios_db[portfolio_id]["total_value"] > 0 else 0
            
            position_attribution.append({
                "symbol": position["symbol"],
                "sector": position["sector"],
                "weight": position["weight"],
                "contribution": round(contribution, 2),
                "contribution_percent": round(contribution_percent, 2),
                "return": round(position["unrealized_pnl_percent"], 2)
            })
            
            total_contribution += contribution
        
        # Sort by contribution
        position_attribution.sort(key=lambda x: x["contribution"], reverse=True)
        
        # Calculate attribution by sector
        sector_attribution = {}
        for position in positions:
            sector = position["sector"]
            if sector not in sector_attribution:
                sector_attribution[sector] = {
                    "weight": 0,
                    "contribution": 0,
                    "contribution_percent": 0,
                    "return": 0,
                    "position_count": 0
                }
            
            sector_attribution[sector]["weight"] += position["weight"]
            sector_attribution[sector]["contribution"] += position["unrealized_pnl"]
            sector_attribution[sector]["position_count"] += 1
        
        # Calculate sector returns
        for sector, data in sector_attribution.items():
            sector_positions = [pos for pos in positions if pos["sector"] == sector]
            total_cost = sum(pos["quantity"] * pos["avg_cost"] for pos in sector_positions)
            data["return"] = (data["contribution"] / total_cost * 100) if total_cost > 0 else 0
            data["contribution_percent"] = (data["contribution"] / self.portfolios_db[portfolio_id]["total_value"] * 100) if self.portfolios_db[portfolio_id]["total_value"] > 0 else 0
        
        return {
            "period": period,
            "total_contribution": round(total_contribution, 2),
            "position_attribution": position_attribution,
            "sector_attribution": sector_attribution,
            "top_contributors": position_attribution[:5],
            "bottom_contributors": position_attribution[-5:],
            "analysis_date": datetime.now().isoformat()
        }
    
    def get_correlation_analysis(self, portfolio_id: str) -> Dict[str, Any]:
        """Get portfolio correlation analysis"""
        if portfolio_id not in self.portfolios_db:
            return {"error": "Portfolio not found"}
        
        positions = [pos for pos in self.positions_db.values() if pos["portfolio_id"] == portfolio_id]
        
        # Mock correlation matrix
        symbols = [pos["symbol"] for pos in positions]
        correlation_matrix = {}
        
        for i, symbol1 in enumerate(symbols):
            correlation_matrix[symbol1] = {}
            for j, symbol2 in enumerate(symbols):
                if i == j:
                    correlation_matrix[symbol1][symbol2] = 1.0
                else:
                    # Mock correlation based on sectors
                    pos1 = next(pos for pos in positions if pos["symbol"] == symbol1)
                    pos2 = next(pos for pos in positions if pos["symbol"] == symbol2)
                    
                    if pos1["sector"] == pos2["sector"]:
                        correlation = random.uniform(0.6, 0.9)
                    else:
                        correlation = random.uniform(0.1, 0.5)
                    
                    correlation_matrix[symbol1][symbol2] = round(correlation, 3)
        
        # Calculate average correlation
        correlations = []
        for symbol1 in symbols:
            for symbol2 in symbols:
                if symbol1 != symbol2:
                    correlations.append(correlation_matrix[symbol1][symbol2])
        
        avg_correlation = sum(correlations) / len(correlations) if correlations else 0
        
        # Find highest correlations
        high_correlations = []
        for symbol1 in symbols:
            for symbol2 in symbols:
                if symbol1 != symbol2 and correlation_matrix[symbol1][symbol2] > 0.7:
                    high_correlations.append({
                        "symbol1": symbol1,
                        "symbol2": symbol2,
                        "correlation": correlation_matrix[symbol1][symbol2],
                        "sector1": next(pos["sector"] for pos in positions if pos["symbol"] == symbol1),
                        "sector2": next(pos["sector"] for pos in positions if pos["symbol"] == symbol2)
                    })
        
        high_correlations.sort(key=lambda x: x["correlation"], reverse=True)
        
        return {
            "portfolio_id": portfolio_id,
            "correlation_matrix": correlation_matrix,
            "avg_correlation": round(avg_correlation, 3),
            "high_correlations": high_correlations[:10],
            "correlation_risk": {
                "level": "low" if avg_correlation < 0.3 else "moderate" if avg_correlation < 0.6 else "high",
                "description": f"Average correlation of {avg_correlation:.1%} indicates {'low' if avg_correlation < 0.3 else 'moderate' if avg_correlation < 0.6 else 'high'} diversification"
            },
            "analysis_date": datetime.now().isoformat()
        }
    
    def get_tax_analysis(self, portfolio_id: str) -> Dict[str, Any]:
        """Get tax analysis and optimization suggestions"""
        if portfolio_id not in self.portfolios_db:
            return {"error": "Portfolio not found"}
        
        positions = [pos for pos in self.positions_db.values() if pos["portfolio_id"] == portfolio_id]
        
        # Calculate tax implications
        short_term_positions = []
        long_term_positions = []
        
        for position in positions:
            purchase_date = datetime.fromisoformat(position["purchase_date"])
            holding_period = datetime.now() - purchase_date
            
            if holding_period.days < 365:
                short_term_positions.append(position)
            else:
                long_term_positions.append(position)
        
        # Calculate unrealized gains/losses
        short_term_gains = sum(pos["unrealized_pnl"] for pos in short_term_positions if pos["unrealized_pnl"] > 0)
        short_term_losses = sum(pos["unrealized_pnl"] for pos in short_term_positions if pos["unrealized_pnl"] < 0)
        long_term_gains = sum(pos["unrealized_pnl"] for pos in long_term_positions if pos["unrealized_pnl"] > 0)
        long_term_losses = sum(pos["unrealized_pnl"] for pos in long_term_positions if pos["unrealized_pnl"] < 0)
        
        # Mock tax rates
        short_term_tax_rate = 0.37  # 37% for high income
        long_term_tax_rate = 0.20  # 20% for long-term gains
        
        # Calculate tax liability
        short_term_tax = short_term_gains * short_term_tax_rate
        long_term_tax = long_term_gains * long_term_tax_rate
        total_tax_liability = short_term_tax + long_term_tax
        
        # Tax optimization suggestions
        suggestions = []
        
        if short_term_losses > 0 and short_term_gains > 0:
            suggestions.append({
                "type": "tax_loss_harvesting",
                "description": f"Consider realizing ${abs(short_term_losses):.2f} in short-term losses to offset gains",
                "potential_savings": abs(short_term_losses) * short_term_tax_rate
            })
        
        if long_term_gains > 0:
            suggestions.append({
                "type": "long_term_holding",
                "description": f"Hold positions for over 1 year to qualify for lower long-term capital gains rate",
                "potential_savings": long_term_gains * (short_term_tax_rate - long_term_tax_rate)
            })
        
        return {
            "portfolio_id": portfolio_id,
            "tax_summary": {
                "short_term_gains": round(short_term_gains, 2),
                "short_term_losses": round(short_term_losses, 2),
                "long_term_gains": round(long_term_gains, 2),
                "long_term_losses": round(long_term_losses, 2),
                "total_tax_liability": round(total_tax_liability, 2),
                "short_term_tax_rate": short_term_tax_rate,
                "long_term_tax_rate": long_term_tax_rate
            },
            "position_breakdown": {
                "short_term_positions": len(short_term_positions),
                "long_term_positions": len(long_term_positions),
                "total_positions": len(positions)
            },
            "optimization_suggestions": suggestions,
            "analysis_date": datetime.now().isoformat()
        }
    
    def get_rebalancing_suggestions(self, portfolio_id: str, target_allocation: Dict[str, float] = None) -> Dict[str, Any]:
        """Get portfolio rebalancing suggestions"""
        if portfolio_id not in self.portfolios_db:
            return {"error": "Portfolio not found"}
        
        if target_allocation is None:
            # Default target allocation
            target_allocation = {
                "Technology": 40.0,
                "Healthcare": 20.0,
                "Finance": 15.0,
                "Consumer": 15.0,
                "Energy": 10.0
            }
        
        positions = [pos for pos in self.positions_db.values() if pos["portfolio_id"] == portfolio_id]
        portfolio_value = sum(pos["market_value"] for pos in positions)
        
        # Calculate current allocation
        current_allocation = {}
        for position in positions:
            sector = position["sector"]
            if sector not in current_allocation:
                current_allocation[sector] = 0
            current_allocation[sector] += position["weight"]
        
        # Calculate rebalancing needs
        rebalancing_actions = []
        total_rebalance_amount = 0
        
        for sector, target_weight in target_allocation.items():
            current_weight = current_allocation.get(sector, 0)
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > 2.0:  # Only rebalance if difference > 2%
                target_value = portfolio_value * target_weight / 100
                current_value = portfolio_value * current_weight / 100
                rebalance_amount = target_value - current_value
                
                rebalancing_actions.append({
                    "sector": sector,
                    "current_weight": round(current_weight, 2),
                    "target_weight": round(target_weight, 2),
                    "weight_diff": round(weight_diff, 2),
                    "current_value": round(current_value, 2),
                    "target_value": round(target_value, 2),
                    "rebalance_amount": round(rebalance_amount, 2),
                    "action": "buy" if rebalance_amount > 0 else "sell"
                })
                
                total_rebalance_amount += abs(rebalance_amount)
        
        # Calculate rebalancing cost
        rebalancing_cost = total_rebalance_amount * 0.001  # 0.1% transaction cost
        
        return {
            "portfolio_id": portfolio_id,
            "current_allocation": current_allocation,
            "target_allocation": target_allocation,
            "rebalancing_actions": rebalancing_actions,
            "rebalancing_summary": {
                "total_rebalance_amount": round(total_rebalance_amount, 2),
                "rebalancing_cost": round(rebalancing_cost, 2),
                "actions_count": len(rebalancing_actions)
            },
            "recommendations": [
                "Consider rebalancing when allocation drifts more than 5% from target",
                "Rebalance quarterly or when major market movements occur",
                "Use dollar-cost averaging for large rebalancing moves"
            ],
            "analysis_date": datetime.now().isoformat()
        }
