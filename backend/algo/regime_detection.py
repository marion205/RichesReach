"""
AI-Powered Market Regime Detection
Adaptive strategy switching based on market conditions
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

from ..market.providers.enhanced_base import MarketDataProvider
from ..broker.adapters.enhanced_base import BrokerageAdapter


@dataclass
class MarketRegime:
    """Market regime data structure"""
    regime_type: str  # "BULL", "BEAR", "SIDEWAYS", "HIGH_VOL"
    confidence: float
    duration_minutes: int
    volatility_regime: str  # "LOW", "MEDIUM", "HIGH"
    momentum_regime: str  # "STRONG_UP", "WEAK_UP", "NEUTRAL", "WEAK_DOWN", "STRONG_DOWN"
    
    # Regime-specific weights
    momentum_weight: float
    mean_reversion_weight: float
    range_weight: float
    volatility_weight: float
    
    # Market features
    vix_level: float
    spy_momentum: float
    sector_rotation: Dict[str, float]
    
    # Trading recommendations
    recommended_mode: str  # "SAFE" or "AGGRESSIVE"
    max_position_size: float
    risk_multiplier: float


class MarketRegimeDetector:
    """AI-powered market regime detection and adaptive strategy switching"""
    
    def __init__(self, market_data_provider: MarketDataProvider):
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        
        # ML Model for regime classification
        self.regime_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            random_state=42
        )
        
        # Feature scaler
        self.scaler = StandardScaler()
        
        # Regime history for pattern recognition
        self.regime_history = []
        self.current_regime = None
        
        # Initialize with training data
        self._train_model()
        
        # Regime-specific strategy weights
        self.regime_strategies = {
            "BULL": {
                "momentum_weight": 0.4,
                "mean_reversion_weight": 0.2,
                "range_weight": 0.1,
                "volatility_weight": 0.3,
                "recommended_mode": "AGGRESSIVE",
                "max_position_size": 0.10,
                "risk_multiplier": 1.2
            },
            "BEAR": {
                "momentum_weight": 0.1,
                "mean_reversion_weight": 0.5,
                "range_weight": 0.2,
                "volatility_weight": 0.2,
                "recommended_mode": "SAFE",
                "max_position_size": 0.05,
                "risk_multiplier": 0.8
            },
            "SIDEWAYS": {
                "momentum_weight": 0.2,
                "mean_reversion_weight": 0.3,
                "range_weight": 0.4,
                "volatility_weight": 0.1,
                "recommended_mode": "SAFE",
                "max_position_size": 0.07,
                "risk_multiplier": 0.9
            },
            "HIGH_VOL": {
                "momentum_weight": 0.3,
                "mean_reversion_weight": 0.2,
                "range_weight": 0.1,
                "volatility_weight": 0.4,
                "recommended_mode": "AGGRESSIVE",
                "max_position_size": 0.08,
                "risk_multiplier": 1.1
            }
        }
    
    def _train_model(self):
        """Train the regime detection model on historical data"""
        try:
            # Generate synthetic training data (in production, use real historical data)
            np.random.seed(42)
            
            # Features: VIX, SPY momentum, sector rotation, volume, volatility
            n_samples = 10000
            X = np.random.randn(n_samples, 8)
            
            # Create realistic feature distributions
            X[:, 0] = np.random.normal(20, 8, n_samples)  # VIX (10-40 range)
            X[:, 1] = np.random.normal(0, 0.02, n_samples)  # SPY momentum (-0.1 to 0.1)
            X[:, 2] = np.random.normal(0.5, 0.2, n_samples)  # Tech sector rotation
            X[:, 3] = np.random.normal(1.0, 0.3, n_samples)  # Volume ratio
            X[:, 4] = np.random.normal(0.02, 0.01, n_samples)  # Volatility
            X[:, 5] = np.random.normal(0, 0.1, n_samples)  # Market breadth
            X[:, 6] = np.random.normal(0, 0.05, n_samples)  # Bond yield change
            X[:, 7] = np.random.normal(0, 0.02, n_samples)  # Dollar strength
            
            # Create regime labels based on feature combinations
            y = []
            for i in range(n_samples):
                vix = X[i, 0]
                spy_mom = X[i, 1]
                vol = X[i, 4]
                
                if vix < 15 and spy_mom > 0.01:
                    y.append("BULL")
                elif vix > 25 and spy_mom < -0.01:
                    y.append("BEAR")
                elif vix > 30 or vol > 0.03:
                    y.append("HIGH_VOL")
                else:
                    y.append("SIDEWAYS")
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.regime_model.fit(X_scaled, y)
            
            self.logger.info("Market regime detection model trained successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to train regime model: {e}")
    
    async def detect_current_regime(self) -> MarketRegime:
        """Detect current market regime using real-time data"""
        try:
            # Get real-time market features
            market_features = await self._get_market_features()
            
            # Prepare features for prediction
            feature_vector = np.array([
                market_features["vix"],
                market_features["spy_momentum"],
                market_features["tech_rotation"],
                market_features["volume_ratio"],
                market_features["volatility"],
                market_features["market_breadth"],
                market_features["bond_yield_change"],
                market_features["dollar_strength"]
            ]).reshape(1, -1)
            
            # Scale features
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Predict regime
            regime_prediction = self.regime_model.predict(feature_vector_scaled)[0]
            regime_proba = self.regime_model.predict_proba(feature_vector_scaled)[0]
            confidence = np.max(regime_proba)
            
            # Get regime-specific parameters
            regime_params = self.regime_strategies[regime_prediction]
            
            # Create regime object
            regime = MarketRegime(
                regime_type=regime_prediction,
                confidence=confidence,
                duration_minutes=self._estimate_regime_duration(regime_prediction),
                volatility_regime=self._classify_volatility_regime(market_features["vix"]),
                momentum_regime=self._classify_momentum_regime(market_features["spy_momentum"]),
                momentum_weight=regime_params["momentum_weight"],
                mean_reversion_weight=regime_params["mean_reversion_weight"],
                range_weight=regime_params["range_weight"],
                volatility_weight=regime_params["volatility_weight"],
                vix_level=market_features["vix"],
                spy_momentum=market_features["spy_momentum"],
                sector_rotation=market_features["sector_rotation"],
                recommended_mode=regime_params["recommended_mode"],
                max_position_size=regime_params["max_position_size"],
                risk_multiplier=regime_params["risk_multiplier"]
            )
            
            # Update regime history
            self.regime_history.append(regime)
            self.current_regime = regime
            
            # Keep only last 100 regimes
            if len(self.regime_history) > 100:
                self.regime_history = self.regime_history[-100:]
            
            self.logger.info(f"Detected market regime: {regime_prediction} (confidence: {confidence:.2f})")
            
            return regime
            
        except Exception as e:
            self.logger.error(f"Failed to detect market regime: {e}")
            # Return default regime
            return self._get_default_regime()
    
    async def _get_market_features(self) -> Dict[str, float]:
        """Get real-time market features for regime detection"""
        try:
            # Get market data
            quotes = await self.market_data_provider.get_quotes(["SPY", "QQQ", "IWM", "VIX"])
            market_status = await self.market_data_provider.get_market_status()
            
            # Calculate features
            spy_price = quotes.get("SPY", {}).get("price", 400.0)
            qqq_price = quotes.get("QQQ", {}).get("price", 350.0)
            iwm_price = quotes.get("IWM", {}).get("price", 200.0)
            vix_price = quotes.get("VIX", {}).get("price", 20.0)
            
            # Calculate momentum (simplified)
            spy_momentum = (spy_price - 400.0) / 400.0  # Relative to baseline
            
            # Calculate sector rotation (Tech vs Small Cap)
            tech_rotation = (qqq_price - 350.0) / 350.0
            small_cap_rotation = (iwm_price - 200.0) / 200.0
            
            # Calculate volume ratio (simplified)
            volume_ratio = 1.0  # Would need historical data
            
            # Calculate volatility
            volatility = vix_price / 100.0  # Normalize VIX
            
            # Calculate market breadth (simplified)
            market_breadth = (spy_momentum + tech_rotation + small_cap_rotation) / 3
            
            # Calculate bond yield change (simplified)
            bond_yield_change = 0.0  # Would need bond data
            
            # Calculate dollar strength (simplified)
            dollar_strength = 0.0  # Would need DXY data
            
            return {
                "vix": vix_price,
                "spy_momentum": spy_momentum,
                "tech_rotation": tech_rotation,
                "volume_ratio": volume_ratio,
                "volatility": volatility,
                "market_breadth": market_breadth,
                "bond_yield_change": bond_yield_change,
                "dollar_strength": dollar_strength,
                "sector_rotation": {
                    "technology": tech_rotation,
                    "small_cap": small_cap_rotation,
                    "financials": 0.0,  # Would need XLF data
                    "healthcare": 0.0,  # Would need XLV data
                    "energy": 0.0       # Would need XLE data
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get market features: {e}")
            return self._get_default_features()
    
    def _get_default_features(self) -> Dict[str, float]:
        """Get default market features when data is unavailable"""
        return {
            "vix": 20.0,
            "spy_momentum": 0.0,
            "tech_rotation": 0.0,
            "volume_ratio": 1.0,
            "volatility": 0.02,
            "market_breadth": 0.0,
            "bond_yield_change": 0.0,
            "dollar_strength": 0.0,
            "sector_rotation": {
                "technology": 0.0,
                "small_cap": 0.0,
                "financials": 0.0,
                "healthcare": 0.0,
                "energy": 0.0
            }
        }
    
    def _classify_volatility_regime(self, vix: float) -> str:
        """Classify volatility regime based on VIX"""
        if vix < 15:
            return "LOW"
        elif vix < 25:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _classify_momentum_regime(self, spy_momentum: float) -> str:
        """Classify momentum regime based on SPY momentum"""
        if spy_momentum > 0.02:
            return "STRONG_UP"
        elif spy_momentum > 0.005:
            return "WEAK_UP"
        elif spy_momentum < -0.02:
            return "STRONG_DOWN"
        elif spy_momentum < -0.005:
            return "WEAK_DOWN"
        else:
            return "NEUTRAL"
    
    def _estimate_regime_duration(self, regime_type: str) -> int:
        """Estimate regime duration in minutes"""
        duration_map = {
            "BULL": 240,      # 4 hours average
            "BEAR": 180,      # 3 hours average
            "SIDEWAYS": 120,  # 2 hours average
            "HIGH_VOL": 60    # 1 hour average
        }
        return duration_map.get(regime_type, 120)
    
    def _get_default_regime(self) -> MarketRegime:
        """Get default regime when detection fails"""
        return MarketRegime(
            regime_type="SIDEWAYS",
            confidence=0.5,
            duration_minutes=120,
            volatility_regime="MEDIUM",
            momentum_regime="NEUTRAL",
            momentum_weight=0.2,
            mean_reversion_weight=0.3,
            range_weight=0.4,
            volatility_weight=0.1,
            vix_level=20.0,
            spy_momentum=0.0,
            sector_rotation={},
            recommended_mode="SAFE",
            max_position_size=0.07,
            risk_multiplier=0.9
        )
    
    def get_regime_recommendations(self) -> Dict[str, any]:
        """Get trading recommendations based on current regime"""
        if not self.current_regime:
            return {}
        
        regime = self.current_regime
        
        return {
            "regime_type": regime.regime_type,
            "confidence": regime.confidence,
            "recommended_mode": regime.recommended_mode,
            "max_position_size": regime.max_position_size,
            "risk_multiplier": regime.risk_multiplier,
            "strategy_weights": {
                "momentum": regime.momentum_weight,
                "mean_reversion": regime.mean_reversion_weight,
                "range": regime.range_weight,
                "volatility": regime.volatility_weight
            },
            "market_conditions": {
                "vix_level": regime.vix_level,
                "volatility_regime": regime.volatility_regime,
                "momentum_regime": regime.momentum_regime
            },
            "trading_recommendations": self._get_trading_recommendations(regime)
        }
    
    def _get_trading_recommendations(self, regime: MarketRegime) -> List[str]:
        """Get specific trading recommendations for the regime"""
        recommendations = []
        
        if regime.regime_type == "BULL":
            recommendations.extend([
                "Focus on momentum strategies",
                "Increase position sizes",
                "Look for breakout patterns",
                "Consider growth stocks"
            ])
        elif regime.regime_type == "BEAR":
            recommendations.extend([
                "Focus on mean reversion",
                "Reduce position sizes",
                "Use defensive stocks",
                "Consider short strategies"
            ])
        elif regime.regime_type == "SIDEWAYS":
            recommendations.extend([
                "Focus on range trading",
                "Use support/resistance levels",
                "Consider iron condors",
                "Avoid momentum strategies"
            ])
        elif regime.regime_type == "HIGH_VOL":
            recommendations.extend([
                "Focus on volatility strategies",
                "Use wider stops",
                "Consider straddles/strangles",
                "Monitor VIX closely"
            ])
        
        return recommendations
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        try:
            joblib.dump({
                'regime_model': self.regime_model,
                'scaler': self.scaler
            }, filepath)
            self.logger.info(f"Model saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")
    
    def load_model(self, filepath: str):
        """Load a pre-trained model"""
        try:
            model_data = joblib.load(filepath)
            self.regime_model = model_data['regime_model']
            self.scaler = model_data['scaler']
            self.logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")


# Integration with existing trading engine
class AdaptiveTradingEngine:
    """Trading engine that adapts to market regimes"""
    
    def __init__(self, regime_detector: MarketRegimeDetector):
        self.regime_detector = regime_detector
        self.logger = logging.getLogger(__name__)
    
    async def generate_adaptive_picks(self, mode: str = "AUTO") -> List[Dict]:
        """Generate picks adapted to current market regime"""
        try:
            # Detect current regime
            regime = await self.regime_detector.detect_current_regime()
            
            # Override mode if AUTO
            if mode == "AUTO":
                mode = regime.recommended_mode
            
            # Get regime-specific recommendations
            recommendations = self.regime_detector.get_regime_recommendations()
            
            # Generate picks with regime-adapted scoring
            picks = await self._generate_regime_adapted_picks(regime, mode)
            
            # Add regime context to picks
            for pick in picks:
                pick["regime_context"] = {
                    "regime_type": regime.regime_type,
                    "confidence": regime.confidence,
                    "strategy_weights": recommendations["strategy_weights"],
                    "recommendations": recommendations["trading_recommendations"]
                }
            
            return picks
            
        except Exception as e:
            self.logger.error(f"Failed to generate adaptive picks: {e}")
            return []
    
    async def _generate_regime_adapted_picks(self, regime: MarketRegime, mode: str) -> List[Dict]:
        """Generate picks adapted to current regime"""
        # This would integrate with your existing pick generation
        # but with regime-specific scoring weights
        
        picks = []
        
        # Example: Generate picks with regime-adapted scoring
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        
        for symbol in symbols:
            pick = {
                "symbol": symbol,
                "side": "LONG" if regime.momentum_regime in ["STRONG_UP", "WEAK_UP"] else "SHORT",
                "score": np.random.uniform(0.6, 0.9),
                "regime_boost": regime.confidence * 0.1,  # Boost based on regime confidence
                "features": {
                    "momentum_15m": np.random.uniform(-0.05, 0.05),
                    "rvol_10m": np.random.uniform(0.5, 2.0),
                    "vwap_dist": np.random.uniform(-0.01, 0.01),
                    "breakout_pct": np.random.uniform(0, 0.02),
                    "spread_bps": np.random.uniform(1, 10),
                    "catalyst_score": np.random.uniform(0, 1)
                },
                "risk": {
                    "atr_5m": np.random.uniform(0.5, 2.0),
                    "size_shares": int(100 * regime.max_position_size),
                    "stop": np.random.uniform(0.95, 0.98),
                    "targets": [1.02, 1.05],
                    "time_stop_min": regime.duration_minutes
                },
                "notes": f"Regime-adapted pick for {regime.regime_type} market"
            }
            
            # Apply regime-specific scoring
            pick["score"] = self._apply_regime_scoring(pick, regime)
            
            picks.append(pick)
        
        return picks
    
    def _apply_regime_scoring(self, pick: Dict, regime: MarketRegime) -> float:
        """Apply regime-specific scoring to picks"""
        base_score = pick["score"]
        
        # Apply regime weights to different features
        momentum_score = pick["features"]["momentum_15m"] * regime.momentum_weight
        mean_reversion_score = pick["features"]["breakout_pct"] * regime.mean_reversion_weight
        range_score = pick["features"]["vwap_dist"] * regime.range_weight
        volatility_score = pick["features"]["rvol_10m"] * regime.volatility_weight
        
        # Combine scores
        regime_score = (momentum_score + mean_reversion_score + range_score + volatility_score) * 0.5
        
        # Apply regime boost
        final_score = base_score + regime_score + (regime.confidence * 0.1)
        
        return min(max(final_score, 0.0), 1.0)  # Clamp to [0, 1]
