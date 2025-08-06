import boto3
import time
import pytest
import os

# Assume env variables are set for staging resources (e.g., STATE_MACHINE_ARN)
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]
RAW_BUCKET = os.environ["RAW_BUCKET"]
OS_HOST = os.environ["OS_HOST"]

@pytest.mark.integration
def test_full_pipeline_run():
    s3_client = boto3.client("s3")
    sfn_client = boto3.client("stepfunctions")
    
    # 1. ARRANGE: Upload a sample product file to the raw S3 bucket
    product_id = "test-product-123"
    s3_key = f"products/{product_id}.json"
    sample_data = {"product_id": product_id, "description": "This is a test."}
    s3_client.put_object(Bucket=RAW_BUCKET, Key=s3_key, Body=json.dumps(sample_data))

    # 2. ACT: Trigger the Step Function and wait for completion
    response = sfn_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input=json.dumps({"bucket": RAW_BUCKET, "key": s3_key})
    )
    execution_arn = response['executionArn']
    
    while True:
        status_response = sfn_client.describe_execution(executionArn=execution_arn)
        status = status_response['status']
        if status in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
            break
        time.sleep(5)
    
    # 3. ASSERT
    assert status == 'SUCCEEDED'
    
    # Assert that the data was indexed correctly in OpenSearch
    # In a real test, you'd use the opensearch_indexer client to query the index
    # os_client = opensearch_indexer.get_opensearch_client(...)
    # indexed_doc = os_client.get(index=..., id=...)
    # assert indexed_doc['found'] == True
    
    # 4. CLEANUP (Optional but recommended)
    s3_client.delete_object(Bucket=RAW_BUCKET, Key=s3_key)
    # os_client.delete(index=..., id=...)