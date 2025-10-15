# Multi-Region Infrastructure Outputs

output "vpc_ids" {
  description = "VPC IDs for each region"
  value = {
    us_east_1     = module.vpc_us_east_1.vpc_id
    eu_west_1     = module.vpc_eu_west_1.vpc_id
    ap_southeast_1 = module.vpc_ap_southeast_1.vpc_id
  }
}

output "ecs_cluster_arns" {
  description = "ECS cluster ARNs for each region"
  value = {
    us_east_1     = module.ecs_cluster_us_east_1.cluster_arn
    eu_west_1     = module.ecs_cluster_eu_west_1.cluster_arn
    ap_southeast_1 = module.ecs_cluster_ap_southeast_1.cluster_arn
  }
}

output "alb_dns_names" {
  description = "ALB DNS names for each region"
  value = {
    us_east_1     = module.alb_us_east_1.dns_name
    eu_west_1     = module.alb_eu_west_1.dns_name
    ap_southeast_1 = module.alb_ap_southeast_1.dns_name
  }
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name"
  value       = module.cloudfront.domain_name
}

output "route53_zone_id" {
  description = "Route 53 hosted zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "route53_name_servers" {
  description = "Route 53 name servers"
  value       = aws_route53_zone.main.name_servers
}

output "certificate_arn" {
  description = "ACM certificate ARN"
  value       = aws_acm_certificate.main.arn
}

output "health_check_ids" {
  description = "Route 53 health check IDs"
  value = {
    us_east_1     = aws_route53_health_check.us_east_1.id
    eu_west_1     = aws_route53_health_check.eu_west_1.id
    ap_southeast_1 = aws_route53_health_check.ap_southeast_1.id
  }
}
