"""All HTTP endpoints for the Sahayak flow."""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session as DBSession

from ..config import settings
from ..core import orchestrator as orch
from ..core import teachback as tb
from ..core.checklist import build_checklist, build_output_meta
from ..core.pdf import render_form_pdf
from ..core.pii import safe_log
from ..core.registry_helpers import form_or_scheme_form, load_schemes, scheme_for
from ..data.samples import PERSONAS, persona_documents
from ..db import AuditRow, SessionRow, TrackingRow, RejectionRow, get_db, utcnow
from ..schemas.core import Document
from ..schemas.flow import (
    AnswerRequest,
    CaptureRequest,
    ConsentRequest,
    CreateSessionRequest,
    ReferenceRequest,
    RejectionRequest,
    ResolveRequest,
    SelectFormRequest,
    VoiceASRRequest,
    VoiceTTSRequest,
)
from ..services.llm import get_llm
from ..services.storage import get_storage
from ..services.voice import LANGS, get_voice

router = APIRouter(prefix="/api")


# ───────────────────────────── helpers ──────────────────────────────────────
def _get_session(db: DBSession, sid: str) -> SessionRow:
    row = db.get(SessionRow, sid)
    if row is None:
        raise HTTPException(404, "Session not found")
    return row


def _audit(db: DBSession, sid: str, action: str, detail: dict[str, Any]) -> None:
    db.add(AuditRow(session_id=sid, action=action, detail=safe_log(detail)))


def _save(db: DBSession, row: SessionRow) -> None:
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(row, "data")
    row.updated_at = utcnow()
    db.commit()


# ───────────────────────────── meta ─────────────────────────────────────────
@router.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "grok": settings.grok_enabled, "ocr": settings.ocr_provider,
            "voice": settings.voice_provider}


@router.get("/meta")
def meta() -> dict[str, Any]:
    return {
        "languages": LANGS,
        "personas": [{"id": k, "label": v["label"], "asked_scheme": v["asked_scheme"]}
                     for k, v in PERSONAS.items()],
        "schemes": [{"id": s.id, "name": s.name, "category": s.category,
                     "summary": s.summary, "benefit": s.benefit} for s in load_schemes()],
    }


# ───────────────────────────── session lifecycle ────────────────────────────
@router.post("/session")
def create_session(req: CreateSessionRequest, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    sid = "s_" + uuid.uuid4().hex[:12]
    expires = utcnow() + dt.timedelta(seconds=settings.session_ttl_seconds)
    row = SessionRow(id=sid, owner=req.owner, language=req.language, state="capture",
                     data={"operator_mode": req.operator_mode, "spoken": {}, "resolutions": {}},
                     expires_at=expires)
    db.add(row)
    _audit(db, sid, "session_created", {"language": req.language, "operator": req.operator_mode})
    db.commit()
    return {"id": sid, "state": row.state, "language": row.language}


@router.get("/session/{sid}")
def get_session(sid: str, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = _get_session(db, sid)
    return {"id": row.id, "state": row.state, "language": row.language,
            "owner": row.owner, "data": row.data}


# ───────────────────────────── capture / extract ────────────────────────────
@router.post("/session/{sid}/capture")
def capture(sid: str, req: CaptureRequest, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = _get_session(db, sid)
    lang = row.language

    if req.persona:
        docs = persona_documents(req.persona)
        if not docs:
            raise HTTPException(400, f"Unknown persona {req.persona}")
        row.data["asked_scheme"] = PERSONAS[req.persona]["asked_scheme"]
    else:
        docs = [Document(**d.model_dump()) for d in req.documents]
        if req.asked_scheme:
            row.data["asked_scheme"] = req.asked_scheme

    orch.ingest_documents(row.data, docs, lang)
    row.state = row.data["state"]
    _audit(db, sid, "documents_read",
           {"count": len(docs), "types": [d.type.value for d in docs]})
    _save(db, row)
    return {
        "documents": [d.model_dump() for d in docs],
        "mismatches": row.data.get("mismatches", []),
        "recapture": row.data.get("recapture", []),
        "state": row.state,
    }


@router.post("/session/{sid}/resolve")
def resolve(sid: str, req: ResolveRequest, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = _get_session(db, sid)
    orch.apply_resolutions(row.data, req.resolutions)
    row.state = row.data["state"]
    _audit(db, sid, "mismatch_resolved", {"fields": list(req.resolutions.keys())})
    _save(db, row)
    return {"state": row.state, "resolutions": row.data["resolutions"]}


@router.post("/session/{sid}/answer")
def answer(sid: str, req: AnswerRequest, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = _get_session(db, sid)
    orch.apply_answers(row.data, req.answers)
    _audit(db, sid, "answers_given", {"fields": list(req.answers.keys())})
    _save(db, row)
    return {"state": row.state, "spoken_keys": list(row.data.get("spoken", {}).keys())}


# ───────────────────────────── reason / eligibility ─────────────────────────
@router.get("/session/{sid}/eligibility")
async def eligibility(sid: str, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = _get_session(db, sid)
    result = await orch.run_eligibility(row.data, row.language)
    row.state = row.data["state"]
    _audit(db, sid, "eligibility_computed",
           {"qualifies": [r["scheme_id"] for r in result["qualifies"]],
            "surprises": [r["scheme_id"] for r in result["surprises"]]})
    _save(db, row)
    return result


# ───────────────────────────── fill ─────────────────────────────────────────
@router.post("/session/{sid}/select-form")
async def select_form(sid: str, req: SelectFormRequest, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = _get_session(db, sid)
    try:
        result = await orch.select_form(row.data, req.scheme_id, row.language)
    except ValueError as e:
        raise HTTPException(400, str(e))
    row.state = row.data["state"]
    _audit(db, sid, "form_selected", {"scheme": req.scheme_id, "form": result["form_id"]})
    _save(db, row)
    return {**result, "state": row.state}


# ───────────────────────────── teach-back ───────────────────────────────────
@router.get("/session/{sid}/teachback")
async def teachback(sid: str, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = _get_session(db, sid)
    filled = row.data.get("filled", [])
    if not filled:
        raise HTTPException(400, "No filled form yet — select a form first")
    script = tb.build_teachback(filled, row.language)
    voice = get_voice()
    audio = await voice.synthesize(script["script"], row.language)
    row.state = "teach_back"
    _save(db, row)
    return {**script, "audio_b64": audio, "state": row.state}


# ───────────────────────────── consent + output ─────────────────────────────
@router.post("/session/{sid}/consent")
def consent(sid: str, req: ConsentRequest, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = _get_session(db, sid)
    if not req.confirmed:
        _audit(db, sid, "consent_declined", {"method": req.method})
        db.commit()
        raise HTTPException(409, "Consent not given — nothing produced (never auto-submits).")

    # Apply any operator edits before producing the PDF.
    filled = row.data.get("filled", [])
    for f in filled:
        if f["key"] in req.edits:
            f["value"] = req.edits[f["key"]]
            f["tier"] = "green"
            f["verified"] = True
            f["source"] = "confirmed by operator"

    scheme_id = row.data.get("selected_scheme")
    template = form_or_scheme_form(scheme_id)
    if template is None:
        raise HTTPException(400, "No form selected")
    lang = row.language
    checklist = build_checklist(template, lang)
    output_meta = build_output_meta(template, lang)

    pdf = render_form_pdf(
        title=template.title.get(lang, template.title.get("en")),
        subtitle=scheme_for(scheme_id).name.get(lang, scheme_for(scheme_id).name.get("en")),
        filled_fields=filled, checklist=checklist, output_meta=output_meta, lang=lang,
    )
    key = f"{sid}/{template.id}.pdf"
    pdf_url = get_storage().put_pdf(key, pdf)

    tracking_id = "t_" + uuid.uuid4().hex[:12]
    db.add(TrackingRow(id=tracking_id, owner=row.owner, scheme_id=scheme_id,
                       form_template_id=template.id, status="draft", pdf_url=pdf_url,
                       submitted_to=output_meta["submit_to"]))
    row.data["consent"] = {"method": req.method, "at": utcnow().isoformat()}
    row.data["pdf_url"] = pdf_url
    row.data["tracking_id"] = tracking_id
    row.state = "output"
    _audit(db, sid, "consent_given", {"method": req.method, "form": template.id})
    _audit(db, sid, "pdf_produced", {"form": template.id, "url": pdf_url})
    _save(db, row)
    return {"pdf_url": pdf_url, "checklist": checklist, "output": output_meta,
            "tracking_id": tracking_id, "state": row.state}


@router.get("/files/{sid}/{name}")
def get_file(sid: str, name: str) -> Response:
    data = get_storage().get_pdf(f"{sid}/{name}")
    if data is None:
        raise HTTPException(404, "File not found")
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{name}"'})


# ───────────────────────────── tracking + reminders ─────────────────────────
@router.get("/tracking")
def list_tracking(owner: str = "guest", db: DBSession = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.query(TrackingRow).filter(TrackingRow.owner == owner).all()
    return [{"id": r.id, "scheme_id": r.scheme_id, "form": r.form_template_id,
             "status": r.status, "reference_number": r.reference_number,
             "submitted_to": r.submitted_to, "pdf_url": r.pdf_url,
             "reminders": r.reminders} for r in rows]


@router.post("/tracking/{tid}/reference")
def set_reference(tid: str, req: ReferenceRequest, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    row = db.get(TrackingRow, tid)
    if row is None:
        raise HTTPException(404, "Tracking not found")
    row.reference_number = req.reference_number
    row.status = "submitted"
    if req.submitted_to:
        row.submitted_to = req.submitted_to
    # Schedule a simple follow-up reminder (e.g. 30 days).
    follow = (utcnow() + dt.timedelta(days=30)).date().isoformat()
    row.reminders = (row.reminders or []) + [
        {"on": follow, "text": "Check application status / follow up at the office."}
    ]
    db.commit()
    return {"id": tid, "status": row.status, "reference_number": row.reference_number,
            "reminders": row.reminders}


# ───────────────────────────── rejection learning loop ──────────────────────
@router.post("/rejections")
def add_rejection(req: RejectionRequest, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    db.add(RejectionRow(scheme_id=req.scheme_id, form_template_id=req.form_template_id,
                        state=req.state, reason=req.reason,
                        suggested_validation=req.suggested_validation))
    db.commit()
    return {"recorded": True}


# ───────────────────────────── voice ────────────────────────────────────────
@router.post("/voice/asr")
async def asr(req: VoiceASRRequest) -> dict[str, Any]:
    text = await get_voice().transcribe(req.audio_b64, req.language)
    return {"text": text}


@router.post("/voice/tts")
async def tts(req: VoiceTTSRequest) -> dict[str, Any]:
    audio = await get_voice().synthesize(req.text, req.language)
    return {"audio_b64": audio}


@router.get("/version")
def version() -> dict[str, Any]:
    """Build/version metadata for clients and uptime checks."""
    return {"app": "Sahayak", "version": "0.1.0", "api": "v1"}


@router.get("/schemes/search")
def search_schemes(q: str = "", lang: str = "en") -> dict[str, Any]:
    """Search the scheme KB by localized name / summary / benefit (case-insensitive)."""

    def _txt(v: Any) -> str:
        if isinstance(v, dict):
            return str(v.get(lang) or v.get("en") or next(iter(v.values()), ""))
        return str(v or "")

    needle = q.strip().lower()
    results = []
    for s in load_schemes():
        hay = " ".join(_txt(x) for x in (s.name, s.summary, s.benefit)).lower()
        if not needle or needle in hay:
            results.append(
                {"id": s.id, "name": _txt(s.name), "category": s.category, "summary": _txt(s.summary)}
            )
    return {"query": q, "count": len(results), "results": results}


@router.get("/health/deep")
def health_deep() -> dict[str, Any]:
    """Deep health: DB connectivity plus loaded knowledge-base counts."""
    from sqlalchemy import text

    from ..core.registry import load_form_templates
    from ..db import SessionLocal

    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {
        "ok": db_ok,
        "db": db_ok,
        "schemes": len(load_schemes()),
        "forms": len(load_form_templates()),
        "ocr": settings.ocr_provider,
        "voice": settings.voice_provider,
    }


@router.get("/session/{sid}/audit")
def session_audit(sid: str, db: DBSession = Depends(get_db)) -> dict[str, Any]:
    """Return the append-only audit trail for a session (DPDP evidence)."""
    row = db.get(SessionRow, sid)
    if row is None:
        raise HTTPException(404, "Session not found")
    entries = (
        db.query(AuditRow).filter(AuditRow.session_id == sid).order_by(AuditRow.at.asc()).all()
    )
    return {
        "session": sid,
        "count": len(entries),
        "entries": [
            {"at": e.at.isoformat(), "action": e.action, "detail": e.detail} for e in entries
        ],
    }


@router.get("/stats")
def stats() -> dict[str, Any]:
    """Aggregate counts across the knowledge-base and the database."""
    from ..core.registry import load_form_templates
    from ..db import SessionLocal

    with SessionLocal() as db:
        sessions = db.query(SessionRow).count()
        tracking = db.query(TrackingRow).count()
    return {
        "schemes": len(load_schemes()),
        "forms": len(load_form_templates()),
        "languages": len(LANGS),
        "sessions": sessions,
        "tracking": tracking,
    }
