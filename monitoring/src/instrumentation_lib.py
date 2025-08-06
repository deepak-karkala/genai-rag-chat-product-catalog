import logging
import json
import os
import boto3
from uuid import uuid4

# Use a custom JSON formatter for structured logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", "N/A"),
            "service": "RAGInferenceService"
        }
        # Add exception info if it exists
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def configure_logging():
    """Configures root logger for structured JSON logging."""
    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

def get_trace_id() -> str:
    """Generates a unique trace ID."""
    return str(uuid4())

def emit_cloudwatch_metric(metric_name: str, value: float, unit: str = 'Milliseconds'):
    """Emits a custom metric to CloudWatch."""
    try:
        cloudwatch = boto3.client('cloudwatch')
        cloudwatch.put_metric_data(
            Namespace='RAGApplication',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Dimensions': [
                        {
                            'Name': 'Service',
                            'Value': 'RAGInferenceService'
                        }
                    ]
                },
            ]
        )
    except Exception as e:
        # Log error but don't fail the main application path
        logging.error(f"Failed to emit CloudWatch metric '{metric_name}': {e}")