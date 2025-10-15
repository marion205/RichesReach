# Multi-Region Infrastructure - Phase 3
# Global deployment with ECS clusters, Route 53, and CloudFront

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider configuration for multiple regions
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
}

provider "aws" {
  alias  = "ap_southeast_1"
  region = "ap-southeast-1"
}

# Local variables
locals {
  project_name = "richesreach"
  environment  = var.environment
  regions = {
    us_east_1     = "us-east-1"
    eu_west_1     = "eu-west-1"
    ap_southeast_1 = "ap-southeast-1"
  }
  
  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
    Phase       = "3"
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# VPC and Networking for each region
module "vpc_us_east_1" {
  source = "./modules/vpc"
  
  providers = {
    aws = aws.us_east_1
  }
  
  region     = local.regions.us_east_1
  cidr_block = "10.0.0.0/16"
  
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  
  tags = local.common_tags
}

module "vpc_eu_west_1" {
  source = "./modules/vpc"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  region     = local.regions.eu_west_1
  cidr_block = "10.1.0.0/16"
  
  availability_zones = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  
  tags = local.common_tags
}

module "vpc_ap_southeast_1" {
  source = "./modules/vpc"
  
  providers = {
    aws = aws.ap_southeast_1
  }
  
  region     = local.regions.ap_southeast_1
  cidr_block = "10.2.0.0/16"
  
  availability_zones = ["ap-southeast-1a", "ap-southeast-1b", "ap-southeast-1c"]
  
  tags = local.common_tags
}

# ECS Clusters for each region
module "ecs_cluster_us_east_1" {
  source = "./modules/ecs-cluster"
  
  providers = {
    aws = aws.us_east_1
  }
  
  cluster_name = "${local.project_name}-${local.environment}-us-east-1"
  vpc_id       = module.vpc_us_east_1.vpc_id
  subnet_ids   = module.vpc_us_east_1.private_subnet_ids
  
  tags = local.common_tags
}

module "ecs_cluster_eu_west_1" {
  source = "./modules/ecs-cluster"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  cluster_name = "${local.project_name}-${local.environment}-eu-west-1"
  vpc_id       = module.vpc_eu_west_1.vpc_id
  subnet_ids   = module.vpc_eu_west_1.private_subnet_ids
  
  tags = local.common_tags
}

module "ecs_cluster_ap_southeast_1" {
  source = "./modules/ecs-cluster"
  
  providers = {
    aws = aws.ap_southeast_1
  }
  
  cluster_name = "${local.project_name}-${local.environment}-ap-southeast-1"
  vpc_id       = module.vpc_ap_southeast_1.vpc_id
  subnet_ids   = module.vpc_ap_southeast_1.private_subnet_ids
  
  tags = local.common_tags
}

# Application Load Balancers for each region
module "alb_us_east_1" {
  source = "./modules/alb"
  
  providers = {
    aws = aws.us_east_1
  }
  
  name               = "${local.project_name}-${local.environment}-us-east-1"
  vpc_id             = module.vpc_us_east_1.vpc_id
  subnet_ids         = module.vpc_us_east_1.public_subnet_ids
  security_group_ids = [module.vpc_us_east_1.alb_security_group_id]
  
  tags = local.common_tags
}

module "alb_eu_west_1" {
  source = "./modules/alb"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  name               = "${local.project_name}-${local.environment}-eu-west-1"
  vpc_id             = module.vpc_eu_west_1.vpc_id
  subnet_ids         = module.vpc_eu_west_1.public_subnet_ids
  security_group_ids = [module.vpc_eu_west_1.alb_security_group_id]
  
  tags = local.common_tags
}

module "alb_ap_southeast_1" {
  source = "./modules/alb"
  
  providers = {
    aws = aws.ap_southeast_1
  }
  
  name               = "${local.project_name}-${local.environment}-ap-southeast-1"
  vpc_id             = module.vpc_ap_southeast_1.vpc_id
  subnet_ids         = module.vpc_ap_southeast_1.public_subnet_ids
  security_group_ids = [module.vpc_ap_southeast_1.alb_security_group_id]
  
  tags = local.common_tags
}

# RDS Multi-AZ clusters for each region
module "rds_us_east_1" {
  source = "./modules/rds"
  
  providers = {
    aws = aws.us_east_1
  }
  
  cluster_identifier = "${local.project_name}-${local.environment}-us-east-1"
  vpc_id             = module.vpc_us_east_1.vpc_id
  subnet_ids         = module.vpc_us_east_1.database_subnet_ids
  security_group_ids = [module.vpc_us_east_1.database_security_group_id]
  
  tags = local.common_tags
}

module "rds_eu_west_1" {
  source = "./modules/rds"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  cluster_identifier = "${local.project_name}-${local.environment}-eu-west-1"
  vpc_id             = module.vpc_eu_west_1.vpc_id
  subnet_ids         = module.vpc_eu_west_1.database_subnet_ids
  security_group_ids = [module.vpc_eu_west_1.database_security_group_id]
  
  tags = local.common_tags
}

module "rds_ap_southeast_1" {
  source = "./modules/rds"
  
  providers = {
    aws = aws.ap_southeast_1
  }
  
  cluster_identifier = "${local.project_name}-${local.environment}-ap-southeast-1"
  vpc_id             = module.vpc_ap_southeast_1.vpc_id
  subnet_ids         = module.vpc_ap_southeast_1.database_subnet_ids
  security_group_ids = [module.vpc_ap_southeast_1.database_security_group_id]
  
  tags = local.common_tags
}

# ElastiCache Redis clusters for each region
module "redis_us_east_1" {
  source = "./modules/redis"
  
  providers = {
    aws = aws.us_east_1
  }
  
  cluster_id         = "${local.project_name}-${local.environment}-us-east-1"
  vpc_id             = module.vpc_us_east_1.vpc_id
  subnet_ids         = module.vpc_us_east_1.private_subnet_ids
  security_group_ids = [module.vpc_us_east_1.redis_security_group_id]
  
  tags = local.common_tags
}

module "redis_eu_west_1" {
  source = "./modules/redis"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  cluster_id         = "${local.project_name}-${local.environment}-eu-west-1"
  vpc_id             = module.vpc_eu_west_1.vpc_id
  subnet_ids         = module.vpc_eu_west_1.private_subnet_ids
  security_group_ids = [module.vpc_eu_west_1.redis_security_group_id]
  
  tags = local.common_tags
}

module "redis_ap_southeast_1" {
  source = "./modules/redis"
  
  providers = {
    aws = aws.ap_southeast_1
  }
  
  cluster_id         = "${local.project_name}-${local.environment}-ap-southeast-1"
  vpc_id             = module.vpc_ap_southeast_1.vpc_id
  subnet_ids         = module.vpc_ap_southeast_1.private_subnet_ids
  security_group_ids = [module.vpc_ap_southeast_1.redis_security_group_id]
  
  tags = local.common_tags
}

# Route 53 Hosted Zone (in us-east-1)
resource "aws_route53_zone" "main" {
  provider = aws.us_east_1
  
  name = var.domain_name
  
  tags = merge(local.common_tags, {
    Name = "${local.project_name}-${local.environment}-hosted-zone"
  })
}

# Route 53 Health Checks for each region
resource "aws_route53_health_check" "us_east_1" {
  provider = aws.us_east_1
  
  fqdn                            = module.alb_us_east_1.dns_name
  port                            = 80
  type                            = "HTTP"
  resource_path                   = "/health"
  failure_threshold               = "3"
  request_interval                = "30"
  cloudwatch_alarm_region         = "us-east-1"
  cloudwatch_alarm_name           = "${local.project_name}-${local.environment}-us-east-1-health"
  
  tags = merge(local.common_tags, {
    Name = "${local.project_name}-${local.environment}-us-east-1-health-check"
  })
}

resource "aws_route53_health_check" "eu_west_1" {
  provider = aws.eu_west_1
  
  fqdn                            = module.alb_eu_west_1.dns_name
  port                            = 80
  type                            = "HTTP"
  resource_path                   = "/health"
  failure_threshold               = "3"
  request_interval                = "30"
  cloudwatch_alarm_region         = "eu-west-1"
  cloudwatch_alarm_name           = "${local.project_name}-${local.environment}-eu-west-1-health"
  
  tags = merge(local.common_tags, {
    Name = "${local.project_name}-${local.environment}-eu-west-1-health-check"
  })
}

resource "aws_route53_health_check" "ap_southeast_1" {
  provider = aws.ap_southeast_1
  
  fqdn                            = module.alb_ap_southeast_1.dns_name
  port                            = 80
  type                            = "HTTP"
  resource_path                   = "/health"
  failure_threshold               = "3"
  request_interval                = "30"
  cloudwatch_alarm_region         = "ap-southeast-1"
  cloudwatch_alarm_name           = "${local.project_name}-${local.environment}-ap-southeast-1-health"
  
  tags = merge(local.common_tags, {
    Name = "${local.project_name}-${local.environment}-ap-southeast-1-health-check"
  })
}

# Route 53 Latency-based routing records
resource "aws_route53_record" "us_east_1" {
  provider = aws.us_east_1
  
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  
  set_identifier = "us-east-1"
  
  latency_routing_policy {
    region = "us-east-1"
  }
  
  alias {
    name                   = module.alb_us_east_1.dns_name
    zone_id                = module.alb_us_east_1.zone_id
    evaluate_target_health = true
  }
  
  health_check_id = aws_route53_health_check.us_east_1.id
}

resource "aws_route53_record" "eu_west_1" {
  provider = aws.eu_west_1
  
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  
  set_identifier = "eu-west-1"
  
  latency_routing_policy {
    region = "eu-west-1"
  }
  
  alias {
    name                   = module.alb_eu_west_1.dns_name
    zone_id                = module.alb_eu_west_1.zone_id
    evaluate_target_health = true
  }
  
  health_check_id = aws_route53_health_check.eu_west_1.id
}

resource "aws_route53_record" "ap_southeast_1" {
  provider = aws.ap_southeast_1
  
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  
  set_identifier = "ap-southeast-1"
  
  latency_routing_policy {
    region = "ap-southeast-1"
  }
  
  alias {
    name                   = module.alb_ap_southeast_1.dns_name
    zone_id                = module.alb_ap_southeast_1.zone_id
    evaluate_target_health = true
  }
  
  health_check_id = aws_route53_health_check.ap_southeast_1.id
}

# CloudFront Distribution
module "cloudfront" {
  source = "./modules/cloudfront"
  
  providers = {
    aws = aws.us_east_1
  }
  
  domain_name = var.domain_name
  origin_domain = module.alb_us_east_1.dns_name
  
  # Additional origins for failover
  additional_origins = {
    eu-west-1 = {
      domain_name = module.alb_eu_west_1.dns_name
      origin_path = ""
    }
    ap-southeast-1 = {
      domain_name = module.alb_ap_southeast_1.dns_name
      origin_path = ""
    }
  }
  
  tags = local.common_tags
}

# ACM Certificate for HTTPS
resource "aws_acm_certificate" "main" {
  provider = aws.us_east_1
  
  domain_name       = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.project_name}-${local.environment}-certificate"
  })
}

# ACM Certificate validation
resource "aws_route53_record" "cert_validation" {
  provider = aws.us_east_1
  
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  
  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main.zone_id
}

resource "aws_acm_certificate_validation" "main" {
  provider = aws.us_east_1
  
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# CloudWatch Dashboards for each region
module "cloudwatch_us_east_1" {
  source = "./modules/cloudwatch"
  
  providers = {
    aws = aws.us_east_1
  }
  
  region      = "us-east-1"
  cluster_name = module.ecs_cluster_us_east_1.cluster_name
  alb_arn     = module.alb_us_east_1.arn
  
  tags = local.common_tags
}

module "cloudwatch_eu_west_1" {
  source = "./modules/cloudwatch"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  region      = "eu-west-1"
  cluster_name = module.ecs_cluster_eu_west_1.cluster_name
  alb_arn     = module.alb_eu_west_1.arn
  
  tags = local.common_tags
}

module "cloudwatch_ap_southeast_1" {
  source = "./modules/cloudwatch"
  
  providers = {
    aws = aws.ap_southeast_1
  }
  
  region      = "ap-southeast-1"
  cluster_name = module.ecs_cluster_ap_southeast_1.cluster_name
  alb_arn     = module.alb_ap_southeast_1.arn
  
  tags = local.common_tags
}
