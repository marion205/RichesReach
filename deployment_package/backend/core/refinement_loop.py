# core/refinement_loop.py
"""
Refinement Loop - Behavioral Coaching
Automatically suggests improvements when algorithm results show low probability.

The Logic: If Monte Carlo returns a 60% success rate, don't just tell the user.
The AI Action: Automatically trigger a second query: "What savings increase is needed to get this user to 90%?"
The Result: Proactive advice: "You're at 60%, but if you save just $150 more per month, your success rate jumps to 91%."
"""
import logging
from typing import Dict, Any, Optional
from .quantitative_algorithms import MonteCarloSimulation

logger = logging.getLogger(__name__)


class RefinementLoop:
    """
    Implements iterative refinement for algorithm results.
    
    When results show low probability, automatically suggests improvements.
    """
    
    def __init__(self):
        """Initialize refinement loop"""
        self.monte_carlo = MonteCarloSimulation()
    
    def refine_goal_simulation(
        self,
        initial_result: Dict[str, Any],
        goal_amount: float,
        time_horizon_months: int,
        current_savings: float,
        monthly_contribution: float,
        target_success_probability: float = 0.90,
        risk_level: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Refine goal simulation if success probability is low.
        
        If probability < target, automatically calculates required savings increase.
        
        Args:
            initial_result: Initial Monte Carlo result
            goal_amount: Target goal amount
            time_horizon_months: Time horizon
            current_savings: Current savings
            monthly_contribution: Current monthly contribution
            target_success_probability: Target probability (default 90%)
            risk_level: Risk level
            
        Returns:
            Refined result with improvement suggestions
        """
        success_prob = initial_result.get("success_probability", 0)
        
        # If already above target, no refinement needed
        if success_prob >= target_success_probability:
            return {
                **initial_result,
                "refinement_applied": False,
                "refinement_message": None
            }
        
        # Calculate required savings to reach target probability
        risk_params = {
            "conservative": {"mean": 0.05, "std": 0.10},
            "moderate": {"mean": 0.07, "std": 0.15},
            "aggressive": {"mean": 0.10, "std": 0.20}
        }
        params = risk_params.get(risk_level.lower(), risk_params["moderate"])
        
        # Estimate years to goal (simplified)
        years_to_goal = time_horizon_months / 12
        
        required_savings = self.monte_carlo.find_required_savings(
            current_age=0,  # Not used for goal simulation
            retirement_age=0,
            current_savings=current_savings,
            target_amount=goal_amount,
            annual_return_mean=params["mean"],
            annual_return_std=params["std"],
            target_success_probability=target_success_probability,
            num_simulations=10000
        )
        
        # Adjust for time horizon
        required_monthly = required_savings * (12 / time_horizon_months) if time_horizon_months > 0 else required_savings
        
        # Calculate increase needed
        savings_increase = max(0, required_monthly - monthly_contribution)
        
        # Run refined simulation
        refined_result = self.monte_carlo.simulate_goal(
            goal_amount=goal_amount,
            time_horizon_months=time_horizon_months,
            current_savings=current_savings,
            monthly_contribution=required_monthly,
            annual_return_mean=params["mean"],
            annual_return_std=params["std"]
        )
        
        # Build refinement message
        refinement_message = self._build_refinement_message(
            current_prob=success_prob,
            target_prob=target_success_probability,
            savings_increase=savings_increase,
            refined_prob=refined_result.success_probability
        )
        
        return {
            **initial_result,
            "refinement_applied": True,
            "refinement_message": refinement_message,
            "required_monthly_savings": required_monthly,
            "savings_increase_needed": savings_increase,
            "refined_success_probability": refined_result.success_probability,
            "refined_result": {
                "success_probability": refined_result.success_probability,
                "median_outcome": refined_result.median_outcome,
                "worst_case": refined_result.worst_case_10th_percentile,
                "best_case": refined_result.best_case_90th_percentile
            }
        }
    
    def refine_retirement_simulation(
        self,
        initial_result: Dict[str, Any],
        current_age: int,
        retirement_age: int,
        current_savings: float,
        monthly_contribution: float,
        target_amount: Optional[float] = None,
        target_success_probability: float = 0.85
    ) -> Dict[str, Any]:
        """
        Refine retirement simulation if safety score is low.
        
        Args:
            initial_result: Initial retirement simulation result
            current_age: Current age
            retirement_age: Retirement age
            current_savings: Current savings
            monthly_contribution: Current monthly contribution
            target_amount: Optional target amount
            target_success_probability: Target safety score (default 85%)
            
        Returns:
            Refined result with improvement suggestions
        """
        success_prob = initial_result.get("success_probability", 0)
        
        if success_prob >= target_success_probability:
            return {
                **initial_result,
                "refinement_applied": False,
                "refinement_message": None
            }
        
        # Find required savings
        required_savings = self.monte_carlo.find_required_savings(
            current_age=current_age,
            retirement_age=retirement_age,
            current_savings=current_savings,
            target_amount=target_amount or (current_savings * 10),  # Rough estimate
            target_success_probability=target_success_probability
        )
        
        savings_increase = max(0, required_savings - monthly_contribution)
        
        # Run refined simulation
        refined_result = self.monte_carlo.simulate_retirement(
            current_age=current_age,
            retirement_age=retirement_age,
            current_savings=current_savings,
            monthly_contribution=required_savings,
            target_amount=target_amount
        )
        
        refinement_message = self._build_refinement_message(
            current_prob=success_prob,
            target_prob=target_success_probability,
            savings_increase=savings_increase,
            refined_prob=refined_result.success_probability
        )
        
        return {
            **initial_result,
            "refinement_applied": True,
            "refinement_message": refinement_message,
            "required_monthly_savings": required_savings,
            "savings_increase_needed": savings_increase,
            "refined_success_probability": refined_result.success_probability,
            "refined_result": {
                "success_probability": refined_result.success_probability,
                "median_outcome": refined_result.median_outcome,
                "worst_case": refined_result.worst_case_10th_percentile,
                "best_case": refined_result.best_case_90th_percentile
            }
        }
    
    def _build_refinement_message(
        self,
        current_prob: float,
        target_prob: float,
        savings_increase: float,
        refined_prob: float
    ) -> str:
        """Build a supportive refinement message"""
        if savings_increase <= 0:
            return None
        
        message = f"Your current path shows a {current_prob:.0%} success rate. "
        message += f"To boost your confidence score to {target_prob:.0%}, "
        
        if savings_increase < 50:
            message += f"a small increase of ${savings_increase:.0f} per month would make a significant difference. "
        elif savings_increase < 200:
            message += f"increasing your monthly savings by ${savings_increase:.0f} would strengthen your position. "
        else:
            message += f"consider increasing your monthly savings by ${savings_increase:.0f}. "
        
        message += f"This adjustment would bring your success probability to {refined_prob:.0%}."
        
        return message


# Singleton instance
_refinement_loop = RefinementLoop()


def refine_algorithm_result(algorithm_name: str, result: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Convenience function for refinement loop"""
    if algorithm_name == "monte_carlo_goal":
        return _refinement_loop.refine_goal_simulation(result, **kwargs)
    elif algorithm_name == "monte_carlo_retirement":
        return _refinement_loop.refine_retirement_simulation(result, **kwargs)
    else:
        return result

