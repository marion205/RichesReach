data "aws_caller_identity" "current" {}

resource "aws_kms_key" "secrets_mrk" {
  description         = "${var.project}-${var.env}-secrets-mrk"
  enable_key_rotation = true
  multi_region        = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Secrets Manager"
        Effect = "Allow"
        Principal = {
          Service = "secretsmanager.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "secrets_mrk_alias" {
  name          = "alias/${var.project}-${var.env}-secrets"
  target_key_id = aws_kms_key.secrets_mrk.key_id
}
