"""Builds the post-fill output: attachment checklist, where-to-submit, the
online-wall hand-off notice, and the fair-price meter (official fee vs tout)."""
from __future__ import annotations

from typing import Any

from ..schemas.core import FormTemplate

_DOC_LABELS = {
    "aadhaar": {"en": "Aadhaar card", "hi": "आधार कार्ड"},
    "ration_card": {"en": "Ration card", "hi": "राशन कार्ड"},
    "marksheet": {"en": "Marksheet", "hi": "अंकतालिका"},
    "land_record": {"en": "Land record (7/12 / khasra)", "hi": "भूमि रिकॉर्ड (7/12 / खसरा)"},
    "income_cert": {"en": "Income certificate", "hi": "आय प्रमाण पत्र"},
    "caste_cert": {"en": "Caste certificate", "hi": "जाति प्रमाण पत्र"},
    "death_cert": {"en": "Death certificate", "hi": "मृत्यु प्रमाण पत्र"},
    "disability_cert": {"en": "Disability (UDID) certificate", "hi": "दिव्यांगता (UDID) प्रमाण पत्र"},
    "bank_passbook": {"en": "Bank passbook", "hi": "बैंक पासबुक"},
    "passport_photo": {"en": "Passport-size photo", "hi": "पासपोर्ट आकार की फोटो"},
}


def _loc(d: dict[str, str], lang: str) -> str:
    return d.get(lang) or d.get("en") or next(iter(d.values()), "")


def build_checklist(template: FormTemplate, lang: str) -> list[dict[str, Any]]:
    items = []
    for att in template.attachments:
        label = _DOC_LABELS.get(att.doc, {"en": att.doc})
        copy_txt = {
            "en": f"{att.copies} {'original' if att.original else 'photocopy' if att.copies == 1 else 'photocopies'}",
            "hi": f"{att.copies} {'मूल' if att.original else 'फोटोकॉपी'}",
        }
        items.append({
            "doc": att.doc,
            "label": _loc(label, lang),
            "copies": att.copies,
            "original": att.original,
            "instruction": _loc(copy_txt, lang),
            "note": _loc(att.note, lang) if att.note else "",
        })
    return items


def build_output_meta(template: FormTemplate, lang: str) -> dict[str, Any]:
    s = template.submit_to
    savings = max(s.tout_price - s.fee, 0)
    return {
        "submit_to": _loc(s.office, lang),
        "online_wall": s.online_wall,
        "online_wall_note": _loc(s.online_wall_note, lang) if s.online_wall else "",
        "fair_price": {
            "official_fee": s.fee,
            "tout_price": s.tout_price,
            "you_save": savings,
            "currency": "INR",
        },
    }
