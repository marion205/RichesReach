"""
Spending-Based Predictive Models - Your Competitive Moat
Predicts stock performance based on real consumer spending patterns

Week 1 Implementation: Baseline model with spending features only
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.core.cache import cache
import warnings
warnings.filterwarnings('ignore')

# ML imports
try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, TimeSeriesSplit
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available - install with: pip install xgboost")

from .banking_models import BankTransaction
from .models import Stock
from .market_data_api_service import MarketDataAPIService, DataProvider
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Mapping: Spending categories/merchants → Stock tickers/sectors
SPENDING_TO_STOCKS = {
    # Technology
    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA'],
    'Subscriptions': ['NFLX', 'SPOT', 'DIS', 'CMCSA'],
    'APPLE': ['AAPL'],
    'MICROSOFT': ['MSFT'],
    'GOOGLE': ['GOOGL'],
    'AMAZON': ['AMZN'],
    'NETFLIX': ['NFLX'],
    'SPOTIFY': ['SPOT'],
    
    # Travel
    'Travel': ['DAL', 'AAL', 'UAL', 'LUV', 'BKNG', 'EXPE', 'ABNB'],
    'AIRLINE': ['DAL', 'AAL', 'UAL', 'LUV'],
    'HOTEL': ['MAR', 'HLT', 'H'],
    'UBER': ['UBER'],
    'LYFT': ['LYFT'],
    'AIRBNB': ['ABNB'],
    
    # Food & Dining
    'Food & Dining': ['MCD', 'SBUX', 'CMG', 'YUM', 'DPZ'],
    'RESTAURANT': ['MCD', 'SBUX', 'CMG', 'YUM', 'DPZ'],
    'STARBUCKS': ['SBUX'],
    'MCDONALD': ['MCD'],
    
    # Shopping
    'Shopping': ['TGT', 'WMT', 'HD', 'LOW', 'COST'],
    'TARGET': ['TGT'],
    'WALMART': ['WMT'],
    'AMAZON': ['AMZN'],  # Also shopping
    
    # Healthcare
    'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABT', 'TMO'],
    'CVS': ['CVS'],
    'WALGREENS': ['WBA'],
    
    # Transportation
    'Transportation': ['F', 'GM', 'TSLA', 'FORD'],
    'GAS': ['XOM', 'CVX', 'COP'],
    
    # Entertainment
    'Entertainment': ['DIS', 'NFLX', 'CMCSA', 'FOXA'],
    
    # Utilities
    'Utilities': ['NEE', 'DUK', 'SO', 'AEP'],
}

# Sector mappings
SPENDING_TO_SECTORS = {
    'Technology': 'Technology',
    'Subscriptions': 'Technology',
    'Travel': 'Consumer Discretionary',
    'Food & Dining': 'Consumer Staples',
    'Shopping': 'Consumer Discretionary',
    'Healthcare': 'Healthcare',
    'Transportation': 'Industrials',
    'Entertainment': 'Communication Services',
    'Utilities': 'Utilities',
}


class SpendingTrendPredictor:
    """
    Predicts stock performance based on consumer spending patterns
    This is your competitive moat - no competitor has this data!
    """
    
    def __init__(self):
        self.model = None
        self.feature_names = []
        self.market_data_service = None
        self.xgboost_available = XGBOOST_AVAILABLE
        
        if not self.xgboost_available:
            logger.warning("XGBoost not available - spending predictor will use fallback")
    
    async def prepare_training_data(
        self,
        lookback_months: int = 36,
        min_users_per_ticker: int = 5
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from real spending and stock price data
        
        Args:
            lookback_months: How many months of historical data to use
            min_users_per_ticker: Minimum users spending in category to include ticker
            
        Returns:
            (features_df, targets_series) - Features and target returns
        """
        logger.info(f"Preparing training data: {lookback_months} months lookback")
        
        # Step 1: Get all spending transactions (last 24-36 months)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=lookback_months * 30)
        
        # Use sync_to_async for Django ORM queries
        transactions_qs = await sync_to_async(list)(
            BankTransaction.objects.filter(
                transaction_type='DEBIT',
                transaction_date__gte=start_date,
                transaction_date__lte=end_date,
                status='POSTED'
            ).select_related('user').order_by('transaction_date')
        )
        
        logger.info(f"Found {len(transactions_qs)} transactions")
        
        if len(transactions_qs) < 1000:
            logger.warning("Not enough transactions for training - need at least 1000")
            return pd.DataFrame(), pd.Series()
        
        # Step 2: Aggregate spending by category/merchant → map to tickers
        spending_by_ticker = self._aggregate_spending_by_ticker(transactions_qs)
        
        # Step 3: Create weekly/monthly % change features
        spending_features = self._create_spending_change_features(spending_by_ticker)
        
        # Step 4: Get real stock price data and calculate forward returns
        targets = await self._calculate_forward_returns(spending_features.index.tolist())
        
        # Step 5: Align features and targets by date
        aligned_data = self._align_features_targets(spending_features, targets)
        
        if aligned_data[0].empty:
            logger.warning("No aligned data after processing")
            return pd.DataFrame(), pd.Series()
        
        logger.info(f"Prepared {len(aligned_data[0])} training samples with {len(aligned_data[0].columns)} features")
        return aligned_data
    
    def _aggregate_spending_by_ticker(self, transactions) -> pd.DataFrame:
        """
        Aggregate spending by ticker based on merchant/category mapping
        Returns DataFrame with columns: date, ticker, total_spending, user_count
        """
        spending_data = []
        
        # Group by week for efficiency
        for transaction in transactions:
            date = transaction.transaction_date or transaction.posted_date
            merchant = (transaction.merchant_name or '').upper()
            category = (transaction.category or '').upper()
            description = (transaction.description or '').upper()
            amount = abs(float(transaction.amount))
            
            # Find matching tickers
            matched_tickers = set()
            
            # Check merchant name
            for key, tickers in SPENDING_TO_STOCKS.items():
                if key in merchant or key in description:
                    matched_tickers.update(tickers)
            
            # Check category
            for key, tickers in SPENDING_TO_STOCKS.items():
                if key in category:
                    matched_tickers.update(tickers)
            
            # If no direct match, try sector mapping
            if not matched_tickers:
                for cat_key, sector in SPENDING_TO_SECTORS.items():
                    if cat_key in category or cat_key in merchant:
                        # Get all stocks in that sector (simplified - in production, use actual sector data)
                        matched_tickers.update(SPENDING_TO_STOCKS.get(cat_key, []))
            
            # Add spending for each matched ticker
            for ticker in matched_tickers:
                spending_data.append({
                    'date': date,
                    'ticker': ticker,
                    'amount': amount,
                    'user_id': transaction.user_id
                })
        
        if not spending_data:
            logger.warning("No spending data matched to tickers")
            return pd.DataFrame()
        
        df = pd.DataFrame(spending_data)
        
        # Aggregate by week and ticker
        df['week'] = pd.to_datetime(df['date']).dt.to_period('W').dt.start_time
        weekly_spending = df.groupby(['week', 'ticker']).agg({
            'amount': 'sum',
            'user_id': 'nunique'
        }).reset_index()
        weekly_spending.columns = ['date', 'ticker', 'total_spending', 'user_count']
        
        return weekly_spending
    
    def _create_spending_change_features(self, spending_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create weekly/monthly % change features from spending data
        Returns DataFrame with features: ticker_date, spending_change_1w, spending_change_4w, etc.
        """
        if spending_df.empty:
            return pd.DataFrame()
        
        features_list = []
        
        for ticker in spending_df['ticker'].unique():
            ticker_data = spending_df[spending_df['ticker'] == ticker].sort_values('date')
            
            if len(ticker_data) < 5:  # Need at least 5 weeks
                continue
            
            for idx, row in ticker_data.iterrows():
                date = row['date']
                current_spending = row['total_spending']
                current_users = row['user_count']
                
                # Calculate % changes
                features = {'date': date, 'ticker': ticker}
                
                # 1-week change
                week_ago = date - timedelta(weeks=1)
                week_ago_data = ticker_data[ticker_data['date'] <= week_ago].tail(1)
                if not week_ago_data.empty:
                    prev_spending = week_ago_data.iloc[0]['total_spending']
                    features['spending_change_1w'] = (current_spending - prev_spending) / prev_spending if prev_spending > 0 else 0
                    features['user_change_1w'] = current_users - week_ago_data.iloc[0]['user_count']
                else:
                    features['spending_change_1w'] = 0
                    features['user_change_1w'] = 0
                
                # 4-week change
                month_ago = date - timedelta(weeks=4)
                month_ago_data = ticker_data[ticker_data['date'] <= month_ago].tail(1)
                if not month_ago_data.empty:
                    prev_spending = month_ago_data.iloc[0]['total_spending']
                    features['spending_change_4w'] = (current_spending - prev_spending) / prev_spending if prev_spending > 0 else 0
                    features['user_change_4w'] = current_users - month_ago_data.iloc[0]['user_count']
                else:
                    features['spending_change_4w'] = 0
                    features['user_change_4w'] = 0
                
                # 12-week change
                quarter_ago = date - timedelta(weeks=12)
                quarter_ago_data = ticker_data[ticker_data['date'] <= quarter_ago].tail(1)
                if not quarter_ago_data.empty:
                    prev_spending = quarter_ago_data.iloc[0]['total_spending']
                    features['spending_change_12w'] = (current_spending - prev_spending) / prev_spending if prev_spending > 0 else 0
                else:
                    features['spending_change_12w'] = 0
                
                # Rolling statistics
                recent_data = ticker_data[ticker_data['date'] <= date].tail(4)
                if len(recent_data) > 1:
                    features['spending_momentum'] = recent_data['total_spending'].pct_change().mean()
                    features['spending_volatility'] = recent_data['total_spending'].std()
                else:
                    features['spending_momentum'] = 0
                    features['spending_volatility'] = 0
                
                # Absolute spending levels (normalized)
                features['total_spending'] = current_spending
                features['user_count'] = current_users
                
                features_list.append(features)
        
        if not features_list:
            return pd.DataFrame()
        
        features_df = pd.DataFrame(features_list)
        features_df['ticker_date'] = features_df['ticker'] + '_' + features_df['date'].astype(str)
        features_df = features_df.set_index('ticker_date')
        
        return features_df
    
    async def _calculate_forward_returns(self, ticker_dates: List[str]) -> pd.Series:
        """
        Calculate forward 4-week and 12-week excess returns vs SPY using real price data
        Returns Series indexed by ticker_date
        """
        logger.info(f"Calculating forward returns for {len(ticker_dates)} ticker-date pairs")
        
        if not self.market_data_service:
            self.market_data_service = MarketDataAPIService()
        
        returns_data = []
        
        # Get SPY data once (benchmark)
        spy_data = None
        try:
            async with self.market_data_service:
                spy_hist = await self.market_data_service.get_historical_data('SPY', period='2y')
                if spy_hist is not None and not spy_hist.empty:
                    spy_data = spy_hist['Close'] if 'Close' in spy_hist.columns else spy_hist.iloc[:, 0]
        except Exception as e:
            logger.error(f"Error fetching SPY data: {e}")
        
        # Process each ticker-date
        processed = 0
        for ticker_date in ticker_dates:
            try:
                ticker, date_str = ticker_date.split('_', 1)
                date = pd.to_datetime(date_str).date()
                
                # Get historical data for this ticker
                async with self.market_data_service:
                    hist_data = await self.market_data_service.get_historical_data(ticker, period='1y')
                
                if hist_data is None or hist_data.empty:
                    continue
                
                # Get price at date and forward prices
                hist_data.index = pd.to_datetime(hist_data.index).date()
                if date not in hist_data.index:
                    # Find closest date
                    closest_idx = min(hist_data.index, key=lambda x: abs((x - date).days))
                    if abs((closest_idx - date).days) > 7:  # Too far away
                        continue
                    date = closest_idx
                
                price_col = 'Close' if 'Close' in hist_data.columns else hist_data.columns[0]
                current_price = hist_data.loc[date, price_col]
                
                # Calculate 4-week forward return
                future_4w_date = date + timedelta(weeks=4)
                future_4w_price = None
                if future_4w_date in hist_data.index:
                    future_4w_price = hist_data.loc[future_4w_date, price_col]
                else:
                    # Find closest future date
                    future_dates = [d for d in hist_data.index if d > date]
                    if future_dates:
                        closest_future = min(future_dates, key=lambda x: abs((x - future_4w_date).days))
                        if abs((closest_future - future_4w_date).days) <= 7:
                            future_4w_price = hist_data.loc[closest_future, price_col]
                
                # Calculate 12-week forward return
                future_12w_date = date + timedelta(weeks=12)
                future_12w_price = None
                if future_12w_date in hist_data.index:
                    future_12w_price = hist_data.loc[future_12w_date, price_col]
                else:
                    future_dates = [d for d in hist_data.index if d > date]
                    if future_dates:
                        closest_future = min(future_dates, key=lambda x: abs((x - future_12w_date).days))
                        if abs((closest_future - future_12w_date).days) <= 14:
                            future_12w_price = hist_data.loc[closest_future, price_col]
                
                if future_4w_price and current_price > 0:
                    return_4w = (future_4w_price - current_price) / current_price
                    
                    # Calculate excess return vs SPY
                    excess_return_4w = return_4w
                    if spy_data is not None and date in spy_data.index:
                        spy_price = spy_data.loc[date]
                        spy_future_date = min([d for d in spy_data.index if d > date], default=None)
                        if spy_future_date:
                            spy_future_price = spy_data.loc[spy_future_date]
                            spy_return = (spy_future_price - spy_price) / spy_price if spy_price > 0 else 0
                            excess_return_4w = return_4w - spy_return
                    
                    returns_data.append({
                        'ticker_date': ticker_date,
                        'return_4w': return_4w,
                        'excess_return_4w': excess_return_4w,
                        'return_12w': (future_12w_price - current_price) / current_price if future_12w_price and current_price > 0 else None
                    })
                
                processed += 1
                if processed % 50 == 0:
                    logger.info(f"Processed {processed}/{len(ticker_dates)} ticker-dates")
                    
            except Exception as e:
                logger.error(f"Error calculating returns for {ticker_date}: {e}")
                continue
        
        if not returns_data:
            logger.warning("No forward returns calculated")
            return pd.Series()
        
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.set_index('ticker_date')
        
        logger.info(f"Calculated forward returns for {len(returns_df)} samples")
        return returns_df['excess_return_4w']  # Primary target: 4-week excess return
    
    def _align_features_targets(self, features_df: pd.DataFrame, targets: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Align features and targets by ticker_date index"""
        if features_df.empty or targets.empty:
            return pd.DataFrame(), pd.Series()
        
        # Find common indices
        common_idx = features_df.index.intersection(targets.index)
        
        if len(common_idx) == 0:
            logger.warning("No common indices between features and targets")
            return pd.DataFrame(), pd.Series()
        
        aligned_features = features_df.loc[common_idx]
        aligned_targets = targets.loc[common_idx]
        
        # Remove NaN targets
        valid_mask = ~aligned_targets.isna()
        aligned_features = aligned_features[valid_mask]
        aligned_targets = aligned_targets[valid_mask]
        
        return aligned_features, aligned_targets
    
    async def train_baseline_model(self, lookback_months: int = 36) -> Dict[str, Any]:
        """
        Train baseline XGBoost model using only spending features
        Returns model performance metrics
        """
        if not self.xgboost_available:
            logger.error("XGBoost not available - cannot train model")
            return {'error': 'XGBoost not available'}
        
        logger.info("Training baseline spending-based predictive model...")
        
        # Prepare training data
        features_df, targets = await self.prepare_training_data(lookback_months)
        
        if features_df.empty or targets.empty:
            logger.error("No training data available")
            return {'error': 'No training data'}
        
        # Remove date/ticker columns (keep only numeric features)
        feature_cols = [col for col in features_df.columns if col not in ['date', 'ticker']]
        X = features_df[feature_cols].fillna(0)
        y = targets.fillna(0)
        
        self.feature_names = feature_cols
        
        # Time-series split (don't shuffle - respect temporal order)
        tscv = TimeSeriesSplit(n_splits=3)
        scores = []
        
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Train XGBoost
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            
            scores.append({
                'r2': r2,
                'rmse': rmse,
                'mae': mae
            })
        
        # Train final model on all data
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X, y)
        
        # Calculate average metrics
        avg_r2 = np.mean([s['r2'] for s in scores])
        avg_rmse = np.mean([s['rmse'] for s in scores])
        avg_mae = np.mean([s['mae'] for s in scores])
        
        results = {
            'model_type': 'XGBoost',
            'cv_r2': avg_r2,
            'cv_rmse': avg_rmse,
            'cv_mae': avg_mae,
            'n_features': len(feature_cols),
            'n_samples': len(X),
            'feature_names': feature_cols,
            'trained': True
        }
        
        logger.info(f"Baseline model trained: R² = {avg_r2:.4f}, RMSE = {avg_rmse:.4f}")
        
        # Cache model
        cache.set('spending_predictor_model', self.model, 86400)  # 24 hours
        cache.set('spending_predictor_features', feature_cols, 86400)
        
        return results
    
    def predict_stock_return(self, spending_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict forward return for a stock based on spending features
        
        Args:
            spending_features: Dictionary of spending features for a ticker
            
        Returns:
            Prediction with confidence and reasoning
        """
        if self.model is None:
            # Try to load from cache
            self.model = cache.get('spending_predictor_model')
            self.feature_names = cache.get('spending_predictor_features', [])
        
        if self.model is None:
            return {
                'predicted_return': 0.0,
                'confidence': 0.0,
                'reasoning': 'Model not trained yet'
            }
        
        # Create feature vector
        feature_vector = np.array([spending_features.get(fname, 0.0) for fname in self.feature_names])
        
        if len(feature_vector) != len(self.feature_names):
            return {
                'predicted_return': 0.0,
                'confidence': 0.0,
                'reasoning': 'Feature mismatch'
            }
        
        # Predict
        prediction = self.model.predict(feature_vector.reshape(1, -1))[0]
        
        # Calculate confidence based on feature strength
        feature_strength = np.abs(feature_vector).mean()
        confidence = min(0.9, 0.3 + feature_strength * 0.6)
        
        # Generate reasoning
        top_features = sorted(
            zip(self.feature_names, feature_vector),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:3]
        
        reasoning_parts = []
        for fname, value in top_features:
            if 'change' in fname and abs(value) > 0.1:
                direction = "increase" if value > 0 else "decrease"
                pct = abs(value) * 100
                reasoning_parts.append(f"{pct:.1f}% {direction} in {fname.replace('_', ' ')}")
        
        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Baseline prediction"
        
        return {
            'predicted_return': float(prediction),
            'excess_return_4w': float(prediction),  # Already excess vs SPY
            'confidence': float(confidence),
            'reasoning': reasoning,
            'top_features': {fname: float(value) for fname, value in top_features}
        }


# Global instance
spending_predictor = SpendingTrendPredictor()

