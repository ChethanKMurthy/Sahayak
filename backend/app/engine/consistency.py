"""Cross-document consistency engine.

Detects the single biggest cause of rejected applications: name / DOB / address
mismatches across documents. Uses fuzzy matching so "Mohd Imran" vs "Mohammad
Imran" is flagged, not silently picked. See docs spec §3 (Trust & correctness).
"""
from __future__ import annotations

from typing import Any

from rapidfuzz import fuzz

from ..schemas.core import Document, Mismatch
from .facts import _parse_date

# Fields worth cross-checking and the localized question to ask on mismatch.
_CHECK_FIELDS = ["name", "dob", "address", "father_name", "gender"]

_QUESTION = {
    "name": {
        "en": "Your name appears differently across documents — which one should the form use?",
        "hi": "आपका नाम दस्तावेज़ों में अलग-अलग है — फ़ॉर्म में कौन सा इस्तेमाल करें?",
        "kn": "ನಿಮ್ಮ ಹೆಸರು ದಾಖಲೆಗಳಲ್ಲಿ ವಿಭಿನ್ನವಾಗಿದೆ — ಫಾರ್ಮ್‌ನಲ್ಲಿ ಯಾವುದನ್ನು ಬಳಸಬೇಕು?",
    },
    "dob": {
        "en": "Your date of birth differs across documents — which is correct?",
        "hi": "आपकी जन्मतिथि दस्तावेज़ों में अलग है — कौन सी सही है?",
        "kn": "ನಿಮ್ಮ ಜನ್ಮ ದಿನಾಂಕ ವಿಭಿನ್ನವಾಗಿದೆ — ಯಾವುದು ಸರಿ?",
    },
    "address": {
        "en": "Your address differs across documents — which should the form use?",
        "hi": "आपका पता दस्तावेज़ों में अलग है — फ़ॉर्म में कौन सा इस्तेमाल करें?",
        "kn": "ನಿಮ್ಮ ವಿಳಾಸ ವಿಭಿನ್ನವಾಗಿದೆ — ಫಾರ್ಮ್‌ನಲ್ಲಿ ಯಾವುದನ್ನು ಬಳಸಬೇಕು?",
    },
}
_GENERIC_Q = {
    "en": "This value differs across documents — which one is correct?",
    "hi": "यह जानकारी दस्तावेज़ों में अलग है — कौन सी सही है?",
}

# Similarity below which two string values are considered a real mismatch.
_NAME_THRESHOLD = 88


def _values_agree(field: str, a: Any, b: Any) -> bool:
    if a is None or b is None or a == "" or b == "":
        return True  # missing on one side isn't a mismatch
    if field == "dob":
        da, db = _parse_date(a), _parse_date(b)
        if da and db:
            return da == db
        return str(a).strip() == str(b).strip()
    if field in ("name", "father_name", "address"):
        return fuzz.token_sort_ratio(str(a).lower(), str(b).lower()) >= _NAME_THRESHOLD
    return str(a).strip().lower() == str(b).strip().lower()


def detect_mismatches(documents: list[Document], lang: str = "en") -> list[Mismatch]:
    """Return one Mismatch per field whose values disagree across documents."""
    # Gather {field: [(value, document)]}
    by_field: dict[str, list[tuple[Any, Document]]] = {f: [] for f in _CHECK_FIELDS}
    for doc in documents:
        for ef in doc.fields:
            if ef.key in by_field and ef.value not in (None, ""):
                by_field[ef.key].append((ef.value, doc))

    mismatches: list[Mismatch] = []
    for field, entries in by_field.items():
        if len(entries) < 2:
            continue
        # Are all pairwise values in agreement?
        agree = all(
            _values_agree(field, entries[0][0], v) for v, _ in entries[1:]
        ) and all(_values_agree(field, a, b) for a, _ in entries for b, _ in entries)
        if agree:
            continue
        seen: list[Any] = []
        values_payload = []
        for value, doc in entries:
            if any(_values_agree(field, value, s) for s in seen):
                continue
            seen.append(value)
            values_payload.append(
                {"value": value, "document_id": doc.id, "doc_type": doc.type.value}
            )
        if len(values_payload) < 2:
            continue
        q = _QUESTION.get(field, _GENERIC_Q)
        question = {lang: q.get(lang, q.get("en", _GENERIC_Q["en"]))}
        if lang != "en":
            question.setdefault("en", q.get("en", _GENERIC_Q["en"]))
        mismatches.append(Mismatch(field=field, values=values_payload, question=question))
    return mismatches
