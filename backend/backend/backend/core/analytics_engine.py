"""
Advanced Analytics Engine - Phase 3
Real-time business intelligence, market analytics, user behavior, and predictive analytics
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import aiohttp
import websockets
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

logger = logging.getLogger("richesreach")

class AnalyticsType(Enum):
    """Types of analytics"""
    REALTIME_BI = "realtime_bi"
    MARKET_ANALYTICS = "market_analytics"
    USER_BEHAVIOR = "user_behavior"
    PREDICTIVE = "predictive"
    PERFORMANCE = "performance"
    FINANCIAL = "financial"

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Metric:
    """Analytics metric"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    metric_type: MetricType
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AnalyticsEvent:
    """Analytics event"""
    event_id: str
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    properties: Dict[str, Any]
    context: Dict[str, Any]

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    change: float
    change_percent: float
    high: float
    low: float
    open_price: float
    close_price: float

@dataclass
class UserBehavior:
    """User behavior data"""
    user_id: str
    session_id: str
    event_type: str
    timestamp: datetime
    page: str
    action: str
    duration: float
    properties: Dict[str, Any]

class RealTimeAnalytics:
    """Real-time analytics engine"""
    
    def __init__(self, redis_client, db_connection):
        self.redis = redis_client
        self.db = db_connection
        self.metrics_buffer = deque(maxlen=10000)
        self.events_buffer = deque(maxlen=50000)
        self.market_data_buffer = deque(maxlen=100000)
        self.user_behavior_buffer = deque(maxlen=100000)
        
        # Real-time dashboards
        self.dashboards = {
            "business_intelligence": self._create_bi_dashboard(),
            "market_analytics": self._create_market_dashboard(),
            "user_analytics": self._create_user_dashboard(),
            "performance": self._create_performance_dashboard()
        }
        
        # Start background tasks
        asyncio.create_task(self._process_metrics())
        asyncio.create_task(self._process_events())
        asyncio.create_task(self._process_market_data())
        asyncio.create_task(self._process_user_behavior())
    
    def _create_bi_dashboard(self) -> Dict[str, Any]:
        """Create business intelligence dashboard"""
        return {
            "revenue_metrics": {
                "total_revenue": 0,
                "revenue_growth": 0,
                "revenue_per_user": 0,
                "revenue_trend": []
            },
            "user_metrics": {
                "total_users": 0,
                "active_users": 0,
                "new_users": 0,
                "user_retention": 0
            },
            "engagement_metrics": {
                "session_duration": 0,
                "page_views": 0,
                "bounce_rate": 0,
                "conversion_rate": 0
            },
            "financial_metrics": {
                "portfolio_value": 0,
                "trading_volume": 0,
                "profit_loss": 0,
                "risk_metrics": {}
            }
        }
    
    def _create_market_dashboard(self) -> Dict[str, Any]:
        """Create market analytics dashboard"""
        return {
            "market_overview": {
                "total_market_cap": 0,
                "market_trend": "neutral",
                "volatility_index": 0,
                "sector_performance": {}
            },
            "stock_analytics": {
                "top_gainers": [],
                "top_losers": [],
                "most_active": [],
                "sector_analysis": {}
            },
            "crypto_analytics": {
                "total_crypto_market_cap": 0,
                "crypto_trend": "neutral",
                "top_crypto_gainers": [],
                "crypto_volatility": 0
            },
            "technical_indicators": {
                "rsi_distribution": {},
                "macd_signals": {},
                "bollinger_bands": {},
                "moving_averages": {}
            }
        }
    
    def _create_user_dashboard(self) -> Dict[str, Any]:
        """Create user analytics dashboard"""
        return {
            "user_segments": {
                "beginners": 0,
                "intermediate": 0,
                "advanced": 0,
                "professional": 0
            },
            "behavior_patterns": {
                "peak_hours": [],
                "popular_features": [],
                "user_journey": {},
                "drop_off_points": []
            },
            "engagement_analysis": {
                "session_frequency": 0,
                "feature_usage": {},
                "content_consumption": {},
                "social_interactions": {}
            },
            "conversion_funnel": {
                "visitors": 0,
                "registered": 0,
                "active": 0,
                "premium": 0
            }
        }
    
    def _create_performance_dashboard(self) -> Dict[str, Any]:
        """Create performance dashboard"""
        return {
            "system_metrics": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "network_usage": 0
            },
            "api_metrics": {
                "request_rate": 0,
                "response_time": 0,
                "error_rate": 0,
                "throughput": 0
            },
            "database_metrics": {
                "connection_pool": 0,
                "query_performance": {},
                "cache_hit_rate": 0,
                "replication_lag": 0
            },
            "infrastructure_metrics": {
                "ecs_tasks": 0,
                "alb_health": 0,
                "cloudfront_hits": 0,
                "lambda_invocations": 0
            }
        }
    
    async def record_metric(self, metric: Metric):
        """Record a metric"""
        self.metrics_buffer.append(metric)
        
        # Store in Redis for real-time access
        key = f"metrics:{metric.name}:{metric.timestamp.isoformat()}"
        await self.redis.setex(
            key, 
            3600,  # 1 hour TTL
            json.dumps(asdict(metric), default=str)
        )
    
    async def record_event(self, event: AnalyticsEvent):
        """Record an analytics event"""
        self.events_buffer.append(event)
        
        # Store in Redis for real-time access
        key = f"events:{event.event_type}:{event.timestamp.isoformat()}"
        await self.redis.setex(
            key,
            7200,  # 2 hours TTL
            json.dumps(asdict(event), default=str)
        )
    
    async def record_market_data(self, market_data: MarketData):
        """Record market data"""
        self.market_data_buffer.append(market_data)
        
        # Store in Redis for real-time access
        key = f"market:{market_data.symbol}:{market_data.timestamp.isoformat()}"
        await self.redis.setex(
            key,
            1800,  # 30 minutes TTL
            json.dumps(asdict(market_data), default=str)
        )
    
    async def record_user_behavior(self, behavior: UserBehavior):
        """Record user behavior"""
        self.user_behavior_buffer.append(behavior)
        
        # Store in Redis for real-time access
        key = f"behavior:{behavior.user_id}:{behavior.timestamp.isoformat()}"
        await self.redis.setex(
            key,
            3600,  # 1 hour TTL
            json.dumps(asdict(behavior), default=str)
        )
    
    async def _process_metrics(self):
        """Process metrics in background"""
        while True:
            try:
                if self.metrics_buffer:
                    # Process metrics batch
                    batch = list(self.metrics_buffer)
                    self.metrics_buffer.clear()
                    
                    # Update dashboards
                    await self._update_bi_dashboard(batch)
                    await self._update_performance_dashboard(batch)
                    
                    # Store in database
                    await self._store_metrics_batch(batch)
                
                await asyncio.sleep(5)  # Process every 5 seconds
            except Exception as e:
                logger.error(f"Error processing metrics: {e}")
                await asyncio.sleep(10)
    
    async def _process_events(self):
        """Process events in background"""
        while True:
            try:
                if self.events_buffer:
                    # Process events batch
                    batch = list(self.events_buffer)
                    self.events_buffer.clear()
                    
                    # Update dashboards
                    await self._update_user_dashboard(batch)
                    
                    # Store in database
                    await self._store_events_batch(batch)
                
                await asyncio.sleep(10)  # Process every 10 seconds
            except Exception as e:
                logger.error(f"Error processing events: {e}")
                await asyncio.sleep(15)
    
    async def _process_market_data(self):
        """Process market data in background"""
        while True:
            try:
                if self.market_data_buffer:
                    # Process market data batch
                    batch = list(self.market_data_buffer)
                    self.market_data_buffer.clear()
                    
                    # Update dashboards
                    await self._update_market_dashboard(batch)
                    
                    # Store in database
                    await self._store_market_data_batch(batch)
                
                await asyncio.sleep(30)  # Process every 30 seconds
            except Exception as e:
                logger.error(f"Error processing market data: {e}")
                await asyncio.sleep(60)
    
    async def _process_user_behavior(self):
        """Process user behavior in background"""
        while True:
            try:
                if self.user_behavior_buffer:
                    # Process user behavior batch
                    batch = list(self.user_behavior_buffer)
                    self.user_behavior_buffer.clear()
                    
                    # Update dashboards
                    await self._update_user_dashboard(batch)
                    
                    # Store in database
                    await self._store_user_behavior_batch(batch)
                
                await asyncio.sleep(15)  # Process every 15 seconds
            except Exception as e:
                logger.error(f"Error processing user behavior: {e}")
                await asyncio.sleep(30)
    
    async def _update_bi_dashboard(self, metrics: List[Metric]):
        """Update business intelligence dashboard"""
        for metric in metrics:
            if metric.name.startswith("revenue"):
                if metric.name == "total_revenue":
                    self.dashboards["business_intelligence"]["revenue_metrics"]["total_revenue"] = metric.value
                elif metric.name == "revenue_growth":
                    self.dashboards["business_intelligence"]["revenue_metrics"]["revenue_growth"] = metric.value
            
            elif metric.name.startswith("user"):
                if metric.name == "total_users":
                    self.dashboards["business_intelligence"]["user_metrics"]["total_users"] = metric.value
                elif metric.name == "active_users":
                    self.dashboards["business_intelligence"]["user_metrics"]["active_users"] = metric.value
    
    async def _update_market_dashboard(self, market_data: List[MarketData]):
        """Update market analytics dashboard"""
        for data in market_data:
            # Update market overview
            if data.symbol in ["SPY", "QQQ", "IWM"]:  # Market indices
                self.dashboards["market_analytics"]["market_overview"]["total_market_cap"] += data.price * data.volume
            
            # Update stock analytics
            if data.change_percent > 0:
                self.dashboards["market_analytics"]["stock_analytics"]["top_gainers"].append({
                    "symbol": data.symbol,
                    "change_percent": data.change_percent,
                    "price": data.price
                })
            else:
                self.dashboards["market_analytics"]["stock_analytics"]["top_losers"].append({
                    "symbol": data.symbol,
                    "change_percent": data.change_percent,
                    "price": data.price
                })
    
    async def _update_user_dashboard(self, events: List[AnalyticsEvent]):
        """Update user analytics dashboard"""
        for event in events:
            if event.event_type == "user_registration":
                self.dashboards["user_analytics"]["conversion_funnel"]["registered"] += 1
            elif event.event_type == "user_login":
                self.dashboards["user_analytics"]["conversion_funnel"]["active"] += 1
            elif event.event_type == "premium_upgrade":
                self.dashboards["user_analytics"]["conversion_funnel"]["premium"] += 1
    
    async def _update_performance_dashboard(self, metrics: List[Metric]):
        """Update performance dashboard"""
        for metric in metrics:
            if metric.name.startswith("system"):
                if metric.name == "cpu_usage":
                    self.dashboards["performance"]["system_metrics"]["cpu_usage"] = metric.value
                elif metric.name == "memory_usage":
                    self.dashboards["performance"]["system_metrics"]["memory_usage"] = metric.value
    
    async def _store_metrics_batch(self, metrics: List[Metric]):
        """Store metrics batch in database"""
        try:
            with self.db.cursor() as cursor:
                for metric in metrics:
                    cursor.execute("""
                        INSERT INTO analytics_metrics 
                        (name, value, timestamp, labels, metric_type, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        metric.name,
                        metric.value,
                        metric.timestamp,
                        json.dumps(metric.labels),
                        metric.metric_type.value,
                        json.dumps(metric.metadata) if metric.metadata else None
                    ))
                self.db.commit()
        except Exception as e:
            logger.error(f"Error storing metrics batch: {e}")
            self.db.rollback()
    
    async def _store_events_batch(self, events: List[AnalyticsEvent]):
        """Store events batch in database"""
        try:
            with self.db.cursor() as cursor:
                for event in events:
                    cursor.execute("""
                        INSERT INTO analytics_events 
                        (event_id, event_type, user_id, session_id, timestamp, properties, context)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        event.event_id,
                        event.event_type,
                        event.user_id,
                        event.session_id,
                        event.timestamp,
                        json.dumps(event.properties),
                        json.dumps(event.context)
                    ))
                self.db.commit()
        except Exception as e:
            logger.error(f"Error storing events batch: {e}")
            self.db.rollback()
    
    async def _store_market_data_batch(self, market_data: List[MarketData]):
        """Store market data batch in database"""
        try:
            with self.db.cursor() as cursor:
                for data in market_data:
                    cursor.execute("""
                        INSERT INTO market_data 
                        (symbol, price, volume, timestamp, change, change_percent, high, low, open_price, close_price)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data.symbol,
                        data.price,
                        data.volume,
                        data.timestamp,
                        data.change,
                        data.change_percent,
                        data.high,
                        data.low,
                        data.open_price,
                        data.close_price
                    ))
                self.db.commit()
        except Exception as e:
            logger.error(f"Error storing market data batch: {e}")
            self.db.rollback()
    
    async def _store_user_behavior_batch(self, behaviors: List[UserBehavior]):
        """Store user behavior batch in database"""
        try:
            with self.db.cursor() as cursor:
                for behavior in behaviors:
                    cursor.execute("""
                        INSERT INTO user_behavior 
                        (user_id, session_id, event_type, timestamp, page, action, duration, properties)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        behavior.user_id,
                        behavior.session_id,
                        behavior.event_type,
                        behavior.timestamp,
                        behavior.page,
                        behavior.action,
                        behavior.duration,
                        json.dumps(behavior.properties)
                    ))
                self.db.commit()
        except Exception as e:
            logger.error(f"Error storing user behavior batch: {e}")
            self.db.rollback()
    
    async def get_dashboard_data(self, dashboard_type: str) -> Dict[str, Any]:
        """Get dashboard data"""
        if dashboard_type in self.dashboards:
            return self.dashboards[dashboard_type]
        else:
            return {"error": f"Dashboard type {dashboard_type} not found"}
    
    async def get_real_time_metrics(self, metric_names: List[str]) -> Dict[str, Any]:
        """Get real-time metrics"""
        metrics = {}
        for name in metric_names:
            # Get from Redis
            keys = await self.redis.keys(f"metrics:{name}:*")
            if keys:
                latest_key = max(keys)
                data = await self.redis.get(latest_key)
                if data:
                    metrics[name] = json.loads(data)
        return metrics
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        return {
            "total_metrics": len(self.metrics_buffer),
            "total_events": len(self.events_buffer),
            "total_market_data": len(self.market_data_buffer),
            "total_user_behavior": len(self.user_behavior_buffer),
            "dashboards": list(self.dashboards.keys()),
            "last_updated": datetime.now().isoformat()
        }

class PredictiveAnalytics:
    """Predictive analytics engine"""
    
    def __init__(self, analytics_engine: RealTimeAnalytics):
        self.analytics = analytics_engine
        self.models = {}
        self.scalers = {}
        self.predictions = {}
    
    async def train_price_prediction_model(self, symbol: str, lookback_days: int = 30):
        """Train price prediction model for a symbol"""
        try:
            # Get historical data
            with self.analytics.db.cursor() as cursor:
                cursor.execute("""
                    SELECT price, volume, change, change_percent, high, low, open_price, close_price
                    FROM market_data 
                    WHERE symbol = %s AND timestamp >= %s
                    ORDER BY timestamp
                """, (symbol, datetime.now() - timedelta(days=lookback_days)))
                
                data = cursor.fetchall()
            
            if len(data) < 10:
                logger.warning(f"Insufficient data for {symbol}")
                return False
            
            # Prepare features
            df = pd.DataFrame(data, columns=['price', 'volume', 'change', 'change_percent', 'high', 'low', 'open_price', 'close_price'])
            
            # Create features
            df['price_ma_5'] = df['price'].rolling(window=5).mean()
            df['price_ma_20'] = df['price'].rolling(window=20).mean()
            df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
            df['price_std'] = df['price'].rolling(window=20).std()
            df['rsi'] = self._calculate_rsi(df['price'])
            
            # Drop NaN values
            df = df.dropna()
            
            if len(df) < 5:
                logger.warning(f"Insufficient data after feature engineering for {symbol}")
                return False
            
            # Prepare training data
            X = df[['price_ma_5', 'price_ma_20', 'volume_ma_5', 'price_std', 'rsi']].values
            y = df['price'].values
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            model = LinearRegression()
            model.fit(X_scaled, y)
            
            # Store model and scaler
            self.models[symbol] = model
            self.scalers[symbol] = scaler
            
            # Calculate accuracy
            y_pred = model.predict(X_scaled)
            mse = mean_squared_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            
            logger.info(f"Price prediction model trained for {symbol}: MSE={mse:.4f}, R2={r2:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Error training price prediction model for {symbol}: {e}")
            return False
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    async def predict_price(self, symbol: str, horizon_hours: int = 24) -> Dict[str, Any]:
        """Predict price for a symbol"""
        if symbol not in self.models:
            await self.train_price_prediction_model(symbol)
        
        if symbol not in self.models:
            return {"error": f"No model available for {symbol}"}
        
        try:
            # Get latest data
            with self.analytics.db.cursor() as cursor:
                cursor.execute("""
                    SELECT price, volume, change, change_percent, high, low, open_price, close_price
                    FROM market_data 
                    WHERE symbol = %s
                    ORDER BY timestamp DESC
                    LIMIT 20
                """, (symbol,))
                
                data = cursor.fetchall()
            
            if len(data) < 5:
                return {"error": f"Insufficient data for {symbol}"}
            
            # Prepare features
            df = pd.DataFrame(data, columns=['price', 'volume', 'change', 'change_percent', 'high', 'low', 'open_price', 'close_price'])
            df = df.sort_index()  # Sort by index (oldest first)
            
            # Create features
            df['price_ma_5'] = df['price'].rolling(window=5).mean()
            df['price_ma_20'] = df['price'].rolling(window=20).mean()
            df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
            df['price_std'] = df['price'].rolling(window=20).std()
            df['rsi'] = self._calculate_rsi(df['price'])
            
            # Get latest features
            latest_features = df[['price_ma_5', 'price_ma_20', 'volume_ma_5', 'price_std', 'rsi']].iloc[-1].values
            
            # Scale features
            X_scaled = self.scalers[symbol].transform([latest_features])
            
            # Make prediction
            prediction = self.models[symbol].predict(X_scaled)[0]
            
            # Calculate confidence based on model performance
            confidence = min(0.95, max(0.1, 0.7))  # Placeholder confidence
            
            return {
                "symbol": symbol,
                "current_price": data[0][0],  # Latest price
                "predicted_price": prediction,
                "price_change": prediction - data[0][0],
                "price_change_percent": ((prediction - data[0][0]) / data[0][0]) * 100,
                "confidence": confidence,
                "horizon_hours": horizon_hours,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting price for {symbol}: {e}")
            return {"error": str(e)}
    
    async def detect_anomalies(self, symbol: str, threshold: float = 0.1) -> Dict[str, Any]:
        """Detect anomalies in market data"""
        try:
            # Get recent data
            with self.analytics.db.cursor() as cursor:
                cursor.execute("""
                    SELECT price, volume, change_percent
                    FROM market_data 
                    WHERE symbol = %s AND timestamp >= %s
                    ORDER BY timestamp
                """, (symbol, datetime.now() - timedelta(days=7)))
                
                data = cursor.fetchall()
            
            if len(data) < 10:
                return {"error": f"Insufficient data for {symbol}"}
            
            # Prepare data
            df = pd.DataFrame(data, columns=['price', 'volume', 'change_percent'])
            
            # Detect anomalies using Isolation Forest
            model = IsolationForest(contamination=threshold, random_state=42)
            anomalies = model.fit_predict(df.values)
            
            # Get anomaly indices
            anomaly_indices = np.where(anomalies == -1)[0]
            
            return {
                "symbol": symbol,
                "total_data_points": len(data),
                "anomalies_detected": len(anomaly_indices),
                "anomaly_rate": len(anomaly_indices) / len(data),
                "anomaly_timestamps": [data[i][0] for i in anomaly_indices] if len(anomaly_indices) > 0 else [],
                "threshold": threshold,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for {symbol}: {e}")
            return {"error": str(e)}
    
    async def cluster_users(self, n_clusters: int = 5) -> Dict[str, Any]:
        """Cluster users based on behavior"""
        try:
            # Get user behavior data
            with self.analytics.db.cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, 
                           COUNT(*) as total_events,
                           AVG(duration) as avg_duration,
                           COUNT(DISTINCT page) as unique_pages,
                           COUNT(DISTINCT DATE(timestamp)) as active_days
                    FROM user_behavior 
                    WHERE timestamp >= %s
                    GROUP BY user_id
                    HAVING COUNT(*) >= 5
                """, (datetime.now() - timedelta(days=30),))
                
                data = cursor.fetchall()
            
            if len(data) < n_clusters:
                return {"error": f"Insufficient users for clustering (need at least {n_clusters})"}
            
            # Prepare features
            df = pd.DataFrame(data, columns=['user_id', 'total_events', 'avg_duration', 'unique_pages', 'active_days'])
            X = df[['total_events', 'avg_duration', 'unique_pages', 'active_days']].values
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Add cluster labels
            df['cluster'] = clusters
            
            # Analyze clusters
            cluster_analysis = {}
            for i in range(n_clusters):
                cluster_data = df[df['cluster'] == i]
                cluster_analysis[f"cluster_{i}"] = {
                    "size": len(cluster_data),
                    "avg_events": cluster_data['total_events'].mean(),
                    "avg_duration": cluster_data['avg_duration'].mean(),
                    "avg_pages": cluster_data['unique_pages'].mean(),
                    "avg_active_days": cluster_data['active_days'].mean()
                }
            
            return {
                "n_clusters": n_clusters,
                "total_users": len(df),
                "cluster_analysis": cluster_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error clustering users: {e}")
            return {"error": str(e)}

# Global analytics engine instance
analytics_engine = None
predictive_analytics = None

def initialize_analytics(redis_client, db_connection):
    """Initialize analytics engine"""
    global analytics_engine, predictive_analytics
    analytics_engine = RealTimeAnalytics(redis_client, db_connection)
    predictive_analytics = PredictiveAnalytics(analytics_engine)
    logger.info("✅ Analytics engine initialized successfully")
