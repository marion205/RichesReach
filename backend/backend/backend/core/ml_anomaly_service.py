import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.contrib.auth.models import User
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from scipy import stats
from .models_smart_alerts import MLAnomalyDetection, SmartAlert
from .yodlee_service import yodlee_service
from .real_market_data_service import real_market_data_service

logger = logging.getLogger(__name__)

class MLAnomalyService:
    """Service for ML-driven anomaly detection in portfolio behavior"""
    
    def __init__(self):
        self.yodlee_service = yodlee_service
        self.market_service = real_market_data_service
        self.models = {}  # Cache trained models per user
        self.scalers = {}  # Cache scalers per user
    
    async def detect_anomalies(self, user: User, portfolio_id: str = None, 
                             time_window: str = '30d') -> List[Dict[str, Any]]:
        """Detect anomalies in user's portfolio behavior"""
        try:
            anomalies = []
            
            # Get user's historical data
            historical_data = await self._get_historical_data(user, portfolio_id, time_window)
            
            if not historical_data or len(historical_data) < 10:
                logger.warning(f"Insufficient data for anomaly detection for user {user.id}")
                return []
            
            # Detect different types of anomalies
            anomalies.extend(await self._detect_trading_anomalies(user, historical_data))
            anomalies.extend(await self._detect_allocation_anomalies(user, historical_data))
            anomalies.extend(await self._detect_performance_anomalies(user, historical_data))
            anomalies.extend(await self._detect_cash_flow_anomalies(user, historical_data))
            anomalies.extend(await self._detect_risk_anomalies(user, historical_data))
            
            # Store anomalies in database
            await self._store_anomalies(user, anomalies)
            
            # Generate alerts for significant anomalies
            alert_anomalies = await self._generate_anomaly_alerts(user, anomalies)
            
            return alert_anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for user {user.id}: {e}")
            return []
    
    async def _get_historical_data(self, user: User, portfolio_id: str, time_window: str) -> Dict[str, Any]:
        """Get historical portfolio data for analysis"""
        try:
            # Calculate date range
            days = int(time_window.replace('d', ''))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get portfolio data from Yodlee
            portfolio_data = await self.yodlee_service.get_portfolio_history(
                user, start_date, end_date
            )
            
            # Get transaction data
            transaction_data = await self.yodlee_service.get_transaction_history(
                user, start_date, end_date
            )
            
            # Get market data for comparison
            market_data = await self.market_service.get_market_history(
                start_date, end_date
            )
            
            return {
                'portfolio': portfolio_data,
                'transactions': transaction_data,
                'market': market_data,
                'start_date': start_date,
                'end_date': end_date,
                'time_window': time_window
            }
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return {}
    
    async def _detect_trading_anomalies(self, user: User, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in trading behavior"""
        try:
            anomalies = []
            transactions = data.get('transactions', [])
            
            if not transactions:
                return anomalies
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
            # Feature engineering
            features = self._extract_trading_features(df)
            
            if len(features) < 10:
                return anomalies
            
            # Detect anomalies using Isolation Forest
            anomaly_scores = self._detect_isolation_forest_anomalies(features)
            
            # Analyze specific trading patterns
            anomalies.extend(self._analyze_trading_frequency_anomalies(df, anomaly_scores))
            anomalies.extend(self._analyze_trading_amount_anomalies(df, anomaly_scores))
            anomalies.extend(self._analyze_trading_timing_anomalies(df, anomaly_scores))
            anomalies.extend(self._analyze_trading_pattern_anomalies(df, anomaly_scores))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting trading anomalies: {e}")
            return []
    
    async def _detect_allocation_anomalies(self, user: User, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in portfolio allocation"""
        try:
            anomalies = []
            portfolio_data = data.get('portfolio', [])
            
            if not portfolio_data:
                return anomalies
            
            # Convert to DataFrame
            df = pd.DataFrame(portfolio_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Analyze allocation changes over time
            allocation_features = self._extract_allocation_features(df)
            
            if len(allocation_features) < 5:
                return anomalies
            
            # Detect sudden allocation changes
            anomalies.extend(self._analyze_allocation_drift_anomalies(allocation_features))
            anomalies.extend(self._analyze_concentration_anomalies(allocation_features))
            anomalies.extend(self._analyze_rebalancing_anomalies(allocation_features))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting allocation anomalies: {e}")
            return []
    
    async def _detect_performance_anomalies(self, user: User, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in portfolio performance"""
        try:
            anomalies = []
            portfolio_data = data.get('portfolio', [])
            market_data = data.get('market', [])
            
            if not portfolio_data or not market_data:
                return anomalies
            
            # Convert to DataFrames
            portfolio_df = pd.DataFrame(portfolio_data)
            market_df = pd.DataFrame(market_data)
            
            portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
            market_df['date'] = pd.to_datetime(market_df['date'])
            
            # Calculate performance metrics
            performance_features = self._extract_performance_features(portfolio_df, market_df)
            
            if len(performance_features) < 10:
                return anomalies
            
            # Detect performance anomalies
            anomalies.extend(self._analyze_volatility_anomalies(performance_features))
            anomalies.extend(self._analyze_correlation_anomalies(performance_features))
            anomalies.extend(self._analyze_alpha_anomalies(performance_features))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting performance anomalies: {e}")
            return []
    
    async def _detect_cash_flow_anomalies(self, user: User, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in cash flow patterns"""
        try:
            anomalies = []
            transactions = data.get('transactions', [])
            
            if not transactions:
                return anomalies
            
            # Convert to DataFrame
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
            # Analyze cash flow patterns
            cash_flow_features = self._extract_cash_flow_features(df)
            
            if len(cash_flow_features) < 10:
                return anomalies
            
            # Detect cash flow anomalies
            anomalies.extend(self._analyze_spending_anomalies(cash_flow_features))
            anomalies.extend(self._analyze_income_anomalies(cash_flow_features))
            anomalies.extend(self._analyze_cash_position_anomalies(cash_flow_features))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting cash flow anomalies: {e}")
            return []
    
    async def _detect_risk_anomalies(self, user: User, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in risk metrics"""
        try:
            anomalies = []
            portfolio_data = data.get('portfolio', [])
            
            if not portfolio_data:
                return anomalies
            
            # Convert to DataFrame
            df = pd.DataFrame(portfolio_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Calculate risk metrics
            risk_features = self._extract_risk_features(df)
            
            if len(risk_features) < 10:
                return anomalies
            
            # Detect risk anomalies
            anomalies.extend(self._analyze_var_anomalies(risk_features))
            anomalies.extend(self._analyze_drawdown_anomalies(risk_features))
            anomalies.extend(self._analyze_beta_anomalies(risk_features))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting risk anomalies: {e}")
            return []
    
    def _extract_trading_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features for trading behavior analysis"""
        try:
            features = []
            
            # Daily trading volume
            daily_volume = df.groupby(df['date'].dt.date)['amount'].sum()
            features.append(daily_volume.values)
            
            # Number of transactions per day
            daily_count = df.groupby(df['date'].dt.date).size()
            features.append(daily_count.values)
            
            # Transaction amounts
            features.append(df['amount'].values)
            
            # Time between transactions
            df_sorted = df.sort_values('date')
            time_diffs = df_sorted['date'].diff().dt.total_seconds() / 3600  # hours
            features.append(time_diffs.dropna().values)
            
            # Combine features
            max_len = max(len(f) for f in features if len(f) > 0)
            combined_features = []
            
            for feature in features:
                if len(feature) > 0:
                    # Pad or truncate to max_len
                    if len(feature) < max_len:
                        padded = np.pad(feature, (0, max_len - len(feature)), 'constant')
                    else:
                        padded = feature[:max_len]
                    combined_features.append(padded)
            
            return np.column_stack(combined_features) if combined_features else np.array([])
            
        except Exception as e:
            logger.error(f"Error extracting trading features: {e}")
            return np.array([])
    
    def _extract_allocation_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features for allocation analysis"""
        try:
            features = []
            
            # Portfolio value over time
            if 'total_value' in df.columns:
                features.append(df['total_value'].values)
            
            # Allocation percentages by asset class
            asset_columns = [col for col in df.columns if col.endswith('_allocation')]
            for col in asset_columns:
                features.append(df[col].values)
            
            # Cash percentage
            if 'cash_percentage' in df.columns:
                features.append(df['cash_percentage'].values)
            
            return np.column_stack(features) if features else np.array([])
            
        except Exception as e:
            logger.error(f"Error extracting allocation features: {e}")
            return np.array([])
    
    def _extract_performance_features(self, portfolio_df: pd.DataFrame, market_df: pd.DataFrame) -> np.ndarray:
        """Extract features for performance analysis"""
        try:
            features = []
            
            # Portfolio returns
            if 'total_value' in portfolio_df.columns:
                portfolio_returns = portfolio_df['total_value'].pct_change().dropna()
                features.append(portfolio_returns.values)
            
            # Market returns
            if 'close' in market_df.columns:
                market_returns = market_df['close'].pct_change().dropna()
                features.append(market_returns.values)
            
            # Volatility
            if len(portfolio_returns) > 0:
                volatility = portfolio_returns.rolling(window=5).std().dropna()
                features.append(volatility.values)
            
            return np.column_stack(features) if features else np.array([])
            
        except Exception as e:
            logger.error(f"Error extracting performance features: {e}")
            return np.array([])
    
    def _extract_cash_flow_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features for cash flow analysis"""
        try:
            features = []
            
            # Daily cash flow
            daily_cashflow = df.groupby(df['date'].dt.date)['amount'].sum()
            features.append(daily_cashflow.values)
            
            # Spending patterns (negative amounts)
            spending = df[df['amount'] < 0]['amount'].values
            features.append(spending)
            
            # Income patterns (positive amounts)
            income = df[df['amount'] > 0]['amount'].values
            features.append(income)
            
            return np.column_stack(features) if features else np.array([])
            
        except Exception as e:
            logger.error(f"Error extracting cash flow features: {e}")
            return np.array([])
    
    def _extract_risk_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features for risk analysis"""
        try:
            features = []
            
            # Portfolio value for VaR calculation
            if 'total_value' in df.columns:
                returns = df['total_value'].pct_change().dropna()
                features.append(returns.values)
            
            # Drawdown
            if 'total_value' in df.columns:
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                features.append(drawdown.values)
            
            return np.column_stack(features) if features else np.array([])
            
        except Exception as e:
            logger.error(f"Error extracting risk features: {e}")
            return np.array([])
    
    def _detect_isolation_forest_anomalies(self, features: np.ndarray) -> np.ndarray:
        """Detect anomalies using Isolation Forest"""
        try:
            if len(features) < 10:
                return np.array([])
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Fit Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_scores = iso_forest.fit_predict(features_scaled)
            
            return anomaly_scores
            
        except Exception as e:
            logger.error(f"Error in isolation forest detection: {e}")
            return np.array([])
    
    def _analyze_trading_frequency_anomalies(self, df: pd.DataFrame, anomaly_scores: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze trading frequency anomalies"""
        try:
            anomalies = []
            
            # Calculate daily trading frequency
            daily_freq = df.groupby(df['date'].dt.date).size()
            
            # Detect sudden changes in frequency
            freq_changes = daily_freq.diff().abs()
            threshold = freq_changes.quantile(0.95)  # Top 5% of changes
            
            for date, change in freq_changes.items():
                if change > threshold and change > 5:  # Significant increase
                    anomalies.append({
                        'type': 'trading_frequency_spike',
                        'anomaly_score': min(change / 10, 1.0),  # Normalize to 0-1
                        'confidence': 0.8,
                        'description': f"Trading frequency spiked to {daily_freq[date]} transactions on {date}",
                        'details': {
                            'date': date.isoformat(),
                            'frequency': int(daily_freq[date]),
                            'change': int(change),
                            'threshold': int(threshold)
                        },
                        'severity': 'high' if change > threshold * 2 else 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing trading frequency anomalies: {e}")
            return []
    
    def _analyze_trading_amount_anomalies(self, df: pd.DataFrame, anomaly_scores: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze trading amount anomalies"""
        try:
            anomalies = []
            
            # Detect unusually large transactions
            amount_threshold = df['amount'].quantile(0.99)  # Top 1% of amounts
            
            large_transactions = df[df['amount'] > amount_threshold]
            
            for _, transaction in large_transactions.iterrows():
                anomalies.append({
                    'type': 'large_transaction',
                    'anomaly_score': min(transaction['amount'] / amount_threshold, 1.0),
                    'confidence': 0.9,
                    'description': f"Unusually large transaction of ${transaction['amount']:,.2f}",
                    'details': {
                        'amount': float(transaction['amount']),
                        'date': transaction['date'].isoformat(),
                        'threshold': float(amount_threshold)
                    },
                    'severity': 'high'
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing trading amount anomalies: {e}")
            return []
    
    def _analyze_trading_timing_anomalies(self, df: pd.DataFrame, anomaly_scores: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze trading timing anomalies"""
        try:
            anomalies = []
            
            # Detect unusual trading times (outside market hours)
            df['hour'] = df['date'].dt.hour
            after_hours = df[(df['hour'] < 9) | (df['hour'] > 16)]
            
            if len(after_hours) > 0:
                anomalies.append({
                    'type': 'after_hours_trading',
                    'anomaly_score': len(after_hours) / len(df),
                    'confidence': 0.7,
                    'description': f"{len(after_hours)} transactions occurred outside market hours",
                    'details': {
                        'count': len(after_hours),
                        'percentage': len(after_hours) / len(df) * 100
                    },
                    'severity': 'medium'
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing trading timing anomalies: {e}")
            return []
    
    def _analyze_trading_pattern_anomalies(self, df: pd.DataFrame, anomaly_scores: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze trading pattern anomalies"""
        try:
            anomalies = []
            
            # Detect clustering of transactions (potential panic selling/buying)
            df_sorted = df.sort_values('date')
            time_diffs = df_sorted['date'].diff().dt.total_seconds() / 60  # minutes
            
            # Find clusters of transactions within short time periods
            clusters = []
            current_cluster = []
            
            for i, diff in enumerate(time_diffs):
                if diff < 30:  # Within 30 minutes
                    current_cluster.append(i)
                else:
                    if len(current_cluster) > 3:  # More than 3 transactions in cluster
                        clusters.append(current_cluster)
                    current_cluster = [i]
            
            for cluster in clusters:
                cluster_transactions = df_sorted.iloc[cluster]
                total_amount = cluster_transactions['amount'].sum()
                
                anomalies.append({
                    'type': 'transaction_clustering',
                    'anomaly_score': min(len(cluster) / 10, 1.0),
                    'confidence': 0.8,
                    'description': f"Cluster of {len(cluster)} transactions totaling ${total_amount:,.2f}",
                    'details': {
                        'count': len(cluster),
                        'total_amount': float(total_amount),
                        'time_span': float((cluster_transactions['date'].max() - cluster_transactions['date'].min()).total_seconds() / 60)
                    },
                    'severity': 'high' if len(cluster) > 5 else 'medium'
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing trading pattern anomalies: {e}")
            return []
    
    def _analyze_allocation_drift_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze allocation drift anomalies"""
        try:
            anomalies = []
            
            # Calculate allocation changes over time
            if features.shape[1] > 1:
                allocation_changes = np.diff(features, axis=0)
                
                # Detect large allocation changes
                change_threshold = np.percentile(np.abs(allocation_changes), 95)
                
                for i, change in enumerate(allocation_changes):
                    max_change = np.max(np.abs(change))
                    if max_change > change_threshold:
                        anomalies.append({
                            'type': 'allocation_drift',
                            'anomaly_score': min(max_change / change_threshold, 1.0),
                            'confidence': 0.8,
                            'description': f"Significant allocation change detected",
                            'details': {
                                'max_change': float(max_change),
                                'threshold': float(change_threshold),
                                'period': i
                            },
                            'severity': 'medium'
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing allocation drift anomalies: {e}")
            return []
    
    def _analyze_concentration_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze concentration anomalies"""
        try:
            anomalies = []
            
            # Calculate concentration metrics
            for i, allocation in enumerate(features):
                # Calculate Herfindahl-Hirschman Index (concentration measure)
                hhi = np.sum(allocation ** 2)
                
                if hhi > 0.5:  # High concentration threshold
                    anomalies.append({
                        'type': 'high_concentration',
                        'anomaly_score': min(hhi, 1.0),
                        'confidence': 0.9,
                        'description': f"Portfolio concentration is high (HHI: {hhi:.3f})",
                        'details': {
                            'hhi': float(hhi),
                            'period': i
                        },
                        'severity': 'high' if hhi > 0.7 else 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing concentration anomalies: {e}")
            return []
    
    def _analyze_rebalancing_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze rebalancing anomalies"""
        try:
            anomalies = []
            
            # Detect frequent rebalancing
            if len(features) > 5:
                changes = np.diff(features, axis=0)
                change_magnitude = np.sum(np.abs(changes), axis=1)
                
                # Count significant changes
                significant_changes = np.sum(change_magnitude > 0.1)
                
                if significant_changes > len(features) * 0.3:  # More than 30% of periods
                    anomalies.append({
                        'type': 'frequent_rebalancing',
                        'anomaly_score': significant_changes / len(features),
                        'confidence': 0.7,
                        'description': f"Frequent rebalancing detected ({significant_changes} significant changes)",
                        'details': {
                            'significant_changes': int(significant_changes),
                            'total_periods': len(features),
                            'percentage': significant_changes / len(features) * 100
                        },
                        'severity': 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing rebalancing anomalies: {e}")
            return []
    
    def _analyze_volatility_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze volatility anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 0:
                returns = features[:, 0]  # First column should be returns
                
                # Calculate rolling volatility
                window = min(10, len(returns) // 2)
                if window > 1:
                    rolling_vol = pd.Series(returns).rolling(window=window).std()
                    
                    # Detect volatility spikes
                    vol_threshold = rolling_vol.quantile(0.95)
                    vol_spikes = rolling_vol[rolling_vol > vol_threshold]
                    
                    for date, vol in vol_spikes.items():
                        anomalies.append({
                            'type': 'volatility_spike',
                            'anomaly_score': min(vol / vol_threshold, 1.0),
                            'confidence': 0.8,
                            'description': f"Volatility spike detected ({vol:.3f})",
                            'details': {
                                'volatility': float(vol),
                                'threshold': float(vol_threshold),
                                'period': int(date)
                            },
                            'severity': 'high' if vol > vol_threshold * 2 else 'medium'
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing volatility anomalies: {e}")
            return []
    
    def _analyze_correlation_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze correlation anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 1:
                # Calculate correlation between portfolio and market
                portfolio_returns = features[:, 0]
                market_returns = features[:, 1]
                
                correlation = np.corrcoef(portfolio_returns, market_returns)[0, 1]
                
                # Detect unusual correlation changes
                if abs(correlation) < 0.3:  # Low correlation
                    anomalies.append({
                        'type': 'low_correlation',
                        'anomaly_score': 1 - abs(correlation),
                        'confidence': 0.7,
                        'description': f"Low correlation with market ({correlation:.3f})",
                        'details': {
                            'correlation': float(correlation)
                        },
                        'severity': 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing correlation anomalies: {e}")
            return []
    
    def _analyze_alpha_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze alpha anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 1:
                portfolio_returns = features[:, 0]
                market_returns = features[:, 1]
                
                # Calculate alpha (excess return)
                alpha = np.mean(portfolio_returns) - np.mean(market_returns)
                
                # Detect significant alpha
                if abs(alpha) > 0.05:  # 5% alpha threshold
                    anomalies.append({
                        'type': 'significant_alpha',
                        'anomaly_score': min(abs(alpha) / 0.1, 1.0),
                        'confidence': 0.8,
                        'description': f"Significant alpha detected ({alpha:.3f})",
                        'details': {
                            'alpha': float(alpha),
                            'portfolio_return': float(np.mean(portfolio_returns)),
                            'market_return': float(np.mean(market_returns))
                        },
                        'severity': 'high' if abs(alpha) > 0.1 else 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing alpha anomalies: {e}")
            return []
    
    def _analyze_spending_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze spending anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 0:
                cash_flow = features[:, 0]
                spending = cash_flow[cash_flow < 0]  # Negative amounts
                
                if len(spending) > 0:
                    # Detect spending spikes
                    spending_threshold = np.percentile(np.abs(spending), 95)
                    large_spending = spending[np.abs(spending) > spending_threshold]
                    
                    for amount in large_spending:
                        anomalies.append({
                            'type': 'spending_spike',
                            'anomaly_score': min(np.abs(amount) / spending_threshold, 1.0),
                            'confidence': 0.8,
                            'description': f"Unusual spending detected (${abs(amount):,.2f})",
                            'details': {
                                'amount': float(amount),
                                'threshold': float(spending_threshold)
                            },
                            'severity': 'high' if abs(amount) > spending_threshold * 2 else 'medium'
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing spending anomalies: {e}")
            return []
    
    def _analyze_income_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze income anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 1:
                income = features[:, 2]  # Third column should be income
                
                if len(income) > 0:
                    # Detect income changes
                    income_changes = np.diff(income)
                    change_threshold = np.std(income_changes) * 2
                    
                    large_changes = income_changes[np.abs(income_changes) > change_threshold]
                    
                    for change in large_changes:
                        anomalies.append({
                            'type': 'income_change',
                            'anomaly_score': min(abs(change) / change_threshold, 1.0),
                            'confidence': 0.7,
                            'description': f"Significant income change detected (${change:,.2f})",
                            'details': {
                                'change': float(change),
                                'threshold': float(change_threshold)
                            },
                            'severity': 'medium'
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing income anomalies: {e}")
            return []
    
    def _analyze_cash_position_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze cash position anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 0:
                cash_flow = features[:, 0]
                cumulative_cash = np.cumsum(cash_flow)
                
                # Detect negative cash positions
                negative_cash = cumulative_cash < 0
                
                if np.any(negative_cash):
                    anomalies.append({
                        'type': 'negative_cash_position',
                        'anomaly_score': 1.0,
                        'confidence': 0.9,
                        'description': "Negative cash position detected",
                        'details': {
                            'min_cash': float(np.min(cumulative_cash)),
                            'periods_negative': int(np.sum(negative_cash))
                        },
                        'severity': 'high'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing cash position anomalies: {e}")
            return []
    
    def _analyze_var_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze VaR anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 0:
                returns = features[:, 0]
                
                # Calculate 95% VaR
                var_95 = np.percentile(returns, 5)
                
                # Detect VaR breaches
                var_breaches = returns < var_95
                
                if np.any(var_breaches):
                    breach_count = np.sum(var_breaches)
                    breach_rate = breach_count / len(returns)
                    
                    if breach_rate > 0.1:  # More than 10% breach rate
                        anomalies.append({
                            'type': 'var_breach',
                            'anomaly_score': breach_rate,
                            'confidence': 0.8,
                            'description': f"VaR breaches detected ({breach_count} breaches)",
                            'details': {
                                'var_95': float(var_95),
                                'breach_count': int(breach_count),
                                'breach_rate': float(breach_rate)
                            },
                            'severity': 'high' if breach_rate > 0.2 else 'medium'
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing VaR anomalies: {e}")
            return []
    
    def _analyze_drawdown_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze drawdown anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 1:
                drawdown = features[:, 1]  # Second column should be drawdown
                
                # Detect large drawdowns
                max_drawdown = np.min(drawdown)
                
                if max_drawdown < -0.2:  # 20% drawdown threshold
                    anomalies.append({
                        'type': 'large_drawdown',
                        'anomaly_score': min(abs(max_drawdown) / 0.5, 1.0),
                        'confidence': 0.9,
                        'description': f"Large drawdown detected ({max_drawdown:.1%})",
                        'details': {
                            'max_drawdown': float(max_drawdown)
                        },
                        'severity': 'high' if max_drawdown < -0.3 else 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing drawdown anomalies: {e}")
            return []
    
    def _analyze_beta_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze beta anomalies"""
        try:
            anomalies = []
            
            if features.shape[1] > 0:
                returns = features[:, 0]
                
                # Calculate rolling beta (simplified)
                window = min(20, len(returns) // 2)
                if window > 1:
                    rolling_beta = pd.Series(returns).rolling(window=window).std()
                    
                    # Detect beta spikes
                    beta_threshold = rolling_beta.quantile(0.95)
                    beta_spikes = rolling_beta[rolling_beta > beta_threshold]
                    
                    for date, beta in beta_spikes.items():
                        anomalies.append({
                            'type': 'beta_spike',
                            'anomaly_score': min(beta / beta_threshold, 1.0),
                            'confidence': 0.7,
                            'description': f"Beta spike detected ({beta:.3f})",
                            'details': {
                                'beta': float(beta),
                                'threshold': float(beta_threshold),
                                'period': int(date)
                            },
                            'severity': 'medium'
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing beta anomalies: {e}")
            return []
    
    async def _store_anomalies(self, user: User, anomalies: List[Dict[str, Any]]):
        """Store detected anomalies in database"""
        try:
            for anomaly in anomalies:
                MLAnomalyDetection.objects.create(
                    user=user,
                    anomaly_type=anomaly['type'],
                    anomaly_score=anomaly['anomaly_score'],
                    confidence=anomaly['confidence'],
                    description=anomaly['description'],
                    input_data=anomaly.get('details', {}),
                    model_version='v1.0'
                )
        except Exception as e:
            logger.error(f"Error storing anomalies: {e}")
    
    async def _generate_anomaly_alerts(self, user: User, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate alerts for significant anomalies"""
        try:
            alert_anomalies = []
            
            for anomaly in anomalies:
                # Only generate alerts for high-confidence, significant anomalies
                if anomaly['confidence'] > 0.7 and anomaly['anomaly_score'] > 0.5:
                    alert = {
                        'id': f"ml_anomaly_{anomaly['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'type': f"ml_{anomaly['type']}",
                        'priority': 'high' if anomaly['severity'] == 'high' else 'medium',
                        'category': 'behavior',
                        'title': f"Unusual Activity Detected: {anomaly['type'].replace('_', ' ').title()}",
                        'message': anomaly['description'],
                        'details': {
                            'anomaly_score': anomaly['anomaly_score'],
                            'confidence': anomaly['confidence'],
                            'severity': anomaly['severity'],
                            'data_source': 'ml_anomaly_detection',
                            **anomaly.get('details', {})
                        },
                        'actionable': True,
                        'suggested_actions': self._get_anomaly_actions(anomaly['type']),
                        'coaching_tip': self._get_anomaly_coaching_tip(anomaly['type']),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    alert_anomalies.append(alert)
            
            return alert_anomalies
            
        except Exception as e:
            logger.error(f"Error generating anomaly alerts: {e}")
            return []
    
    def _get_anomaly_actions(self, anomaly_type: str) -> List[str]:
        """Get suggested actions for anomaly type"""
        actions_map = {
            'trading_frequency_spike': [
                "Review recent trading activity",
                "Consider if this aligns with your investment strategy",
                "Document the reasoning for increased activity"
            ],
            'large_transaction': [
                "Verify the transaction details",
                "Ensure this aligns with your financial plan",
                "Consider the impact on your portfolio allocation"
            ],
            'after_hours_trading': [
                "Review why trades occurred outside market hours",
                "Consider setting up limit orders for better execution",
                "Be aware of potential higher spreads"
            ],
            'transaction_clustering': [
                "Review the reasoning for multiple rapid trades",
                "Consider if this indicates emotional trading",
                "Implement a cooling-off period for large decisions"
            ],
            'allocation_drift': [
                "Review your target asset allocation",
                "Consider rebalancing if appropriate",
                "Document the reasons for allocation changes"
            ],
            'high_concentration': [
                "Review portfolio diversification",
                "Consider reducing concentration in single positions",
                "Assess risk tolerance vs. current allocation"
            ],
            'volatility_spike': [
                "Review recent market conditions",
                "Consider if your risk tolerance has changed",
                "Evaluate if current volatility is acceptable"
            ],
            'spending_spike': [
                "Review recent spending patterns",
                "Ensure spending aligns with your budget",
                "Consider the impact on your financial goals"
            ],
            'negative_cash_position': [
                "Review cash flow management",
                "Consider liquidating some investments if needed",
                "Implement better cash flow monitoring"
            ]
        }
        
        return actions_map.get(anomaly_type, [
            "Review the detected anomaly",
            "Consider if this aligns with your financial strategy",
            "Document any changes in your approach"
        ])
    
    def _get_anomaly_coaching_tip(self, anomaly_type: str) -> str:
        """Get coaching tip for anomaly type"""
        tips_map = {
            'trading_frequency_spike': "Frequent trading can increase costs and reduce returns. Consider a more systematic approach to portfolio management.",
            'large_transaction': "Large transactions can significantly impact your portfolio. Always ensure they align with your long-term financial plan.",
            'after_hours_trading': "After-hours trading often has wider spreads and higher volatility. Consider market hours for better execution.",
            'transaction_clustering': "Rapid-fire trading decisions often lead to suboptimal outcomes. Take time to think through major portfolio changes.",
            'allocation_drift': "Portfolio drift is natural, but regular rebalancing helps maintain your target risk-return profile.",
            'high_concentration': "Diversification is one of the few free lunches in investing. Consider spreading risk across more positions.",
            'volatility_spike': "Market volatility is normal, but ensure your portfolio's risk level matches your comfort zone.",
            'spending_spike': "Consistent spending patterns are key to long-term financial success. Track and review your expenses regularly.",
            'negative_cash_position': "Maintaining adequate cash reserves provides flexibility and reduces the need for forced sales during market stress."
        }
        
        return tips_map.get(anomaly_type, "Regular monitoring of your financial behavior helps identify patterns and opportunities for improvement.")

# Global instance
ml_anomaly_service = MLAnomalyService()
