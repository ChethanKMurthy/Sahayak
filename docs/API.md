# Sahayak API reference

Base URL: `/api` (the web app proxies `/api/*` to the backend, so the browser stays same-origin).
All payloads are JSON unless noted. Sessions are ephemeral and identified by `sid`.

## Meta & health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness + provider modes (`grok`, `ocr`, `voice`). |
| GET | `/health/deep` | DB connectivity + loaded scheme/form counts. |
| GET | `/version` | App name + version. |
| GET | `/meta` | Languages, demo personas, and the scheme catalog. |
| GET | `/stats` | Aggregate KB + database counts. |
| GET | `/schemes/search?q=&lang=` | Search the scheme catalog. |
| GET | `/fair-price/{scheme_id}` | Official fee vs. typical tout price. |

## Session lifecycle

| Method | Path | Description |
|---|---|---|
| POST | `/session` | Create a session. Body: `{ "language": "hi" }` → `{ "id": "s_…" }`. |
| GET | `/session/{sid}` | Fetch current session state. |
| POST | `/session/{sid}/capture` | Ingest documents. Body: `{ "persona": "ramesh" }` (demo) or document payloads. |
| POST | `/session/{sid}/resolve` | Resolve a consistency mismatch. Body: `{ "resolutions": { field: value } }`. |
| GET | `/session/{sid}/eligibility` | Run the rules-gate → `qualifies` / `needs_prerequisite` / `surprises` / `dependencies`. |
| POST | `/session/{sid}/select-form` | Pick a scheme/form. Body: `{ "scheme_id": "…" }` → filled fields + missing gaps. |
| POST | `/session/{sid}/answer` | Provide gap answers. Body: `{ "answers": { key: value } }`. |
| GET | `/session/{sid}/teachback` | Get the read-back script for consent. |
| POST | `/session/{sid}/consent` | Confirm and produce the PDF. Body: `{ "confirmed": true, "method": "voice" }`. |
| GET | `/session/{sid}/audit` | Append-only audit trail (DPDP evidence). |

## Files, tracking & voice

| Method | Path | Description |
|---|---|---|
| GET | `/files/{sid}/{name}` | Stream a generated PDF (stored in the database). |
| GET | `/tracking?owner=` | List tracked applications. |
| POST | `/tracking/{tid}/reference` | Attach a submission reference number. |
| POST | `/rejections` | Submit rejection feedback (learning loop). |
| POST | `/voice/asr` | Speech → text. |
| POST | `/voice/tts` | Text → speech. |

> **Invariant:** eligibility is decided only by the deterministic rules-gate. The LLM
> phrases explanations and gap questions; it never decides who qualifies.
