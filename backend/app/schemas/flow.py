"""API request/response models for the session flow."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from .core import Document, ExtractedField


class CreateSessionRequest(BaseModel):
    language: str = "hi"
    owner: str = "guest"
    operator_mode: bool = False


class SessionView(BaseModel):
    id: str
    state: str
    language: str
    owner: str
    data: dict[str, Any] = Field(default_factory=dict)


class CaptureDocIn(BaseModel):
    """A document captured on-device: either pre-extracted fields (mock/demo or
    on-device ML Kit) or raw OCR text. Aadhaar full number must already be masked."""
    id: str
    type: str = "unknown"
    type_confidence: float = 1.0
    raw_text: str = ""
    ocr_quality: float = 1.0
    fields: list[ExtractedField] = Field(default_factory=list)


class CaptureRequest(BaseModel):
    persona: Optional[str] = None          # demo path: load a synthetic persona
    documents: list[CaptureDocIn] = Field(default_factory=list)
    asked_scheme: Optional[str] = None     # what the user came asking for


class CaptureResponse(BaseModel):
    documents: list[Document]
    mismatches: list[dict[str, Any]]
    recapture: list[dict[str, Any]]        # docs needing re-capture + hint
    state: str


class ResolveRequest(BaseModel):
    resolutions: dict[str, Any]            # {field: chosen_value}


class AnswerRequest(BaseModel):
    answers: dict[str, Any]                # {field_key: spoken_value}


class GapQuestion(BaseModel):
    key: str
    label: str
    question: str
    type: str = "text"
    options: list[str] = Field(default_factory=list)


class EligibilityView(BaseModel):
    qualifies: list[dict[str, Any]]
    needs_prerequisite: list[dict[str, Any]]
    surprises: list[dict[str, Any]]        # didn't ask, qualifies — the kicker
    dependencies: list[dict[str, Any]]
    all_results: list[dict[str, Any]]


class SelectFormRequest(BaseModel):
    scheme_id: str


class SelectFormResponse(BaseModel):
    form_id: str
    title: str
    filled: list[dict[str, Any]]
    review: list[dict[str, Any]]           # amber/red fields to check
    missing: list[GapQuestion]             # required-but-empty → ask by voice
    state: str


class ConsentRequest(BaseModel):
    confirmed: bool
    method: str = "voice"                  # voice | tap
    edits: dict[str, Any] = Field(default_factory=dict)   # operator corrections


class ConsentResponse(BaseModel):
    pdf_url: str
    checklist: list[dict[str, Any]]
    output: dict[str, Any]
    tracking_id: str
    state: str


class ReferenceRequest(BaseModel):
    reference_number: str
    submitted_to: str = ""


class RejectionRequest(BaseModel):
    scheme_id: str
    form_template_id: str
    state: str = ""
    reason: str
    suggested_validation: str = ""


class VoiceASRRequest(BaseModel):
    audio_b64: str
    language: str = "hi"


class VoiceTTSRequest(BaseModel):
    text: str
    language: str = "hi"
