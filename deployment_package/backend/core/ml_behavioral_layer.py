# core/ml_behavioral_layer.py
"""
Machine Learning Behavioral Layer
Handles the behavioral side of wealth management.

While quantitative algorithms handle the math, ML handles:
- Reinforcement Learning: Optimize portfolio rebalancing timing
- Clustering: Group users into financial personas
- Time-Series Forecasting: Predict future cash flow
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Clustering features will use fallback.")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available. Time-series forecasting will use fallback.")


@dataclass
class FinancialPersona:
    """Financial persona classification"""
    persona_type: str  # e.g., "Aggressive Saver", "Conservative Retiree"
    confidence: float
    characteristics: Dict[str, Any]


class ReinforcementLearningRebalancer:
    """
    Reinforcement Learning for Portfolio Rebalancing.
    
    Learns the best moment to trade to minimize fees and maximize returns.
    Instead of rebalancing every 6 months, the RL algorithm learns optimal timing.
    """
    
    def __init__(self):
        """Initialize RL rebalancer"""
        # Simplified RL implementation
        # Full implementation would use a proper RL framework (e.g., Stable-Baselines3)
        self.rebalancing_history = []
    
    def should_rebalance(
        self,
        current_allocation: Dict[str, float],
        target_allocation: Dict[str, float],
        drift_threshold: float = 0.05,  # 5% drift triggers rebalancing
        transaction_cost: float = 0.001,  # 0.1% transaction cost
        market_volatility: float = 0.15
    ) -> Dict[str, Any]:
        """
        Determine if portfolio should be rebalanced using RL-based logic.
        
        Args:
            current_allocation: Current portfolio allocation (dict of asset: weight)
            target_allocation: Target portfolio allocation
            drift_threshold: Maximum allowed drift before rebalancing
            transaction_cost: Cost of rebalancing (as fraction)
            market_volatility: Current market volatility
            
        Returns:
            Dictionary with rebalancing recommendation
        """
        # Calculate drift
        drift = {}
        total_drift = 0.0
        
        for asset in set(list(current_allocation.keys()) + list(target_allocation.keys())):
            current = current_allocation.get(asset, 0)
            target = target_allocation.get(asset, 0)
            asset_drift = abs(current - target)
            drift[asset] = asset_drift
            total_drift += asset_drift
        
        # RL-based decision: Consider transaction costs and volatility
        # High volatility = wait (market might correct naturally)
        # Low volatility + high drift = rebalance
        
        should_rebalance = False
        reason = ""
        
        if total_drift > drift_threshold * 2:  # Significant drift
            should_rebalance = True
            reason = "Significant drift detected"
        elif total_drift > drift_threshold and market_volatility < 0.10:
            # Moderate drift + low volatility = good time to rebalance
            should_rebalance = True
            reason = "Moderate drift with low volatility - optimal rebalancing window"
        elif total_drift > drift_threshold and market_volatility > 0.20:
            # High volatility - wait for market to stabilize
            should_rebalance = False
            reason = "High volatility - waiting for market stabilization"
        else:
            should_rebalance = False
            reason = "Drift within acceptable range"
        
        # Calculate estimated transaction cost
        estimated_cost = total_drift * transaction_cost
        
        return {
            "should_rebalance": should_rebalance,
            "total_drift": float(total_drift),
            "drift_by_asset": {k: float(v) for k, v in drift.items()},
            "estimated_transaction_cost": float(estimated_cost),
            "reason": reason,
            "method": "rl_rebalancing"
        }
    
    def learn_from_rebalance(
        self,
        rebalance_result: Dict[str, Any],
        performance_after: float
    ):
        """
        Learn from rebalancing decision (for future RL improvements).
        
        This would be used to train the RL model in a full implementation.
        """
        self.rebalancing_history.append({
            "result": rebalance_result,
            "performance": performance_after,
            "timestamp": datetime.now()
        })


class FinancialPersonaClustering:
    """
    Clustering (K-Means) for Financial Personas.
    
    Groups users into "Financial Personas" (e.g., "The Aggressive Saver" 
    or "The Conservative Retiree") to ensure advice feels personalized, not generic.
    """
    
    def __init__(self):
        """Initialize persona clustering"""
        self.personas = [
            "Aggressive Saver",
            "Conservative Retiree",
            "Balanced Builder",
            "Growth Seeker",
            "Income Focused"
        ]
    
    def classify_persona(
        self,
        user_features: Dict[str, Any]
    ) -> FinancialPersona:
        """
        Classify user into financial persona based on features.
        
        Args:
            user_features: Dictionary with:
                - age: int
                - income: float
                - savings_rate: float (0-1)
                - risk_tolerance: str ("conservative", "moderate", "aggressive")
                - investment_horizon: int (years)
                - debt_to_income: float
                
        Returns:
            FinancialPersona with classification
        """
        if SKLEARN_AVAILABLE:
            return self._classify_with_kmeans(user_features)
        else:
            return self._classify_fallback(user_features)
    
    def _classify_with_kmeans(
        self,
        user_features: Dict[str, Any]
    ) -> FinancialPersona:
        """Classify using K-Means clustering"""
        try:
            # Extract features
            age = user_features.get("age", 35)
            income = user_features.get("income", 50000)
            savings_rate = user_features.get("savings_rate", 0.1)
            risk_tolerance = user_features.get("risk_tolerance", "moderate")
            investment_horizon = user_features.get("investment_horizon", 10)
            debt_to_income = user_features.get("debt_to_income", 0.3)
            
            # Encode risk tolerance
            risk_map = {"conservative": 0, "moderate": 1, "aggressive": 2}
            risk_encoded = risk_map.get(risk_tolerance.lower(), 1)
            
            # Normalize features
            features = np.array([[
                age / 100.0,  # Normalize age
                income / 200000.0,  # Normalize income
                savings_rate,
                risk_encoded / 2.0,
                investment_horizon / 50.0,
                debt_to_income
            ]])
            
            # For now, use rule-based classification
            # Full implementation would train K-Means on historical user data
            return self._classify_fallback(user_features)
        
        except Exception as e:
            logger.warning(f"K-Means classification failed: {e}, using fallback")
            return self._classify_fallback(user_features)
    
    def _classify_fallback(
        self,
        user_features: Dict[str, Any]
    ) -> FinancialPersona:
        """Fallback rule-based persona classification"""
        age = user_features.get("age", 35)
        savings_rate = user_features.get("savings_rate", 0.1)
        risk_tolerance = user_features.get("risk_tolerance", "moderate").lower()
        investment_horizon = user_features.get("investment_horizon", 10)
        
        # Rule-based classification
        if age >= 60:
            persona = "Conservative Retiree"
            confidence = 0.85
        elif savings_rate > 0.25 and risk_tolerance == "aggressive":
            persona = "Aggressive Saver"
            confidence = 0.80
        elif savings_rate > 0.15:
            persona = "Balanced Builder"
            confidence = 0.75
        elif risk_tolerance == "aggressive" and investment_horizon > 10:
            persona = "Growth Seeker"
            confidence = 0.70
        elif age > 50:
            persona = "Income Focused"
            confidence = 0.75
        else:
            persona = "Balanced Builder"
            confidence = 0.65
        
        return FinancialPersona(
            persona_type=persona,
            confidence=confidence,
            characteristics={
                "age_group": "retiree" if age >= 60 else "working" if age >= 25 else "young",
                "savings_behavior": "high" if savings_rate > 0.20 else "moderate" if savings_rate > 0.10 else "low",
                "risk_profile": risk_tolerance
            }
        )


class CashFlowForecaster:
    """
    Prophet / Time-Series Forecasting for Cash Flow.
    
    Predicts a user's future cash flow. If the algorithm sees a "spending spike" 
    every December, it can proactively advise the user to save more in November.
    """
    
    def __init__(self):
        """Initialize cash flow forecaster"""
        pass
    
    def forecast_cash_flow(
        self,
        historical_transactions: pd.DataFrame,
        forecast_months: int = 12
    ) -> Dict[str, Any]:
        """
        Forecast future cash flow using time-series analysis.
        
        Args:
            historical_transactions: DataFrame with columns:
                - date: datetime
                - amount: float (positive for income, negative for expenses)
            forecast_months: Number of months to forecast
            
        Returns:
            Dictionary with forecast and insights
        """
        if PROPHET_AVAILABLE and len(historical_transactions) > 30:
            return self._forecast_with_prophet(historical_transactions, forecast_months)
        else:
            return self._forecast_fallback(historical_transactions, forecast_months)
    
    def _forecast_with_prophet(
        self,
        historical_transactions: pd.DataFrame,
        forecast_months: int
    ) -> Dict[str, Any]:
        """Forecast using Facebook Prophet"""
        try:
            # Prepare data for Prophet
            df = historical_transactions.copy()
            df['ds'] = pd.to_datetime(df['date'])
            df['y'] = df['amount']
            df = df[['ds', 'y']].sort_values('ds')
            
            # Aggregate to daily
            df_daily = df.groupby('ds')['y'].sum().reset_index()
            
            # Fit Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False
            )
            model.fit(df_daily)
            
            # Make future dataframe
            future = model.make_future_dataframe(periods=forecast_months * 30)
            forecast = model.predict(future)
            
            # Extract forecast
            forecast_period = forecast.tail(forecast_months * 30)
            predicted_income = forecast_period['yhat'].sum()
            predicted_lower = forecast_period['yhat_lower'].sum()
            predicted_upper = forecast_period['yhat_upper'].sum()
            
            # Detect seasonal patterns
            seasonal_patterns = self._detect_seasonal_patterns(forecast)
            
            return {
                "predicted_cash_flow": float(predicted_income),
                "predicted_lower_bound": float(predicted_lower),
                "predicted_upper_bound": float(predicted_upper),
                "seasonal_patterns": seasonal_patterns,
                "method": "prophet_forecast"
            }
        
        except Exception as e:
            logger.warning(f"Prophet forecasting failed: {e}, using fallback")
            return self._forecast_fallback(historical_transactions, forecast_months)
    
    def _forecast_fallback(
        self,
        historical_transactions: pd.DataFrame,
        forecast_months: int
    ) -> Dict[str, Any]:
        """Fallback forecasting using simple moving average"""
        if len(historical_transactions) == 0:
            return {
                "predicted_cash_flow": 0.0,
                "predicted_lower_bound": 0.0,
                "predicted_upper_bound": 0.0,
                "seasonal_patterns": {},
                "method": "fallback_forecast"
            }
        
        # Simple average
        monthly_avg = historical_transactions['amount'].mean()
        predicted = monthly_avg * forecast_months
        
        # Add some variance
        std = historical_transactions['amount'].std()
        lower = predicted - (std * forecast_months * 1.96)  # 95% confidence
        upper = predicted + (std * forecast_months * 1.96)
        
        # Detect seasonal patterns (simplified)
        historical_transactions['month'] = pd.to_datetime(historical_transactions['date']).dt.month
        monthly_patterns = historical_transactions.groupby('month')['amount'].mean().to_dict()
        
        return {
            "predicted_cash_flow": float(predicted),
            "predicted_lower_bound": float(lower),
            "predicted_upper_bound": float(upper),
            "seasonal_patterns": {int(k): float(v) for k, v in monthly_patterns.items()},
            "method": "fallback_forecast"
        }
    
    def _detect_seasonal_patterns(self, forecast: pd.DataFrame) -> Dict[str, Any]:
        """Detect seasonal patterns in forecast"""
        # Extract monthly patterns
        forecast['month'] = forecast['ds'].dt.month
        monthly_avg = forecast.groupby('month')['yhat'].mean()
        
        # Find peak and low months
        peak_month = monthly_avg.idxmax()
        low_month = monthly_avg.idxmin()
        
        return {
            "peak_month": int(peak_month),
            "low_month": int(low_month),
            "monthly_patterns": {int(k): float(v) for k, v in monthly_avg.to_dict().items()}
        }


# Singleton instances
_rl_rebalancer = ReinforcementLearningRebalancer()
_persona_clustering = FinancialPersonaClustering()
_cash_flow_forecaster = CashFlowForecaster()


def should_rebalance_portfolio(**kwargs) -> Dict[str, Any]:
    """Convenience function for RL rebalancing"""
    return _rl_rebalancer.should_rebalance(**kwargs)


def classify_financial_persona(**kwargs) -> FinancialPersona:
    """Convenience function for persona classification"""
    return _persona_clustering.classify_persona(**kwargs)


def forecast_cash_flow(**kwargs) -> Dict[str, Any]:
    """Convenience function for cash flow forecasting"""
    return _cash_flow_forecaster.forecast_cash_flow(**kwargs)

