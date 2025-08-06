import boto3
import requests
import time
import pytest
import os
import gzip

API_ENDPOINT = os.environ["STAGING_API_ENDPOINT"]
LOG_ARCHIVE_BUCKET = os.environ["STAGING_LOG_BUCKET"]

@pytest.mark.integration
def test_end_to_end_logging_flow():
    s3_client = boto3.client("s3")
    
    # 1. ARRANGE: Generate a unique ID to find in the logs
    unique_id = f"integration-test-{int(time.time())}"
    
    # 2. ACT: Make a request to the service that will generate a log
    requests.post(f"{API_ENDPOINT}/search", json={"query": unique_id})
    
    # 3. ASSERT: Poll the S3 bucket until the log file appears
    found_log = False
    for _ in range(12): # Poll for up to 1 minute
        time.sleep(5)
        # Construct prefix based on Firehose date partitioning
        prefix = f"{time.strftime('%Y/%m/%d/%H')}/"
        response = s3_client.list_objects_v2(Bucket=LOG_ARCHIVE_BUCKET, Prefix=prefix)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                log_obj = s3_client.get_object(Bucket=LOG_ARCHIVE_BUCKET, Key=obj['Key'])
                log_content = gzip.decompress(log_obj['Body'].read()).decode('utf-8')
                
                if unique_id in log_content:
                    found_log = True
                    # Check if the log was enriched by our Lambda
                    assert 'processed_by' in log_content
                    break
        if found_log:
            break
            
    assert found_log, "Log file with unique ID was not found in S3 within 60 seconds."