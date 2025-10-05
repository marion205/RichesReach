output "kms_key_arn" {
  description = "KMS key ARN for secrets encryption"
  value       = aws_kms_key.secrets_mrk.arn
}

output "kms_key_alias" {
  description = "KMS key alias"
  value       = aws_kms_alias.secrets_mrk_alias.name
}

output "secret_arns" {
  description = "Map of secret names to ARNs"
  value = {
    for k, v in aws_secretsmanager_secret.secret : k => v.arn
  }
}

output "rotation_lambda_arn" {
  description = "Rotation Lambda function ARN"
  value       = aws_lambda_function.rotate_generic.arn
}

output "app_read_secrets_policy_arn" {
  description = "IAM policy ARN for application secret access"
  value       = aws_iam_policy.app_read_secrets.arn
}

output "ci_rotate_secrets_policy_arn" {
  description = "IAM policy ARN for CI/CD secret rotation"
  value       = aws_iam_policy.ci_rotate_secrets.arn
}
