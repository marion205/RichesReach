# core/fss_ml_weights.py
"""
FSS ML Weight Optimization
Learn optimal component weights from historical data using ElasticNet regression.

Converts learned coefficients into dynamic weights that adapt to market conditions.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import sklearn
try:
    from sklearn.linear_model import ElasticNet
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. ML weight optimization disabled.")


@dataclass
class WeightOptimizationResult:
    """Result from ML weight optimization"""
    weights: Dict[str, float]  # Learned weights for T, F, C, R
    raw_coefficients: Dict[str, float]  # Raw ElasticNet coefficients
    r_squared: float  # Model fit quality
    feature_importance: Dict[str, float]  # Feature importance scores


class FSSMLWeightOptimizer:
    """
    ML-based weight optimizer for FSS components.
    
    Uses ElasticNet regression to learn optimal weights from historical
    forward returns, then converts coefficients to usable weights.
    """
    
    def __init__(self, alpha: float = 0.02, l1_ratio: float = 0.2):
        """
        Initialize ML weight optimizer.
        
        Args:
            alpha: ElasticNet regularization strength (default: 0.02)
            l1_ratio: L1/L2 mix (0.2 = mostly L2, default: 0.2)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML weight optimization")
        
        self.alpha = alpha
        self.l1_ratio = l1_ratio
    
    def prepare_ml_dataset(
        self,
        fss_components: pd.DataFrame,
        prices: pd.DataFrame,
        spy: Optional[pd.Series] = None,
        horizon: int = 126,
        include_interactions: bool = True
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare dataset for ML training (v2.0 with interactions).
        
        Args:
            fss_components: Output from compute_fss_v3 (MultiIndex: [component][ticker])
            prices: Price DataFrame
            spy: Optional SPY Series for excess return calculation
            horizon: Forward return horizon in days (default: 126 = 6 months)
            include_interactions: Whether to include interaction terms (T×F, T×C, F×C)
            
        Returns:
            (X, y) where X is features (T, F, C, R, interactions) and y is forward returns (excess if spy provided)
        """
        # Extract component panels
        T = fss_components["T"]
        F = fss_components["F"]
        C = fss_components["C"]
        R = fss_components["R"]
        
        # Calculate forward returns
        forward_ret = prices.shift(-horizon) / prices - 1.0
        
        # Calculate excess return vs SPY if provided
        if spy is not None:
            spy_ret = spy.pct_change(horizon).reindex(prices.index, method='ffill')
            forward_ret = forward_ret.sub(spy_ret, axis=0)  # Excess return
        
        # Stack into long format
        features = [
            T.stack().rename("T"),
            F.stack().rename("F"),
            C.stack().rename("C"),
            R.stack().rename("R"),
        ]
        
        # Add interaction terms if requested
        if include_interactions:
            features.extend([
                (T * F).stack().rename("T_F"),
                (T * C).stack().rename("T_C"),
                (F * C).stack().rename("F_C"),
            ])
        
        X = pd.concat(features, axis=1)
        y = forward_ret.stack().rename("y_excess" if spy is not None else "y")
        
        # Join and drop NaN
        data = X.join(y, how="inner").dropna()
        
        X_clean = data.drop(y.name, axis=1)
        y_clean = data[y.name]
        
        return X_clean, y_clean
    
    def learn_optimal_weights(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        use_time_series_split: bool = True
    ) -> WeightOptimizationResult:
        """
        Learn optimal weights using ElasticNet regression.
        
        Args:
            X: Features DataFrame (columns: T, F, C, R)
            y: Target Series (forward returns)
            use_time_series_split: Whether to use time-series cross-validation
            
        Returns:
            WeightOptimizationResult with learned weights
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required")
        
        # Create pipeline
        model = Pipeline(steps=[
            ("scaler", StandardScaler()),
            ("enet", ElasticNet(
                alpha=self.alpha,
                l1_ratio=self.l1_ratio,
                max_iter=20000,
                random_state=42
            ))
        ])
        
        # Fit on full data
        # (In production, you'd use time-series cross-validation)
        model.fit(X, y)
        
        # Get coefficients
        coef = model.named_steps["enet"].coef_
        feats = X.columns.tolist()
        coef_dict = dict(zip(feats, coef))
        
        # Convert to usable weights:
        # - Keep only positive contributions (optional but common)
        coef_pos = {k: max(0.0, v) for k, v in coef_dict.items()}
        
        # If all negative, use absolute values
        if sum(coef_pos.values()) == 0:
            coef_pos = {k: abs(v) for k, v in coef_dict.items()}
        
        # Normalize to sum to 1.0
        total = sum(coef_pos.values())
        if total == 0:
            # Fallback: equal weights
            weights = {k: 0.25 for k in feats}
        else:
            weights = {k: v / total for k, v in coef_pos.items()}
        
        # Calculate R-squared
        y_pred = model.predict(X)
        ss_res = ((y - y_pred) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r_squared = 1 - (ss_res / (ss_tot + 1e-12))
        
        # Feature importance (absolute coefficients)
        feature_importance = {k: abs(v) for k, v in coef_dict.items()}
        total_imp = sum(feature_importance.values())
        if total_imp > 0:
            feature_importance = {k: v / total_imp for k, v in feature_importance.items()}
        
        return WeightOptimizationResult(
            weights=weights,
            raw_coefficients=coef_dict,
            r_squared=r_squared,
            feature_importance=feature_importance
        )
    
    def optimize_weights_with_cv(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_splits: int = 5
    ) -> WeightOptimizationResult:
        """
        Optimize weights using time-series cross-validation.
        
        Args:
            X: Features DataFrame
            y: Target Series
            n_splits: Number of CV splits
            
        Returns:
            WeightOptimizationResult with averaged weights
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required")
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        all_weights = []
        all_r_squared = []
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Train model
            result = self.learn_optimal_weights(X_train, y_train, use_time_series_split=False)
            
            all_weights.append(result.weights)
            all_r_squared.append(result.r_squared)
        
        # Average weights across folds
        avg_weights = {}
        for key in ["T", "F", "C", "R"]:
            avg_weights[key] = np.mean([w.get(key, 0.25) for w in all_weights])
        
        # Renormalize
        total = sum(avg_weights.values())
        if total > 0:
            avg_weights = {k: v / total for k, v in avg_weights.items()}
        
        avg_r_squared = np.mean(all_r_squared)
        
        return WeightOptimizationResult(
            weights=avg_weights,
            raw_coefficients={},  # Not meaningful for averaged weights
            r_squared=avg_r_squared,
            feature_importance=avg_weights  # Use weights as importance proxy
        )
    
    def learn_optimal_weights_rf(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_estimators: int = 100,
        max_depth: int = 5,
        n_splits: int = 5
    ) -> WeightOptimizationResult:
        """
        Learn optimal weights using RandomForest with interaction terms.
        
        Non-linear model that captures T×F, T×C, F×C interactions.
        Better handles market non-linearities than linear ElasticNet.
        
        Args:
            X: Features DataFrame (should include interaction terms)
            y: Target Series (forward excess returns)
            n_estimators: Number of trees
            max_depth: Max tree depth
            n_splits: Number of CV splits
            
        Returns:
            WeightOptimizationResult with learned weights
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required")
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1
        )
        
        # Cross-validation
        scores = []
        for train_idx, test_idx in tscv.split(X):
            model.fit(X.iloc[train_idx], y.iloc[train_idx])
            pred = model.predict(X.iloc[test_idx])
            scores.append(mean_squared_error(y.iloc[test_idx], pred))
        
        logger.info(f"RF CV MSE: {np.mean(scores):.6f}")
        
        # Final fit on all data
        model.fit(X, y)
        
        # Get feature importances
        importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
        
        # Normalize positive importances to weights
        pos_imp = importances.clip(lower=0)
        if pos_imp.sum() == 0:
            pos_imp = importances.abs()
        
        weights_dict = (pos_imp / pos_imp.sum()).to_dict()
        
        # Map back to main components (interactions boost parent weights)
        main_weights = {
            "T": weights_dict.get("T", 0) + 0.5 * weights_dict.get("T_F", 0) + 0.5 * weights_dict.get("T_C", 0),
            "F": weights_dict.get("F", 0) + 0.5 * weights_dict.get("T_F", 0) + 0.5 * weights_dict.get("F_C", 0),
            "C": weights_dict.get("C", 0) + 0.5 * weights_dict.get("T_C", 0) + 0.5 * weights_dict.get("F_C", 0),
            "R": weights_dict.get("R", 0),
        }
        
        # Renormalize
        total = sum(main_weights.values())
        if total > 0:
            normalized = {k: v / total for k, v in main_weights.items()}
        else:
            normalized = {"T": 0.30, "F": 0.30, "C": 0.25, "R": 0.15}  # Fallback
        
        # Calculate R-squared
        y_pred = model.predict(X)
        ss_res = ((y - y_pred) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r_squared = 1 - (ss_res / (ss_tot + 1e-12))
        
        return WeightOptimizationResult(
            weights=normalized,
            raw_coefficients=weights_dict,
            r_squared=r_squared,
            feature_importance=weights_dict
        )


# Singleton instance
_fss_ml_optimizer = None


def get_fss_ml_optimizer() -> Optional[FSSMLWeightOptimizer]:
    """Get singleton FSS ML optimizer instance"""
    global _fss_ml_optimizer
    if _fss_ml_optimizer is None and SKLEARN_AVAILABLE:
        _fss_ml_optimizer = FSSMLWeightOptimizer()
    return _fss_ml_optimizer

