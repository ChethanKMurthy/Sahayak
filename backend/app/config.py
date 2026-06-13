"""Central configuration. Reads .env; every external provider defaults to a mock."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _hydrate_from_secrets_manager() -> None:
    """In AWS, pull the app-config secret JSON into os.environ before Settings
    is built. No-op locally (AWS_SECRET_NAME unset). Keeps keys out of the image."""
    name = os.environ.get("AWS_SECRET_NAME")
    if not name:
        return
    try:
        import boto3  # only present/needed in the cloud image

        client = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
        secret = client.get_secret_value(SecretId=name)["SecretString"]
        for k, v in json.loads(secret).items():
            os.environ.setdefault(k, str(v))  # explicit env still wins
    except Exception as e:  # never crash the app over secret hydration
        print(f"[config] Secrets Manager hydration skipped: {e}")


_hydrate_from_secrets_manager()

# Repo root = .../SAHELI ; shared data lives in /shared
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
SHARED_DIR = REPO_ROOT / "shared"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core
    database_url: str = "sqlite:///./sahayak.db"
    cors_origins: str = "http://localhost:3000"
    session_ttl_seconds: int = 86400

    # Grok (xAI)
    grok_api_key: str = ""
    grok_base_url: str = "https://api.x.ai/v1"
    grok_model: str = "grok-4-fast"
    grok_model_large: str = "grok-4"

    # OCR / Voice provider selection
    ocr_provider: str = "mock"      # mock | textract
    voice_provider: str = "mock"    # mock | bhashini | aws

    # Bhashini
    bhashini_user_id: str = ""
    bhashini_api_key: str = ""
    bhashini_pipeline_id: str = ""

    # AWS
    aws_region: str = "ap-south-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket: str = "sahayak-documents"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def grok_enabled(self) -> bool:
        return bool(self.grok_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
