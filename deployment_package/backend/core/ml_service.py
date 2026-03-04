"""
ML Service for Enhanced AI Portfolio Recommendations
Handles machine learning models for market analysis, portfolio optimization, and stock scoring
"""
import logging
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd

try:
    from .improved_ml_service import ImprovedMLService
except (ImportError, SyntaxError):
    ImprovedMLService = None

warnings.filterwarnings("ignore")

# ML imports
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, mean_squared_error
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    import statsmodels.api as sm
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose

    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")
    ML_AVAILABLE = False

# Production R² Model import
try:
    import os
    from .ml.model_registry import ModelRegistry as _ModelRegistry

    PRODUCTION_R2_AVAILABLE = _ModelRegistry.exists()
    if not PRODUCTION_R2_AVAILABLE:
        logging.info(
            "Production R² model not yet trained. "
            "Run ml.train.run_pipeline() to train and save it."
        )
except Exception as e:
    logging.warning(f"Production R² model registry unavailable: {e}")
    PRODUCTION_R2_AVAILABLE = False

logger = logging.getLogger(__name__)


class MLService:
    """
    Machine Learning service for enhanced AI portfolio recommendations
    """

    def __init__(self):
        self.ml_available = ML_AVAILABLE
        self.production_r2_available = PRODUCTION_R2_AVAILABLE

        if not self.ml_available:
            logger.warning("ML Service initialized in fallback mode")

        # Initialize models
        self.market_regime_model = None
        self.portfolio_optimizer = None
        self.stock_scorer = None
        self.scaler = StandardScaler()

        # Initialize production ML pipeline (new walk-forward LightGBM model)
        try:
            from .ml.model_registry import ModelRegistry
            self._model_registry = ModelRegistry
            self.production_r2_available = ModelRegistry.exists()
            if self.production_r2_available:
                logger.info("Production ML model available (ml_models/production_r2.pkl)")
            else:
                logger.info(
                    "Production ML model not yet trained — run ml.train.run_pipeline() "
                    "to build it. Falling back to standard ML scoring."
                )
        except Exception as exc:
            logger.warning("Could not load ModelRegistry: %s", exc)
            self._model_registry = None
            self.production_r2_available = False

        self.production_r2_model = None  # kept for backwards-compat attribute access

        # Model parameters
        self.model_params = {
            "market_regime": {
                "n_estimators": 100,
                "max_depth": 10,
                "random_state": 42,
            },
            "portfolio_optimization": {
                "n_estimators": 200,
                "max_depth": 15,
                "learning_rate": 0.1,
                "random_state": 42,
            },
        }

        # Enhanced market regime labels with granular detection
        self.regime_labels = [
            "early_bull_market",        # Strong growth, low volatility
            "late_bull_market",         # High growth, increasing volatility
            "correction",               # Temporary pullback in bull market
            "bear_market",              # Declining market
            "sideways_consolidation",   # Range-bound, low volatility
            "high_volatility",          # Uncertain, high volatility
            "recovery",                 # Bouncing back from decline
            "bubble_formation",         # Excessive optimism, high valuations
        ]

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check if ML capabilities are available"""
        return self.ml_available

    def predict_market_regime(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict market regime using ML models
        Args:
            market_data: Dictionary containing market indicators
        Returns:
            Dictionary with regime prediction and confidence
        """
        if not self.ml_available:
            return self._fallback_market_regime(market_data)

        try:
            # Extract features from market data
            features = self._extract_market_features(market_data)

            # Train model if not available
            if self.market_regime_model is None:
                self._train_market_regime_model()

            if self.market_regime_model is None:
                return self._fallback_market_regime(market_data)

            # Predict regime
            probs = self.market_regime_model.predict_proba([features])[0]
            prediction = probs.argmax()
            confidence = probs.max()
            regime = self.regime_labels[prediction]

            return {
                "regime": regime,
                "confidence": float(confidence),
                "all_probabilities": {
                    label: float(prob)
                    for label, prob in zip(self.regime_labels, probs)
                },
                "method": "ml_model",
            }
        except Exception as e:
            logger.error(f"Error in market regime prediction: {e}")
            return self._fallback_market_regime(market_data)

    def optimize_portfolio_allocation(
        self,
        user_profile: Dict[str, Any],
        market_conditions: Dict[str, Any],
        available_stocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Optimize portfolio allocation using ML-based optimization
        Args:
            user_profile: User's financial profile
            market_conditions: Current market conditions
            available_stocks: List of available stocks with metrics
        Returns:
            Optimized portfolio allocation
        """
        if not self.ml_available:
            return self._fallback_portfolio_optimization(
                user_profile, market_conditions
            )

        try:
            # Create feature matrix for optimization
            features = self._create_portfolio_features(
                user_profile, market_conditions, available_stocks
            )

            # Train portfolio optimizer if needed
            if self.portfolio_optimizer is None:
                self._train_portfolio_optimizer()

            if self.portfolio_optimizer is None:
                return self._fallback_portfolio_optimization(
                    user_profile, market_conditions
                )

            # Generate optimal allocation
            optimal_allocation = self._generate_optimal_allocation(
                features, user_profile
            )

            return {
                "allocation": optimal_allocation,
                "expected_return": self._calculate_ml_expected_return(
                    optimal_allocation, features
                ),
                "risk_score": self._calculate_ml_risk_score(
                    optimal_allocation, features
                ),
                "method": "ml_optimization",
            }
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return self._fallback_portfolio_optimization(
                user_profile, market_conditions
            )

    def score_stocks_production_r2(
        self,
        stocks: List[Dict[str, Any]],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Score stocks using the production R² model.

        Note: R² = 0.023 — this model explains ~2.3% of forward-return variance.
        That is weak by institutional standards (typical: 0.15–0.30) and should
        be treated as one low-confidence signal among several, not a primary
        ranking driver. Use in combination with FSS and regime signals.
        """
        if not self.production_r2_available or self._model_registry is None:
            logger.info(
                "Production ML model not available — falling back to standard ML scoring. "
                "Train it with: python -m deployment_package.backend.core.ml.train"
            )
            return self.score_stocks_ml(stocks, market_conditions, user_profile)

        try:
            import yfinance as yf
        except ImportError:
            logger.warning("yfinance not installed — cannot run production ML scoring")
            return self.score_stocks_ml(stocks, market_conditions, user_profile)

        scored_stocks: List[Dict[str, Any]] = []

        # Load model metadata once (avoids re-reading .pkl for each stock)
        try:
            meta = self._model_registry.metadata()
            fold_ic = meta.get("fold_metrics", {}).get("ic", None)
            horizon = meta.get("horizon", 20)
        except Exception:
            meta = {}
            fold_ic = None
            horizon = 20

        for stock in stocks:
            symbol = stock.get("symbol", stock.get("ticker", ""))
            if not symbol:
                continue

            try:
                # Fetch recent history for this ticker (need 252+ rows for features)
                ticker_df = yf.download(
                    symbol, period="2y", auto_adjust=True, progress=False
                )
                if ticker_df.empty or len(ticker_df) < 100:
                    raise ValueError(f"Insufficient history for {symbol}")

                # Normalise column names (yfinance returns Title Case)
                ticker_df.columns = [c.lower() for c in ticker_df.columns]

                # Attach SPY as cross-asset context
                spy_df = yf.download("SPY", period="2y", auto_adjust=True, progress=False)
                if not spy_df.empty:
                    spy_df.columns = [c.lower() for c in spy_df.columns]
                    ticker_df["spy_close"] = spy_df["close"].reindex(ticker_df.index)
                    ticker_df["spy_volume"] = spy_df["volume"].reindex(ticker_df.index)

                # Get prediction from registry
                raw_pred = self._model_registry.predict(ticker_df)

                # Map vol-adjusted prediction to 0-10 score.
                # Vol-adjusted returns typically range ±2.0 (±2σ), so:
                # pred=+2.0 → score=10, pred=0 → score=5, pred=-2.0 → score=0
                ml_score = max(0.0, min(10.0, 5.0 + raw_pred * 2.5))

                # Confidence: based on IC magnitude (if available)
                if fold_ic is not None and fold_ic > 0.05:
                    confidence = "medium"
                elif fold_ic is not None and fold_ic > 0.02:
                    confidence = "low"
                else:
                    confidence = "low"

                scored_stock = {
                    **stock,
                    "ml_score": float(ml_score),
                    "ml_confidence": confidence,
                    "ml_reasoning": (
                        f"Walk-forward LightGBM ({horizon}D vol-adj return): "
                        f"raw signal={raw_pred:.3f}"
                        + (f", mean OOS IC={fold_ic:.3f}" if fold_ic else "")
                    ),
                    "predicted_return": float(raw_pred),
                    "model_type": "production_lgbm_walkforward",
                }

            except Exception as exc:
                logger.warning("Could not score %s with production model: %s", symbol, exc)
                scored_stock = self._fallback_stock_scoring(
                    [stock], market_conditions, user_profile
                )[0]

            scored_stocks.append(scored_stock)

        scored_stocks.sort(key=lambda x: x.get("ml_score", 0), reverse=True)
        logger.info("Scored %d stocks using production walk-forward ML model", len(scored_stocks))
        return scored_stocks

    def score_stocks_ml(
        self,
        stocks: List[Dict[str, Any]],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any],
        spending_analysis: Optional[Dict[str, Any]] = None,
        use_fss: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Score stocks using the best available ML model with spending habits
        NOW INCLUDES SPENDING-BASED PREDICTIVE MODEL (Your Competitive Moat!)
        Args:
            stocks: List of stocks to score
            market_conditions: Current market conditions
            user_profile: User's financial profile
            spending_analysis: Optional spending habits analysis from transactions
        Returns:
            List of scored stocks with ML scores
        """
        # PRIORITY: Use spending-based predictor if available
        try:
            from .spending_trend_predictor import spending_predictor

            if spending_predictor.model is not None:
                logger.info(
                    "Using spending-based predictive model for stock scoring"
                )
                return self._score_with_spending_predictor(
                    stocks, market_conditions, user_profile, spending_analysis
                )
        except Exception as e:
            logger.warning(f"Spending predictor not available: {e}")

        # Use production R² model if available (best performance)
        if self.production_r2_available and self.production_r2_model:
            return self.score_stocks_production_r2(
                stocks, market_conditions, user_profile
            )

        if not self.ml_available:
            return self._fallback_stock_scoring(
                stocks, market_conditions, user_profile
            )

        try:
            # Optionally enhance with FSS v3.0 scores
            if use_fss:
                try:
                    from .fss_service import get_fss_service
                    import asyncio
                    
                    fss_service = get_fss_service()
                    symbols = [stock.get('symbol', '') for stock in stocks]
                    
                    # Get FSS scores (non-blocking if in async context)
                    try:
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            fss_results = loop.run_until_complete(
                                fss_service.get_stocks_fss(symbols)
                            )
                            
                            # Enhance stocks with FSS scores
                            for stock in stocks:
                                symbol = stock.get('symbol', '')
                                fss_data = fss_results.get(symbol)
                                if fss_data:
                                    stock['fss_score'] = fss_data.get('fss_score', 0)
                                    stock['fss_confidence'] = fss_data.get('confidence', 'low')
                                    stock['fss_regime'] = fss_data.get('regime', 'Unknown')
                                    # Blend FSS with ML score if available
                                    if 'ml_score' in stock:
                                        # Weighted blend: 60% FSS, 40% ML
                                        stock['ml_score'] = (
                                            0.6 * (fss_data.get('fss_score', 0) / 100.0) +
                                            0.4 * stock['ml_score']
                                        )
                    except RuntimeError:
                        logger.debug("FSS calculation skipped (no event loop)")
                except Exception as e:
                    logger.warning(f"FSS integration failed: {e}")
            
            # Try to use improved ML service first
            if ImprovedMLService is None:
                raise ImportError("ImprovedMLService not available")
            improved_ml = ImprovedMLService()
            if improved_ml.is_available():
                # Use improved ML service with real data and proper validation
                scored_stocks = improved_ml.score_stocks_improved(
                    stocks, market_conditions, user_profile
                )
                if scored_stocks:
                    logger.info("Used improved ML service for stock scoring")
                    return scored_stocks

            # Fallback to original method
            # Create feature matrix for stocks (enhanced with spending preferences)
            stock_features = self._create_stock_features(
                stocks, market_conditions, user_profile, spending_analysis
            )

            # Train stock scorer if needed
            if self.stock_scorer is None:
                self._train_stock_scorer()

            if self.stock_scorer is None:
                return self._fallback_stock_scoring(
                    stocks, market_conditions, user_profile
                )

            # Score stocks
            scores = self.stock_scorer.predict(stock_features)

            scored_stocks: List[Dict[str, Any]] = []
            for i, stock in enumerate(stocks):
                scored_stocks.append(
                    {
                        **stock,
                        "ml_score": float(scores[i]),
                        "ml_confidence": self._calculate_stock_confidence(
                            stock_features[i]
                        ),
                        "ml_reasoning": self._generate_ml_reasoning(
                            stock_features[i], scores[i]
                        ),
                    }
                )

            # Sort by ML score
            scored_stocks.sort(key=lambda x: x["ml_score"], reverse=True)
            return scored_stocks

        except Exception as e:
            logger.error(f"Error in improved ML service / stock scoring: {e}")
            return self._fallback_stock_scoring(
                stocks, market_conditions, user_profile
            )

    # -------------------------------------------------------------------------
    # Spending & hybrid scoring helpers
    # -------------------------------------------------------------------------

    def _score_with_spending_predictor(
        self,
        stocks: List[Dict[str, Any]],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any],
        spending_analysis: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score stocks using spending-based predictive model
        NOW WITH WEEK 2: Hybrid ensemble (spending + options + earnings + insider)
        """
        import asyncio

        # Try hybrid model first (Week 2)
        try:
            from .hybrid_ml_predictor import hybrid_predictor

            if hybrid_predictor.meta_learner is not None:
                logger.info(
                    "Using hybrid ensemble model (Week 2) for stock scoring"
                )
                return self._score_with_hybrid_model(
                    stocks, market_conditions, user_profile, spending_analysis
                )
        except Exception as e:
            logger.debug(
                f"Hybrid model not available, using spending-only: {e}"
            )

        # Fallback to spending-only model (Week 1)
        from .spending_trend_predictor import spending_predictor
        from .spending_habits_service import SpendingHabitsService

        scored_stocks: List[Dict[str, Any]] = []
        spending_service = SpendingHabitsService()

        for stock in stocks:
            symbol = stock.get("symbol", "").upper()

            # Get spending features for this ticker
            spending_features = self._get_spending_features_for_ticker(
                symbol, spending_analysis
            )

            # Predict using spending model
            prediction = spending_predictor.predict_stock_return(
                spending_features
            )

            # Combine with existing scores
            base_score = stock.get("beginner_friendly_score", 5.0) / 10.0
            spending_score = prediction["predicted_return"]

            # Normalize spending score to 0-1 range (assume returns in [-0.2, 0.2])
            spending_score_normalized = (spending_score + 0.2) / 0.4
            spending_score_normalized = max(
                0.0, min(1.0, spending_score_normalized)
            )

            # Weighted combination: 60% spending predictor, 40% base score
            final_score = 0.6 * spending_score_normalized + 0.4 * base_score

            scored_stocks.append(
                {
                    **stock,
                    "ml_score": float(final_score),
                    "spending_score": float(spending_score_normalized),
                    "predicted_excess_return_4w": prediction[
                        "predicted_return"
                    ],
                    "ml_confidence": prediction["confidence"],
                    "ml_reasoning": (
                        f"Spending-based prediction: {prediction['reasoning']}"
                    ),
                    "spending_insights": prediction.get("top_features", {}),
                }
            )

        scored_stocks.sort(key=lambda x: x["ml_score"], reverse=True)
        return scored_stocks

    def _score_with_hybrid_model(
        self,
        stocks: List[Dict[str, Any]],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any],
        spending_analysis: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score stocks using Week 2 hybrid ensemble model
        Combines: Spending + Options Flow + Earnings + Insider signals
        """
        import asyncio
        from .hybrid_ml_predictor import hybrid_predictor

        scored_stocks: List[Dict[str, Any]] = []

        for stock in stocks:
            symbol = stock.get("symbol", "").upper()

            # Get spending features
            spending_features = self._get_spending_features_for_ticker(
                symbol, spending_analysis
            )

            # Predict using hybrid model (async)
            try:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                prediction = loop.run_until_complete(
                    hybrid_predictor.predict(symbol, spending_features)
                )
            except Exception as e:
                logger.error(
                    "Error running hybrid prediction for %s: %s", symbol, e
                )
                continue

            # Combine with existing scores
            base_score = stock.get("beginner_friendly_score", 5.0) / 10.0
            hybrid_score = prediction["predicted_return"]

            # Normalize hybrid score to 0-1 range
            hybrid_score_normalized = (hybrid_score + 0.2) / 0.4
            hybrid_score_normalized = max(
                0.0, min(1.0, hybrid_score_normalized)
            )

            # Weighted combination: 70% hybrid predictor, 30% base score
            final_score = 0.7 * hybrid_score_normalized + 0.3 * base_score

            contributions = prediction.get("feature_contributions", {})

            scored_stocks.append(
                {
                    **stock,
                    "ml_score": float(final_score),
                    "hybrid_score": float(hybrid_score_normalized),
                    "spending_score": float(contributions.get("spending", 0.0)),
                    "options_score": float(contributions.get("options", 0.0)),
                    "earnings_score": float(contributions.get("earnings", 0.0)),
                    "insider_score": float(contributions.get("insider", 0.0)),
                    "predicted_excess_return_4w": prediction[
                        "predicted_return"
                    ],
                    "ml_confidence": prediction["confidence"],
                    "ml_reasoning": (
                        f"Hybrid ensemble: {prediction['reasoning']}"
                    ),
                    "feature_contributions": contributions,
                    "stage1_predictions": prediction.get("stage1_predictions", {}),
                }
            )

        scored_stocks.sort(key=lambda x: x["ml_score"], reverse=True)
        return scored_stocks

    def _get_spending_features_for_ticker(
        self,
        symbol: str,
        spending_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        Get spending features for a specific ticker
        Uses aggregate spending data from all users
        """
        from datetime import timedelta

        from django.utils import timezone

        from .banking_models import BankTransaction
        from .spending_trend_predictor import SPENDING_TO_STOCKS

        # Find which spending categories map to this ticker
        relevant_categories: List[str] = []
        for category, tickers in SPENDING_TO_STOCKS.items():
            if symbol in tickers:
                relevant_categories.append(category)

        if not relevant_categories:
            # Return default features
            return {
                "spending_change_1w": 0.0,
                "spending_change_4w": 0.0,
                "spending_change_12w": 0.0,
                "spending_momentum": 0.0,
                "spending_volatility": 0.0,
                "total_spending": 0.0,
                "user_count": 0.0,
                "user_change_1w": 0.0,
                "user_change_4w": 0.0,
            }

        # Get recent spending for these categories
        end_date = timezone.now().date()

        # Current week
        current_transactions = BankTransaction.objects.filter(
            transaction_type="DEBIT",
            transaction_date__gte=end_date - timedelta(weeks=1),
            transaction_date__lte=end_date,
        )

        current_spending = 0.0
        current_users = set()

        for txn in current_transactions:
            merchant = (txn.merchant_name or "").upper()
            category = (txn.category or "").upper()
            for cat in relevant_categories:
                if cat in merchant or cat in category:
                    current_spending += abs(float(txn.amount))
                    current_users.add(txn.user_id)
                    break

        # 1 week ago
        week_ago_start = end_date - timedelta(weeks=2)
        week_ago_end = end_date - timedelta(weeks=1)
        week_ago_transactions = BankTransaction.objects.filter(
            transaction_type="DEBIT",
            transaction_date__gte=week_ago_start,
            transaction_date__lte=week_ago_end,
        )

        week_ago_spending = 0.0
        week_ago_users = set()

        for txn in week_ago_transactions:
            merchant = (txn.merchant_name or "").upper()
            category = (txn.category or "").upper()
            for cat in relevant_categories:
                if cat in merchant or cat in category:
                    week_ago_spending += abs(float(txn.amount))
                    week_ago_users.add(txn.user_id)
                    break

        # 4 weeks ago
        month_ago_start = end_date - timedelta(weeks=5)
        month_ago_end = end_date - timedelta(weeks=4)
        month_ago_transactions = BankTransaction.objects.filter(
            transaction_type="DEBIT",
            transaction_date__gte=month_ago_start,
            transaction_date__lte=month_ago_end,
        )

        month_ago_spending = 0.0
        month_ago_users = set()

        for txn in month_ago_transactions:
            merchant = (txn.merchant_name or "").upper()
            category = (txn.category or "").upper()
            for cat in relevant_categories:
                if cat in merchant or cat in category:
                    month_ago_spending += abs(float(txn.amount))
                    month_ago_users.add(txn.user_id)
                    break

        # Calculate features
        spending_change_1w = (
            (current_spending - week_ago_spending) / week_ago_spending
            if week_ago_spending > 0
            else 0.0
        )
        spending_change_4w = (
            (current_spending - month_ago_spending) / month_ago_spending
            if month_ago_spending > 0
            else 0.0
        )
        user_change_1w = len(current_users) - len(week_ago_users)
        user_change_4w = len(current_users) - len(month_ago_users)

        return {
            "spending_change_1w": float(spending_change_1w),
            "spending_change_4w": float(spending_change_4w),
            "spending_change_12w": 0.0,  # Would need 12-week data
            "spending_momentum": float(spending_change_1w),
            "spending_volatility": abs(float(spending_change_1w)),
            "total_spending": float(current_spending),
            "user_count": float(len(current_users)),
            "user_change_1w": float(user_change_1w),
            "user_change_4w": float(user_change_4w),
        }

    # -------------------------------------------------------------------------
    # Feature builders
    # -------------------------------------------------------------------------

    def _extract_market_features(
        self, market_data: Dict[str, Any]
    ) -> List[float]:
        """Extract enhanced numerical features from market data for ML models"""
        features: List[float] = []

        # Core market indicators
        features.append(float(market_data.get("sp500_return", 0.0)))
        features.append(float(market_data.get("volatility", 0.15)))
        features.append(float(market_data.get("interest_rate", 0.05)))

        # Enhanced market indicators
        vix_index = float(market_data.get("vix_index", 25.0))
        features.append(vix_index / 50.0)

        bond_yield_10y = float(market_data.get("bond_yield_10y", 0.05))
        features.append(bond_yield_10y / 10.0)

        features.append(float(market_data.get("dollar_strength", 0.5)))

        oil_price = float(market_data.get("oil_price", 70.0))
        features.append(oil_price / 100.0)

        # Sector performance (convert to numerical)
        sector_performance = market_data.get("sector_performance", {})
        sector_scores: List[float] = []
        for sector in [
            "technology",
            "healthcare",
            "financials",
            "consumer_discretionary",
            "utilities",
            "energy",
        ]:
            perf = sector_performance.get(sector, "neutral")
            if perf == "outperforming":
                sector_scores.append(1.0)
            elif perf == "neutral":
                sector_scores.append(0.0)
            else:
                sector_scores.append(-1.0)
        features.extend(sector_scores)

        # Economic indicators
        features.append(float(market_data.get("gdp_growth", 0.02)))
        features.append(float(market_data.get("unemployment_rate", 0.05)))

        inflation_rate = float(market_data.get("inflation_rate", 0.03))
        features.append(inflation_rate / 10.0)

        consumer_sentiment = float(market_data.get("consumer_sentiment", 60.0))
        features.append(consumer_sentiment / 100.0)

        # Ensure we always return exactly 20 features for the enhanced model
        while len(features) < 20:
            features.append(0.0)
        return features[:20]

    def _create_portfolio_features(
        self,
        user_profile: Dict[str, Any],
        market_conditions: Dict[str, Any],
        available_stocks: List[Dict[str, Any]],
        spending_analysis: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        """Create feature matrix for portfolio optimization with spending habits"""
        # Enhanced user profile features
        age = user_profile.get("age", 30)
        income_bracket = user_profile.get("income_bracket", "Under $50,000")
        risk_tolerance = user_profile.get("risk_tolerance", "Moderate")
        investment_horizon = user_profile.get(
            "investment_horizon", "5-10 years"
        )
        investment_experience = user_profile.get(
            "investment_experience", "Beginner"
        )
        tax_bracket = user_profile.get("tax_bracket", "22%")
        specific_goals = user_profile.get("investment_goals", [])

        # Encodings
        income_encoding = {
            "Under $30,000": 0.2,
            "$30,000 - $50,000": 0.4,
            "$50,000 - $75,000": 0.6,
            "$75,000 - $100,000": 0.8,
            "$100,000 - $150,000": 0.9,
            "Over $150,000": 1.0,
        }
        risk_encoding = {
            "Conservative": 0.3,
            "Moderate": 0.6,
            "Aggressive": 0.9,
        }
        horizon_encoding = {
            "1-3 years": 0.2,
            "3-5 years": 0.5,
            "5-10 years": 0.7,
            "10+ years": 1.0,
        }
        experience_encoding = {
            "Beginner": 0.2,
            "Intermediate": 0.5,
            "Advanced": 0.8,
            "Expert": 1.0,
        }
        tax_encoding = {
            "10%": 0.1,
            "12%": 0.2,
            "22%": 0.4,
            "24%": 0.6,
            "32%": 0.8,
            "35%": 0.9,
            "37%": 1.0,
        }

        goal_weights = {
            "Retirement Savings": 0.3,
            "Buy a Home": 0.2,
            "Emergency Fund": 0.1,
            "Wealth Building": 0.3,
            "Passive Income": 0.4,
            "Tax Benefits": 0.2,
            "College Fund": 0.2,
            "Travel Fund": 0.1,
        }
        goal_score = (
            sum(goal_weights.get(goal, 0.1) for goal in specific_goals)
            / len(specific_goals)
            if specific_goals
            else 0.2
        )

        # Spending habits
        if spending_analysis:
            discretionary_income = spending_analysis.get(
                "discretionary_income", 0
            )
            monthly_income = spending_analysis.get("monthly_income", 0)
            suggested_budget = spending_analysis.get("suggested_budget", 0)
            spending_health = (
                spending_analysis.get("spending_patterns", {}).get(
                    "spending_health", "unknown"
                )
            )

            if monthly_income > 0:
                discretionary_ratio = discretionary_income / monthly_income
                budget_ratio = (
                    suggested_budget / monthly_income
                    if monthly_income > 0
                    else 0.0
                )
            else:
                discretionary_ratio = 0.3
                budget_ratio = 0.09

            health_encoding = {
                "excellent": 1.0,
                "good": 0.75,
                "fair": 0.5,
                "poor": 0.25,
                "unknown": 0.5,
            }
            health_score = health_encoding.get(spending_health, 0.5)

            spending_features = [
                discretionary_ratio,
                budget_ratio,
                health_score,
            ]
        else:
            spending_features = [0.3, 0.09, 0.5]

        user_features = [
            age / 100.0,
            income_encoding.get(income_bracket, 0.5),
            risk_encoding.get(risk_tolerance, 0.6),
            horizon_encoding.get(investment_horizon, 0.7),
            experience_encoding.get(investment_experience, 0.2),
            tax_encoding.get(tax_bracket, 0.4),
            goal_score,
        ] + spending_features

        # Market features
        market_features = self._extract_market_features(market_conditions)

        # Stock market features (aggregate)
        if available_stocks:
            beginner_scores = [
                s.get("beginner_friendly_score", 5.0) for s in available_stocks
            ]
            stock_features = [
                float(np.mean(beginner_scores)),
                float(np.std(beginner_scores)),
                float(
                    len(
                        [
                            s
                            for s in available_stocks
                            if s.get("beginner_friendly_score", 0) >= 7.0
                        ]
                    )
                ),
            ]
        else:
            stock_features = [5.0, 1.0, 0.0]

        all_features = user_features + market_features + stock_features

        # Ensure fixed length (28)
        while len(all_features) < 28:
            all_features.append(0.0)

        return np.array(all_features[:28]).reshape(1, -1)

    def _create_stock_features(
        self,
        stocks: List[Dict[str, Any]],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any],
        spending_analysis: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        """Create enhanced feature matrix for stock scoring with ESG, momentum, and value factors"""
        features: List[List[float]] = []

        for stock in stocks:
            stock_features: List[float] = []

            # Core stock features
            stock_features.append(
                stock.get("beginner_friendly_score", 5.0) / 10.0
            )

            # ESG factors
            esg_score = stock.get("esg_score", 5.0) / 10.0
            sustainability_rating = stock.get("sustainability_rating", 5.0) / 10.0
            governance_score = stock.get("governance_score", 5.0) / 10.0
            stock_features.extend(
                [esg_score, sustainability_rating, governance_score]
            )

            # Value factors
            pe_ratio = stock.get("pe_ratio", 15.0) / 30.0
            pb_ratio = stock.get("pb_ratio", 1.5) / 5.0
            debt_to_equity = stock.get("debt_to_equity", 0.5) / 2.0
            stock_features.extend([pe_ratio, pb_ratio, debt_to_equity])

            # Momentum factors
            price_momentum = stock.get("price_momentum", 0.0)
            volume_momentum = stock.get("volume_momentum", 0.0)
            stock_features.extend([price_momentum, volume_momentum])

            # Market condition features (subset for stock scoring)
            market_feats = self._extract_market_features(market_conditions)[:6]
            stock_features.extend(market_feats)

            # User profile features (normalized)
            age = user_profile.get("age", 30) / 100.0
            risk_tolerance = user_profile.get("risk_tolerance", "Moderate")
            risk_encoding = {
                "Conservative": 0.3,
                "Moderate": 0.6,
                "Aggressive": 0.9,
            }
            risk_score = risk_encoding.get(risk_tolerance, 0.6)
            stock_features.extend([age, risk_score])

            # Spending-based preferences
            if spending_analysis:
                from .spending_habits_service import SpendingHabitsService

                spending_service = SpendingHabitsService()
                sector_weights = (
                    spending_service.get_spending_based_stock_preferences(
                        spending_analysis
                    )
                )

                stock_sector = stock.get("sector", "Unknown")
                sector_preference = sector_weights.get(stock_sector, 0.0)
                stock_features.append(sector_preference)
            else:
                stock_features.append(0.0)

            # Ensure fixed length (21 features)
            while len(stock_features) < 21:
                stock_features.append(0.0)

            features.append(stock_features[:21])

        return np.array(features)

    # -------------------------------------------------------------------------
    # Training helpers
    # -------------------------------------------------------------------------

    def _train_market_regime_model(self) -> None:
        """Train the enhanced market regime prediction model with 20 features"""
        if not self.ml_available:
            self.market_regime_model = None
            return

        try:
            n_samples = 1000
            np.random.seed(42)

            # Synthetic market data with 20 features.
            # Feature semantics (mirrors regime_detector feature engineering):
            #   0: VIX-proxy / volatility level (z-scored)
            #   1: 5-day returns (directional momentum)
            #   2: ADX-proxy (trend strength)
            #   3: IV rank (relative vol level)
            #   4: Put/call ratio proxy
            #   5–19: Additional market micro-structure noise
            X = np.random.randn(n_samples, 20)

            # Encode regime rules so the model learns real decision boundaries
            # rather than memorising random class distributions.
            #   early_bull=0, late_bull=1, correction=2, bear=3,
            #   sideways=4, high_vol=5, recovery=6, bubble=7
            y = np.full(n_samples, 4, dtype=int)  # default: sideways_consolidation

            # Bear / crash: high vol + negative returns
            bear_mask = (X[:, 0] > 1.5) & (X[:, 1] < -0.8)
            y[bear_mask] = 3  # bear_market

            # High volatility: very high vol, mixed direction
            high_vol_mask = (X[:, 0] > 1.2) & ~bear_mask
            y[high_vol_mask] = 5  # high_volatility

            # Early bull: strong trend up, moderate vol
            early_bull_mask = (X[:, 2] > 1.0) & (X[:, 1] > 0.5) & (X[:, 0] < 0.5)
            y[early_bull_mask] = 0  # early_bull_market

            # Late bull / bubble: strong trend up + rising vol
            late_bull_mask = (X[:, 2] > 1.0) & (X[:, 1] > 0.5) & (X[:, 0] > 0.5)
            y[late_bull_mask] = 1  # late_bull_market

            # Correction: mild negative returns after bull
            correction_mask = (X[:, 1] < -0.3) & (X[:, 1] > -0.8) & (X[:, 0] < 1.2)
            y[correction_mask] = 2  # correction

            # Recovery: positive returns from low-vol base
            recovery_mask = (X[:, 1] > 0.3) & (X[:, 0] < -0.5)
            y[recovery_mask] = 6  # recovery

            self.market_regime_model = RandomForestClassifier(
                **self.model_params["market_regime"]
            )
            self.market_regime_model.fit(X, y)
            logger.info(
                "Market regime model trained on structured synthetic data with 20 features"
            )
        except Exception as e:
            logger.error(
                f"Error training enhanced market regime model: {e}"
            )
            self.market_regime_model = None

    def _train_portfolio_optimizer(self) -> None:
        """Train the enhanced portfolio optimization model"""
        if not self.ml_available:
            self.portfolio_optimizer = None
            return

        try:
            n_samples = 500
            np.random.seed(42)

            # Synthetic portfolio data: 25 features
            X = np.random.randn(n_samples, 25)
            y = np.random.rand(n_samples)  # Expected returns

            self.portfolio_optimizer = GradientBoostingRegressor(
                **self.model_params["portfolio_optimization"]
            )
            self.portfolio_optimizer.fit(X, y)
            logger.info(
                "Enhanced portfolio optimizer trained successfully with 25 features"
            )
        except Exception as e:
            logger.error(
                f"Error training enhanced portfolio optimizer: {e}"
            )
            self.portfolio_optimizer = None

    def _train_stock_scorer(self) -> None:
        """Train the enhanced stock scoring model with proper validation and regularization"""
        if not self.ml_available:
            self.stock_scorer = None
            return

        try:
            from .models import Stock
            from sklearn.linear_model import Ridge

            if ImprovedMLService is None:
                raise ImportError("ImprovedMLService not available")
            
            improved_ml = ImprovedMLService()

            # Try real market data via improved ML service
            if improved_ml.is_available():
                all_stocks = Stock.objects.all()[:20]
                symbols = [stock.symbol for stock in all_stocks]
                market_data = improved_ml.get_enhanced_stock_data(
                    symbols, days=365
                )

                if market_data:
                    X, y = improved_ml.create_enhanced_features(market_data)
                    if len(X) > 0:
                        results = improved_ml.train_improved_models(X, y)

                        best_model_name = max(
                            results.keys(),
                            key=lambda k: results[k].get(
                                "cv_mean", float("-inf")
                            ),
                        )
                        self.stock_scorer = results[best_model_name]["model"]
                        logger.info(
                            "Enhanced stock scorer trained with %s "
                            "(CV R²: %.3f)",
                            best_model_name,
                            results[best_model_name].get("cv_mean", 0.0),
                        )
                        return

            # Fallback to synthetic data
            n_samples = 2000
            np.random.seed(42)

            X = np.random.randn(n_samples, 20)
            y = np.random.uniform(1, 10, n_samples)

            from sklearn.linear_model import Ridge

            self.stock_scorer = Ridge(alpha=10.0)
            self.stock_scorer.fit(X, y)
            logger.info(
                "Enhanced stock scorer trained with Ridge regularization (fallback)"
            )
        except Exception as e:
            logger.error(f"Error training enhanced stock scorer: {e}")
            self.stock_scorer = None

    # -------------------------------------------------------------------------
    # Portfolio helpers
    # -------------------------------------------------------------------------

    def _generate_optimal_allocation(
        self,
        features: np.ndarray,
        user_profile: Dict[str, Any],
    ) -> Dict[str, float]:
        """Generate optimal portfolio allocation using ML model"""
        risk_tolerance = user_profile.get("risk_tolerance", "Moderate")

        base_allocations = {
            "Conservative": {
                "stocks": 35,
                "bonds": 40,
                "etfs": 10,
                "reits": 8,
                "commodities": 2,
                "international": 3,
                "cash": 2,
            },
            "Moderate": {
                "stocks": 55,
                "bonds": 20,
                "etfs": 10,
                "reits": 8,
                "commodities": 3,
                "international": 2,
                "cash": 2,
            },
            "Aggressive": {
                "stocks": 70,
                "bonds": 8,
                "etfs": 8,
                "reits": 6,
                "commodities": 4,
                "international": 2,
                "cash": 2,
            },
        }

        allocation = base_allocations.get(
            risk_tolerance, base_allocations["Moderate"]
        ).copy()

        # Adjust based on ML model output (simplified)
        if self.portfolio_optimizer is not None:
            try:
                prediction = self.portfolio_optimizer.predict(features)[0]

                if prediction > 0.6:
                    allocation["stocks"] += 5
                    allocation["bonds"] -= 5
                elif prediction < 0.4:
                    allocation["cash"] += 5
                    allocation["stocks"] -= 5
            except Exception as e:
                logger.error(
                    "Error using portfolio optimizer for allocation: %s", e
                )

        return allocation

    def _calculate_ml_expected_return(
        self,
        allocation: Dict[str, float],
        features: np.ndarray,
    ) -> str:
        """Calculate expected return using ML model"""
        if self.portfolio_optimizer is not None:
            try:
                base_return = self.portfolio_optimizer.predict(features)[0]
                stock_weight = allocation.get("stocks", 60) / 100.0
                adjusted_return = base_return * (0.8 + 0.4 * stock_weight)
                return f"{adjusted_return*100:.1f}-{(adjusted_return*100)*1.3:.1f}%"
            except Exception as e:
                logger.error(
                    "Error calculating ML expected return: %s", e
                )
                return "8-12%"

        return "8-12%"  # Fallback

    def _calculate_ml_risk_score(
        self,
        allocation: Dict[str, float],
        features: np.ndarray,
    ) -> float:
        """Calculate risk score using ML model"""
        stock_weight = allocation.get("stocks", 60) / 100.0
        bond_weight = allocation.get("bonds", 25) / 100.0
        cash_weight = allocation.get("cash", 3) / 100.0

        risk_score = stock_weight * 0.8 + bond_weight * 0.3 + cash_weight * 0.1
        return float(min(1.0, max(0.0, risk_score)))

    # -------------------------------------------------------------------------
    # Stock scoring helpers
    # -------------------------------------------------------------------------

    def _calculate_stock_confidence(self, features: np.ndarray) -> float:
        """Calculate confidence score for stock prediction (placeholder)"""
        return 0.8

    def _generate_ml_reasoning(
        self,
        features: np.ndarray,
        score: float,
    ) -> str:
        """Generate reasoning for ML-based stock score"""
        reasoning_parts: List[str] = []

        if score >= 8.0:
            reasoning_parts.append("Exceptional ML score")
        elif score >= 7.0:
            reasoning_parts.append("Strong ML prediction")
        else:
            reasoning_parts.append("Good ML fundamentals")

        if len(features) > 0 and features[0] >= 0.7:
            reasoning_parts.append("High beginner-friendly rating")

        if len(features) > 1 and features[1] > 0:
            reasoning_parts.append("Favorable market conditions")

        return " | ".join(reasoning_parts)

    # -------------------------------------------------------------------------
    # Fallback methods
    # -------------------------------------------------------------------------

    def _fallback_market_regime(
        self,
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Enhanced fallback market regime prediction with granular labels"""
        return {
            "regime": "sideways_consolidation",
            "confidence": 0.5,
            "all_probabilities": {
                "early_bull_market": 0.15,
                "late_bull_market": 0.10,
                "correction": 0.15,
                "bear_market": 0.15,
                "sideways_consolidation": 0.20,
                "high_volatility": 0.10,
                "recovery": 0.10,
                "bubble_formation": 0.05,
            },
            "method": "fallback",
        }

    def _fallback_portfolio_optimization(
        self,
        user_profile: Dict[str, Any],
        market_conditions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Enhanced fallback portfolio optimization with more asset classes"""
        risk_tolerance = user_profile.get("risk_tolerance", "Moderate")

        base_allocations = {
            "Conservative": {
                "stocks": 35,
                "bonds": 40,
                "etfs": 10,
                "reits": 8,
                "commodities": 2,
                "international": 3,
                "cash": 2,
            },
            "Moderate": {
                "stocks": 55,
                "bonds": 20,
                "etfs": 10,
                "reits": 8,
                "commodities": 3,
                "international": 2,
                "cash": 2,
            },
            "Aggressive": {
                "stocks": 70,
                "bonds": 8,
                "etfs": 8,
                "reits": 6,
                "commodities": 4,
                "international": 2,
                "cash": 2,
            },
        }

        allocation = base_allocations.get(
            risk_tolerance, base_allocations["Moderate"]
        )

        return {
            "allocation": allocation,
            "expected_return": "8-15%",  # Enhanced range
            "risk_score": 0.6,
            "method": "fallback",
        }

    def _fallback_stock_scoring(
        self,
        stocks: List[Dict[str, Any]],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Enhanced fallback stock scoring with ESG, momentum, and value factors"""
        scored_stocks: List[Dict[str, Any]] = []

        for stock in stocks:
            base_score = float(stock.get("beginner_friendly_score", 5.0))

            esg_bonus = stock.get("esg_score", 5.0) / 10.0 * 0.5
            value_bonus = self._calculate_value_bonus(stock)
            momentum_bonus = self._calculate_momentum_bonus(stock)

            enhanced_score = min(
                10.0, base_score + esg_bonus + value_bonus + momentum_bonus
            )

            reasoning_parts = [f"Base score: {base_score:.1f}"]
            if esg_bonus > 0:
                reasoning_parts.append("ESG positive")
            if value_bonus > 0:
                reasoning_parts.append("Value attractive")
            if momentum_bonus > 0:
                reasoning_parts.append("Momentum positive")

            scored_stocks.append(
                {
                    **stock,
                    "ml_score": enhanced_score,
                    "ml_confidence": 0.6,
                    "ml_reasoning": " | ".join(reasoning_parts),
                }
            )

        scored_stocks.sort(key=lambda x: x["ml_score"], reverse=True)
        return scored_stocks

    def _calculate_value_bonus(self, stock: Dict[str, Any]) -> float:
        """Calculate value factor bonus for stock scoring"""
        bonus = 0.0

        pe_ratio = stock.get("pe_ratio", 15.0)
        if pe_ratio < 12.0:
            bonus += 0.5
        elif pe_ratio < 15.0:
            bonus += 0.3
        elif pe_ratio < 20.0:
            bonus += 0.1

        pb_ratio = stock.get("pb_ratio", 1.5)
        if pb_ratio < 1.0:
            bonus += 0.3
        elif pb_ratio < 1.5:
            bonus += 0.2

        debt_equity = stock.get("debt_to_equity", 0.5)
        if debt_equity < 0.3:
            bonus += 0.2
        elif debt_equity < 0.5:
            bonus += 0.1

        return float(min(1.0, bonus))

    def _calculate_momentum_bonus(self, stock: Dict[str, Any]) -> float:
        """Calculate momentum factor bonus for stock scoring"""
        bonus = 0.0

        momentum = stock.get("price_momentum", 0.0)
        if momentum > 0.1:
            bonus += 0.4
        elif momentum > 0.05:
            bonus += 0.2

        volume_momentum = stock.get("volume_momentum", 0.0)
        if volume_momentum > 0.2:
            bonus += 0.2
        elif volume_momentum > 0.1:
            bonus += 0.1

        return float(min(0.6, bonus))