"""
Phase 2A: Streaming Data Producer

This module handles real-time data ingestion from various sources
and publishes to Kafka/Kinesis streams for downstream processing.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import boto3
from kafka import KafkaProducer
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Market data structure for streaming"""
    symbol: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str
    timeframe: str = "1m"

@dataclass
class TechnicalIndicators:
    """Technical indicators structure for streaming"""
    symbol: str
    timestamp: str
    timeframe: str
    indicators: Dict[str, float]
    source: str = "calculation"

@dataclass
class MLPrediction:
    """ML prediction structure for streaming"""
    symbol: str
    timestamp: str
    model_version: str
    prediction: float
    confidence: float
    features: Dict[str, float]
    source: str = "ml_model"

class StreamingProducer:
    """Handles data streaming to Kafka and Kinesis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kafka_producer = None
        self.kinesis_client = None
        self._setup_producers()
    
    def _setup_producers(self):
        """Initialize Kafka and Kinesis producers"""
        try:
            # Kafka producer
            if self.config.get('kafka_enabled', True):
                kafka_config = self.config.get('kafka', {})
                self.kafka_producer = KafkaProducer(
                    bootstrap_servers=kafka_config.get('bootstrap_servers', ['localhost:9092']),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',
                    retries=3,
                    batch_size=16384,
                    linger_ms=10,
                    compression_type='snappy'
                )
                logger.info("✅ Kafka producer initialized")
            
            # Kinesis client
            if self.config.get('kinesis_enabled', True):
                kinesis_config = self.config.get('kinesis', {})
                self.kinesis_client = boto3.client(
                    'kinesis',
                    region_name=kinesis_config.get('region', 'us-east-1'),
                    aws_access_key_id=kinesis_config.get('access_key_id'),
                    aws_secret_access_key=kinesis_config.get('secret_access_key')
                )
                logger.info("✅ Kinesis client initialized")
                
        except Exception as e:
            logger.error(f"❌ Failed to setup streaming producers: {e}")
    
    async def publish_market_data(self, data: MarketData) -> bool:
        """Publish market data to streams"""
        try:
            data_dict = asdict(data)
            data_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            success = True
            
            # Publish to Kafka
            if self.kafka_producer:
                try:
                    future = self.kafka_producer.send(
                        'market-data',
                        key=data.symbol,
                        value=data_dict
                    )
                    # Don't wait for confirmation in async context
                    logger.debug(f"Published market data to Kafka: {data.symbol}")
                except Exception as e:
                    logger.error(f"Failed to publish to Kafka: {e}")
                    success = False
            
            # Publish to Kinesis
            if self.kinesis_client:
                try:
                    self.kinesis_client.put_record(
                        StreamName=self.config.get('kinesis', {}).get('stream_name', 'market-data'),
                        Data=json.dumps(data_dict),
                        PartitionKey=data.symbol
                    )
                    logger.debug(f"Published market data to Kinesis: {data.symbol}")
                except Exception as e:
                    logger.error(f"Failed to publish to Kinesis: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to publish market data: {e}")
            return False
    
    async def publish_technical_indicators(self, data: TechnicalIndicators) -> bool:
        """Publish technical indicators to streams"""
        try:
            data_dict = asdict(data)
            data_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            success = True
            
            # Publish to Kafka
            if self.kafka_producer:
                try:
                    future = self.kafka_producer.send(
                        'technical-indicators',
                        key=data.symbol,
                        value=data_dict
                    )
                    logger.debug(f"Published technical indicators to Kafka: {data.symbol}")
                except Exception as e:
                    logger.error(f"Failed to publish to Kafka: {e}")
                    success = False
            
            # Publish to Kinesis
            if self.kinesis_client:
                try:
                    self.kinesis_client.put_record(
                        StreamName=self.config.get('kinesis', {}).get('stream_name', 'technical-indicators'),
                        Data=json.dumps(data_dict),
                        PartitionKey=data.symbol
                    )
                    logger.debug(f"Published technical indicators to Kinesis: {data.symbol}")
                except Exception as e:
                    logger.error(f"Failed to publish to Kinesis: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to publish technical indicators: {e}")
            return False
    
    async def publish_ml_prediction(self, data: MLPrediction) -> bool:
        """Publish ML predictions to streams"""
        try:
            data_dict = asdict(data)
            data_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            success = True
            
            # Publish to Kafka
            if self.kafka_producer:
                try:
                    future = self.kafka_producer.send(
                        'ml-predictions',
                        key=data.symbol,
                        value=data_dict
                    )
                    logger.debug(f"Published ML prediction to Kafka: {data.symbol}")
                except Exception as e:
                    logger.error(f"Failed to publish to Kafka: {e}")
                    success = False
            
            # Publish to Kinesis
            if self.kinesis_client:
                try:
                    self.kinesis_client.put_record(
                        StreamName=self.config.get('kinesis', {}).get('stream_name', 'ml-predictions'),
                        Data=json.dumps(data_dict),
                        PartitionKey=data.symbol
                    )
                    logger.debug(f"Published ML prediction to Kinesis: {data.symbol}")
                except Exception as e:
                    logger.error(f"Failed to publish to Kinesis: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to publish ML prediction: {e}")
            return False
    
    def close(self):
        """Close streaming producers"""
        try:
            if self.kafka_producer:
                self.kafka_producer.close()
                logger.info("✅ Kafka producer closed")
        except Exception as e:
            logger.error(f"❌ Error closing Kafka producer: {e}")

class MarketDataIngestion:
    """Handles real-time market data ingestion from various sources"""
    
    def __init__(self, producer: StreamingProducer, config: Dict[str, Any]):
        self.producer = producer
        self.config = config
        self.symbols = config.get('symbols', ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'])
        self.sources = config.get('sources', ['polygon', 'finnhub'])
        self.running = False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_polygon_data(self, symbol: str) -> Optional[MarketData]:
        """Fetch market data from Polygon API"""
        try:
            api_key = self.config.get('polygon_api_key')
            if not api_key:
                logger.warning("Polygon API key not configured")
                return None
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
            params = {'apikey': api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results'][0]
                return MarketData(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    open=result['o'],
                    high=result['h'],
                    low=result['l'],
                    close=result['c'],
                    volume=result['v'],
                    source='polygon',
                    timeframe='1d'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Polygon data for {symbol}: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_finnhub_data(self, symbol: str) -> Optional[MarketData]:
        """Fetch market data from Finnhub API"""
        try:
            api_key = self.config.get('finnhub_api_key')
            if not api_key:
                logger.warning("Finnhub API key not configured")
                return None
            
            url = f"https://finnhub.io/api/v1/quote"
            params = {'symbol': symbol, 'token': api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('c'):  # current price
                return MarketData(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    open=data.get('o', data['c']),
                    high=data.get('h', data['c']),
                    low=data.get('l', data['c']),
                    close=data['c'],
                    volume=data.get('v', 0),
                    source='finnhub',
                    timeframe='1m'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Finnhub data for {symbol}: {e}")
            return None
    
    async def ingest_market_data(self):
        """Continuously ingest market data from all sources"""
        logger.info("🚀 Starting market data ingestion...")
        self.running = True
        
        while self.running:
            try:
                tasks = []
                
                for symbol in self.symbols:
                    for source in self.sources:
                        if source == 'polygon':
                            tasks.append(self.fetch_polygon_data(symbol))
                        elif source == 'finnhub':
                            tasks.append(self.fetch_finnhub_data(symbol))
                
                # Fetch data from all sources concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Publish successful results
                for result in results:
                    if isinstance(result, MarketData):
                        await self.producer.publish_market_data(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Data fetch failed: {result}")
                
                # Wait before next iteration
                await asyncio.sleep(self.config.get('ingestion_interval', 60))
                
            except Exception as e:
                logger.error(f"❌ Error in market data ingestion: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    def stop(self):
        """Stop market data ingestion"""
        self.running = False
        logger.info("🛑 Market data ingestion stopped")

class TechnicalIndicatorCalculator:
    """Calculates technical indicators in real-time"""
    
    def __init__(self, producer: StreamingProducer, config: Dict[str, Any]):
        self.producer = producer
        self.config = config
        self.price_history = {}  # symbol -> list of prices
        self.max_history = config.get('max_history', 100)
    
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0.0
        return sum(prices[-period:]) / period
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if not prices:
            return 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def process_market_data(self, market_data: MarketData):
        """Process market data and calculate technical indicators"""
        try:
            symbol = market_data.symbol
            
            # Update price history
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append(market_data.close)
            
            # Keep only recent prices
            if len(self.price_history[symbol]) > self.max_history:
                self.price_history[symbol] = self.price_history[symbol][-self.max_history:]
            
            prices = self.price_history[symbol]
            
            if len(prices) < 2:
                return  # Need at least 2 prices for indicators
            
            # Calculate indicators
            indicators = {
                'sma_20': self.calculate_sma(prices, 20),
                'sma_50': self.calculate_sma(prices, 50),
                'ema_12': self.calculate_ema(prices, 12),
                'ema_26': self.calculate_ema(prices, 26),
                'rsi': self.calculate_rsi(prices, 14)
            }
            
            # Create technical indicators data
            tech_data = TechnicalIndicators(
                symbol=symbol,
                timestamp=datetime.now(timezone.utc).isoformat(),
                timeframe=market_data.timeframe,
                indicators=indicators,
                source='calculation'
            )
            
            # Publish to stream
            await self.producer.publish_technical_indicators(tech_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to process market data for {market_data.symbol}: {e}")

# Global streaming producer instance
streaming_producer = None

def get_streaming_producer() -> Optional[StreamingProducer]:
    """Get the global streaming producer instance"""
    return streaming_producer

def initialize_streaming(config: Dict[str, Any]) -> StreamingProducer:
    """Initialize the streaming producer"""
    global streaming_producer
    streaming_producer = StreamingProducer(config)
    return streaming_producer

async def start_streaming_services(config: Dict[str, Any]):
    """Start all streaming services"""
    try:
        producer = initialize_streaming(config)
        
        # Start market data ingestion
        ingestion = MarketDataIngestion(producer, config)
        indicator_calc = TechnicalIndicatorCalculator(producer, config)
        
        # Start ingestion in background
        asyncio.create_task(ingestion.ingest_market_data())
        
        logger.info("✅ Streaming services started")
        return producer
        
    except Exception as e:
        logger.error(f"❌ Failed to start streaming services: {e}")
        return None
