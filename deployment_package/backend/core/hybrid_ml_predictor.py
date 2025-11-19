"""
Week 2: Hybrid ML Predictor with Options Flow + Earnings + Insider Signals
Two-stage ensemble: Stage 1 (separate models) → Stage 2 (meta-learner)
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
import warnings
warnings.filterwarnings('ignore')

# ML imports
try:
    import xgboost as xgb
    import lightgbm as lgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import r2_score, mean_squared_error
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available")

from .spending_trend_predictor import spending_predictor, SPENDING_TO_STOCKS
from .market_data_api_service import MarketDataAPIService
from .data_sources.options_flow_service import OptionsFlowService
from .options_service import OptionsAnalysisService

logger = logging.getLogger(__name__)


class OptionsFlowFeatures:
    """Extract options flow features for ML models"""
    
    def __init__(self):
        self.options_service = OptionsFlowService()
        self.options_analysis = OptionsAnalysisService()
        self.market_data_service = MarketDataAPIService()
    
    async def get_options_features(self, symbol: str) -> Dict[str, float]:
        """
        Extract options flow features for a symbol
        Returns features like: unusual_volume, call_put_ratio, sweep_detection, etc.
        """
        try:
            # Get options analysis
            options_data = self.options_analysis.get_comprehensive_analysis(symbol)
            
            unusual_flow = options_data.get('unusual_flow', {})
            market_sentiment = options_data.get('market_sentiment', {})
            options_chain = options_data.get('options_chain', {})
            
            # Extract features
            features = {}
            
            # Put/Call Ratio
            put_call_ratio = market_sentiment.get('put_call_ratio', 1.0)
            features['put_call_ratio'] = float(put_call_ratio)
            features['call_bias'] = 1.0 - put_call_ratio if put_call_ratio > 0 else 0.0  # Higher = more bullish
            
            # Unusual Volume
            unusual_volume = unusual_flow.get('unusual_volume', 0)
            total_volume = unusual_flow.get('total_volume', 1)
            features['unusual_volume_pct'] = float(unusual_volume / total_volume) if total_volume > 0 else 0.0
            
            # Top Trades Analysis
            top_trades = unusual_flow.get('top_trades', [])
            if top_trades:
                call_volume = sum(t.get('volume', 0) for t in top_trades if t.get('option_type') == 'call')
                put_volume = sum(t.get('volume', 0) for t in top_trades if t.get('option_type') == 'put')
                total_trade_volume = call_volume + put_volume
                
                features['call_volume_ratio'] = float(call_volume / total_trade_volume) if total_trade_volume > 0 else 0.5
                features['put_volume_ratio'] = float(put_volume / total_trade_volume) if total_trade_volume > 0 else 0.5
                
                # Average unusual activity score
                avg_score = np.mean([t.get('unusual_activity_score', 0.5) for t in top_trades])
                features['avg_unusual_score'] = float(avg_score)
                
                # Sweep detection
                sweep_count = sum(1 for t in top_trades if 'sweep' in str(t.get('activity_type', '')).lower())
                features['sweep_detection'] = float(sweep_count / len(top_trades)) if top_trades else 0.0
            else:
                features['call_volume_ratio'] = 0.5
                features['put_volume_ratio'] = 0.5
                features['avg_unusual_score'] = 0.5
                features['sweep_detection'] = 0.0
            
            # Implied Volatility Rank
            iv_rank = market_sentiment.get('implied_volatility_rank', 50.0)
            features['iv_rank'] = float(iv_rank / 100.0)  # Normalize to 0-1
            
            # Skew (put/call skew)
            skew = market_sentiment.get('skew', 0.0)
            features['skew'] = float(skew)
            features['bearish_skew'] = 1.0 if skew > 0.2 else 0.0  # High skew = bearish
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting options features for {symbol}: {e}")
            return self._get_default_options_features()
    
    def _get_default_options_features(self) -> Dict[str, float]:
        """Return default options features when data unavailable"""
        return {
            'put_call_ratio': 1.0,
            'call_bias': 0.0,
            'unusual_volume_pct': 0.0,
            'call_volume_ratio': 0.5,
            'put_volume_ratio': 0.5,
            'avg_unusual_score': 0.5,
            'sweep_detection': 0.0,
            'iv_rank': 0.5,
            'skew': 0.0,
            'bearish_skew': 0.0
        }


class EarningsInsiderFeatures:
    """Extract earnings surprise and insider trading features"""
    
    def __init__(self):
        self.market_data_service = MarketDataAPIService()
    
    async def get_earnings_features(self, symbol: str) -> Dict[str, float]:
        """
        Get earnings surprise features
        Uses Polygon/Finnhub APIs for real earnings data
        """
        try:
            # Try to get earnings data from Polygon
            async with self.market_data_service:
                # Polygon earnings endpoint
                api_key = self.market_data_service.get_api_key('polygon')
                if api_key:
                    import aiohttp
                    url = f"https://api.polygon.io/v2/reference/financials"
                    params = {
                        'ticker': symbol,
                        'timeframe': 'quarterly',
                        'limit': 4,  # Last 4 quarters
                        'apikey': api_key.key
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                results = data.get('results', [])
                                
                                if results:
                                    # Calculate earnings surprise history
                                    surprises = []
                                    for result in results[:4]:  # Last 4 quarters
                                        # Extract earnings data (structure varies by API)
                                        earnings = result.get('financials', {}).get('income_statement', {})
                                        # This is simplified - actual structure may differ
                                        surprises.append(0.0)  # Placeholder
                                    
                                    avg_surprise = np.mean(surprises) if surprises else 0.0
                                    surprise_volatility = np.std(surprises) if len(surprises) > 1 else 0.0
                                    
                                    return {
                                        'earnings_surprise_avg': float(avg_surprise),
                                        'earnings_surprise_volatility': float(surprise_volatility),
                                        'positive_surprise_rate': float(sum(1 for s in surprises if s > 0) / len(surprises)) if surprises else 0.5
                                    }
            
            # Fallback: use Finnhub
            finnhub_key = self.market_data_service.get_api_key('finnhub')
            if finnhub_key:
                import aiohttp
                url = f"https://finnhub.io/api/v1/stock/earnings"
                params = {
                    'symbol': symbol,
                    'token': finnhub_key.key
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            earnings_list = data if isinstance(data, list) else []
                            
                            if earnings_list:
                                # Calculate surprises from actual/estimate
                                surprises = []
                                for earning in earnings_list[:4]:
                                    actual = earning.get('actual', 0)
                                    estimate = earning.get('estimate', 0)
                                    if estimate != 0:
                                        surprise = (actual - estimate) / abs(estimate)
                                        surprises.append(surprise)
                                
                                if surprises:
                                    avg_surprise = np.mean(surprises)
                                    surprise_volatility = np.std(surprises)
                                    positive_rate = sum(1 for s in surprises if s > 0) / len(surprises)
                                    
                                    return {
                                        'earnings_surprise_avg': float(avg_surprise),
                                        'earnings_surprise_volatility': float(surprise_volatility),
                                        'positive_surprise_rate': float(positive_rate)
                                    }
            
            # Default if no data
            return self._get_default_earnings_features()
            
        except Exception as e:
            logger.error(f"Error getting earnings features for {symbol}: {e}")
            return self._get_default_earnings_features()
    
    async def get_insider_features(self, symbol: str) -> Dict[str, float]:
        """
        Get insider trading features
        Uses Finnhub API for insider transaction data
        """
        try:
            finnhub_key = self.market_data_service.get_api_key('finnhub')
            if not finnhub_key:
                return self._get_default_insider_features()
            
            import aiohttp
            url = f"https://finnhub.io/api/v1/stock/insider-transactions"
            params = {
                'symbol': symbol,
                'token': finnhub_key.key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        transactions = data.get('data', []) if isinstance(data, dict) else []
                        
                        if transactions:
                            # Analyze last 90 days
                            cutoff_date = datetime.now() - timedelta(days=90)
                            recent_txns = [
                                t for t in transactions
                                if pd.to_datetime(t.get('transactionDate', '2000-01-01')) >= cutoff_date
                            ]
                            
                            if recent_txns:
                                # Calculate buy/sell ratios
                                buys = sum(1 for t in recent_txns if t.get('transactionCode') == 'P')
                                sells = sum(1 for t in recent_txns if t.get('transactionCode') != 'P')
                                total = buys + sells
                                
                                # Calculate value-weighted signals
                                buy_value = sum(
                                    float(t.get('value', 0)) for t in recent_txns
                                    if t.get('transactionCode') == 'P'
                                )
                                sell_value = sum(
                                    float(t.get('value', 0)) for t in recent_txns
                                    if t.get('transactionCode') != 'P'
                                )
                                total_value = buy_value + sell_value
                                
                                return {
                                    'insider_buy_ratio': float(buys / total) if total > 0 else 0.5,
                                    'insider_sell_ratio': float(sells / total) if total > 0 else 0.5,
                                    'insider_buy_value_ratio': float(buy_value / total_value) if total_value > 0 else 0.5,
                                    'insider_activity_score': float(len(recent_txns) / 10.0)  # Normalize
                                }
            
            return self._get_default_insider_features()
            
        except Exception as e:
            logger.error(f"Error getting insider features for {symbol}: {e}")
            return self._get_default_insider_features()
    
    def _get_default_earnings_features(self) -> Dict[str, float]:
        return {
            'earnings_surprise_avg': 0.0,
            'earnings_surprise_volatility': 0.1,
            'positive_surprise_rate': 0.5
        }
    
    def _get_default_insider_features(self) -> Dict[str, float]:
        return {
            'insider_buy_ratio': 0.5,
            'insider_sell_ratio': 0.5,
            'insider_buy_value_ratio': 0.5,
            'insider_activity_score': 0.0
        }


class HybridMLPredictor:
    """
    Week 2: Hybrid ML Predictor
    Two-stage ensemble: Stage 1 (separate models) → Stage 2 (meta-learner)
    """
    
    def __init__(self):
        self.spending_model = None
        self.options_model = None
        self.earnings_model = None
        self.insider_model = None
        self.meta_learner = None  # LightGBM meta-learner
        self.feature_names = []
        self.ml_available = ML_AVAILABLE
        
        self.options_features = OptionsFlowFeatures()
        self.earnings_insider = EarningsInsiderFeatures()
        self.market_data_service = MarketDataAPIService()
    
    async def prepare_hybrid_training_data(
        self,
        lookback_months: int = 36
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data with all features:
        - Spending features (from Week 1)
        - Options flow features
        - Earnings surprise features
        - Insider trading features
        """
        logger.info("Preparing hybrid training data with all feature sources...")
        
        # Step 1: Get spending features (from Week 1)
        spending_features_df, targets = await spending_predictor.prepare_training_data(lookback_months)
        
        if spending_features_df.empty:
            logger.warning("No spending features available")
            return pd.DataFrame(), pd.Series()
        
        # Step 2: Get options flow features for each ticker-date
        options_features_list = []
        earnings_features_list = []
        insider_features_list = []
        
        ticker_dates = spending_features_df.index.tolist()
        logger.info(f"Fetching options/earnings/insider features for {len(ticker_dates)} samples...")
        
        processed = 0
        for ticker_date in ticker_dates:
            try:
                ticker, _ = ticker_date.split('_', 1)
                
                # Get options features
                options_feat = await self.options_features.get_options_features(ticker)
                options_features_list.append(options_feat)
                
                # Get earnings features
                earnings_feat = await self.earnings_insider.get_earnings_features(ticker)
                earnings_features_list.append(earnings_feat)
                
                # Get insider features
                insider_feat = await self.earnings_insider.get_insider_features(ticker)
                insider_features_list.append(insider_feat)
                
                processed += 1
                if processed % 20 == 0:
                    logger.info(f"Processed {processed}/{len(ticker_dates)} samples...")
                    
            except Exception as e:
                logger.error(f"Error processing {ticker_date}: {e}")
                # Use defaults
                options_features_list.append(self.options_features._get_default_options_features())
                earnings_features_list.append(self.earnings_insider._get_default_earnings_features())
                insider_features_list.append(self.earnings_insider._get_default_insider_features())
        
        # Step 3: Combine all features
        options_df = pd.DataFrame(options_features_list, index=spending_features_df.index)
        earnings_df = pd.DataFrame(earnings_features_list, index=spending_features_df.index)
        insider_df = pd.DataFrame(insider_features_list, index=spending_features_df.index)
        
        # Combine all features
        all_features = pd.concat([
            spending_features_df,
            options_df,
            earnings_df,
            insider_df
        ], axis=1)
        
        # Align with targets
        common_idx = all_features.index.intersection(targets.index)
        all_features = all_features.loc[common_idx]
        targets = targets.loc[common_idx]
        
        # Remove NaN targets
        valid_mask = ~targets.isna()
        all_features = all_features[valid_mask]
        targets = targets[valid_mask]
        
        logger.info(f"Prepared {len(all_features)} samples with {len(all_features.columns)} features")
        return all_features, targets
    
    async def train_hybrid_model(self, lookback_months: int = 36) -> Dict[str, Any]:
        """
        Train two-stage ensemble model
        Stage 1: Separate models for each feature group
        Stage 2: LightGBM meta-learner
        """
        if not self.ml_available:
            logger.error("ML libraries not available")
            return {'error': 'ML libraries not available'}
        
        logger.info("Training hybrid two-stage ensemble model...")
        
        # Prepare training data
        features_df, targets = await self.prepare_hybrid_training_data(lookback_months)
        
        if features_df.empty or targets.empty:
            logger.error("No training data available")
            return {'error': 'No training data'}
        
        # Identify feature groups
        spending_cols = [c for c in features_df.columns if 'spending' in c.lower() or 'user' in c.lower()]
        options_cols = [c for c in features_df.columns if any(x in c.lower() for x in ['put', 'call', 'unusual', 'sweep', 'iv', 'skew'])]
        earnings_cols = [c for c in features_df.columns if 'earnings' in c.lower() or 'surprise' in c.lower()]
        insider_cols = [c for c in features_df.columns if 'insider' in c.lower()]
        
        X = features_df.fillna(0)
        y = targets.fillna(0)
        
        self.feature_names = list(X.columns)
        
        # Time-series split
        tscv = TimeSeriesSplit(n_splits=3)
        stage1_predictions = []
        stage1_scores = []
        
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Stage 1: Train separate models
            stage1_preds = {}
            
            # Spending model
            if spending_cols:
                spending_cols_available = [c for c in spending_cols if c in X_train.columns]
                if spending_cols_available:
                    spending_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, random_state=42)
                    spending_model.fit(X_train[spending_cols_available], y_train)
                    stage1_preds['spending'] = spending_model.predict(X_test[spending_cols_available])
                    stage1_scores.append(('spending', r2_score(y_test, stage1_preds['spending'])))
            
            # Options model
            if options_cols:
                options_cols_available = [c for c in options_cols if c in X_train.columns]
                if options_cols_available:
                    options_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, random_state=42)
                    options_model.fit(X_train[options_cols_available], y_train)
                    stage1_preds['options'] = options_model.predict(X_test[options_cols_available])
                    stage1_scores.append(('options', r2_score(y_test, stage1_preds['options'])))
            
            # Earnings model
            if earnings_cols:
                earnings_cols_available = [c for c in earnings_cols if c in X_train.columns]
                if earnings_cols_available:
                    earnings_model = xgb.XGBRegressor(n_estimators=50, max_depth=4, random_state=42)
                    earnings_model.fit(X_train[earnings_cols_available], y_train)
                    stage1_preds['earnings'] = earnings_model.predict(X_test[earnings_cols_available])
                    stage1_scores.append(('earnings', r2_score(y_test, stage1_preds['earnings'])))
            
            # Insider model
            if insider_cols:
                insider_cols_available = [c for c in insider_cols if c in X_train.columns]
                if insider_cols_available:
                    insider_model = xgb.XGBRegressor(n_estimators=50, max_depth=4, random_state=42)
                    insider_model.fit(X_train[insider_cols_available], y_train)
                    stage1_preds['insider'] = insider_model.predict(X_test[insider_cols_available])
                    stage1_scores.append(('insider', r2_score(y_test, stage1_preds['insider'])))
            
            # Stage 2: Meta-learner features = Stage 1 predictions + original features
            meta_features = pd.DataFrame(stage1_preds, index=X_test.index)
            # Add some original features for context
            meta_features = pd.concat([meta_features, X_test[spending_cols_available[:3]]], axis=1)
            
            stage1_predictions.append({
                'meta_features': meta_features,
                'y_test': y_test
            })
        
        # Train final Stage 1 models on all data
        self.spending_model = None
        self.options_model = None
        self.earnings_model = None
        self.insider_model = None
        
        if spending_cols:
            spending_cols_available = [c for c in spending_cols if c in X.columns]
            if spending_cols_available:
                self.spending_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, random_state=42)
                self.spending_model.fit(X[spending_cols_available], y)
        
        if options_cols:
            options_cols_available = [c for c in options_cols if c in X.columns]
            if options_cols_available:
                self.options_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, random_state=42)
                self.options_model.fit(X[options_cols_available], y)
        
        if earnings_cols:
            earnings_cols_available = [c for c in earnings_cols if c in X.columns]
            if earnings_cols_available:
                self.earnings_model = xgb.XGBRegressor(n_estimators=50, max_depth=4, random_state=42)
                self.earnings_model.fit(X[earnings_cols_available], y)
        
        if insider_cols:
            insider_cols_available = [c for c in insider_cols if c in X.columns]
            if insider_cols_available:
                self.insider_model = xgb.XGBRegressor(n_estimators=50, max_depth=4, random_state=42)
                self.insider_model.fit(X[insider_cols_available], y)
        
        # Train Stage 2 meta-learner
        meta_train_features = []
        meta_train_targets = []
        
        for fold_data in stage1_predictions:
            meta_train_features.append(fold_data['meta_features'])
            meta_train_targets.append(fold_data['y_test'])
        
        if meta_train_features:
            meta_X = pd.concat(meta_train_features)
            meta_y = pd.concat(meta_train_targets)
            
            self.meta_learner = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
            self.meta_learner.fit(meta_X, meta_y)
            
            # Evaluate meta-learner
            meta_pred = self.meta_learner.predict(meta_X)
            meta_r2 = r2_score(meta_y, meta_pred)
            
            logger.info(f"Meta-learner R²: {meta_r2:.4f}")
        else:
            logger.warning("No meta-learner training data")
            self.meta_learner = None
        
        # Calculate average Stage 1 scores
        avg_scores = {}
        for model_name, score in stage1_scores:
            if model_name not in avg_scores:
                avg_scores[model_name] = []
            avg_scores[model_name].append(score)
        
        avg_scores = {k: np.mean(v) for k, v in avg_scores.items()}
        
        results = {
            'model_type': 'Hybrid Two-Stage Ensemble',
            'stage1_scores': avg_scores,
            'meta_learner_r2': meta_r2 if self.meta_learner else None,
            'n_features': len(X.columns),
            'n_samples': len(X),
            'feature_groups': {
                'spending': len(spending_cols),
                'options': len(options_cols),
                'earnings': len(earnings_cols),
                'insider': len(insider_cols)
            },
            'trained': True
        }
        
        # Cache models
        cache.set('hybrid_predictor', self, 86400)
        
        logger.info(f"Hybrid model trained: Meta-learner R² = {meta_r2:.4f}")
        return results
    
    async def predict(
        self,
        symbol: str,
        spending_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Make prediction using hybrid ensemble
        """
        if not self.meta_learner:
            # Fallback to spending model only
            return spending_predictor.predict_stock_return(spending_features)
        
        try:
            # Get all features
            options_feat = await self.options_features.get_options_features(symbol)
            earnings_feat = await self.earnings_insider.get_earnings_features(symbol)
            insider_feat = await self.earnings_insider.get_insider_features(symbol)
            
            # Stage 1: Get predictions from each model
            stage1_preds = {}
            
            if self.spending_model:
                spending_cols = [c for c in self.feature_names if 'spending' in c.lower() or 'user' in c.lower()]
                spending_vec = np.array([spending_features.get(c, 0.0) for c in spending_cols if c in spending_features])
                if len(spending_vec) == len(spending_cols):
                    stage1_preds['spending'] = self.spending_model.predict(spending_vec.reshape(1, -1))[0]
            
            if self.options_model:
                options_cols = [c for c in self.feature_names if any(x in c.lower() for x in ['put', 'call', 'unusual', 'sweep', 'iv', 'skew'])]
                options_vec = np.array([options_feat.get(c, 0.0) for c in options_cols])
                if len(options_vec) == len(options_cols):
                    stage1_preds['options'] = self.options_model.predict(options_vec.reshape(1, -1))[0]
            
            if self.earnings_model:
                earnings_cols = [c for c in self.feature_names if 'earnings' in c.lower() or 'surprise' in c.lower()]
                earnings_vec = np.array([earnings_feat.get(c, 0.0) for c in earnings_cols])
                if len(earnings_vec) == len(earnings_cols):
                    stage1_preds['earnings'] = self.earnings_model.predict(earnings_vec.reshape(1, -1))[0]
            
            if self.insider_model:
                insider_cols = [c for c in self.feature_names if 'insider' in c.lower()]
                insider_vec = np.array([insider_feat.get(c, 0.0) for c in insider_cols])
                if len(insider_vec) == len(insider_cols):
                    stage1_preds['insider'] = self.insider_model.predict(insider_vec.reshape(1, -1))[0]
            
            # Stage 2: Meta-learner prediction
            meta_features = pd.DataFrame([stage1_preds])
            # Add spending context
            if spending_cols:
                meta_features = pd.concat([meta_features, pd.DataFrame([{c: spending_features.get(c, 0.0) for c in spending_cols[:3]}])], axis=1)
            
            final_prediction = self.meta_learner.predict(meta_features)[0]
            
            # Calculate confidence
            confidence = 0.5 + 0.4 * min(1.0, abs(final_prediction) / 0.2)  # Higher for stronger signals
            
            # Generate reasoning
            reasoning_parts = []
            if 'spending' in stage1_preds and abs(stage1_preds['spending']) > 0.05:
                reasoning_parts.append(f"Spending signal: {stage1_preds['spending']:.2%}")
            if 'options' in stage1_preds and abs(stage1_preds['options']) > 0.05:
                reasoning_parts.append(f"Options flow: {stage1_preds['options']:.2%}")
            if 'earnings' in stage1_preds and abs(stage1_preds['earnings']) > 0.05:
                reasoning_parts.append(f"Earnings: {stage1_preds['earnings']:.2%}")
            if 'insider' in stage1_preds and abs(stage1_preds['insider']) > 0.05:
                reasoning_parts.append(f"Insider: {stage1_preds['insider']:.2%}")
            
            reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Hybrid ensemble prediction"
            
            return {
                'predicted_return': float(final_prediction),
                'excess_return_4w': float(final_prediction),
                'confidence': float(confidence),
                'reasoning': reasoning,
                'stage1_predictions': {k: float(v) for k, v in stage1_preds.items()},
                'feature_contributions': {
                    'spending': float(stage1_preds.get('spending', 0.0)),
                    'options': float(stage1_preds.get('options', 0.0)),
                    'earnings': float(stage1_preds.get('earnings', 0.0)),
                    'insider': float(stage1_preds.get('insider', 0.0))
                }
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid prediction: {e}")
            return spending_predictor.predict_stock_return(spending_features)


# Global instance
hybrid_predictor = HybridMLPredictor()

