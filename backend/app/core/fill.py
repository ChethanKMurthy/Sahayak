"""Form-fill mapper: binds known facts to a form template's fields using the
DSL source-hints, recording provenance + confidence tier on each binding.

Deterministic-first: a source-hint match or a same-key fact binds directly. The
LLM field-mapper is only a fallback for fields with no deterministic match.
"""
from __future__ import annotations

from typing import Any

from ..schemas.core import (
    ConfidenceTier,
    FieldValue,
    FormField,
    FormTemplate,
    Provenance,
    SourceType,
)


def _facts_by_key(field_values: list[FieldValue]) -> dict[str, FieldValue]:
    return {fv.key: fv for fv in field_values}


def _hint_key(hint: str) -> str:
    # "aadhaar.name" -> "name"
    return hint.split(".", 1)[1] if "." in hint else hint


def fill_form(
    template: FormTemplate, field_values: list[FieldValue], lang: str = "en"
) -> list[dict[str, Any]]:
    """Return one record per template field: {key,label,value,tier,source,required,
    self_declared,verified}."""
    facts = _facts_by_key(field_values)
    out: list[dict[str, Any]] = []

    for field in template.fields:
        fv = _bind_field(field, facts)
        label = field.label.get(lang) or field.label.get("en") or field.key
        if fv is None:
            out.append({
                "key": field.key, "label": label, "value": None,
                "tier": ConfidenceTier.AMBER.value, "source": "", "required": field.required,
                "self_declared": field.self_declared, "verified": False, "missing": True,
            })
            continue
        tier = ConfidenceTier.RED.value if field.self_declared else fv.tier.value
        out.append({
            "key": field.key, "label": label, "value": fv.value, "tier": tier,
            "source": fv.provenance.note or fv.provenance.source_ref,
            "source_ref": fv.provenance.source_ref,
            "required": field.required, "self_declared": field.self_declared,
            "verified": fv.verified, "missing": False,
        })
    return out


def _bind_field(field: FormField, facts: dict[str, FieldValue]) -> FieldValue | None:
    # 1) exact key match
    if field.key in facts:
        return facts[field.key]
    # 2) source-hint match (first hint whose underlying key we know)
    for hint in field.source_hints:
        key = _hint_key(hint)
        if key in facts:
            return facts[key]
    return None


def missing_required(filled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [f for f in filled if f.get("required") and f.get("value") in (None, "")]


def fields_to_review(filled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only amber + red need human review (green is cross-verified)."""
    return [f for f in filled if f.get("tier") in ("amber", "red") and not f.get("missing")]
