data "aws_iam_policy_document" "app_read_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = [
      for k, _ in var.secrets_list :
      aws_secretsmanager_secret.secret[k].arn
    ]
    condition {
      test     = "StringEquals"
      variable = "aws:ResourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_policy" "app_read_secrets" {
  name        = "${var.project}-${var.env}-app-read-secrets"
  description = "Policy for application to read secrets"
  policy      = data.aws_iam_policy_document.app_read_secrets.json
}

# CI/CD role for secret rotation
data "aws_iam_policy_document" "ci_rotate_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:PutSecretValue",
      "secretsmanager:UpdateSecretVersionStage",
      "secretsmanager:ListSecrets"
    ]
    resources = [
      for k, _ in var.secrets_list :
      aws_secretsmanager_secret.secret[k].arn
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.rotate_generic.arn
    ]
  }
}

resource "aws_iam_policy" "ci_rotate_secrets" {
  name        = "${var.project}-${var.env}-ci-rotate-secrets"
  description = "Policy for CI/CD to rotate secrets"
  policy      = data.aws_iam_policy_document.ci_rotate_secrets.json
}
