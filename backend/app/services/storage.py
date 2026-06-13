"""Storage adapter for generated PDFs. S3 in cloud, database otherwise.

PDFs live in the DB by default (not the local filesystem) so the app keeps no
local state — this is what lets it run on a serverless/ephemeral filesystem
(Vercel) as well as locally on SQLite, with identical behaviour."""
from __future__ import annotations

from typing import Protocol

from ..config import settings


class StorageAdapter(Protocol):
    def put_pdf(self, key: str, data: bytes) -> str: ...
    def get_pdf(self, key: str) -> bytes | None: ...


class DbStorage:
    """Stores PDF bytes in the `pdf_blobs` table. Opens its own short-lived
    session so callers don't have to thread one through."""

    def put_pdf(self, key: str, data: bytes) -> str:
        from ..db import PdfBlob, SessionLocal

        with SessionLocal() as db:
            db.merge(PdfBlob(key=key, data=data))
            db.commit()
        return f"/api/files/{key}"  # served by the API

    def get_pdf(self, key: str) -> bytes | None:
        from ..db import PdfBlob, SessionLocal

        with SessionLocal() as db:
            row = db.get(PdfBlob, key)
            return bytes(row.data) if row else None


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
    return S3Storage() if use_s3 else DbStorage()
