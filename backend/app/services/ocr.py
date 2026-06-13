"""OCR adapter. On-device ML Kit runs in the apps; this is the server-side cloud
fallback (AWS Textract). Mock returns the raw text already carried by an uploaded
payload, so the pipeline runs without AWS.

Returns (raw_text, ocr_quality 0..1, recapture_hint|None).
"""
from __future__ import annotations

from typing import Optional, Protocol

from ..config import settings


class OCRAdapter(Protocol):
    async def read(self, image_bytes: bytes, mime: str) -> tuple[str, float, Optional[str]]: ...


class MockOCR:
    async def read(self, image_bytes: bytes, mime: str) -> tuple[str, float, Optional[str]]:
        # In mock mode the client sends pre-extracted text; if bytes are tiny we
        # simulate a low-quality capture to exercise the assisted-recapture path.
        if len(image_bytes) < 32:
            return ("", 0.4, "Image looks unclear — move the document into the frame and avoid glare.")
        try:
            return (image_bytes.decode("utf-8", "ignore"), 0.95, None)
        except Exception:
            return ("", 0.5, "Could not read the image — try again in better light.")


class TextractOCR:
    def __init__(self) -> None:
        import boto3  # imported lazily so boto3 isn't required in mock mode

        self._client = boto3.client(
            "textract",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

    async def read(self, image_bytes: bytes, mime: str) -> tuple[str, float, Optional[str]]:
        resp = self._client.detect_document_text(Document={"Bytes": image_bytes})
        lines, confs = [], []
        for block in resp.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                lines.append(block.get("Text", ""))
                confs.append(block.get("Confidence", 0) / 100.0)
        quality = sum(confs) / len(confs) if confs else 0.5
        hint = None if quality >= 0.6 else "Low confidence — re-capture the document without glare."
        return ("\n".join(lines), quality, hint)


def get_ocr() -> OCRAdapter:
    return TextractOCR() if settings.ocr_provider == "textract" else MockOCR()
