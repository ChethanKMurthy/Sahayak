data "aws_caller_identity" "me" {}
data "aws_region" "current" {}

# Use the account's default VPC + subnets (free; fine for an MVP).
data "aws_vpc" "default" { default = true }
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

locals {
  name = var.project
  acct = data.aws_caller_identity.me.account_id
}

# ───────────────────────── S3: generated PDFs (private) ─────────────────────
resource "aws_s3_bucket" "docs" {
  bucket = "${local.name}-documents-${local.acct}"
}

resource "aws_s3_bucket_public_access_block" "docs" {
  bucket                  = aws_s3_bucket.docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "docs" {
  bucket = aws_s3_bucket.docs.id
  # Transient document images expire fast; generated PDFs kept 90 days.
  rule {
    id     = "expire-transient"
    status = "Enabled"
    filter { prefix = "transient/" }
    expiration { days = 3 }
  }
  rule {
    id     = "expire-pdfs"
    status = "Enabled"
    filter { prefix = "" }
    expiration { days = 90 }
  }
}

# ───────────────────────── RDS Postgres (free tier) ─────────────────────────
resource "aws_security_group" "rds" {
  name_prefix = "${local.name}-rds-"
  vpc_id      = data.aws_vpc.default.id
  description = "Postgres access from the App Runner VPC connector only"
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "apprunner" {
  name_prefix = "${local.name}-apprunner-"
  vpc_id      = data.aws_vpc.default.id
  description = "App Runner egress to RDS"
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group_rule" "rds_from_apprunner" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds.id
  source_security_group_id = aws_security_group.apprunner.id
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_db_instance" "pg" {
  identifier             = "${local.name}-pg"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t4g.micro" # free tier
  allocated_storage      = 20             # free tier
  storage_type           = "gp2"
  db_name                = "sahayak"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  skip_final_snapshot    = true
  apply_immediately      = true
  deletion_protection    = false
}

# ───────────────────────── Cognito (phone OTP) ──────────────────────────────
resource "aws_cognito_user_pool" "main" {
  name                     = "${local.name}-users"
  username_attributes      = ["phone_number"]
  auto_verified_attributes = ["phone_number"]
  sms_authentication_message = "Your Sahayak code is {####}"
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_phone_number"
      priority = 1
    }
  }
}

resource "aws_cognito_user_pool_client" "app" {
  name            = "${local.name}-client"
  user_pool_id    = aws_cognito_user_pool.main.id
  generate_secret = false
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]
}

# ───────────────────────── Secrets Manager (app config) ─────────────────────
resource "aws_secretsmanager_secret" "app" {
  name = "${local.name}/app-config"
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    DATABASE_URL         = "postgresql+psycopg://${var.db_username}:${var.db_password}@${aws_db_instance.pg.address}:5432/sahayak"
    GROK_API_KEY         = var.grok_api_key
    GROK_BASE_URL        = var.grok_base_url
    GROK_MODEL           = var.grok_model
    GROK_MODEL_LARGE     = var.grok_model
    BHASHINI_API_KEY     = var.bhashini_api_key
    BHASHINI_USER_ID     = var.bhashini_user_id
    OCR_PROVIDER         = var.ocr_provider
    VOICE_PROVIDER       = var.voice_provider
    S3_BUCKET            = aws_s3_bucket.docs.bucket
    COGNITO_USER_POOL_ID = aws_cognito_user_pool.main.id
    COGNITO_CLIENT_ID    = aws_cognito_user_pool_client.app.id
    AWS_REGION           = var.aws_region
  })
}

# ───────────────────────── ECR repositories ─────────────────────────────────
resource "aws_ecr_repository" "api" {
  name                 = "${local.name}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_ecr_repository" "web" {
  name                 = "${local.name}-web"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

# ───────────────────────── IAM for App Runner ───────────────────────────────
# Access role: lets App Runner pull from ECR.
resource "aws_iam_role" "apprunner_access" {
  name = "${local.name}-apprunner-access"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "build.apprunner.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# Instance role: the running app's permissions (S3, Secrets, Textract, etc.).
resource "aws_iam_role" "apprunner_instance" {
  name = "${local.name}-apprunner-instance"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "tasks.apprunner.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "apprunner_app" {
  name = "${local.name}-app-policy"
  role = aws_iam_role.apprunner_instance.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:PutObject", "s3:GetObject"], Resource = "${aws_s3_bucket.docs.arn}/*" },
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = aws_secretsmanager_secret.app.arn },
      { Effect = "Allow", Action = ["textract:DetectDocumentText", "textract:AnalyzeDocument"], Resource = "*" },
      { Effect = "Allow", Action = ["transcribe:StartStreamTranscription", "polly:SynthesizeSpeech"], Resource = "*" },
      { Effect = "Allow", Action = ["sns:Publish"], Resource = "*" }
    ]
  })
}

# VPC connector so App Runner can reach the private RDS.
resource "aws_apprunner_vpc_connector" "main" {
  vpc_connector_name = "${local.name}-vpc"
  subnets            = data.aws_subnets.default.ids
  security_groups    = [aws_security_group.apprunner.id]
}

# ───────────────────────── App Runner: API ──────────────────────────────────
resource "aws_apprunner_service" "api" {
  service_name = "${local.name}-api"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }
    image_repository {
      image_identifier      = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
      image_repository_type = "ECR"
      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          # The app reads secrets from Secrets Manager at runtime via AWS_SECRET_NAME.
          AWS_SECRET_NAME = aws_secretsmanager_secret.app.name
          # "*" for MVP; tighten to the web URL post-deploy (see infra/README).
          CORS_ORIGINS = "*"
        }
      }
    }
  }

  instance_configuration {
    cpu               = "512"  # 0.5 vCPU — cost-minimised
    memory            = "1024" # 1 GB
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.main.arn
    }
  }

  health_check_configuration {
    path     = "/api/health"
    protocol = "HTTP"
  }

  # CI updates the image tag; don't let Terraform fight it.
  lifecycle { ignore_changes = [source_configuration[0].image_repository[0].image_identifier] }
}

# ───────────────────────── App Runner: Web ──────────────────────────────────
resource "aws_apprunner_service" "web" {
  service_name = "${local.name}-web"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }
    image_repository {
      image_identifier      = "${aws_ecr_repository.web.repository_url}:${var.web_image_tag}"
      image_repository_type = "ECR"
      image_configuration {
        port = "3000"
        runtime_environment_variables = {
          NEXT_PUBLIC_API_URL = "https://${aws_apprunner_service.api.service_url}"
        }
      }
    }
  }

  instance_configuration {
    cpu    = "256"  # 0.25 vCPU — cost-minimised
    memory = "512"  # 0.5 GB
  }

  lifecycle { ignore_changes = [source_configuration[0].image_repository[0].image_identifier] }
}
