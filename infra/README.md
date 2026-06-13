# Sahayak — AWS infrastructure (Terraform)

Provisions a complete, cost-aware deployment on AWS (Mumbai / `ap-south-1`, keeping
data in India for DPDP):

| Resource | Service | Free-tier note |
|---|---|---|
| API + Web | **App Runner** (2 services, containers from ECR) | Not free-tier, but cheap and covered by credits; scales to small |
| Database | **RDS PostgreSQL** `db.t4g.micro`, 20 GB | Free tier 12 months |
| PDF storage | **S3** (private, lifecycle expiry) | 5 GB free |
| Auth | **Cognito** phone-OTP user pool | 50k MAU free |
| Secrets | **Secrets Manager** (`sahayak/app-config`) | small cost |
| OCR/Voice | IAM perms for **Textract / Transcribe / Polly** | intro free tiers |

> **Cost honesty:** this is right-sized for an MVP/demo and covered by free credits.
> The path to 1cr+ users (cells, Aurora, queues, on-device-first) is in
> [`../docs/SCALING.md`](../docs/SCALING.md).

## Prerequisites

- Terraform ≥ 1.6, AWS CLI configured (`aws configure`) with an IAM user/role that can
  create the above, Docker.

## Deploy (first time)

App Runner needs an image in ECR before it can start, so we bootstrap in two phases.

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # set db_password (+ keys if you have them)

# Phase 1 — create just the ECR repos.
terraform init
terraform apply -target=aws_ecr_repository.api -target=aws_ecr_repository.web

# Phase 2 — build & push the images (from the REPO ROOT).
cd ..
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=ap-south-1
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com
docker build -f backend/Dockerfile -t $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sahayak-api:latest .
docker build -f web/Dockerfile     -t $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sahayak-web:latest .
docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sahayak-api:latest
docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sahayak-web:latest

# Phase 3 — create everything else.
cd infra && terraform apply
terraform output            # api_url, web_url, etc.
```

After the first deploy, **CI** (`.github/workflows/deploy.yml`) rebuilds and pushes on
every push to `main`, then triggers an App Runner deployment — no Terraform needed for
routine releases.

## Post-deploy hardening

- Tighten the API's `CORS_ORIGINS` from `*` to the `web_url` output.
- Enable RDS deletion protection + automated backups for anything beyond a demo.
- Move Terraform state to the S3 backend block in `versions.tf`.

## Required GitHub Actions secrets (for CI/CD)

- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (deployer IAM user), `AWS_REGION`

## Teardown

```bash
cd infra && terraform destroy
```
