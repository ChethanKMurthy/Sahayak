output "api_url" {
  description = "Public HTTPS URL of the backend API."
  value       = "https://${aws_apprunner_service.api.service_url}"
}

output "web_url" {
  description = "Public HTTPS URL of the web app."
  value       = "https://${aws_apprunner_service.web.service_url}"
}

output "ecr_api_repo" { value = aws_ecr_repository.api.repository_url }
output "ecr_web_repo" { value = aws_ecr_repository.web.repository_url }
output "rds_endpoint" { value = aws_db_instance.pg.address }
output "s3_bucket" { value = aws_s3_bucket.docs.bucket }
output "cognito_user_pool_id" { value = aws_cognito_user_pool.main.id }
output "cognito_client_id" { value = aws_cognito_user_pool_client.app.id }
output "secret_name" { value = aws_secretsmanager_secret.app.name }
