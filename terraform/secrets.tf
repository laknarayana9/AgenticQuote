# AWS Secrets Manager for secure secret storage

resource "aws_secretsmanager_secret" "database" {
  name = "agenticquote/production/database"
  description = "Database credentials for AgenticQuote production"

  recovery_window_in_days = 30
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    username = "agenticquote"
    password = var.database_password
    host     = "postgres-primary.production.svc.cluster.local"
    port     = 5432
    dbname   = "agenticquote"
  })
}

resource "aws_secretsmanager_secret" "api_keys" {
  name = "agenticquote/production/api-keys"
  description = "API keys for external providers"

  recovery_window_in_days = 30
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    google_maps_api_key = var.google_maps_api_key
    corelogic_api_key    = var.corelogic_api_key
    fema_api_key         = var.fema_api_key
    lexisnexis_api_key   = var.lexisnexis_api_key
    openai_api_key       = var.openai_api_key
  })
}

resource "aws_secretsmanager_secret" "oauth" {
  name = "agenticquote/production/oauth"
  description = "OAuth client credentials"

  recovery_window_in_days = 30
}

resource "aws_secretsmanager_secret_version" "oauth" {
  secret_id = aws_secretsmanager_secret.oauth.id
  secret_string = jsonencode({
    client_id     = var.oauth_client_id
    client_secret = var.oauth_client_secret
  })
}

resource "aws_secretsmanager_secret" "encryption" {
  name = "agenticquote/production/encryption"
  description = "Encryption key for data at rest"

  recovery_window_in_days = 30
}

resource "aws_secretsmanager_secret_version" "encryption" {
  secret_id = aws_secretsmanager_secret.encryption.id
  secret_string = jsonencode({
    encryption_key = var.encryption_key
  })
}

# IAM role for Kubernetes to access Secrets Manager
resource "aws_iam_role" "secrets_manager" {
  name = "agenticquote-secrets-manager"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = module.eks.oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "${module.eks.oidc_provider}:sub" = "system:serviceaccount:production:agenticquote"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "secrets_manager" {
  name = "secrets-manager-access"
  role = aws_iam_role.secrets_manager.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.database.arn,
          aws_secretsmanager_secret.api_keys.arn,
          aws_secretsmanager_secret.oauth.arn,
          aws_secretsmanager_secret.encryption.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_manager" {
  role       = aws_iam_role.secrets_manager.name
  policy_arn = aws_iam_role_policy.secrets_manager.arn
}
