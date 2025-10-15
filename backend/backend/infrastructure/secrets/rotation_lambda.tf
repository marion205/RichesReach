# Generic rotation Lambda for vendor APIs
data "archive_file" "rotate_generic_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/rotate_generic"
  output_path = "${path.module}/.build/rotate_generic.zip"
}

resource "aws_iam_role" "rotate_generic_role" {
  name = "${var.project}-${var.env}-rotate-generic"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "rotate_generic_policy" {
  name = "${var.project}-${var.env}-rotate-generic"
  role = aws_iam_role.rotate_generic_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = [
          for k, _ in var.secrets_list :
          aws_secretsmanager_secret.secret[k].arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "rotate_generic" {
  function_name = "${var.project}-${var.env}-rotate-generic"
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.rotate_generic_role.arn
  filename      = data.archive_file.rotate_generic_zip.output_path
  timeout       = 60
  
  environment {
    variables = {
      HEALTHCHECK_URL = "https://api.richesreach.net/health/ready"
      PROJECT         = var.project
      ENV             = var.env
    }
  }
  
  tags = {
    Environment = var.env
    Project     = var.project
  }
}

# Enable rotation for all secrets
resource "aws_secretsmanager_secret_rotation" "generic_rotation" {
  for_each               = var.secrets_list
  secret_id              = aws_secretsmanager_secret.secret[each.key].id
  rotation_lambda_arn    = aws_lambda_function.rotate_generic.arn
  
  rotation_rules {
    automatically_after_days = 30
  }
}
