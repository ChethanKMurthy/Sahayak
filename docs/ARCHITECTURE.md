# Sahayak — System Architecture

This document describes the MVP architecture and the reasoning behind it. For the growth path to
10M+ (1cr+) users, see [`SCALING.md`](SCALING.md).

---

## 1. Design principles

1. **The LLM explains; code decides.** Eligibility is a legal/financial determination. A deterministic
   rules-gate (plain Python over typed criteria) is the only thing allowed to output "you qualify."
   The LLM (Grok) extracts structure, drafts explanations, maps fields, and generates the next voice
   question — all *suggestions* that the rules-gate and the human confirm.
2. **Privacy is on-device, by construction.** Document detection, OCR quality-check, and PII masking
   happen on the device. Only masked, minimal text reaches the cloud. Aadhaar's full number never
   leaves the device and is never written to a database.
3. **Everything traces to a source.** Each value in a filled form carries provenance: which document
   (and which field on it) or which spoken answer (and timestamp) it came from, plus a confidence tier.
4. **Forms are data, not code.** A declarative DSL describes fields, types, validations, language, and
   source-mapping hints. New forms/states ship as JSON, no redeploy.
5. **Honest about limits.** Database-gated eligibility (PM-JAY/SECC) and online-only walls (biometrics,
   OTP, appointment booking) are *prepared up to the wall* and clearly handed off — never faked.

---

## 2. Component map

```
┌──────────────────────────── ON DEVICE (Flutter / Browser) ─────────────────────────────┐
│  Camera intake → Document detection & framing → OCR quality gate (ML Kit)               │
│  Voice capture (mic) → ASR                                                              │
│  ── PII MASKING (Aadhaar→last4, regex redaction) happens HERE, before egress ──         │
│  Local store (SQLite / IndexedDB) for offline-ready capture + fill queue                │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │  HTTPS (masked text + structured payloads only)
                                             ▼
┌──────────────────────────────── CLOUD (FastAPI on AWS) ──────────────────────────────────┐
│                                                                                          │
│   API layer  ──►  Orchestrator (per-session state machine)                               │
│                      │                                                                   │
│        ┌─────────────┼───────────────────────────────────────────────┐                  │
│        ▼             ▼                  ▼                ▼             ▼                  │
│  Extraction     Eligibility       Consistency       Form-fill     Provenance             │
│  service        engine            engine            (DSL mapper)   ledger                 │
│  (Grok +        (RULES-GATE,      (fuzzy name/      (template +    (every field's         │
│   Textract)      deterministic)    DOB/addr match)   source map)    origin + tier)        │
│        │             │                  │                │             │                  │
│        ▼             ▼                  ▼                ▼             ▼                  │
│  ┌────────────────────────────────────────────────────────────────────────────────┐    │
│  │  Adapters (swappable, each with a mock): Grok · Textract · Transcribe · Polly ·  │    │
│  │  Bhashini · Cognito · S3 · SNS                                                    │    │
│  └────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
│   PDF generator (clean official-style render from DSL) → S3                              │
│   Voice teach-back (TTS read-back) → consent capture → audit trail                       │
│                                                                                          │
│   Postgres: sessions(ephemeral) · applicants · households · documents(meta only) ·       │
│             field_values+provenance · schemes · form_templates · audit_log ·             │
│             tracking/reminders · rejection_feedback                                       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The end-to-end flow (state machine)

The orchestrator drives a session through these states; each is resumable (offline-ready):

`CAPTURE → EXTRACT → CONSISTENCY_CHECK → CONVERSE(gap-fill) → REASON(eligibility) →`
`SELECT_FORM → FILL → TEACH_BACK(consent) → OUTPUT(pdf+checklist) → TRACK`

- **CAPTURE** — device frames each document, classifies type (Aadhaar/ration/marksheet/land-record/
  blank target form), runs an OCR quality gate, prompts re-capture on glare/low confidence.
- **EXTRACT** — per document: OCR text → Grok structured extraction → typed fields with confidence.
  Aadhaar already masked on-device.
- **CONSISTENCY_CHECK** — compare shared fields (name, DOB, address) across documents; surface
  mismatches with a "which should the form use?" resolution.
- **CONVERSE** — the orchestrator computes which fields are still missing/low-confidence for the
  candidate forms and asks *only those*, as generated voice questions in the user's language.
- **REASON** — the deterministic rules-gate evaluates every scheme's hard criteria over the known
  facts; Grok writes the plain-language "why." Dependency-chains and the entitlement graph are
  computed here.
- **FILL** — DSL mapper binds facts → form fields using source-mapping hints; each binding records
  provenance + confidence tier.
- **TEACH_BACK** — TTS reads the filled form aloud; amber/red fields highlighted; user confirms by
  voice/tap; consent written to audit log. **Nothing is produced before consent.**
- **OUTPUT** — clean PDF rendered from the DSL + an attachment checklist + where/how to submit.
- **TRACK** — reference number captured; reminders scheduled.

---

## 4. The deterministic rules-gate (the part that keeps us safe)

Each scheme declares hard criteria as typed predicates evaluated in code:

```python
Criterion(field="age",        op=">=", value=60)
Criterion(field="income",     op="<=", value=ceiling_for(state))
Criterion(field="disability", op=">=", value=40)            # percent
```

The engine returns one of: **QUALIFIES**, **DOES_NOT_QUALIFY**, **NEEDS_INFO** (a required fact is
missing), or **NEEDS_PREREQUISITE** (a required document is itself an application — feeds the
dependency-chain). The LLM is given the *result* and asked only to phrase the "why." It is never
asked "does this person qualify?".

See `backend/app/engine/` for the implementation.

---

## 5. The form-template DSL

A form is a versioned JSON document. Abbreviated example:

```jsonc
{
  "id": "voter-id-form6", "version": "2024.1", "title": {"en": "...", "hi": "..."},
  "jurisdiction": {"country": "IN", "state": "*"},
  "fields": [
    { "key": "applicant_name", "type": "name", "required": true,
      "label": {"en": "Full name", "hi": "पूरा नाम"},
      "source_hints": ["aadhaar.name", "marksheet.name"],   // where to look first
      "validations": ["nonEmpty", "maxLen:99"] },
    { "key": "dob", "type": "date", "required": true,
      "source_hints": ["aadhaar.dob"], "validations": ["pastDate", "age>=18"] }
  ],
  "attachments": [ {"doc": "aadhaar", "copies": 1}, {"doc": "passport_photo", "copies": 1} ],
  "submit_to": {"office": "Electoral Registration Officer", "online_wall": false}
}
```

Source-mapping hints let the FILL stage bind facts deterministically before falling back to the LLM
mapper. `attachments` drives the checklist generator. `online_wall` tells the app where to hand off.

---

## 6. Provenance & confidence tiers

Every filled value stores: `{value, source_type, source_ref, confidence_tier, captured_at}`.

- **Green** — read directly from a document *and* cross-verified across documents.
- **Amber** — inferred, or single-source with low OCR confidence.
- **Red** — user-spoken and unverifiable (e.g. income, "no existing connection").

The operator/teach-back step only needs to review **amber + red**, which is what makes
human-in-the-loop fast instead of pointless.

---

## 7. Adapter pattern (runs with zero credentials)

Every external service implements a small Python `Protocol` with two concrete classes: a real client
and a `Mock*` returning realistic canned data. Selection is by env var. This is why `uvicorn` boots
and the full flow demos before any key exists, and why swapping Grok→Gemini or Textract→Vision is a
one-file change. See `backend/app/services/`.

---

## 8. Data model (Postgres) — privacy-shaped

- `sessions` — ephemeral, TTL-expired; holds working state.
- `documents` — **metadata + provenance only**; raw images live transiently in S3 with lifecycle
  expiry, never the full Aadhaar number.
- `field_values` — value + provenance + tier, linked to applicant.
- `applicants`, `households`, `household_members` — the relationship graph for household schemes.
- `schemes`, `form_templates` — versioned reference data (seeded from `/shared`).
- `audit_log` — append-only: what was read, asked, confirmed, by whom, when (DPDP evidence).
- `tracking`, `reminders` — post-submission follow-up.
- `rejection_feedback` — the learning loop's raw input.

---

## 9. Why these choices (trade-offs)

- **FastAPI over Node** for the backend: the rules engine, document pipelines, and data work are
  cleaner in Python; the web app keeps its own TS world via a thin typed client.
- **Flutter over native**: one codebase reaches a polished Android app now and iOS/web later, with
  excellent animation and a strong on-device ML/camera story — the privacy claim survives.
- **Deterministic gate over LLM eligibility**: correctness, auditability, and legal safety. The LLM's
  value is language and mapping, where mistakes are recoverable and human-reviewed.
