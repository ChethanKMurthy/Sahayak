"""Storage adapter for generated PDFs. S3 in cloud, local filesystem in dev."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..config import BACKEND_DIR, settings

_LOCAL_DIR = BACKEND_DIR / "generated"
_LOCAL_DIR.mkdir(exist_ok=True)


class StorageAdapter(Protocol):
    def put_pdf(self, key: str, data: bytes) -> str: ...
    def get_pdf(self, key: str) -> bytes | None: ...


class LocalStorage:
    def put_pdf(self, key: str, data: bytes) -> str:
        path = _LOCAL_DIR / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"/api/files/{key}"  # served by the API

    def get_pdf(self, key: str) -> bytes | None:
        path = _LOCAL_DIR / key
        return path.read_bytes() if path.exists() else None


class S3Storage:
    def __init__(self) -> None:
        import boto3

        self._s3 = boto3.client("s3", region_name=settings.aws_region)
        self._bucket = settings.s3_bucket

    def put_pdf(self, key: str, data: bytes) -> str:
        self._s3.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType="application/pdf")
        # Presigned URL (1h) — PDFs are user data, not public.
        return self._s3.generate_presigned_url(
            "get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=3600
        )

    def get_pdf(self, key: str) -> bytes | None:
        try:
            return self._s3.get_object(Bucket=self._bucket, Key=key)["Body"].read()
        except Exception:
            return None


def get_storage() -> StorageAdapter:
    use_s3 = bool(settings.aws_access_key_id) and settings.ocr_provider == "textract"
    return S3Storage() if use_s3 else LocalStorage()
