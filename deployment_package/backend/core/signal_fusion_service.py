"""
Multi-Signal Fusion Service
Real-time signal updates and notifications
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q
from .models import Stock, User
from .hybrid_ml_predictor import hybrid_predictor
from .consumer_strength_service import ConsumerStrengthService
from .spending_habits_service import SpendingHabitsService
try:
    from .ml_service import MLService
except ImportError:
    MLService = None
import asyncio

logger = logging.getLogger(__name__)


class SignalFusionService:
    """Service for real-time multi-signal fusion and notifications"""
    
    CACHE_TTL = 300  # 5 minutes
    
    def __init__(self):
        self.consumer_strength_service = ConsumerStrengthService()
        self.spending_service = SpendingHabitsService()
        try:
            self.ml_service = MLService() if MLService else None
        except Exception as e:
            logger.warning(f"MLService not available: {e}")
            self.ml_service = None
    
    def get_signal_updates(
        self,
        symbol: str,
        user_id: Optional[int] = None,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get real-time signal updates for a stock
        
        Returns:
        {
            'symbol': str,
            'timestamp': datetime,
            'signals': {
                'spending': {...},
                'options': {...},
                'earnings': {...},
                'insider': {...},
            },
            'fusion_score': float,  # Combined signal strength
            'alerts': [...],  # List of alerts/notifications
            'recommendation': str,  # 'BUY', 'SELL', 'HOLD'
        }
        """
        cache_key = f"signal_updates:{symbol}:{user_id or 'anon'}:{lookback_hours}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Get spending analysis if user is authenticated
            spending_analysis = None
            if user_id:
                try:
                    spending_analysis = self.spending_service.analyze_spending_habits(user_id, months=3)
                except Exception as e:
                    logger.warning(f"Error getting spending analysis for user {user_id}: {e}")
                    spending_analysis = None
            
            # Get Consumer Strength Score (includes all signals)
            consumer_strength = None
            try:
                consumer_strength = self.consumer_strength_service.calculate_consumer_strength(
                    symbol, spending_analysis, user_id
                )
            except Exception as e:
                logger.warning(f"Error calculating consumer strength for {symbol}: {e}")
                # Use default consumer strength
                consumer_strength = {
                    'overall_score': 50.0,
                    'spending_score': 50.0,
                    'options_score': 50.0,
                    'earnings_score': 50.0,
                    'insider_score': 50.0,
                    'spending_growth': 0.0,
                }
            
            # Get spending features
            spending_features = {}
            if spending_analysis and self.ml_service:
                try:
                    spending_features = self.ml_service._get_spending_features_for_ticker(
                        symbol, spending_analysis
                    )
                except Exception as e:
                    logger.warning(f"Error getting spending features for {symbol}: {e}")
                    spending_features = {}
            
            # Get hybrid model prediction with timeout
            prediction = None
            contributions = {}
            try:
                # Try to get existing event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is already running, we can't use run_until_complete
                        # Skip the prediction for now (will use fallback)
                        logger.warning(f"Event loop is already running, skipping hybrid predictor for {symbol}")
                        prediction = None
                        contributions = {}
                    else:
                        # Loop exists but not running, we can use it
                        prediction = loop.run_until_complete(
                            asyncio.wait_for(
                                hybrid_predictor.predict(symbol, spending_features),
                                timeout=5.0
                            )
                        )
                        contributions = prediction.get('feature_contributions', {}) if prediction else {}
                except RuntimeError:
                    # No event loop exists, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        prediction = loop.run_until_complete(
                            asyncio.wait_for(
                                hybrid_predictor.predict(symbol, spending_features),
                                timeout=5.0
                            )
                        )
                        contributions = prediction.get('feature_contributions', {}) if prediction else {}
                    finally:
                        loop.close()
            except asyncio.TimeoutError:
                logger.warning(f"Hybrid predictor timeout for {symbol} after 5s. Using fallback.")
                prediction = None
                contributions = {}
            except Exception as e:
                logger.warning(f"Hybrid predictor error for {symbol}: {e}. Using fallback.", exc_info=True)
                prediction = None
                contributions = {}
            
            signals = {
                'spending': {
                    'score': consumer_strength.get('spending_score', 50.0),
                    'growth': consumer_strength.get('spending_growth', 0.0),
                    'trend': self._determine_trend(consumer_strength.get('spending_growth', 0.0)),
                    'strength': 'strong' if consumer_strength.get('spending_score', 50.0) >= 70 else 'moderate' if consumer_strength.get('spending_score', 50.0) >= 50 else 'weak',
                },
                'options': {
                    'score': consumer_strength.get('options_score', 50.0),
                    'trend': self._determine_trend(consumer_strength.get('options_score', 50.0) - 50.0),
                    'strength': 'strong' if consumer_strength.get('options_score', 50.0) >= 70 else 'moderate' if consumer_strength.get('options_score', 50.0) >= 50 else 'weak',
                },
                'earnings': {
                    'score': consumer_strength.get('earnings_score', 50.0),
                    'trend': self._determine_trend(consumer_strength.get('earnings_score', 50.0) - 50.0),
                    'strength': 'strong' if consumer_strength.get('earnings_score', 50.0) >= 70 else 'moderate' if consumer_strength.get('earnings_score', 50.0) >= 50 else 'weak',
                },
                'insider': {
                    'score': consumer_strength.get('insider_score', 50.0),
                    'trend': self._determine_trend(consumer_strength.get('insider_score', 50.0) - 50.0),
                    'strength': 'strong' if consumer_strength.get('insider_score', 50.0) >= 70 else 'moderate' if consumer_strength.get('insider_score', 50.0) >= 50 else 'weak',
                },
            }
            
            # Calculate fusion score (weighted combination)
            fusion_score = (
                0.40 * signals['spending']['score'] +
                0.30 * signals['options']['score'] +
                0.20 * signals['earnings']['score'] +
                0.10 * signals['insider']['score']
            )
            
            # Generate alerts
            alerts = self._generate_alerts(signals, fusion_score, consumer_strength)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(fusion_score, signals)
            
            result = {
                'symbol': symbol,
                'timestamp': timezone.now().isoformat(),
                'signals': signals,
                'fusion_score': round(fusion_score, 1),
                'alerts': alerts,
                'recommendation': recommendation,
                'consumer_strength': consumer_strength.get('overall_score', 50.0),
            }
            
            cache.set(cache_key, result, self.CACHE_TTL)
            return result
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Error getting signal updates for {symbol}: {error_type}: {error_msg}", exc_info=True)
            # Return fallback data with error information
            return {
                'symbol': symbol,
                'timestamp': timezone.now().isoformat(),
                'signals': {
                    'spending': {'score': 50.0, 'growth': 0.0, 'trend': 'stable', 'strength': 'moderate'},
                    'options': {'score': 50.0, 'trend': 'stable', 'strength': 'moderate'},
                    'earnings': {'score': 50.0, 'trend': 'stable', 'strength': 'moderate'},
                    'insider': {'score': 50.0, 'trend': 'stable', 'strength': 'moderate'},
                },
                'fusion_score': 50.0,
                'alerts': [{
                    'type': 'service_error',
                    'severity': 'low',
                    'message': f'Signal data temporarily unavailable ({error_type}). Please try again later.',
                    'timestamp': timezone.now().isoformat(),
                }],
                'recommendation': 'HOLD',
                'consumer_strength': 50.0,
                'error': error_msg,  # Include error for debugging
            }
    
    def get_watchlist_signals(
        self,
        user_id: int,
        threshold: float = 70.0
    ) -> List[Dict[str, Any]]:
        """
        Get signal updates for all stocks in user's watchlist
        
        Returns list of stocks with strong signals (above threshold)
        """
        try:
            from .models import Watchlist
            
            watchlist = Watchlist.objects.filter(user_id=user_id).select_related('stock')
            
            strong_signals = []
            for item in watchlist:
                symbol = item.stock.symbol
                updates = self.get_signal_updates(symbol, user_id)
                
                if updates.get('fusion_score', 0) >= threshold:
                    strong_signals.append({
                        'symbol': symbol,
                        'company_name': item.stock.company_name,
                        'fusion_score': updates.get('fusion_score', 0),
                        'recommendation': updates.get('recommendation', 'HOLD'),
                        'alerts': updates.get('alerts', []),
                    })
            
            # Sort by fusion score
            strong_signals.sort(key=lambda x: x['fusion_score'], reverse=True)
            
            return strong_signals
            
        except Exception as e:
            logger.error(f"Error getting watchlist signals for user {user_id}: {e}", exc_info=True)
            return []
    
    def _determine_trend(self, value: float) -> str:
        """Determine trend direction from value"""
        if value > 5:
            return 'increasing'
        elif value < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_alerts(
        self,
        signals: Dict[str, Any],
        fusion_score: float,
        consumer_strength: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate alerts based on signal strength"""
        alerts = []
        
        # Strong fusion score alert
        if fusion_score >= 75:
            alerts.append({
                'type': 'strong_buy_signal',
                'severity': 'high',
                'message': f'Strong multi-signal buy signal detected (Score: {fusion_score:.1f}/100)',
                'timestamp': timezone.now().isoformat(),
            })
        elif fusion_score <= 25:
            alerts.append({
                'type': 'strong_sell_signal',
                'severity': 'high',
                'message': f'Strong multi-signal sell signal detected (Score: {fusion_score:.1f}/100)',
                'timestamp': timezone.now().isoformat(),
            })
        
        # Spending growth alert
        spending_growth = consumer_strength.get('spending_growth', 0.0)
        if spending_growth > 20:
            alerts.append({
                'type': 'spending_surge',
                'severity': 'medium',
                'message': f'Consumer spending surge detected: {spending_growth:.1f}% growth',
                'timestamp': timezone.now().isoformat(),
            })
        elif spending_growth < -15:
            alerts.append({
                'type': 'spending_decline',
                'severity': 'medium',
                'message': f'Consumer spending decline: {spending_growth:.1f}% decrease',
                'timestamp': timezone.now().isoformat(),
            })
        
        # Options flow alert
        options_score = signals['options']['score']
        if options_score >= 75:
            alerts.append({
                'type': 'strong_options_flow',
                'severity': 'medium',
                'message': 'Strong institutional options flow detected',
                'timestamp': timezone.now().isoformat(),
            })
        
        # Earnings alert
        earnings_score = signals['earnings']['score']
        if earnings_score >= 75:
            alerts.append({
                'type': 'positive_earnings_signal',
                'severity': 'medium',
                'message': 'Positive earnings surprise history detected',
                'timestamp': timezone.now().isoformat(),
            })
        
        # Insider activity alert
        insider_score = signals['insider']['score']
        if insider_score >= 75:
            alerts.append({
                'type': 'insider_buying',
                'severity': 'medium',
                'message': 'Significant insider buying activity detected',
                'timestamp': timezone.now().isoformat(),
            })
        
        return alerts
    
    def _generate_recommendation(
        self,
        fusion_score: float,
        signals: Dict[str, Any]
    ) -> str:
        """Generate recommendation based on fusion score and signals"""
        if fusion_score >= 70:
            return 'BUY'
        elif fusion_score >= 50:
            # Check if multiple signals are strong
            strong_count = sum(1 for s in signals.values() if s.get('score', 0) >= 70)
            if strong_count >= 2:
                return 'BUY'
            return 'HOLD'
        elif fusion_score >= 30:
            return 'HOLD'
        else:
            return 'SELL'
    
    def get_portfolio_signals(
        self,
        user_id: int,
        threshold: float = 60.0
    ) -> Dict[str, Any]:
        """
        Get signal updates for all stocks in user's portfolio
        
        Returns:
        {
            'portfolio_signals': [...],
            'strong_buy_count': int,
            'strong_sell_count': int,
            'overall_sentiment': str,
        }
        """
        try:
            from .models import Portfolio
            
            portfolios = Portfolio.objects.filter(user_id=user_id, shares__gt=0).select_related('stock')
            
            portfolio_signals = []
            strong_buy_count = 0
            strong_sell_count = 0
            
            for portfolio in portfolios:
                symbol = portfolio.stock.symbol
                updates = self.get_signal_updates(symbol, user_id)
                
                fusion_score = updates.get('fusion_score', 50.0)
                recommendation = updates.get('recommendation', 'HOLD')
                
                portfolio_signals.append({
                    'symbol': symbol,
                    'company_name': portfolio.stock.company_name,
                    'shares': portfolio.shares,
                    'fusion_score': fusion_score,
                    'recommendation': recommendation,
                    'alerts': updates.get('alerts', []),
                })
                
                if fusion_score >= threshold and recommendation == 'BUY':
                    strong_buy_count += 1
                elif fusion_score < (100 - threshold) and recommendation == 'SELL':
                    strong_sell_count += 1
            
            # Determine overall sentiment
            if strong_buy_count > strong_sell_count:
                overall_sentiment = 'bullish'
            elif strong_sell_count > strong_buy_count:
                overall_sentiment = 'bearish'
            else:
                overall_sentiment = 'neutral'
            
            return {
                'portfolio_signals': portfolio_signals,
                'strong_buy_count': strong_buy_count,
                'strong_sell_count': strong_sell_count,
                'overall_sentiment': overall_sentiment,
                'total_positions': len(portfolio_signals),
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio signals for user {user_id}: {e}", exc_info=True)
            return {
                'portfolio_signals': [],
                'strong_buy_count': 0,
                'strong_sell_count': 0,
                'overall_sentiment': 'neutral',
                'total_positions': 0,
            }

