"""Builds the canonical list of FieldValues (facts) from documents, spoken
answers, and mismatch resolutions — assigning the green/amber/red confidence
tier to each, with full provenance. See docs/ARCHITECTURE.md §6.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from ..schemas.core import (
    ConfidenceTier,
    Document,
    FieldValue,
    Provenance,
    SourceType,
)

# Fields that are inherently self-declared / unverifiable → always RED.
SELF_DECLARED_FIELDS = {"income", "annual_income", "no_existing_lpg", "occupation_self"}

# OCR confidence below this drops a document-sourced field from green→amber.
_OCR_GREEN_THRESHOLD = 0.85


def _doc_origin_note(field: str, doc: Document) -> str:
    return f"{field} read from {doc.type.value.replace('_', ' ')}"


def build_field_values(
    documents: list[Document],
    spoken: dict[str, Any],
    resolutions: Optional[dict[str, Any]] = None,
    cross_verified: Optional[set[str]] = None,
) -> list[FieldValue]:
    """Merge all sources into one fact list with tiers + provenance.

    Priority for a field's value: explicit mismatch resolution > document > spoken.
    Tier rules:
      green = from a document, OCR-confident, AND cross-verified across ≥2 docs
      amber = single-source document / lower OCR confidence / inferred
      red   = self-declared spoken value
    """
    resolutions = resolutions or {}
    cross_verified = cross_verified or set()

    # Collect document-sourced values per field (keep best OCR confidence).
    doc_values: dict[str, tuple[Any, Document, float]] = {}
    doc_count: dict[str, int] = {}
    for doc in documents:
        for ef in doc.fields:
            doc_count[ef.key] = doc_count.get(ef.key, 0) + 1
            cur = doc_values.get(ef.key)
            if cur is None or ef.ocr_confidence > cur[2]:
                doc_values[ef.key] = (ef.value, doc, ef.ocr_confidence)

    out: dict[str, FieldValue] = {}

    # 1) Document-sourced facts.
    for key, (value, doc, conf) in doc_values.items():
        verified = key in cross_verified or doc_count.get(key, 0) >= 2
        if key in SELF_DECLARED_FIELDS:
            tier = ConfidenceTier.RED
        elif conf >= _OCR_GREEN_THRESHOLD and verified:
            tier = ConfidenceTier.GREEN
        else:
            tier = ConfidenceTier.AMBER
        out[key] = FieldValue(
            key=key,
            value=value,
            tier=tier,
            verified=verified,
            provenance=Provenance(
                source_type=SourceType.DOCUMENT,
                source_ref=f"{doc.type.value}.{key}",
                document_id=doc.id,
                ocr_confidence=conf,
                note=_doc_origin_note(key, doc),
            ),
        )

    # 2) Spoken facts (fill gaps; spoken income etc. is RED).
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    for key, value in spoken.items():
        if value in (None, ""):
            continue
        if key in out and out[key].value not in (None, ""):
            # Spoken doesn't override a document value unless document was empty.
            continue
        tier = ConfidenceTier.RED if key in SELF_DECLARED_FIELDS else ConfidenceTier.AMBER
        out[key] = FieldValue(
            key=key,
            value=value,
            tier=tier,
            verified=False,
            provenance=Provenance(
                source_type=SourceType.SPOKEN,
                source_ref=f"spoken.{key}",
                captured_at=now,
                note=f"{key} from your spoken answer",
            ),
        )

    # 3) Mismatch resolutions win and become cross-verified (user chose).
    for key, value in resolutions.items():
        prov = out[key].provenance if key in out else Provenance(
            source_type=SourceType.DOCUMENT, source_ref=f"resolved.{key}"
        )
        prov.note = f"{key} confirmed by you after a document mismatch"
        out[key] = FieldValue(
            key=key, value=value, tier=ConfidenceTier.GREEN, verified=True, provenance=prov
        )

    return list(out.values())
