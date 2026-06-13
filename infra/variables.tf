variable "aws_region" {
  description = "AWS region (Mumbai keeps data in India for DPDP)."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  type    = string
  default = "sahayak"
}

variable "db_username" {
  type    = string
  default = "sahayak"
}

variable "db_password" {
  description = "RDS master password. Pass via TF_VAR_db_password or tfvars (never commit)."
  type        = string
  sensitive   = true
}

variable "grok_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

# Reasoning LLM endpoint (Groq is OpenAI-compatible; same adapter as xAI Grok).
variable "grok_base_url" {
  type    = string
  default = "https://api.groq.com/openai/v1"
}

variable "grok_model" {
  type    = string
  default = "llama-3.3-70b-versatile"
}

# Cloud AI providers. Per the deploy choice, OCR/voice stay on mock initially.
variable "ocr_provider" {
  type    = string
  default = "mock"
}

variable "voice_provider" {
  type    = string
  default = "mock"
}

variable "bhashini_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "bhashini_user_id" {
  type    = string
  default = ""
}

# Container image tags (CI pushes these to ECR, then updates App Runner).
variable "api_image_tag" {
  type    = string
  default = "latest"
}

variable "web_image_tag" {
  type    = string
  default = "latest"
}
