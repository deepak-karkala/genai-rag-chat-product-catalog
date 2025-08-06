import base64
import json
from src import log_processing_lambda

def test_lambda_handler_processes_records():
    """Tests that the Lambda handler correctly processes a Kinesis Firehose event."""
    # ARRANGE: Create a sample Kinesis Firehose event
    log_event = {
        "timestamp": "2025-08-08T10:00:00Z",
        "level": "INFO",
        "message": "Search successful",
        "trace_id": "123-abc"
    }
    event_data = base64.b64encode(json.dumps(log_event).encode('utf-8')).decode('utf-8')
    
    kinesis_event = {
        'records': [{
            'recordId': '4964251234',
            'data': event_data
        }]
    }

    # ACT: Call the handler
    result = log_processing_lambda.handler(kinesis_event, {})

    # ASSERT: Check the result structure and content
    assert len(result['records']) == 1
    record = result['records'][0]
    assert record['result'] == 'Ok'
    
    # Decode the processed data to verify enrichment
    processed_data_decoded = base64.b64decode(record['data']).decode('utf-8')
    processed_data_json = json.loads(processed_data_decoded)
    
    assert processed_data_json['trace_id'] == "123-abc"
    assert 'processed_by' in processed_data_json