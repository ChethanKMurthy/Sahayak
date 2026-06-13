"""Core domain models shared across the whole backend.

These mirror the concepts in docs/ARCHITECTURE.md: confidence tiers, provenance,
the form-template DSL, extraction output, and eligibility results.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─────────────────────────── Confidence & provenance ────────────────────────
class ConfidenceTier(str, Enum):
    """Drives the color-coding and what the human must review."""
    GREEN = "green"   # read directly AND cross-verified across documents
    AMBER = "amber"   # inferred, or single-source / low OCR confidence
    RED = "red"       # user-spoken and unverifiable (income, self-declarations)


class SourceType(str, Enum):
    DOCUMENT = "document"      # came from an OCR'd document field
    SPOKEN = "spoken"          # user said it during the voice conversation
    INFERRED = "inferred"      # derived (e.g. age from DOB)
    DEFAULT = "default"        # template default / constant


class Provenance(BaseModel):
    """Where a value came from — tap a field in the UI to see this."""
    source_type: SourceType
    source_ref: str = ""               # e.g. "aadhaar.dob" or "spoken@00:42"
    document_id: Optional[str] = None
    ocr_confidence: Optional[float] = None   # 0..1 when from OCR
    captured_at: Optional[str] = None        # ISO timestamp for spoken answers
    note: str = ""                           # human-readable origin string


class FieldValue(BaseModel):
    """A single resolved fact about an applicant, with full provenance."""
    key: str
    value: Any = None
    tier: ConfidenceTier = ConfidenceTier.AMBER
    provenance: Provenance
    verified: bool = False             # set true after human/teach-back review

    def origin_phrase(self, lang: str = "en") -> str:
        return self.provenance.note or self.provenance.source_ref


# ─────────────────────────────── Documents ──────────────────────────────────
class DocumentType(str, Enum):
    AADHAAR = "aadhaar"
    RATION_CARD = "ration_card"
    MARKSHEET = "marksheet"
    LAND_RECORD = "land_record"
    INCOME_CERT = "income_cert"
    CASTE_CERT = "caste_cert"
    DOMICILE_CERT = "domicile_cert"
    DISABILITY_CERT = "disability_cert"   # UDID
    DEATH_CERT = "death_cert"
    BANK_PASSBOOK = "bank_passbook"
    PASSPORT_PHOTO = "passport_photo"
    BLANK_FORM = "blank_form"
    UNKNOWN = "unknown"


class ExtractedField(BaseModel):
    key: str
    value: Any
    ocr_confidence: float = 1.0


class Document(BaseModel):
    id: str
    type: DocumentType
    type_confidence: float = 1.0
    raw_text: str = ""
    fields: list[ExtractedField] = Field(default_factory=list)
    ocr_quality: float = 1.0           # 0..1; low → assisted re-capture prompt
    recapture_hint: Optional[str] = None  # e.g. "glare on the card — tilt it up"


# ──────────────────────── Cross-document consistency ────────────────────────
class Mismatch(BaseModel):
    field: str                          # e.g. "name"
    values: list[dict[str, Any]]        # [{value, document_id, doc_type}]
    question: dict[str, str]            # localized "which should the form use?"
    resolved_value: Optional[Any] = None


# ─────────────────────────── Form-template DSL ──────────────────────────────
class FieldType(str, Enum):
    TEXT = "text"
    NAME = "name"
    DATE = "date"
    NUMBER = "number"
    INTEGER = "integer"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    ENUM = "enum"
    PHONE = "phone"
    AADHAAR_LAST4 = "aadhaar_last4"
    ADDRESS = "address"
    IFSC = "ifsc"


class FormField(BaseModel):
    key: str
    type: FieldType = FieldType.TEXT
    required: bool = False
    label: dict[str, str] = Field(default_factory=dict)     # localized
    options: list[str] = Field(default_factory=list)        # for ENUM
    source_hints: list[str] = Field(default_factory=list)   # ["aadhaar.name", ...]
    validations: list[str] = Field(default_factory=list)    # ["nonEmpty","age>=18"]
    self_declared: bool = False         # forces RED tier (e.g. income)


class Attachment(BaseModel):
    doc: str                            # DocumentType value
    copies: int = 1
    original: bool = False
    note: dict[str, str] = Field(default_factory=dict)


class SubmitInfo(BaseModel):
    office: dict[str, str] = Field(default_factory=dict)
    online_wall: bool = False
    online_wall_note: dict[str, str] = Field(default_factory=dict)
    fee: float = 0.0                    # official fee in ₹ (fair-price meter)
    tout_price: float = 0.0             # typical tout charge in ₹


class FormTemplate(BaseModel):
    id: str
    version: str
    scheme_id: str                      # links to a Scheme in the KB
    title: dict[str, str]
    jurisdiction: dict[str, str] = Field(default_factory=dict)
    fields: list[FormField] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    submit_to: SubmitInfo = Field(default_factory=SubmitInfo)


# ─────────────────────────── Eligibility (rules-gate) ───────────────────────
class Op(str, Enum):
    GE = ">="
    LE = "<="
    GT = ">"
    LT = "<"
    EQ = "=="
    NE = "!="
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    TRUE = "is_true"


class Criterion(BaseModel):
    field: str
    op: Op
    value: Any = None
    description: dict[str, str] = Field(default_factory=dict)  # localized "why"


class Scheme(BaseModel):
    id: str
    name: dict[str, str]
    category: str                       # pension | scholarship | identity | ...
    summary: dict[str, str] = Field(default_factory=dict)
    criteria: list[Criterion] = Field(default_factory=list)
    household_scheme: bool = False
    requires_documents: list[str] = Field(default_factory=list)
    # documents that are themselves applications → dependency-chain
    prerequisite_schemes: list[str] = Field(default_factory=list)
    form_template_id: Optional[str] = None
    benefit: dict[str, str] = Field(default_factory=dict)  # localized payoff line
    # Fields that must be KNOWN before this scheme is surfaced to a user who did
    # not ask for it (avoids e.g. suggesting disability pension to everyone).
    discovery_gate: list[str] = Field(default_factory=list)


class EligibilityStatus(str, Enum):
    QUALIFIES = "qualifies"
    DOES_NOT_QUALIFY = "does_not_qualify"
    NEEDS_INFO = "needs_info"                 # a required fact is missing
    NEEDS_PREREQUISITE = "needs_prerequisite" # a prerequisite doc/scheme missing


class CriterionResult(BaseModel):
    criterion: Criterion
    passed: Optional[bool]              # None = unknown (missing fact)
    actual: Any = None


class EligibilityResult(BaseModel):
    scheme_id: str
    status: EligibilityStatus
    score: float = 0.0                  # ranking score for discovery
    why: dict[str, str] = Field(default_factory=dict)   # localized explanation
    criterion_results: list[CriterionResult] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    user_asked_for_it: bool = False     # vs surfaced by discovery
