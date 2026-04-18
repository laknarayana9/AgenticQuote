variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "agenticquote-production"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "agenticquote.com"
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "enable_monitoring" {
  description = "Enable monitoring stack"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable logging stack"
  type        = bool
  default     = true
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "google_maps_api_key" {
  description = "Google Maps API key"
  type        = string
  sensitive   = true
}

variable "corelogic_api_key" {
  description = "CoreLogic API key"
  type        = string
  sensitive   = true
}

variable "fema_api_key" {
  description = "FEMA API key"
  type        = string
  sensitive   = true
}

variable "lexisnexis_api_key" {
  description = "LexisNexis API key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "oauth_client_id" {
  description = "OAuth client ID"
  type        = string
  sensitive   = true
}

variable "oauth_client_secret" {
  description = "OAuth client secret"
  type        = string
  sensitive   = true
}

variable "encryption_key" {
  description = "Encryption key (32 bytes)"
  type        = string
  sensitive   = true
}
