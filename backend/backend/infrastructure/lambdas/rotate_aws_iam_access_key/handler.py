import json
import boto3
from botocore.exceptions import ClientError

iam = boto3.client("iam")
sm = boto3.client("secretsmanager")

IAM_USER = "richesreach-ci"

def lambda_handler(event, context):
    """Rotate AWS IAM access keys"""
    try:
        secret_id = event["SecretId"]
        
        # Create new access key
        response = iam.create_access_key(UserName=IAM_USER)
        new_key = {
            "aws_access_key_id": response["AccessKey"]["AccessKeyId"],
            "aws_secret_access_key": response["AccessKey"]["SecretAccessKey"],
            "metadata": {
                "created_at": response["AccessKey"]["CreateDate"].isoformat(),
                "user": IAM_USER
            }
        }
        
        # Stage as pending
        sm.put_secret_value(
            SecretId=secret_id,
            SecretString=json.dumps(new_key),
            VersionStages=["AWSPENDING"]
        )
        
        # Promote to current
        sm.put_secret_value(
            SecretId=secret_id,
            SecretString=json.dumps(new_key),
            VersionStages=["AWSCURRENT"]
        )
        
        # Deactivate old key (optional - list and deactivate previous)
        try:
            old_keys = iam.list_access_keys(UserName=IAM_USER)
            for key in old_keys["AccessKeyMetadata"]:
                if key["AccessKeyId"] != new_key["aws_access_key_id"]:
                    iam.delete_access_key(
                        UserName=IAM_USER,
                        AccessKeyId=key["AccessKeyId"]
                    )
        except ClientError as e:
            print(f"Warning: Could not clean up old key: {e}")
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "rotated",
                "secret_id": secret_id,
                "new_key_id": new_key["aws_access_key_id"]
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
