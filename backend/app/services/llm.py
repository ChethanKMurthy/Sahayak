"""Reasoning-layer adapter (Grok / xAI).

The LLM does three jobs — structured extraction, phrasing the eligibility "why",
and generating the next voice gap-question. It NEVER decides eligibility (that is
the deterministic rules-gate). Falls back to a deterministic Mock when no key set.
"""
from __future__ import annotations

import json
from typing import Any, Optional, Protocol

import httpx

from ..config import settings
from ..schemas.core import EligibilityResult, Scheme


class LLMAdapter(Protocol):
    async def extract_fields(self, raw_text: str, doc_type: str) -> list[dict[str, Any]]: ...
    async def explain(self, scheme: Scheme, result: EligibilityResult, lang: str) -> str: ...
    async def gap_question(self, field_key: str, label: str, lang: str) -> str: ...


# ─────────────────────────────── Mock ───────────────────────────────────────
_GAP_TEMPLATES = {
    "hi": "क्या आप {label} बता सकते हैं?",
    "en": "Could you tell me your {label}?",
    "kn": "ನಿಮ್ಮ {label} ಹೇಳಬಹುದೇ?",
    "ta": "உங்கள் {label} சொல்ல முடியுமா?",
    "te": "మీ {label} చెప్పగలరా?",
    "mr": "तुम्ही {label} सांगू शकता का?",
    "bn": "আপনি কি {label} বলতে পারেন?",
}


class MockLLM:
    """Deterministic stand-in. Extraction returns nothing (the synthetic sample
    fixtures already carry typed fields); explanation/questions are templated."""

    async def extract_fields(self, raw_text: str, doc_type: str) -> list[dict[str, Any]]:
        return []

    async def explain(self, scheme: Scheme, result: EligibilityResult, lang: str) -> str:
        name = scheme.name.get(lang, scheme.name.get("en", scheme.id))
        passed = [
            c.criterion.description.get(lang, c.criterion.description.get("en", c.criterion.field))
            for c in result.criterion_results
            if c.passed is True
        ]
        if result.status.value == "qualifies":
            reasons = "; ".join(passed) if passed else ""
            lead = {"hi": f"आप {name} के लिए पात्र हैं", "en": f"You qualify for {name}"}.get(
                lang, f"You qualify for {name}"
            )
            return f"{lead}. {reasons}".strip(". ") + "."
        if result.status.value == "needs_prerequisite":
            return {
                "hi": f"{name} के लिए पहले एक ज़रूरी दस्तावेज़ चाहिए।",
                "en": f"For {name} you first need a prerequisite document.",
            }.get(lang, f"For {name} you first need a prerequisite document.")
        if result.status.value == "needs_info":
            missing = ", ".join(result.missing_facts)
            return {
                "hi": f"{name} की जाँच के लिए और जानकारी चाहिए: {missing}.",
                "en": f"To check {name}, we need a bit more information: {missing}.",
            }.get(lang, f"To check {name}, we need more info: {missing}.")
        return {
            "hi": f"फ़िलहाल आप {name} के लिए पात्र नहीं दिखते।",
            "en": f"You don't appear to qualify for {name} right now.",
        }.get(lang, f"You don't appear to qualify for {name} right now.")

    async def gap_question(self, field_key: str, label: str, lang: str) -> str:
        return _GAP_TEMPLATES.get(lang, _GAP_TEMPLATES["en"]).format(label=label)


# ─────────────────────────────── Grok (real) ────────────────────────────────
_EXTRACT_SYS = (
    "You extract structured fields from Indian government document OCR text. "
    "Return ONLY a JSON array of {key, value, ocr_confidence}. Use snake_case keys "
    "from this set when present: name, father_name, dob, gender, address, "
    "aadhaar_last4, caste_category, income, marks_percent, course_level, "
    "bank_account, ifsc, land_area, owns_cultivable_land, bpl. Never output the "
    "full 12-digit Aadhaar number — only the last 4 as aadhaar_last4."
)


class GrokLLM:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.grok_base_url,
            headers={"Authorization": f"Bearer {settings.grok_api_key}"},
            timeout=30.0,
        )

    async def _chat(self, system: str, user: str, large: bool = False) -> str:
        model = settings.grok_model_large if large else settings.grok_model
        resp = await self._client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def extract_fields(self, raw_text: str, doc_type: str) -> list[dict[str, Any]]:
        try:
            content = await self._chat(_EXTRACT_SYS, f"Document type: {doc_type}\n\n{raw_text}")
            start, end = content.find("["), content.rfind("]")
            if start >= 0 and end > start:
                return json.loads(content[start : end + 1])
        except (httpx.HTTPError, json.JSONDecodeError, KeyError):
            pass
        return []

    async def explain(self, scheme: Scheme, result: EligibilityResult, lang: str) -> str:
        # Hand the LLM the DECISION; ask only for phrasing. It cannot change it.
        facts = [
            {"criterion": c.criterion.field, "passed": c.passed, "actual": c.actual}
            for c in result.criterion_results
        ]
        prompt = (
            f"The deterministic rules engine decided status='{result.status.value}' for the "
            f"scheme '{scheme.name.get('en')}'. Criteria outcomes: {json.dumps(facts)}. "
            f"Write ONE short, warm sentence in language code '{lang}' explaining this to a "
            f"citizen. Do not change the decision; only explain it."
        )
        try:
            return (await self._chat("You are a kind government-scheme assistant.", prompt)).strip()
        except httpx.HTTPError:
            return await MockLLM().explain(scheme, result, lang)

    async def gap_question(self, field_key: str, label: str, lang: str) -> str:
        prompt = (
            f"Ask the citizen for their '{label}' in one short, polite spoken sentence in "
            f"language code '{lang}'. Output only the sentence."
        )
        try:
            return (await self._chat("You are a kind government-scheme assistant.", prompt)).strip()
        except httpx.HTTPError:
            return await MockLLM().gap_question(field_key, label, lang)


def get_llm() -> LLMAdapter:
    return GrokLLM() if settings.grok_enabled else MockLLM()
