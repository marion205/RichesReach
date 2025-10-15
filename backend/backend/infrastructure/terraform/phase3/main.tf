# Phase 3 Multi-Region Infrastructure
# Advanced AI, Multi-region, Performance Optimization

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "riches-reach-terraform-state"
    key    = "phase3/terraform.tfstate"
    region = "us-east-1"
  }
}

# Configure providers for multiple regions
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

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local values
locals {
  project_name = "riches-reach"
  environment  = var.environment
  regions = {
    us_east_1     = "us-east-1"
    eu_west_1     = "eu-west-1"
    ap_southeast_1 = "ap-southeast-1"
  }
  
  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    Phase       = "3"
    ManagedBy   = "terraform"
  }
}

# VPC and Networking for each region
module "vpc_us_east_1" {
  source = "./modules/vpc"
  
  providers = {
    aws = aws.us_east_1
  }
  
  region     = local.regions.us_east_1
  cidr_block = "10.0.0.0/16"
  
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
  
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
  
  public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  private_subnet_cidrs = ["10.1.11.0/24", "10.1.12.0/24", "10.1.13.0/24"]
  
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
  
  public_subnet_cidrs  = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
  private_subnet_cidrs = ["10.2.11.0/24", "10.2.12.0/24", "10.2.13.0/24"]
  
  tags = local.common_tags
}

# ECS Clusters for each region
module "ecs_cluster_us_east_1" {
  source = "./modules/ecs-cluster"
  
  providers = {
    aws = aws.us_east_1
  }
  
  cluster_name = "${local.project_name}-${local.environment}-us-east-1"
  region       = local.regions.us_east_1
  
  vpc_id             = module.vpc_us_east_1.vpc_id
  private_subnet_ids = module.vpc_us_east_1.private_subnet_ids
  public_subnet_ids  = module.vpc_us_east_1.public_subnet_ids
  
  instance_types = ["t3.medium", "t3.large"]
  min_size       = 2
  max_size       = 10
  desired_size   = 3
  
  tags = local.common_tags
}

module "ecs_cluster_eu_west_1" {
  source = "./modules/ecs-cluster"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  cluster_name = "${local.project_name}-${local.environment}-eu-west-1"
  region       = local.regions.eu_west_1
  
  vpc_id             = module.vpc_eu_west_1.vpc_id
  private_subnet_ids = module.vpc_eu_west_1.private_subnet_ids
  public_subnet_ids  = module.vpc_eu_west_1.public_subnet_ids
  
  instance_types = ["t3.medium", "t3.large"]
  min_size       = 1
  max_size       = 8
  desired_size   = 2
  
  tags = local.common_tags
}

module "ecs_cluster_ap_southeast_1" {
  source = "./modules/ecs-cluster"
  
  providers = {
    aws = aws.ap_southeast_1
  }
  
  cluster_name = "${local.project_name}-${local.environment}-ap-southeast-1"
  region       = local.regions.ap_southeast_1
  
  vpc_id             = module.vpc_ap_southeast_1.vpc_id
  private_subnet_ids = module.vpc_ap_southeast_1.private_subnet_ids
  public_subnet_ids  = module.vpc_ap_southeast_1.public_subnet_ids
  
  instance_types = ["t3.medium", "t3.large"]
  min_size       = 1
  max_size       = 6
  desired_size   = 2
  
  tags = local.common_tags
}

# Aurora Global Database
module "aurora_global" {
  source = "./modules/aurora-global"
  
  providers = {
    aws.primary   = aws.us_east_1
    aws.secondary = aws.eu_west_1
    aws.tertiary  = aws.ap_southeast_1
  }
  
  cluster_identifier = "${local.project_name}-${local.environment}-global"
  
  primary_region   = local.regions.us_east_1
  secondary_region = local.regions.eu_west_1
  tertiary_region  = local.regions.ap_southeast_1
  
  primary_vpc_id   = module.vpc_us_east_1.vpc_id
  secondary_vpc_id = module.vpc_eu_west_1.vpc_id
  tertiary_vpc_id  = module.vpc_ap_southeast_1.vpc_id
  
  primary_subnet_ids   = module.vpc_us_east_1.private_subnet_ids
  secondary_subnet_ids = module.vpc_eu_west_1.private_subnet_ids
  tertiary_subnet_ids  = module.vpc_ap_southeast_1.private_subnet_ids
  
  tags = local.common_tags
}

# CloudFront Distribution
module "cloudfront" {
  source = "./modules/cloudfront"
  
  providers = {
    aws = aws.us_east_1
  }
  
  distribution_name = "${local.project_name}-${local.environment}"
  
  # Origin configurations for each region
  origins = {
    us_east_1 = {
      domain_name = module.ecs_cluster_us_east_1.alb_dns_name
      origin_path = ""
      custom_origin_config = {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
    eu_west_1 = {
      domain_name = module.ecs_cluster_eu_west_1.alb_dns_name
      origin_path = ""
      custom_origin_config = {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
    ap_southeast_1 = {
      domain_name = module.ecs_cluster_ap_southeast_1.alb_dns_name
      origin_path = ""
      custom_origin_config = {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }
  
  # Cache behaviors
  cache_behaviors = {
    api = {
      path_pattern     = "/api/*"
      target_origin_id = "us_east_1"
      cache_policy_id  = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled
    }
    ai = {
      path_pattern     = "/ai/*"
      target_origin_id = "us_east_1"
      cache_policy_id  = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled
    }
    static = {
      path_pattern     = "/static/*"
      target_origin_id = "us_east_1"
      cache_policy_id  = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    }
  }
  
  tags = local.common_tags
}

# Route 53 with latency-based routing
module "route53" {
  source = "./modules/route53"
  
  providers = {
    aws = aws.us_east_1
  }
  
  domain_name = var.domain_name
  cloudfront_domain = module.cloudfront.distribution_domain_name
  
  # Regional health checks
  health_checks = {
    us_east_1 = {
      endpoint = module.ecs_cluster_us_east_1.alb_dns_name
      region   = local.regions.us_east_1
    }
    eu_west_1 = {
      endpoint = module.ecs_cluster_eu_west_1.alb_dns_name
      region   = local.regions.eu_west_1
    }
    ap_southeast_1 = {
      endpoint = module.ecs_cluster_ap_southeast_1.alb_dns_name
      region   = local.regions.ap_southeast_1
    }
  }
  
  tags = local.common_tags
}

# Redis Cluster for caching
module "redis_cluster_us_east_1" {
  source = "./modules/redis-cluster"
  
  providers = {
    aws = aws.us_east_1
  }
  
  cluster_id = "${local.project_name}-${local.environment}-us-east-1"
  region     = local.regions.us_east_1
  
  vpc_id             = module.vpc_us_east_1.vpc_id
  subnet_ids         = module.vpc_us_east_1.private_subnet_ids
  security_group_ids = [module.ecs_cluster_us_east_1.security_group_id]
  
  node_type           = "cache.t3.medium"
  num_cache_clusters  = 3
  parameter_group_name = "default.redis7"
  
  tags = local.common_tags
}

# Security Hub and GuardDuty
module "security" {
  source = "./modules/security"
  
  providers = {
    aws = aws.us_east_1
  }
  
  regions = [local.regions.us_east_1, local.regions.eu_west_1, local.regions.ap_southeast_1]
  
  tags = local.common_tags
}

# KMS for encryption
module "kms" {
  source = "./modules/kms"
  
  providers = {
    aws = aws.us_east_1
  }
  
  key_name = "${local.project_name}-${local.environment}-encryption"
  
  tags = local.common_tags
}

# Outputs
output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.distribution_domain_name
}

output "route53_domain" {
  description = "Route 53 domain name"
  value       = module.route53.domain_name
}

output "aurora_endpoints" {
  description = "Aurora cluster endpoints"
  value = {
    primary   = module.aurora_global.primary_endpoint
    secondary = module.aurora_global.secondary_endpoint
    tertiary  = module.aurora_global.tertiary_endpoint
  }
}

output "ecs_clusters" {
  description = "ECS cluster information"
  value = {
    us_east_1 = {
      cluster_name = module.ecs_cluster_us_east_1.cluster_name
      alb_dns_name = module.ecs_cluster_us_east_1.alb_dns_name
    }
    eu_west_1 = {
      cluster_name = module.ecs_cluster_eu_west_1.cluster_name
      alb_dns_name = module.ecs_cluster_eu_west_1.alb_dns_name
    }
    ap_southeast_1 = {
      cluster_name = module.ecs_cluster_ap_southeast_1.cluster_name
      alb_dns_name = module.ecs_cluster_ap_southeast_1.alb_dns_name
    }
  }
}

output "redis_endpoints" {
  description = "Redis cluster endpoints"
  value = {
    us_east_1 = module.redis_cluster_us_east_1.cluster_endpoint
  }
}
