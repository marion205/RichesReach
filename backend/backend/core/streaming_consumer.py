"""
Phase 2A: Streaming Data Consumer

This module handles real-time data consumption from Kafka/Kinesis streams
and processes the data for downstream applications like ML models and analytics.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import boto3
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class StreamMessage:
    """Structure for stream messages"""
    topic: str
    partition: int
    offset: int
    key: str
    value: Dict[str, Any]
    timestamp: datetime

class StreamProcessor:
    """Base class for stream processors"""
    
    def __init__(self, name: str):
        self.name = name
        self.running = False
        self.processed_count = 0
        self.error_count = 0
    
    async def process(self, message: StreamMessage) -> bool:
        """Process a stream message. Override in subclasses."""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'name': self.name,
            'running': self.running,
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'success_rate': self.processed_count / (self.processed_count + self.error_count) if (self.processed_count + self.error_count) > 0 else 0
        }

class MarketDataProcessor(StreamProcessor):
    """Processes market data messages"""
    
    def __init__(self, feast_manager=None, redis_cluster=None):
        super().__init__("market_data_processor")
        self.feast_manager = feast_manager
        self.redis_cluster = redis_cluster
    
    async def process(self, message: StreamMessage) -> bool:
        """Process market data message"""
        try:
            data = message.value
            
            # Validate required fields
            required_fields = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in market data: {data}")
                return False
            
            # Store in Redis for real-time access
            if self.redis_cluster:
                cache_key = f"market_data:{data['symbol']}:{data['timestamp']}"
                self.redis_cluster.set(cache_key, data, ex=3600)  # 1 hour TTL
            
            # Store in Feast feature store
            if self.feast_manager:
                # Convert to Feast format
                feature_data = {
                    'stock_id': data['symbol'],
                    'event_timestamp': data['timestamp'],
                    'open': data['open'],
                    'high': data['high'],
                    'low': data['low'],
                    'close': data['close'],
                    'volume': data['volume']
                }
                
                # In a real implementation, you would use Feast's write_to_online_store
                # For now, we'll just log the data
                logger.debug(f"Storing market data in Feast: {data['symbol']}")
            
            self.processed_count += 1
            logger.debug(f"Processed market data: {data['symbol']} at {data['timestamp']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing market data: {e}")
            self.error_count += 1
            return False

class TechnicalIndicatorProcessor(StreamProcessor):
    """Processes technical indicator messages"""
    
    def __init__(self, feast_manager=None, redis_cluster=None):
        super().__init__("technical_indicator_processor")
        self.feast_manager = feast_manager
        self.redis_cluster = redis_cluster
    
    async def process(self, message: StreamMessage) -> bool:
        """Process technical indicator message"""
        try:
            data = message.value
            
            # Validate required fields
            required_fields = ['symbol', 'timestamp', 'timeframe', 'indicators']
            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in technical indicators: {data}")
                return False
            
            # Store in Redis for real-time access
            if self.redis_cluster:
                cache_key = f"indicators:{data['symbol']}:{data['timeframe']}:{data['timestamp']}"
                self.redis_cluster.set(cache_key, data, ex=3600)  # 1 hour TTL
            
            # Store in Feast feature store
            if self.feast_manager:
                # Convert to Feast format
                feature_data = {
                    'stock_id': data['symbol'],
                    'event_timestamp': data['timestamp'],
                    **data['indicators']
                }
                
                logger.debug(f"Storing technical indicators in Feast: {data['symbol']}")
            
            self.processed_count += 1
            logger.debug(f"Processed technical indicators: {data['symbol']} at {data['timestamp']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing technical indicators: {e}")
            self.error_count += 1
            return False

class MLPredictionProcessor(StreamProcessor):
    """Processes ML prediction messages"""
    
    def __init__(self, feast_manager=None, redis_cluster=None):
        super().__init__("ml_prediction_processor")
        self.feast_manager = feast_manager
        self.redis_cluster = redis_cluster
    
    async def process(self, message: StreamMessage) -> bool:
        """Process ML prediction message"""
        try:
            data = message.value
            
            # Validate required fields
            required_fields = ['symbol', 'timestamp', 'model_version', 'prediction', 'confidence']
            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in ML prediction: {data}")
                return False
            
            # Store in Redis for real-time access
            if self.redis_cluster:
                cache_key = f"ml_prediction:{data['symbol']}:{data['model_version']}:{data['timestamp']}"
                self.redis_cluster.set(cache_key, data, ex=3600)  # 1 hour TTL
            
            # Store in Feast feature store
            if self.feast_manager:
                # Convert to Feast format
                feature_data = {
                    'stock_id': data['symbol'],
                    'event_timestamp': data['timestamp'],
                    'model_version': data['model_version'],
                    'prediction': data['prediction'],
                    'confidence': data['confidence']
                }
                
                logger.debug(f"Storing ML prediction in Feast: {data['symbol']}")
            
            self.processed_count += 1
            logger.debug(f"Processed ML prediction: {data['symbol']} at {data['timestamp']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing ML prediction: {e}")
            self.error_count += 1
            return False

class StreamingConsumer:
    """Handles data consumption from Kafka and Kinesis streams"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kafka_consumer = None
        self.kinesis_client = None
        self.processors = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._setup_consumers()
    
    def _setup_consumers(self):
        """Initialize Kafka and Kinesis consumers"""
        try:
            # Kafka consumer
            if self.config.get('kafka_enabled', True):
                kafka_config = self.config.get('kafka', {})
                self.kafka_consumer = KafkaConsumer(
                    bootstrap_servers=kafka_config.get('bootstrap_servers', ['localhost:9092']),
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    key_deserializer=lambda m: m.decode('utf-8') if m else None,
                    group_id=kafka_config.get('group_id', 'riches-reach-consumer'),
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    auto_commit_interval_ms=1000,
                    max_poll_records=100,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000
                )
                logger.info("✅ Kafka consumer initialized")
            
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
            logger.error(f"❌ Failed to setup streaming consumers: {e}")
    
    def register_processor(self, topic: str, processor: StreamProcessor):
        """Register a processor for a specific topic"""
        if topic not in self.processors:
            self.processors[topic] = []
        self.processors[topic].append(processor)
        logger.info(f"Registered processor {processor.name} for topic {topic}")
    
    async def process_message(self, message: StreamMessage):
        """Process a single message with all registered processors"""
        topic = message.topic
        
        if topic not in self.processors:
            logger.warning(f"No processors registered for topic: {topic}")
            return
        
        # Process with all registered processors
        tasks = []
        for processor in self.processors[topic]:
            tasks.append(processor.process(message))
        
        # Wait for all processors to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for i, result in enumerate(results):
            processor = self.processors[topic][i]
            if isinstance(result, Exception):
                logger.error(f"Processor {processor.name} failed: {result}")
            elif result:
                logger.debug(f"Processor {processor.name} succeeded")
            else:
                logger.warning(f"Processor {processor.name} returned False")
    
    async def consume_kafka(self):
        """Consume messages from Kafka"""
        if not self.kafka_consumer:
            logger.warning("Kafka consumer not initialized")
            return
        
        try:
            # Subscribe to topics
            topics = list(self.processors.keys())
            if topics:
                self.kafka_consumer.subscribe(topics)
                logger.info(f"Subscribed to Kafka topics: {topics}")
            
            self.running = True
            logger.info("🚀 Starting Kafka consumption...")
            
            while self.running:
                try:
                    # Poll for messages
                    message_batch = self.kafka_consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            # Convert Kafka message to StreamMessage
                            stream_message = StreamMessage(
                                topic=message.topic,
                                partition=message.partition,
                                offset=message.offset,
                                key=message.key,
                                value=message.value,
                                timestamp=datetime.fromtimestamp(message.timestamp / 1000, tz=timezone.utc)
                            )
                            
                            # Process message
                            await self.process_message(stream_message)
                    
                    # Commit offsets
                    self.kafka_consumer.commit()
                    
                except KafkaError as e:
                    logger.error(f"Kafka error: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
                except Exception as e:
                    logger.error(f"Unexpected error in Kafka consumption: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
            
        except Exception as e:
            logger.error(f"❌ Failed to consume from Kafka: {e}")
        finally:
            if self.kafka_consumer:
                self.kafka_consumer.close()
                logger.info("✅ Kafka consumer closed")
    
    async def consume_kinesis(self):
        """Consume messages from Kinesis"""
        if not self.kinesis_client:
            logger.warning("Kinesis client not initialized")
            return
        
        try:
            stream_name = self.config.get('kinesis', {}).get('stream_name', 'market-data')
            
            # Get shard iterator
            response = self.kinesis_client.get_shard_iterator(
                StreamName=stream_name,
                ShardId='shardId-000000000000',  # First shard
                ShardIteratorType='LATEST'
            )
            
            shard_iterator = response['ShardIterator']
            self.running = True
            logger.info("🚀 Starting Kinesis consumption...")
            
            while self.running:
                try:
                    # Get records
                    response = self.kinesis_client.get_records(
                        ShardIterator=shard_iterator,
                        Limit=100
                    )
                    
                    records = response['Records']
                    shard_iterator = response['NextShardIterator']
                    
                    for record in records:
                        try:
                            # Parse record data
                            data = json.loads(record['Data'].decode('utf-8'))
                            
                            # Create StreamMessage
                            stream_message = StreamMessage(
                                topic='kinesis',  # Use 'kinesis' as topic name
                                partition=0,  # Kinesis doesn't have partitions
                                offset=record['SequenceNumber'],
                                key=record['PartitionKey'],
                                value=data,
                                timestamp=record['ApproximateArrivalTimestamp']
                            )
                            
                            # Process message
                            await self.process_message(stream_message)
                            
                        except Exception as e:
                            logger.error(f"Error processing Kinesis record: {e}")
                    
                    # Wait before next poll
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error consuming from Kinesis: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
            
        except Exception as e:
            logger.error(f"❌ Failed to consume from Kinesis: {e}")
    
    async def start_consumption(self):
        """Start consuming from all configured streams"""
        tasks = []
        
        if self.kafka_consumer:
            tasks.append(self.consume_kafka())
        
        if self.kinesis_client:
            tasks.append(self.consume_kinesis())
        
        if tasks:
            logger.info(f"Starting {len(tasks)} consumption tasks...")
            await asyncio.gather(*tasks)
        else:
            logger.warning("No consumers configured")
    
    def stop(self):
        """Stop consumption"""
        self.running = False
        logger.info("🛑 Stopping stream consumption...")
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get statistics from all processors"""
        stats = {}
        for topic, processors in self.processors.items():
            stats[topic] = [processor.get_stats() for processor in processors]
        return stats

# Global streaming consumer instance
streaming_consumer = None

def get_streaming_consumer() -> Optional[StreamingConsumer]:
    """Get the global streaming consumer instance"""
    return streaming_consumer

def initialize_streaming_consumer(config: Dict[str, Any]) -> StreamingConsumer:
    """Initialize the streaming consumer"""
    global streaming_consumer
    streaming_consumer = StreamingConsumer(config)
    return streaming_consumer

async def start_streaming_consumption(config: Dict[str, Any], feast_manager=None, redis_cluster=None):
    """Start streaming consumption with processors"""
    try:
        consumer = initialize_streaming_consumer(config)
        
        # Register processors
        consumer.register_processor('market-data', MarketDataProcessor(feast_manager, redis_cluster))
        consumer.register_processor('technical-indicators', TechnicalIndicatorProcessor(feast_manager, redis_cluster))
        consumer.register_processor('ml-predictions', MLPredictionProcessor(feast_manager, redis_cluster))
        
        # Start consumption in background
        asyncio.create_task(consumer.start_consumption())
        
        logger.info("✅ Streaming consumption started")
        return consumer
        
    except Exception as e:
        logger.error(f"❌ Failed to start streaming consumption: {e}")
        return None
