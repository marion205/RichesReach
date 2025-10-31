# CloudFront Distribution with GraphQL APQ Caching
# Automatic Persisted Queries (APQ) for GraphQL performance

resource "aws_cloudfront_cache_policy" "graphql_apq" {
  name        = "richesreach-graphql-apq"
  comment     = "GraphQL APQ caching policy with query hashing"
  default_ttl = 60
  max_ttl     = 300
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip    = true

    query_strings_config {
      query_string_behavior = "whitelist"
      # APQ uses SHA256 hash in extensions parameter
      query_strings = [
        "extensions",
        "operationName",
        "variables"  # Keep if needed, but can hash/order for better caching
      ]
    }

    headers_config {
      header_behavior = "whitelist"
      # Forward Authorization only if origin requires it
      headers = ["Authorization"]
    }

    cookies_config {
      cookie_behavior = "none"
    }
  }
}

resource "aws_cloudfront_response_headers_policy" "graphql_security" {
  name = "richesreach-graphql-security-headers"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains          = true
      preload                     = true
    }
    content_type_options {
      override = true
    }
    frame_options {
      frame_option = "DENY"
      override     = true
    }
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
  }

  custom_headers_config {
    items {
      header   = "X-Cache-Status"
      value    = "%{CloudFront-Cache-Status}"
      override = false
    }
  }
}

resource "aws_cloudfront_distribution" "api" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "RichesReach API with GraphQL APQ"
  default_root_object = ""
  price_class         = "PriceClass_100"  # Use only North America and Europe

  origin {
    domain_name = var.api_alb_dns_name
    origin_id   = "api-origin"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "https-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_read_timeout      = 60
      origin_keepalive_timeout  = 5
    }

    custom_header {
      name  = "X-Forwarded-Host"
      value = var.api_domain_name
    }
  }

  # GraphQL endpoint with APQ caching
  default_cache_behavior {
    target_origin_id       = "api-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]

    cache_policy_id            = aws_cloudfront_cache_policy.graphql_apq.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.graphql_security.id
    compress                   = true

    # Forward query string for APQ
    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
      headers = ["Authorization", "Content-Type"]
    }
  }

  # Static assets caching
  ordered_cache_behavior {
    path_pattern           = "/static/*"
    target_origin_id       = "static-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Environment = var.environment
    Service     = "api"
  }
}

# GraphQL APQ Storage (optional - can use Redis instead)
resource "aws_s3_bucket" "apq_cache" {
  bucket = "${var.project_name}-apq-cache-${var.environment}"
}

resource "aws_s3_bucket_versioning" "apq_cache" {
  bucket = aws_s3_bucket.apq_cache.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Variables
variable "api_alb_dns_name" {
  description = "DNS name of the API Application Load Balancer"
  type        = string
}

variable "api_domain_name" {
  description = "Domain name for the API"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "richesreach"
}

variable "static_origin_domain" {
  description = "Domain for static assets (S3 bucket)"
  type        = string
  default     = ""
}

