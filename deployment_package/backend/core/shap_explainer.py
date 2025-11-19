"""
SHAP Explainability for Hybrid ML Model
Week 3: Add explainable AI to show WHY predictions are made
"""
import logging
import numpy as np
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not available - install with: pip install shap")


class SHAPExplainer:
    """
    Generate SHAP values for model predictions
    Provides explainability: WHY did the model predict this?
    """
    
    def __init__(self, model=None, feature_names=None):
        self.model = model
        self.feature_names = feature_names or []
        self.explainer = None
        self.shap_available = SHAP_AVAILABLE
    
    def create_explainer(self, X_sample: np.ndarray):
        """Create SHAP explainer from sample data"""
        if not self.shap_available or self.model is None:
            return None
        
        try:
            self.explainer = shap.TreeExplainer(self.model)
            logger.info("SHAP TreeExplainer created")
            return self.explainer
        except Exception as e:
            logger.error(f"Error creating SHAP explainer: {e}")
            return None
    
    def explain_prediction(self, X: np.ndarray, prediction: float) -> Dict[str, Any]:
        """Generate SHAP values for a single prediction"""
        if not self.shap_available or self.explainer is None:
            return self._get_fallback_explanation(X, prediction)
        
        try:
            shap_values = self.explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            if len(shap_values.shape) > 1:
                shap_values = shap_values[0]
            
            shap_dict = {}
            for i, feature_name in enumerate(self.feature_names):
                if i < len(shap_values):
                    shap_dict[feature_name] = float(shap_values[i])
            
            feature_importance = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
            explanation = self._generate_explanation(shap_dict, feature_importance, prediction)
            
            return {
                'shap_values': shap_dict,
                'feature_importance': feature_importance,
                'explanation': explanation,
                'prediction': float(prediction)
            }
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {e}")
            return self._get_fallback_explanation(X, prediction)
    
    def _generate_explanation(self, shap_dict: Dict[str, float], feature_importance: List[tuple], prediction: float) -> str:
        """Generate natural language explanation from SHAP values"""
        if not feature_importance:
            return "Prediction based on model analysis."
        
        top_features = feature_importance[:3]
        explanation_parts = []
        
        for feature_name, shap_value in top_features:
            direction = "increases" if shap_value > 0 else "decreases"
            magnitude = abs(shap_value)
            readable_name = self._format_feature_name(feature_name)
            
            if magnitude > 0.05:
                pct_impact = (magnitude / abs(prediction)) * 100 if prediction != 0 else 0
                explanation_parts.append(f"{readable_name} {direction} prediction by {pct_impact:.1f}%")
        
        if explanation_parts:
            return "Prediction driven by: " + ", ".join(explanation_parts) + "."
        return "Prediction based on balanced model signals."
    
    def _format_feature_name(self, feature_name: str) -> str:
        """Convert feature name to readable format"""
        readable = feature_name.replace('_', ' ').title()
        replacements = {
            'Spending Change 1W': '1-week spending change',
            'Spending Change 4W': '4-week spending change',
            'Unusual Volume Pct': 'Unusual options volume',
            'Sweep Detection': 'Options sweep activity',
            'Put Call Ratio': 'Put/Call ratio',
            'Earnings Surprise Avg': 'Earnings surprise history',
            'Insider Buy Ratio': 'Insider buying activity',
        }
        for key, value in replacements.items():
            if key in readable:
                readable = readable.replace(key, value)
        return readable
    
    def _get_fallback_explanation(self, X: np.ndarray, prediction: float) -> Dict[str, Any]:
        """Fallback when SHAP is not available"""
        return {
            'shap_values': {},
            'feature_importance': [],
            'explanation': f"Prediction: {prediction:.2%} excess return. (SHAP explainability not available - install shap library)",
            'prediction': float(prediction)
        }


def explain_hybrid_prediction(model, X: np.ndarray, prediction: float, feature_names: List[str]) -> Dict[str, Any]:
    """Convenience function to explain a hybrid model prediction"""
    explainer = SHAPExplainer(model=model, feature_names=feature_names)
    explainer.create_explainer(X)
    return explainer.explain_prediction(X, prediction)

