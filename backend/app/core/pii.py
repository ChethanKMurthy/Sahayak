"""PII safety helpers (DPDP Act 2023 + Aadhaar Act aligned).

The same masking runs on-device in the apps BEFORE egress; this server-side copy
is defence-in-depth. The full 12-digit Aadhaar number is never stored or logged —
only the last 4 digits are kept.
"""
from __future__ import annotations

import re
from typing import Any

# 12 digits, optionally in 4-4-4 groups.
_AADHAAR_RE = re.compile(r"\b(\d{4})\s?-?(\d{4})\s?-?(\d{4})\b")
_AADHAAR_KEYS = {"aadhaar", "aadhaar_number", "uid", "uidai"}


def mask_aadhaar_in_text(text: str) -> str:
    """Replace any full Aadhaar number with XXXX-XXXX-<last4>."""
    return _AADHAAR_RE.sub(lambda m: f"XXXX-XXXX-{m.group(3)}", text or "")


def extract_aadhaar_last4(text: str) -> str | None:
    m = _AADHAAR_RE.search(text or "")
    return m.group(3) if m else None


def scrub_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Drop any full-Aadhaar field, converting it to aadhaar_last4."""
    out: dict[str, Any] = {}
    for k, v in fields.items():
        key = k.lower()
        if key in _AADHAAR_KEYS and isinstance(v, str):
            last4 = extract_aadhaar_last4(v) or v[-4:]
            out["aadhaar_last4"] = last4
            continue
        out[k] = mask_aadhaar_in_text(v) if isinstance(v, str) else v
    return out


def safe_log(detail: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask any string before it touches the audit log."""
    def _walk(obj: Any) -> Any:
        if isinstance(obj, str):
            return mask_aadhaar_in_text(obj)
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_walk(v) for v in obj]
        return obj

    return _walk(detail)
