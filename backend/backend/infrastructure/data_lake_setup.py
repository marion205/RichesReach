#!/usr/bin/env python3
"""
RichesReach Data Lake Setup
Phase 1: S3 Data Lake Infrastructure
"""

import boto3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class DataLakeManager:
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        self.s3_resource = boto3.resource('s3', region_name=region)
        
    def setup_data_lake_structure(self):
        """Create the standard data lake folder structure"""
        structure = {
            "raw/": {
                "market_data/": {
                    "polygon/": {},
                    "finnhub/": {},
                    "coingecko/": {}
                },
                "news/": {},
                "sentiment/": {}
            },
            "processed/": {
                "features/": {
                    "technical_indicators/": {},
                    "fundamental_data/": {},
                    "sentiment_scores/": {}
                },
                "ml_models/": {
                    "training_data/": {},
                    "model_artifacts/": {},
                    "predictions/": {}
                }
            },
            "curated/": {
                "daily_summaries/": {},
                "portfolio_analytics/": {},
                "risk_metrics/": {}
            },
            "metadata/": {
                "schemas/": {},
                "lineage/": {},
                "quality_checks/": {}
            }
        }
        
        self._create_folder_structure(structure)
        print(f"✅ Data lake structure created in s3://{self.bucket_name}")
        
    def _create_folder_structure(self, structure, prefix=""):
        """Recursively create folder structure in S3"""
        for folder, subfolders in structure.items():
            folder_path = f"{prefix}{folder}"
            # Create folder marker
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=folder_path,
                Body=b'',
                ContentType='application/x-directory'
            )
            
            if subfolders:
                self._create_folder_structure(subfolders, folder_path)
    
    def setup_lifecycle_policies(self):
        """Set up S3 lifecycle policies for cost optimization"""
        lifecycle_config = {
            "Rules": [
                {
                    "ID": "RawDataTransition",
                    "Status": "Enabled",
                    "Filter": {"Prefix": "raw/"},
                    "Transitions": [
                        {
                            "Days": 30,
                            "StorageClass": "STANDARD_IA"
                        },
                        {
                            "Days": 90,
                            "StorageClass": "GLACIER"
                        },
                        {
                            "Days": 365,
                            "StorageClass": "DEEP_ARCHIVE"
                        }
                    ]
                },
                {
                    "ID": "ProcessedDataTransition",
                    "Status": "Enabled",
                    "Filter": {"Prefix": "processed/"},
                    "Transitions": [
                        {
                            "Days": 30,
                            "StorageClass": "STANDARD_IA"
                        },
                        {
                            "Days": 90,
                            "StorageClass": "GLACIER"
                        }
                    ]
                },
                {
                    "ID": "CuratedDataRetention",
                    "Status": "Enabled",
                    "Filter": {"Prefix": "curated/"},
                    "Transitions": [
                        {
                            "Days": 30,
                            "StorageClass": "STANDARD_IA"
                        }
                    ]
                }
            ]
        }
        
        self.s3_client.put_bucket_lifecycle_configuration(
            Bucket=self.bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        print("✅ Lifecycle policies configured")
    
    def setup_cors_policy(self):
        """Set up CORS policy for web access"""
        cors_config = {
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
                    "AllowedOrigins": ["*"],
                    "ExposeHeaders": ["ETag"],
                    "MaxAgeSeconds": 3000
                }
            ]
        }
        
        self.s3_client.put_bucket_cors(
            Bucket=self.bucket_name,
            CORSConfiguration=cors_config
        )
        print("✅ CORS policy configured")
    
    def create_sample_data_schema(self):
        """Create sample data schemas for different data types"""
        schemas = {
            "market_data_schema.json": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "open": {"type": "number"},
                    "high": {"type": "number"},
                    "low": {"type": "number"},
                    "close": {"type": "number"},
                    "volume": {"type": "integer"},
                    "source": {"type": "string", "enum": ["polygon", "finnhub"]}
                },
                "required": ["symbol", "timestamp", "close", "volume", "source"]
            },
            "technical_indicators_schema.json": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "sma_20": {"type": "number"},
                    "ema_12": {"type": "number"},
                    "rsi_14": {"type": "number"},
                    "macd": {"type": "number"},
                    "bollinger_upper": {"type": "number"},
                    "bollinger_lower": {"type": "number"}
                },
                "required": ["symbol", "timestamp"]
            },
            "sentiment_schema.json": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "sentiment_score": {"type": "number", "minimum": -1, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "source": {"type": "string"},
                    "text": {"type": "string"}
                },
                "required": ["symbol", "timestamp", "sentiment_score", "source"]
            }
        }
        
        for filename, schema in schemas.items():
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"metadata/schemas/{filename}",
                Body=json.dumps(schema, indent=2),
                ContentType='application/json'
            )
        
        print("✅ Data schemas created")

def main():
    """Main setup function"""
    bucket_name = "riches-reach-ai-datalake-20251005"
    
    print("🚀 Setting up RichesReach Data Lake...")
    
    dl_manager = DataLakeManager(bucket_name)
    
    # Create folder structure
    dl_manager.setup_data_lake_structure()
    
    # Set up lifecycle policies
    dl_manager.setup_lifecycle_policies()
    
    # Set up CORS
    dl_manager.setup_cors_policy()
    
    # Create sample schemas
    dl_manager.create_sample_data_schema()
    
    print(f"✅ Data lake setup complete!")
    print(f"📊 Bucket: s3://{bucket_name}")
    print(f"🌍 Region: us-east-1")
    print(f"📁 Structure: raw/ → processed/ → curated/")

if __name__ == "__main__":
    main()
