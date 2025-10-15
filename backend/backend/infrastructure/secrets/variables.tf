variable "project" {
  type        = string
  description = "Project name"
  default     = "richesreach"
}

variable "env" {
  type        = string
  description = "Environment (production, staging, development)"
  default     = "production"
}

variable "regions" {
  type        = list(string)
  description = "AWS regions for multi-region deployment"
  default     = ["us-east-1", "eu-west-1", "ap-southeast-1"]
}

variable "secrets_list" {
  type = map(string)
  description = "Logical names -> descriptions for secrets"
  default = {
    "openai_api_key"      = "OpenAI API key for AI features"
    "polygon_api_key"     = "Polygon.io API key for market data"
    "finnhub_api_key"     = "Finnhub API key for stock data"
    "alpha_vantage_key"   = "Alpha Vantage API key for technical indicators"
    "alchemy_key"         = "Alchemy API key for blockchain data"
    "walletconnect_id"    = "WalletConnect project ID"
    "newsapi_key"         = "News API key for financial news"
    "aws_access_key"      = "AWS IAM access key for CI/CD"
  }
}
