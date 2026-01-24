# core/algorithm_service.py
"""
Algorithm Service - The Bridge Between LLM and Quantitative Algorithms

The LLM acts as a "translator" that:
1. Interprets user needs from natural language
2. Extracts variables (amounts, timeframes, etc.)
3. Calls the appropriate quantitative algorithm
4. Translates the mathematical result back into user-friendly language

This service provides a clean API that the LLM can call.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .quantitative_algorithms import (
    MonteCarloSimulation,
    ModernPortfolioTheory,
    BlackLittermanModel,
    TaxLossHarvesting,
    run_monte_carlo_simulation,
    optimize_portfolio_mpt,
    optimize_portfolio_black_litterman,
    identify_tax_loss_harvesting
)
from .ml_behavioral_layer import (
    ReinforcementLearningRebalancer,
    FinancialPersonaClustering,
    CashFlowForecaster,
    should_rebalance_portfolio,
    classify_financial_persona,
    forecast_cash_flow
)
from .refinement_loop import RefinementLoop
from .direct_indexing import get_direct_indexing_service
from .tax_smart_transitions import get_tspt_service

logger = logging.getLogger(__name__)


class AlgorithmService:
    """
    Service that provides quantitative algorithms to the LLM.
    
    The LLM calls these functions instead of doing math itself.
    """
    
    def __init__(self):
        """Initialize algorithm service"""
        self.monte_carlo = MonteCarloSimulation()
        self.mpt = ModernPortfolioTheory()
        self.black_litterman = BlackLittermanModel()
        self.tlh = TaxLossHarvesting()
        self.rl_rebalancer = ReinforcementLearningRebalancer()
        self.persona_clustering = FinancialPersonaClustering()
        self.cash_flow_forecaster = CashFlowForecaster()
        self.refinement_loop = RefinementLoop()
        self.direct_indexing = get_direct_indexing_service()
        self.tspt = get_tspt_service()
    
    def run_goal_simulation(
        self,
        goal_amount: float,
        time_horizon_months: int,
        current_savings: float,
        monthly_contribution: float,
        risk_level: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Simulate achieving a specific goal (e.g., "Can I afford a $50k wedding in 2 years?").
        
        Args:
            goal_amount: Target amount (e.g., 50000)
            time_horizon_months: Time to reach goal (e.g., 24)
            current_savings: Current savings
            monthly_contribution: Monthly contribution
            risk_level: Risk level ("conservative", "moderate", "aggressive")
            
        Returns:
            Dictionary with success probability and recommendations
        """
        # Map risk level to return assumptions
        risk_params = {
            "conservative": {"mean": 0.05, "std": 0.10},
            "moderate": {"mean": 0.07, "std": 0.15},
            "aggressive": {"mean": 0.10, "std": 0.20}
        }
        params = risk_params.get(risk_level.lower(), risk_params["moderate"])
        
        # Run Monte Carlo simulation
        result = self.monte_carlo.simulate_goal(
            goal_amount=goal_amount,
            time_horizon_months=time_horizon_months,
            current_savings=current_savings,
            monthly_contribution=monthly_contribution,
            annual_return_mean=params["mean"],
            annual_return_std=params["std"]
        )
        
        # Apply refinement loop if probability is low
        base_result = {
            "success_probability": result.success_probability,
            "median_outcome": result.median_outcome,
            "worst_case": result.worst_case_10th_percentile,
            "best_case": result.best_case_90th_percentile,
            "simulations_run": result.simulations_run,
            "algorithm": "monte_carlo_simulation"
        }
        
        # Refinement loop: automatically suggest improvements
        if result.success_probability < 0.90:
            refined = self.refinement_loop.refine_goal_simulation(
                initial_result=base_result,
                goal_amount=goal_amount,
                time_horizon_months=time_horizon_months,
                current_savings=current_savings,
                monthly_contribution=monthly_contribution,
                target_success_probability=0.90,
                risk_level=risk_level
            )
            return refined
        
        return base_result
    
    def run_retirement_simulation(
        self,
        current_age: int,
        retirement_age: int,
        current_savings: float,
        monthly_contribution: float,
        target_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Simulate retirement savings (Monte Carlo).
        
        Returns "Safety Score" - probability of not running out of money.
        """
        result = self.monte_carlo.simulate_retirement(
            current_age=current_age,
            retirement_age=retirement_age,
            current_savings=current_savings,
            monthly_contribution=monthly_contribution,
            target_amount=target_amount
        )
        
        base_result = {
            "success_probability": result.success_probability,
            "safety_score": result.success_probability * 100,  # Convert to percentage
            "median_outcome": result.median_outcome,
            "worst_case": result.worst_case_10th_percentile,
            "best_case": result.best_case_90th_percentile,
            "simulations_run": result.simulations_run,
            "algorithm": "monte_carlo_retirement"
        }
        
        # Refinement loop: automatically suggest improvements
        if result.success_probability < 0.85:
            refined = self.refinement_loop.refine_retirement_simulation(
                initial_result=base_result,
                current_age=current_age,
                retirement_age=retirement_age,
                current_savings=current_savings,
                monthly_contribution=monthly_contribution,
                target_amount=target_amount,
                target_success_probability=0.85
            )
            return refined
        
        return base_result
    
    def optimize_portfolio_allocation(
        self,
        assets: List[str],
        expected_returns: Dict[str, float],
        cov_matrix: Dict[str, Dict[str, float]],
        risk_tolerance: str = "moderate",
        user_views: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio using MPT or Black-Litterman.
        
        Args:
            assets: List of asset symbols
            expected_returns: Expected returns for each asset
            cov_matrix: Covariance matrix (nested dict)
            risk_tolerance: Risk tolerance level
            user_views: Optional user views for Black-Litterman (e.g., [{"asset": "AAPL", "return": 0.10}])
            
        Returns:
            Optimal portfolio allocation
        """
        import pandas as pd
        
        # Convert to pandas
        returns_series = pd.Series(expected_returns)
        cov_df = pd.DataFrame(cov_matrix)
        
        # Use Black-Litterman if user views provided, otherwise MPT
        if user_views:
            # Market cap weights (simplified - would use actual market caps)
            market_caps = pd.Series({asset: 1.0 / len(assets) for asset in assets})
            
            result = self.black_litterman.optimize_with_views(
                market_caps=market_caps,
                cov_matrix=cov_df,
                views=user_views
            )
        else:
            result = self.mpt.optimize_portfolio(
                expected_returns=returns_series,
                cov_matrix=cov_df,
                risk_tolerance=risk_tolerance
            )
        
        return {
            "optimal_weights": result.get("weights", {}),
            "expected_return": result.get("expected_return", 0),
            "volatility": result.get("volatility", 0),
            "sharpe_ratio": result.get("sharpe_ratio", 0),
            "algorithm": result.get("method", "mpt")
        }
    
    def find_tax_loss_harvesting(
        self,
        positions: List[Dict[str, Any]],
        realized_gains: float = 0.0
    ) -> Dict[str, Any]:
        """
        Identify tax-loss harvesting opportunities.
        
        Args:
            positions: List of positions with cost_basis, current_price, quantity, purchase_date
            realized_gains: Already realized gains to offset
            
        Returns:
            Tax-loss harvesting recommendations
        """
        result = self.tlh.identify_harvesting_opportunities(
            positions=positions,
            realized_gains=realized_gains
        )
        
        return {
            "opportunities": result.get("opportunities", []),
            "total_tax_savings": result.get("total_potential_tax_savings", 0),
            "can_offset_gains": result.get("can_offset_realized_gains", False),
            "net_tax_benefit": result.get("net_tax_benefit", 0),
            "algorithm": "tax_loss_harvesting"
        }
    
    def check_rebalancing(
        self,
        current_allocation: Dict[str, float],
        target_allocation: Dict[str, float],
        market_volatility: float = 0.15
    ) -> Dict[str, Any]:
        """
        Check if portfolio should be rebalanced (RL-based).
        
        Returns recommendation with reasoning.
        """
        result = self.rl_rebalancer.should_rebalance(
            current_allocation=current_allocation,
            target_allocation=target_allocation,
            market_volatility=market_volatility
        )
        
        return {
            "should_rebalance": result.get("should_rebalance", False),
            "total_drift": result.get("total_drift", 0),
            "estimated_cost": result.get("estimated_transaction_cost", 0),
            "reason": result.get("reason", ""),
            "algorithm": "rl_rebalancing"
        }
    
    def classify_user_persona(
        self,
        user_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify user into financial persona.
        
        Args:
            user_features: age, income, savings_rate, risk_tolerance, etc.
            
        Returns:
            Persona classification
        """
        persona = self.persona_clustering.classify_persona(user_features)
        
        return {
            "persona_type": persona.persona_type,
            "confidence": persona.confidence,
            "characteristics": persona.characteristics,
            "algorithm": "kmeans_clustering"
        }
    
    def forecast_user_cash_flow(
        self,
        historical_transactions: List[Dict[str, Any]],
        forecast_months: int = 12
    ) -> Dict[str, Any]:
        """
        Forecast future cash flow.
        
        Args:
            historical_transactions: List of {date, amount} transactions
            forecast_months: Months to forecast
            
        Returns:
            Cash flow forecast with seasonal patterns
        """
        import pandas as pd
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_transactions)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        result = self.cash_flow_forecaster.forecast_cash_flow(
            historical_transactions=df,
            forecast_months=forecast_months
        )
        
        return {
            "predicted_cash_flow": result.get("predicted_cash_flow", 0),
            "predicted_lower_bound": result.get("predicted_lower_bound", 0),
            "predicted_upper_bound": result.get("predicted_upper_bound", 0),
            "seasonal_patterns": result.get("seasonal_patterns", {}),
            "algorithm": result.get("method", "forecast")
        }
    
    def create_direct_index(
        self,
        target_etf: str,
        portfolio_value: float,
        excluded_stocks: Optional[List[str]] = None,
        tax_optimization: bool = True
    ) -> Dict[str, Any]:
        """
        Create a direct indexing portfolio that tracks an ETF.
        
        Args:
            target_etf: ETF to replicate (e.g., "SPY", "QQQ")
            portfolio_value: Total portfolio value
            excluded_stocks: Stocks to exclude (e.g., employer stock)
            tax_optimization: Enable tax-loss harvesting optimization
            
        Returns:
            Direct indexing portfolio with allocations and tax benefits
        """
        result = self.direct_indexing.create_direct_index(
            target_etf=target_etf,
            portfolio_value=portfolio_value,
            excluded_stocks=excluded_stocks,
            tax_optimization=tax_optimization
        )
        
        return {
            "allocations": result.get("allocations", []),
            "target_etf": result.get("target_etf", target_etf),
            "total_stocks": result.get("total_stocks", 0),
            "tracking_error": result.get("tracking_error", {}),
            "expected_tax_benefits": result.get("expected_tax_benefits", {}),
            "excluded_stocks": excluded_stocks or [],
            "algorithm": "direct_indexing"
        }
    
    def create_tax_smart_transition(
        self,
        concentrated_position: Dict[str, Any],
        target_allocation: Dict[str, float],
        time_horizon_months: int = 36,
        annual_income: float = 0,
        tax_bracket: str = "high"
    ) -> Dict[str, Any]:
        """
        Create a tax-smart transition plan for concentrated positions.
        
        Args:
            concentrated_position: Position to transition
                - symbol: Stock symbol
                - quantity: Number of shares
                - cost_basis: Purchase price per share
                - current_price: Current market price
            target_allocation: Target portfolio allocation
            time_horizon_months: Months to complete transition
            annual_income: Annual income for tax calculations
            tax_bracket: Tax bracket ("low", "medium", "high")
            
        Returns:
            TSPT plan with monthly sales and tax benefits
        """
        result = self.tspt.create_transition_plan(
            concentrated_position=concentrated_position,
            target_allocation=target_allocation,
            time_horizon_months=time_horizon_months,
            annual_income=annual_income,
            tax_bracket=tax_bracket
        )
        
        return {
            "transition_plan": result.get("transition_plan", []),
            "total_tax_savings": result.get("total_tax_savings", 0),
            "total_capital_gains_tax": result.get("total_capital_gains_tax", 0),
            "reinvestment_plan": result.get("reinvestment_plan", {}),
            "estimated_completion_date": result.get("estimated_completion_date"),
            "time_horizon_months": time_horizon_months,
            "algorithm": "tspt"
        }


# Singleton instance
_algorithm_service = AlgorithmService()


def get_algorithm_service() -> AlgorithmService:
    """Get singleton algorithm service instance"""
    return _algorithm_service

