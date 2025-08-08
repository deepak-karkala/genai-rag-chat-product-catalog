# Defines the SageMaker Model Group for versioning our fine-tuned models

resource "aws_sagemaker_model_package_group" "embedding_models" {
  model_package_group_name        = "rag-embedding-models-${var.env}"
  model_package_group_description = "All versions of the fine-tuned RAG embedding model."
}

# IAM role for the SageMaker training jobs
resource "aws_iam_role" "sagemaker_training_role" {
  name = "SageMakerTrainingRole-${var.env}"
  assume_role_policy = # ... (trust policy for sagemaker.amazonaws.com) ...
}

# Attach policies granting access to S3 data buckets and ECR
resource "aws_iam_role_policy_attachment" "s3_access" {
  role       = aws_iam_role.sagemaker_training_role.name
  policy_arn = # ... (ARN of a policy allowing read from data bucket, write to artifact bucket) ...
}