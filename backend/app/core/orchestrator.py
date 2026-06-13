"""Session orchestrator: the state machine that drives capture → extract →
consistency → converse → reason → fill → teach-back → output → track.

Works on a plain session-data dict (persisted as JSON on SessionRow) so the whole
flow is resumable and offline-friendly. Pure-deterministic steps are sync; steps
that phrase things via the LLM are async.
"""
from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

from ..engine.consistency import detect_mismatches
from ..engine.discovery import run_discovery
from ..engine.facts import build_fact_map
from ..engine.provenance import build_field_values
from ..schemas.core import Document, EligibilityStatus, FieldValue
from ..services.llm import get_llm
from . import checklist as checklist_mod
from . import fill as fill_mod
from .pii import scrub_fields
from .registry_helpers import all_schemes, form_for, form_or_scheme_form, scheme_for


# ─────────────────────────── document ingestion ─────────────────────────────
def ingest_documents(data: dict[str, Any], docs: list[Document], lang: str) -> dict[str, Any]:
    # Mask any PII that slipped through before storing.
    stored = []
    for d in docs:
        masked = scrub_fields({f.key: f.value for f in d.fields})
        d.fields = [f for f in d.fields if f.key in masked]
        for f in d.fields:
            f.value = masked.get(f.key, f.value)
        stored.append(d.model_dump())
    data["documents"] = stored

    # Assisted re-capture: which docs need another shot.
    recapture = [
        {"id": d.id, "type": d.type.value, "hint": d.recapture_hint or
         "Image is unclear — reposition the document and avoid glare."}
        for d in docs if d.ocr_quality < 0.6
    ]
    data["recapture"] = recapture

    # Cross-document consistency.
    mismatches = detect_mismatches(docs, lang)
    data["mismatches"] = [m.model_dump() for m in mismatches]
    data["state"] = "consistency_check" if mismatches else "converse"
    return data


def load_documents(data: dict[str, Any]) -> list[Document]:
    return [Document(**d) for d in data.get("documents", [])]


# ─────────────────────────── fact resolution ────────────────────────────────
def compute_field_values(data: dict[str, Any]) -> list[FieldValue]:
    docs = load_documents(data)
    spoken = data.get("spoken", {})
    resolutions = data.get("resolutions", {})
    # Fields agreeing across ≥2 docs are cross-verified → eligible for green.
    cross: set[str] = set()
    seen: dict[str, Any] = {}
    counts: dict[str, int] = {}
    for d in docs:
        for f in d.fields:
            counts[f.key] = counts.get(f.key, 0) + 1
    cross = {k for k, c in counts.items() if c >= 2}
    return build_field_values(docs, spoken, resolutions, cross)


def available_document_types(data: dict[str, Any]) -> set[str]:
    return {d.type.value for d in load_documents(data)}


# ─────────────────────────── eligibility / discovery ────────────────────────
async def run_eligibility(data: dict[str, Any], lang: str) -> dict[str, Any]:
    fvs = compute_field_values(data)
    facts = build_fact_map(fvs)
    docs_avail = available_document_types(data)
    asked = {data.get("asked_scheme")} if data.get("asked_scheme") else set()

    graph = run_discovery(all_schemes(), facts, docs_avail, asked)
    llm = get_llm()

    async def decorate(res, with_llm: bool) -> dict[str, Any]:
        # Only call the LLM for schemes we actually surface — explaining all ~12
        # (and re-explaining surprises) wastes latency + LLM rate-limit budget.
        scheme = scheme_for(res.scheme_id)
        why = await llm.explain(scheme, res, lang) if with_llm else ""
        return {
            **res.model_dump(),
            "scheme_name": scheme.name.get(lang, scheme.name.get("en")),
            "category": scheme.category,
            "benefit": scheme.benefit.get(lang, scheme.benefit.get("en", "")),
            "why": why,
            "form_template_id": scheme.form_template_id,
        }

    # Certificates are enablers (everyone "qualifies"); keep them out of the
    # headline benefit lists and surface them only as their own bucket / as
    # dependency targets, so the entitlement graph stays meaningful.
    def is_cert(scheme_id: str) -> bool:
        s = scheme_for(scheme_id)
        return bool(s and s.category == "certificate")

    def gated_out(scheme_id: str) -> bool:
        """Don't surface a scheme to a user who didn't ask unless its defining
        facts are known (e.g. don't suggest disability pension to everyone)."""
        if scheme_id in asked:
            return False
        s = scheme_for(scheme_id)
        return bool(s and any(g not in facts for g in s.discovery_gate))

    def is_surfaced(res) -> bool:
        if gated_out(res.scheme_id):
            return False
        if is_cert(res.scheme_id):
            return res.status == EligibilityStatus.QUALIFIES
        return res.status in (EligibilityStatus.QUALIFIES, EligibilityStatus.NEEDS_PREREQUISITE)

    # Decorate every result once; the LLM explains only surfaced schemes,
    # and all those explanations run concurrently.
    decorated = await asyncio.gather(
        *(decorate(res, with_llm=is_surfaced(res)) for res in graph.results)
    )

    # Keep the buckets DISJOINT: what the user came for (qualifies / needs_prereq)
    # vs. the bonus discoveries they didn't ask about (surprises — the kicker).
    # If they asked for nothing (e.g. camera path), nothing is a "surprise".
    has_asked = bool(asked)
    qualifies, needs_prereq, surprises, certificates = [], [], [], []
    all_results = decorated
    for res, dec in zip(graph.results, decorated):
        if not is_surfaced(res):
            continue
        if is_cert(res.scheme_id):
            certificates.append(dec)
        elif has_asked and not res.user_asked_for_it:
            surprises.append(dec)
        elif res.status == EligibilityStatus.QUALIFIES:
            qualifies.append(dec)
        elif res.status == EligibilityStatus.NEEDS_PREREQUISITE:
            needs_prereq.append(dec)

    deps = []
    for node in graph.dependencies:
        if gated_out(node.scheme_id):
            continue
        scheme = scheme_for(node.scheme_id)
        deps.append({
            "scheme_id": node.scheme_id,
            "scheme_name": scheme.name.get(lang, scheme.name.get("en")),
            "needs": [
                {"scheme_id": s, "scheme_name": scheme_for(s).name.get(lang, scheme_for(s).name.get("en"))}
                for s in node.needs if scheme_for(s)
            ],
            "needs_documents": node.needs_documents,
        })

    data["eligibility"] = {
        "qualifies": qualifies, "needs_prerequisite": needs_prereq,
        "surprises": surprises, "certificates": certificates,
        "dependencies": deps, "all_results": all_results,
    }
    data["state"] = "reason"
    return data["eligibility"]


# ─────────────────────────── form fill ──────────────────────────────────────
async def select_form(data: dict[str, Any], scheme_id: str, lang: str) -> dict[str, Any]:
    template = form_or_scheme_form(scheme_id)
    if template is None:
        raise ValueError(f"No form template for scheme {scheme_id}")

    fvs = compute_field_values(data)
    filled = fill_mod.fill_form(template, fvs, lang)
    review = fill_mod.fields_to_review(filled)
    missing = fill_mod.missing_required(filled)

    llm = get_llm()
    gap_questions = []
    for f in missing:
        field = next((ff for ff in template.fields if ff.key == f["key"]), None)
        q = await llm.gap_question(f["key"], f["label"], lang)
        gap_questions.append({
            "key": f["key"], "label": f["label"], "question": q,
            "type": field.type.value if field else "text",
            "options": field.options if field else [],
        })

    data["selected_scheme"] = scheme_id
    data["selected_form"] = template.id
    data["filled"] = filled
    data["state"] = "fill"
    return {
        "form_id": template.id,
        "title": template.title.get(lang, template.title.get("en")),
        "filled": filled, "review": review, "missing": gap_questions,
    }


def apply_answers(data: dict[str, Any], answers: dict[str, Any]) -> None:
    spoken = data.get("spoken", {})
    spoken.update({k: v for k, v in answers.items() if v not in (None, "")})
    data["spoken"] = spoken


def apply_resolutions(data: dict[str, Any], resolutions: dict[str, Any]) -> None:
    res = data.get("resolutions", {})
    res.update(resolutions)
    data["resolutions"] = res
    # Mark mismatches resolved.
    for m in data.get("mismatches", []):
        if m["field"] in resolutions:
            m["resolved_value"] = resolutions[m["field"]]
    data["state"] = "converse"
