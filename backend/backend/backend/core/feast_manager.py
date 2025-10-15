"""
Feast Feature Store Manager for RichesReach AI
Phase 1: ML Feature Management
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

try:
    from feast import FeatureStore
    from feast.errors import FeatureViewNotFoundException
    FEAST_AVAILABLE = True
except ImportError:
    FEAST_AVAILABLE = False
    logging.warning("Feast not available - feature store functionality disabled")

class FeastManager:
    """Manages Feast feature store operations"""
    
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or os.path.join(os.path.dirname(__file__), "..", "feast")
        self.store = None
        self.available = FEAST_AVAILABLE
        
        if self.available:
            try:
                self.store = FeatureStore(repo_path=self.repo_path)
                logging.info("✅ Feast feature store initialized successfully")
            except Exception as e:
                logging.error(f"❌ Failed to initialize Feast feature store: {e}")
                self.available = False
    
    def get_features(self, 
                    entity_ids: List[str], 
                    feature_names: List[str],
                    timestamp: Optional[datetime] = None) -> pd.DataFrame:
        """Get features for given entities"""
        if not self.available or not self.store:
            logging.warning("Feast not available - returning empty DataFrame")
            return pd.DataFrame()
        
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Create entity dataframe
            entity_df = pd.DataFrame({
                'symbol': entity_ids,
                'event_timestamp': [timestamp] * len(entity_ids)
            })
            
            # Get features
            features = self.store.get_historical_features(
                entity_df=entity_df,
                features=feature_names
            ).to_df()
            
            logging.info(f"Retrieved {len(features)} feature records for {len(entity_ids)} entities")
            return features
            
        except Exception as e:
            logging.error(f"Error retrieving features: {e}")
            return pd.DataFrame()
    
    def get_online_features(self, 
                           entity_ids: List[str], 
                           feature_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get online features for real-time predictions"""
        if not self.available or not self.store:
            logging.warning("Feast not available - returning empty dict")
            return {}
        
        try:
            # Create entity rows
            entity_rows = [{"symbol": entity_id} for entity_id in entity_ids]
            
            # Get online features
            features = self.store.get_online_features(
                features=feature_names,
                entity_rows=entity_rows
            ).to_dict()
            
            logging.info(f"Retrieved online features for {len(entity_ids)} entities")
            return features
            
        except Exception as e:
            logging.error(f"Error retrieving online features: {e}")
            return {}
    
    def materialize_features(self, 
                           start_date: datetime, 
                           end_date: Optional[datetime] = None) -> bool:
        """Materialize features for offline store"""
        if not self.available or not self.store:
            logging.warning("Feast not available - skipping materialization")
            return False
        
        try:
            if end_date is None:
                end_date = datetime.now()
            
            self.store.materialize(start_date=start_date, end_date=end_date)
            logging.info(f"Materialized features from {start_date} to {end_date}")
            return True
            
        except Exception as e:
            logging.error(f"Error materializing features: {e}")
            return False
    
    def get_feature_statistics(self, feature_name: str) -> Dict[str, Any]:
        """Get statistics for a specific feature"""
        if not self.available or not self.store:
            return {}
        
        try:
            # This would require custom implementation based on your data
            # For now, return basic info
            return {
                "feature_name": feature_name,
                "available": True,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting feature statistics: {e}")
            return {}
    
    def validate_feature_data(self, 
                             entity_id: str, 
                             feature_name: str, 
                             value: Any) -> bool:
        """Validate feature data before storing"""
        if not self.available:
            return True
        
        try:
            # Basic validation logic
            if feature_name.endswith('_score') and not isinstance(value, (int, float)):
                return False
            
            if feature_name.endswith('_count') and not isinstance(value, int):
                return False
            
            if feature_name.endswith('_ratio') and not isinstance(value, (int, float)):
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating feature data: {e}")
            return False
    
    def get_available_features(self) -> List[str]:
        """Get list of available features"""
        if not self.available or not self.store:
            return []
        
        try:
            feature_views = self.store.list_feature_views()
            features = []
            
            for fv in feature_views:
                for feature in fv.features:
                    features.append(f"{fv.name}:{feature.name}")
            
            return features
            
        except Exception as e:
            logging.error(f"Error getting available features: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check feature store health"""
        if not self.available:
            return {
                "status": "unavailable",
                "reason": "Feast not installed or configured"
            }
        
        try:
            if not self.store:
                return {
                    "status": "unhealthy",
                    "reason": "Feature store not initialized"
                }
            
            # Try to list feature views as a health check
            feature_views = self.store.list_feature_views()
            
            return {
                "status": "healthy",
                "feature_views_count": len(feature_views),
                "available_features": len(self.get_available_features()),
                "repo_path": self.repo_path
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": str(e)
            }

# Global instance
feast_manager = FeastManager()

# Convenience functions
def get_market_features(symbols: List[str]) -> pd.DataFrame:
    """Get market data features for symbols"""
    feature_names = [
        "market_data_features:price",
        "market_data_features:volume",
        "market_data_features:change_percent"
    ]
    return feast_manager.get_features(symbols, feature_names)

def get_technical_features(symbols: List[str]) -> pd.DataFrame:
    """Get technical indicator features for symbols"""
    feature_names = [
        "technical_indicators_features:sma_20",
        "technical_indicators_features:rsi_14",
        "technical_indicators_features:macd",
        "technical_indicators_features:bollinger_upper",
        "technical_indicators_features:bollinger_lower"
    ]
    return feast_manager.get_features(symbols, feature_names)

def get_sentiment_features(symbols: List[str]) -> pd.DataFrame:
    """Get sentiment features for symbols"""
    feature_names = [
        "sentiment_features:sentiment_score",
        "sentiment_features:sentiment_confidence",
        "sentiment_features:news_count"
    ]
    return feast_manager.get_features(symbols, feature_names)

def get_ml_features(symbols: List[str]) -> pd.DataFrame:
    """Get ML prediction features for symbols"""
    feature_names = [
        "ml_prediction_features:prediction_score",
        "ml_prediction_features:prediction_confidence",
        "ml_prediction_features:risk_score"
    ]
    return feast_manager.get_features(symbols, feature_names)
