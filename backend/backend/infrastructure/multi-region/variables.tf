# Multi-Region Infrastructure Variables

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "api.richesreach.com"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate"
  type        = string
  default     = null
}

variable "enable_cloudfront" {
  description = "Enable CloudFront distribution"
  type        = bool
  default     = true
}

variable "enable_multi_region" {
  description = "Enable multi-region deployment"
  type        = bool
  default     = true
}

variable "enable_redis_cluster" {
  description = "Enable Redis cluster"
  type        = bool
  default     = true
}

variable "enable_rds_cluster" {
  description = "Enable RDS cluster"
  type        = bool
  default     = true
}
