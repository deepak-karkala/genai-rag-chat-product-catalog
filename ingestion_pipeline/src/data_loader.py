import boto3
import json
import logging

logger = logging.getLogger(__name__)

def load_product_data(bucket: str, key: str) -> dict:
    """Loads a single product's JSON data from S3."""
    try:
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error loading data from s3://{bucket}/{key}: {e}")
        raise

# In a real scenario, this would list all new/updated product files.
# For the Step Function, the input `key` will be provided in the event payload.