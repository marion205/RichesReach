import json
import os
import time
import urllib.request
import boto3
from botocore.exceptions import ClientError

sm = boto3.client("secretsmanager")

def _get_stage_val(secret_id, stage):
    """Get secret value for a specific stage"""
    try:
        v = sm.get_secret_value(SecretId=secret_id, VersionStage=stage)
        body = json.loads(v.get("SecretString") or "{}")
        return body.get("value")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        raise

def _put_stage_val(secret_id, value, stage):
    """Set secret value for a specific stage"""
    secret_data = {
        "value": value,
        "metadata": {
            "source": "lambda_rotation",
            "rotated_at": time.time(),
            "stage": stage
        }
    }
    sm.put_secret_value(
        SecretId=secret_id,
        SecretString=json.dumps(secret_data),
        VersionStages=[stage]
    )

def _health_check(url):
    """Perform health check on application"""
    try:
        response = urllib.request.urlopen(url, timeout=10)
        return response.status == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def _promote_secret(secret_id, new_secret_value):
    """Promote new secret from AWSPENDING to AWSCURRENT"""
    # 1) Set AWSPENDING to new value
    _put_stage_val(secret_id, new_secret_value, "AWSPENDING")
    
    # 2) Optional health check
    health_url = os.getenv("HEALTHCHECK_URL")
    if health_url:
        if not _health_check(health_url):
            raise RuntimeError("Health check failed; aborting promotion")
    
    # 3) Promote pending to current
    _put_stage_val(secret_id, new_secret_value, "AWSCURRENT")
    
    print(f"Successfully rotated secret: {secret_id}")

def lambda_handler(event, context):
    """Main Lambda handler for secret rotation"""
    try:
        # Parse event
        if isinstance(event, str):
            event = json.loads(event)
        
        secret_id = event.get("SecretId")
        candidate_value = event.get("CandidateValue")
        action = event.get("Action", "rotate")
        
        if not secret_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "SecretId is required"})
            }
        
        if action == "check_rotation_status":
            # Just check if rotation is needed
            current_value = _get_stage_val(secret_id, "AWSCURRENT")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "checked",
                    "secret_id": secret_id,
                    "has_current": current_value is not None
                })
            }
        
        if not candidate_value:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "CandidateValue is required for rotation"})
            }
        
        # Perform rotation
        _promote_secret(secret_id, candidate_value)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "rotated",
                "secret_id": secret_id,
                "timestamp": time.time()
            })
        }
        
    except Exception as e:
        print(f"Rotation failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
