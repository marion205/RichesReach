# ECS Cluster Module for Multi-Region Deployment

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = var.tags
}

# ECS Cluster Capacity Providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${var.cluster_name}"
  retention_in_days = 30
  
  tags = var.tags
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.cluster_name}-task-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.cluster_name}-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# IAM Policy for ECS Task Role
resource "aws_iam_policy" "ecs_task_policy" {
  name        = "${var.cluster_name}-task-policy"
  description = "Policy for ECS task role"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.ecs_task_policy.arn
}

# Auto Scaling Group for ECS (if using EC2 launch type)
resource "aws_launch_template" "ecs" {
  name_prefix   = "${var.cluster_name}-"
  image_id      = data.aws_ami.ecs_optimized.id
  instance_type = "t3.medium"
  
  vpc_security_group_ids = [var.security_group_ids[0]]
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    cluster_name = var.cluster_name
  }))
  
  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, {
      Name = "${var.cluster_name}-instance"
    })
  }
  
  tags = var.tags
}

data "aws_ami" "ecs_optimized" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-ecs-hvm-*-x86_64-ebs"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Application Load Balancer Target Group
resource "aws_lb_target_group" "main" {
  name        = "${var.cluster_name}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = var.tags
}

# ECS Service
resource "aws_ecs_service" "main" {
  name            = "${var.cluster_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    security_groups  = var.security_group_ids
    subnets          = var.subnet_ids
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "richesreach-backend"
    container_port   = 8000
  }
  
  depends_on = [aws_lb_listener.main]
  
  tags = var.tags
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = "${var.cluster_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn
  
  container_definitions = jsonencode([
    {
      name  = "richesreach-backend"
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/richesreach:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      
      essential = true
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = "production"
        },
        {
          name  = "PHASE3_ENABLED"
          value = "true"
        }
      ]
      
      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:richesreach/database-url"
        },
        {
          name      = "REDIS_URL"
          valueFrom = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:richesreach/redis-url"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.main.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
  
  tags = var.tags
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.cluster_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids
  
  enable_deletion_protection = false
  
  tags = var.tags
}

# ALB Listener
resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# ALB Listener for HTTPS (if certificate is provided)
resource "aws_lb_listener" "https" {
  count = var.certificate_arn != null ? 1 : 0
  
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}
