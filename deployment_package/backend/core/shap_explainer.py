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
        """Generate SHAP values for a single prediction with detailed breakdown"""
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
            
            # Enhanced breakdown by category
            category_breakdown = self._get_category_breakdown(shap_dict)
            
            # Top 10 features for visualization
            top_10_features = feature_importance[:10]
            
            return {
                'shap_values': shap_dict,
                'feature_importance': feature_importance,
                'top_features': top_10_features,
                'category_breakdown': category_breakdown,
                'explanation': explanation,
                'prediction': float(prediction),
                'total_positive_impact': sum(v for v in shap_dict.values() if v > 0),
                'total_negative_impact': sum(v for v in shap_dict.values() if v < 0),
            }
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {e}")
            return self._get_fallback_explanation(X, prediction)
    
    def _get_category_breakdown(self, shap_dict: Dict[str, float]) -> Dict[str, Any]:
        """Break down SHAP values by feature category"""
        categories = {
            'spending': {'features': [], 'total_impact': 0.0, 'positive': 0.0, 'negative': 0.0},
            'options': {'features': [], 'total_impact': 0.0, 'positive': 0.0, 'negative': 0.0},
            'earnings': {'features': [], 'total_impact': 0.0, 'positive': 0.0, 'negative': 0.0},
            'insider': {'features': [], 'total_impact': 0.0, 'positive': 0.0, 'negative': 0.0},
            'other': {'features': [], 'total_impact': 0.0, 'positive': 0.0, 'negative': 0.0},
        }
        
        for feature_name, shap_value in shap_dict.items():
            feature_lower = feature_name.lower()
            readable_name = self._format_feature_name(feature_name)
            
            if 'spending' in feature_lower:
                cat = 'spending'
            elif any(x in feature_lower for x in ['options', 'put', 'call', 'sweep', 'unusual', 'iv', 'skew']):
                cat = 'options'
            elif 'earnings' in feature_lower or 'surprise' in feature_lower:
                cat = 'earnings'
            elif 'insider' in feature_lower:
                cat = 'insider'
            else:
                cat = 'other'
            
            categories[cat]['features'].append({
                'name': readable_name,
                'value': shap_value,
                'abs_value': abs(shap_value)
            })
            categories[cat]['total_impact'] += abs(shap_value)
            if shap_value > 0:
                categories[cat]['positive'] += shap_value
            else:
                categories[cat]['negative'] += abs(shap_value)
        
        # Calculate percentages
        total_impact = sum(cat['total_impact'] for cat in categories.values())
        if total_impact > 0:
            for cat in categories.values():
                cat['percentage'] = (cat['total_impact'] / total_impact) * 100
                cat['features'].sort(key=lambda x: x['abs_value'], reverse=True)
        else:
            for cat in categories.values():
                cat['percentage'] = 0.0
        
        return categories
    
    def _generate_explanation(self, shap_dict: Dict[str, float], feature_importance: List[tuple], prediction: float) -> str:
        """Generate natural language explanation from SHAP values"""
        if not feature_importance:
            return "Prediction based on model analysis."
        
        top_features = feature_importance[:5]  # Show top 5 instead of 3
        explanation_parts = []
        
        # Group features by category
        spending_features = []
        options_features = []
        earnings_features = []
        insider_features = []
        other_features = []
        
        for feature_name, shap_value in top_features:
            readable_name = self._format_feature_name(feature_name)
            magnitude = abs(shap_value)
            
            if 'spending' in feature_name.lower():
                spending_features.append((readable_name, shap_value, magnitude))
            elif any(x in feature_name.lower() for x in ['options', 'put', 'call', 'sweep', 'unusual']):
                options_features.append((readable_name, shap_value, magnitude))
            elif 'earnings' in feature_name.lower() or 'surprise' in feature_name.lower():
                earnings_features.append((readable_name, shap_value, magnitude))
            elif 'insider' in feature_name.lower():
                insider_features.append((readable_name, shap_value, magnitude))
            else:
                other_features.append((readable_name, shap_value, magnitude))
        
        # Build explanation by category
        category_explanations = []
        
        if spending_features:
            total_spending_impact = sum(m for _, _, m in spending_features)
            direction = "positive" if sum(v for _, v, _ in spending_features) > 0 else "negative"
            category_explanations.append(f"Consumer spending signals ({direction} impact: {total_spending_impact:.2%})")
        
        if options_features:
            total_options_impact = sum(m for _, _, m in options_features)
            direction = "bullish" if sum(v for _, v, _ in options_features) > 0 else "bearish"
            category_explanations.append(f"Options flow ({direction} signals: {total_options_impact:.2%})")
        
        if earnings_features:
            total_earnings_impact = sum(m for _, _, m in earnings_features)
            category_explanations.append(f"Earnings patterns (impact: {total_earnings_impact:.2%})")
        
        if insider_features:
            total_insider_impact = sum(m for _, _, m in insider_features)
            direction = "buying" if sum(v for _, v, _ in insider_features) > 0 else "selling"
            category_explanations.append(f"Insider activity ({direction} pressure: {total_insider_impact:.2%})")
        
        # Add top individual features
        for feature_name, shap_value in top_features[:3]:
            direction = "increases" if shap_value > 0 else "decreases"
            magnitude = abs(shap_value)
            readable_name = self._format_feature_name(feature_name)
            
            if magnitude > 0.05:
                pct_impact = (magnitude / abs(prediction)) * 100 if prediction != 0 else 0
                explanation_parts.append(f"{readable_name} {direction} prediction by {pct_impact:.1f}%")
        
        # Combine category and feature explanations
        if category_explanations:
            explanation = "Prediction driven by: " + "; ".join(category_explanations)
            if explanation_parts:
                explanation += ". Top factors: " + ", ".join(explanation_parts[:2]) + "."
            return explanation
        
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

