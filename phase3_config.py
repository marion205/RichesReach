#!/usr/bin/env python3
"""
Phase 3 Configuration Management
Centralized configuration for all Phase 3 components
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class AIConfig:
    """AI Router configuration"""
    openai_api_key: str
    anthropic_api_key: str
    google_ai_api_key: str
    default_model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout_seconds: int = 30
    retry_attempts: int = 3
    cost_optimization: bool = True
    performance_tracking: bool = True

@dataclass
class AnalyticsConfig:
    """Analytics configuration"""
    enable_realtime_bi: bool = True
    enable_market_analytics: bool = True
    enable_user_behavior: bool = True
    enable_predictive_analytics: bool = True
    dashboard_refresh_interval: int = 30
    metrics_retention_days: int = 90
    websocket_enabled: bool = True
    websocket_port: int = 8001

@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    cache_max_size_mb: int = 100
    cache_compression: bool = True
    cdn_enabled: bool = True
    cdn_distribution_id: str = ""
    database_optimization: bool = True
    query_cache_enabled: bool = True
    connection_pooling: bool = True

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 30
    query_timeout: int = 60
    enable_query_cache: bool = True
    enable_connection_pooling: bool = True
    enable_query_optimization: bool = True
    enable_slow_query_logging: bool = True
    slow_query_threshold_ms: int = 1000

@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    cluster_enabled: bool = False
    sentinel_enabled: bool = False
    max_connections: int = 20
    connection_timeout: int = 5
    socket_timeout: int = 5
    retry_on_timeout: bool = True

@dataclass
class AWSConfig:
    """AWS configuration"""
    region: str = "us-east-1"
    access_key_id: str = ""
    secret_access_key: str = ""
    s3_bucket: str = ""
    cloudfront_distribution_id: str = ""
    ecs_cluster: str = ""
    ecs_service: str = ""
    ecr_repository: str = ""

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    enable_cloudwatch: bool = True
    log_level: str = "INFO"
    enable_structured_logging: bool = True
    enable_health_checks: bool = True
    health_check_interval: int = 30

@dataclass
class Phase3Config:
    """Complete Phase 3 configuration"""
    ai: AIConfig
    analytics: AnalyticsConfig
    performance: PerformanceConfig
    database: DatabaseConfig
    redis: RedisConfig
    aws: AWSConfig
    monitoring: MonitoringConfig
    
    # Global settings
    environment: str = "production"
    debug: bool = False
    phase3_enabled: bool = True
    ai_router_enabled: bool = True
    analytics_enabled: bool = True
    performance_optimization_enabled: bool = True

class Phase3ConfigManager:
    """Phase 3 configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "phase3_config.yaml"
        self.config: Optional[Phase3Config] = None
    
    def load_from_env(self) -> Phase3Config:
        """Load configuration from environment variables"""
        try:
            # AI Configuration
            ai_config = AIConfig(
                openai_api_key=os.getenv("OPENAI_API_KEY", ""),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                google_ai_api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
                default_model=os.getenv("AI_DEFAULT_MODEL", "gpt-4"),
                max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
                timeout_seconds=int(os.getenv("AI_TIMEOUT_SECONDS", "30")),
                retry_attempts=int(os.getenv("AI_RETRY_ATTEMPTS", "3")),
                cost_optimization=os.getenv("AI_COST_OPTIMIZATION", "true").lower() == "true",
                performance_tracking=os.getenv("AI_PERFORMANCE_TRACKING", "true").lower() == "true"
            )
            
            # Analytics Configuration
            analytics_config = AnalyticsConfig(
                enable_realtime_bi=os.getenv("ANALYTICS_REALTIME_BI", "true").lower() == "true",
                enable_market_analytics=os.getenv("ANALYTICS_MARKET", "true").lower() == "true",
                enable_user_behavior=os.getenv("ANALYTICS_USER_BEHAVIOR", "true").lower() == "true",
                enable_predictive_analytics=os.getenv("ANALYTICS_PREDICTIVE", "true").lower() == "true",
                dashboard_refresh_interval=int(os.getenv("ANALYTICS_REFRESH_INTERVAL", "30")),
                metrics_retention_days=int(os.getenv("ANALYTICS_RETENTION_DAYS", "90")),
                websocket_enabled=os.getenv("ANALYTICS_WEBSOCKET", "true").lower() == "true",
                websocket_port=int(os.getenv("ANALYTICS_WEBSOCKET_PORT", "8001"))
            )
            
            # Performance Configuration
            performance_config = PerformanceConfig(
                cache_enabled=os.getenv("PERFORMANCE_CACHE_ENABLED", "true").lower() == "true",
                cache_ttl_seconds=int(os.getenv("PERFORMANCE_CACHE_TTL", "3600")),
                cache_max_size_mb=int(os.getenv("PERFORMANCE_CACHE_MAX_SIZE", "100")),
                cache_compression=os.getenv("PERFORMANCE_CACHE_COMPRESSION", "true").lower() == "true",
                cdn_enabled=os.getenv("PERFORMANCE_CDN_ENABLED", "true").lower() == "true",
                cdn_distribution_id=os.getenv("CLOUDFRONT_DISTRIBUTION_ID", ""),
                database_optimization=os.getenv("PERFORMANCE_DB_OPTIMIZATION", "true").lower() == "true",
                query_cache_enabled=os.getenv("PERFORMANCE_QUERY_CACHE", "true").lower() == "true",
                connection_pooling=os.getenv("PERFORMANCE_CONNECTION_POOLING", "true").lower() == "true"
            )
            
            # Database Configuration
            database_config = DatabaseConfig(
                host=os.getenv("DATABASE_HOST", "localhost"),
                port=int(os.getenv("DATABASE_PORT", "5432")),
                database=os.getenv("DATABASE_NAME", "richesreach"),
                username=os.getenv("DATABASE_USER", "admin"),
                password=os.getenv("DATABASE_PASSWORD", "password"),
                min_connections=int(os.getenv("DATABASE_MIN_CONNECTIONS", "5")),
                max_connections=int(os.getenv("DATABASE_MAX_CONNECTIONS", "20")),
                connection_timeout=int(os.getenv("DATABASE_CONNECTION_TIMEOUT", "30")),
                query_timeout=int(os.getenv("DATABASE_QUERY_TIMEOUT", "60")),
                enable_query_cache=os.getenv("DATABASE_QUERY_CACHE", "true").lower() == "true",
                enable_connection_pooling=os.getenv("DATABASE_CONNECTION_POOLING", "true").lower() == "true",
                enable_query_optimization=os.getenv("DATABASE_QUERY_OPTIMIZATION", "true").lower() == "true",
                enable_slow_query_logging=os.getenv("DATABASE_SLOW_QUERY_LOGGING", "true").lower() == "true",
                slow_query_threshold_ms=int(os.getenv("DATABASE_SLOW_QUERY_THRESHOLD", "1000"))
            )
            
            # Redis Configuration
            redis_config = RedisConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD", ""),
                db=int(os.getenv("REDIS_DB", "0")),
                cluster_enabled=os.getenv("REDIS_CLUSTER_ENABLED", "false").lower() == "true",
                sentinel_enabled=os.getenv("REDIS_SENTINEL_ENABLED", "false").lower() == "true",
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
                connection_timeout=int(os.getenv("REDIS_CONNECTION_TIMEOUT", "5")),
                socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
                retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
            )
            
            # AWS Configuration
            aws_config = AWSConfig(
                region=os.getenv("AWS_REGION", "us-east-1"),
                access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
                secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                s3_bucket=os.getenv("AWS_S3_BUCKET", ""),
                cloudfront_distribution_id=os.getenv("CLOUDFRONT_DISTRIBUTION_ID", ""),
                ecs_cluster=os.getenv("ECS_CLUSTER", "richesreach-cluster"),
                ecs_service=os.getenv("ECS_SERVICE", "richesreach-service"),
                ecr_repository=os.getenv("ECR_REPOSITORY", "richesreach")
            )
            
            # Monitoring Configuration
            monitoring_config = MonitoringConfig(
                enable_prometheus=os.getenv("MONITORING_PROMETHEUS", "true").lower() == "true",
                prometheus_port=int(os.getenv("MONITORING_PROMETHEUS_PORT", "9090")),
                enable_cloudwatch=os.getenv("MONITORING_CLOUDWATCH", "true").lower() == "true",
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                enable_structured_logging=os.getenv("STRUCTURED_LOGGING", "true").lower() == "true",
                enable_health_checks=os.getenv("HEALTH_CHECKS_ENABLED", "true").lower() == "true",
                health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
            )
            
            # Global Configuration
            config = Phase3Config(
                ai=ai_config,
                analytics=analytics_config,
                performance=performance_config,
                database=database_config,
                redis=redis_config,
                aws=aws_config,
                monitoring=monitoring_config,
                environment=os.getenv("ENVIRONMENT", "production"),
                debug=os.getenv("DEBUG", "false").lower() == "true",
                phase3_enabled=os.getenv("PHASE3_ENABLED", "true").lower() == "true",
                ai_router_enabled=os.getenv("AI_ROUTER_ENABLED", "true").lower() == "true",
                analytics_enabled=os.getenv("ANALYTICS_ENABLED", "true").lower() == "true",
                performance_optimization_enabled=os.getenv("PERFORMANCE_OPTIMIZATION_ENABLED", "true").lower() == "true"
            )
            
            self.config = config
            logger.info("✅ Configuration loaded from environment variables")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration from environment: {e}")
            raise
    
    def load_from_file(self, file_path: str) -> Phase3Config:
        """Load configuration from YAML file"""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    data = yaml.safe_load(f)
                elif file_path.endswith('.json'):
                    data = json.load(f)
                else:
                    raise ValueError("Unsupported file format. Use .yaml, .yml, or .json")
            
            # Convert to dataclass
            config = Phase3Config(**data)
            self.config = config
            logger.info(f"✅ Configuration loaded from file: {file_path}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration from file {file_path}: {e}")
            raise
    
    def save_to_file(self, file_path: str, config: Optional[Phase3Config] = None):
        """Save configuration to file"""
        try:
            config = config or self.config
            if not config:
                raise ValueError("No configuration to save")
            
            # Convert to dictionary
            data = asdict(config)
            
            with open(file_path, 'w') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    yaml.dump(data, f, default_flow_style=False, indent=2)
                elif file_path.endswith('.json'):
                    json.dump(data, f, indent=2)
                else:
                    raise ValueError("Unsupported file format. Use .yaml, .yml, or .json")
            
            logger.info(f"✅ Configuration saved to file: {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save configuration to file {file_path}: {e}")
            raise
    
    def validate_config(self, config: Optional[Phase3Config] = None) -> List[str]:
        """Validate configuration and return list of issues"""
        config = config or self.config
        if not config:
            return ["No configuration loaded"]
        
        issues = []
        
        # Validate AI configuration
        if not config.ai.openai_api_key:
            issues.append("OpenAI API key is required")
        if not config.ai.anthropic_api_key:
            issues.append("Anthropic API key is required")
        if not config.ai.google_ai_api_key:
            issues.append("Google AI API key is required")
        
        # Validate database configuration
        if not config.database.host:
            issues.append("Database host is required")
        if not config.database.database:
            issues.append("Database name is required")
        if not config.database.username:
            issues.append("Database username is required")
        if not config.database.password:
            issues.append("Database password is required")
        
        # Validate Redis configuration
        if not config.redis.host:
            issues.append("Redis host is required")
        
        # Validate AWS configuration
        if config.performance.cdn_enabled and not config.aws.cloudfront_distribution_id:
            issues.append("CloudFront distribution ID is required when CDN is enabled")
        
        return issues
    
    def get_config(self) -> Optional[Phase3Config]:
        """Get current configuration"""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        if not self.config:
            raise ValueError("No configuration loaded")
        
        # Update configuration fields
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")
        
        logger.info("✅ Configuration updated")

def create_default_config() -> Phase3Config:
    """Create default Phase 3 configuration"""
    return Phase3Config(
        ai=AIConfig(
            openai_api_key="",
            anthropic_api_key="",
            google_ai_api_key=""
        ),
        analytics=AnalyticsConfig(),
        performance=PerformanceConfig(),
        database=DatabaseConfig(
            host="localhost",
            database="richesreach",
            username="admin",
            password="password"
        ),
        redis=RedisConfig(),
        aws=AWSConfig(),
        monitoring=MonitoringConfig()
    )

def main():
    """CLI for configuration management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3 Configuration Manager")
    parser.add_argument("--load-env", action="store_true", help="Load configuration from environment")
    parser.add_argument("--load-file", help="Load configuration from file")
    parser.add_argument("--save-file", help="Save configuration to file")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--create-default", help="Create default configuration file")
    
    args = parser.parse_args()
    
    manager = Phase3ConfigManager()
    
    try:
        if args.create_default:
            config = create_default_config()
            manager.save_to_file(args.create_default, config)
            print(f"✅ Default configuration created: {args.create_default}")
        
        elif args.load_env:
            config = manager.load_from_env()
            print("✅ Configuration loaded from environment")
        
        elif args.load_file:
            config = manager.load_from_file(args.load_file)
            print(f"✅ Configuration loaded from file: {args.load_file}")
        
        if args.save_file:
            manager.save_to_file(args.save_file)
            print(f"✅ Configuration saved to file: {args.save_file}")
        
        if args.validate:
            issues = manager.validate_config()
            if issues:
                print("❌ Configuration validation failed:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("✅ Configuration validation passed")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
