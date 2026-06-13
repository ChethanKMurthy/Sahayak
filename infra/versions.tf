terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
  # For team use, store state remotely (uncomment + create the bucket/table first):
  # backend "s3" {
  #   bucket         = "sahayak-tfstate"
  #   key            = "infra/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "sahayak-tflock"
  # }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = "sahayak"
      Managed = "terraform"
    }
  }
}
