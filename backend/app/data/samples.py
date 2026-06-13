"""Synthetic sample documents (clearly SAMPLE data, no real PII).

These power the demo and the test suite: each persona is a set of documents with
typed fields, so the full capture→track flow runs deterministically without a
camera or any OCR keys. Real camera uploads go through the OCR + LLM extractor
instead; these fixtures are the offline/demo path.
"""
from __future__ import annotations

from ..schemas.core import Document, DocumentType, ExtractedField


def _doc(doc_id: str, dtype: DocumentType, fields: dict, quality: float = 0.97) -> Document:
    return Document(
        id=doc_id,
        type=dtype,
        type_confidence=0.98,
        ocr_quality=quality,
        raw_text=f"[SAMPLE {dtype.value}] " + " ".join(f"{k}:{v}" for k, v in fields.items()),
        fields=[ExtractedField(key=k, value=v, ocr_confidence=quality) for k, v in fields.items()],
    )


# Each persona: id -> {label, asked_scheme, documents[]}
PERSONAS: dict[str, dict] = {
    "ramesh": {
        "label": {"en": "Ramesh, 67 — came to renew ration card", "hi": "रमेश, 67 — राशन कार्ड नवीनीकरण के लिए"},
        "asked_scheme": "nfsa-ration-card",
        "documents": [
            _doc("d-aadhaar", DocumentType.AADHAAR, {
                "name": "Ramesh Kumar", "dob": "1958-03-12", "gender": "male",
                "address": "Plot 4, Anjanapura, Bengaluru, Karnataka", "father_name": "Late Shankar",
                "aadhaar_last4": "4821"}),
            _doc("d-ration", DocumentType.RATION_CARD, {
                "name": "Ramesh Kumar", "address": "Plot 4, Anjanapura, Bengaluru, Karnataka",
                "bpl": True, "household_size": 4}),
            _doc("d-bank", DocumentType.BANK_PASSBOOK, {
                "name": "Ramesh Kumar", "bank_account": "3041xxxx9921", "ifsc": "SBIN0004512"}),
        ],
    },
    "lakshmi": {
        "label": {"en": "Lakshmi, 52 — widow, BPL household", "hi": "लक्ष्मी, 52 — विधवा, बीपीएल परिवार"},
        "asked_scheme": "nsap-widow-pension",
        "documents": [
            _doc("d-aadhaar", DocumentType.AADHAAR, {
                "name": "Lakshmi Devi", "dob": "1973-07-21", "gender": "female",
                "address": "House 22, Hubballi, Karnataka", "aadhaar_last4": "1190"}),
            _doc("d-ration", DocumentType.RATION_CARD, {
                "name": "Lakshmi Devi", "address": "House 22, Hubballi, Karnataka",
                "bpl": True, "household_size": 3}),
            _doc("d-death", DocumentType.DEATH_CERT, {
                "name": "Lakshmi Devi", "marital_status": "widow"}),
            _doc("d-bank", DocumentType.BANK_PASSBOOK, {
                "name": "Lakshmi Devi", "bank_account": "5512xxxx0034", "ifsc": "KARB0000234"}),
        ],
    },
    "priya": {
        "label": {"en": "Priya, 17 — SC student, low income", "hi": "प्रिया, 17 — SC छात्रा, कम आय"},
        "asked_scheme": "post-matric-scholarship",
        "documents": [
            _doc("d-aadhaar", DocumentType.AADHAAR, {
                "name": "Priya Nayak", "dob": "2007-11-02", "gender": "female",
                "address": "Ward 9, Mangaluru, Karnataka", "father_name": "Suresh Nayak",
                "aadhaar_last4": "7763"}),
            _doc("d-marksheet", DocumentType.MARKSHEET, {
                "name": "Priya Nayak", "father_name": "Suresh Nayak", "dob": "2007-11-02",
                "marks_percent": 82, "course_level": "class11"}),
            _doc("d-caste", DocumentType.CASTE_CERT, {
                "name": "Priya Nayak", "caste_category": "sc"}),
            _doc("d-income", DocumentType.INCOME_CERT, {
                "name": "Priya Nayak", "income": 140000}, quality=0.78),
            _doc("d-bank", DocumentType.BANK_PASSBOOK, {
                "name": "Priya Nayak", "bank_account": "8890xxxx1145", "ifsc": "CNRB0001882"}),
        ],
    },
    "priya_missing_certs": {
        "label": {"en": "Priya — wants scholarship but has no income/caste certificate (dependency-chain demo)", "hi": "प्रिया — छात्रवृत्ति चाहती है पर आय/जाति प्रमाण नहीं (निर्भरता-श्रृंखला डेमो)"},
        "asked_scheme": "post-matric-scholarship",
        "documents": [
            _doc("d-aadhaar", DocumentType.AADHAAR, {
                "name": "Priya Nayak", "dob": "2007-11-02", "gender": "female",
                "address": "Ward 9, Mangaluru, Karnataka", "father_name": "Suresh Nayak",
                "aadhaar_last4": "7763"}),
            _doc("d-marksheet", DocumentType.MARKSHEET, {
                "name": "Priya Nayak", "marks_percent": 82, "course_level": "class11"}),
            _doc("d-bank", DocumentType.BANK_PASSBOOK, {
                "name": "Priya Nayak", "bank_account": "8890xxxx1145", "ifsc": "CNRB0001882"}),
        ],
    },
    "imran": {
        "label": {"en": "Imran — name spelled differently across documents (consistency-engine demo)", "hi": "इमरान — दस्तावेज़ों में नाम अलग वर्तनी (संगति-इंजन डेमो)"},
        "asked_scheme": "voter-id-form6",
        "documents": [
            _doc("d-aadhaar", DocumentType.AADHAAR, {
                "name": "Mohd Imran", "dob": "2004-01-15", "gender": "male",
                "address": "12 Frazer Town, Bengaluru, Karnataka", "father_name": "Abdul Razak",
                "aadhaar_last4": "5567", "citizenship": "indian"}),
            _doc("d-marksheet", DocumentType.MARKSHEET, {
                "name": "Mohammad Imran", "dob": "2004-01-15", "course_level": "class12"}),
        ],
    },
}


def persona_documents(persona_id: str) -> list[Document]:
    p = PERSONAS.get(persona_id)
    return list(p["documents"]) if p else []
