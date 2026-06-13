#!/usr/bin/env bash
# Park the whole project on AWS as STORAGE ONLY — no servers, no compute, ~no cost.
# An S3 bucket holding the repo + media + the APK. Well within the 5 GB Free Tier;
# beyond that it's pennies/month. This does NOT deploy or run anything.
#
# Prereq: `aws configure` done (region ap-south-1). Usage: bash scripts/archive-to-s3.sh
set -euo pipefail

REGION="${AWS_REGION:-ap-south-1}"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="sahayak-archive-${ACCOUNT}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "▸ Account $ACCOUNT · region $REGION · bucket s3://$BUCKET"

# Create the bucket if it doesn't exist (private, versioned).
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION"
  aws s3api put-public-access-block --bucket "$BUCKET" \
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-versioning --bucket "$BUCKET" \
    --versioning-configuration Status=Enabled
  echo "  created."
fi

# Sync source (skip heavy/build/secret dirs). Secrets never leave the machine.
echo "▸ syncing source → s3://$BUCKET/src/"
aws s3 sync "$ROOT" "s3://$BUCKET/src/" \
  --exclude ".git/*" \
  --exclude "*/.venv/*" --exclude "*/node_modules/*" \
  --exclude "web/.next/*" --exclude "mobile/build/*" --exclude "mobile/.dart_tool/*" \
  --exclude "infra/.terraform/*" --exclude "*.tfstate*" \
  --exclude "**/.env" --exclude "infra/terraform.tfvars" --exclude "backend/sahayak.db" \
  --delete

# Optionally archive the built APK if present.
APK="$ROOT/mobile/build/app/outputs/flutter-apk/app-debug.apk"
[ -f "$APK" ] && { echo "▸ uploading APK"; aws s3 cp "$APK" "s3://$BUCKET/artifacts/sahayak-debug.apk"; }

echo "✅ Done. Files parked at s3://$BUCKET (storage only — no running cost)."
echo "   Browse: aws s3 ls s3://$BUCKET/ --recursive --human-readable --summarize"
