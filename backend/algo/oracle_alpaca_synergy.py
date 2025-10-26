"""
Oracle + Alpaca Synergy System
AI-powered adaptive scoring with real-time market data integration
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

from ..market.providers.base import MarketDataProvider
from ..broker.adapters.base import Broker
from .enhanced_scoring import EnhancedScoringEngine, PickScore
from .advanced_features import AdvancedFeatures, AdvancedIntradayCalculator


@dataclass
class OracleInsight:
    """Oracle AI insight with confidence scoring"""
    symbol: str
    insight_type: str  # "MOMENTUM", "VOLUME", "TECHNICAL", "SENTIMENT", "RISK"
    insight_text: str
    confidence: float
    impact_score: float
    time_horizon: str  # "SHORT", "MEDIUM", "LONG"
    supporting_evidence: List[str]
    timestamp: datetime


@dataclass
class AdaptiveScore:
    """Adaptive score with Oracle enhancement"""
    symbol: str
    side: str
    
    # Base scores
    base_score: float
    ml_score: float
    
    # Oracle enhancement
    oracle_score: float
    oracle_confidence: float
    
    # Adaptive components
    market_regime_adjustment: float
    volatility_adjustment: float
    liquidity_adjustment: float
    
    # Final adaptive score
    adaptive_score: float
    confidence_interval: Tuple[float, float]
    
    # Oracle insights
    insights: List[OracleInsight]
    
    # Metadata
    model_version: str
    last_updated: datetime


class OracleAlpacaSynergy:
    """Oracle AI + Alpaca integration for adaptive scoring"""
    
    def __init__(
        self, 
        market_data_provider: MarketDataProvider,
        broker: Broker,
        scoring_engine: EnhancedScoringEngine,
        feature_calculator: AdvancedIntradayCalculator
    ):
        self.market_data_provider = market_data_provider
        self.broker = broker
        self.scoring_engine = scoring_engine
        self.feature_calculator = feature_calculator
        self.logger = logging.getLogger(__name__)
        
        # Oracle AI models
        self.oracle_models = {}
        self.oracle_scalers = {}
        self.oracle_performance = {}
        
        # Adaptive learning
        self.adaptive_weights = {
            "base_score": 0.3,
            "ml_score": 0.4,
            "oracle_score": 0.3
        }
        
        # Market regime detection
        self.market_regimes = {
            "BULL": {"momentum_weight": 1.2, "risk_weight": 0.8},
            "BEAR": {"momentum_weight": 0.8, "risk_weight": 1.2},
            "SIDEWAYS": {"momentum_weight": 1.0, "risk_weight": 1.0},
            "VOLATILE": {"momentum_weight": 0.9, "risk_weight": 1.1}
        }
        
        # Performance tracking
        self.performance_history = []
        self.insight_accuracy = {}
        
        # Load Oracle models
        self._load_oracle_models()
    
    async def generate_adaptive_score(
        self, 
        symbol: str, 
        side: str, 
        features: AdvancedFeatures
    ) -> AdaptiveScore:
        """Generate adaptive score with Oracle AI enhancement"""
        
        try:
            # Get base scores
            base_pick_score = await self.scoring_engine.calculate_enhanced_score(symbol, side, features)
            
            # Generate Oracle insights
            oracle_insights = await self._generate_oracle_insights(symbol, features, side)
            
            # Calculate Oracle score
            oracle_score, oracle_confidence = await self._calculate_oracle_score(oracle_insights)
            
            # Detect market regime
            market_regime = await self._detect_market_regime()
            
            # Calculate adaptive adjustments
            adjustments = await self._calculate_adaptive_adjustments(
                features, market_regime, oracle_insights
            )
            
            # Calculate final adaptive score
            adaptive_score = self._calculate_adaptive_score(
                base_pick_score, oracle_score, adjustments
            )
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                adaptive_score, oracle_confidence, base_pick_score.prediction_confidence
            )
            
            return AdaptiveScore(
                symbol=symbol,
                side=side,
                base_score=base_pick_score.base_score,
                ml_score=base_pick_score.ml_score,
                oracle_score=oracle_score,
                oracle_confidence=oracle_confidence,
                market_regime_adjustment=adjustments["market_regime"],
                volatility_adjustment=adjustments["volatility"],
                liquidity_adjustment=adjustments["liquidity"],
                adaptive_score=adaptive_score,
                confidence_interval=confidence_interval,
                insights=oracle_insights,
                model_version="oracle_v2.1",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Adaptive scoring failed for {symbol}: {e}")
            # Return fallback score
            return AdaptiveScore(
                symbol=symbol,
                side=side,
                base_score=0.5,
                ml_score=0.5,
                oracle_score=0.5,
                oracle_confidence=0.5,
                market_regime_adjustment=0.0,
                volatility_adjustment=0.0,
                liquidity_adjustment=0.0,
                adaptive_score=0.5,
                confidence_interval=(0.3, 0.7),
                insights=[],
                model_version="fallback",
                last_updated=datetime.now()
            )
    
    async def _generate_oracle_insights(
        self, 
        symbol: str, 
        features: AdvancedFeatures, 
        side: str
    ) -> List[OracleInsight]:
        """Generate Oracle AI insights"""
        
        insights = []
        
        # Momentum insights
        momentum_insight = await self._analyze_momentum(symbol, features, side)
        if momentum_insight:
            insights.append(momentum_insight)
        
        # Volume insights
        volume_insight = await self._analyze_volume(symbol, features, side)
        if volume_insight:
            insights.append(volume_insight)
        
        # Technical insights
        technical_insight = await self._analyze_technical(symbol, features, side)
        if technical_insight:
            insights.append(technical_insight)
        
        # Sentiment insights
        sentiment_insight = await self._analyze_sentiment(symbol, features, side)
        if sentiment_insight:
            insights.append(sentiment_insight)
        
        # Risk insights
        risk_insight = await self._analyze_risk(symbol, features, side)
        if risk_insight:
            insights.append(risk_insight)
        
        return insights
    
    async def _analyze_momentum(self, symbol: str, features: AdvancedFeatures, side: str) -> Optional[OracleInsight]:
        """Analyze momentum patterns"""
        
        try:
            momentum_data = features.price_momentum
            
            if not momentum_data:
                return None
            
            # Extract momentum values
            momentum_5 = momentum_data.get("momentum_5", 0)
            momentum_10 = momentum_data.get("momentum_10", 0)
            momentum_20 = momentum_data.get("momentum_20", 0)
            
            # Analyze momentum pattern
            momentum_trend = "ACCELERATING" if momentum_5 > momentum_10 > momentum_20 else "DECELERATING"
            momentum_strength = abs(momentum_5) + abs(momentum_10) + abs(momentum_20)
            
            # Generate insight
            if side == "LONG":
                if momentum_5 > 0.01 and momentum_trend == "ACCELERATING":
                    insight_text = f"Oracle: {symbol} showing strong bullish momentum acceleration. 5m momentum {momentum_5:.2%} exceeds 10m {momentum_10:.2%}, indicating increasing buying pressure."
                    confidence = min(0.95, momentum_strength * 10)
                    impact_score = momentum_5 * 100
                elif momentum_5 < -0.01:
                    insight_text = f"Oracle: {symbol} showing bearish momentum divergence. Recent 5m momentum {momentum_5:.2%} suggests potential reversal risk for long positions."
                    confidence = min(0.95, abs(momentum_5) * 10)
                    impact_score = -abs(momentum_5) * 100
                else:
                    return None
            else:  # SHORT
                if momentum_5 < -0.01 and momentum_trend == "ACCELERATING":
                    insight_text = f"Oracle: {symbol} showing strong bearish momentum acceleration. 5m momentum {momentum_5:.2%} exceeds 10m {momentum_10:.2%}, indicating increasing selling pressure."
                    confidence = min(0.95, momentum_strength * 10)
                    impact_score = abs(momentum_5) * 100
                elif momentum_5 > 0.01:
                    insight_text = f"Oracle: {symbol} showing bullish momentum divergence. Recent 5m momentum {momentum_5:.2%} suggests potential reversal risk for short positions."
                    confidence = min(0.95, abs(momentum_5) * 10)
                    impact_score = -abs(momentum_5) * 100
                else:
                    return None
            
            return OracleInsight(
                symbol=symbol,
                insight_type="MOMENTUM",
                insight_text=insight_text,
                confidence=confidence,
                impact_score=impact_score,
                time_horizon="SHORT",
                supporting_evidence=[
                    f"5m momentum: {momentum_5:.2%}",
                    f"10m momentum: {momentum_10:.2%}",
                    f"20m momentum: {momentum_20:.2%}",
                    f"Momentum trend: {momentum_trend}"
                ],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Momentum analysis failed for {symbol}: {e}")
            return None
    
    async def _analyze_volume(self, symbol: str, features: AdvancedFeatures, side: str) -> Optional[OracleInsight]:
        """Analyze volume patterns"""
        
        try:
            volume_data = features.volume_profile
            
            if not volume_data:
                return None
            
            # Extract volume metrics
            rvol_10 = volume_data.get("rvol_10", 1.0)
            volume_spike = volume_data.get("volume_spike", 1.0)
            vwap_distance = volume_data.get("vwap_distance_10", 0.0)
            
            # Analyze volume pattern
            volume_confirmation = rvol_10 > 1.5 and volume_spike > 1.2
            volume_divergence = abs(vwap_distance) > 0.01
            
            # Generate insight
            if volume_confirmation:
                if side == "LONG" and vwap_distance > 0:
                    insight_text = f"Oracle: {symbol} showing strong volume confirmation for bullish move. {rvol_10:.1f}x relative volume with price above VWAP by {vwap_distance:.2%}, indicating institutional buying."
                    confidence = min(0.95, rvol_10 / 3)
                    impact_score = rvol_10 * 10
                elif side == "SHORT" and vwap_distance < 0:
                    insight_text = f"Oracle: {symbol} showing strong volume confirmation for bearish move. {rvol_10:.1f}x relative volume with price below VWAP by {vwap_distance:.2%}, indicating institutional selling."
                    confidence = min(0.95, rvol_10 / 3)
                    impact_score = rvol_10 * 10
                else:
                    return None
            elif volume_divergence:
                insight_text = f"Oracle: {symbol} showing volume-price divergence. Price movement not supported by volume, suggesting potential reversal."
                confidence = 0.7
                impact_score = -20
            else:
                return None
            
            return OracleInsight(
                symbol=symbol,
                insight_type="VOLUME",
                insight_text=insight_text,
                confidence=confidence,
                impact_score=impact_score,
                time_horizon="SHORT",
                supporting_evidence=[
                    f"Relative volume: {rvol_10:.1f}x",
                    f"Volume spike: {volume_spike:.1f}x",
                    f"VWAP distance: {vwap_distance:.2%}",
                    f"Volume confirmation: {volume_confirmation}"
                ],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Volume analysis failed for {symbol}: {e}")
            return None
    
    async def _analyze_technical(self, symbol: str, features: AdvancedFeatures, side: str) -> Optional[OracleInsight]:
        """Analyze technical indicators"""
        
        try:
            oscillators = features.oscillators
            trend_indicators = features.trend_indicators
            
            if not oscillators or not trend_indicators:
                return None
            
            # Extract technical metrics
            rsi_14 = oscillators.get("rsi_14", 50)
            macd_signal = trend_indicators.get("macd_signal", 0)
            bb_position = trend_indicators.get("bb_position", 0.5)
            
            # Analyze technical setup
            rsi_extreme = rsi_14 > 70 or rsi_14 < 30
            macd_bullish = macd_signal > 0.1
            macd_bearish = macd_signal < -0.1
            bb_extreme = bb_position > 0.8 or bb_position < 0.2
            
            # Generate insight
            if side == "LONG":
                if rsi_14 < 30 and macd_bullish:
                    insight_text = f"Oracle: {symbol} showing oversold bounce setup. RSI {rsi_14:.1f} indicates oversold conditions with MACD signal {macd_signal:.3f} showing bullish divergence."
                    confidence = 0.85
                    impact_score = 30
                elif bb_position < 0.2 and macd_bullish:
                    insight_text = f"Oracle: {symbol} showing Bollinger Band bounce setup. Price at {bb_position:.1%} of BB range with MACD confirmation, suggesting mean reversion opportunity."
                    confidence = 0.8
                    impact_score = 25
                elif rsi_extreme:
                    insight_text = f"Oracle: {symbol} showing extreme RSI {rsi_14:.1f} suggesting potential reversal risk for long positions."
                    confidence = 0.75
                    impact_score = -15
                else:
                    return None
            else:  # SHORT
                if rsi_14 > 70 and macd_bearish:
                    insight_text = f"Oracle: {symbol} showing overbought rejection setup. RSI {rsi_14:.1f} indicates overbought conditions with MACD signal {macd_signal:.3f} showing bearish divergence."
                    confidence = 0.85
                    impact_score = 30
                elif bb_position > 0.8 and macd_bearish:
                    insight_text = f"Oracle: {symbol} showing Bollinger Band rejection setup. Price at {bb_position:.1%} of BB range with MACD confirmation, suggesting mean reversion opportunity."
                    confidence = 0.8
                    impact_score = 25
                elif rsi_extreme:
                    insight_text = f"Oracle: {symbol} showing extreme RSI {rsi_14:.1f} suggesting potential reversal risk for short positions."
                    confidence = 0.75
                    impact_score = -15
                else:
                    return None
            
            return OracleInsight(
                symbol=symbol,
                insight_type="TECHNICAL",
                insight_text=insight_text,
                confidence=confidence,
                impact_score=impact_score,
                time_horizon="MEDIUM",
                supporting_evidence=[
                    f"RSI(14): {rsi_14:.1f}",
                    f"MACD signal: {macd_signal:.3f}",
                    f"BB position: {bb_position:.1%}",
                    f"RSI extreme: {rsi_extreme}"
                ],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Technical analysis failed for {symbol}: {e}")
            return None
    
    async def _analyze_sentiment(self, symbol: str, features: AdvancedFeatures, side: str) -> Optional[OracleInsight]:
        """Analyze market sentiment"""
        
        try:
            macro_features = features.macro_features
            
            if not macro_features:
                return None
            
            # Extract sentiment metrics
            economic_sentiment = macro_features.get("economic_sentiment", 0.5)
            risk_appetite = macro_features.get("risk_appetite", 0.5)
            liquidity_conditions = macro_features.get("liquidity_conditions", 0.5)
            
            # Analyze sentiment
            bullish_sentiment = economic_sentiment > 0.6 and risk_appetite > 0.6
            bearish_sentiment = economic_sentiment < 0.4 and risk_appetite < 0.4
            liquidity_support = liquidity_conditions > 0.7
            
            # Generate insight
            if bullish_sentiment and liquidity_support:
                if side == "LONG":
                    insight_text = f"Oracle: {symbol} benefiting from positive macro sentiment. Economic sentiment {economic_sentiment:.1%} and risk appetite {risk_appetite:.1%} support bullish thesis with strong liquidity conditions."
                    confidence = 0.8
                    impact_score = 20
                else:
                    insight_text = f"Oracle: {symbol} facing headwinds from positive macro sentiment. Strong economic sentiment and risk appetite may limit downside potential for short positions."
                    confidence = 0.7
                    impact_score = -10
            elif bearish_sentiment:
                if side == "SHORT":
                    insight_text = f"Oracle: {symbol} supported by negative macro sentiment. Economic sentiment {economic_sentiment:.1%} and risk appetite {risk_appetite:.1%} create favorable environment for bearish thesis."
                    confidence = 0.8
                    impact_score = 20
                else:
                    insight_text = f"Oracle: {symbol} facing headwinds from negative macro sentiment. Weak economic sentiment and risk appetite may limit upside potential for long positions."
                    confidence = 0.7
                    impact_score = -10
            else:
                return None
            
            return OracleInsight(
                symbol=symbol,
                insight_type="SENTIMENT",
                insight_text=insight_text,
                confidence=confidence,
                impact_score=impact_score,
                time_horizon="LONG",
                supporting_evidence=[
                    f"Economic sentiment: {economic_sentiment:.1%}",
                    f"Risk appetite: {risk_appetite:.1%}",
                    f"Liquidity conditions: {liquidity_conditions:.1%}",
                    f"Bullish sentiment: {bullish_sentiment}"
                ],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Sentiment analysis failed for {symbol}: {e}")
            return None
    
    async def _analyze_risk(self, symbol: str, features: AdvancedFeatures, side: str) -> Optional[OracleInsight]:
        """Analyze risk factors"""
        
        try:
            volatility_features = features.volatility_features
            microstructure = features.microstructure
            
            if not volatility_features or not microstructure:
                return None
            
            # Extract risk metrics
            volatility_5 = volatility_features.get("volatility_5", 0.02)
            spread_bps = microstructure.get("spread_bps", 5.0)
            price_volume_correlation = microstructure.get("price_volume_correlation", 0.0)
            
            # Analyze risk factors
            high_volatility = volatility_5 > 0.03
            wide_spreads = spread_bps > 10
            low_correlation = abs(price_volume_correlation) < 0.3
            
            # Generate insight
            risk_factors = []
            risk_score = 0
            
            if high_volatility:
                risk_factors.append(f"High volatility: {volatility_5:.2%}")
                risk_score += 20
            
            if wide_spreads:
                risk_factors.append(f"Wide spreads: {spread_bps:.1f} bps")
                risk_score += 15
            
            if low_correlation:
                risk_factors.append(f"Low price-volume correlation: {price_volume_correlation:.2f}")
                risk_score += 10
            
            if risk_factors:
                insight_text = f"Oracle: {symbol} showing elevated risk factors: {', '.join(risk_factors)}. Consider reducing position size or tightening stops."
                confidence = min(0.95, risk_score / 50)
                impact_score = -risk_score
                
                return OracleInsight(
                    symbol=symbol,
                    insight_type="RISK",
                    insight_text=insight_text,
                    confidence=confidence,
                    impact_score=impact_score,
                    time_horizon="SHORT",
                    supporting_evidence=risk_factors,
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Risk analysis failed for {symbol}: {e}")
            return None
    
    async def _calculate_oracle_score(self, insights: List[OracleInsight]) -> Tuple[float, float]:
        """Calculate Oracle score from insights"""
        
        if not insights:
            return 0.5, 0.3
        
        # Weight insights by type
        type_weights = {
            "MOMENTUM": 0.3,
            "VOLUME": 0.25,
            "TECHNICAL": 0.25,
            "SENTIMENT": 0.15,
            "RISK": 0.05
        }
        
        weighted_score = 0
        total_weight = 0
        confidence_scores = []
        
        for insight in insights:
            weight = type_weights.get(insight.insight_type, 0.1)
            weighted_score += insight.impact_score * weight * insight.confidence
            total_weight += weight
            confidence_scores.append(insight.confidence)
        
        if total_weight == 0:
            return 0.5, 0.3
        
        oracle_score = weighted_score / total_weight
        oracle_score = max(0, min(1, (oracle_score + 50) / 100))  # Normalize to 0-1
        
        oracle_confidence = np.mean(confidence_scores) if confidence_scores else 0.3
        
        return oracle_score, oracle_confidence
    
    async def _detect_market_regime(self) -> str:
        """Detect current market regime"""
        
        try:
            # Get market data for regime detection
            # This would integrate with real market data
            vix_level = 18.5  # Mock VIX level
            treasury_yield = 4.2  # Mock treasury yield
            
            # Simple regime detection logic
            if vix_level > 25:
                return "VOLATILE"
            elif vix_level < 15 and treasury_yield > 4.0:
                return "BULL"
            elif vix_level > 20 and treasury_yield < 3.5:
                return "BEAR"
            else:
                return "SIDEWAYS"
                
        except Exception as e:
            self.logger.error(f"❌ Market regime detection failed: {e}")
            return "SIDEWAYS"
    
    async def _calculate_adaptive_adjustments(
        self, 
        features: AdvancedFeatures, 
        market_regime: str, 
        insights: List[OracleInsight]
    ) -> Dict[str, float]:
        """Calculate adaptive adjustments"""
        
        # Market regime adjustment
        regime_params = self.market_regimes.get(market_regime, self.market_regimes["SIDEWAYS"])
        market_regime_adj = (regime_params["momentum_weight"] - 1.0) * 0.1
        
        # Volatility adjustment
        volatility_features = features.volatility_features
        volatility_5 = volatility_features.get("volatility_5", 0.02) if volatility_features else 0.02
        volatility_adj = -min(0.1, volatility_5 * 2)  # Penalty for high volatility
        
        # Liquidity adjustment
        microstructure = features.microstructure
        spread_bps = microstructure.get("spread_bps", 5.0) if microstructure else 5.0
        liquidity_adj = -min(0.05, spread_bps / 200)  # Penalty for wide spreads
        
        return {
            "market_regime": market_regime_adj,
            "volatility": volatility_adj,
            "liquidity": liquidity_adj
        }
    
    def _calculate_adaptive_score(
        self, 
        base_pick_score: PickScore, 
        oracle_score: float, 
        adjustments: Dict[str, float]
    ) -> float:
        """Calculate final adaptive score"""
        
        # Base adaptive score
        adaptive_score = (
            base_pick_score.base_score * self.adaptive_weights["base_score"] +
            base_pick_score.ml_score * self.adaptive_weights["ml_score"] +
            oracle_score * self.adaptive_weights["oracle_score"]
        )
        
        # Apply adjustments
        total_adjustment = sum(adjustments.values())
        adaptive_score += total_adjustment
        
        # Ensure score is within bounds
        adaptive_score = max(0, min(1, adaptive_score))
        
        return adaptive_score
    
    def _calculate_confidence_interval(
        self, 
        adaptive_score: float, 
        oracle_confidence: float, 
        base_confidence: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval"""
        
        # Combine confidence scores
        combined_confidence = (oracle_confidence + base_confidence) / 2
        
        # Calculate interval width
        interval_width = (1 - combined_confidence) * 0.3
        
        lower_bound = max(0, adaptive_score - interval_width)
        upper_bound = min(1, adaptive_score + interval_width)
        
        return lower_bound, upper_bound
    
    def _load_oracle_models(self):
        """Load Oracle AI models"""
        
        model_dir = "backend/models/oracle"
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        # Load Oracle models for different insight types
        oracle_model_types = ["momentum", "volume", "technical", "sentiment", "risk"]
        
        for model_type in oracle_model_types:
            model_path = os.path.join(model_dir, f"oracle_{model_type}.joblib")
            scaler_path = os.path.join(model_dir, f"oracle_{model_type}_scaler.joblib")
            
            try:
                if os.path.exists(model_path):
                    self.oracle_models[model_type] = joblib.load(model_path)
                    self.logger.info(f"✅ Loaded Oracle {model_type} model")
                
                if os.path.exists(scaler_path):
                    self.oracle_scalers[model_type] = joblib.load(scaler_path)
                    
            except Exception as e:
                self.logger.warning(f"Failed to load Oracle {model_type} model: {e}")
    
    async def train_oracle_models(self, training_data: List[Dict[str, Any]]):
        """Train Oracle AI models"""
        
        try:
            self.logger.info("🤖 Training Oracle AI models...")
            
            # Prepare training data
            df = pd.DataFrame(training_data)
            
            # Train models for each insight type
            for model_type in ["momentum", "volume", "technical", "sentiment", "risk"]:
                try:
                    # Prepare features and targets for this model type
                    feature_columns = [col for col in df.columns if col.startswith(f"{model_type}_")]
                    target_column = f"{model_type}_score"
                    
                    if target_column not in df.columns or len(feature_columns) == 0:
                        continue
                    
                    X = df[feature_columns].fillna(0)
                    y = df[target_column].fillna(0)
                    
                    if len(X) < 50:  # Need minimum data
                        continue
                    
                    # Train model
                    model = RandomForestRegressor(n_estimators=100, random_state=42)
                    model.fit(X, y)
                    
                    # Store model
                    self.oracle_models[model_type] = model
                    
                    # Calculate performance
                    y_pred = model.predict(X)
                    r2 = np.corrcoef(y, y_pred)[0, 1] ** 2
                    
                    self.oracle_performance[model_type] = {
                        'r2_score': r2,
                        'last_trained': datetime.now()
                    }
                    
                    self.logger.info(f"✅ Trained Oracle {model_type} model: R²={r2:.3f}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to train Oracle {model_type} model: {e}")
            
            # Save models
            self._save_oracle_models()
            
        except Exception as e:
            self.logger.error(f"❌ Oracle model training failed: {e}")
    
    def _save_oracle_models(self):
        """Save Oracle AI models"""
        
        model_dir = "backend/models/oracle"
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        for model_type, model in self.oracle_models.items():
            try:
                model_path = os.path.join(model_dir, f"oracle_{model_type}.joblib")
                joblib.dump(model, model_path)
                
                if model_type in self.oracle_scalers:
                    scaler_path = os.path.join(model_dir, f"oracle_{model_type}_scaler.joblib")
                    joblib.dump(self.oracle_scalers[model_type], scaler_path)
                
                self.logger.info(f"✅ Saved Oracle {model_type} model")
                
            except Exception as e:
                self.logger.error(f"Failed to save Oracle {model_type} model: {e}")


# Factory function
async def create_oracle_alpaca_synergy(
    alpaca_api_key: str,
    alpaca_secret: str,
    polygon_api_key: str
) -> OracleAlpacaSynergy:
    """Create Oracle + Alpaca synergy system"""
    
    from ..broker.adapters.alpaca_paper import AlpacaPaperBroker
    from ..market.providers.polygon import PolygonProvider
    from .enhanced_scoring import EnhancedScoringEngine
    from .advanced_features import AdvancedIntradayCalculator
    
    # Create components
    broker = AlpacaPaperBroker(
        api_key_id=alpaca_api_key,
        api_secret_key=alpaca_secret
    )
    
    market_provider = PolygonProvider(api_key=polygon_api_key)
    scoring_engine = EnhancedScoringEngine(market_provider)
    feature_calculator = AdvancedIntradayCalculator(market_provider)
    
    # Create synergy system
    synergy = OracleAlpacaSynergy(
        market_data_provider=market_provider,
        broker=broker,
        scoring_engine=scoring_engine,
        feature_calculator=feature_calculator
    )
    
    return synergy
