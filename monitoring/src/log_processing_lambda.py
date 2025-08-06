import json
import base64
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Processes logs from Kinesis Firehose, enriches them,
    and returns them for storage in S3.
    """
    output_records = []

    for record in event['records']:
        try:
            # Decode the payload from Firehose
            payload_decoded = base64.b64decode(record['data']).decode('utf-8')
            log_data = json.loads(payload_decoded)

            # 1. PARSE: The data is already structured JSON.
            # 2. ENRICH: Add additional metadata.
            #    (e.g., lookup user details from a DB using log_data['user_id'])
            log_data['processed_by'] = context.function_name
            
            # 3. AGGREGATE/ANALYZE (Example):
            # In a more complex scenario, you could send a sample of responses
            # to another service (e.g., an LLM-as-a-judge) here to calculate a
            # groundedness score before archiving.
            
            processed_payload = json.dumps(log_data).encode('utf-8')
            
            output_records.append({
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(processed_payload).decode('utf-8')
            })

        except Exception as e:
            logger.error(f"Failed to process record {record['recordId']}: {e}")
            output_records.append({
                'recordId': record['recordId'],
                'result': 'ProcessingFailed',
                'data': record['data'] # Return original data on failure
            })

    return {'records': output_records}