locals {
  name_prefix = "${var.project}/${var.env}"
}

# Create secrets in primary region (us-east-1)
resource "aws_secretsmanager_secret" "secret" {
  for_each                = var.secrets_list
  name                    = "${local.name_prefix}/${each.key}"
  kms_key_id              = aws_kms_key.secrets_mrk.arn
  recovery_window_in_days = 7
  description             = each.value
  
  tags = {
    Environment = var.env
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

# Initial placeholder values - CI will populate
resource "aws_secretsmanager_secret_version" "secret_init" {
  for_each      = var.secrets_list
  secret_id     = aws_secretsmanager_secret.secret[each.key].id
  secret_string = jsonencode({
    value = "REPLACE_ME_VIA_CI"
    metadata = {
      source     = "bootstrap"
      created_at = timestamp()
      rotated_by = "terraform"
    }
  })
}
