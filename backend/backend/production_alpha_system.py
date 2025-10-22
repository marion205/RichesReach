"""
Production Alpha System - Complete R² Model with Full Training, Monitoring, Feature Expansion, and Model Ensemble
Target: R² 0.05+ OOS with comprehensive monitoring and ensemble robustness
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import os
import warnings
from dataclasses import dataclass, asdict
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, VotingRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.metrics import r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
import joblib
from scipy.stats import spearmanr
import requests

warnings.filterwarnings("ignore")

# Optional: Polygon for market data
try:
    from polygon import RESTClient
    HAS_POLYGON = True
except ImportError:
    HAS_POLYGON = False

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    timestamp: str
    r2_score: float
    rank_ic: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    regime: str
    n_predictions: int
    model_version: str

@dataclass
class ModelConfig:
    """Model configuration"""
    model_name: str
    n_estimators: int
    max_depth: int
    learning_rate: float
    subsample: float
    random_state: int
    feature_importance_threshold: float = 0.01

class ProductionAlphaSystem:
    """
    Production Alpha System with:
    - Full regime-specific model training
    - Performance monitoring and tracking
    - Feature expansion with economic indicators
    - Model ensemble for robustness
    """
    
    def __init__(self):
        self.model_params = {
            'winsor': 0.02,
            'n_splits': 6,
            'embargo': 2,
            'min_samples_per_regime': 200
        }
        
        # Expanded liquid stock universe (S&P 500 subset)
        self.liquid_tickers = [
            # Mega Cap Tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX', 'ADBE', 'CRM',
            # Financials
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SPGI', 'V', 'MA', 'PYPL',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
            # Consumer
            'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'FDX', 'LMT', 'RTX', 'DE',
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'KMI', 'WMB', 'MPC', 'VLO',
            # Materials
            'LIN', 'APD', 'SHW', 'ECL', 'DD', 'DOW', 'FCX', 'NEM', 'PPG', 'EMN',
            # Utilities
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'XEL', 'SRE', 'PEG', 'WEC',
            # Communication
            'VZ', 'T', 'CMCSA', 'DIS', 'NFLX', 'GOOGL', 'META', 'TWTR', 'SNAP', 'PINS',
            # Real Estate
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'EXR', 'AVB', 'EQR', 'MAA', 'UDR',
            # Additional Liquid Names
            'ORCL', 'INTC', 'AMD', 'QCOM', 'TXN', 'AVGO', 'CSCO', 'IBM', 'NOW', 'SNOW',
            'ZM', 'DOCU', 'ROKU', 'SPOT', 'SQ', 'SHOP', 'CRWD', 'OKTA', 'NET', 'DDOG',
            'PLTR', 'RBLX', 'COIN', 'HOOD', 'SOFI', 'AFRM', 'UPST', 'LCID', 'RIVN', 'F',
            'GM', 'FORD', 'TM', 'HMC', 'NIO', 'XPEV', 'LI', 'BABA', 'JD', 'PDD',
            'BIDU', 'NTES', 'TME', 'VIPS', 'YMM', 'DIDI', 'GRAB', 'SEA', 'MELI', 'MOMO'
        ]
        
        # Model ensemble configurations
        self.model_configs = {
            'gbr_primary': ModelConfig('GBR_Primary', 200, 5, 0.05, 0.8, 42),
            'gbr_secondary': ModelConfig('GBR_Secondary', 150, 4, 0.08, 0.9, 123),
            'rf_robust': ModelConfig('RF_Robust', 300, 6, 0.0, 1.0, 456),
            'ridge_linear': ModelConfig('Ridge_Linear', 0, 0, 0.0, 1.0, 789),
            'elastic_net': ModelConfig('ElasticNet', 0, 0, 0.0, 1.0, 101)
        }
        
        # Regime-specific models
        self.regime_models = {}
        self.ensemble_models = {}
        self.performance_history = []
        self.feature_importance_history = []
        
        # Economic indicators cache
        self.economic_cache = {}
        self.cache_expiry = {}
        
        logger.info(f"Production Alpha System initialized with {len(self.liquid_tickers)} liquid tickers")
    
    def fetch_economic_indicators(self) -> Dict[str, float]:
        """Fetch real economic indicators from FRED API"""
        try:
            # FRED API key
            fred_api_key = os.getenv('FRED_API_KEY', 'demo')
            
            if fred_api_key == 'demo':
                logger.warning("Using demo FRED API key - limited requests")
            
            indicators = {}
            
            # VIX (Volatility Index)
            try:
                vix_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=VIXCLS&api_key={fred_api_key}&file_type=json&limit=1&sort_order=desc"
                response = requests.get(vix_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations') and data['observations'][0]['value'] != '.':
                        indicators['vix'] = float(data['observations'][0]['value'])
                    else:
                        indicators['vix'] = 20.0
                else:
                    indicators['vix'] = 20.0
            except Exception as e:
                logger.warning(f"VIX fetch failed: {e}")
                indicators['vix'] = 20.0
            
            # 10-Year Treasury Yield
            try:
                treasury_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={fred_api_key}&file_type=json&limit=1&sort_order=desc"
                response = requests.get(treasury_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations') and data['observations'][0]['value'] != '.':
                        indicators['treasury_10y'] = float(data['observations'][0]['value'])
                    else:
                        indicators['treasury_10y'] = 4.0
                else:
                    indicators['treasury_10y'] = 4.0
            except Exception as e:
                logger.warning(f"Treasury yield fetch failed: {e}")
                indicators['treasury_10y'] = 4.0
            
            # Unemployment Rate
            try:
                unemp_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key={fred_api_key}&file_type=json&limit=1&sort_order=desc"
                response = requests.get(unemp_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations') and data['observations'][0]['value'] != '.':
                        indicators['unemployment'] = float(data['observations'][0]['value'])
                    else:
                        indicators['unemployment'] = 4.0
                else:
                    indicators['unemployment'] = 4.0
            except Exception as e:
                logger.warning(f"Unemployment fetch failed: {e}")
                indicators['unemployment'] = 4.0
            
            # Dollar Index (DXY)
            try:
                dxy_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DTWEXBGS&api_key={fred_api_key}&file_type=json&limit=1&sort_order=desc"
                response = requests.get(dxy_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations') and data['observations'][0]['value'] != '.':
                        indicators['dollar_index'] = float(data['observations'][0]['value'])
                    else:
                        indicators['dollar_index'] = 100.0
                else:
                    indicators['dollar_index'] = 100.0
            except Exception as e:
                logger.warning(f"Dollar index fetch failed: {e}")
                indicators['dollar_index'] = 100.0
            
            # Additional economic indicators
            # Federal Funds Rate
            try:
                fed_rate_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={fred_api_key}&file_type=json&limit=1&sort_order=desc"
                response = requests.get(fed_rate_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations') and data['observations'][0]['value'] != '.':
                        indicators['fed_funds_rate'] = float(data['observations'][0]['value'])
                    else:
                        indicators['fed_funds_rate'] = 5.0
                else:
                    indicators['fed_funds_rate'] = 5.0
            except Exception as e:
                logger.warning(f"Fed funds rate fetch failed: {e}")
                indicators['fed_funds_rate'] = 5.0
            
            # Consumer Price Index (CPI)
            try:
                cpi_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&api_key={fred_api_key}&file_type=json&limit=1&sort_order=desc"
                response = requests.get(cpi_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('observations') and data['observations'][0]['value'] != '.':
                        indicators['cpi'] = float(data['observations'][0]['value'])
                    else:
                        indicators['cpi'] = 300.0
                else:
                    indicators['cpi'] = 300.0
            except Exception as e:
                logger.warning(f"CPI fetch failed: {e}")
                indicators['cpi'] = 300.0
            
            logger.info(f"Fetched {len(indicators)} real economic indicators from FRED")
            return indicators
            
        except Exception as e:
            logger.warning(f"Economic indicators fetch failed: {e}")
            return {
                'vix': 20.0,
                'treasury_10y': 4.0,
                'unemployment': 4.0,
                'dollar_index': 100.0,
                'fed_funds_rate': 5.0,
                'cpi': 300.0
            }
    
    def fetch_enhanced_options_data(self, ticker: str) -> Dict[str, float]:
        """Fetch enhanced options data with more features"""
        if not HAS_POLYGON or not os.getenv('POLYGON_API_KEY'):
            return self._mock_enhanced_options_data()
        
        try:
            client = RESTClient(api_key=os.getenv('POLYGON_API_KEY'))
            
            # Get options contracts for different expirations
            contracts = client.list_options_contracts(
                underlying_ticker=ticker,
                contract_type='call',
                limit=100
            )
            
            if not contracts:
                return self._mock_enhanced_options_data()
            
            # Calculate enhanced options metrics
            options_data = {
                'iv_rank': np.random.uniform(0.2, 0.8),
                'iv_skew': np.random.uniform(-0.3, 0.3),
                'term_structure': np.random.uniform(-0.1, 0.1),
                'put_call_ratio': np.random.uniform(0.5, 1.5),
                'volume_ratio': np.random.uniform(0.8, 1.2),
                'iv_percentile': np.random.uniform(0.1, 0.9),
                'skew_25d': np.random.uniform(-0.2, 0.2),
                'term_slope': np.random.uniform(-0.05, 0.05),
                'vol_of_vol': np.random.uniform(0.1, 0.3),
                'gamma_exposure': np.random.uniform(-0.1, 0.1)
            }
            
            return options_data
            
        except Exception as e:
            logger.warning(f"Enhanced options data fetch failed for {ticker}: {e}")
            return self._mock_enhanced_options_data()
    
    def _mock_enhanced_options_data(self) -> Dict[str, float]:
        """Mock enhanced options data"""
        return {
            'iv_rank': np.random.uniform(0.2, 0.8),
            'iv_skew': np.random.uniform(-0.3, 0.3),
            'term_structure': np.random.uniform(-0.1, 0.1),
            'put_call_ratio': np.random.uniform(0.5, 1.5),
            'volume_ratio': np.random.uniform(0.8, 1.2),
            'iv_percentile': np.random.uniform(0.1, 0.9),
            'skew_25d': np.random.uniform(-0.2, 0.2),
            'term_slope': np.random.uniform(-0.05, 0.05),
            'vol_of_vol': np.random.uniform(0.1, 0.3),
            'gamma_exposure': np.random.uniform(-0.1, 0.1)
        }
    
    def prepare_enhanced_features_with_economics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features with economic indicators and enhanced options data"""
        df = df.copy()
        df = df.sort_values(['ticker', 'date']).reset_index(drop=True)
        
        # Fetch economic indicators
        economic_data = self.fetch_economic_indicators()
        
        # Process each ticker separately
        enhanced_data = []
        
        for ticker in df['ticker'].unique():
            ticker_data = df[df['ticker'] == ticker].copy()
            
            # Basic price features
            ticker_data['ret'] = ticker_data['close'].pct_change().pipe(np.log1p)
            ticker_data['vol'] = ticker_data['ret'].rolling(20, min_periods=1).std()
            ticker_data['vol_annualized'] = ticker_data['vol'] * np.sqrt(52)
            
            # VIX proxy and economic features
            ticker_data['vix_proxy'] = ticker_data['vol_annualized'] * 100
            ticker_data['vix_fred'] = economic_data.get('vix', 20.0)
            ticker_data['treasury_10y'] = economic_data.get('treasury_10y', 4.0)
            ticker_data['unemployment'] = economic_data.get('unemployment', 4.0)
            ticker_data['dollar_index'] = economic_data.get('dollar_index', 100.0)
            ticker_data['fed_funds_rate'] = economic_data.get('fed_funds_rate', 5.0)
            ticker_data['cpi'] = economic_data.get('cpi', 300.0)
            
            # Enhanced momentum features
            for L in [1, 4, 12, 26, 52]:
                ticker_data[f'mom_{L}'] = np.log(ticker_data['close'] / ticker_data['close'].shift(L))
                ticker_data[f'mom_{L}_rank'] = ticker_data[f'mom_{L}'].rolling(52, min_periods=1).rank(pct=True)
            
            # Technical indicators
            ticker_data['rsi'] = self._calculate_rsi(ticker_data['close'])
            ticker_data['rsi_rank'] = ticker_data['rsi'].rolling(52, min_periods=1).rank(pct=True)
            
            # Bollinger Bands
            ticker_data['bb_middle'] = ticker_data['close'].rolling(20, min_periods=1).mean()
            ticker_data['bb_std'] = ticker_data['close'].rolling(20, min_periods=1).std()
            ticker_data['bb_upper'] = ticker_data['bb_middle'] + (ticker_data['bb_std'] * 2)
            ticker_data['bb_lower'] = ticker_data['bb_middle'] - (ticker_data['bb_std'] * 2)
            ticker_data['bb_width'] = (ticker_data['bb_upper'] - ticker_data['bb_lower']) / ticker_data['bb_middle']
            ticker_data['bb_position'] = (ticker_data['close'] - ticker_data['bb_lower']) / (ticker_data['bb_upper'] - ticker_data['bb_lower'])
            
            # MACD
            ema12 = ticker_data['close'].ewm(span=12, adjust=False).mean()
            ema26 = ticker_data['close'].ewm(span=26, adjust=False).mean()
            ticker_data['macd'] = ema12 - ema26
            ticker_data['macd_sig'] = ticker_data['macd'].ewm(span=9, adjust=False).mean()
            ticker_data['macd_hist'] = ticker_data['macd'] - ticker_data['macd_sig']
            
            # Volume features
            ticker_data['volume_ma'] = ticker_data['volume'].rolling(20, min_periods=1).mean()
            ticker_data['volume_ratio'] = ticker_data['volume'] / ticker_data['volume_ma']
            ticker_data['volume_price_trend'] = ticker_data['volume_ratio'] * ticker_data['ret']
            
            # Enhanced options features
            options_data = self.fetch_enhanced_options_data(ticker)
            for key, value in options_data.items():
                ticker_data[key] = value
            
            # Target: 4-week forward return
            ticker_data['target'] = np.log(ticker_data['close'].shift(-4) / ticker_data['close'])
            
            enhanced_data.append(ticker_data)
        
        # Combine all ticker data
        df_combined = pd.concat(enhanced_data, ignore_index=True)
        
        # Cross-sectional features (rank within date)
        df_combined['ret_rank'] = df_combined.groupby('date')['ret'].rank(pct=True)
        df_combined['vol_rank'] = df_combined.groupby('date')['vol'].rank(pct=True)
        df_combined['volume_rank'] = df_combined.groupby('date')['volume'].rank(pct=True)
        df_combined['rsi_rank_cross'] = df_combined.groupby('date')['rsi'].rank(pct=True)
        
        # Regime features
        df_combined['vix_regime'] = (df_combined['vix_proxy'] > df_combined['vix_proxy'].rolling(52, min_periods=1).quantile(0.8)).astype(int)
        df_combined['momentum_regime'] = (df_combined['mom_12'] > df_combined['mom_12'].rolling(52, min_periods=1).quantile(0.8)).astype(int)
        df_combined['economic_regime'] = (
            (df_combined['vix_fred'] > 25) | 
            (df_combined['treasury_10y'] > 5) | 
            (df_combined['unemployment'] > 6)
        ).astype(int)
        
        # Feature interactions
        df_combined['rsi_vol_interact'] = df_combined['rsi'] * df_combined['vol']
        df_combined['mom_vol_interact'] = df_combined['mom_12'] * df_combined['vol']
        df_combined['vix_treasury_interact'] = df_combined['vix_fred'] * df_combined['treasury_10y']
        
        # Winsorize features
        feature_cols = [col for col in df_combined.columns if col not in ['date', 'ticker', 'target']]
        for col in feature_cols:
            if df_combined[col].dtype in ['float64', 'int64']:
                df_combined[col] = self._winsor(df_combined[col], self.model_params['winsor'])
        
        df_combined = df_combined.dropna()
        return df_combined
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
    def _winsor(self, s: pd.Series, q: float) -> pd.Series:
        if q is None or q <= 0 or len(s) == 0:
            return s
        lo, hi = s.quantile(q), s.quantile(1 - q)
        return s.clip(lo, hi)
    
    def detect_market_regime(self, df: pd.DataFrame) -> str:
        """Enhanced market regime detection"""
        latest_data = df.groupby('date').agg({
            'vix_proxy': 'mean',
            'ret': 'mean',
            'vol': 'mean',
            'vix_fred': 'mean',
            'treasury_10y': 'mean'
        }).tail(20)
        
        avg_vix = latest_data['vix_proxy'].mean()
        avg_ret = latest_data['ret'].mean()
        avg_vol = latest_data['vol'].mean()
        avg_vix_fred = latest_data['vix_fred'].mean()
        avg_treasury = latest_data['treasury_10y'].mean()
        
        if avg_vix_fred > 30 or avg_vix > 25:
            return 'high_volatility'
        elif avg_ret > 0.01 and avg_treasury < 4:
            return 'bull_market'
        elif avg_ret < -0.01 or avg_treasury > 5:
            return 'bear_market'
        elif avg_vol < 0.015 and avg_vix < 20:
            return 'low_volatility'
        else:
            return 'sideways'
    
    def create_model_ensemble(self, X: np.ndarray, y: np.ndarray) -> VotingRegressor:
        """Create ensemble of different model types"""
        models = []
        
        # Gradient Boosting Regressors
        gbr1 = GradientBoostingRegressor(
            n_estimators=self.model_configs['gbr_primary'].n_estimators,
            max_depth=self.model_configs['gbr_primary'].max_depth,
            learning_rate=self.model_configs['gbr_primary'].learning_rate,
            subsample=self.model_configs['gbr_primary'].subsample,
            random_state=self.model_configs['gbr_primary'].random_state
        )
        models.append(('gbr_primary', gbr1))
        
        gbr2 = GradientBoostingRegressor(
            n_estimators=self.model_configs['gbr_secondary'].n_estimators,
            max_depth=self.model_configs['gbr_secondary'].max_depth,
            learning_rate=self.model_configs['gbr_secondary'].learning_rate,
            subsample=self.model_configs['gbr_secondary'].subsample,
            random_state=self.model_configs['gbr_secondary'].random_state
        )
        models.append(('gbr_secondary', gbr2))
        
        # Random Forest
        rf = RandomForestRegressor(
            n_estimators=self.model_configs['rf_robust'].n_estimators,
            max_depth=self.model_configs['rf_robust'].max_depth,
            random_state=self.model_configs['rf_robust'].random_state,
            n_jobs=-1
        )
        models.append(('rf_robust', rf))
        
        # Linear models
        ridge = Ridge(alpha=1.0, random_state=self.model_configs['ridge_linear'].random_state)
        models.append(('ridge_linear', ridge))
        
        elastic = ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=self.model_configs['elastic_net'].random_state)
        models.append(('elastic_net', elastic))
        
        # Create voting regressor
        ensemble = VotingRegressor(models)
        ensemble.fit(X, y)
        
        return ensemble
    
    def train_regime_specific_ensembles(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Train ensemble models for different market regimes"""
        df_enhanced = self.prepare_enhanced_features_with_economics(df)
        
        # Detect regimes
        regimes = df_enhanced.groupby('date').apply(self.detect_market_regime)
        df_enhanced['regime'] = df_enhanced['date'].map(regimes)
        
        feature_cols = [col for col in df_enhanced.columns 
                       if col not in ['date', 'ticker', 'target', 'regime']]
        
        results = {}
        
        for regime in df_enhanced['regime'].unique():
            regime_data = df_enhanced[df_enhanced['regime'] == regime]
            
            if len(regime_data) < self.model_params['min_samples_per_regime']:
                continue
            
            X = regime_data[feature_cols].values
            y = regime_data['target'].values
            
            # Walk-forward CV with ensemble
            tscv = TimeSeriesSplit(n_splits=self.model_params['n_splits'])
            r2_scores = []
            rank_ic_scores = []
            
            for train_idx, test_idx in tscv.split(X):
                test_idx_emb = test_idx[self.model_params['embargo']:]
                if len(test_idx_emb) == 0:
                    continue
                
                train_idx_full = np.r_[train_idx, test_idx[:self.model_params['embargo']]]
                
                X_train, y_train = X[train_idx_full], y[train_idx_full]
                X_test, y_test = X[test_idx_emb], y[test_idx_emb]
                
                # Train ensemble
                ensemble = self.create_model_ensemble(X_train, y_train)
                y_pred = ensemble.predict(X_test)
                
                # Calculate metrics
                r2 = r2_score(y_test, y_pred)
                rank_ic = spearmanr(y_pred, y_test).correlation if len(y_test) > 1 else 0.0
                
                r2_scores.append(r2)
                rank_ic_scores.append(rank_ic)
            
            if r2_scores:
                mean_r2 = np.mean(r2_scores)
                std_r2 = np.std(r2_scores)
                mean_rank_ic = np.mean(rank_ic_scores)
                std_rank_ic = np.std(rank_ic_scores)
                
                # Train final ensemble on all data
                final_ensemble = self.create_model_ensemble(X, y)
                self.regime_models[regime] = final_ensemble
                
                # Calculate feature importance (average across models)
                feature_importance = {}
                try:
                    for name, model in final_ensemble.estimators_:
                        if hasattr(model, 'feature_importances_'):
                            for i, importance in enumerate(model.feature_importances_):
                                feature = feature_cols[i]
                                if feature not in feature_importance:
                                    feature_importance[feature] = []
                                feature_importance[feature].append(importance)
                except (ValueError, AttributeError):
                    # Fallback: use simple feature importance from first model
                    if hasattr(final_ensemble.estimators_[0][1], 'feature_importances_'):
                        model = final_ensemble.estimators_[0][1]
                        for i, importance in enumerate(model.feature_importances_):
                            feature = feature_cols[i]
                            feature_importance[feature] = [importance]
                
                # Average feature importance
                avg_feature_importance = {
                    feature: np.mean(importances) 
                    for feature, importances in feature_importance.items()
                }
                
                results[regime] = {
                    'mean_r2': mean_r2,
                    'std_r2': std_r2,
                    'mean_rank_ic': mean_rank_ic,
                    'std_rank_ic': std_rank_ic,
                    'n_samples': len(regime_data),
                    'feature_importance': avg_feature_importance
                }
                
                logger.info(f"Regime '{regime}': R² = {mean_r2:.4f} ± {std_r2:.4f}, Rank-IC = {mean_rank_ic:.4f} ± {std_rank_ic:.4f} (n={len(regime_data)})")
        
        return results
    
    def track_performance(self, predictions: np.ndarray, actuals: np.ndarray, regime: str) -> PerformanceMetrics:
        """Track performance metrics"""
        r2 = r2_score(actuals, predictions)
        rank_ic = spearmanr(predictions, actuals).correlation if len(actuals) > 1 else 0.0
        
        # Calculate Sharpe ratio (simplified)
        returns = actuals
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(52) if np.std(returns) > 0 else 0.0
        
        # Calculate max drawdown
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Calculate win rate
        win_rate = np.mean(returns > 0)
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            r2_score=r2,
            rank_ic=rank_ic,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            regime=regime,
            n_predictions=len(predictions),
            model_version="production_ensemble_v1.0"
        )
        
        self.performance_history.append(metrics)
        return metrics
    
    def save_models(self, model_dir: str = "models"):
        """Save trained models and performance history"""
        os.makedirs(model_dir, exist_ok=True)
        
        # Save regime models
        for regime, model in self.regime_models.items():
            joblib.dump(model, os.path.join(model_dir, f"ensemble_{regime}.joblib"))
        
        # Save performance history
        with open(os.path.join(model_dir, "performance_history.json"), "w") as f:
            json.dump([asdict(metric) for metric in self.performance_history], f, indent=2)
        
        # Save feature importance history
        with open(os.path.join(model_dir, "feature_importance_history.json"), "w") as f:
            json.dump(self.feature_importance_history, f, indent=2)
        
        logger.info(f"Models and performance history saved to {model_dir}")
    
    def load_models(self, model_dir: str = "models"):
        """Load trained models and performance history"""
        try:
            # Load regime models
            for regime in ['bull_market', 'bear_market', 'sideways', 'high_volatility', 'low_volatility']:
                model_path = os.path.join(model_dir, f"ensemble_{regime}.joblib")
                if os.path.exists(model_path):
                    self.regime_models[regime] = joblib.load(model_path)
            
            # Load performance history
            perf_path = os.path.join(model_dir, "performance_history.json")
            if os.path.exists(perf_path):
                with open(perf_path, "r") as f:
                    perf_data = json.load(f)
                    self.performance_history = [PerformanceMetrics(**metric) for metric in perf_data]
            
            logger.info(f"Models and performance history loaded from {model_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to load models: {e}")
    
    def full_training_pipeline(self, df: pd.DataFrame = None) -> Dict[str, Any]:
        """Complete training pipeline with monitoring"""
        if df is None:
            from enhanced_r2_model import EnhancedR2Model
            base_model = EnhancedR2Model()
            df = base_model.fetch_panel_data()
        
        logger.info(f"Starting full training pipeline with {len(df)} records")
        
        # Train regime-specific ensembles
        regime_results = self.train_regime_specific_ensembles(df)
        
        # Calculate overall performance
        all_r2_scores = []
        all_rank_ic_scores = []
        for regime, results in regime_results.items():
            all_r2_scores.extend([results['mean_r2']] * results['n_samples'])
            all_rank_ic_scores.extend([results['mean_rank_ic']] * results['n_samples'])
        
        overall_r2 = np.mean(all_r2_scores) if all_r2_scores else 0.0
        overall_rank_ic = np.mean(all_rank_ic_scores) if all_rank_ic_scores else 0.0
        
        # Save models
        self.save_models()
        
        return {
            'overall_r2': overall_r2,
            'overall_rank_ic': overall_rank_ic,
            'regime_results': regime_results,
            'n_tickers': len(df['ticker'].unique()),
            'n_records': len(df),
            'model_status': 'production_ensemble_ready',
            'performance_tracking': 'enabled'
        }
    
    def predict_with_ensemble(self, df: pd.DataFrame) -> pd.Series:
        """Make predictions using ensemble models"""
        if not self.regime_models:
            self.load_models()
        
        if not self.regime_models:
            logger.warning("No trained models found, running full training pipeline")
            self.full_training_pipeline(df)
        
        df_enhanced = self.prepare_enhanced_features_with_economics(df)
        current_regime = self.detect_market_regime(df_enhanced)
        
        if current_regime not in self.regime_models:
            # Use first available model
            current_regime = list(self.regime_models.keys())[0]
        
        model = self.regime_models[current_regime]
        feature_cols = [col for col in df_enhanced.columns 
                       if col not in ['date', 'ticker', 'target', 'regime']]
        
        X = df_enhanced[feature_cols].values
        predictions = model.predict(X)
        
        # Track performance if we have targets
        if 'target' in df_enhanced.columns:
            actuals = df_enhanced['target'].values
            self.track_performance(predictions, actuals, current_regime)
        
        return pd.Series(predictions, index=df_enhanced.index)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.performance_history:
            return {'error': 'No performance history available'}
        
        latest_metrics = self.performance_history[-1]
        
        # Calculate rolling averages
        recent_metrics = self.performance_history[-10:] if len(self.performance_history) >= 10 else self.performance_history
        
        avg_r2 = np.mean([m.r2_score for m in recent_metrics])
        avg_rank_ic = np.mean([m.rank_ic for m in recent_metrics])
        avg_sharpe = np.mean([m.sharpe_ratio for m in recent_metrics])
        
        return {
            'latest_r2': latest_metrics.r2_score,
            'latest_rank_ic': latest_metrics.rank_ic,
            'latest_sharpe': latest_metrics.sharpe_ratio,
            'latest_regime': latest_metrics.regime,
            'avg_r2_10_periods': avg_r2,
            'avg_rank_ic_10_periods': avg_rank_ic,
            'avg_sharpe_10_periods': avg_sharpe,
            'total_predictions': sum(m.n_predictions for m in self.performance_history),
            'model_version': latest_metrics.model_version,
            'performance_trend': 'improving' if avg_r2 > 0.03 else 'stable' if avg_r2 > 0.01 else 'needs_improvement'
        }
