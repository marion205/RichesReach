# CloudFront Module for Phase 3 Multi-Region Infrastructure

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = var.origins["us_east_1"].domain_name
    origin_id   = "us_east_1"
    origin_path = var.origins["us_east_1"].origin_path

    custom_origin_config {
      http_port                = var.origins["us_east_1"].custom_origin_config.http_port
      https_port               = var.origins["us_east_1"].custom_origin_config.https_port
      origin_protocol_policy   = var.origins["us_east_1"].custom_origin_config.origin_protocol_policy
      origin_ssl_protocols     = var.origins["us_east_1"].custom_origin_config.origin_ssl_protocols
      origin_keepalive_timeout = 5
      origin_read_timeout      = 30
    }

    custom_header {
      name  = "X-Region"
      value = "us-east-1"
    }
  }

  origin {
    domain_name = var.origins["eu_west_1"].domain_name
    origin_id   = "eu_west_1"
    origin_path = var.origins["eu_west_1"].origin_path

    custom_origin_config {
      http_port                = var.origins["eu_west_1"].custom_origin_config.http_port
      https_port               = var.origins["eu_west_1"].custom_origin_config.https_port
      origin_protocol_policy   = var.origins["eu_west_1"].custom_origin_config.origin_protocol_policy
      origin_ssl_protocols     = var.origins["eu_west_1"].custom_origin_config.origin_ssl_protocols
      origin_keepalive_timeout = 5
      origin_read_timeout      = 30
    }

    custom_header {
      name  = "X-Region"
      value = "eu-west-1"
    }
  }

  origin {
    domain_name = var.origins["ap_southeast_1"].domain_name
    origin_id   = "ap_southeast_1"
    origin_path = var.origins["ap_southeast_1"].origin_path

    custom_origin_config {
      http_port                = var.origins["ap_southeast_1"].custom_origin_config.http_port
      https_port               = var.origins["ap_southeast_1"].custom_origin_config.https_port
      origin_protocol_policy   = var.origins["ap_southeast_1"].custom_origin_config.origin_protocol_policy
      origin_ssl_protocols     = var.origins["ap_southeast_1"].custom_origin_config.origin_ssl_protocols
      origin_keepalive_timeout = 5
      origin_read_timeout      = 30
    }

    custom_header {
      name  = "X-Region"
      value = "ap-southeast-1"
    }
  }

  enabled             = var.cloudfront_config.enabled
  is_ipv6_enabled     = var.cloudfront_config.is_ipv6_enabled
  comment             = var.cloudfront_config.comment
  default_root_object = var.cloudfront_config.default_root_object
  price_class         = var.cloudfront_config.price_class

  # Default cache behavior
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "us_east_1"

    forwarded_values {
      query_string = true
      headers      = ["Host", "Authorization", "X-Region"]
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
    path_pattern     = var.cache_behaviors["api"].path_pattern
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = var.cache_behaviors["api"].target_origin_id

    forwarded_values {
      query_string = true
      headers      = ["Host", "Authorization", "X-Region", "X-Request-ID"]
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
  }

  # AI API cache behavior
  ordered_cache_behavior {
    path_pattern     = var.cache_behaviors["ai"].path_pattern
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = var.cache_behaviors["ai"].target_origin_id

    forwarded_values {
      query_string = true
      headers      = ["Host", "Authorization", "X-Region", "X-Request-ID"]
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
  }

  # Static assets cache behavior
  ordered_cache_behavior {
    path_pattern     = var.cache_behaviors["static"].path_pattern
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = var.cache_behaviors["static"].target_origin_id

    forwarded_values {
      query_string = false
      headers      = ["Origin"]
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

  # Lambda@Edge functions
  dynamic "lambda_function_association" {
    for_each = var.lambda_edge_functions
    content {
      event_type   = lambda_function_association.value.event_type
      lambda_arn   = lambda_function_association.value.lambda_arn
      include_body = lambda_function_association.value.include_body
    }
  }

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Viewer certificate
  viewer_certificate {
    cloudfront_default_certificate = true
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

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "${var.distribution_name}-oac"
  description                       = "OAC for ${var.distribution_name}"
  origin_access_control_origin_type = "custom"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Cache Policy for API
resource "aws_cloudfront_cache_policy" "api" {
  name        = "${var.distribution_name}-api-cache-policy"
  comment     = "Cache policy for API endpoints"
  default_ttl = 0
  max_ttl     = 0
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true

    query_strings_config {
      query_string_behavior = "all"
    }

    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Host", "Authorization", "X-Region", "X-Request-ID"]
      }
    }

    cookies_config {
      cookie_behavior = "none"
    }
  }
}

# CloudFront Cache Policy for Static Assets
resource "aws_cloudfront_cache_policy" "static" {
  name        = "${var.distribution_name}-static-cache-policy"
  comment     = "Cache policy for static assets"
  default_ttl = 86400
  max_ttl     = 31536000
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true

    query_strings_config {
      query_string_behavior = "none"
    }

    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Origin"]
      }
    }

    cookies_config {
      cookie_behavior = "none"
    }
  }
}

# CloudFront Origin Request Policy for API
resource "aws_cloudfront_origin_request_policy" "api" {
  name    = "${var.distribution_name}-api-origin-request-policy"
  comment = "Origin request policy for API endpoints"

  query_strings_config {
    query_string_behavior = "all"
  }

  headers_config {
    header_behavior = "whitelist"
    headers {
      items = ["Host", "Authorization", "X-Region", "X-Request-ID"]
    }
  }

  cookies_config {
    cookie_behavior = "none"
  }
}

# CloudFront Response Headers Policy
resource "aws_cloudfront_response_headers_policy" "security" {
  name    = "${var.distribution_name}-security-headers"
  comment = "Security headers policy"

  security_headers_config {
    content_type_options {
      override = false
    }
    frame_options {
      frame_option = "DENY"
      override     = false
    }
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = false
    }
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = false
    }
  }

  custom_headers_config {
    items {
      header   = "X-Content-Type-Options"
      value    = "nosniff"
      override = false
    }
    items {
      header   = "X-Frame-Options"
      value    = "DENY"
      override = false
    }
    items {
      header   = "X-XSS-Protection"
      value    = "1; mode=block"
      override = false
    }
  }
}

# CloudFront Function for request routing
resource "aws_cloudfront_function" "request_router" {
  name    = "${var.distribution_name}-request-router"
  runtime = "cloudfront-js-1.0"
  comment = "Request router for geographic distribution"
  publish = true
  code    = file("${path.module}/request-router.js")
}

# CloudFront Function association
resource "aws_cloudfront_distribution" "main" {
  # ... existing configuration ...

  # Associate the function with the distribution
  default_cache_behavior {
    # ... existing configuration ...
    
    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.request_router.arn
    }
  }
}
