"""
CDN and Edge Computing Optimizer - Phase 3
CloudFront optimization, edge computing, and global content delivery
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import aiohttp
import gzip
import base64
from pathlib import Path
import mimetypes
import os

logger = logging.getLogger("richesreach")

@dataclass
class CDNConfig:
    """CDN configuration"""
    distribution_id: str
    region: str = "us-east-1"
    cache_ttl: int = 86400  # 24 hours
    compression_enabled: bool = True
    gzip_enabled: bool = True
    brotli_enabled: bool = True
    edge_locations: List[str] = None
    origin_domain: str = ""
    ssl_certificate_arn: str = ""
    custom_headers: Dict[str, str] = None

@dataclass
class EdgeLocation:
    """Edge location information"""
    location: str
    region: str
    latency_ms: float
    cache_hit_rate: float
    requests_per_second: float
    last_updated: datetime

@dataclass
class CDNMetrics:
    """CDN performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    average_latency_ms: float = 0.0
    bandwidth_saved_mb: float = 0.0
    compression_ratio: float = 0.0
    edge_locations_active: int = 0
    origin_requests: int = 0
    error_rate: float = 0.0

class CloudFrontOptimizer:
    """CloudFront CDN optimization system"""
    
    def __init__(self, config: CDNConfig):
        self.config = config
        self.cloudfront_client = boto3.client('cloudfront', region_name=config.region)
        self.s3_client = boto3.client('s3', region_name=config.region)
        self.metrics = CDNMetrics()
        self.edge_locations = {}
        self.cache_invalidation_queue = []
        
        # Initialize CDN
        asyncio.create_task(self._initialize_cdn())
        
        # Start background tasks
        asyncio.create_task(self._monitor_cdn_performance())
        asyncio.create_task(self._process_invalidations())
        asyncio.create_task(self._optimize_cache_behavior())
    
    async def _initialize_cdn(self):
        """Initialize CloudFront distribution"""
        try:
            # Get distribution configuration
            response = self.cloudfront_client.get_distribution_config(Id=self.config.distribution_id)
            self.distribution_config = response['DistributionConfig']
            self.etag = response['ETag']
            
            logger.info(f"✅ CloudFront distribution {self.config.distribution_id} initialized")
            
        except ClientError as e:
            logger.error(f"❌ Failed to initialize CloudFront: {e}")
            raise
    
    async def _monitor_cdn_performance(self):
        """Monitor CDN performance metrics"""
        while True:
            try:
                # Get CloudWatch metrics for the distribution
                cloudwatch = boto3.client('cloudwatch', region_name=self.config.region)
                
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=1)
                
                # Get cache hit rate
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/CloudFront',
                    MetricName='CacheHitRate',
                    Dimensions=[
                        {'Name': 'DistributionId', 'Value': self.config.distribution_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                if response['Datapoints']:
                    self.metrics.hit_rate = response['Datapoints'][-1]['Average']
                
                # Get request count
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/CloudFront',
                    MetricName='Requests',
                    Dimensions=[
                        {'Name': 'DistributionId', 'Value': self.config.distribution_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                if response['Datapoints']:
                    self.metrics.total_requests = int(response['Datapoints'][-1]['Sum'])
                
                # Get origin requests
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/CloudFront',
                    MetricName='OriginRequests',
                    Dimensions=[
                        {'Name': 'DistributionId', 'Value': self.config.distribution_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                if response['Datapoints']:
                    self.metrics.origin_requests = int(response['Datapoints'][-1]['Sum'])
                
                # Calculate cache hits and misses
                self.metrics.cache_hits = int(self.metrics.total_requests * self.metrics.hit_rate)
                self.metrics.cache_misses = self.metrics.total_requests - self.metrics.cache_hits
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring CDN performance: {e}")
                await asyncio.sleep(300)
    
    async def _process_invalidations(self):
        """Process cache invalidation queue"""
        while True:
            try:
                if self.cache_invalidation_queue:
                    # Process invalidation batch
                    paths = self.cache_invalidation_queue[:1000]  # Max 1000 paths per invalidation
                    self.cache_invalidation_queue = self.cache_invalidation_queue[1000:]
                    
                    # Create invalidation
                    response = self.cloudfront_client.create_invalidation(
                        DistributionId=self.config.distribution_id,
                        InvalidationBatch={
                            'Paths': {
                                'Quantity': len(paths),
                                'Items': paths
                            },
                            'CallerReference': f"batch-{int(time.time())}"
                        }
                    )
                    
                    logger.info(f"Created invalidation for {len(paths)} paths: {response['Invalidation']['Id']}")
                
                await asyncio.sleep(60)  # Process every minute
                
            except Exception as e:
                logger.error(f"Error processing invalidations: {e}")
                await asyncio.sleep(60)
    
    async def _optimize_cache_behavior(self):
        """Optimize cache behavior based on performance"""
        while True:
            try:
                # Analyze cache performance and optimize
                if self.metrics.hit_rate < 0.8:  # Low hit rate
                    await self._optimize_cache_headers()
                
                if self.metrics.origin_requests > self.metrics.total_requests * 0.3:  # High origin requests
                    await self._optimize_cache_ttl()
                
                await asyncio.sleep(1800)  # Optimize every 30 minutes
                
            except Exception as e:
                logger.error(f"Error optimizing cache behavior: {e}")
                await asyncio.sleep(1800)
    
    async def _optimize_cache_headers(self):
        """Optimize cache headers for better hit rates"""
        try:
            # Update cache behavior configuration
            logger.info("Optimizing cache headers for better hit rates")
            
            # This would typically involve updating the CloudFront distribution configuration
            # For now, just log the optimization attempt
            
        except Exception as e:
            logger.error(f"Error optimizing cache headers: {e}")
    
    async def _optimize_cache_ttl(self):
        """Optimize cache TTL based on content type"""
        try:
            # Update TTL settings for different content types
            logger.info("Optimizing cache TTL settings")
            
            # This would typically involve updating the CloudFront distribution configuration
            # For now, just log the optimization attempt
            
        except Exception as e:
            logger.error(f"Error optimizing cache TTL: {e}")
    
    async def invalidate_cache(self, paths: List[str]):
        """Invalidate cache for specific paths"""
        try:
            # Add paths to invalidation queue
            self.cache_invalidation_queue.extend(paths)
            logger.info(f"Queued {len(paths)} paths for cache invalidation")
            
        except Exception as e:
            logger.error(f"Error queuing cache invalidation: {e}")
    
    async def preload_cache(self, paths: List[str]):
        """Preload cache for specific paths"""
        try:
            # Preload cache by making requests to CloudFront
            async with aiohttp.ClientSession() as session:
                for path in paths:
                    url = f"https://{self.config.origin_domain}{path}"
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                logger.info(f"Preloaded cache for: {path}")
                    except Exception as e:
                        logger.warning(f"Failed to preload {path}: {e}")
            
        except Exception as e:
            logger.error(f"Error preloading cache: {e}")
    
    def get_metrics(self) -> CDNMetrics:
        """Get CDN performance metrics"""
        return self.metrics

class EdgeComputingOptimizer:
    """Edge computing optimization system"""
    
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.edge_functions = {}
        self.edge_metrics = {}
        
        # Initialize edge computing
        asyncio.create_task(self._initialize_edge_computing())
    
    async def _initialize_edge_computing(self):
        """Initialize edge computing functions"""
        try:
            # List existing Lambda@Edge functions
            response = self.lambda_client.list_functions()
            
            for function in response['Functions']:
                if 'edge' in function['FunctionName'].lower():
                    self.edge_functions[function['FunctionName']] = {
                        'arn': function['FunctionArn'],
                        'runtime': function['Runtime'],
                        'last_modified': function['LastModified']
                    }
            
            logger.info(f"✅ Edge computing initialized with {len(self.edge_functions)} functions")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize edge computing: {e}")
    
    async def deploy_edge_function(self, function_name: str, code: str, runtime: str = "python3.9"):
        """Deploy Lambda@Edge function"""
        try:
            # Create or update Lambda function
            try:
                # Try to update existing function
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=code.encode('utf-8')
                )
                logger.info(f"Updated edge function: {function_name}")
            except ClientError:
                # Create new function
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=runtime,
                    Role='arn:aws:iam::123456789012:role/lambda-edge-role',  # Replace with actual role
                    Handler='index.handler',
                    Code={'ZipFile': code.encode('utf-8')},
                    Description=f'Edge function for {function_name}'
                )
                logger.info(f"Created edge function: {function_name}")
            
            self.edge_functions[function_name] = {
                'arn': response['FunctionArn'],
                'runtime': runtime,
                'last_modified': response['LastModified']
            }
            
            return response['FunctionArn']
            
        except Exception as e:
            logger.error(f"Error deploying edge function {function_name}: {e}")
            raise
    
    async def optimize_response_compression(self, content: str, content_type: str) -> Tuple[str, str]:
        """Optimize response compression at edge"""
        try:
            # Determine best compression method
            if self._should_compress(content_type, len(content)):
                if self.config.brotli_enabled:
                    # Use Brotli compression
                    compressed = self._brotli_compress(content)
                    return compressed, 'br'
                elif self.config.gzip_enabled:
                    # Use Gzip compression
                    compressed = gzip.compress(content.encode('utf-8'))
                    return base64.b64encode(compressed).decode('utf-8'), 'gzip'
            
            return content, 'identity'
            
        except Exception as e:
            logger.error(f"Error optimizing response compression: {e}")
            return content, 'identity'
    
    def _should_compress(self, content_type: str, content_length: int) -> bool:
        """Determine if content should be compressed"""
        compressible_types = [
            'text/html', 'text/css', 'text/javascript', 'application/javascript',
            'application/json', 'text/xml', 'application/xml'
        ]
        
        return (
            any(ct in content_type for ct in compressible_types) and
            content_length > 1024  # Only compress if > 1KB
        )
    
    def _brotli_compress(self, content: str) -> str:
        """Compress content using Brotli"""
        try:
            import brotli
            compressed = brotli.compress(content.encode('utf-8'))
            return base64.b64encode(compressed).decode('utf-8')
        except ImportError:
            logger.warning("Brotli not available, falling back to gzip")
            compressed = gzip.compress(content.encode('utf-8'))
            return base64.b64encode(compressed).decode('utf-8')
    
    async def optimize_image_delivery(self, image_path: str, width: int = None, height: int = None, format: str = None) -> str:
        """Optimize image delivery at edge"""
        try:
            # Generate optimized image URL
            params = []
            if width:
                params.append(f"w_{width}")
            if height:
                params.append(f"h_{height}")
            if format:
                params.append(f"f_{format}")
            
            if params:
                optimized_path = f"{image_path}?{'&'.join(params)}"
            else:
                optimized_path = image_path
            
            return optimized_path
            
        except Exception as e:
            logger.error(f"Error optimizing image delivery: {e}")
            return image_path
    
    async def optimize_api_response(self, response_data: Dict[str, Any], user_location: str = None) -> Dict[str, Any]:
        """Optimize API response for edge delivery"""
        try:
            # Add edge-specific optimizations
            optimized_response = response_data.copy()
            
            # Add edge location information
            if user_location:
                optimized_response['_edge'] = {
                    'location': user_location,
                    'timestamp': datetime.utcnow().isoformat(),
                    'optimized': True
                }
            
            # Optimize JSON structure for faster parsing
            if 'data' in optimized_response and isinstance(optimized_response['data'], list):
                # Sort by relevance if possible
                optimized_response['data'] = sorted(
                    optimized_response['data'],
                    key=lambda x: x.get('relevance', 0),
                    reverse=True
                )
            
            return optimized_response
            
        except Exception as e:
            logger.error(f"Error optimizing API response: {e}")
            return response_data

class CDNOptimizer:
    """Comprehensive CDN and edge computing optimizer"""
    
    def __init__(self, cdn_config: CDNConfig):
        self.cdn_config = cdn_config
        self.cloudfront_optimizer = CloudFrontOptimizer(cdn_config)
        self.edge_optimizer = EdgeComputingOptimizer()
        self.optimization_rules = []
        
        # Initialize optimization rules
        self._initialize_optimization_rules()
    
    def _initialize_optimization_rules(self):
        """Initialize CDN optimization rules"""
        self.optimization_rules = [
            self._optimize_static_content,
            self._optimize_api_responses,
            self._optimize_image_delivery,
            self._optimize_video_streaming,
            self._optimize_mobile_delivery
        ]
    
    async def _optimize_static_content(self):
        """Optimize static content delivery"""
        try:
            # Implement static content optimization
            logger.info("Optimizing static content delivery")
            
        except Exception as e:
            logger.error(f"Error optimizing static content: {e}")
    
    async def _optimize_api_responses(self):
        """Optimize API response delivery"""
        try:
            # Implement API response optimization
            logger.info("Optimizing API response delivery")
            
        except Exception as e:
            logger.error(f"Error optimizing API responses: {e}")
    
    async def _optimize_image_delivery(self):
        """Optimize image delivery"""
        try:
            # Implement image optimization
            logger.info("Optimizing image delivery")
            
        except Exception as e:
            logger.error(f"Error optimizing image delivery: {e}")
    
    async def _optimize_video_streaming(self):
        """Optimize video streaming"""
        try:
            # Implement video optimization
            logger.info("Optimizing video streaming")
            
        except Exception as e:
            logger.error(f"Error optimizing video streaming: {e}")
    
    async def _optimize_mobile_delivery(self):
        """Optimize mobile content delivery"""
        try:
            # Implement mobile optimization
            logger.info("Optimizing mobile content delivery")
            
        except Exception as e:
            logger.error(f"Error optimizing mobile delivery: {e}")
    
    async def optimize_content(self, content: str, content_type: str, user_location: str = None) -> Tuple[str, Dict[str, str]]:
        """Optimize content for CDN delivery"""
        try:
            # Apply edge optimizations
            optimized_content, compression_type = await self.edge_optimizer.optimize_response_compression(
                content, content_type
            )
            
            # Add optimization headers
            headers = {
                'Content-Encoding': compression_type,
                'Cache-Control': f'max-age={self.cdn_config.cache_ttl}',
                'Vary': 'Accept-Encoding',
                'X-Edge-Optimized': 'true'
            }
            
            if user_location:
                headers['X-Edge-Location'] = user_location
            
            return optimized_content, headers
            
        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            return content, {}
    
    def get_cdn_metrics(self) -> CDNMetrics:
        """Get CDN performance metrics"""
        return self.cloudfront_optimizer.get_metrics()
    
    async def invalidate_content(self, paths: List[str]):
        """Invalidate CDN cache for specific paths"""
        await self.cloudfront_optimizer.invalidate_cache(paths)
    
    async def preload_content(self, paths: List[str]):
        """Preload CDN cache for specific paths"""
        await self.cloudfront_optimizer.preload_cache(paths)

# Global CDN optimizer instance
cdn_optimizer = None

def initialize_cdn_optimizer(config: CDNConfig):
    """Initialize global CDN optimizer"""
    global cdn_optimizer
    cdn_optimizer = CDNOptimizer(config)
    logger.info("✅ CDN optimizer initialized successfully")
