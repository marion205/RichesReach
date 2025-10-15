# Phase 3 Variables

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "app.richesreach.net"
}

variable "ai_models" {
  description = "AI models configuration"
  type = object({
    openai_api_key = string
    anthropic_api_key = string
    google_api_key = string
    default_model = string
    max_tokens = number
    temperature = number
  })
  default = {
    openai_api_key = ""
    anthropic_api_key = ""
    google_api_key = ""
    default_model = "gpt-4o-mini"
    max_tokens = 4000
    temperature = 0.7
  }
}

variable "database_config" {
  description = "Database configuration"
  type = object({
    instance_class = string
    engine_version = string
    backup_retention_period = number
    preferred_backup_window = string
    preferred_maintenance_window = string
    auto_minor_version_upgrade = bool
    deletion_protection = bool
  })
  default = {
    instance_class = "db.r6g.large"
    engine_version = "15.4"
    backup_retention_period = 7
    preferred_backup_window = "03:00-04:00"
    preferred_maintenance_window = "sun:04:00-sun:05:00"
    auto_minor_version_upgrade = true
    deletion_protection = true
  }
}

variable "redis_config" {
  description = "Redis configuration"
  type = object({
    node_type = string
    num_cache_clusters = number
    parameter_group_name = string
    engine_version = string
  })
  default = {
    node_type = "cache.t3.medium"
    num_cache_clusters = 3
    parameter_group_name = "default.redis7"
    engine_version = "7.0"
  }
}

variable "ecs_config" {
  description = "ECS configuration"
  type = object({
    cpu = number
    memory = number
    desired_count = number
    min_capacity = number
    max_capacity = number
    target_cpu_utilization = number
    target_memory_utilization = number
  })
  default = {
    cpu = 1024
    memory = 2048
    desired_count = 3
    min_capacity = 2
    max_capacity = 10
    target_cpu_utilization = 70
    target_memory_utilization = 80
  }
}

variable "cloudfront_config" {
  description = "CloudFront configuration"
  type = object({
    price_class = string
    default_root_object = string
    enabled = bool
    is_ipv6_enabled = bool
    comment = string
  })
  default = {
    price_class = "PriceClass_100"
    default_root_object = "index.html"
    enabled = true
    is_ipv6_enabled = true
    comment = "RichesReach Phase 3 CloudFront Distribution"
  }
}

variable "security_config" {
  description = "Security configuration"
  type = object({
    enable_guardduty = bool
    enable_security_hub = bool
    enable_config = bool
    enable_cloudtrail = bool
    enable_waf = bool
  })
  default = {
    enable_guardduty = true
    enable_security_hub = true
    enable_config = true
    enable_cloudtrail = true
    enable_waf = true
  }
}

variable "monitoring_config" {
  description = "Monitoring configuration"
  type = object({
    enable_cloudwatch = bool
    enable_xray = bool
    enable_prometheus = bool
    log_retention_days = number
    metrics_retention_days = number
  })
  default = {
    enable_cloudwatch = true
    enable_xray = true
    enable_prometheus = true
    log_retention_days = 30
    metrics_retention_days = 14
  }
}

variable "backup_config" {
  description = "Backup configuration"
  type = object({
    enable_automated_backups = bool
    backup_retention_days = number
    cross_region_backup = bool
    point_in_time_recovery = bool
  })
  default = {
    enable_automated_backups = true
    backup_retention_days = 30
    cross_region_backup = true
    point_in_time_recovery = true
  }
}

variable "cost_optimization" {
  description = "Cost optimization settings"
  type = object({
    use_spot_instances = bool
    enable_auto_scaling = bool
    use_reserved_instances = bool
    enable_savings_plans = bool
  })
  default = {
    use_spot_instances = true
    enable_auto_scaling = true
    use_reserved_instances = false
    enable_savings_plans = false
  }
}

variable "compliance_config" {
  description = "Compliance configuration"
  type = object({
    enable_gdpr_compliance = bool
    enable_soc2_compliance = bool
    enable_hipaa_compliance = bool
    data_retention_days = number
    audit_logging = bool
  })
  default = {
    enable_gdpr_compliance = true
    enable_soc2_compliance = true
    enable_hipaa_compliance = false
    data_retention_days = 2555  # 7 years
    audit_logging = true
  }
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Regional specific variables
variable "us_east_1_config" {
  description = "US East 1 specific configuration"
  type = object({
    primary_region = bool
    min_capacity = number
    max_capacity = number
    desired_capacity = number
  })
  default = {
    primary_region = true
    min_capacity = 2
    max_capacity = 10
    desired_capacity = 3
  }
}

variable "eu_west_1_config" {
  description = "EU West 1 specific configuration"
  type = object({
    primary_region = bool
    min_capacity = number
    max_capacity = number
    desired_capacity = number
  })
  default = {
    primary_region = false
    min_capacity = 1
    max_capacity = 8
    desired_capacity = 2
  }
}

variable "ap_southeast_1_config" {
  description = "AP Southeast 1 specific configuration"
  type = object({
    primary_region = bool
    min_capacity = number
    max_capacity = number
    desired_capacity = number
  })
  default = {
    primary_region = false
    min_capacity = 1
    max_capacity = 6
    desired_capacity = 2
  }
}
