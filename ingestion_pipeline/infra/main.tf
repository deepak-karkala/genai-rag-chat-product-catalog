# main.tf - Defines the core infrastructure for the ingestion pipeline

# Variable for environment (e.g., "staging", "prod")
variable "env" {
  type    = string
  default = "staging"
}

# --- S3 Buckets ---
resource "aws_s3_bucket" "raw_data" {
  bucket = "rag-product-data-raw-${var.env}"
}

resource "aws_s3_bucket" "processed_data" {
  bucket = "rag-product-data-processed-${var.env}"
}

# --- IAM Roles ---
# A comprehensive IAM role for the Lambda functions and Step Function
# In a real setup, you would create separate, least-privilege roles for each component.
resource "aws_iam_role" "ingestion_pipeline_role" {
  name = "IngestionPipelineRole-${var.env}"
  # Assume role policy allows lambda and states services
  assume_role_policy = "..." # Placeholder for IAM trust policy JSON
}
# ... Attach policies for S3, Bedrock, OpenSearch, CloudWatch ...

# --- Lambda Functions ---
# Placeholder for one of the Lambda functions
resource "aws_lambda_function" "load_data_lambda" {
  function_name = "LoadDataLambda-${var.env}"
  role          = aws_iam_role.ingestion_pipeline_role.arn
  handler       = "data_loader.handler"
  runtime       = "python3.11"
  # ... code packaging configuration ...
}

# ... Define other Lambda functions for each step ...

# --- Step Functions State Machine ---
resource "aws_sfn_state_machine" "ingestion_sfn" {
  name     = "RAG-Ingestion-Pipeline-${var.env}"
  role_arn = aws_iam_role.ingestion_pipeline_role.arn

  definition = templatefile("${path.module}/../statemachine/ingestion_statemachine.asl.json", {
    LoadDataLambdaArn = aws_lambda_function.load_data_lambda.arn,
    # ... pass other Lambda ARNs and SNS Topic ARN ...
  })
}

# --- OpenSearch Serverless ---
resource "aws_opensearchserverless_collection" "vector_db" {
  name = "rag-vector-db-${var.env}"
  type = "VECTORSEARCH"
}

# --- EventBridge Scheduler for Batch ---
resource "aws_cloudwatch_event_rule" "nightly_trigger" {
  name                = "NightlyIngestionTrigger-${var.env}"
  schedule_expression = "cron(0 2 * * ? *)" # 2 AM UTC every night
}

resource "aws_cloudwatch_event_target" "step_function_target" {
  rule      = aws_cloudwatch_event_rule.nightly_trigger.name
  arn       = aws_sfn_state_machine.ingestion_sfn.arn
  role_arn  = aws_iam_role.ingestion_pipeline_role.arn # A specific role for EventBridge is better
}