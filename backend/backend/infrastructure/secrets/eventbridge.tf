resource "aws_cloudwatch_event_rule" "rotate_monthly" {
  name                = "${var.project}-${var.env}-rotate-monthly"
  description         = "Trigger monthly secret rotation check"
  schedule_expression = "rate(30 days)"
  
  tags = {
    Environment = var.env
    Project     = var.project
  }
}

resource "aws_cloudwatch_event_target" "rotate_generic_monthly" {
  rule      = aws_cloudwatch_event_rule.rotate_monthly.name
  target_id = "rotate-generic"
  arn       = aws_lambda_function.rotate_generic.arn
  
  input = jsonencode({
    SecretId       = "arn:aws:secretsmanager:us-east-1:${data.aws_caller_identity.current.account_id}:secret:${var.project}/${var.env}/openai_api_key"
    CandidateValue = "PLACEHOLDER_FROM_CI"
    Action         = "check_rotation_status"
  })
}

resource "aws_lambda_permission" "allow_events" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rotate_generic.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rotate_monthly.arn
}
