# CloudFront Module for Multi-Region Deployment

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "${var.domain_name}-oac"
  description                       = "OAC for ${var.domain_name}"
  origin_access_control_origin_type = "loadbalancer"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name              = var.origin_domain
    origin_id                = "primary-origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  
  # Additional origins for failover
  dynamic "origin" {
    for_each = var.additional_origins
    content {
      domain_name              = origin.value.domain_name
      origin_id                = origin.key
      origin_access_control_id = aws_cloudfront_origin_access_control.main.id
      
      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CloudFront distribution for ${var.domain_name}"
  default_root_object = "index.html"
  
  aliases = [var.domain_name]
  
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "primary-origin"
    
    forwarded_values {
      query_string = true
      headers      = ["Host", "Authorization", "CloudFront-Forwarded-Proto"]
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }
  
  # API cache behavior
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "primary-origin"
    
    forwarded_values {
      query_string = true
      headers      = ["Host", "Authorization", "CloudFront-Forwarded-Proto"]
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 300
    max_ttl                = 3600
    compress               = true
  }
  
  # Static assets cache behavior
  ordered_cache_behavior {
    path_pattern     = "/static/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "primary-origin"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
  }
  
  # GraphQL cache behavior
  ordered_cache_behavior {
    path_pattern     = "/graphql"
    allowed_methods  = ["POST", "OPTIONS"]
    cached_methods   = ["POST"]
    target_origin_id = "primary-origin"
    
    forwarded_values {
      query_string = true
      headers      = ["Host", "Authorization", "CloudFront-Forwarded-Proto"]
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
  }
  
  # Price class
  price_class = "PriceClass_All"
  
  # Restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  # Viewer certificate
  viewer_certificate {
    acm_certificate_arn      = var.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
  
  # Custom error pages
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }
  
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  
  tags = var.tags
}

# CloudFront Function for request optimization
resource "aws_cloudfront_function" "request_optimizer" {
  name    = "${var.domain_name}-request-optimizer"
  runtime = "cloudfront-js-1.0"
  comment = "Request optimization function"
  publish = true
  code    = file("${path.module}/request-optimizer.js")
}

# CloudFront Function for response optimization
resource "aws_cloudfront_function" "response_optimizer" {
  name    = "${var.domain_name}-response-optimizer"
  runtime = "cloudfront-js-1.0"
  comment = "Response optimization function"
  publish = true
  code    = file("${path.module}/response-optimizer.js")
}

# Lambda@Edge function for advanced processing
resource "aws_lambda_function" "edge_processor" {
  provider = aws.us_east_1
  
  filename         = "${path.module}/edge-processor.zip"
  function_name    = "${var.domain_name}-edge-processor"
  role            = aws_iam_role.lambda_edge_role.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.edge_processor_zip.output_base64sha256
  runtime         = "nodejs18.x"
  publish         = true
  
  tags = var.tags
}

# IAM role for Lambda@Edge
resource "aws_iam_role" "lambda_edge_role" {
  provider = aws.us_east_1
  
  name = "${var.domain_name}-lambda-edge-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "edgelambda.amazonaws.com"
          ]
        }
      }
    ]
  })
  
  tags = var.tags
}

# IAM policy for Lambda@Edge
resource "aws_iam_role_policy" "lambda_edge_policy" {
  provider = aws.us_east_1
  
  name = "${var.domain_name}-lambda-edge-policy"
  role = aws_iam_role.lambda_edge_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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

# Archive file for Lambda@Edge
data "archive_file" "edge_processor_zip" {
  type        = "zip"
  source_file = "${path.module}/edge-processor.js"
  output_path = "${path.module}/edge-processor.zip"
}

# CloudWatch Log Group for Lambda@Edge
resource "aws_cloudwatch_log_group" "lambda_edge" {
  provider = aws.us_east_1
  
  name              = "/aws/lambda/${aws_lambda_function.edge_processor.function_name}"
  retention_in_days = 14
  
  tags = var.tags
}
