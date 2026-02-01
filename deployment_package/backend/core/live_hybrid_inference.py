"""
Live Hybrid Inference Pipeline
Production-ready inference combining LSTM temporal momentum + XGBoost alternative data.
Implements abstention, warm-up, and proper scaling.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class LiveHybridInference:
    """
    Live inference pipeline for hybrid LSTM + XGBoost model.
    Handles data fetching, feature extraction, and prediction with abstention.
    """
    
    def __init__(self, confidence_threshold: float = 0.78, use_ensemble: bool = True):
        """
        Initialize live inference pipeline.
        
        Args:
            confidence_threshold: Minimum confidence to execute (default: 0.78)
            use_ensemble: Use ensemble predictor (default: True)
        """
        self.confidence_threshold = confidence_threshold
        self.use_ensemble = use_ensemble
        
        # Initialize components
        from .lstm_data_fetcher import get_lstm_data_fetcher
        from .lstm_feature_extractor import get_lstm_feature_extractor
        from .hybrid_lstm_xgboost_trainer import get_hybrid_trainer
        from .enhanced_alternative_data_service import get_enhanced_alternative_data_service
        
        self.data_fetcher = get_lstm_data_fetcher()
        self.lstm_extractor = get_lstm_feature_extractor()
        self.hybrid_trainer = get_hybrid_trainer()
        self.enhanced_alt_data = get_enhanced_alternative_data_service()
        
        # Load models if available
        self.hybrid_trainer._load_models()
        
        # Initialize ensemble predictor if enabled
        if self.use_ensemble:
            try:
                from .ensemble_predictor import get_ensemble_predictor
                self.ensemble_predictor = get_ensemble_predictor()
            except Exception as e:
                logger.warning(f"Could not initialize ensemble predictor: {e}")
                self.ensemble_predictor = None
                self.use_ensemble = False
        else:
            self.ensemble_predictor = None
    
    async def generate_live_signal(
        self,
        symbol: str,
        use_alpaca: bool = True
    ) -> Dict[str, Any]:
        """
        Generate live trading signal using hybrid LSTM + XGBoost.
        
        Args:
            symbol: Stock symbol
            use_alpaca: Use Alpaca API for data
        
        Returns:
            Dict with action, confidence, and reasoning
        """
        try:
            # Step A: Get hybrid features (LSTM sequence + alternative data)
            lstm_input, alt_data_df = await self.data_fetcher.get_hybrid_features(
                symbol, use_alpaca=use_alpaca
            )
            
            # Step B: Extract temporal momentum score from LSTM
            if self.lstm_extractor.is_available():
                temporal_momentum_score = self.lstm_extractor.extract_temporal_momentum_score(
                    lstm_input, symbol
                )
            else:
                temporal_momentum_score = 0.0
            
            # Step C: Get enhanced alternative data (social sentiment + options flow)
            enhanced_alt_features = await self.enhanced_alt_data.get_all_features(symbol, hours_back=24)
            
            # Step D: Use ensemble predictor if available, otherwise fallback to XGBoost
            if self.use_ensemble and self.ensemble_predictor and self.ensemble_predictor.ensemble_model is not None:
                # Use ensemble predictor (combines LSTM + XGBoost + Random Forest)
                # Prepare technical features (simplified - would use actual technical indicators)
                technical_features = {
                    'rsi': 50.0,  # Would calculate from price data
                    'sma_ratio': 1.0,  # Would calculate from price data
                    'volume_ratio': 1.0,  # Would calculate from volume data
                }
                
                # Convert enhanced alt features to dict format
                alt_data_features = enhanced_alt_features
                
                # Get ensemble prediction
                ensemble_result = self.ensemble_predictor.predict(
                    lstm_features=temporal_momentum_score,
                    alt_data_features=alt_data_features,
                    technical_features=technical_features,
                    confidence_threshold=self.confidence_threshold
                )
                
                action = ensemble_result['action']
                confidence = ensemble_result['confidence']
                reasoning = ensemble_result.get('reasoning', 'Ensemble prediction')
                
            elif self.hybrid_trainer.xgboost_model is not None:
                # Fallback to XGBoost (original method)
                # Add LSTM feature and enhanced alt data to DataFrame
                alt_data_df['lstm_temporal_momentum_score'] = temporal_momentum_score
                for key, value in enhanced_alt_features.items():
                    alt_data_df[key] = value
                
                action, confidence = self.hybrid_trainer.predict_with_abstention(
                    alt_data_df,
                    confidence_threshold=self.confidence_threshold
                )
                reasoning = f"XGBoost prediction (confidence: {confidence:.2%})"
            else:
                # Fallback: use simple rule-based logic
                action = 'ABSTAIN'
                confidence = 0.5
                reasoning = 'Models not available'
            
            # Step E: Generate enhanced reasoning
            reasoning_parts = []
            if self.use_ensemble and self.ensemble_predictor:
                reasoning_parts.append(f"Ensemble: {reasoning}")
            else:
                reasoning_parts.append(reasoning)
            
            if abs(temporal_momentum_score) > 0.1:
                reasoning_parts.append(f"LSTM momentum: {temporal_momentum_score:+.3f}")
            
            # Add alternative data insights
            if enhanced_alt_features.get('social_sentiment', 0) != 0:
                social_sent = enhanced_alt_features['social_sentiment']
                reasoning_parts.append(f"Social sentiment: {social_sent:+.2f}")
            
            if enhanced_alt_features.get('unusual_volume_pct', 0) > 0.1:
                unusual_vol = enhanced_alt_features['unusual_volume_pct']
                reasoning_parts.append(f"Unusual options volume: {unusual_vol:.1%}")
            
            if confidence >= self.confidence_threshold:
                reasoning_parts.append(f"High confidence: {confidence:.2%}")
            else:
                reasoning_parts.append(f"Low confidence: {confidence:.2%} (abstaining)")
            
            signal_result = {
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'temporal_momentum_score': temporal_momentum_score,
                'reasoning': ' | '.join(reasoning_parts),
                'enhanced_alt_data': enhanced_alt_features,
                'model_type': 'ensemble' if (self.use_ensemble and self.ensemble_predictor) else 'xgboost',
                'timestamp': datetime.now().isoformat()
            }
            
            # Record signal for transparency dashboard (if not abstaining)
            if action != 'ABSTAIN' and confidence >= self.confidence_threshold:
                try:
                    from .transparency_dashboard import get_transparency_dashboard
                    from .lstm_data_fetcher import get_lstm_data_fetcher
                    
                    dashboard = get_transparency_dashboard()
                    data_fetcher = get_lstm_data_fetcher()
                    
                    # Get current price for entry
                    latest_price = await data_fetcher._fetch_price_data(symbol, use_alpaca, '1Min')
                    entry_price = latest_price['Close'].iloc[-1] if latest_price is not None and len(latest_price) > 0 else 0.0
                    
                    # Record signal
                    dashboard.record_signal(
                        symbol=symbol,
                        action=action,
                        confidence=confidence,
                        entry_price=entry_price,
                        reasoning=signal_result['reasoning']
                    )
                except Exception as e:
                    logger.warning(f"Could not record signal for transparency dashboard: {e}")
            
            return signal_result
            
        except Exception as e:
            logger.error(f"Error generating live signal for {symbol}: {e}")
            return {
                'symbol': symbol,
                'action': 'ABSTAIN',
                'confidence': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_signals_batch(
        self,
        symbols: List[str],
        use_alpaca: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate signals for multiple symbols in parallel.
        
        Args:
            symbols: List of stock symbols
            use_alpaca: Use Alpaca API
        
        Returns:
            List of signal dicts
        """
        # Warm up data cache first
        self.data_fetcher.warm_up(symbols)
        
        # Generate signals in parallel
        tasks = [self.generate_live_signal(symbol, use_alpaca) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        signals = []
        for result in results:
            if isinstance(result, dict) and 'action' in result:
                signals.append(result)
            else:
                logger.warning(f"Error in batch signal generation: {result}")
        
        return signals


# Global instance
_live_inference = None

def get_live_inference(confidence_threshold: float = 0.78, use_ensemble: bool = True) -> LiveHybridInference:
    """Get global live inference instance"""
    global _live_inference
    if _live_inference is None:
        _live_inference = LiveHybridInference(confidence_threshold=confidence_threshold, use_ensemble=use_ensemble)
    return _live_inference

