"""
Consumer Strength Score Service
Enhanced tracking with historical data and sector-specific scores
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Avg, Max, Min, Q
from .models import Stock
from .spending_habits_service import SpendingHabitsService
from .hybrid_ml_predictor import hybrid_predictor
try:
    from .ml_service import MLService
except ImportError:
    MLService = None
import asyncio

logger = logging.getLogger(__name__)


class ConsumerStrengthService:
    """Service for tracking and analyzing Consumer Strength Scores"""
    
    CACHE_TTL = 3600  # 1 hour
    
    def __init__(self):
        self.spending_service = SpendingHabitsService()
        try:
            self.ml_service = MLService() if MLService else None
        except Exception as e:
            logger.warning(f"MLService not available: {e}")
            self.ml_service = None
    
    def calculate_consumer_strength(
        self,
        symbol: str,
        spending_analysis: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive Consumer Strength Score with all components
        
        Returns:
        {
            'overall_score': float (0-100),
            'spending_score': float (0-100),
            'options_score': float (0-100),
            'earnings_score': float (0-100),
            'insider_score': float (0-100),
            'spending_growth': float (percentage),
            'sector_score': float (0-100),  # Sector-specific score
            'historical_trend': str,  # 'increasing', 'decreasing', 'stable'
            'components': {
                'spending': {...},
                'options': {...},
                'earnings': {...},
                'insider': {...}
            }
        }
        """
        cache_key = f"consumer_strength:{symbol}:{user_id or 'anon'}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Get spending features
            if spending_analysis is None and user_id:
                spending_analysis = self.spending_service.analyze_spending_habits(user_id, months=3)
            
            spending_features = {}
            if spending_analysis and self.ml_service:
                try:
                    spending_features = self.ml_service._get_spending_features_for_ticker(
                        symbol, spending_analysis
                    )
                except Exception as e:
                    logger.warning(f"Error getting spending features for {symbol}: {e}")
                    spending_features = {}
            
            # Try to get hybrid model prediction, but fallback to real API data if models not trained
            spending_score_raw = 0.0
            options_score_raw = 0.0
            earnings_score_raw = 0.0
            insider_score_raw = 0.0
            
            try:
                # Use asyncio.run for better compatibility
                prediction = asyncio.run(
                    asyncio.wait_for(
                        hybrid_predictor.predict(symbol, spending_features),
                        timeout=3.0
                    )
                )
                
                # Extract component scores from prediction
                contributions = prediction.get('feature_contributions', {})
                if contributions and any(v != 0.0 for v in contributions.values()):
                    spending_score_raw = contributions.get('spending', 0.0)
                    options_score_raw = contributions.get('options', 0.0)
                    earnings_score_raw = contributions.get('earnings', 0.0)
                    insider_score_raw = contributions.get('insider', 0.0)
                    logger.info(f"✅ Got scores from hybrid predictor for {symbol}")
            except (asyncio.TimeoutError, Exception) as e:
                logger.info(f"Hybrid predictor not available for {symbol}, using real API data: {e}")
            
            # If all scores are still 0, calculate from real data
            if spending_score_raw == 0.0 and options_score_raw == 0.0 and earnings_score_raw == 0.0 and insider_score_raw == 0.0:
                logger.info(f"Calculating scores from real API data for {symbol}")
                try:
                    scores = asyncio.run(
                        self._calculate_scores_from_real_data(symbol, spending_features)
                    )
                    spending_score_raw, options_score_raw, earnings_score_raw, insider_score_raw = scores
                except Exception as e:
                    logger.warning(f"Error calculating from real data: {e}")
            
            # Normalize to 0-100 scale
            spending_score = max(0, min(100, (spending_score_raw + 0.2) / 0.4 * 100))
            options_score = max(0, min(100, (options_score_raw + 0.2) / 0.4 * 100))
            earnings_score = max(0, min(100, (earnings_score_raw + 0.2) / 0.4 * 100))
            insider_score = max(0, min(100, (insider_score_raw + 0.2) / 0.4 * 100))
            
            # Calculate weighted overall score
            overall_score = (
                0.40 * spending_score +  # Spending: 40%
                0.30 * options_score +   # Options: 30%
                0.20 * earnings_score +  # Earnings: 20%
                0.10 * insider_score     # Insider: 10%
            )
            
            # Get spending growth
            spending_growth = spending_features.get('spending_change_4w', 0.0) * 100
            
            # Get sector-specific score
            sector_score = self._calculate_sector_score(symbol, spending_analysis)
            
            # Get historical trend
            historical_trend = self._get_historical_trend(symbol, user_id)
            
            result = {
                'overall_score': round(overall_score, 1),
                'spending_score': round(spending_score, 1),
                'options_score': round(options_score, 1),
                'earnings_score': round(earnings_score, 1),
                'insider_score': round(insider_score, 1),
                'spending_growth': round(spending_growth, 2),
                'sector_score': round(sector_score, 1),
                'historical_trend': historical_trend,
                'components': {
                    'spending': {
                        'score': spending_score,
                        'growth': spending_growth,
                        'weight': 0.40
                    },
                    'options': {
                        'score': options_score,
                        'weight': 0.30
                    },
                    'earnings': {
                        'score': earnings_score,
                        'weight': 0.20
                    },
                    'insider': {
                        'score': insider_score,
                        'weight': 0.10
                    }
                },
                'timestamp': timezone.now().isoformat()
            }
            
            cache.set(cache_key, result, self.CACHE_TTL)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating consumer strength for {symbol}: {e}", exc_info=True)
            return self._get_default_score()
    
    def _calculate_sector_score(
        self,
        symbol: str,
        spending_analysis: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate sector-specific Consumer Strength Score"""
        try:
            stock = Stock.objects.get(symbol=symbol)
            sector = stock.sector or "Unknown"
            
            if not spending_analysis:
                return 50.0  # Default
            
            # Get sector preferences from spending
            sector_weights = self.spending_service.get_spending_based_stock_preferences(
                spending_analysis
            )
            
            # Base score from sector alignment
            sector_alignment = sector_weights.get(sector, 0.0)
            sector_score = 50.0 + (sector_alignment * 50.0)  # Scale to 0-100
            
            # Boost if spending growth in this sector
            top_categories = spending_analysis.get('top_categories', [])
            for cat in top_categories[:5]:
                if sector.lower() in cat.get('category', '').lower():
                    growth = cat.get('growth_pct', 0.0)
                    if growth > 0:
                        sector_score = min(100, sector_score + (growth * 0.5))
            
            return max(0, min(100, sector_score))
            
        except Stock.DoesNotExist:
            return 50.0
        except Exception as e:
            logger.warning(f"Error calculating sector score for {symbol}: {e}")
            return 50.0
    
    def _get_historical_trend(
        self,
        symbol: str,
        user_id: Optional[int] = None
    ) -> str:
        """Determine historical trend of Consumer Strength Score"""
        # In a real implementation, this would query historical scores
        # For now, we'll use a simple heuristic based on recent predictions
        
        # TODO: Implement historical tracking table
        # For now, return 'stable' as default
        return 'stable'
    
    def get_historical_scores(
        self,
        symbol: str,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical Consumer Strength Scores
        
        Returns list of scores over time:
        [
            {'date': '2024-01-01', 'score': 75.5, 'spending_score': 80, ...},
            ...
        ]
        """
        # TODO: Implement historical tracking
        # For now, return current score as single data point
        current_score = self.calculate_consumer_strength(symbol, user_id=user_id)
        return [{
            'date': timezone.now().date().isoformat(),
            'score': current_score['overall_score'],
            'spending_score': current_score['spending_score'],
            'options_score': current_score['options_score'],
            'earnings_score': current_score['earnings_score'],
            'insider_score': current_score['insider_score'],
            'sector_score': current_score['sector_score'],
        }]
    
    def get_sector_comparison(
        self,
        symbol: str,
        spending_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare this stock's Consumer Strength to sector average
        
        Returns:
        {
            'stock_score': float,
            'sector_average': float,
            'sector_rank': int,  # 1 = best, N = worst
            'percentile': float,  # 0-100
            'sector_name': str
        }
        """
        try:
            stock = Stock.objects.get(symbol=symbol)
            sector = stock.sector or "Unknown"
            
            # Get stock's score
            stock_score = self.calculate_consumer_strength(
                symbol, spending_analysis
            )['overall_score']
            
            # Get all stocks in same sector
            sector_stocks = Stock.objects.filter(sector=sector).exclude(symbol=symbol)[:20]
            
            # Calculate sector average (simplified - would need full calculation)
            sector_scores = []
            for s in sector_stocks[:10]:  # Limit to 10 for performance
                try:
                    score = self.calculate_consumer_strength(
                        s.symbol, spending_analysis
                    )['overall_score']
                    sector_scores.append(score)
                except Exception:
                    continue
            
            sector_average = sum(sector_scores) / len(sector_scores) if sector_scores else 50.0
            
            # Calculate rank and percentile
            all_scores = [stock_score] + sector_scores
            all_scores.sort(reverse=True)
            rank = all_scores.index(stock_score) + 1
            percentile = (1 - (rank - 1) / len(all_scores)) * 100 if all_scores else 50.0
            
            return {
                'stock_score': stock_score,
                'sector_average': round(sector_average, 1),
                'sector_rank': rank,
                'percentile': round(percentile, 1),
                'sector_name': sector,
                'total_in_sector': len(all_scores)
            }
            
        except Stock.DoesNotExist:
            return {
                'stock_score': 50.0,
                'sector_average': 50.0,
                'sector_rank': 1,
                'percentile': 50.0,
                'sector_name': 'Unknown',
                'total_in_sector': 1
            }
        except Exception as e:
            logger.error(f"Error getting sector comparison for {symbol}: {e}")
            return {
                'stock_score': 50.0,
                'sector_average': 50.0,
                'sector_rank': 1,
                'percentile': 50.0,
                'sector_name': 'Unknown',
                'total_in_sector': 1
            }
    
    async def _calculate_scores_from_real_data(
        self,
        symbol: str,
        spending_features: Dict[str, float]
    ) -> tuple:
        """
        Calculate scores directly from real API data when ML models aren't available
        Returns: (spending_score, options_score, earnings_score, insider_score)
        """
        try:
            # Get real data from APIs
            from .hybrid_ml_predictor import OptionsFlowFeatures, EarningsInsiderFeatures
            
            options_features = OptionsFlowFeatures()
            earnings_insider = EarningsInsiderFeatures()
            
            # Get options features (real API data)
            options_feat = await options_features.get_options_features(symbol)
            # Calculate options score from put/call ratio and unusual volume
            put_call_ratio = options_feat.get('put_call_ratio', 1.0)
            unusual_volume = options_feat.get('unusual_volume_pct', 0.0)
            # Lower put/call ratio = more bullish = higher score
            # Higher unusual volume = more activity = higher score
            options_score_raw = (1.0 - min(put_call_ratio, 2.0) / 2.0) * 0.3 + min(unusual_volume, 1.0) * 0.2
            
            # Get earnings features (real API data)
            earnings_feat = await earnings_insider.get_earnings_features(symbol)
            # Calculate earnings score from surprise history
            surprise_avg = earnings_feat.get('earnings_surprise_avg', 0.0)
            positive_rate = earnings_feat.get('positive_surprise_rate', 0.5)
            # Positive surprises = higher score
            earnings_score_raw = (surprise_avg + 0.1) * 0.5 + (positive_rate - 0.5) * 0.3
            
            # Get insider features (real API data)
            insider_feat = await earnings_insider.get_insider_features(symbol)
            # Calculate insider score from buy/sell ratio
            buy_ratio = insider_feat.get('insider_buy_ratio', 0.5)
            buy_value_ratio = insider_feat.get('insider_buy_value_ratio', 0.5)
            # More buying = higher score
            insider_score_raw = (buy_ratio - 0.5) * 0.4 + (buy_value_ratio - 0.5) * 0.3
            
            # Calculate spending score from spending features
            spending_growth = spending_features.get('spending_change_4w', 0.0)
            spending_score_raw = spending_growth * 0.5  # Scale spending growth to score
            
            logger.info(f"✅ Calculated real scores for {symbol}: spending={spending_score_raw:.3f}, options={options_score_raw:.3f}, earnings={earnings_score_raw:.3f}, insider={insider_score_raw:.3f}")
            
            return (spending_score_raw, options_score_raw, earnings_score_raw, insider_score_raw)
            
        except Exception as e:
            logger.warning(f"Error calculating scores from real data for {symbol}: {e}")
            # Return neutral scores (will normalize to 50)
            return (0.0, 0.0, 0.0, 0.0)
    
    async def _calculate_scores_from_real_data(
        self,
        symbol: str,
        spending_features: Dict[str, float]
    ) -> tuple:
        """
        Calculate scores directly from real API data when ML models aren't available
        Returns: (spending_score, options_score, earnings_score, insider_score)
        """
        try:
            # Get real data from APIs
            from .hybrid_ml_predictor import OptionsFlowFeatures, EarningsInsiderFeatures
            
            options_features = OptionsFlowFeatures()
            earnings_insider = EarningsInsiderFeatures()
            
            # Get options features (real API data)
            options_feat = await options_features.get_options_features(symbol)
            # Calculate options score from put/call ratio and unusual volume
            put_call_ratio = options_feat.get('put_call_ratio', 1.0)
            unusual_volume = options_feat.get('unusual_volume_pct', 0.0)
            # Lower put/call ratio = more bullish = higher score
            # Higher unusual volume = more activity = higher score
            options_score_raw = (1.0 - min(put_call_ratio, 2.0) / 2.0) * 0.3 + min(unusual_volume, 1.0) * 0.2
            
            # Get earnings features (real API data)
            earnings_feat = await earnings_insider.get_earnings_features(symbol)
            # Calculate earnings score from surprise history
            surprise_avg = earnings_feat.get('earnings_surprise_avg', 0.0)
            positive_rate = earnings_feat.get('positive_surprise_rate', 0.5)
            # Positive surprises = higher score
            earnings_score_raw = (surprise_avg + 0.1) * 0.5 + (positive_rate - 0.5) * 0.3
            
            # Get insider features (real API data)
            insider_feat = await earnings_insider.get_insider_features(symbol)
            # Calculate insider score from buy/sell ratio
            buy_ratio = insider_feat.get('insider_buy_ratio', 0.5)
            buy_value_ratio = insider_feat.get('insider_buy_value_ratio', 0.5)
            # More buying = higher score
            insider_score_raw = (buy_ratio - 0.5) * 0.4 + (buy_value_ratio - 0.5) * 0.3
            
            # Calculate spending score from spending features
            spending_growth = spending_features.get('spending_change_4w', 0.0)
            spending_score_raw = spending_growth * 0.5  # Scale spending growth to score
            
            logger.info(f"✅ Calculated real scores for {symbol}: spending={spending_score_raw:.3f}, options={options_score_raw:.3f}, earnings={earnings_score_raw:.3f}, insider={insider_score_raw:.3f}")
            
            return (spending_score_raw, options_score_raw, earnings_score_raw, insider_score_raw)
            
        except Exception as e:
            logger.warning(f"Error calculating scores from real data for {symbol}: {e}")
            # Return neutral scores (will normalize to 50)
            return (0.0, 0.0, 0.0, 0.0)
    
    def _get_default_score(self) -> Dict[str, Any]:
        """Return default score when calculation fails"""
        return {
            'overall_score': 50.0,
            'spending_score': 50.0,
            'options_score': 50.0,
            'earnings_score': 50.0,
            'insider_score': 50.0,
            'spending_growth': 0.0,
            'sector_score': 50.0,
            'historical_trend': 'stable',
            'components': {
                'spending': {'score': 50.0, 'growth': 0.0, 'weight': 0.40},
                'options': {'score': 50.0, 'weight': 0.30},
                'earnings': {'score': 50.0, 'weight': 0.20},
                'insider': {'score': 50.0, 'weight': 0.10}
            },
            'timestamp': timezone.now().isoformat()
        }

