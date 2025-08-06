# main.tf - Defines the infrastructure for the observability pipeline

# --- CloudWatch Resources ---
resource "aws_cloudwatch_log_group" "inference_service_logs" {
  name              = "/aws/ecs/rag-inference-service-${var.env}"
  retention_in_days = 30
}

resource "aws_cloudwatch_dashboard" "rag_dashboard" {
  dashboard_name = "RAG-Observability-Dashboard-${var.env}"
  dashboard_body = jsonencode({
    # ... (Dashboard widget definitions for Latency, Cost, RAG Quality metrics) ...
  })
}

resource "aws_cloudwatch_metric_alarm" "p99_latency_alarm" {
  alarm_name          = "High-P99-Latency-Alarm-${var.env}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "p99_latency" # Custom metric emitted by the app
  namespace           = "RAGApplication"
  period              = "60"
  statistic           = "Average"
  threshold           = "1500" # 1.5 seconds
  alarm_description   = "P99 latency for the RAG inference service is too high."
  alarm_actions       = [aws_sns_topic.alarms.arn]
}

# --- Kinesis Firehose for Log Streaming ---
resource "aws_kinesis_firehose_delivery_stream" "log_stream" {
  name        = "rag-log-stream-${var.env}"
  destination = "extended_s3"

  extended_s3_configuration {
    bucket_arn        = aws_s3_bucket.log_archive.arn
    role_arn          = aws_iam_role.firehose_role.arn
    
    # Route logs through our Lambda for processing
    processing_configuration {
      enabled = "true"
      processors {
        type = "Lambda"
        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = aws_lambda_function.log_processor.arn
        }
      }
    }
  }
}

# Subscription to send logs from CloudWatch to Kinesis
resource "aws_cloudwatch_log_subscription_filter" "log_subscription" {
  name            = "KinesisSubscriptionFilter-${var.env}"
  log_group_name  = aws_cloudwatch_log_group.inference_service_logs.name
  filter_pattern  = "" # Send all logs
  destination_arn = aws_kinesis_firehose_delivery_stream.log_stream.arn
  role_arn        = aws_iam_role.cloudwatch_to_firehose_role.arn
}

# --- Supporting Resources (S3, Lambda, IAM, SNS) ---
resource "aws_s3_bucket" "log_archive" {
  bucket = "rag-log-archive-${var.env}"
}

resource "aws_lambda_function" "log_processor" {
  function_name = "LogProcessorLambda-${var.env}"
  # ... (configuration for the log processing lambda) ...
}

resource "aws_sns_topic" "alarms" {
  name = "RAG-Alarms-Topic-${var.env}"
}