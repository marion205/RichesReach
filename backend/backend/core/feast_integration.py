"""
Feast Feature Store Integration
================================
Simplified integration with Feast for ML feature serving.

This module provides a wrapper around Feast for easy feature retrieval.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Optional Feast import
try:
    from feast import FeatureStore
    FEAST_AVAILABLE = True
except ImportError:
    FEAST_AVAILABLE = False
    logger.warning("Feast not installed, feature store disabled")


class FeastClient:
    """
    Simplified client for Feast feature store.
    
    Usage:
        client = FeastClient()
        features = client.get_features(
            user_id=123,
            ticker="AAPL",
            feature_names=[
                "market_state:volatility_14d",
                "portfolio_state:equity_ratio"
            ]
        )
    """
    
    def __init__(self, repo_path: str = "backend/backend/feast"):
        """
        Initialize Feast client.
        
        Args:
            repo_path: Path to Feast repository
        """
        self.store = None
        if FEAST_AVAILABLE:
            try:
                self.store = FeatureStore(repo_path=repo_path)
                logger.info(f"✅ Feast feature store initialized: {repo_path}")
            except Exception as e:
                logger.warning(f"Failed to initialize Feast: {e}")
        else:
            logger.warning("Feast not available")
    
    def get_features(
        self,
        user_id: Optional[int] = None,
        ticker: Optional[str] = None,
        feature_names: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get features from online store.
        
        Args:
            user_id: User ID (optional)
            ticker: Ticker symbol (optional)
            feature_names: List of feature names to retrieve
            
        Returns:
            Dictionary of feature values
        """
        if not self.store:
            return {}
        
        if not feature_names:
            feature_names = []
        
        # Build entity rows
        entity_rows = []
        if user_id is not None:
            entity_rows.append({"user_id": user_id})
        if ticker is not None:
            if not entity_rows:
                entity_rows.append({"ticker": ticker})
            else:
                entity_rows[0]["ticker"] = ticker
        
        if not entity_rows:
            logger.warning("No entities provided for feature retrieval")
            return {}
        
        try:
            feature_vector = self.store.get_online_features(
                entity_rows=entity_rows,
                features=feature_names
            ).to_dict()
            
            return feature_vector
        except Exception as e:
            logger.error(f"Failed to get features from Feast: {e}")
            return {}
    
    def get_market_features(self, ticker: str) -> Dict[str, Any]:
        """Get market state features for a ticker."""
        return self.get_features(
            ticker=ticker,
            feature_names=[
                "market_state:volatility_14d",
                "market_state:iv_rank",
                "market_state:momentum_21d",
                "market_state:liquidity_score",
            ]
        )
    
    def get_portfolio_features(self, user_id: int) -> Dict[str, Any]:
        """Get portfolio state features for a user."""
        return self.get_features(
            user_id=user_id,
            feature_names=[
                "portfolio_state:equity_ratio",
                "portfolio_state:cash_available",
                "portfolio_state:risk_budget",
                "portfolio_state:total_return_pct",
            ]
        )


# Global Feast client
_feast_client: Optional[FeastClient] = None


def get_feast_client() -> FeastClient:
    """Get global Feast client instance."""
    global _feast_client
    if _feast_client is None:
        _feast_client = FeastClient()
    return _feast_client

