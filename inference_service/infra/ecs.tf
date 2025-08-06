# Defines the AWS Fargate service for our FastAPI application

resource "aws_ecs_cluster" "main" {
  name = "rag-inference-cluster-${var.env}"
}

resource "aws_ecs_task_definition" "api" {
  family                   = "rag-api-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024 # 1 vCPU
  memory                   = 2048 # 2 GB

  # ... (container definition pointing to the ECR image, port mappings, etc.) ...
  
  # IAM role for the task to access Bedrock, SageMaker, OpenSearch
  task_role_arn            = aws_iam_role.inference_task_role.arn
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
}

resource "aws_ecs_service" "main" {
  name            = "rag-inference-service-${var.env}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2 # Start with 2 tasks for high availability
  launch_type     = "FARGATE"
  
  # ... (network configuration, load balancer attachment) ...
}

# ... (Autoscaling configuration based on CPU or request count) ...