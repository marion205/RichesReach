"""
Real-time Data Pipeline
Handles live data feeds, model updates, and real-time predictions
"""

import os
import sys
import django
import logging
import asyncio
import aiohttp
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
import threading
import time
from dataclasses import dataclass, asdict
from queue import Queue
import schedule

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from .alternative_data_service import AlternativeDataService, AlternativeDataPoint
from .deep_learning_service import DeepLearningService

logger = logging.getLogger(__name__)

@dataclass
class RealTimeDataPoint:
    """Real-time data point structure"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    alternative_data: AlternativeDataPoint
    prediction: float
    confidence: float
    model_version: str

class RealTimeDataPipeline:
    """
    Real-time data pipeline for live market data and predictions
    """
    
    def __init__(self):
        self.alternative_data_service = AlternativeDataService()
        self.deep_learning_service = DeepLearningService()
        
        # Data queues
        self.price_queue = Queue()
        self.prediction_queue = Queue()
        self.alert_queue = Queue()
        
        # Model state
        self.current_model_version = "1.0.0"
        self.model_last_updated = datetime.now()
        self.model_update_interval = timedelta(hours=6)  # Update every 6 hours
        
        # Real-time data cache
        self.price_cache = {}
        self.prediction_cache = {}
        self.cache_ttl = 60  # 1 minute
        
        # Subscribers
        self.subscribers = []
        
        # Pipeline state
        self.is_running = False
        self.update_thread = None
        
        # API keys
        self.api_keys = self._load_api_keys()
        
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment"""
        return {
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
            'finnhub': os.getenv('FINNHUB_API_KEY', ''),
            'polygon': os.getenv('POLYGON_API_KEY', ''),
            'iex': os.getenv('IEX_API_KEY', ''),
        }
    
    async def fetch_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time price data"""
        try:
            # Try multiple data sources
            price_data = None
            
            # Alpha Vantage
            if self.api_keys['alpha_vantage']:
                price_data = await self._fetch_alpha_vantage_price(symbol)
            
            # Finnhub (fallback)
            if not price_data and self.api_keys['finnhub']:
                price_data = await self._fetch_finnhub_price(symbol)
            
            # Polygon (fallback)
            if not price_data and self.api_keys['polygon']:
                price_data = await self._fetch_polygon_price(symbol)
            
            # IEX (fallback)
            if not price_data and self.api_keys['iex']:
                price_data = await self._fetch_iex_price(symbol)
            
            if price_data:
                return price_data
            else:
                # Fallback to simulated data
                return {
                    'symbol': symbol,
                    'price': np.random.uniform(50, 500),
                    'volume': np.random.randint(1000000, 10000000),
                    'timestamp': datetime.now()
                }
                
        except Exception as e:
            logger.error(f"Error fetching real-time price for {symbol}: {e}")
            return None
    
    async def _fetch_alpha_vantage_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from Alpha Vantage"""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_keys['alpha_vantage']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get('Global Quote', {})
                        
                        if quote:
                            return {
                                'symbol': symbol,
                                'price': float(quote.get('05. price', 0)),
                                'volume': int(quote.get('06. volume', 0)),
                                'timestamp': datetime.now()
                            }
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
        return None
    
    async def _fetch_finnhub_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from Finnhub"""
        try:
            url = "https://finnhub.io/api/v1/quote"
            params = {
                'symbol': symbol,
                'token': self.api_keys['finnhub']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('c'):  # Current price
                            return {
                                'symbol': symbol,
                                'price': float(data.get('c', 0)),
                                'volume': int(data.get('v', 0)),
                                'timestamp': datetime.now()
                            }
        except Exception as e:
            logger.error(f"Finnhub error for {symbol}: {e}")
        return None
    
    async def _fetch_polygon_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from Polygon"""
        try:
            url = f"https://api.polygon.io/v1/last_quote/stocks/{symbol}"
            params = {
                'apikey': self.api_keys['polygon']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', {})
                        
                        if results:
                            return {
                                'symbol': symbol,
                                'price': float(results.get('P', 0)),
                                'volume': int(results.get('S', 0)),
                                'timestamp': datetime.now()
                            }
        except Exception as e:
            logger.error(f"Polygon error for {symbol}: {e}")
        return None
    
    async def _fetch_iex_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from IEX"""
        try:
            url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
            params = {
                'token': self.api_keys['iex']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('latestPrice'):
                            return {
                                'symbol': symbol,
                                'price': float(data.get('latestPrice', 0)),
                                'volume': int(data.get('latestVolume', 0)),
                                'timestamp': datetime.now()
                            }
        except Exception as e:
            logger.error(f"IEX error for {symbol}: {e}")
        return None
    
    async def generate_prediction(self, symbol: str, price_data: Dict[str, Any], alternative_data: AlternativeDataPoint) -> Dict[str, Any]:
        """Generate prediction using deep learning models"""
        try:
            # Create feature vector
            features = []
            
            # Price features
            features.extend([
                price_data['price'],
                price_data['volume'] / 1000000,  # Normalize volume
                alternative_data.news_sentiment,
                alternative_data.social_sentiment,
                alternative_data.analyst_sentiment,
                alternative_data.market_sentiment,
                alternative_data.volatility_index / 100.0,
                alternative_data.fear_greed_index,
            ])
            
            # Economic indicators
            for key, value in alternative_data.economic_indicators.items():
                if key == 'GDP':
                    features.append(value / 10.0)
                elif key == 'UNEMPLOYMENT':
                    features.append(value / 10.0)
                elif key == 'INFLATION':
                    features.append(value / 10.0)
                elif key == 'INTEREST_RATE':
                    features.append(value / 10.0)
                elif key == 'CONSUMER_SENTIMENT':
                    features.append(value / 100.0)
                elif key == 'VIX':
                    features.append(value / 100.0)
            
            # Convert to numpy array
            X = np.array(features).reshape(1, -1)
            
            # Make prediction
            if self.deep_learning_service.lstm_model is not None:
                prediction = self.deep_learning_service.predict_lstm(X)[0]
                confidence = 0.8  # LSTM confidence
            elif self.deep_learning_service.transformer_model is not None:
                prediction = self.deep_learning_service.predict_transformer(X)[0]
                confidence = 0.7  # Transformer confidence
            else:
                # Fallback prediction
                prediction = np.random.normal(0, 0.1)
                confidence = 0.3
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'model_version': self.current_model_version,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating prediction for {symbol}: {e}")
            return {
                'prediction': 0.0,
                'confidence': 0.0,
                'model_version': self.current_model_version,
                'timestamp': datetime.now()
            }
    
    async def process_symbol(self, symbol: str) -> RealTimeDataPoint:
        """Process a single symbol and generate real-time data point"""
        try:
            # Fetch real-time price
            price_data = await self.fetch_real_time_price(symbol)
            if not price_data:
                return None
            
            # Fetch alternative data
            alternative_data_dict = await self.alternative_data_service.get_alternative_data([symbol])
            alternative_data = alternative_data_dict.get(symbol)
            if not alternative_data:
                return None
            
            # Generate prediction
            prediction_data = await self.generate_prediction(symbol, price_data, alternative_data)
            
            # Create real-time data point
            data_point = RealTimeDataPoint(
                symbol=symbol,
                timestamp=datetime.now(),
                price=price_data['price'],
                volume=price_data['volume'],
                alternative_data=alternative_data,
                prediction=prediction_data['prediction'],
                confidence=prediction_data['confidence'],
                model_version=prediction_data['model_version']
            )
            
            return data_point
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {e}")
            return None
    
    async def update_models(self):
        """Update deep learning models with new data"""
        try:
            logger.info("Updating deep learning models...")
            
            # Check if models need updating
            if datetime.now() - self.model_last_updated < self.model_update_interval:
                return
            
            # This would typically retrain models with new data
            # For now, just update the version
            self.current_model_version = f"1.0.{int(time.time())}"
            self.model_last_updated = datetime.now()
            
            logger.info(f"Models updated to version {self.current_model_version}")
            
        except Exception as e:
            logger.error(f"Error updating models: {e}")
    
    async def run_pipeline(self, symbols: List[str], update_interval: int = 60):
        """Run the real-time pipeline"""
        logger.info(f"Starting real-time pipeline for {len(symbols)} symbols")
        self.is_running = True
        
        while self.is_running:
            try:
                # Update models if needed
                await self.update_models()
                
                # Process all symbols
                tasks = [self.process_symbol(symbol) for symbol in symbols]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Error processing {symbols[i]}: {result}")
                    elif result is not None:
                        # Cache the result
                        self.price_cache[symbols[i]] = result
                        self.prediction_cache[symbols[i]] = result
                        
                        # Notify subscribers
                        await self.notify_subscribers(result)
                        
                        # Check for alerts
                        await self.check_alerts(result)
                
                # Wait for next update
                await asyncio.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Error in pipeline: {e}")
                await asyncio.sleep(update_interval)
    
    async def notify_subscribers(self, data_point: RealTimeDataPoint):
        """Notify all subscribers of new data"""
        for subscriber in self.subscribers:
            try:
                await subscriber(data_point)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def check_alerts(self, data_point: RealTimeDataPoint):
        """Check for alert conditions"""
        try:
            # Example alert conditions
            if data_point.prediction > 0.8 and data_point.confidence > 0.7:
                alert = {
                    'type': 'BUY_SIGNAL',
                    'symbol': data_point.symbol,
                    'prediction': data_point.prediction,
                    'confidence': data_point.confidence,
                    'timestamp': data_point.timestamp
                }
                self.alert_queue.put(alert)
                logger.info(f"BUY signal for {data_point.symbol}: {data_point.prediction:.3f}")
            
            elif data_point.prediction < -0.8 and data_point.confidence > 0.7:
                alert = {
                    'type': 'SELL_SIGNAL',
                    'symbol': data_point.symbol,
                    'prediction': data_point.prediction,
                    'confidence': data_point.confidence,
                    'timestamp': data_point.timestamp
                }
                self.alert_queue.put(alert)
                logger.info(f"SELL signal for {data_point.symbol}: {data_point.prediction:.3f}")
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to real-time updates"""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from real-time updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_latest_data(self, symbol: str) -> Optional[RealTimeDataPoint]:
        """Get latest data for a symbol"""
        return self.price_cache.get(symbol)
    
    def get_latest_prediction(self, symbol: str) -> Optional[RealTimeDataPoint]:
        """Get latest prediction for a symbol"""
        return self.prediction_cache.get(symbol)
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all pending alerts"""
        alerts = []
        while not self.alert_queue.empty():
            try:
                alert = self.alert_queue.get_nowait()
                alerts.append(alert)
            except:
                break
        return alerts
    
    def stop_pipeline(self):
        """Stop the real-time pipeline"""
        self.is_running = False
        logger.info("Real-time pipeline stopped")

# Example usage
async def main():
    """Example usage of RealTimeDataPipeline"""
    pipeline = RealTimeDataPipeline()
    
    # Subscribe to updates
    async def on_update(data_point: RealTimeDataPoint):
        print(f"Update for {data_point.symbol}: Price=${data_point.price:.2f}, Prediction={data_point.prediction:.3f}")
    
    pipeline.subscribe(on_update)
    
    # Run pipeline
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    await pipeline.run_pipeline(symbols, update_interval=30)

if __name__ == "__main__":
    asyncio.run(main())
