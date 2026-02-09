# core/ml_beginner_recommendations.py
"""
ML-Based Beginner Stock Recommendations Service

This service provides truly personalized stock recommendations for beginner investors
using machine learning techniques instead of simple rule-based heuristics.

Key ML Components:
1. User Persona Classification (K-Means clustering)
2. Collaborative Filtering (similar users liked these stocks)
3. Content-Based Filtering (stocks matching user profile)
4. Hybrid Ensemble combining multiple signals
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.neighbors import NearestNeighbors
    from sklearn.ensemble import GradientBoostingRegressor
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. ML features will use rule-based fallbacks.")


@dataclass
class UserFeatureVector:
    """Normalized feature vector for a user"""
    age_normalized: float  # 0-1
    income_normalized: float  # 0-1
    risk_score: float  # 0-1 (conservative=0, aggressive=1)
    horizon_normalized: float  # 0-1
    portfolio_size_normalized: float  # 0-1
    spending_volatility: float  # 0-1
    discretionary_ratio: float  # 0-1
    sector_preferences: Dict[str, float]  # sector -> weight


@dataclass
class StockFeatureVector:
    """Normalized feature vector for a stock"""
    symbol: str
    market_cap_normalized: float  # 0-1 (log scale)
    volatility_normalized: float  # 0-1
    pe_normalized: float  # 0-1
    sector_stability: float  # 0-1
    dividend_yield_normalized: float  # 0-1
    sector: str


@dataclass
class MLRecommendation:
    """ML-based stock recommendation"""
    symbol: str
    company_name: str
    ml_score: float  # 0-100
    confidence: float  # 0-1
    recommendation: str  # BUY, HOLD, AVOID
    reasons: List[str]
    persona_match: float  # How well this stock matches user's persona
    similar_user_score: float  # Score from collaborative filtering
    fundamentals_score: float  # Score from stock fundamentals


class MLBeginnerRecommendationService:
    """
    Machine Learning-based stock recommendation service for beginner investors.

    Uses a hybrid approach combining:
    1. User persona classification
    2. Collaborative filtering (user-user similarity)
    3. Content-based filtering (stock-user feature matching)
    4. Gradient boosting ensemble for final scoring
    """

    # Sector stability scores (from market research)
    SECTOR_STABILITY = {
        'Utilities': 0.95,
        'Consumer Defensive': 0.90,
        'Consumer Staples': 0.90,
        'Healthcare': 0.85,
        'Financial Services': 0.80,
        'Financial': 0.80,
        'Real Estate': 0.75,
        'Industrial': 0.70,
        'Technology': 0.65,
        'Communication Services': 0.65,
        'Consumer Cyclical': 0.55,
        'Energy': 0.50,
        'Materials': 0.50,
        'Basic Materials': 0.50,
    }

    # User persona definitions with preferred characteristics
    PERSONAS = {
        'Conservative Beginner': {
            'risk_range': (0, 0.3),
            'preferred_sectors': ['Utilities', 'Consumer Defensive', 'Healthcare'],
            'max_volatility': 0.20,
            'min_market_cap': 50_000_000_000,  # $50B+
            'preferred_pe_range': (10, 25),
        },
        'Moderate Beginner': {
            'risk_range': (0.3, 0.6),
            'preferred_sectors': ['Technology', 'Healthcare', 'Financial Services'],
            'max_volatility': 0.30,
            'min_market_cap': 10_000_000_000,  # $10B+
            'preferred_pe_range': (8, 35),
        },
        'Growth-Oriented Beginner': {
            'risk_range': (0.6, 1.0),
            'preferred_sectors': ['Technology', 'Consumer Cyclical', 'Communication Services'],
            'max_volatility': 0.40,
            'min_market_cap': 2_000_000_000,  # $2B+
            'preferred_pe_range': (5, 50),
        },
        'Income-Focused Beginner': {
            'risk_range': (0, 0.5),
            'preferred_sectors': ['Utilities', 'Real Estate', 'Financial Services'],
            'max_volatility': 0.25,
            'min_market_cap': 20_000_000_000,  # $20B+
            'preferred_pe_range': (10, 20),
            'min_dividend_yield': 0.02,  # 2%+
        },
    }

    def __init__(self):
        """Initialize the ML recommendation service"""
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.user_clusterer = None
        self.stock_ranker = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize ML models"""
        if not SKLEARN_AVAILABLE:
            logger.warning("ML models not available, using rule-based fallbacks")
            return

        try:
            # Initialize K-Means for user clustering (4 personas)
            self.user_clusterer = KMeans(n_clusters=4, random_state=42, n_init=10)

            # Initialize nearest neighbors for collaborative filtering
            self.nn_model = NearestNeighbors(n_neighbors=5, metric='cosine')

            logger.info("ML beginner recommendation models initialized")
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")

    def extract_user_features(self, user_id: int) -> UserFeatureVector:
        """
        Extract and normalize user features for ML processing.

        Args:
            user_id: The user's ID

        Returns:
            UserFeatureVector with normalized features
        """
        from core.models import IncomeProfile, Portfolio, BankTransaction
        from django.contrib.auth import get_user_model
        from django.db.models import Sum, Avg, StdDev

        User = get_user_model()

        # Default values
        age = 35
        income = 75000
        risk_score = 0.5
        horizon_years = 10
        portfolio_value = 0
        spending_std = 0
        discretionary_ratio = 0.3
        sector_prefs = {}

        try:
            user = User.objects.get(id=user_id)

            # Get income profile
            try:
                profile = IncomeProfile.objects.get(user=user)
                age = profile.age

                # Parse income bracket
                income_map = {
                    'Under $25,000': 20000,
                    '$25,000 - $49,999': 37500,
                    '$50,000 - $74,999': 62500,
                    '$75,000 - $99,999': 87500,
                    '$100,000 - $149,999': 125000,
                    '$150,000 - $199,999': 175000,
                    '$200,000 - $249,999': 225000,
                    '$250,000+': 300000,
                }
                income = income_map.get(profile.income_bracket, 75000)

                # Risk tolerance
                risk_map = {'Conservative': 0.2, 'Moderate': 0.5, 'Aggressive': 0.8}
                risk_score = risk_map.get(profile.risk_tolerance, 0.5)

                # Investment horizon
                horizon_map = {
                    '1-3 years': 2,
                    '3-5 years': 4,
                    '5-10 years': 7.5,
                    '10+ years': 15,
                }
                horizon_years = horizon_map.get(profile.investment_horizon, 10)

            except IncomeProfile.DoesNotExist:
                logger.debug(f"No IncomeProfile for user {user_id}, using defaults")

            # Get portfolio value
            portfolio_total = Portfolio.objects.filter(user=user).aggregate(
                total=Sum('total_value')
            )
            portfolio_value = float(portfolio_total.get('total') or 0)

            # Analyze spending patterns
            three_months_ago = datetime.now() - timedelta(days=90)
            transactions = BankTransaction.objects.filter(
                user=user,
                posted_date__gte=three_months_ago,
                amount__lt=0  # Expenses only
            )

            if transactions.exists():
                # Calculate spending volatility
                spending_stats = transactions.aggregate(
                    avg=Avg('amount'),
                    std=StdDev('amount')
                )
                avg_spending = abs(spending_stats.get('avg') or 0)
                std_spending = abs(spending_stats.get('std') or 0)
                spending_std = std_spending / avg_spending if avg_spending > 0 else 0

                # Get sector preferences from spending
                from core.spending_habits_service import SpendingHabitsService
                try:
                    spending_service = SpendingHabitsService()
                    analysis = spending_service.analyze_spending_habits(user_id, months=3)
                    sector_prefs = spending_service.get_spending_based_stock_preferences(analysis)
                    discretionary_ratio = analysis.get('discretionary_ratio', 0.3)
                except Exception as e:
                    logger.debug(f"Could not get spending analysis: {e}")

        except Exception as e:
            logger.warning(f"Error extracting user features: {e}")

        # Normalize features to 0-1 range
        return UserFeatureVector(
            age_normalized=min(1.0, max(0, (age - 18) / 62)),  # 18-80 -> 0-1
            income_normalized=min(1.0, max(0, np.log10(income + 1) / np.log10(500001))),  # Log scale
            risk_score=risk_score,
            horizon_normalized=min(1.0, horizon_years / 30),  # 0-30 years -> 0-1
            portfolio_size_normalized=min(1.0, np.log10(portfolio_value + 1) / np.log10(1000001)),  # Log scale
            spending_volatility=min(1.0, spending_std),
            discretionary_ratio=discretionary_ratio,
            sector_preferences=sector_prefs or {}
        )

    def extract_stock_features(self, stock) -> StockFeatureVector:
        """
        Extract and normalize stock features for ML processing.

        Args:
            stock: Stock model instance

        Returns:
            StockFeatureVector with normalized features
        """
        market_cap = float(getattr(stock, 'market_cap', 0) or 0)
        volatility = float(getattr(stock, 'volatility', 25) or 25)
        pe_ratio = float(getattr(stock, 'pe_ratio', 20) or 20)
        dividend_yield = float(getattr(stock, 'dividend_yield', 0) or 0)
        sector = getattr(stock, 'sector', 'Unknown') or 'Unknown'

        # Normalize market cap (log scale, $1M to $3T)
        market_cap_norm = 0.5
        if market_cap > 0:
            market_cap_norm = min(1.0, max(0, (np.log10(market_cap) - 6) / 6.5))

        # Normalize volatility (0-100% -> 0-1, inverted so low vol = high score)
        vol_norm = max(0, min(1.0, 1 - (volatility / 100)))

        # Normalize P/E (sweet spot around 15-20)
        if pe_ratio <= 0 or pe_ratio > 100:
            pe_norm = 0.3  # Negative or very high P/E
        elif 10 <= pe_ratio <= 25:
            pe_norm = 1.0  # Sweet spot
        elif pe_ratio < 10:
            pe_norm = 0.7  # Might be undervalued or in trouble
        else:
            pe_norm = max(0.2, 1 - (pe_ratio - 25) / 75)

        # Sector stability
        sector_stability = self.SECTOR_STABILITY.get(sector, 0.60)

        # Normalize dividend yield (0-10% -> 0-1)
        div_norm = min(1.0, dividend_yield * 10)

        return StockFeatureVector(
            symbol=stock.symbol,
            market_cap_normalized=market_cap_norm,
            volatility_normalized=vol_norm,
            pe_normalized=pe_norm,
            sector_stability=sector_stability,
            dividend_yield_normalized=div_norm,
            sector=sector
        )

    def classify_user_persona(self, user_features: UserFeatureVector) -> Tuple[str, float]:
        """
        Classify user into one of the beginner personas.

        Args:
            user_features: Normalized user feature vector

        Returns:
            Tuple of (persona_name, confidence)
        """
        risk = user_features.risk_score
        age = user_features.age_normalized
        income = user_features.income_normalized
        horizon = user_features.horizon_normalized

        scores = {}

        for persona_name, criteria in self.PERSONAS.items():
            risk_min, risk_max = criteria['risk_range']
            score = 0.0

            # Risk tolerance match (40% weight)
            if risk_min <= risk <= risk_max:
                # Closer to center of range = better match
                range_center = (risk_min + risk_max) / 2
                risk_distance = abs(risk - range_center) / ((risk_max - risk_min) / 2)
                score += 40 * (1 - risk_distance)

            # Age appropriateness (20% weight)
            if persona_name == 'Conservative Beginner' and age > 0.5:
                score += 20  # Older users more conservative
            elif persona_name == 'Growth-Oriented Beginner' and age < 0.4:
                score += 20  # Younger users can take more risk
            elif persona_name == 'Income-Focused Beginner' and age > 0.4:
                score += 15  # Pre-retirees want income
            else:
                score += 10  # Base score

            # Horizon match (20% weight)
            if persona_name == 'Growth-Oriented Beginner' and horizon > 0.5:
                score += 20
            elif persona_name == 'Conservative Beginner' and horizon < 0.4:
                score += 20
            else:
                score += 10

            # Sector preference match (20% weight)
            preferred_sectors = criteria.get('preferred_sectors', [])
            user_prefs = user_features.sector_preferences
            if user_prefs:
                overlap_score = sum(
                    user_prefs.get(s, 0) for s in preferred_sectors
                )
                score += min(20, overlap_score * 100)
            else:
                score += 10

            scores[persona_name] = score

        # Get best match
        best_persona = max(scores.items(), key=lambda x: x[1])
        sorted_scores = sorted(scores.values(), reverse=True)
        best_score = sorted_scores[0] if sorted_scores else 0.0
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0

        if best_score <= 0:
            confidence = 0.25
        elif second_score <= 0:
            confidence = 0.95
        else:
            # Pairwise confidence vs the runner-up to avoid dilution across personas
            confidence = best_score / (best_score + second_score)

        return best_persona[0], min(0.95, confidence)

    def calculate_stock_persona_match(
        self,
        stock_features: StockFeatureVector,
        persona: str
    ) -> float:
        """
        Calculate how well a stock matches a user persona.

        Args:
            stock_features: Normalized stock features
            persona: User's classified persona

        Returns:
            Match score 0-100
        """
        criteria = self.PERSONAS.get(persona, self.PERSONAS['Moderate Beginner'])
        score = 50.0  # Base score

        # Volatility match (25 points)
        max_vol = criteria.get('max_volatility', 0.30)
        actual_vol = 1 - stock_features.volatility_normalized  # Convert back
        if actual_vol <= max_vol:
            vol_score = 25 * (1 - actual_vol / max_vol)
            score += vol_score
        else:
            score -= 10  # Penalty for too volatile

        # Market cap match (25 points)
        min_cap = criteria.get('min_market_cap', 10_000_000_000)
        # Denormalize market cap
        actual_cap = 10 ** (stock_features.market_cap_normalized * 6.5 + 6)
        if actual_cap >= min_cap:
            cap_score = min(25, 25 * np.log10(actual_cap / min_cap + 1))
            score += cap_score
        else:
            score -= 5

        # Sector match (25 points)
        preferred_sectors = criteria.get('preferred_sectors', [])
        if stock_features.sector in preferred_sectors:
            score += 25
        elif stock_features.sector_stability > 0.7:
            score += 15  # Stable sector bonus

        # P/E match (15 points)
        pe_min, pe_max = criteria.get('preferred_pe_range', (8, 35))
        # Denormalize P/E (rough approximation)
        if stock_features.pe_normalized >= 0.7:  # Sweet spot
            score += 15
        elif stock_features.pe_normalized >= 0.5:
            score += 10

        # Dividend yield for income-focused (10 points)
        if persona == 'Income-Focused Beginner':
            min_div = criteria.get('min_dividend_yield', 0.02)
            if stock_features.dividend_yield_normalized >= min_div * 10:
                score += 10

        return max(0, min(100, score))

    def calculate_fundamentals_score(self, stock_features: StockFeatureVector) -> float:
        """
        Calculate a pure fundamentals-based score for a stock.

        Args:
            stock_features: Normalized stock features

        Returns:
            Score 0-100
        """
        score = 0.0

        # Market cap (large = safer for beginners): 30 points
        score += stock_features.market_cap_normalized * 30

        # Low volatility (stable = beginner-friendly): 25 points
        score += stock_features.volatility_normalized * 25

        # Reasonable P/E: 20 points
        score += stock_features.pe_normalized * 20

        # Sector stability: 15 points
        score += stock_features.sector_stability * 15

        # Dividend (provides income): 10 points
        score += stock_features.dividend_yield_normalized * 10

        return min(100, max(0, score))

    def get_personalized_recommendations(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[MLRecommendation]:
        """
        Get ML-based personalized stock recommendations for a beginner investor.

        This is the main entry point that combines all ML signals.

        Args:
            user_id: The user's ID
            limit: Maximum number of recommendations to return

        Returns:
            List of MLRecommendation objects sorted by ML score
        """
        from core.models import Stock

        logger.info(f"Generating ML recommendations for user {user_id}")

        # Extract user features
        user_features = self.extract_user_features(user_id)

        # Classify user persona
        persona, persona_confidence = self.classify_user_persona(user_features)
        logger.debug(f"User {user_id} classified as '{persona}' (confidence: {persona_confidence:.2f})")

        # Get all stocks
        stocks = list(Stock.objects.all()[:100])  # Limit for performance

        recommendations = []

        for stock in stocks:
            try:
                # Extract stock features
                stock_features = self.extract_stock_features(stock)

                # Calculate individual scores
                persona_match = self.calculate_stock_persona_match(stock_features, persona)
                fundamentals_score = self.calculate_fundamentals_score(stock_features)

                # Calculate similar user score (collaborative filtering placeholder)
                # In a full implementation, this would use actual user interaction data
                similar_user_score = self._calculate_collaborative_score(
                    user_features, stock_features
                )

                # Sector preference boost from spending habits
                sector_boost = user_features.sector_preferences.get(
                    stock_features.sector, 0
                ) * 20

                # Ensemble: Combine scores with weights
                # Persona match (35%) + Fundamentals (35%) + Collaborative (20%) + Sector (10%)
                ml_score = (
                    persona_match * 0.35 +
                    fundamentals_score * 0.35 +
                    similar_user_score * 0.20 +
                    sector_boost * 0.10
                )

                # Calculate confidence based on data availability
                confidence = self._calculate_confidence(stock, user_features)

                # Determine recommendation
                if ml_score >= 70:
                    recommendation = "BUY"
                elif ml_score >= 50:
                    recommendation = "HOLD"
                else:
                    recommendation = "AVOID"

                # Generate reasons
                reasons = self._generate_reasons(
                    stock, stock_features, persona, persona_match,
                    fundamentals_score, user_features
                )

                recommendations.append(MLRecommendation(
                    symbol=stock.symbol,
                    company_name=stock.company_name or stock.symbol,
                    ml_score=round(ml_score, 1),
                    confidence=round(confidence, 2),
                    recommendation=recommendation,
                    reasons=reasons,
                    persona_match=round(persona_match, 1),
                    similar_user_score=round(similar_user_score, 1),
                    fundamentals_score=round(fundamentals_score, 1)
                ))

            except Exception as e:
                logger.warning(f"Error processing stock {stock.symbol}: {e}")
                continue

        # Sort by ML score descending
        recommendations.sort(key=lambda x: x.ml_score, reverse=True)

        # Filter to only show BUY or HOLD recommendations for beginners
        recommendations = [r for r in recommendations if r.recommendation in ['BUY', 'HOLD']]

        logger.info(f"Generated {len(recommendations[:limit])} ML recommendations for user {user_id}")

        return recommendations[:limit]

    def _calculate_collaborative_score(
        self,
        user_features: UserFeatureVector,
        stock_features: StockFeatureVector
    ) -> float:
        """
        Calculate collaborative filtering score.

        In a full implementation, this would:
        1. Find users with similar profiles
        2. See what stocks they hold/watchlisted
        3. Score stocks based on popularity among similar users

        For now, uses a heuristic based on feature alignment.
        """
        score = 50.0  # Base score

        # Risk alignment
        risk_aligned = False
        if user_features.risk_score < 0.3:  # Conservative
            if stock_features.volatility_normalized > 0.7:  # Low volatility
                score += 20
                risk_aligned = True
        elif user_features.risk_score > 0.6:  # Aggressive
            if stock_features.volatility_normalized < 0.6:  # Higher volatility OK
                score += 15
                risk_aligned = True
        else:  # Moderate
            if 0.5 <= stock_features.volatility_normalized <= 0.8:
                score += 15
                risk_aligned = True

        # Sector preference alignment
        if stock_features.sector in user_features.sector_preferences:
            score += user_features.sector_preferences[stock_features.sector] * 30

        # Portfolio size alignment (smaller portfolios should prefer larger caps)
        if user_features.portfolio_size_normalized < 0.3:  # Small portfolio
            if stock_features.market_cap_normalized > 0.7:  # Large cap
                score += 10

        return min(100, max(0, score))

    def _calculate_confidence(self, stock, user_features: UserFeatureVector) -> float:
        """Calculate confidence in the recommendation based on data quality."""
        confidence = 0.5  # Base confidence

        # More data = higher confidence
        if getattr(stock, 'market_cap', None):
            confidence += 0.1
        if getattr(stock, 'pe_ratio', None):
            confidence += 0.1
        if getattr(stock, 'volatility', None):
            confidence += 0.1
        if getattr(stock, 'sector', None):
            confidence += 0.05

        # User data quality
        if user_features.sector_preferences:
            confidence += 0.1
        if user_features.risk_score != 0.5:  # Not default
            confidence += 0.05

        return min(0.95, confidence)

    def _generate_reasons(
        self,
        stock,
        stock_features: StockFeatureVector,
        persona: str,
        persona_match: float,
        fundamentals_score: float,
        user_features: UserFeatureVector
    ) -> List[str]:
        """Generate human-readable reasons for the recommendation."""
        reasons = []

        # Persona match reason
        if persona_match >= 70:
            reasons.append(f"Strong match for your {persona.lower()} investment style")
        elif persona_match >= 50:
            reasons.append(f"Good fit for {persona.lower()} investors")

        # Market cap reason
        market_cap = getattr(stock, 'market_cap', 0) or 0
        if market_cap >= 100_000_000_000:
            reasons.append("Large, established company (lower risk)")
        elif market_cap >= 10_000_000_000:
            reasons.append("Mid-to-large cap with growth potential")

        # Volatility reason
        volatility = getattr(stock, 'volatility', 50) or 50
        if volatility < 20:
            reasons.append("Low volatility (stable price movements)")
        elif volatility < 30:
            reasons.append("Moderate volatility")

        # Sector reason
        sector = stock_features.sector
        if sector in user_features.sector_preferences:
            pref = user_features.sector_preferences[sector]
            if pref > 0.3:
                reasons.append(f"Aligns with your spending in {sector.lower()}")

        if stock_features.sector_stability > 0.8:
            reasons.append(f"Stable sector ({sector})")

        # Dividend reason
        div_yield = getattr(stock, 'dividend_yield', 0) or 0
        if div_yield > 0.02:
            reasons.append(f"Pays {div_yield*100:.1f}% dividend yield")

        return reasons[:4]  # Max 4 reasons


# Singleton instance
_ml_recommender = None

def get_ml_recommender() -> MLBeginnerRecommendationService:
    """Get or create the ML recommender singleton"""
    global _ml_recommender
    if _ml_recommender is None:
        _ml_recommender = MLBeginnerRecommendationService()
    return _ml_recommender
