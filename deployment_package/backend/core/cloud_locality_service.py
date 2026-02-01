"""
Cloud Locality Optimization Service
Routes inference requests to the nearest inference engine based on broker API location.
"""
import logging
import os
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BrokerRegion(Enum):
    """Broker API regions"""
    US_EAST = "us-east-1"  # New York (Alpaca primary)
    US_WEST = "us-west-2"  # California (Alpaca secondary)
    EU_WEST = "eu-west-1"  # Europe (for international brokers)
    ASIA_PACIFIC = "ap-southeast-1"  # Asia Pacific
    UNKNOWN = "unknown"


@dataclass
class InferenceEndpoint:
    """Inference engine endpoint configuration"""
    region: str
    url: str
    latency_ms: float = 0.0
    last_checked: float = 0.0
    is_active: bool = True
    priority: int = 0  # Lower = higher priority


class CloudLocalityService:
    """
    Manages cloud locality optimization by routing requests to nearest inference engine.
    
    Features:
    - Detects broker API region
    - Maintains list of inference engine endpoints by region
    - Routes requests to nearest endpoint
    - Monitors latency and health
    - Falls back to default if nearest is unavailable
    """
    
    def __init__(self):
        self.broker_regions = self._detect_broker_regions()
        self.inference_endpoints: Dict[str, List[InferenceEndpoint]] = {}
        self.default_endpoint: Optional[str] = None
        self.health_check_interval = 60  # Check health every 60 seconds
        self.last_health_check = 0.0
        
        # Load configuration from environment
        self._load_configuration()
        
        # Initialize default endpoint (local if not configured)
        if not self.default_endpoint:
            self.default_endpoint = "http://localhost:8000"
    
    def _detect_broker_regions(self) -> Dict[str, BrokerRegion]:
        """
        Detect broker API regions from configuration.
        
        Returns:
            Dict mapping broker name to region
        """
        regions = {}
        
        # Alpaca API endpoints
        alpaca_base_url = os.getenv('ALPACA_API_BASE_URL', 'https://paper-api.alpaca.markets')
        alpaca_broker_url = os.getenv('ALPACA_BROKER_API_BASE_URL', 'https://broker-api.sandbox.alpaca.markets')
        
        # Detect Alpaca region from URL
        if 'sandbox' in alpaca_base_url or 'sandbox' in alpaca_broker_url:
            # Sandbox is typically in us-east-1
            regions['alpaca'] = BrokerRegion.US_EAST
        elif 'api.alpaca.markets' in alpaca_base_url:
            # Production Alpaca is in us-east-1 (New York)
            regions['alpaca'] = BrokerRegion.US_EAST
        else:
            regions['alpaca'] = BrokerRegion.UNKNOWN
        
        # Add other brokers as needed
        # Example: Interactive Brokers, TD Ameritrade, etc.
        
        logger.info(f"Detected broker regions: {regions}")
        return regions
    
    def _load_configuration(self):
        """Load inference endpoint configuration from environment variables"""
        # Format: INFERENCE_ENDPOINTS=region1:url1,region2:url2
        endpoints_str = os.getenv('INFERENCE_ENDPOINTS', '')
        
        if endpoints_str:
            for endpoint_config in endpoints_str.split(','):
                if ':' in endpoint_config:
                    region, url = endpoint_config.split(':', 1)
                    self.add_inference_endpoint(region, url)
        
        # Set default endpoint
        default_url = os.getenv('DEFAULT_INFERENCE_ENDPOINT')
        if default_url:
            self.default_endpoint = default_url
        
        logger.info(f"Loaded {len(self.inference_endpoints)} inference endpoint regions")
    
    def add_inference_endpoint(self, region: str, url: str, priority: int = 0):
        """
        Add an inference endpoint for a specific region.
        
        Args:
            region: AWS region name (e.g., 'us-east-1')
            url: Inference engine URL
            priority: Priority (lower = higher priority)
        """
        if region not in self.inference_endpoints:
            self.inference_endpoints[region] = []
        
        endpoint = InferenceEndpoint(
            region=region,
            url=url,
            priority=priority,
            is_active=True
        )
        
        self.inference_endpoints[region].append(endpoint)
        
        # Sort by priority
        self.inference_endpoints[region].sort(key=lambda x: x.priority)
        
        logger.info(f"Added inference endpoint: {region} -> {url} (priority: {priority})")
    
    def get_nearest_endpoint(self, broker_name: str = 'alpaca') -> Optional[str]:
        """
        Get the nearest inference endpoint for a broker.
        
        Args:
            broker_name: Name of the broker (default: 'alpaca')
        
        Returns:
            URL of nearest inference endpoint, or default if none found
        """
        # Get broker region
        broker_region = self.broker_regions.get(broker_name, BrokerRegion.UNKNOWN)
        
        if broker_region == BrokerRegion.UNKNOWN:
            logger.warning(f"Unknown broker region for {broker_name}, using default endpoint")
            return self.default_endpoint
        
        # Find endpoints in the same region
        region_str = broker_region.value
        if region_str in self.inference_endpoints:
            endpoints = self.inference_endpoints[region_str]
            
            # Return first active endpoint (sorted by priority)
            for endpoint in endpoints:
                if endpoint.is_active:
                    # Check health if needed
                    if time.time() - endpoint.last_checked > self.health_check_interval:
                        self._check_endpoint_health(endpoint)
                    
                    if endpoint.is_active:
                        logger.debug(f"Using nearest endpoint: {endpoint.url} (region: {region_str})")
                        return endpoint.url
        
        # Fallback: try nearby regions
        nearby_regions = self._get_nearby_regions(broker_region)
        for nearby_region in nearby_regions:
            if nearby_region.value in self.inference_endpoints:
                endpoints = self.inference_endpoints[nearby_region.value]
                for endpoint in endpoints:
                    if endpoint.is_active:
                        logger.info(f"Using nearby endpoint: {endpoint.url} (region: {nearby_region.value})")
                        return endpoint.url
        
        # Final fallback: default endpoint
        logger.warning(f"No active inference endpoint found for {broker_name}, using default: {self.default_endpoint}")
        return self.default_endpoint
    
    def _get_nearby_regions(self, region: BrokerRegion) -> List[BrokerRegion]:
        """
        Get nearby regions for fallback routing.
        
        Args:
            region: Primary region
        
        Returns:
            List of nearby regions in order of proximity
        """
        nearby_map = {
            BrokerRegion.US_EAST: [BrokerRegion.US_WEST, BrokerRegion.EU_WEST],
            BrokerRegion.US_WEST: [BrokerRegion.US_EAST, BrokerRegion.ASIA_PACIFIC],
            BrokerRegion.EU_WEST: [BrokerRegion.US_EAST, BrokerRegion.ASIA_PACIFIC],
            BrokerRegion.ASIA_PACIFIC: [BrokerRegion.US_WEST, BrokerRegion.EU_WEST],
        }
        
        return nearby_map.get(region, [])
    
    def _check_endpoint_health(self, endpoint: InferenceEndpoint):
        """
        Check health of an inference endpoint.
        
        Args:
            endpoint: Endpoint to check
        """
        try:
            start_time = time.time()
            response = requests.get(
                f"{endpoint.url}/health",
                timeout=2.0  # 2 second timeout
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                endpoint.is_active = True
                endpoint.latency_ms = latency_ms
                endpoint.last_checked = time.time()
                logger.debug(f"Endpoint {endpoint.url} is healthy (latency: {latency_ms:.1f}ms)")
            else:
                endpoint.is_active = False
                logger.warning(f"Endpoint {endpoint.url} returned status {response.status_code}")
        
        except Exception as e:
            endpoint.is_active = False
            logger.warning(f"Endpoint {endpoint.url} health check failed: {e}")
    
    def measure_latency(self, endpoint_url: str, broker_name: str = 'alpaca') -> float:
        """
        Measure latency to an inference endpoint from broker location.
        
        Args:
            endpoint_url: Inference endpoint URL
            broker_name: Broker name
        
        Returns:
            Latency in milliseconds
        """
        try:
            # Measure round-trip time
            start_time = time.time()
            response = requests.get(
                f"{endpoint_url}/health",
                timeout=5.0
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                logger.debug(f"Latency to {endpoint_url}: {latency_ms:.1f}ms")
                return latency_ms
            else:
                logger.warning(f"Endpoint {endpoint_url} returned status {response.status_code}")
                return float('inf')
        
        except Exception as e:
            logger.error(f"Error measuring latency to {endpoint_url}: {e}")
            return float('inf')
    
    def get_optimal_endpoint(self, broker_name: str = 'alpaca') -> Tuple[str, float]:
        """
        Get optimal inference endpoint with measured latency.
        
        Args:
            broker_name: Broker name
        
        Returns:
            Tuple of (endpoint_url, latency_ms)
        """
        endpoint_url = self.get_nearest_endpoint(broker_name)
        
        if endpoint_url:
            latency = self.measure_latency(endpoint_url, broker_name)
            return (endpoint_url, latency)
        
        return (self.default_endpoint, float('inf'))
    
    def get_status(self) -> Dict[str, any]:
        """
        Get status of cloud locality optimization.
        
        Returns:
            Dict with status information
        """
        status = {
            'enabled': len(self.inference_endpoints) > 0,
            'broker_regions': {
                name: region.value
                for name, region in self.broker_regions.items()
            },
            'endpoints': {},
            'default_endpoint': self.default_endpoint
        }
        
        for region, endpoints in self.inference_endpoints.items():
            status['endpoints'][region] = [
                {
                    'url': ep.url,
                    'is_active': ep.is_active,
                    'latency_ms': ep.latency_ms,
                    'priority': ep.priority
                }
                for ep in endpoints
            ]
        
        return status


# Global instance
_cloud_locality_service = None

def get_cloud_locality_service() -> CloudLocalityService:
    """Get global cloud locality service instance"""
    global _cloud_locality_service
    if _cloud_locality_service is None:
        _cloud_locality_service = CloudLocalityService()
    return _cloud_locality_service

