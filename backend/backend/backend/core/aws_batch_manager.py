"""
Phase 2: AWS Batch Manager for ML Model Training

This module manages AWS Batch jobs for large-scale ML model training,
scheduled training jobs, and distributed training across multiple instances.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class BatchJobConfig:
    """Configuration for AWS Batch jobs"""
    job_name: str
    job_queue: str
    job_definition: str
    parameters: Dict[str, Any]
    environment_variables: Dict[str, str]
    vcpus: int = 2
    memory: int = 4096
    timeout_minutes: int = 60
    retry_attempts: int = 3

@dataclass
class TrainingJob:
    """Training job information"""
    job_id: str
    job_name: str
    model_type: str
    training_data_path: str
    hyperparameters: Dict[str, Any]
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    log_stream_name: Optional[str] = None
    error_message: Optional[str] = None

class AWSBatchManager:
    """Manages AWS Batch jobs for ML model training"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.region = config.get('region', 'us-east-1')
        self.account_id = config.get('account_id')
        
        # Initialize AWS clients
        self.batch_client = boto3.client('batch', region_name=self.region)
        self.ecs_client = boto3.client('ecs', region_name=self.region)
        self.iam_client = boto3.client('iam', region_name=self.region)
        self.logs_client = boto3.client('logs', region_name=self.region)
        self.s3_client = boto3.client('s3', region_name=self.region)
        
        # Batch configuration
        self.job_queue_name = config.get('job_queue_name', 'riches-reach-ml-queue')
        self.job_definition_name = config.get('job_definition_name', 'riches-reach-ml-training')
        self.compute_environment_name = config.get('compute_environment_name', 'riches-reach-ml-compute')
        self.role_name = config.get('role_name', 'riches-reach-batch-role')
        
        # S3 configuration
        self.s3_bucket = config.get('s3_bucket', 'riches-reach-ml-training-data')
        self.s3_prefix = config.get('s3_prefix', 'training-jobs')
        
        # Training jobs tracking
        self.training_jobs = {}
        
        logger.info(f"✅ AWS Batch Manager initialized for region: {self.region}")
    
    def setup_batch_infrastructure(self) -> bool:
        """Set up AWS Batch infrastructure (compute environment, job queue, job definition)"""
        try:
            logger.info("🏗️ Setting up AWS Batch infrastructure...")
            
            # Create IAM role for Batch
            if not self._create_batch_role():
                return False
            
            # Create compute environment
            if not self._create_compute_environment():
                return False
            
            # Create job queue
            if not self._create_job_queue():
                return False
            
            # Create job definition
            if not self._create_job_definition():
                return False
            
            # Create S3 bucket for training data
            if not self._create_s3_bucket():
                return False
            
            logger.info("✅ AWS Batch infrastructure setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup AWS Batch infrastructure: {e}")
            return False
    
    def _create_batch_role(self) -> bool:
        """Create IAM role for AWS Batch"""
        try:
            role_name = self.role_name
            
            # Check if role already exists
            try:
                self.iam_client.get_role(RoleName=role_name)
                logger.info(f"IAM role {role_name} already exists")
                return True
            except ClientError:
                pass
            
            # Create trust policy
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": [
                                "batch.amazonaws.com",
                                "ecs-tasks.amazonaws.com"
                            ]
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Create role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for RichesReach ML training jobs"
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
            ]
            
            for policy_arn in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
            
            logger.info(f"✅ Created IAM role: {role_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create IAM role: {e}")
            return False
    
    def _create_compute_environment(self) -> bool:
        """Create compute environment for Batch jobs"""
        try:
            compute_env_name = self.compute_environment_name
            
            # Check if compute environment already exists
            try:
                response = self.batch_client.describe_compute_environments(
                    computeEnvironments=[compute_env_name]
                )
                if response['computeEnvironments']:
                    logger.info(f"Compute environment {compute_env_name} already exists")
                    return True
            except ClientError:
                pass
            
            # Create compute environment
            response = self.batch_client.create_compute_environment(
                computeEnvironmentName=compute_env_name,
                type='MANAGED',
                state='ENABLED',
                computeResources={
                    'type': 'EC2',
                    'minvCpus': 0,
                    'maxvCpus': 100,
                    'desiredvCpus': 0,
                    'instanceTypes': ['m5.large', 'm5.xlarge', 'c5.large', 'c5.xlarge'],
                    'subnets': self.config.get('subnet_ids', []),
                    'securityGroupIds': self.config.get('security_group_ids', []),
                    'instanceRole': f'arn:aws:iam::{self.account_id}:instance-profile/ecsInstanceRole',
                    'tags': {
                        'Name': 'RichesReach-ML-Training',
                        'Environment': 'Production'
                    }
                },
                serviceRole=f'arn:aws:iam::{self.account_id}:role/{self.role_name}'
            )
            
            logger.info(f"✅ Created compute environment: {compute_env_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create compute environment: {e}")
            return False
    
    def _create_job_queue(self) -> bool:
        """Create job queue for Batch jobs"""
        try:
            queue_name = self.job_queue_name
            
            # Check if job queue already exists
            try:
                response = self.batch_client.describe_job_queues(
                    jobQueues=[queue_name]
                )
                if response['jobQueues']:
                    logger.info(f"Job queue {queue_name} already exists")
                    return True
            except ClientError:
                pass
            
            # Create job queue
            response = self.batch_client.create_job_queue(
                jobQueueName=queue_name,
                state='ENABLED',
                priority=1,
                computeEnvironmentOrder=[
                    {
                        'order': 1,
                        'computeEnvironment': self.compute_environment_name
                    }
                ]
            )
            
            logger.info(f"✅ Created job queue: {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create job queue: {e}")
            return False
    
    def _create_job_definition(self) -> bool:
        """Create job definition for ML training"""
        try:
            job_def_name = self.job_definition_name
            
            # Check if job definition already exists
            try:
                response = self.batch_client.describe_job_definitions(
                    jobDefinitionName=job_def_name,
                    status='ACTIVE'
                )
                if response['jobDefinitions']:
                    logger.info(f"Job definition {job_def_name} already exists")
                    return True
            except ClientError:
                pass
            
            # Create job definition
            response = self.batch_client.register_job_definition(
                jobDefinitionName=job_def_name,
                type='container',
                containerProperties={
                    'image': self.config.get('training_image', 'python:3.9-slim'),
                    'vcpus': 2,
                    'memory': 4096,
                    'jobRoleArn': f'arn:aws:iam::{self.account_id}:role/{self.role_name}',
                    'environment': [
                        {'name': 'AWS_DEFAULT_REGION', 'value': self.region},
                        {'name': 'S3_BUCKET', 'value': self.s3_bucket},
                        {'name': 'S3_PREFIX', 'value': self.s3_prefix}
                    ],
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-group': f'/aws/batch/{job_def_name}',
                            'awslogs-region': self.region,
                            'awslogs-stream-prefix': 'batch'
                        }
                    }
                },
                retryStrategy={
                    'attempts': 3
                },
                timeout={
                    'attemptDurationSeconds': 3600  # 1 hour
                }
            )
            
            logger.info(f"✅ Created job definition: {job_def_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create job definition: {e}")
            return False
    
    def _create_s3_bucket(self) -> bool:
        """Create S3 bucket for training data"""
        try:
            bucket_name = self.s3_bucket
            
            # Check if bucket already exists
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"S3 bucket {bucket_name} already exists")
                return True
            except ClientError:
                pass
            
            # Create bucket
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Set bucket policy for Batch access
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowBatchAccess",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{self.account_id}:role/{self.role_name}"
                        },
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject"
                        ],
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            logger.info(f"✅ Created S3 bucket: {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create S3 bucket: {e}")
            return False
    
    def submit_training_job(
        self,
        job_name: str,
        model_type: str,
        training_data: pd.DataFrame,
        hyperparameters: Dict[str, Any],
        feature_columns: List[str],
        target_column: str
    ) -> str:
        """Submit a training job to AWS Batch"""
        try:
            # Generate unique job name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_job_name = f"{job_name}_{timestamp}"
            
            # Upload training data to S3
            data_key = f"{self.s3_prefix}/{unique_job_name}/training_data.csv"
            training_data.to_csv(f"s3://{self.s3_bucket}/{data_key}", index=False)
            
            # Prepare job parameters
            job_parameters = {
                'model_type': model_type,
                'training_data_path': f"s3://{self.s3_bucket}/{data_key}",
                'hyperparameters': json.dumps(hyperparameters),
                'feature_columns': json.dumps(feature_columns),
                'target_column': target_column,
                'output_path': f"s3://{self.s3_bucket}/{self.s3_prefix}/{unique_job_name}/output/"
            }
            
            # Submit job
            response = self.batch_client.submit_job(
                jobName=unique_job_name,
                jobQueue=self.job_queue_name,
                jobDefinition=self.job_definition_name,
                parameters=job_parameters,
                containerOverrides={
                    'environment': [
                        {'name': 'JOB_NAME', 'value': unique_job_name},
                        {'name': 'MODEL_TYPE', 'value': model_type},
                        {'name': 'TRAINING_DATA_PATH', 'value': job_parameters['training_data_path']},
                        {'name': 'HYPERPARAMETERS', 'value': job_parameters['hyperparameters']},
                        {'name': 'FEATURE_COLUMNS', 'value': job_parameters['feature_columns']},
                        {'name': 'TARGET_COLUMN', 'value': target_column},
                        {'name': 'OUTPUT_PATH', 'value': job_parameters['output_path']}
                    ]
                }
            )
            
            job_id = response['jobId']
            
            # Create training job record
            training_job = TrainingJob(
                job_id=job_id,
                job_name=unique_job_name,
                model_type=model_type,
                training_data_path=job_parameters['training_data_path'],
                hyperparameters=hyperparameters,
                status='SUBMITTED',
                created_at=datetime.now()
            )
            
            self.training_jobs[job_id] = training_job
            
            logger.info(f"✅ Submitted training job: {unique_job_name} (ID: {job_id})")
            return job_id
            
        except Exception as e:
            logger.error(f"❌ Failed to submit training job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a training job"""
        try:
            response = self.batch_client.describe_jobs(jobs=[job_id])
            
            if not response['jobs']:
                return {'error': 'Job not found'}
            
            job = response['jobs'][0]
            
            # Update training job record
            if job_id in self.training_jobs:
                training_job = self.training_jobs[job_id]
                training_job.status = job['jobStatus']
                
                if job.get('startedAt'):
                    training_job.started_at = datetime.fromtimestamp(job['startedAt'] / 1000)
                
                if job.get('stoppedAt'):
                    training_job.completed_at = datetime.fromtimestamp(job['stoppedAt'] / 1000)
                
                if job.get('exitCode') is not None:
                    training_job.exit_code = job['exitCode']
                
                if job.get('logStreamName'):
                    training_job.log_stream_name = job['logStreamName']
            
            return {
                'job_id': job_id,
                'job_name': job['jobName'],
                'status': job['jobStatus'],
                'status_reason': job.get('statusReason', ''),
                'created_at': datetime.fromtimestamp(job['createdAt'] / 1000).isoformat(),
                'started_at': datetime.fromtimestamp(job['startedAt'] / 1000).isoformat() if job.get('startedAt') else None,
                'stopped_at': datetime.fromtimestamp(job['stoppedAt'] / 1000).isoformat() if job.get('stoppedAt') else None,
                'exit_code': job.get('exitCode'),
                'log_stream_name': job.get('logStreamName')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get job status: {e}")
            return {'error': str(e)}
    
    def get_job_logs(self, job_id: str) -> str:
        """Get logs for a training job"""
        try:
            if job_id not in self.training_jobs:
                return "Job not found"
            
            training_job = self.training_jobs[job_id]
            
            if not training_job.log_stream_name:
                return "No logs available"
            
            # Get logs from CloudWatch
            log_group = f"/aws/batch/{self.job_definition_name}"
            log_stream = training_job.log_stream_name
            
            response = self.logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                startFromHead=True
            )
            
            logs = []
            for event in response['events']:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                logs.append(f"[{timestamp}] {event['message']}")
            
            return '\n'.join(logs)
            
        except Exception as e:
            logger.error(f"❌ Failed to get job logs: {e}")
            return f"Error retrieving logs: {e}"
    
    def list_training_jobs(self) -> List[Dict[str, Any]]:
        """List all training jobs"""
        try:
            jobs = []
            for job_id, training_job in self.training_jobs.items():
                job_info = {
                    'job_id': job_id,
                    'job_name': training_job.job_name,
                    'model_type': training_job.model_type,
                    'status': training_job.status,
                    'created_at': training_job.created_at.isoformat(),
                    'started_at': training_job.started_at.isoformat() if training_job.started_at else None,
                    'completed_at': training_job.completed_at.isoformat() if training_job.completed_at else None,
                    'exit_code': training_job.exit_code
                }
                jobs.append(job_info)
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Failed to list training jobs: {e}")
            return []
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a training job"""
        try:
            self.batch_client.cancel_job(
                jobId=job_id,
                reason="Cancelled by user"
            )
            
            if job_id in self.training_jobs:
                self.training_jobs[job_id].status = 'CANCELLED'
            
            logger.info(f"✅ Cancelled job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel job: {e}")
            return False
    
    def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get status of AWS Batch infrastructure"""
        try:
            status = {
                'compute_environment': {'exists': False, 'status': None},
                'job_queue': {'exists': False, 'status': None},
                'job_definition': {'exists': False, 'status': None},
                's3_bucket': {'exists': False}
            }
            
            # Check compute environment
            try:
                response = self.batch_client.describe_compute_environments(
                    computeEnvironments=[self.compute_environment_name]
                )
                if response['computeEnvironments']:
                    ce = response['computeEnvironments'][0]
                    status['compute_environment'] = {
                        'exists': True,
                        'status': ce['status'],
                        'state': ce['state']
                    }
            except ClientError:
                pass
            
            # Check job queue
            try:
                response = self.batch_client.describe_job_queues(
                    jobQueues=[self.job_queue_name]
                )
                if response['jobQueues']:
                    jq = response['jobQueues'][0]
                    status['job_queue'] = {
                        'exists': True,
                        'status': jq['status'],
                        'state': jq['state']
                    }
            except ClientError:
                pass
            
            # Check job definition
            try:
                response = self.batch_client.describe_job_definitions(
                    jobDefinitionName=self.job_definition_name,
                    status='ACTIVE'
                )
                if response['jobDefinitions']:
                    status['job_definition'] = {
                        'exists': True,
                        'status': 'ACTIVE',
                        'revision': response['jobDefinitions'][0]['revision']
                    }
            except ClientError:
                pass
            
            # Check S3 bucket
            try:
                self.s3_client.head_bucket(Bucket=self.s3_bucket)
                status['s3_bucket'] = {'exists': True}
            except ClientError:
                pass
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get infrastructure status: {e}")
            return {'error': str(e)}

# Global AWS Batch manager instance
aws_batch_manager = None

def get_aws_batch_manager() -> Optional[AWSBatchManager]:
    """Get the global AWS Batch manager instance"""
    return aws_batch_manager

def initialize_aws_batch(config: Dict[str, Any]) -> AWSBatchManager:
    """Initialize AWS Batch manager"""
    global aws_batch_manager
    aws_batch_manager = AWSBatchManager(config)
    return aws_batch_manager
